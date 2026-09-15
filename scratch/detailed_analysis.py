import json
import csv
import math

with open('experiments/EXP-DEV-004/RAW_RESULTS.json') as f:
    records = json.load(f)

deltas = [r['paired_mean_delta'] for r in records]
n = len(deltas)
sorted_d = sorted(deltas)

mean = sum(deltas) / n
variance = sum((x - mean)**2 for x in deltas) / (n - 1)
sd = math.sqrt(variance)
se = sd / math.sqrt(n)
t_stat = mean / se

# Print all deltas
print("All 50 paired deltas:")
for idx, r in enumerate(records, 1):
    s = r['seed']
    d = r['paired_mean_delta']
    out = r['outcome']
    p0 = r['match0']['cand_plan']
    p1 = r['match1']['cand_plan']
    print(f"[{idx:02d}] Seed {s}: {d:+9.2f} ({out}) | P0: {p0} | P1: {p1}")

print("\n--- Summary Statistics ---")
print(f"N = {n}")
print(f"Mean Paired Delta = {mean:+.2f}")
print(f"Median Paired Delta = {sorted_d[25]:+.2f}")
print(f"Standard Deviation = {sd:.2f}")
print(f"Standard Error = {se:.2f}")
print(f"Student-t = {t_stat:.2f}")
print(f"Min = {min(deltas):+.2f}")
print(f"Max = {max(deltas):+.2f}")
wins = sum(1 for d in deltas if d > 0)
losses = sum(1 for d in deltas if d < 0)
ties = sum(1 for d in deltas if d == 0)
print(f"Wins: {wins} ({wins/n*100:.1f}%)")
print(f"Losses: {losses} ({losses/n*100:.1f}%)")
print(f"Ties: {ties} ({ties/n*100:.1f}%)")

# Trimmed mean (10%)
trimmed = sorted_d[5:45]
print(f"10% Trimmed Mean = {sum(trimmed)/len(trimmed):+.2f}")

# Outlier sensitivities
print(f"Mean excl best: {sum(sorted_d[:-1])/(n-1):+.2f}")
print(f"Mean excl worst: {sum(sorted_d[1:])/(n-1):+.2f}")
print(f"Mean excl top-2: {sum(sorted_d[:-2])/(n-2):+.2f}")

# Concentration
best1 = sorted_d[-1]
best2 = sorted_d[-2]
print(f"Top 1: Seed {records[deltas.index(best1)]['seed']} with {best1:+.2f} ({best1/(n*mean)*100:.2f}% of sum)")
print(f"Top 2: Seed {records[deltas.index(best2)]['seed']} with {best2:+.2f} (Top 2 sum = {best1+best2:+.2f}, {(best1+best2)/(n*mean)*100:.2f}% of sum)")
