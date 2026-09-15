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
from scratch.labor_reservation_policies import (
    L1_ReserveOneWorkerAgent,
    L2_ReserveAllStrawberryCapacityAgent,
    L3_SafeWindowUrgencyAgent,
    L4_EconomicUrgencyAgent,
    L5_OpportunityCostGatingAgent
)

LABOR_POLICIES = {
    "M1_Baseline": m1_module.ClosedLoopEconomicV1,
    "Raw_Q50": BaseQ50Agent,
    "L1_Reserve1Worker": L1_ReserveOneWorkerAgent,
    "L2_ReserveAllCapacity": L2_ReserveAllStrawberryCapacityAgent,
    "L3_SafeWindowUrgency": L3_SafeWindowUrgencyAgent,
    "L4_EconomicUrgency": L4_EconomicUrgencyAgent,
    "L5_OpportunityCostGating": L5_OpportunityCostGatingAgent
}

def run_policy_seed(args):
    pol_name, seed = args
    cls = LABOR_POLICIES[pol_name]
    agent = cls()
    cfg = {"episodeSteps": 720, "seed": seed}
    env = kaggle_environments.make("kaggriculture", configuration=cfg)
    steps = env.run([agent, "starter"])
    rew = float(steps[-1][0]["reward"])

    # Sold quantities
    sold_qty = defaultdict(int)
    for st in steps:
        for o in (st[0].get("action") or {}).get("market", []):
            if isinstance(o, list) and len(o) >= 3 and o[0] == "SELL":
                sold_qty[o[1]] += int(o[2])

    return {
        "policy": pol_name,
        "seed": seed,
        "reward": rew,
        "sold_qty": dict(sold_qty)
    }

def compute_bootstrap_ci(diffs, n_boot=2000, ci=0.95):
    boot_means = [np.mean(np.random.choice(diffs, size=len(diffs), replace=True)) for _ in range(n_boot)]
    alpha = (1 - ci) / 2
    return float(np.percentile(boot_means, alpha * 100)), float(np.percentile(boot_means, (1 - alpha) * 100))

def main():
    seeds = list(range(1250, 1350)) # 100 seeds
    print(f"Evaluating L1-L5 Labor Reservation Policies across {len(seeds)} seeds...")

    all_jobs = []
    for p_name in LABOR_POLICIES.keys():
        for s in seeds:
            all_jobs.append((p_name, s))

    print(f"Total simulations: {len(all_jobs)} across {len(LABOR_POLICIES)} policies...")

    results = defaultdict(dict)
    with ProcessPoolExecutor(max_workers=11) as executor:
        for res in executor.map(run_policy_seed, all_jobs, chunksize=5):
            results[res["policy"]][res["seed"]] = res

    # Summary analysis
    print("\n" + "="*125)
    print("PHASE 6 & 7: LABOR RESERVATION POLICIES (L1-L5) VS M1 AND RAW Q50 (100 SEEDS)")
    print("="*125)

    base_q50_rews = np.array([results["Raw_Q50"][s]["reward"] for s in seeds])
    m1_rews = np.array([results["M1_Baseline"][s]["reward"] for s in seeds])

    summary_records = []

    for p_name in LABOR_POLICIES.keys():
        rews = np.array([results[p_name][s]["reward"] for s in seeds])
        m_rew = float(np.mean(rews))
        med_rew = float(np.median(rews))
        sd_rew = float(np.std(rews))

        # Diff vs M1
        diff_m1 = rews - m1_rews
        m_del_m1 = float(np.mean(diff_m1))
        ci_m1 = compute_bootstrap_ci(diff_m1)
        t_stat_m1, p_t_m1 = stats.ttest_rel(rews, m1_rews)
        w_stat_m1, p_w_m1 = stats.wilcoxon(rews, m1_rews) if np.any(diff_m1 != 0) else (0, 1.0)
        win_m1 = float(np.sum(diff_m1 > 0) / len(seeds) * 100)

        # Diff vs Q50
        diff_q50 = rews - base_q50_rews
        m_del_q50 = float(np.mean(diff_q50))
        ci_q50 = compute_bootstrap_ci(diff_q50)
        t_stat_q50, p_t_q50 = stats.ttest_rel(rews, base_q50_rews)
        w_stat_q50, p_w_q50 = stats.wilcoxon(rews, base_q50_rews) if np.any(diff_q50 != 0) else (0, 1.0)
        win_q50 = float(np.sum(diff_q50 > 0) / len(seeds) * 100)

        # Commodity averages
        sb_sold = float(np.mean([results[p_name][s]["sold_qty"].get("STRAWBERRY", 0) for s in seeds]))
        wheat_sold = float(np.mean([results[p_name][s]["sold_qty"].get("WHEAT", 0) for s in seeds]))
        milk_sold = float(np.mean([results[p_name][s]["sold_qty"].get("MILK", 0) for s in seeds]))
        wool_sold = float(np.mean([results[p_name][s]["sold_qty"].get("WOOL", 0) for s in seeds]))

        print(f"\n--- Policy: {p_name} ---")
        print(f"  Mean: ${m_rew:,.2f} | Median: ${med_rew:,.2f} | SD: ${sd_rew:,.2f}")
        print(f"  Vs M1:  Delta = ${m_del_m1:+,.2f} | 95% CI = [${ci_m1[0]:+,.1f}, ${ci_m1[1]:+,.1f}] | Win = {win_m1:.1f}% | p(t) = {p_t_m1:.4f} | p(W) = {p_w_m1:.4f}")
        print(f"  Vs Q50: Delta = ${m_del_q50:+,.2f} | 95% CI = [${ci_q50[0]:+,.1f}, ${ci_q50[1]:+,.1f}] | Win = {win_q50:.1f}% | p(t) = {p_t_q50:.4f} | p(W) = {p_w_q50:.4f}")
        print(f"  Sales: Straw = {sb_sold:.1f} u | Wheat = {wheat_sold:.1f} u | Milk = {milk_sold:.1f} u | Wool = {wool_sold:.1f} u")

        # Best 10 and Worst 10 vs Q50
        sorted_diff_q50 = sorted([(s, float(diff_q50[i])) for i, s in enumerate(seeds)], key=lambda x: x[1])
        worst_10 = sorted_diff_q50[:10]
        best_10 = sorted_diff_q50[-10:]

        summary_records.append({
            "policy": p_name,
            "mean": m_rew,
            "median": med_rew,
            "sd": sd_rew,
            "delta_m1": m_del_m1,
            "ci_m1": ci_m1,
            "win_m1": win_m1,
            "p_t_m1": float(p_t_m1),
            "p_w_m1": float(p_w_m1),
            "delta_q50": m_del_q50,
            "ci_q50": ci_q50,
            "win_q50": win_q50,
            "p_t_q50": float(p_t_q50),
            "p_w_q50": float(p_w_q50),
            "commodities": {
                "strawberry": sb_sold,
                "wheat": wheat_sold,
                "milk": milk_sold,
                "wool": wool_sold
            },
            "worst_10_vs_q50": worst_10,
            "best_10_vs_q50": best_10
        })

    with open("scratch/labor_reservation_policies_results.json", "w") as f:
        json.dump(summary_records, f, indent=2)
    print("\nSaved policy evaluation summary to scratch/labor_reservation_policies_results.json")

if __name__ == "__main__":
    main()
