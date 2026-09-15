import sys
import os
import json
from collections import defaultdict
import numpy as np
from scipy import stats
from concurrent.futures import ProcessPoolExecutor
import kaggle_environments

sys.path.insert(0, os.path.abspath('.'))

import candidates.candidate_cl_fert_gated as m1_module
from scratch.counterfactual_policies_w1_w7 import BaseQ50Agent
import kaggle_environments.envs.kaggriculture.kaggriculture as engine

class L_LaborBandwidthMinimalAgent(BaseQ50Agent):
    """
    FROZEN MINIMAL LABOR BANDWIDTH POLICY (L_MINIMAL):
    Derived from empirical opportunity-cost analysis and shadow-value ordering:
    1. Safe Window Urgency: Sort ripe crop harvest candidates so that perishable/capped crops
       (Strawberry, yield >= 2) are harvested first, followed by Melon, followed by Wheat.
    2. Discretionary Task Gating: When mature strawberries await harvest, suppress peripheral
       weed digging (which has negative net marginal value during harvest contention).
    """
    def __init__(self, quota=50):
        super().__init__(quota)

    def _scan_field(self, tiles, quads, seeds, shed, invs, day):
        res = super()._scan_field(tiles, quads, seeds, shed, invs, day)
        
        has_ripe_straw = False
        def crop_urgency_key(pos):
            nonlocal has_ripe_straw
            t = tiles[pos[1]][pos[0]]
            if not isinstance(t, dict): return 999
            c = t.get("crop")
            yu = t.get("yield_units", 0)
            if c == "STRAWBERRY":
                has_ripe_straw = True
                return 0 if yu >= 2 else 5
            elif c == "MELON":
                return 10
            elif c == "WHEAT":
                return 20
            return 50
        
        res["ripe_crops"].sort(key=crop_urgency_key)
        if has_ripe_straw:
            res["weeds"] = [] # Prohibit discretionary weed digging when ripe strawberries wait
        return res

TRUE_ORIG_COMMIT = engine._commit_unit
TRUE_ORIG_HIRE = engine._do_hire
TRUE_ORIG_LAND = engine._do_buy_land
TRUE_ORIG_PROCESS = engine._process_market

def run_agent_with_exact_ledger(args):
    pol_name, seed = args
    if pol_name == "M1_Baseline":
        agent = m1_module.ClosedLoopEconomicV1()
    elif pol_name == "Raw_Q50":
        agent = BaseQ50Agent(50)
    elif pol_name == "L_Minimal":
        agent = L_LaborBandwidthMinimalAgent(50)
    else:
        raise ValueError(f"Unknown policy {pol_name}")

    ledger = defaultdict(float)
    current_f0 = [None]

    def my_commit(op, item, price, farm, private, market, shed_capacity=100):
        m_b = farm['money']
        res = TRUE_ORIG_COMMIT(op, item, price, farm, private, market, shed_capacity)
        if res and farm is current_f0[0]:
            delta = farm['money'] - m_b
            if op == 'SELL':
                ledger['REV_' + item] += delta
            elif op == 'BUY_PRODUCT':
                ledger['EXP_FEED_' + item] += abs(delta)
            elif op == 'BUY_SEED':
                ledger['EXP_SEED_' + item] += abs(delta)
            elif op == 'BUY_ANIMAL':
                ledger['EXP_ANIMAL_' + item] += abs(delta)
        return res

    def my_hire(farm, private, board_size, mult=engine.FARM_HAND_COST_MULT):
        m_b = farm['money']
        TRUE_ORIG_HIRE(farm, private, board_size, mult)
        if farm is current_f0[0]:
            ledger['EXP_HIRE'] += (m_b - farm['money'])

    def my_land(farm, board_size):
        m_b = farm['money']
        TRUE_ORIG_LAND(farm, board_size)
        if farm is current_f0[0]:
            ledger['EXP_LAND'] += (m_b - farm['money'])

    def my_process_market(state, env):
        current_f0[0] = state[0].observation.farms[0]
        TRUE_ORIG_PROCESS(state, env)

    engine._commit_unit = my_commit
    engine._do_hire = my_hire
    engine._do_buy_land = my_land
    engine._process_market = my_process_market

    try:
        cfg = {"episodeSteps": 720, "seed": seed}
        env = kaggle_environments.make("kaggriculture", configuration=cfg)
        steps = env.run([agent, "starter"])
    finally:
        engine._commit_unit = TRUE_ORIG_COMMIT
        engine._do_hire = TRUE_ORIG_HIRE
        engine._do_buy_land = TRUE_ORIG_LAND
        engine._process_market = TRUE_ORIG_PROCESS

    env_rew = float(steps[-1][0]["reward"])
    start_money = float(steps[0][0]["observation"]["farms"][0]["money"])

    total_rev = sum(v for k, v in ledger.items() if k.startswith("REV_"))
    total_exp = sum(v for k, v in ledger.items() if k.startswith("EXP_"))
    reconstructed = start_money + total_rev - total_exp
    diff = abs(reconstructed - env_rew)
    assert diff < 1e-6, f"Mismatch on seed {seed}: recon={reconstructed}, env={env_rew}, diff={diff}"

    sold_qty = defaultdict(int)
    for st in steps:
        for o in (st[0].get("action") or {}).get("market", []):
            if isinstance(o, list) and len(o) >= 3 and o[0] == "SELL":
                sold_qty[o[1]] += int(o[2])

    return {
        "policy": pol_name,
        "seed": seed,
        "reward": env_rew,
        "reconstructed": reconstructed,
        "diff": diff,
        "ledger": dict(ledger),
        "sold_qty": dict(sold_qty)
    }

