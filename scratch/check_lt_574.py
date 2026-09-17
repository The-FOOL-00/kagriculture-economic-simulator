import csv
from collections import Counter

events_lt_574 = Counter()
opp_counts_lt_574 = Counter()

with open("experiments/EXP-AEC-001/TELEMETRY_EVENTS.csv", "r") as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row["abstain_reason"] == "NO_FEASIBLE_CANDIDATE_PATCHES":
            step = int(row["step"])
            if step < 574:
                events_lt_574[row["events"]] += 1
                opp_counts_lt_574[int(row["opp_count"])] += 1

print(f"Events for steps < 574 with NO_FEASIBLE_CANDIDATE_PATCHES:")
for ev, cnt in events_lt_574.most_common():
    print(f"  {cnt}: {ev}")
print(f"Opp counts for steps < 574 with NO_FEASIBLE_CANDIDATE_PATCHES: {opp_counts_lt_574}")
