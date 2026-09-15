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
import candidates.slot2_aethel_refined_v2 as v2_module
from scratch.qualification_counterfactual_suite import BaseQ50Agent, L_MinimalAgent

def compute_ci(diffs, n_boot=5000, ci=0.95):
    boot_means = [np.mean(np.random.choice(diffs, size=len(diffs), replace=True)) for _ in range(n_boot)]
    alpha = (1 - ci) / 2
    return float(np.percentile(boot_means, alpha * 100)), float(np.percentile(boot_means, (1 - alpha) * 100))

def run_v2_seed(seed):
    agent = v2_module.agent
    cfg = {"episodeSteps": 720, "seed": seed}
    env = kaggle_environments.make("kaggriculture", configuration=cfg)
    steps = env.run([agent, "starter"])
    rew = float(steps[-1][0]["reward"])

    sold_qty = defaultdict(int)
    for st in steps:
        for o in (st[0].get("action") or {}).get("market", []):
            if isinstance(o, list) and len(o) >= 3 and o[0] == "SELL":
                sold_qty[o[1]] += int(o[2])

    moves = 0
    idle = 0
    prod = 0
    for st in steps:
        a = st[0].get("action") or {}
        all_a = [a.get("farmer")] + (a.get("hands") or [])
        for act in all_a:
            if act and isinstance(act, list) and len(act) > 0:
                op = act[0]
                if op in {"NORTH", "SOUTH", "EAST", "WEST"}:
                    moves += 1
                elif op == "PASS":
                    idle += 1
                else:
                    prod += 1
            else:
                idle += 1

    return seed, rew, dict(sold_qty), moves, idle, prod

