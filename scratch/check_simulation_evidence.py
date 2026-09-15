import json

with open("scratch/qualification_and_holdout_results.json", "r") as f:
    qdata = json.load(f)

print("Keys in qualification_and_holdout_results.json:", list(qdata.keys()))
for k, v in qdata.items():
    if isinstance(v, list) and len(v) > 0 and isinstance(v[0], dict) and "seed" in v[0]:
        seeds = [x["seed"] for x in v]
        overlap = [s for s in seeds if 50100 <= s <= 50149]
        print(f"  {k}: {len(v)} entries, min={min(seeds)}, max={max(seeds)}, 50100..50149 overlap count={len(overlap)}")
    elif isinstance(v, dict):
        print(f"  {k} (dict keys): {list(v.keys())[:5]}")

with open("scratch/v2_dmitrii_margin_scan.json", "r") as f:
    vdata = json.load(f)

print("\nKeys in v2_dmitrii_margin_scan.json:", list(vdata.keys()))
for k, v in vdata.items():
    if isinstance(v, list) and len(v) > 0 and isinstance(v[0], dict) and "seed" in v[0]:
        seeds = [x["seed"] for x in v]
        overlap = [s for s in seeds if 50100 <= s <= 50149]
        print(f"  {k}: {len(v)} entries, min={min(seeds)}, max={max(seeds)}, 50100..50149 overlap count={len(overlap)}")
