import json
import csv
import math
import os

BASE_DIR = r"c:\Users\Sundareswaran\Kagriculture"
QUAL_DIR = os.path.join(BASE_DIR, "experiments", "EXP-DEV-002", "qualification")
RAW_JSON = os.path.join(QUAL_DIR, "QUALIFICATION_RAW_RESULTS.json")
CSV_PATH = os.path.join(QUAL_DIR, "QUALIFICATION_PAIRED_DELTAS.csv")

with open(RAW_JSON, "r", encoding="utf-8") as f:
    raw_data = json.load(f)

# 1. Parse CSV independently
rows = []
with open(CSV_PATH, "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for r in reader:
        rows.append(r)

print(f"Total rows in CSV: {len(rows)}")
assert len(rows) == 50

# 2. Extract paired deltas vs V2
deltas_v2 = [float(r["paired_margin_vs_v2"]) for r in rows]
deltas_dmi = [float(r["paired_margin_vs_dmi"]) for r in rows]
deltas_dev001 = [float(r["dev001_paired_margin_vs_v2"]) for r in rows]
diff_002_001 = [float(r["dev002_minus_dev001"]) for r in rows]
seeds = [int(r["seed"]) for r in rows]

# Verify exact correspondence with raw_data
raw_v2_deltas = [r["paired_margin"] for r in raw_data["results_vs_v2"]]
assert deltas_v2 == raw_v2_deltas, "CSV and JSON deltas vs V2 mismatch!"

# 3. Independent Statistical Computation
n = len(deltas_v2)
mean = sum(deltas_v2) / n
sorted_d = sorted(deltas_v2)
median = sorted_d[n // 2] if n % 2 == 1 else (sorted_d[n // 2 - 1] + sorted_d[n // 2]) / 2.0
var = sum((x - mean) ** 2 for x in deltas_v2) / (n - 1)
sd = math.sqrt(var)
se = sd / math.sqrt(n)
t_stat = mean / se if se > 0 else 0.0

# Student-t critical value for df=49: 2.009575
t_crit = 2.009575
ci_lower = mean - t_crit * se
ci_upper = mean + t_crit * se

# Two-sided p-value using erf approximation
z = abs(t_stat)
p_val = 2.0 * (1.0 - 0.5 * (1.0 + math.erf(z / math.sqrt(2.0))))

# 10% Trimmed Mean
trim_k = int(0.10 * n)  # 5
trimmed = sorted_d[trim_k : n - trim_k]
trimmed_mean = sum(trimmed) / len(trimmed)

def quantile(p, data):
    idx = p * (len(data) - 1)
    low = int(math.floor(idx))
    high = int(math.ceil(idx))
    w = idx - low
    return data[low] * (1.0 - w) + data[high] * w

p01 = quantile(0.01, sorted_d)
p05 = quantile(0.05, sorted_d)
p10 = quantile(0.10, sorted_d)
p25 = quantile(0.25, sorted_d)
p50 = quantile(0.50, sorted_d)
p75 = quantile(0.75, sorted_d)
p90 = quantile(0.90, sorted_d)
p95 = quantile(0.95, sorted_d)
p99 = quantile(0.99, sorted_d)

wins = sum(1 for x in deltas_v2 if x > 0)
losses = sum(1 for x in deltas_v2 if x < 0)
ties = sum(1 for x in deltas_v2 if x == 0)

win_rate = (wins / n) * 100.0
loss_rate = (losses / n) * 100.0
tie_rate = (ties / n) * 100.0
downside_freq = loss_rate

# Tail & Concentration Analysis
total_surplus = sum(deltas_v2)
top1_surplus = sorted_d[-1]
top2_surplus = sorted_d[-2] + sorted_d[-1]
top1_pct = (top1_surplus / total_surplus * 100.0) if total_surplus != 0 else 0.0
top2_pct = (top2_surplus / total_surplus * 100.0) if total_surplus != 0 else 0.0

mean_ex_best = sum(sorted_d[:-1]) / (n - 1)
mean_ex_worst = sum(sorted_d[1:]) / (n - 1)
mean_ex_top2 = sum(sorted_d[:-2]) / (n - 2)

print("\n=== SUMMARY RECOMPUTED STATISTICS ===")
print(f"N: {n}")
print(f"Mean: ${mean:+.2f}")
print(f"Median: ${median:+.2f}")
print(f"10% Trimmed Mean: ${trimmed_mean:+.2f}")
print(f"Standard Deviation (SD): ${sd:.2f}")
print(f"Standard Error (SE): ${se:.2f}")
print(f"t-statistic: {t_stat:.4f}")
print(f"p-value (two-sided): {p_val:.6f}")
print(f"95% CI: [${ci_lower:+.2f}, ${ci_upper:+.2f}]")
print(f"Min (Worst Loss): ${sorted_d[0]:+.2f}")
print(f"Max (Best Win): ${sorted_d[-1]:+.2f}")
print(f"Quantiles: p01=${p01:+.2f}, p05=${p05:+.2f}, p10=${p10:+.2f}, p25=${p25:+.2f}, p50=${p50:+.2f}, p75=${p75:+.2f}, p90=${p90:+.2f}, p95=${p95:+.2f}, p99=${p99:+.2f}")
print(f"Records: {wins} Wins ({win_rate:.1f}%), {losses} Losses ({loss_rate:.1f}%), {ties} Ties ({tie_rate:.1f}%)")
print(f"Downside Frequency (< $0): {downside_freq:.1f}%")
print(f"Total Surplus: ${total_surplus:+.2f}")
print(f"Top-1 Contribution: ${top1_surplus:+.2f} ({top1_pct:.1f}%)")
print(f"Top-2 Contribution: ${top2_surplus:+.2f} ({top2_pct:.1f}%)")
print(f"Mean Ex-Best: ${mean_ex_best:+.2f}")
print(f"Mean Ex-Worst: ${mean_ex_worst:+.2f}")
print(f"Mean Ex-Top2: ${mean_ex_top2:+.2f}")

# 4. Dmitrii Statistics
mean_dmi = sum(deltas_dmi) / n
sd_dmi = math.sqrt(sum((x - mean_dmi) ** 2 for x in deltas_dmi) / (n - 1))
se_dmi = sd_dmi / math.sqrt(n)
t_dmi = mean_dmi / se_dmi if se_dmi > 0 else 0
wins_dmi = sum(1 for x in deltas_dmi if x > 0)
losses_dmi = sum(1 for x in deltas_dmi if x < 0)
ties_dmi = sum(1 for x in deltas_dmi if x == 0)
print(f"\n=== REFERENCE COMPARISON VS DMITRII-LB2800 ===")
print(f"Mean Margin vs Dmi: ${mean_dmi:+.2f}")
print(f"SD: ${sd_dmi:.2f}, SE: ${se_dmi:.2f}, t: {t_dmi:.4f}")
print(f"Record vs Dmi: {wins_dmi}W - {losses_dmi}L - {ties_dmi}T (Win Rate: {wins_dmi/n*100:.1f}%)")

# 5. DEV-001 Comparison Statistics
mean_dev001 = sum(deltas_dev001) / n
mean_diff = sum(diff_002_001) / n
sd_diff = math.sqrt(sum((x - mean_diff) ** 2 for x in diff_002_001) / (n - 1))
se_diff = sd_diff / math.sqrt(n)
t_diff = mean_diff / se_diff if se_diff > 0 else 0
worst_loss_001 = min(deltas_dev001)
worst_loss_002 = min(deltas_v2)
print(f"\n=== COMPARISON WITH DEV-001 ===")
print(f"Mean DEV-001 Margin vs V2: ${mean_dev001:+.2f} (Worst Loss: ${worst_loss_001:+.2f})")
print(f"Mean DEV-002 Margin vs V2: ${mean:+.2f} (Worst Loss: ${worst_loss_002:+.2f})")
print(f"Mean Difference (DEV-002 - DEV-001): ${mean_diff:+.2f} (SE: ${se_diff:.2f}, t: {t_diff:.4f})")

# 6. Detailed per-seed breakdown of non-zero deltas
print("\n=== NON-ZERO DELTA SEEDS ===")
for r in rows:
    m = float(r["paired_margin_vs_v2"])
    if m != 0:
        print(f"Seed {r['seed']}: Margin vs V2 = ${m:+.2f}, DEV-001 = ${float(r['dev001_paired_margin_vs_v2']):+.2f}, Mode = {r['cand_mode']}, Shops = {r['unlocked_shops']}")
