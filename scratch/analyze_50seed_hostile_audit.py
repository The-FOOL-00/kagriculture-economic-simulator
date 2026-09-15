import json
import numpy as np
import scipy.stats as stats

def bootstrap_ci(data, n_boot=10000, ci=0.95):
    boot_means = [np.mean(np.random.choice(data, size=len(data), replace=True)) for _ in range(n_boot)]
    lower = np.percentile(boot_means, (1 - ci) / 2 * 100)
    upper = np.percentile(boot_means, (1 + ci) / 2 * 100)
    return lower, upper

def permutation_test(a, b, n_perm=10000):
    diff = np.array(a) - np.array(b)
    observed_mean = np.mean(diff)
    count = 0
    for _ in range(n_perm):
        signs = np.random.choice([-1, 1], size=len(diff))
        perm_mean = np.mean(diff * signs)
        if abs(perm_mean) >= abs(observed_mean):
            count += 1
    return count / n_perm

def analyze():
    with open("scratch/50seed_hostile_audit_raw.json") as f:
        raw = json.load(f)

    arms = ["A_Baseline", "B_Gated_M1", "C_Prio_M3", "D_Pair_M1_M3"]
    seeds = sorted([int(s) for s in raw["A_Baseline"].keys()])
    n_seeds = len(seeds)

    print("=" * 100)
    print(f"50-SEED MATCHED BENCHMARK (SEEDS 1000-1049, N={n_seeds})")
    print("=" * 100)

    # Summary table of arm means
    metrics_to_show = [
        ("Terminal Reward ($)", "reward", "${:,.1f}"),
        ("Strawberry Harvested (u)", "straw_harvested", "{:.2f}"),
        ("Strawberry Sold (u)", "straw_sold", "{:.2f}"),
        ("Strawberry Rev ($)", "straw_rev", "${:,.1f}"),
        ("Milk Rev ($)", "milk_rev", "${:,.1f}"),
        ("Wool Rev ($)", "wool_rev", "${:,.1f}"),
        ("Melon Rev ($)", "melon_rev", "${:,.1f}"),
        ("Wheat Rev ($)", "wheat_rev", "${:,.1f}"),
        ("Fertilizer Rev ($)", "fert_rev", "${:,.1f}"),
        ("Total Rev ($)", "total_rev", "${:,.1f}"),
        ("Total Exp ($)", "total_exp", "${:,.1f}"),
        ("Max Shed Fill (u)", "max_shed_fill", "{:.1f}"),
        ("Term Shed Inv (u)", "term_shed_inv", "{:.1f}"),
        ("Strawberry Avg P ($)", "straw_avg_p", "${:.1f}"),
        ("Strawberry Min P ($)", "straw_min_p", "${:.1f}"),
    ]

    header = f"{'Metric':<25} | " + " | ".join([f"{arm:>16}" for arm in arms])
    print(header)
    print("-" * len(header))

    arm_means = {}
    for label, key, fmt in metrics_to_show:
        row = [f"{label:<25}"]
        for arm in arms:
            vals = [raw[arm][str(s)][key] for s in seeds]
            m = np.mean(vals)
            arm_means.setdefault(arm, {})[key] = m
            row.append(f"{fmt.format(m):>16}")
        print(" | ".join(row))

    print("\n" + "=" * 100)
    print("PAIRED DELTA ANALYSIS (PRIMARY METRIC: TERMINAL REWARD)")
    print("=" * 100)

    comparisons = [
        ("B_Gated_M1 vs A_Baseline", "B_Gated_M1", "A_Baseline"),
        ("C_Prio_M3 vs A_Baseline", "C_Prio_M3", "A_Baseline"),
        ("D_Pair_M1_M3 vs A_Baseline", "D_Pair_M1_M3", "A_Baseline"),
        ("D_Pair_M1_M3 vs B_Gated_M1", "D_Pair_M1_M3", "B_Gated_M1"),
        ("D_Pair_M1_M3 vs C_Prio_M3", "D_Pair_M1_M3", "C_Prio_M3"),
    ]

    for comp_name, arm1, arm2 in comparisons:
        rew1 = [raw[arm1][str(s)]["reward"] for s in seeds]
        rew2 = [raw[arm2][str(s)]["reward"] for s in seeds]
        diff_rew = np.array(rew1) - np.array(rew2)

        straw1 = [raw[arm1][str(s)]["straw_harvested"] for s in seeds]
        straw2 = [raw[arm2][str(s)]["straw_harvested"] for s in seeds]
        diff_straw = np.array(straw1) - np.array(straw2)

        m_rew = np.mean(diff_rew)
        med_rew = np.median(diff_rew)
        std_rew = np.std(diff_rew, ddof=1)
        ci_low, ci_high = bootstrap_ci(diff_rew)
        t_stat, p_val = stats.ttest_rel(rew1, rew2)
        perm_p = permutation_test(rew1, rew2)

        wins = np.sum(diff_rew > 0)
        losses = np.sum(diff_rew < 0)
        ties = np.sum(diff_rew == 0)
        pct_pos = (wins / n_seeds) * 100

        m_str = np.mean(diff_straw)
        ci_str_low, ci_str_high = bootstrap_ci(diff_straw)

        print(f"\n--- Comparison: {comp_name} ---")
        print(f"  Strawberry Harvest Delta: {m_str:>+6.2f} u (95% CI [{ci_str_low:>+6.2f}, {ci_str_high:>+6.2f}])")
        print(f"  Terminal Reward Delta:    ${m_rew:>+9,.1f}")
        print(f"  Median Reward Delta:      ${med_rew:>+9,.1f}")
        print(f"  Std Deviation:            ${std_rew:>9,.1f}")
        print(f"  95% Bootstrap CI:         [${ci_low:>+9,.1f}, ${ci_high:>+9,.1f}]")
        print(f"  Paired t-test:            t = {t_stat:>+6.3f}, p-value = {p_val:.4f}")
        print(f"  Permutation test p-value: p = {perm_p:.4f}")
        print(f"  Win / Loss / Tie:         {wins} Wins ({pct_pos:.1f}%) / {losses} Losses / {ties} Ties")

    # Reconcile Accounting Bridge for B-A and D-A over all 50 seeds
    print("\n" + "=" * 100)
    print("50-SEED EXACT REWARD BRIDGES (MEANS OVER 50 SEEDS)")
    print("=" * 100)

    for target_arm, name in [("B_Gated_M1", "Gated M1 vs Baseline"), ("D_Pair_M1_M3", "Pair M1+M3 vs Baseline")]:
        d_straw_rev = np.mean([raw[target_arm][str(s)]["straw_rev"] - raw["A_Baseline"][str(s)]["straw_rev"] for s in seeds])
        d_milk_rev = np.mean([raw[target_arm][str(s)]["milk_rev"] - raw["A_Baseline"][str(s)]["milk_rev"] for s in seeds])
        d_wool_rev = np.mean([raw[target_arm][str(s)]["wool_rev"] - raw["A_Baseline"][str(s)]["wool_rev"] for s in seeds])
        d_melon_rev = np.mean([raw[target_arm][str(s)]["melon_rev"] - raw["A_Baseline"][str(s)]["melon_rev"] for s in seeds])
        d_wheat_rev = np.mean([raw[target_arm][str(s)]["wheat_rev"] - raw["A_Baseline"][str(s)]["wheat_rev"] for s in seeds])
        d_fert_rev = np.mean([raw[target_arm][str(s)]["fert_rev"] - raw["A_Baseline"][str(s)]["fert_rev"] for s in seeds])

        d_exp_animals = np.mean([raw[target_arm][str(s)]["exp_animals"] - raw["A_Baseline"][str(s)]["exp_animals"] for s in seeds])
        d_exp_seeds = np.mean([raw[target_arm][str(s)]["exp_seeds"] - raw["A_Baseline"][str(s)]["exp_seeds"] for s in seeds])
        d_exp_feed = np.mean([raw[target_arm][str(s)]["exp_feed"] - raw["A_Baseline"][str(s)]["exp_feed"] for s in seeds])
        d_exp_hires = np.mean([raw[target_arm][str(s)]["exp_hires"] - raw["A_Baseline"][str(s)]["exp_hires"] for s in seeds])

        d_tot_rev = np.mean([raw[target_arm][str(s)]["total_rev"] - raw["A_Baseline"][str(s)]["total_rev"] for s in seeds])
        d_tot_exp = np.mean([raw[target_arm][str(s)]["total_exp"] - raw["A_Baseline"][str(s)]["total_exp"] for s in seeds])
        d_reward = np.mean([raw[target_arm][str(s)]["reward"] - raw["A_Baseline"][str(s)]["reward"] for s in seeds])

        recon = d_tot_rev - d_tot_exp
        resid = d_reward - recon

        print(f"\n--- Accounting Bridge: {name} ---")
        print(f"  Terminal Reward Delta:     ${d_reward:>10,.2f}")
        print(f"  Revenues:")
        print(f"    Strawberry Rev Delta:    ${d_straw_rev:>10,.2f}")
        print(f"    Milk Rev Delta:          ${d_milk_rev:>10,.2f}")
        print(f"    Wool Rev Delta:          ${d_wool_rev:>10,.2f}")
        print(f"    Melon Rev Delta:         ${d_melon_rev:>10,.2f}")
        print(f"    Wheat Rev Delta:         ${d_wheat_rev:>10,.2f}")
        print(f"    Fertilizer Rev Delta:    ${d_fert_rev:>10,.2f}")
        print(f"    Total Revenue Delta:     ${d_tot_rev:>10,.2f}")
        print(f"  Expenditures:")
        print(f"    Animals:                 ${d_exp_animals:>10,.2f}")
        print(f"    Seeds:                   ${d_exp_seeds:>10,.2f}")
        print(f"    Feed:                    ${d_exp_feed:>10,.2f}")
        print(f"    Hires:                   ${d_exp_hires:>10,.2f}")
        print(f"    Total Expenditure Delta: ${d_tot_exp:>10,.2f}")
        print(f"  Reconstructed Delta:       ${recon:>10,.2f}")
        print(f"  Unexplained Residual:      ${resid:>10,.2f}")

if __name__ == "__main__":
    analyze()
