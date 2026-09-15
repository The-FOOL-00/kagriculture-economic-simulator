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
from scratch.qualification_counterfactual_suite import SUITE_POLICIES

def compute_bootstrap_ci(diffs, n_boot=2000, ci=0.95):
    boot_means = [np.mean(np.random.choice(diffs, size=len(diffs), replace=True)) for _ in range(n_boot)]
    alpha = (1 - ci) / 2
    return float(np.percentile(boot_means, alpha * 100)), float(np.percentile(boot_means, (1 - alpha) * 100))

def run_generic_job(args):
    p_name, seed = args
    if p_name == "M1_Baseline":
        agent = m1_module.ClosedLoopEconomicV1()
    else:
        cls = SUITE_POLICIES[p_name]
        agent = cls()
    cfg = {"episodeSteps": 720, "seed": seed}
    env = kaggle_environments.make("kaggriculture", configuration=cfg)
    steps = env.run([agent, "starter"])
    rew = float(steps[-1][0]["reward"])

    sold_qty = defaultdict(int)
    for st in steps:
        for o in (st[0].get("action") or {}).get("market", []):
            if isinstance(o, list) and len(o) >= 3 and o[0] == "SELL":
                sold_qty[o[1]] += int(o[2])

    return p_name, seed, rew, dict(sold_qty)

def analyze_policy_group(group_name, policy_names, results, seeds, base_name="Raw_Q50", m1_name="M1_Baseline"):
    print("\n" + "="*110)
    print(f"REPORT GROUP: {group_name} (SEEDS 1250-1349, N={len(seeds)})")
    print("="*110)

    base_rews = np.array([results[base_name][s]["reward"] for s in seeds])
    m1_rews = np.array([results[m1_name][s]["reward"] for s in seeds])

    group_records = []

    for p_name in policy_names:
        rews = np.array([results[p_name][s]["reward"] for s in seeds])
        m_rew = float(np.mean(rews))
        med_rew = float(np.median(rews))
        sd_rew = float(np.std(rews))

        diff_base = rews - base_rews
        m_del_base = float(np.mean(diff_base))
        med_del_base = float(np.median(diff_base))
        ci_base = compute_bootstrap_ci(diff_base)
        t_stat_base, p_t_base = stats.ttest_rel(rews, base_rews) if np.any(diff_base != 0) else (0, 1.0)
        w_stat_base, p_w_base = stats.wilcoxon(rews, base_rews) if np.any(diff_base != 0) else (0, 1.0)
        win_base = float(np.sum(diff_base > 0) / len(seeds) * 100)

        diff_m1 = rews - m1_rews
        m_del_m1 = float(np.mean(diff_m1))
        ci_m1 = compute_bootstrap_ci(diff_m1)
        win_m1 = float(np.sum(diff_m1 > 0) / len(seeds) * 100)

        straw_sold = float(np.mean([results[p_name][s]["sold_qty"].get("STRAWBERRY", 0) for s in seeds]))
        wheat_sold = float(np.mean([results[p_name][s]["sold_qty"].get("WHEAT", 0) for s in seeds]))
        milk_sold = float(np.mean([results[p_name][s]["sold_qty"].get("MILK", 0) for s in seeds]))
        wool_sold = float(np.mean([results[p_name][s]["sold_qty"].get("WOOL", 0) for s in seeds]))

        print(f"\n--- {p_name} ---")
        print(f"  Mean: ${m_rew:,.2f} | Median: ${med_rew:,.2f} | SD: ${sd_rew:,.2f}")
        print(f"  Vs {base_name}: Delta = ${m_del_base:+,.2f} | MedDelta = ${med_del_base:+,.2f} | 95% CI = [${ci_base[0]:+,.1f}, ${ci_base[1]:+,.1f}] | Win = {win_base:.1f}% | p(t) = {p_t_base:.5f} | p(W) = {p_w_base:.5f}")
        print(f"  Vs {m1_name}: Delta = ${m_del_m1:+,.2f} | 95% CI = [${ci_m1[0]:+,.1f}, ${ci_m1[1]:+,.1f}] | Win = {win_m1:.1f}%")
        print(f"  Commodities: Straw = {straw_sold:.2f} u | Wheat = {wheat_sold:.2f} u | Milk = {milk_sold:.2f} u | Wool = {wool_sold:.2f} u")

        sorted_diff_base = sorted([(s, float(diff_base[i])) for i, s in enumerate(seeds)], key=lambda x: x[1])
        worst_10 = sorted_diff_base[:10]
        best_10 = sorted_diff_base[-10:]

        group_records.append({
            "policy": p_name,
            "mean": m_rew,
            "median": med_rew,
            "sd": sd_rew,
            "delta_base": m_del_base,
            "median_delta_base": med_del_base,
            "ci_base": ci_base,
            "win_base": win_base,
            "p_t_base": float(p_t_base),
            "p_w_base": float(p_w_base),
            "delta_m1": m_del_m1,
            "ci_m1": ci_m1,
            "win_m1": win_m1,
            "commodities": {"straw": straw_sold, "wheat": wheat_sold, "milk": milk_sold, "wool": wool_sold},
            "worst_10_vs_base": worst_10,
            "best_10_vs_base": best_10
        })

    return group_records

