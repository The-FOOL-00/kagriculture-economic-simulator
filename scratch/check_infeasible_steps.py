import csv
from collections import Counter

step_counts = Counter()

with open("experiments/EXP-AEC-001/TELEMETRY_EVENTS.csv", "r") as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row["abstain_reason"] == "NO_FEASIBLE_CANDIDATE_PATCHES":
            step = int(row["step"])
            step_counts[step] += 1

print(f"Total NO_FEASIBLE_CANDIDATE_PATCHES: {sum(step_counts.values())}")
print(f"Min step: {min(step_counts.keys())}, Max step: {max(step_counts.keys())}")
print(f"Number of unique steps: {len(step_counts)}")
print(f"Step >= 574 count: {sum(cnt for s, cnt in step_counts.items() if s >= 574)}")
print(f"Step < 574 count: {sum(cnt for s, cnt in step_counts.items() if s < 574)}")
if any(s < 574 for s in step_counts.keys()):
    print("Steps < 574:", sorted([s for s in step_counts.keys() if s < 574]))
