import json
import numpy as np

with open('scratch/v2_dmitrii_margin_scan.json', 'r') as f:
    d = json.load(f)

# Group by seed paired margin first
for part_name, entries in [('discovery', d['discovery']), ('qualification', d['qualification']), ('holdout', d['holdout'])]:
    pass

all_entries = d['discovery'] + d['qualification'] + d['holdout']
# Group by seed
by_seed = {}
for e in all_entries:
    s = e['seed']
    by_seed.setdefault(s, []).append(e)

# Per seed: paired margin, shop_family, shops list
seed_summaries = []
for s, pair in sorted(by_seed.items()):
    paired_margin = pair[0]['margin'] + pair[1]['margin']
    v2_total_cash = pair[0]['v2_cash'] + pair[1]['v2_cash']
    dm_total_cash = pair[0]['dm_cash'] + pair[1]['dm_cash']
    fam = pair[0]['shop_family']
    shops = pair[0]['shops']
    seed_summaries.append({
        'seed': s,
        'margin': paired_margin,
        'v2_cash': v2_total_cash / 2.0,
        'dm_cash': dm_total_cash / 2.0,
        'family': fam,
        'shops': shops
    })

fam_stats = {}
for s in seed_summaries:
    f = s['family']
    fam_stats.setdefault(f, []).append(s)

print(f"{'Shop Family':25s} {'Seeds':>6s} {'Mean Margin':>12s} {'Median':>10s} {'Std':>10s} {'Win Rate':>10s} {'V2 Cash':>12s} {'DM Cash':>12s}")
print("-" * 105)
for f, items in sorted(fam_stats.items()):
    margins = [x['margin'] for x in items]
    v2_cash = [x['v2_cash'] for x in items]
    dm_cash = [x['dm_cash'] for x in items]
    wr = sum(m > 0 for m in margins) / len(margins)
    print(f"{f:25s} {len(items):6d} {np.mean(margins):>+12.2f} {np.median(margins):>+10.2f} {np.std(margins, ddof=1) if len(margins)>1 else 0:>10.2f} {wr*100:>9.1f}% {np.mean(v2_cash):>12.2f} {np.mean(dm_cash):>12.2f}")

# Also check lower tail quantiles across all 150 seeds:
all_m = [x['margin'] for x in seed_summaries]
print("\n--- Empirical Quantiles for Paired Seed Margins (V2 - Dmitrii) ---")
for p in [1, 5, 10, 25, 50, 75, 90, 95, 99]:
    print(f"p{p:02d}: {np.percentile(all_m, p):+8.2f}")
