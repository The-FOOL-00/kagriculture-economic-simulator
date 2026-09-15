import json

raw_path = "experiments/EXP-DEV-001/EXP-DEV-001_RAW_RESULTS.json"

with open(raw_path, "r") as f:
    raw = json.load(f)

v2_runs = raw["discovery_vs_v2"]

print("=== ALL 50 SEEDS VS V2 ===")
wins = []
losses = []
ties = []

for r in v2_runs:
    s = r["seed"]
    pm = r["paired_margin"]
    m0 = r["match0"]["margin"]
    m1 = r["match1"]["margin"]
    if pm > 0:
        wins.append((s, pm, m0, m1))
    elif pm < 0:
        losses.append((s, pm, m0, m1))
    else:
        ties.append(s)

print(f"Wins ({len(wins)}):")
for s, pm, m0, m1 in wins:
    print(f"  Seed {s}: paired={pm} (m0={m0}, m1={m1})")

print(f"Losses ({len(losses)}):")
for s, pm, m0, m1 in losses:
    print(f"  Seed {s}: paired={pm} (m0={m0}, m1={m1})")

print(f"Ties ({len(ties)}):")
print(f"  {ties}")
