import json
import numpy as np
import scipy.stats as stats

with open('scratch/v2_dmitrii_margin_scan.json', 'r') as f:
    data = json.load(f)

disc_m = np.array(data['disc_margins'])
qual_m = np.array(data['qual_margins'])
hold_m = np.array(data['hold_margins'])

print(f"disc_margins count: {len(disc_m)}")
print(f"qual_margins count: {len(qual_m)}")
print(f"hold_margins count: {len(hold_m)}")

# Also verify that disc_margins matches the sum of seat0 and seat1 for each seed
for partition_name, entries, precalc in [('discovery', data['discovery'], disc_m),
                                         ('qualification', data['qualification'], qual_m),
                                         ('holdout', data['holdout'], hold_m)]:
    by_seed = {}
    for e in entries:
        s = e['seed']
        by_seed.setdefault(s, []).append(e)
    
    computed_margins = []
    for s in sorted(by_seed.keys()):
        pair = by_seed[s]
        assert len(pair) == 2, f"Seed {s} has {len(pair)} entries, expected 2"
        # Check seats
        m_pair = pair[0]['margin'] + pair[1]['margin']
        computed_margins.append(m_pair)
    
    diff = np.max(np.abs(np.array(computed_margins) - precalc))
    print(f"Partition {partition_name}: Max discrepancy between raw match sum and stored margin: {diff}")

def print_stats(name, m):
    n = len(m)
    mean = np.mean(m)
    median = np.median(m)
    std = np.std(m, ddof=1)
    se = std / np.sqrt(n)
    ci95 = [mean - stats.t.ppf(0.975, df=n-1)*se, mean + stats.t.ppf(0.975, df=n-1)*se]
    t = mean / se if se > 0 else 0
    p = 2 * (1 - stats.t.cdf(abs(t), df=n-1))
    wins = np.sum(m > 0)
    losses = np.sum(m < 0)
    ties = np.sum(m == 0)
    
    print(f"\n--- {name} (N={n}) ---")
    print(f"Mean:       {mean:+.2f}")
    print(f"Median:     {median:+.2f}")
    print(f"Std (ddof=1): {std:.2f}")
    print(f"SE:         {se:.2f}")
    print(f"95% CI:     [{ci95[0]:+.2f}, {ci95[1]:+.2f}]")
    print(f"t-statistic: {t:.4f}")
    print(f"p-value:    {p:.4f}")
    print(f"Win Rate:   {wins}/{n} = {wins/n*100:.1f}% ({wins}W - {losses}L - {ties}T)")
    print(f"Min:        {np.min(m):+.1f}")
    print(f"Max:        {np.max(m):+.1f}")

print_stats("Discovery (Seeds 50000-50049)", disc_m)
print_stats("Qualification (Seeds 50050-50099)", qual_m)
print_stats("Holdout (Seeds 50100-50149)", hold_m)

all_m = np.concatenate([disc_m, qual_m, hold_m])
n_total = len(all_m)
mean_tot = np.mean(all_m)
median_tot = np.median(all_m)
std_tot = np.std(all_m, ddof=1)
se_tot = std_tot / np.sqrt(n_total)
ci95_tot = [mean_tot - stats.t.ppf(0.975, df=n_total-1)*se_tot, mean_tot + stats.t.ppf(0.975, df=n_total-1)*se_tot]
t_tot = mean_tot / se_tot
p_tot = 2 * (1 - stats.t.cdf(abs(t_tot), df=n_total-1))
wins_tot = np.sum(all_m > 0)
losses_tot = np.sum(all_m < 0)
ties_tot = np.sum(all_m == 0)

print(f"\n=======================================================")
print(f"COMBINED TOTAL (N={n_total} paired seeds)")
print(f"=======================================================")
print(f"Mean Combined Margin: {mean_tot:+.4f} (Audit 2 reported: +24.61)")
print(f"Median Margin:        {median_tot:+.4f} (Audit 2 reported: +58.00)")
print(f"Standard Deviation:   {std_tot:.4f} (Audit 2 reported: 166.75)")
print(f"Standard Error:       {se_tot:.4f} (Audit 2 reported: 13.61)")
print(f"95% Confidence Int:   [{ci95_tot[0]:+.4f}, {ci95_tot[1]:+.4f}] (Audit 2 reported: [-2.07, +51.30])")
print(f"t-statistic:          {t_tot:.4f} (Audit 2 reported: 1.8078)")
print(f"p-value (two-sided):  {p_tot:.4f} (Audit 2 reported: 0.0726)")
print(f"Win Rate:             {wins_tot/n_total*100:.2f}% ({wins_tot}W - {losses_tot}L - {ties_tot}T) (Audit 2: 54.67%, 82W-68L)")
print(f"Worst Paired Loss:    {np.min(all_m):+.1f} (Audit 2: -730.0)")
print(f"Best Paired Win:      {np.max(all_m):+.1f} (Audit 2: +326.0)")
print(f"Losses > $1000:       {np.sum(all_m < -1000)} / {n_total}")

# Bootstrap CI (100,000 resamples)
np.random.seed(42)
boot_means = [np.mean(np.random.choice(all_m, size=n_total, replace=True)) for _ in range(100000)]
boot_ci95 = np.percentile(boot_means, [2.5, 97.5])
print(f"Bootstrap 95% CI:     [{boot_ci95[0]:+.2f}, {boot_ci95[1]:+.2f}]")

# Cohen's d
cohens_d = mean_tot / std_tot
print(f"Cohen's d:            {cohens_d:.4f}")

# Seed mapping for worst and best
seeds_list = list(range(50000, 50150))
indexed = sorted(zip(seeds_list, all_m), key=lambda x: x[1])
print("\nWorst 5 Paired Seeds:")
for s, m in indexed[:5]:
    print(f"  Seed {s}: {m:+.1f}")

print("\nBest 5 Paired Seeds:")
for s, m in indexed[-5:]:
    print(f"  Seed {s}: {m:+.1f}")

# TOST (Two One-Sided Tests) for Equivalence
for bound in [25.0, 50.0, 75.0, 100.0]:
    t_lower = (mean_tot - (-bound)) / se_tot
    p_lower = 1 - stats.t.cdf(t_lower, df=n_total-1)
    t_upper = (mean_tot - bound) / se_tot
    p_upper = stats.t.cdf(t_upper, df=n_total-1)
    p_tost = max(p_lower, p_upper)
    print(f"TOST Equivalence Margin [{-bound:+.0f}, {+bound:+.0f}]: p_lower={p_lower:.4f}, p_upper={p_upper:.4f}, p_TOST={p_tost:.4f} -> {'EQUIVALENT' if p_tost < 0.05 else 'NOT EQUIVALENT'}")
