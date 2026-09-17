import csv
from collections import Counter

cand_steps = Counter()
cand_events = Counter()
step_events_map = {}

with open("experiments/EXP-AEC-001/TELEMETRY_EVENTS.csv", "r") as f:
    reader = csv.DictReader(f)
    for row in reader:
        cand_c = int(row["cand_count"])
        if cand_c > 0:
            step = int(row["step"])
            cand_steps[step] += 1
            ev = row["events"]
            cand_events[ev] += 1
            if step not in step_events_map:
                step_events_map[step] = Counter()
            step_events_map[step][ev] += 1

print(f"All steps where cand_count > 0 (total {sum(cand_steps.values())} turns across 100 matches):")
for s in sorted(cand_steps.keys()):
    print(f"Step {s:3d}: count={cand_steps[s]:3d}, events={dict(step_events_map[s])}")
