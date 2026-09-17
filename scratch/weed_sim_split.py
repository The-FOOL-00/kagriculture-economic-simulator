import csv

weed_sim_lt_574 = 0
weed_sim_ge_574 = 0

with open("experiments/EXP-AEC-001/TELEMETRY_EVENTS.csv", "r") as f:
    reader = csv.DictReader(f)
    for row in reader:
        cand_c = int(row["cand_count"])
        sim_c = int(row["sim_count"])
        step = int(row["step"])
        ev = row["events"]
        
        if "E1_FARM_OBSTRUCTION" in ev and cand_c > 0:
            if step < 574:
                weed_sim_lt_574 += sim_c
            else:
                weed_sim_ge_574 += sim_c

print(f"LOCAL_WEED_DIG simulations: step < 574: {weed_sim_lt_574}, step >= 574: {weed_sim_ge_574}, Total: {weed_sim_lt_574 + weed_sim_ge_574}")
