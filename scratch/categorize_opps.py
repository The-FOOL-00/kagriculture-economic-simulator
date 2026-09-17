import csv
from collections import Counter

# Let's inspect step and event characteristics for all 58,503 opps
opps_by_cat = Counter()

with open("experiments/EXP-AEC-001/TELEMETRY_EVENTS.csv", "r") as f:
    reader = csv.DictReader(f)
    for row in reader:
        opp_c = int(row["opp_count"])
        cand_c = int(row["cand_count"])
        step = int(row["step"])
        ev = row["events"]
        
        if opp_c > 0:
            if step >= 574:
                # Terminal phase shutdown produces opps for infeasible crops (up to 5 crops)
                # But could there also be E1_FARM_OBSTRUCTION (LOCAL_WEED_DIG)?
                if "E1_FARM_OBSTRUCTION" in ev:
                    # Both could be present!
                    opps_by_cat["STEP_GE_574_WITH_E1"] += opp_c
                else:
                    opps_by_cat["PHASE_SHUTDOWN_ONLY"] += opp_c
            else:
                if "E1_FARM_OBSTRUCTION" in ev:
                    opps_by_cat["LOCAL_WEED_DIG_LT_574"] += opp_c
                else:
                    opps_by_cat["FRONTLOAD_ORDERS_LT_574"] += opp_c

for k, v in opps_by_cat.items():
    print(f"  {k}: {v}")
