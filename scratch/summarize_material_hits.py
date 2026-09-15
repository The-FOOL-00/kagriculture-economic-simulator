import json

with open("scratch/fast_provenance_hits.json", "r", encoding="utf-8") as f:
    data = json.load(f)

hits = data["hits"]
range_hits = data["range_hits"]

# Group by category/file
material_files = {}
for h in hits:
    f = h["file"]
    if f not in material_files:
        material_files[f] = []
    material_files[f].append(h)

print(f"Total material files with individual seed hits: {len(material_files)}")
for f, items in sorted(material_files.items()):
    print(f"- {f}: {len(items)} hits")
