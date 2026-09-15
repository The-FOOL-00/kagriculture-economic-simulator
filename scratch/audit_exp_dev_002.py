import json
import csv
import numpy as np
import scipy.stats as stats

# Load EXP-DEV-002 JSON & CSV
with open('experiments/EXP-DEV-002/EXP-DEV-002_RAW_RESULTS.json', 'r') as f:
    raw_002 = json.load(f)

with open('experiments/EXP-DEV-002/EXP-DEV-002_PAIRED_DELTAS.csv', 'r') as f:
    csv_002 = list(csv.DictReader(f))

# Load EXP-DEV-001 JSON & CSV
with open('experiments/EXP-DEV-001/EXP-DEV-001_RAW_RESULTS.json', 'r') as f:
    raw_001 = json.load(f)

with open('experiments/EXP-DEV-001/EXP-DEV-001_PAIRED_DELTAS.csv', 'r') as f:
    csv_001 = list(csv.DictReader(f))

print("=== 1. DATA INTEGRITY & CONSISTENCY ===")
v2_002 = raw_002['discovery_vs_v2']
dmi_002 = raw_002['discovery_vs_dmi']

print(f"Total seeds in DEV-002 vs V2 JSON: {len(v2_002)}")
print(f"Total seeds in DEV-002 vs Dmitrii JSON: {len(dmi_002)}")
print(f"Total rows in DEV-002 CSV: {len(csv_002)}")

seeds_v2 = [x['seed'] for x in v2_002]
seeds_dmi = [x['seed'] for x in dmi_002]
seeds_csv = [int(x['seed']) for x in csv_002]

print(f"Unique seeds V2: {len(set(seeds_v2))}, min={min(seeds_v2)}, max={max(seeds_v2)}")
print(f"Unique seeds Dmi: {len(set(seeds_dmi))}, min={min(seeds_dmi)}, max={max(seeds_dmi)}")
print(f"Unique seeds CSV: {len(set(seeds_csv))}, min={min(seeds_csv)}, max={max(seeds_csv)}")
expected_seeds = list(range(50000, 50050))
print(f"Matches expected 50000..50049: {seeds_v2 == expected_seeds and seeds_dmi == expected_seeds and seeds_csv == expected_seeds}")

# Check seat balance & pairing for every match
seat_balance_clean = True
csv_json_match = True
for i, item in enumerate(v2_002):
    m0 = item['match0']
    m1 = item['match1']
    m0_margin = m0['cand_score'] - m0['opp_score']
    m1_margin = m1['cand_score'] - m1['opp_score']
    paired = m0_margin + m1_margin
    if abs(m0['margin'] - m0_margin) > 1e-6 or abs(m1['margin'] - m1_margin) > 1e-6 or abs(item['paired_margin'] - paired) > 1e-6:
        seat_balance_clean = False
        print(f"Seat balance error on seed {item['seed']}")
    
    # compare with CSV
    csv_row = csv_002[i]
    if int(csv_row['seed']) != item['seed'] or abs(float(csv_row['margin_vs_v2']) - paired) > 1e-6:
        csv_json_match = False
        print(f"CSV mismatch on seed {item['seed']}")

print(f"Seat balance and pairing verified: {seat_balance_clean}")
print(f"CSV vs RAW JSON match verified: {csv_json_match}")

# Recompute statistics vs V2
deltas_v2 = np.array([x['paired_margin'] for x in v2_002], dtype=float)
n = len(deltas_v2)
mean_v2 = np.mean(deltas_v2)
median_v2 = np.median(deltas_v2)
std_v2 = np.std(deltas_v2, ddof=1)
se_v2 = std_v2 / np.sqrt(n)
t_stat = mean_v2 / se_v2 if se_v2 > 0 else 0
p_val = 2 * (1 - stats.t.cdf(abs(t_stat), df=n-1))
ci_low, ci_high = stats.t.interval(0.95, df=n-1, loc=mean_v2, scale=se_v2)

p01 = np.percentile(deltas_v2, 1)
p05 = np.percentile(deltas_v2, 5)
p25 = np.percentile(deltas_v2, 25)
p75 = np.percentile(deltas_v2, 75)
p95 = np.percentile(deltas_v2, 95)
p99 = np.percentile(deltas_v2, 99)

trim10 = stats.trim_mean(deltas_v2, 0.10)
worst_loss = np.min(deltas_v2)
best_win = np.max(deltas_v2)
wins = np.sum(deltas_v2 > 0)
losses = np.sum(deltas_v2 < 0)
ties = np.sum(deltas_v2 == 0)
win_rate = wins / n
loss_rate = losses / n
tie_rate = ties / n
downside_freq = losses / n

print("\n=== 2. INDEPENDENT STATISTICAL RECOMPUTATION (VS V2) ===")
print(f"N: {n}")
print(f"Mean: {mean_v2:.2f}")
print(f"Median: {median_v2:.2f}")
print(f"SD: {std_v2:.2f}")
print(f"SE: {se_v2:.2f}")
print(f"t-statistic: {t_stat:.4f}")
print(f"p-value: {p_val:.4f}")
print(f"95% CI: [{ci_low:.2f}, {ci_high:.2f}]")
print(f"10% Trimmed Mean: {trim10:.2f}")
print(f"Quantiles: p01={p01:.2f}, p05={p05:.2f}, p25={p25:.2f}, p75={p75:.2f}, p95={p95:.2f}, p99={p99:.2f}")
print(f"Worst loss: {worst_loss:.2f}")
print(f"Best win: {best_win:.2f}")
print(f"Wins: {wins} ({win_rate*100:.1f}%), Losses: {losses} ({loss_rate*100:.1f}%), Ties: {ties} ({tie_rate*100:.1f}%)")
print(f"Downside frequency: {downside_freq*100:.1f}% ({losses}/{n})")

