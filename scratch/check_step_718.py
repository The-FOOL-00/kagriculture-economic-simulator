import csv

with open("experiments/EXP-AEC-001/TELEMETRY_EVENTS.csv", "r") as f:
    reader = csv.DictReader(f)
    rows_718 = [r for r in reader if int(r["step"]) == 718]

print(f"Total rows for step 718: {len(rows_718)}")
if rows_718:
    print("Sample step 718 row:")
    for k, v in rows_718[0].items():
        print(f"  {k}: {v}")
    
    # Check distinct values across all 718 rows
    reasons = set(r["abstain_reason"] for r in rows_718)
    opps = set(r["opp_count"] for r in rows_718)
    cands = set(r["cand_count"] for r in rows_718)
    print(f"Abstain reasons at step 718: {reasons}")
    print(f"Opp counts at step 718: {opps}")
    print(f"Cand counts at step 718: {cands}")
