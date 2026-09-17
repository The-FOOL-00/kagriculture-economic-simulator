import csv

with open("experiments/EXP-AEC-001/TELEMETRY_EVENTS.csv", "r") as f:
    reader = csv.DictReader(f)
    rows_121 = [r for r in reader if int(r["step"]) == 121]

print(f"Total rows for step 121: {len(rows_121)}")
for r in rows_121[:5]:
    print(r)
