import csv
from collections import Counter

# Let's inspect rows with opp_count > 0
opp_positive_reasons = Counter()
opp_positive_events = Counter()
cand_positive_reasons = Counter()
cand_positive_events = Counter()
sim_positive_reasons = Counter()
sim_positive_steps = Counter()

with open("experiments/EXP-AEC-001/TELEMETRY_EVENTS.csv", "r") as f:
    reader = csv.DictReader(f)
    for row in reader:
        opp_c = int(row["opp_count"])
        cand_c = int(row["cand_count"])
        sim_c = int(row["sim_count"])
        reason = row["abstain_reason"]
        events = row["events"]
        step = int(row["step"])
        
        if opp_c > 0:
            opp_positive_reasons[reason] += 1
            opp_positive_events[events] += 1
            
        if cand_c > 0:
            cand_positive_reasons[reason] += 1
            cand_positive_events[events] += 1
            sim_positive_steps[step] += 1

print(f"When opp_count > 0, abstain reasons: {opp_positive_reasons}")
print(f"When cand_count > 0, abstain reasons: {cand_positive_reasons}")
print(f"Top events when cand_count > 0: {cand_positive_events.most_common(10)}")
print(f"Steps where cand_count > 0: {sorted(sim_positive_steps.items())[:20]}")
