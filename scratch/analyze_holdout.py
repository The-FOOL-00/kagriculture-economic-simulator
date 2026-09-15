import json
import numpy as np
import scipy.stats as stats

def analyze_holdout():
    with open("scratch/holdout_validation_raw.json") as f:
        data = json.load(f)

    seeds = sorted([int(s) for s in data["Baseline"].keys()])
    n_seeds = len(seeds)
    print("=" * 80)
    print(f"OUT-OF-SAMPLE HOLDOUT VALIDATION (SEEDS 1200-1249, N={n_seeds})")
    print("=" * 80)

    rews_a = np.array([data["Baseline"][str(s)]["reward"] for s in seeds])
    rews_b = np.array([data["Gated_M1"][str(s)]["reward"] for s in seeds])
    diff_rew = rews_b - rews_a

    m_diff = np.mean(diff_rew)
    med_diff = np.median(diff_rew)
    std_diff = np.std(diff_rew, ddof=1)
    se_diff = std_diff / np.sqrt(n_seeds)

    # Bootstrap
    boot_means = [np.mean(np.random.choice(diff_rew, size=len(diff_rew), replace=True)) for _ in range(10000)]
    ci_95 = (np.percentile(boot_means, 2.5), np.percentile(boot_means, 97.5))

    t_stat, p_val = stats.ttest_rel(rews_b, rews_a)
    wins = int(np.sum(diff_rew > 0))
    losses = int(np.sum(diff_rew < 0))

    print(f"Baseline Mean Reward:          ${np.mean(rews_a):>10,.2f}")
    print(f"Gated M1 Mean Reward:          ${np.mean(rews_b):>10,.2f}")
    print(f"Mean Delta Reward (M1 - Base): ${m_diff:>10,.2f}")
    print(f"Median Delta Reward:           ${med_diff:>10,.2f}")
    print(f"Standard Deviation:            ${std_diff:>10,.2f}")
    print(f"Standard Error:                ${se_diff:>10,.2f}")
    print(f"95% Bootstrap CI:              [${ci_95[0]:>8,.2f}, ${ci_95[1]:>8,.2f}]")
    print(f"Paired t-test:                 t = {t_stat:>+.3f}, p = {p_val:.4f}")
    print(f"Win / Loss:                    {wins} Wins ({wins/n_seeds*100:.1f}%) / {losses} Losses")

    # Non-market advantage
    nm_list = []
    for s in seeds:
        b = data["Baseline"][str(s)]
        g = data["Gated_M1"][str(s)]
        nm = (g["fert_rev"] - b["fert_rev"]) + (g["wool_rev"] - b["wool_rev"]) + (g["melon_rev"] - b["melon_rev"]) + (g["wheat_rev"] - b["wheat_rev"]) - (g["total_exp"] - b["total_exp"])
        nm_list.append(nm)
    print(f"Non-Market Advantage:          ${np.mean(nm_list):>10,.2f}")

    # Physical strawberry
    b_sold = np.mean([data["Baseline"][str(s)]["straw_sold"] for s in seeds])
    g_sold = np.mean([data["Gated_M1"][str(s)]["straw_sold"] for s in seeds])
    print(f"Strawberry Sold:               Baseline={b_sold:.2f}u, Gated={g_sold:.2f}u (Delta = {g_sold - b_sold:>+5.2f}u)")

if __name__ == "__main__":
    analyze_holdout()
