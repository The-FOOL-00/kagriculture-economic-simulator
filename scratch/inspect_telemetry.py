import csv
from collections import Counter

# Inspect headers and first few rows of TELEMETRY_EVENTS.csv
with open("experiments/EXP-AEC-001/TELEMETRY_EVENTS.csv", "r") as f:
    reader = csv.reader(f)
    headers = next(reader)
    print("Headers:", headers)
    
    rows = []
    for i, row in enumerate(reader):
        rows.append(row)
        if i >= 20:
            break

print(f"Sample of {len(rows)} rows:")
for r in rows[:5]:
    print(r)
