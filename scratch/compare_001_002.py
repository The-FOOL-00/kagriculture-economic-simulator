import json
import csv

with open('experiments/EXP-DEV-001/EXP-DEV-001_RAW_RESULTS.json', 'r') as f:
    raw_001 = json.load(f)

with open('experiments/EXP-DEV-002/EXP-DEV-002_RAW_RESULTS.json', 'r') as f:
    raw_002 = json.load(f)

v2_001 = {x['seed']: x for x in raw_001['discovery_vs_v2']}
v2_002 = {x['seed']: x for x in raw_002['discovery_vs_v2']}

common_seeds = sorted(list(set(v2_001.keys()) & set(v2_002.keys())))
print(f"Common seeds count: {len(common_seeds)}")

diff_seeds = []
same_seeds = []

print(f"{'Seed':<7} | {'DEV-001':<10} | {'DEV-002':<10} | {'Delta':<10} | {'Mode 001':<10} | {'Mode 002':<10}")
print("-" * 75)

for s in common_seeds:
    m1 = v2_001[s]['paired_margin']
    m2 = v2_002[s]['paired_margin']
    mode1 = v2_001[s].get('cand_mode', 'UNKNOWN')
    mode2 = v2_002[s].get('cand_mode', 'UNKNOWN')
    delta = m2 - m1
    if abs(delta) > 1e-3:
        diff_seeds.append((s, m1, m2, delta, mode1, mode2))
    else:
        same_seeds.append((s, m1, m2, delta, mode1, mode2))
    print(f"{s:<7} | {m1:<+10.2f} | {m2:<+10.2f} | {delta:<+10.2f} | {mode1:<10} | {mode2:<10}")

print(f"\nTotal seeds with non-zero change between DEV-001 and DEV-002: {len(diff_seeds)}")
print(f"Total seeds identical between DEV-001 and DEV-002: {len(same_seeds)}")
for s, m1, m2, d, mod1, mod2 in diff_seeds:
    print(f"Seed {s}: DEV-001={m1:+.1f}, DEV-002={m2:+.1f}, Delta={d:+.1f} (Mode: {mod2})")
