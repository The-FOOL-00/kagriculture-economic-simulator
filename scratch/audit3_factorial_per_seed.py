import sys
import os
import json
import numpy as np
from scipy import stats
from concurrent.futures import ProcessPoolExecutor
import kaggle_environments

sys.path.insert(0, os.path.abspath('.'))

from scratch.qualification_counterfactual_suite import (
    BaseQ50Agent,
    U1_SafeWindowUrgencyAgent,
    B1_WeedSuppressionOnlyAgent,
    L_MinimalAgent
)

def run_single(args):
    pol_name, seed = args
    if pol_name == "Raw_Q50":
        agent = BaseQ50Agent(50)
    elif pol_name == "A_only":
        agent = U1_SafeWindowUrgencyAgent(50)
    elif pol_name == "B_only":
        agent = B1_WeedSuppressionOnlyAgent(50)
    elif pol_name == "A_plus_B":
        agent = L_MinimalAgent(50)
    else:
        raise ValueError(f"Unknown policy {pol_name}")

    cfg = {"episodeSteps": 720, "seed": seed}
    env = kaggle_environments.make("kaggriculture", configuration=cfg)
    steps = env.run([agent, "starter"])
    env_rew = float(steps[-1][0]["reward"])
    return pol_name, seed, env_rew

def run_audit3():
    seeds = list(range(1300, 1400))
    policies = ["Raw_Q50", "A_only", "B_only", "A_plus_B"]
    jobs = [(p, s) for p in policies for s in seeds]

    print(f"Running Factorial Evaluation across {len(seeds)} seeds (1300-1399) with 4 arms ({len(jobs)} games total)...", flush=True)

    results = {p: {} for p in policies}
    with ProcessPoolExecutor(max_workers=11) as executor:
        for i, (pol, seed, rew) in enumerate(executor.map(run_single, jobs, chunksize=4)):
            results[pol][seed] = rew
            if (i + 1) % 50 == 0 or (i + 1) == len(jobs):
                print(f"  Progress: {i + 1}/{len(jobs)} completed", flush=True)

    # Compute per-seed interactions
    interactions = []
    per_seed_records = []
    q50_list, a_list, b_list, ab_list = [], [], [], []

    for s in seeds:
        r_q = results["Raw_Q50"][s]
        r_a = results["A_only"][s]
        r_b = results["B_only"][s]
        r_ab = results["A_plus_B"][s]

        # interaction_s = Reward_AB_s - Reward_A_s - Reward_B_s + Reward_Q50_s
        inter_s = r_ab - r_a - r_b + r_q
        interactions.append(inter_s)
        q50_list.append(r_q)
        a_list.append(r_a)
        b_list.append(r_b)
        ab_list.append(r_ab)

        per_seed_records.append({
            "seed": s,
            "q50": r_q,
            "a_only": r_a,
            "b_only": r_b,
            "ab": r_ab,
            "delta_a": r_a - r_q,
            "delta_b": r_b - r_q,
            "delta_ab": r_ab - r_q,
            "linear_sum": (r_a - r_q) + (r_b - r_q),
            "interaction": inter_s
        })

    inter_arr = np.array(interactions)
    n = len(inter_arr)

    mean_inter = float(np.mean(inter_arr))
    med_inter = float(np.median(inter_arr))
    sd_inter = float(np.std(inter_arr, ddof=1))
    min_inter = float(np.min(inter_arr))
    max_inter = float(np.max(inter_arr))

    frac_gt_0 = float(np.mean(inter_arr > 0))
    frac_lt_0 = float(np.mean(inter_arr < 0))
    frac_eq_0 = float(np.mean(inter_arr == 0))

    # Bootstrap CI on interaction_s
    rng = np.random.default_rng(42)
    boot_means = [np.mean(rng.choice(inter_arr, size=n, replace=True)) for _ in range(10000)]
    ci_low = float(np.percentile(boot_means, 2.5))
    ci_high = float(np.percentile(boot_means, 97.5))

    # Paired significance test: H0: interaction_s == 0
    t_stat, p_val_t = stats.ttest_1samp(inter_arr, 0.0)
    w_stat, p_val_w = stats.wilcoxon(inter_arr, alternative='two-sided')

    print("\n" + "=" * 80)
    print("AUDIT 3: TRUE FACTORIAL INTERACTION TEST RESULTS (SEEDS 1300-1399, N=100)")
    print("=" * 80)
    print(f"Mean Interaction:      ${mean_inter:+8.2f}")
    print(f"Median Interaction:    ${med_inter:+8.2f}")
    print(f"Std Dev:               ${sd_inter:8.2f}")
    print(f"95% Bootstrap CI:      [${ci_low:+8.2f}, ${ci_high:+8.2f}]")
    print(f"Fraction > 0:          {frac_gt_0*100:5.1f}%")
    print(f"Fraction < 0:          {frac_lt_0*100:5.1f}%")
    print(f"Fraction == 0:         {frac_eq_0*100:5.1f}%")
    print(f"Minimum Interaction:   ${min_inter:+8.2f}")
    print(f"Maximum Interaction:   ${max_inter:+8.2f}")
    print(f"1-Sample t-test:       t = {t_stat:.4f}, p = {p_val_t:.6f}")
    print(f"Wilcoxon Signed-Rank:  W = {w_stat:.1f}, p = {p_val_w:.6f}")
    print("-" * 80)

    out = {
        "mean_interaction": mean_inter,
        "median_interaction": med_inter,
        "std_dev": sd_inter,
        "ci95": [ci_low, ci_high],
        "fraction_gt_0": frac_gt_0,
        "fraction_lt_0": frac_lt_0,
        "fraction_eq_0": frac_eq_0,
        "minimum": min_inter,
        "maximum": max_inter,
        "t_stat": float(t_stat),
        "p_val_t": float(p_val_t),
        "w_stat": float(w_stat),
        "p_val_w": float(p_val_w),
        "per_seed_data": per_seed_records
    }
    with open("scratch/audit3_per_seed_data.json", "w") as f:
        json.dump(out, f, indent=2)

if __name__ == "__main__":
    run_audit3()