def compute_paired_stats(test_vals, base_vals, n_boot=2000):
    diffs = test_vals - base_vals
    mean_diff = float(np.mean(diffs))
    med_diff = float(np.median(diffs))
    sd_diff = float(np.std(diffs))
    win_rate = float(np.sum(diffs > 0) / len(diffs) * 100)

    boot_means = [np.mean(np.random.choice(diffs, size=len(diffs), replace=True)) for _ in range(n_boot)]
    ci_low, ci_high = float(np.percentile(boot_means, 2.5)), float(np.percentile(boot_means, 97.5))

    t_stat, p_t = stats.ttest_rel(test_vals, base_vals)
    w_stat, p_w = stats.wilcoxon(test_vals, base_vals) if np.any(diffs != 0) else (0, 1.0)

    return {
        "mean_diff": mean_diff,
        "median_diff": med_diff,
        "sd_diff": sd_diff,
        "win_rate": win_rate,
        "ci_95": [ci_low, ci_high],
        "p_t": float(p_t),
        "p_w": float(p_w)
    }

def main():
    holdout_seeds = list(range(35000, 35200)) # Pristine N=200 holdout
    policies = ["M1_Baseline", "Raw_Q50", "L_Minimal"]
    
    print(f"Starting Fresh Holdout Evaluation on Pristine Seeds 35000-35199 (N={len(holdout_seeds)})...")
    print(f"Policies: {policies}")
    print(f"Total simulations: {len(policies) * len(holdout_seeds)} (with exact machine-precision accounting hooks)...")

    jobs = [(p, s) for p in policies for s in holdout_seeds]
    results = defaultdict(dict)

    with ProcessPoolExecutor(max_workers=11) as executor:
        for res in executor.map(run_agent_with_exact_ledger, jobs, chunksize=5):
            results[res["policy"]][res["seed"]] = res

    print("\n" + "="*120)
    print(f"PHASE 11 & 12: FRESH HOLDOUT VALIDATION REPORT (SEEDS 35000-35199, N=200)")
    print("="*120)

    m1_rews = np.array([results["M1_Baseline"][s]["reward"] for s in holdout_seeds])
    q50_rews = np.array([results["Raw_Q50"][s]["reward"] for s in holdout_seeds])
    l_min_rews = np.array([results["L_Minimal"][s]["reward"] for s in holdout_seeds])

    # Check accounting identity across all 600 runs
    all_diffs = []
    for p in policies:
        for s in holdout_seeds:
            all_diffs.append(results[p][s]["diff"])
    max_diff = max(all_diffs)
    print(f"Exact Accounting Identity: Max |Reconstructed - Env| across {len(all_diffs)} runs = {max_diff:.8e} (100% Exact!)")

    # Overall Summary
    print("\n--- Summary Performance ---")
    for p, rews in [("M1_Baseline", m1_rews), ("Raw_Q50", q50_rews), ("L_Minimal", l_min_rews)]:
        print(f"{p:15s} | Mean: ${np.mean(rews):,.2f} | Median: ${np.median(rews):,.2f} | SD: ${np.std(rews):,.2f}")

    # Paired comparisons
    stats_l_vs_m1 = compute_paired_stats(l_min_rews, m1_rews)
    stats_l_vs_q50 = compute_paired_stats(l_min_rews, q50_rews)
    stats_q50_vs_m1 = compute_paired_stats(q50_rews, m1_rews)

    print("\n--- Paired Statistical Comparisons ---")
    print(f"1. L_Minimal vs M1 Baseline:")
    print(f"   Delta: ${stats_l_vs_m1['mean_diff']:+,.2f} | Median Delta: ${stats_l_vs_m1['median_diff']:+,.2f} | SD: ${stats_l_vs_m1['sd_diff']:,.2f}")
    print(f"   95% Paired Bootstrap CI: [${stats_l_vs_m1['ci_95'][0]:+,.2f}, ${stats_l_vs_m1['ci_95'][1]:+,.2f}]")
    print(f"   Win Rate: {stats_l_vs_m1['win_rate']:.1f}% | Paired t p-val: {stats_l_vs_m1['p_t']:.6f} | Wilcoxon p-val: {stats_l_vs_m1['p_w']:.6f}")

    print(f"\n2. L_Minimal vs Raw Q50:")
    print(f"   Delta: ${stats_l_vs_q50['mean_diff']:+,.2f} | Median Delta: ${stats_l_vs_q50['median_diff']:+,.2f} | SD: ${stats_l_vs_q50['sd_diff']:,.2f}")
    print(f"   95% Paired Bootstrap CI: [${stats_l_vs_q50['ci_95'][0]:+,.2f}, ${stats_l_vs_q50['ci_95'][1]:+,.2f}]")
    print(f"   Win Rate: {stats_l_vs_q50['win_rate']:.1f}% | Paired t p-val: {stats_l_vs_q50['p_t']:.6f} | Wilcoxon p-val: {stats_l_vs_q50['p_w']:.6f}")

    print(f"\n3. Raw Q50 vs M1 Baseline:")
    print(f"   Delta: ${stats_q50_vs_m1['mean_diff']:+,.2f} | Median Delta: ${stats_q50_vs_m1['median_diff']:+,.2f} | SD: ${stats_q50_vs_m1['sd_diff']:,.2f}")
    print(f"   95% Paired Bootstrap CI: [${stats_q50_vs_m1['ci_95'][0]:+,.2f}, ${stats_q50_vs_m1['ci_95'][1]:+,.2f}]")
    print(f"   Win Rate: {stats_q50_vs_m1['win_rate']:.1f}% | Paired t p-val: {stats_q50_vs_m1['p_t']:.6f} | Wilcoxon p-val: {stats_q50_vs_m1['p_w']:.6f}")

    # Commodity Averages
    print("\n--- Commodity Averages (Units Sold per Seed) ---")
    print(f"{'Commodity':<15} | {'M1_Baseline':<12} | {'Raw_Q50':<12} | {'L_Minimal':<12} | {'Delta(L-Q50)':<12} | {'Delta(L-M1)':<12}")
    print("-" * 80)
    for item in ["STRAWBERRY", "WHEAT", "MILK", "WOOL", "MELON", "FERTILIZER"]:
        m1_qty = np.mean([results["M1_Baseline"][s]["sold_qty"].get(item, 0) for s in holdout_seeds])
        q50_qty = np.mean([results["Raw_Q50"][s]["sold_qty"].get(item, 0) for s in holdout_seeds])
        l_qty = np.mean([results["L_Minimal"][s]["sold_qty"].get(item, 0) for s in holdout_seeds])
        print(f"{item:<15} | {m1_qty:<12.2f} | {q50_qty:<12.2f} | {l_qty:<12.2f} | {l_qty - q50_qty:<+12.2f} | {l_qty - m1_qty:<+12.2f}")

    # Ledger Financial Breakdown
    print("\n--- Financial Ledger Averages per Seed ---")
    all_ledger_keys = set()
    for p in policies:
        for s in holdout_seeds:
            all_ledger_keys.update(results[p][s]["ledger"].keys())
    for k in sorted(all_ledger_keys):
        m1_val = np.mean([results["M1_Baseline"][s]["ledger"].get(k, 0) for s in holdout_seeds])
        q50_val = np.mean([results["Raw_Q50"][s]["ledger"].get(k, 0) for s in holdout_seeds])
        l_val = np.mean([results["L_Minimal"][s]["ledger"].get(k, 0) for s in holdout_seeds])
        print(f"{k:<20} | M1: ${m1_val:10.2f} | Q50: ${q50_val:10.2f} | L_Min: ${l_val:10.2f} | Delta(L-Q50): ${l_val - q50_val:+10.2f}")

    # Best 10 and Worst 10 vs Q50
    diff_l_q50 = l_min_rews - q50_rews
    sorted_pairs = sorted([(s, float(diff_l_q50[i])) for i, s in enumerate(holdout_seeds)], key=lambda x: x[1])
    worst_10 = sorted_pairs[:10]
    best_10 = sorted_pairs[-10:]

    print("\n--- Worst 10 Seeds vs Q50 ---")
    for s, d in worst_10:
        print(f"  Seed {s}: ${d:+,.2f}")

    print("\n--- Best 10 Seeds vs Q50 ---")
    for s, d in best_10:
        print(f"  Seed {s}: ${d:+,.2f}")

    out_data = {
        "seeds": holdout_seeds,
        "summary": {
            "M1_Baseline": {"mean": float(np.mean(m1_rews)), "median": float(np.median(m1_rews)), "sd": float(np.std(m1_rews))},
            "Raw_Q50": {"mean": float(np.mean(q50_rews)), "median": float(np.median(q50_rews)), "sd": float(np.std(q50_rews))},
            "L_Minimal": {"mean": float(np.mean(l_min_rews)), "median": float(np.median(l_min_rews)), "sd": float(np.std(l_min_rews))}
        },
        "comparisons": {
            "L_vs_M1": stats_l_vs_m1,
            "L_vs_Q50": stats_l_vs_q50,
            "Q50_vs_M1": stats_q50_vs_m1
        },
        "worst_10_vs_q50": worst_10,
        "best_10_vs_q50": best_10,
        "max_accounting_diff": max_diff,
        "detailed": {p: {s: results[p][s] for s in holdout_seeds} for p in policies}
    }

    with open("scratch/fresh_holdout_200seeds_results.json", "w") as f:
        json.dump(out_data, f, indent=2)

    print("\nSaved complete holdout evaluation results to scratch/fresh_holdout_200seeds_results.json")

if __name__ == "__main__":
    main()
