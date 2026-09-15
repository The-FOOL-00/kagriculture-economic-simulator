import csv

with open('experiments/EXP-DEV-004/PLAN_EVENTS.csv') as f:
    events = list(csv.DictReader(f))

# Group by seed and match
by_seed = {}
for e in events:
    s = int(e['seed'])
    by_seed.setdefault(s, []).append(e)

print(f"Total decision events: {len(events)}")
print(f"Total unique seeds with events: {len(by_seed)}")

switches = []
for s, evs in sorted(by_seed.items()):
    # Each seed has two matches (Match 0 and Match 1), 4 steps each = 8 events
    # Let's inspect Match 0 (first 4) and Match 1 (next 4)
    m0_plans = [e['selected_plan'] for e in evs[:4]]
    m1_plans = [e['selected_plan'] for e in evs[4:]]
    m0_switches = sum(1 for i in range(len(m0_plans)-1) if m0_plans[i] != m0_plans[i+1])
    m1_switches = sum(1 for i in range(len(m1_plans)-1) if m1_plans[i] != m1_plans[i+1])
    if m0_switches > 0 or m1_switches > 0:
        switches.append((s, m0_plans, m1_plans))

print(f"\nSeeds with multi-switch transitions: {len(switches)}")
for s, m0, m1 in switches:
    print(f"Seed {s}: M0: {' -> '.join(m0)} | M1: {' -> '.join(m1)}")