def main():
    seeds = list(range(1250, 1350)) # 100 seeds
    
    policy_list = ["M1_Baseline"] + list(SUITE_POLICIES.keys())
    jobs = [(p, s) for p in policy_list for s in seeds]
    print(f"Executing Qualification Counterfactual Suite: {len(jobs)} simulations across {len(policy_list)} policies...")

    results = defaultdict(dict)
    with ProcessPoolExecutor(max_workers=11) as executor:
        for p_name, s, rew, sq in executor.map(run_generic_job, jobs, chunksize=5):
            results[p_name][s] = {"reward": rew, "sold_qty": sq}

    output_data = {}

    # Phase 4: Reproduction of W1-W7 key variants
    phase4_pols = ["M1_Baseline", "Raw_Q50", "W2_SuppressClearing", "W6_GatedLowerValue", "A_only_U1", "A_plus_B_L_Minimal"]
    output_data["Phase4_Reproduction"] = analyze_policy_group("PHASE 4: KEY REPLICATIONS (W2, W6, L3, L_MINIMAL)", phase4_pols, results, seeds)

    # Phase 6: A/B Component Decomposition
    phase6_pols = ["Raw_Q50", "A_only_U1", "B_only_B1", "A_plus_B_L_Minimal"]
    output_data["Phase6_AB_Decomposition"] = analyze_policy_group("PHASE 6: ISOLATION OF A (URGENCY) AND B (WEED GATING)", phase6_pols, results, seeds)

    # Phase 7: Urgency Ordering Comparison
    phase7_pols = ["Raw_Q50", "A_only_U1", "U2_StrawWheatMelon", "U3_MelonStrawWheat", "U4_EconomicUrgency", "U5_IrreversibleLoss"]
    output_data["Phase7_Urgency_Comparison"] = analyze_policy_group("PHASE 7: URGENCY ORDERING COMPARISON (U1-U5)", phase7_pols, results, seeds)

    # Phase 8: Weed Suppression Condition Comparison
    phase8_pols = ["Raw_Q50", "B_only_B1", "B2_BacklogGt1", "B3_AfternoonGating", "B4_PreserveAccess", "B5_OutsideProdZone", "A_plus_B_L_Minimal"]
    output_data["Phase8_Weed_Gating_Comparison"] = analyze_policy_group("PHASE 8: WEED SUPPRESSION CONDITIONS (B1-B5)", phase8_pols, results, seeds)

    with open("scratch/qualification_suite_results.json", "w") as f:
        json.dump(output_data, f, indent=2)

    print("\nSaved all qualification suite results to scratch/qualification_suite_results.json")

if __name__ == "__main__":
    main()
