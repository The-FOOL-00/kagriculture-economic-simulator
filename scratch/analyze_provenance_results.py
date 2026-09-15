import json
from collections import defaultdict

with open("scratch/fast_provenance_hits.json", "r", encoding="utf-8") as f:
    data = json.load(f)

hits = data["hits"]
range_hits = data["range_hits"]

print(f"Total individual hits: {len(hits)}")
print(f"Total range hits: {len(range_hits)}")

file_counts = defaultdict(list)
for h in hits:
    file_counts[h["file"]].append(h)

print("\n=== Files with Individual Hits ===")
for f, items in sorted(file_counts.items(), key=lambda x: len(x[1]), reverse=True):
    seeds = sorted(list(set(x["seed"] for x in items)))
    print(f"{f}: {len(items)} hits (unique seeds: {len(seeds)}) -> {seeds[:10]}")

print("\n=== Range Overlap Hits ===")
for rh in range_hits:
    print(f"{rh['file']}:{rh['line']} -> range({rh['start']}, {rh['end']}) | {rh['content'][:80]}")
