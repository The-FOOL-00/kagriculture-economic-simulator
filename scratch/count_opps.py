import csv
from collections import Counter

# Let's count total opportunities across all 70,800 rows
# Sum of opp_count:
total_actionable_opps = 0
opp_count_by_event_type = Counter()

with open("experiments/EXP-AEC-001/TELEMETRY_EVENTS.csv", "r") as f:
    reader = csv.DictReader(f)
    for row in reader:
        opp_c = int(row["opp_count"])
        cand_c = int(row["cand_count"])
        sim_c = int(row["sim_count"])
        step = int(row["step"])
        ev = row["events"]
        total_actionable_opps += opp_c

print(f"Total actionable opportunities detected across 100 matches: {total_actionable_opps}")
