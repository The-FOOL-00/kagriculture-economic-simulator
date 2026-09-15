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
from scratch.qualification_counterfactual_suite import BaseQ50Agent
import candidates.candidate_cl_labor_minimal_v1 as candidate_module
import kaggle_environments.envs.kaggriculture.kaggriculture as engine

TRUE_ORIG_COMMIT = engine._commit_unit
TRUE_ORIG_HIRE = engine._do_hire
TRUE_ORIG_LAND = engine._do_buy_land
TRUE_ORIG_PROCESS = engine._process_market

def run_candidate_job(args):
    pol_name, seed = args
    if pol_name == "M1_Baseline":
        agent = m1_module.ClosedLoopEconomicV1()
    elif pol_name == "Raw_Q50":
        agent = BaseQ50Agent(50)
    elif pol_name == "Frozen_Candidate":
        agent = candidate_module.ClosedLoopLaborMinimalV1(50)
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
        "diff": diff,
        "ledger": dict(ledger),
        "sold_qty": dict(sold_qty)
    }

def compute_ci(diffs, n_boot=5000, ci=0.95):
    boot_means = [np.mean(np.random.choice(diffs, size=len(diffs), replace=True)) for _ in range(n_boot)]
    alpha = (1 - ci) / 2
    return float(np.percentile(boot_means, alpha * 100)), float(np.percentile(boot_means, (1 - alpha) * 100))

