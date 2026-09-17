import csv
from collections import Counter

# Let's aggregate telemetry events data
# We know:
# - E1_FARM_OBSTRUCTION -> LOCAL_WEED_DIG
# - Step >= 574 with NO_FEASIBLE_CANDIDATE_PATCHES -> PHASE_SHUTDOWN (and at step 718, TERMINAL_LIQUIDATION check)
# - Steps < 574 with NO_FEASIBLE_CANDIDATE_PATCHES -> FRONTLOAD_ORDERS (Scenario A false positive)
# - Steps 121, 396, 520, 524, 540, 548 -> FRONTLOAD_ORDERS (Scenario B candidates)
# - All other candidate steps have E1_FARM_OBSTRUCTION -> LOCAL_WEED_DIG candidates

sim_mech_counter = Counter()
cand_by_step = {}

with open("experiments/EXP-AEC-001/TELEMETRY_EVENTS.csv", "r") as f:
    reader = csv.DictReader(f)
    for row in reader:
        cand_c = int(row["cand_count"])
        sim_c = int(row["sim_count"])
        step = int(row["step"])
        ev = row["events"]
        
        if cand_c > 0:
            if "E1_FARM_OBSTRUCTION" in ev:
                sim_mech_counter["LOCAL_WEED_DIG"] += sim_c
            elif step in (121, 396, 520, 524, 540, 548):
                sim_mech_counter["FRONTLOAD_ORDERS"] += sim_c
            else:
                sim_mech_counter[f"OTHER_step_{step}_{ev}"] += sim_c

print("Simulations run by mechanism:")
for m, c in sim_mech_counter.items():
    print(f"  {m}: {c}")

print(f"Total simulations: {sum(sim_mech_counter.values())}")
