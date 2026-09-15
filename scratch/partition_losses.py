import json
from collections import defaultdict

with open('research/shop216_holdout_results.json') as f:
    matches = json.load(f)

seed_matches = defaultdict(dict)
for m in matches:
    seed_matches[m['seed']][m['seat']] = m

print(f"Total unique seeds: {len(seed_matches)}")

# Match-level breakdown:
match_v66_10k = [m for m in matches if m['v66_reward'] - m['shop_reward'] >= 10000]
match_v66_5k = [m for m in matches if m['v66_reward'] - m['shop_reward'] >= 5000]
match_v66_2500 = [m for m in matches if m['v66_reward'] - m['shop_reward'] >= 2500]

print("=== MATCH LEVEL (1,000 matches) ===")
print(f"V66 lead >= 10,000: {len(match_v66_10k)}")
print(f"V66 lead >= 5,000:  {len(match_v66_5k)}")
print(f"V66 lead >= 2,500:  {len(match_v66_2500)}")

# Seed-level breakdown (paired symmetric average)
seed_stats = []
for seed, seats in seed_matches.items():
    s0 = seats[0]
    s1 = seats[1]
    v54_avg = (s0['shop_reward'] + s1['shop_reward']) / 2.0
    v66_avg = (s0['v66_reward'] + s1['v66_reward']) / 2.0
    net_margin = v54_avg - v66_avg # positive = V54++ lead
    v66_lead = v66_avg - v54_avg
    seed_stats.append({
        'seed': seed,
        'v54_avg': v54_avg,
        'v66_avg': v66_avg,
        'net_margin': net_margin,
        'v66_lead': v66_lead,
        'seat0_margin': s0['margin'],
        'seat1_margin': s1['margin'],
        's0': s0,
        's1': s1
    })

seed_v66_10k = [s for s in seed_stats if s['v66_lead'] >= 10000]
seed_v66_5k = [s for s in seed_stats if s['v66_lead'] >= 5000]
seed_v66_2500 = [s for s in seed_stats if s['v66_lead'] >= 2500]
seed_close = [s for s in seed_stats if abs(s['net_margin']) < 2500]
seed_v54_5k = [s for s in seed_stats if s['net_margin'] >= 5000]
seed_v54_10k = [s for s in seed_stats if s['net_margin'] >= 10000]

print("\n=== SEED LEVEL (500 symmetric seeds) ===")
print(f"V66 net lead >= 10,000: {len(seed_v66_10k)}: {[s['seed'] for s in seed_v66_10k]}")
for s in seed_v66_10k:
    print(f"  Seed {s['seed']}: V66 lead = {s['v66_lead']:.2f} (seat0: {s['seat0_margin']}, seat1: {s['seat1_margin']})")

print(f"\nV66 net lead >= 5,000:  {len(seed_v66_5k)}: {[s['seed'] for s in seed_v66_5k]}")
for s in seed_v66_5k:
    print(f"  Seed {s['seed']}: V66 lead = {s['v66_lead']:.2f} (seat0: {s['seat0_margin']}, seat1: {s['seat1_margin']})")

print(f"\nV66 net lead >= 2,500: {len(seed_v66_2500)}")
print(f"Close games (|margin| < 2,500): {len(seed_close)}")
print(f"V54++ net lead >= 2,500: {len([s for s in seed_stats if s['net_margin'] >= 2500])}")
print(f"V54++ net lead >= 5,000: {len(seed_v54_5k)}")
print(f"V54++ net lead >= 10,000: {len(seed_v54_10k)}")