def main():
    seeds = list(range(941000, 941500)) # Pristine N=500 qualification block (0 matches across repo)
    policies = ["M1_Baseline", "Raw_Q50", "Frozen_Candidate"]

    print(f"Executing Phase 15 Final Qualification on Pristine Seeds 941000-941499 (N={len(seeds)})...")
    print(f"Total simulations: {len(policies) * len(seeds)} (with machine-precision accounting hooks)...")

    jobs = [(p, s) for p in policies for s in seeds]
    results = defaultdict(dict)

    with ProcessPoolExecutor(max_workers=11) as executor:
        for res in executor.map(run_candidate_job, jobs, chunksize=5):
            results[res["policy"]][res["seed"]] = res

    print("\n" + "="*120)
    print("PHASE 15: FINAL 500-SEED CANDIDATE QUALIFICATION REPORT")
    print("="*120)

    m1_rews = np.array([results["M1_Baseline"][s]["reward"] for s in seeds])
    q50_rews = np.array([results["Raw_Q50"][s]["reward"] for s in seeds])
    cand_rews = np.array([results["Frozen_Candidate"][s]["reward"] for s in seeds])

    # 1. Accounting check
    all_diffs = [results[p][s]["diff"] for p in policies for s in seeds]
    max_diff = max(all_diffs)
    print(f"Exact Accounting Identity: Max |Reconstructed - Env| across {len(all_diffs)} runs = {max_diff:.8e} (100% Exact!)")

    # 2. Overall Performance
    print("\n--- Summary Performance (N=500) ---")
    for p, rews in [("M1_Baseline", m1_rews), ("Raw_Q50", q50_rews), ("Frozen_Candidate", cand_rews)]:
        print(f"{p:18s} | Mean: ${np.mean(rews):,.2f} | Median: ${np.median(rews):,.2f} | SD: ${np.std(rews):,.2f}")

    # 3. Paired Deltas
    diff_c_q50 = cand_rews - q50_rews
    diff_c_m1 = cand_rews - m1_rews
    diff_q50_m1 = q50_rews - m1_rews

    ci95_q50 = compute_ci(diff_c_q50, ci=0.95)
    ci99_q50 = compute_ci(diff_c_q50, ci=0.99)
    ci95_m1 = compute_ci(diff_c_m1, ci=0.95)
    ci99_m1 = compute_ci(diff_c_m1, ci=0.99)

    t_stat_q50, p_t_q50 = stats.ttest_rel(cand_rews, q50_rews)
    w_stat_q50, p_w_q50 = stats.wilcoxon(cand_rews, q50_rews)

    t_stat_m1, p_t_m1 = stats.ttest_rel(cand_rews, m1_rews)
    w_stat_m1, p_w_m1 = stats.wilcoxon(cand_rews, m1_rews)

    print("\n--- Paired Statistical Comparisons ---")
    print(f"1. Frozen_Candidate vs Raw_Q50 (Primary Decision Metric):")
    print(f"   Mean Delta:    ${np.mean(diff_c_q50):+,.2f}")
    print(f"   Median Delta:  ${np.median(diff_c_q50):+,.2f}")
    print(f"   SD of Delta:   ${np.std(diff_c_q50):,.2f}")
    print(f"   95% Paired CI: [${ci95_q50[0]:+,.2f}, ${ci95_q50[1]:+,.2f}]")
    print(f"   99% Paired CI: [${ci99_q50[0]:+,.2f}, ${ci99_q50[1]:+,.2f}]")
    print(f"   Win Rate:      {np.mean(diff_c_q50 > 0)*100:.1f}%")
    print(f"   Paired t-test: t = {t_stat_q50:.4f}, p = {p_t_q50:.8e}")
    print(f"   Wilcoxon test: W = {w_stat_q50:.1f}, p = {p_w_q50:.8e}")

    print(f"\n2. Frozen_Candidate vs M1_Baseline:")
    print(f"   Mean Delta:    ${np.mean(diff_c_m1):+,.2f}")
    print(f"   Median Delta:  ${np.median(diff_c_m1):+,.2f}")
    print(f"   SD of Delta:   ${np.std(diff_c_m1):,.2f}")
    print(f"   95% Paired CI: [${ci95_m1[0]:+,.2f}, ${ci95_m1[1]:+,.2f}]")
    print(f"   99% Paired CI: [${ci99_m1[0]:+,.2f}, ${ci99_m1[1]:+,.2f}]")
    print(f"   Win Rate:      {np.mean(diff_c_m1 > 0)*100:.1f}%")
    print(f"   Paired t-test: p = {p_t_m1:.5f}")
    print(f"   Wilcoxon test: p = {p_w_m1:.5f}")

    # 4. Commodities
    print("\n--- Physical Commodity Sales (Mean Units per Seed) ---")
    print(f"{'Commodity':<15} | {'M1_Baseline':<12} | {'Raw_Q50':<12} | {'Candidate':<12} | {'Delta(C-Q50)':<12} | {'Delta(C-M1)':<12}")
    print("-" * 80)
    for item in ["STRAWBERRY", "WHEAT", "MILK", "WOOL", "MELON", "FERTILIZER"]:
        m1_q = np.mean([results["M1_Baseline"][s]["sold_qty"].get(item, 0) for s in seeds])
        q50_q = np.mean([results["Raw_Q50"][s]["sold_qty"].get(item, 0) for s in seeds])
        c_q = np.mean([results["Frozen_Candidate"][s]["sold_qty"].get(item, 0) for s in seeds])
        print(f"{item:<15} | {m1_q:<12.2f} | {q50_q:<12.2f} | {c_q:<12.2f} | {c_q - q50_q:<+12.2f} | {c_q - m1_q:<+12.2f}")

    # 5. Financial Ledger Breakdown
    print("\n--- Financial Ledger Averages per Seed ---")
    all_keys = set()
    for p in policies:
        for s in seeds:
            all_keys.update(results[p][s]["ledger"].keys())
    for k in sorted(all_keys):
        m1_v = np.mean([results["M1_Baseline"][s]["ledger"].get(k, 0) for s in seeds])
        q50_v = np.mean([results["Raw_Q50"][s]["ledger"].get(k, 0) for s in seeds])
        c_v = np.mean([results["Frozen_Candidate"][s]["ledger"].get(k, 0) for s in seeds])
        print(f"{k:<20} | M1: ${m1_v:10.2f} | Q50: ${q50_v:10.2f} | Cand: ${c_v:10.2f} | Delta(C-Q50): ${c_v - q50_v:+10.2f}")

    # 6. Best 20 and Worst 20 vs Q50
    sorted_pairs = sorted([(s, float(diff_c_q50[i])) for i, s in enumerate(seeds)], key=lambda x: x[1])
    worst_20 = sorted_pairs[:20]
    best_20 = sorted_pairs[-20:]

    out_data = {
        "seeds": seeds,
        "summary": {
            "M1_Baseline": {"mean": float(np.mean(m1_rews)), "median": float(np.median(m1_rews)), "sd": float(np.std(m1_rews))},
            "Raw_Q50": {"mean": float(np.mean(q50_rews)), "median": float(np.median(q50_rews)), "sd": float(np.std(q50_rews))},
            "Frozen_Candidate": {"mean": float(np.mean(cand_rews)), "median": float(np.median(cand_rews)), "sd": float(np.std(cand_rews))}
        },
        "stats_vs_q50": {
            "mean_delta": float(np.mean(diff_c_q50)),
            "median_delta": float(np.median(diff_c_q50)),
            "sd_delta": float(np.std(diff_c_q50)),
            "ci95": ci95_q50,
            "ci99": ci99_q50,
            "win_rate": float(np.mean(diff_c_q50 > 0)*100),
            "p_t": float(p_t_q50),
            "p_w": float(p_w_q50)
        },
        "stats_vs_m1": {
            "mean_delta": float(np.mean(diff_c_m1)),
            "median_delta": float(np.median(diff_c_m1)),
            "ci95": ci95_m1,
            "ci99": ci99_m1,
            "win_rate": float(np.mean(diff_c_m1 > 0)*100),
            "p_t": float(p_t_m1),
            "p_w": float(p_w_m1)
        },
        "worst_20_vs_q50": worst_20,
        "best_20_vs_q50": best_20,
        "detailed": {p: {s: results[p][s] for s in seeds} for p in policies}
    }

    with open("scratch/final_500seed_qualification_results.json", "w") as f:
        json.dump(out_data, f, indent=2)

    print("\nSaved complete 500-seed qualification results to scratch/final_500seed_qualification_results.json")

if __name__ == "__main__":
    main()
