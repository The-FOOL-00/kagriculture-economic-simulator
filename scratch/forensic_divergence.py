import json
import csv

with open('experiments/EXP-DEV-004/RAW_RESULTS.json') as f:
    results = json.load(f)

print("=== SEEDS WHERE CANDIDATE WAS BASELINE_BACKBONE AND DELTA != 0 ===")
backbone_divergent = []
for r in results:
    if r['match0']['cand_plan'] == 'BASELINE_BACKBONE' and r['paired_mean_delta'] != 0:
        backbone_divergent.append(r)
        print(f"Seed {r['seed']}: delta={r['paired_mean_delta']:.2f}, M0: cand={r['match0']['cand_reward']}, base={r['match0']['base_reward']}, M1: base={r['match1']['base_reward']}, cand={r['match1']['cand_reward']}")

print(f"\nTotal backbone divergent seeds: {len(backbone_divergent)}")

# Inspect PLAN_EVENTS for these seeds
print("\n=== PLAN EVENTS FOR THESE SEEDS ===")
with open('experiments/EXP-DEV-004/PLAN_EVENTS.csv') as f:
    reader = csv.DictReader(f)
    events = list(reader)

for r in backbone_divergent[:5]:
    s = r['seed']
    seed_events = [e for e in events if int(e['seed']) == s]
    print(f"\nSeed {s} events:")
    for e in seed_events:
        print(f"  Step {e['step']}: shops={e['unlocked_shops']}, v_base={e['baseline_value']}, best_cand={e['best_candidate_plan']}, best_delta={e['best_candidate_delta']}, decision={e['decision']}")
