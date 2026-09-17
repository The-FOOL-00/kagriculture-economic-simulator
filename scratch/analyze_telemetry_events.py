import csv
from collections import Counter

decisions = Counter()
abstain_reasons = Counter()
opp_counts = Counter()
opp_quarantined_counts = Counter()
cand_counts = Counter()
sim_counts = Counter()
patch_committed_counts = Counter()
committed_mechanisms = Counter()

total_rows = 0
opp_positive_rows = 0
cand_positive_rows = 0
sim_positive_rows = 0

events_counter = Counter()

with open("experiments/EXP-AEC-001/TELEMETRY_EVENTS.csv", "r") as f:
    reader = csv.DictReader(f)
    for row in reader:
        total_rows += 1
        decisions[row["decision"]] += 1
        abstain_reasons[row["abstain_reason"]] += 1
        
        opp_c = int(row["opp_count"])
        opp_q_c = int(row["opp_quarantined_count"])
        cand_c = int(row["cand_count"])
        sim_c = int(row["sim_count"])
        patch_comm = int(row["patch_committed"])
        
        opp_counts[opp_c] += 1
        opp_quarantined_counts[opp_q_c] += 1
        cand_counts[cand_c] += 1
        sim_counts[sim_c] += 1
        patch_committed_counts[patch_comm] += 1
        
        if opp_c > 0:
            opp_positive_rows += 1
        if cand_c > 0:
            cand_positive_rows += 1
        if sim_c > 0:
            sim_positive_rows += 1
            
        comm_mech = row["committed_mechanism"]
        if comm_mech:
            committed_mechanisms[comm_mech] += 1
            
        for ev in row["events"].split(";"):
            if ev:
                events_counter[ev] += 1

print(f"Total rows in TELEMETRY_EVENTS.csv: {total_rows}")
print(f"Decisions: {decisions}")
print(f"Abstain reasons: {abstain_reasons}")
print(f"Opp counts distribution: {opp_counts}")
print(f"Opp quarantined counts distribution: {opp_quarantined_counts}")
print(f"Cand counts distribution: {cand_counts}")
print(f"Sim counts distribution: {sim_counts}")
print(f"Patch committed counts: {patch_committed_counts}")
print(f"Committed mechanisms: {committed_mechanisms}")
print(f"Events detected: {events_counter}")
print(f"Rows with opp_count > 0: {opp_positive_rows}")
print(f"Rows with cand_count > 0: {cand_positive_rows}")
print(f"Rows with sim_count > 0: {sim_positive_rows}")
