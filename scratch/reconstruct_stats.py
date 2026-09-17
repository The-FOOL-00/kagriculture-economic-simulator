import json
import csv
import math
import numpy as np
from scipy import stats

# 1. Load RAW_RESULTS.json
with open("experiments/EXP-AEC-001/RAW_RESULTS.json", "r") as f:
    raw_results = json.load(f)

# 2. Load PAIRED_DELTAS.csv
csv_records = {}
with open("experiments/EXP-AEC-001/PAIRED_DELTAS.csv", "r") as f:
    reader = csv.DictReader(f)
    for row in reader:
        csv_records[int(row["seed"])] = row

# 3. Load SUMMARY.json
with open("experiments/EXP-AEC-001/SUMMARY.json", "r") as f:
    summary_json = json.load(f)

# Reconstruct per-seed table from RAW_RESULTS.json
reconstructed = []
discrepancies = []

treat_wins = 0
ctrl_wins = 0
ties = 0

paired_deltas = []
treat_scores_all = []
ctrl_scores_all = []

for seed in range(340000, 340050):
    seed_str = str(seed)
    s_data = raw_results[seed_str]
    
    m_a = s_data["match_a"]
    m_b = s_data["match_b"]
    
    aec_a = float(m_a["aec_score"])
    v3_a = float(m_a["ctrl_score"])
    delta_a = aec_a - v3_a
    winner_a = "AEC" if delta_a > 0 else ("V3" if delta_a < 0 else "TIE")
    
    aec_b = float(m_b["aec_score"])
    v3_b = float(m_b["ctrl_score"])
    delta_b = aec_b - v3_b
    winner_b = "AEC" if delta_b > 0 else ("V3" if delta_b < 0 else "TIE")
    
    paired_delta = (delta_a + delta_b) / 2.0
    paired_deltas.append(paired_delta)
    
    mean_treat = (aec_a + aec_b) / 2.0
    mean_ctrl = (v3_a + v3_b) / 2.0
    treat_scores_all.append(mean_treat)
    ctrl_scores_all.append(mean_ctrl)
    
    commits_a = sum(m_a.get("commits_by_mechanism", {}).values())
    commits_b = sum(m_b.get("commits_by_mechanism", {}).values())
    total_commits = commits_a + commits_b
    
    for w in (winner_a, winner_b):
        if w == "AEC":
            treat_wins += 1
        elif w == "V3":
            ctrl_wins += 1
        else:
            ties += 1
            
    rec = {
        "seed": seed,
        "aec_score_a": aec_a,
        "v3_score_a": v3_a,
        "delta_a": delta_a,
        "winner_a": winner_a,
        "aec_score_b": aec_b,
        "v3_score_b": v3_b,
        "delta_b": delta_b,
        "winner_b": winner_b,
        "paired_delta": paired_delta,
        "mean_treat": mean_treat,
        "mean_ctrl": mean_ctrl,
        "total_commits": total_commits
    }
    reconstructed.append(rec)
    
    # Check against CSV
    csv_row = csv_records.get(seed)
    if csv_row is None:
        discrepancies.append(f"Seed {seed} missing in CSV")
    else:
        # Compare fields
        csv_delta_a = float(csv_row["delta_margin_a"])
        csv_delta_b = float(csv_row["delta_margin_b"])
        csv_paired_delta = float(csv_row["delta_margin"])
        csv_aec_a = float(csv_row["aec_score_a"])
        csv_v3_a = float(csv_row["ctrl_score_a"])
        csv_aec_b = float(csv_row["aec_score_b"])
        csv_v3_b = float(csv_row["ctrl_score_b"])
        csv_w_a = csv_row["match_a_winner"]
        csv_w_b = csv_row["match_b_winner"]
        csv_commits = int(csv_row["total_commits"])
        
        diffs = []
        if abs(delta_a - csv_delta_a) > 1e-4:
            diffs.append(f"delta_a ({delta_a} vs {csv_delta_a})")
        if abs(delta_b - csv_delta_b) > 1e-4:
            diffs.append(f"delta_b ({delta_b} vs {csv_delta_b})")
        if abs(paired_delta - csv_paired_delta) > 1e-4:
            diffs.append(f"paired_delta ({paired_delta} vs {csv_paired_delta})")
        if abs(aec_a - csv_aec_a) > 1e-4:
            diffs.append(f"aec_a ({aec_a} vs {csv_aec_a})")
        if abs(v3_a - csv_v3_a) > 1e-4:
            diffs.append(f"v3_a ({v3_a} vs {csv_v3_a})")
        if abs(aec_b - csv_aec_b) > 1e-4:
            diffs.append(f"aec_b ({aec_b} vs {csv_aec_b})")
        if abs(v3_b - csv_v3_b) > 1e-4:
            diffs.append(f"v3_b ({v3_b} vs {csv_v3_b})")
        if winner_a != csv_w_a:
            diffs.append(f"winner_a ({winner_a} vs {csv_w_a})")
        if winner_b != csv_w_b:
            diffs.append(f"winner_b ({winner_b} vs {csv_w_b})")
        if total_commits != csv_commits:
            diffs.append(f"commits ({total_commits} vs {csv_commits})")
            
        if diffs:
            discrepancies.append(f"Seed {seed}: " + "; ".join(diffs))

