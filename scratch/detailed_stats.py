import json
import numpy as np
import scipy.stats as stats

raw_path = "experiments/EXP-DEV-001/EXP-DEV-001_RAW_RESULTS.json"
with open(raw_path, "r") as f:
    raw = json.load(f)

v2_runs = raw["discovery_vs_v2"]
dmi_runs = raw["discovery_vs_dmi"]

margins_v2 = np.array([r["paired_margin"] for r in v2_runs])
margins_dmi = np.array([r["paired_margin"] for r in dmi_runs])

def calc_stats(arr, name):
    n = len(arr)
    mean = np.mean(arr)
    median = np.median(arr)
    sd = np.std(arr, ddof=1)
    se = sd / np.sqrt(n)
    t_stat = mean / se
    p_val = 2 * (1 - stats.t.cdf(abs(t_stat), df=n-1))
    ci = [mean - stats.t.ppf(0.975, df=n-1)*se, mean + stats.t.ppf(0.975, df=n-1)*se]
    
    # Bootstrap CI
    np.random.seed(42)
    boot_means = [np.mean(np.random.choice(arr, size=n, replace=True)) for _ in range(10000)]
    boot_ci = [np.percentile(boot_means, 2.5), np.percentile(boot_means, 97.5)]
    
    # Trimmed mean (10% each side = 5 lowest, 5 highest)
    trimmed_mean_10 = stats.trim_mean(arr, 0.10)
    
    quantiles = {
        f"p{int(q*100):02d}": np.percentile(arr, q*100)
        for q in [0.01, 0.05, 0.10, 0.25, 0.50, 0.75, 0.90, 0.95, 0.99]
    }
    
    wins = int(np.sum(arr > 0))
    losses = int(np.sum(arr < 0))
    ties = int(np.sum(arr == 0))
    
    print(f"=== STATISTICS FOR {name} (N={n}) ===")
    print(f"Mean: {mean:.2f}")
    print(f"Median: {median:.2f}")
    print(f"SD: {sd:.2f}")
    print(f"SE: {se:.2f}")
    print(f"t-statistic: {t_stat:.4f}")
    print(f"p-value: {p_val:.6f}")
    print(f"95% Student-t CI: [{ci[0]:.2f}, {ci[1]:.2f}]")
    print(f"95% Bootstrap CI: [{boot_ci[0]:.2f}, {boot_ci[1]:.2f}]")
    print(f"Trimmed Mean (10%): {trimmed_mean_10:.2f}")
    print(f"Wins: {wins}, Losses: {losses}, Ties: {ties}, Win Rate: {wins/n*100:.1f}%")
    print(f"Worst: {np.min(arr):.2f}, Best: {np.max(arr):.2f}")
    print("Quantiles:")
    for k, v in quantiles.items():
        print(f"  {k}: {v:.2f}")
    print()

calc_stats(margins_v2, "TREATMENT VS V2")
calc_stats(margins_dmi, "TREATMENT VS DMITRII")

# Without Seed 50004
v2_no_50004 = np.array([r["paired_margin"] for r in v2_runs if r["seed"] != 50004])
calc_stats(v2_no_50004, "TREATMENT VS V2 (EXCLUDING SEED 50004)")

# Without Seed 50018
v2_no_50018 = np.array([r["paired_margin"] for r in v2_runs if r["seed"] != 50018])
calc_stats(v2_no_50018, "TREATMENT VS V2 (EXCLUDING SEED 50018)")

# Without Both
v2_no_both = np.array([r["paired_margin"] for r in v2_runs if r["seed"] not in (50004, 50018)])
calc_stats(v2_no_both, "TREATMENT VS V2 (EXCLUDING BOTH OUTLIERS)")
