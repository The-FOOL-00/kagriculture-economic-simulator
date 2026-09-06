import json

with open("scratch/our_submissions_snapshot.json", "r", encoding="utf-8") as f:
    subs = json.load(f)

print(f"Total user submissions: {len(subs)}")
for s in subs:
    print(f"Ref: {s['ref']} | Date: {s['date']} | Status: {s['status']} | Desc: {s['description']}")