print(f"Total reconstructed seeds: {len(reconstructed)}")
print(f"Discrepancies vs PAIRED_DELTAS.csv: {len(discrepancies)}")
if discrepancies:
    for d in discrepancies[:10]:
        print(" ", d)

# Independent Win-Rate Calculation
total_matches = len(reconstructed) * 2
win_rate_treat = treat_wins / total_matches
win_rate_ctrl = ctrl_wins / total_matches
delta_win_rate_pct = (win_rate_treat - win_rate_ctrl) * 100.0

print("\n--- WIN-RATE RECONSTRUCTION ---")
print(f"Treatment Wins: {treat_wins}")
print(f"Control Wins:   {ctrl_wins}")
print(f"Ties:           {ties}")
print(f"Total Matches:  {total_matches}")
print(f"Treatment Win Rate: {win_rate_treat:.4f}")
print(f"Control Win Rate:   {win_rate_ctrl:.4f}")
print(f"Delta Win Rate (%p): {delta_win_rate_pct:.4f}")

# Independent Statistical Reconstruction
deltas_arr = np.array(paired_deltas, dtype=np.float64)
N = len(deltas_arr)
mean_pd = float(np.mean(deltas_arr))
median_pd = float(np.median(deltas_arr))
std_pd = float(np.std(deltas_arr, ddof=1))
se_pd = std_pd / np.sqrt(N)
p05_pd = float(np.percentile(deltas_arr, 5.0))

# t-test
if std_pd > 0:
    t_stat, t_pval = stats.ttest_1samp(deltas_arr, 0.0)
else:
    t_stat, t_pval = 0.0, 1.0

# wilcoxon
non_zeros = deltas_arr[deltas_arr != 0.0]
if len(non_zeros) > 0:
    try:
        w_res = stats.wilcoxon(deltas_arr, alternative="two-sided")
        w_stat, w_pval = float(w_res.statistic), float(w_res.pvalue)
    except Exception as e:
        w_stat, w_pval = 0.0, 1.0
else:
    w_stat, w_pval = 0.0, 1.0

# bootstrap CI 95%
rng = np.random.default_rng(12345678)
boot_means = [np.mean(rng.choice(deltas_arr, size=N, replace=True)) for _ in range(10000)]
boot_ci_low = float(np.percentile(boot_means, 2.5))
boot_ci_high = float(np.percentile(boot_means, 97.5))

# Student's t CI 95%
t_crit = float(stats.t.ppf(0.975, df=N-1))
t_ci_low = mean_pd - t_crit * se_pd
t_ci_high = mean_pd + t_crit * se_pd

mean_treat_score = float(np.mean(treat_scores_all))
mean_ctrl_score = float(np.mean(ctrl_scores_all))

print("\n--- STATISTICAL RECONSTRUCTION ---")
print(f"Mean Paired Delta:   {mean_pd:.6f} (SUMMARY: {summary_json['mean_delta_margin']})")
print(f"Median Paired Delta: {median_pd:.6f} (SUMMARY: {summary_json['median_delta_margin']})")
print(f"Std Paired Delta:    {std_pd:.6f} (SUMMARY: {summary_json['std_delta_margin']})")
print(f"SE Paired Delta:     {se_pd:.6f} (SUMMARY: {summary_json['se_delta_margin']})")
print(f"5th Percentile:      {p05_pd:.6f} (SUMMARY: {summary_json['percentile_05_delta_margin']})")
print(f"Paired t-test:       t={t_stat:.4f}, p={t_pval:.6f} (SUMMARY: t={summary_json['paired_t_test']['t_statistic']}, p={summary_json['paired_t_test']['p_value']})")
print(f"Wilcoxon:            W={w_stat:.4f}, p={w_pval:.6f} (SUMMARY: W={summary_json['wilcoxon_test']['w_statistic']}, p={summary_json['wilcoxon_test']['p_value']})")
print(f"Bootstrap 95% CI:    [{boot_ci_low:.4f}, {boot_ci_high:.4f}] (SUMMARY: {summary_json['ci95_bootstrap']})")
print(f"Student t 95% CI:    [{t_ci_low:.4f}, {t_ci_high:.4f}] (SUMMARY: {summary_json['ci95_t']})")
print(f"Mean Treatment Score: {mean_treat_score:.2f} (SUMMARY: {summary_json['mean_treatment_score']})")
print(f"Mean Control Score:   {mean_ctrl_score:.2f} (SUMMARY: {summary_json['mean_control_score']})")