def main():
    # 1. Load holdout results
    with open("scratch/fresh_holdout_200seeds_results.json") as f:
        holdout_data = json.load(f)

    seeds = holdout_data["seeds"]
    m1_detailed = holdout_data["detailed"]["M1_Baseline"]
    q50_detailed = holdout_data["detailed"]["Raw_Q50"]
    l_detailed = holdout_data["detailed"]["L_Minimal"]

    m1_rews = np.array([m1_detailed[str(s)]["reward"] for s in seeds])
    q50_rews = np.array([q50_detailed[str(s)]["reward"] for s in seeds])
    l_rews = np.array([l_detailed[str(s)]["reward"] for s in seeds])

    diff_l_q50 = l_rews - q50_rews
    diff_l_m1 = l_rews - m1_rews

    # Bootstrap 95% and 99% CI
    ci95_q50 = compute_ci(diff_l_q50, ci=0.95)
    ci99_q50 = compute_ci(diff_l_q50, ci=0.99)
    ci95_m1 = compute_ci(diff_l_m1, ci=0.95)
    ci99_m1 = compute_ci(diff_l_m1, ci=0.99)

    t_stat_q50, p_t_q50 = stats.ttest_rel(l_rews, q50_rews)
    w_stat_q50, p_w_q50 = stats.wilcoxon(l_rews, q50_rews)

    t_stat_m1, p_t_m1 = stats.ttest_rel(l_rews, m1_rews)
    w_stat_m1, p_w_m1 = stats.wilcoxon(l_rews, m1_rews)

    print("="*100)
    print("PHASE 10 & 11: STATISTICAL PURITY REPORT ON FRESH HOLDOUT (N=200)")
    print("="*100)
    print(f"L_Minimal vs Raw Q50:")
    print(f"  Mean Delta:    ${np.mean(diff_l_q50):+,.2f}")
    print(f"  Median Delta:  ${np.median(diff_l_q50):+,.2f}")
    print(f"  SD of Delta:   ${np.std(diff_l_q50):,.2f}")
    print(f"  95% Paired CI: [${ci95_q50[0]:+,.2f}, ${ci95_q50[1]:+,.2f}]")
    print(f"  99% Paired CI: [${ci99_q50[0]:+,.2f}, ${ci99_q50[1]:+,.2f}]")
    print(f"  Win Rate:      {np.mean(diff_l_q50 > 0)*100:.1f}%")
    print(f"  Paired t-test: t = {t_stat_q50:.3f}, p = {p_t_q50:.6e}")
    print(f"  Wilcoxon test: W = {w_stat_q50:.1f}, p = {p_w_q50:.6e}")

    print(f"\nL_Minimal vs M1 Baseline:")
    print(f"  Mean Delta:    ${np.mean(diff_l_m1):+,.2f}")
    print(f"  Median Delta:  ${np.median(diff_l_m1):+,.2f}")
    print(f"  95% Paired CI: [${ci95_m1[0]:+,.2f}, ${ci95_m1[1]:+,.2f}]")
    print(f"  99% Paired CI: [${ci99_m1[0]:+,.2f}, ${ci99_m1[1]:+,.2f}]")
    print(f"  Win Rate:      {np.mean(diff_l_m1 > 0)*100:.1f}%")
    print(f"  Paired t-test: p = {p_t_m1:.4f}")
    print(f"  Wilcoxon test: p = {p_w_m1:.4f}")

    # Best 20 and Worst 20
    sorted_pairs = sorted([(s, float(diff_l_q50[i])) for i, s in enumerate(seeds)], key=lambda x: x[1])
    worst_20 = sorted_pairs[:20]
    best_20 = sorted_pairs[-20:]

    # Quartiles of baseline Q50 reward
    q50_q25 = np.percentile(q50_rews, 25)
    q50_q50 = np.percentile(q50_rews, 50)
    q50_q75 = np.percentile(q50_rews, 75)

    q1_idx = np.where(q50_rews <= q50_q25)[0]
    q2_idx = np.where((q50_rews > q50_q25) & (q50_rews <= q50_q50))[0]
    q3_idx = np.where((q50_rews > q50_q50) & (q50_rews <= q50_q75))[0]
    q4_idx = np.where(q50_rews > q50_q75)[0]

    print("\n" + "="*100)
    print("PHASE 12: STRESS-TEST BY Q50 BASELINE REWARD QUARTILES")
    print("="*100)
    for q_name, q_idx in [("Q1 (Lowest 25% Baseline, <$115k)", q1_idx),
                          ("Q2 (25%-50% Baseline, $115k-$132k)", q2_idx),
                          ("Q3 (50%-75% Baseline, $132k-$142k)", q3_idx),
                          ("Q4 (Top 25% Baseline, >$142k)", q4_idx)]:
        q_diffs = diff_l_q50[q_idx]
        print(f"{q_name:40s} | Delta: ${np.mean(q_diffs):+,.2f} | Win: {np.mean(q_diffs > 0)*100:.1f}% | Median Delta: ${np.median(q_diffs):+,.2f}")

    # 2. V2 Comparison on 50 seeds
    v2_seeds = seeds[:50]
    print("\n" + "="*100)
    print("PHASE 13: V2 BEHAVIORAL COMPARISON (SEEDS 35000-35049, N=50)")
    print("="*100)
    v2_results = {}
    with ProcessPoolExecutor(max_workers=11) as ex:
        for s, rew, sq, mv, idl, prd in ex.map(run_v2_seed, v2_seeds, chunksize=2):
            v2_results[s] = {"reward": rew, "sold_qty": sq, "moves": mv, "idle": idl, "prod": prd}

    v2_rews = np.array([v2_results[s]["reward"] for s in v2_seeds])
    l_sub_rews = np.array([l_detailed[str(s)]["reward"] for s in v2_seeds])
    q50_sub_rews = np.array([q50_detailed[str(s)]["reward"] for s in v2_seeds])

    print(f"V2 Mean Reward:      ${np.mean(v2_rews):,.2f}")
    print(f"L_Min Mean Reward:   ${np.mean(l_sub_rews):,.2f}")
    print(f"Q50 Mean Reward:     ${np.mean(q50_sub_rews):,.2f}")
    print(f"V2 - L_Min Gap:      ${np.mean(v2_rews - l_sub_rews):+,.2f}")

    for item in ["STRAWBERRY", "WHEAT", "MILK", "WOOL", "MELON", "FERTILIZER"]:
        v2_q = np.mean([v2_results[s]["sold_qty"].get(item, 0) for s in v2_seeds])
        l_q = np.mean([l_detailed[str(s)]["sold_qty"].get(item, 0) for s in v2_seeds])
        q_q = np.mean([q50_detailed[str(s)]["sold_qty"].get(item, 0) for s in v2_seeds])
        print(f"  {item:<12s} | V2: {v2_q:6.1f} u | L_Min: {l_q:6.1f} u | Q50: {q_q:6.1f} u | Gap(V2 - L): {v2_q - l_q:+6.1f} u")

    v2_mv = np.mean([v2_results[s]["moves"] for s in v2_seeds])
    v2_idl = np.mean([v2_results[s]["idle"] for s in v2_seeds])
    v2_prd = np.mean([v2_results[s]["prod"] for s in v2_seeds])
    print(f"  Actions: Movement = {v2_mv:.1f} | Productive = {v2_prd:.1f} | Idle = {v2_idl:.1f}")

    extended_summary = {
        "ci95_q50": ci95_q50,
        "ci99_q50": ci99_q50,
        "ci95_m1": ci95_m1,
        "ci99_m1": ci99_m1,
        "worst_20": worst_20,
        "best_20": best_20,
        "quartile_deltas": {
            "Q1": float(np.mean(diff_l_q50[q1_idx])),
            "Q2": float(np.mean(diff_l_q50[q2_idx])),
            "Q3": float(np.mean(diff_l_q50[q3_idx])),
            "Q4": float(np.mean(diff_l_q50[q4_idx]))
        },
        "v2_gap": float(np.mean(v2_rews - l_sub_rews))
    }

    with open("scratch/extended_holdout_and_v2_summary.json", "w") as f:
        json.dump(extended_summary, f, indent=2)

if __name__ == "__main__":
    main()