# Recompute statistics vs Dmitrii
deltas_dmi = np.array([x['paired_margin'] for x in dmi_002], dtype=float)
mean_dmi = np.mean(deltas_dmi)
median_dmi = np.median(deltas_dmi)
std_dmi = np.std(deltas_dmi, ddof=1)
se_dmi = std_dmi / np.sqrt(len(deltas_dmi))
t_dmi = mean_dmi / se_dmi if se_dmi > 0 else 0
p_dmi = 2 * (1 - stats.t.cdf(abs(t_dmi), df=len(deltas_dmi)-1))
ci_dmi_low, ci_dmi_high = stats.t.interval(0.95, df=len(deltas_dmi)-1, loc=mean_dmi, scale=se_dmi)
wins_dmi = np.sum(deltas_dmi > 0)
losses_dmi = np.sum(deltas_dmi < 0)
ties_dmi = np.sum(deltas_dmi == 0)
wr_dmi = wins_dmi / len(deltas_dmi)

print("\n=== 3. INDEPENDENT STATISTICAL RECOMPUTATION (VS DMITRII) ===")
print(f"N: {len(deltas_dmi)}")
print(f"Mean vs Dmitrii: {mean_dmi:.2f}")
print(f"Median vs Dmitrii: {median_dmi:.2f}")
print(f"SD vs Dmitrii: {std_dmi:.2f}")
print(f"SE vs Dmitrii: {se_dmi:.2f}")
print(f"t-statistic: {t_dmi:.4f}")
print(f"p-value: {p_dmi:.4f}")
print(f"95% CI: [{ci_dmi_low:.2f}, {ci_dmi_high:.2f}]")
print(f"Wins: {wins_dmi} ({wr_dmi*100:.1f}%), Losses: {losses_dmi} ({losses_dmi/len(deltas_dmi)*100:.1f}%), Ties: {ties_dmi} ({ties_dmi/len(deltas_dmi)*100:.1f}%)")
print(f"Worst loss vs Dmitrii: {np.min(deltas_dmi):.2f}")
print(f"Best win vs Dmitrii: {np.max(deltas_dmi):.2f}")

# Outlier sensitivity analysis
print("\n=== 4. OUTLIER SENSITIVITY (DIAGNOSTIC) ===")
# Exclude best seed (Seed 50004)
idx_best = np.argmax(deltas_v2)
best_seed = seeds_v2[idx_best]
deltas_no_best = np.delete(deltas_v2, idx_best)

# Exclude worst seed (Seed 50017)
idx_worst = np.argmin(deltas_v2)
worst_seed = seeds_v2[idx_worst]
deltas_no_worst = np.delete(deltas_v2, idx_worst)

# Exclude both
deltas_no_both = np.delete(deltas_v2, [idx_best, idx_worst])

# Exclude Seed 50018 as well
deltas_no_50018 = np.array([x['paired_margin'] for x in v2_002 if x['seed'] != 50018])
deltas_no_50004_50018 = np.array([x['paired_margin'] for x in v2_002 if x['seed'] not in (50004, 50018)])

print(f"Best seed: {best_seed} (+{deltas_v2[idx_best]:.2f})")
print(f"Worst seed: {worst_seed} ({deltas_v2[idx_worst]:.2f})")
print(f"Seed 50018: {deltas_v2[seeds_v2.index(50018)]:.2f}")

print(f"Mean (Full, n=50): {mean_v2:.2f}")
print(f"Mean (Excluding Best Seed {best_seed}, n=49): {np.mean(deltas_no_best):.2f} (SE: {np.std(deltas_no_best, ddof=1)/np.sqrt(49):.2f}, p: {2*(1-stats.t.cdf(abs(np.mean(deltas_no_best)/(np.std(deltas_no_best, ddof=1)/np.sqrt(49))), df=48)):.4f})")
print(f"Mean (Excluding Worst Seed {worst_seed}, n=49): {np.mean(deltas_no_worst):.2f}")
print(f"Mean (Excluding Both Best & Worst, n=48): {np.mean(deltas_no_both):.2f}")
print(f"Mean (Excluding Seed 50018, n=49): {np.mean(deltas_no_50018):.2f}")
print(f"Mean (Excluding 50004 & 50018, n=48): {np.mean(deltas_no_50004_50018):.2f}")

# Bootstrap CI
np.random.seed(42)
boot_means = [np.mean(np.random.choice(deltas_v2, size=len(deltas_v2), replace=True)) for _ in range(10000)]
boot_ci = np.percentile(boot_means, [2.5, 97.5])
print(f"Bootstrap 95% CI (10k resamples): [{boot_ci[0]:.2f}, {boot_ci[1]:.2f}]")

# Bootstrap without 50004
boot_means_no_best = [np.mean(np.random.choice(deltas_no_best, size=len(deltas_no_best), replace=True)) for _ in range(10000)]
boot_ci_no_best = np.percentile(boot_means_no_best, [2.5, 97.5])
print(f"Bootstrap 95% CI (without Seed 50004): [{boot_ci_no_best[0]:.2f}, {boot_ci_no_best[1]:.2f}]")

# Bootstrap without 50004 and 50018
boot_means_no_two = [np.mean(np.random.choice(deltas_no_50004_50018, size=len(deltas_no_50004_50018), replace=True)) for _ in range(10000)]
boot_ci_no_two = np.percentile(boot_means_no_two, [2.5, 97.5])
print(f"Bootstrap 95% CI (without 50004 & 50018): [{boot_ci_no_two[0]:.2f}, {boot_ci_no_two[1]:.2f}]")
