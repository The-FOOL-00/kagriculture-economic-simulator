import json
import numpy as np

with open("scratch/causal_factorial_raw_results.json", "r") as f:
    data = json.load(f)

print(f"Total entries: {len(data)}")

t_keys = {}
for entry in data:
    k = entry.get("t_key", "UNKNOWN")
    if k not in t_keys:
        t_keys[k] = {"scores": [], "margins": [], "wins": []}
    t_keys[k]["scores"].append(entry["final_us"])
    t_keys[k]["margins"].append(entry["margin"])
    t_keys[k]["wins"].append(entry["win"])

print(f"{'Treatment Key':<25} | {'N':<6} | {'Mean Score':<14} | {'Mean Margin':<14} | {'Win Rate':<10}")
print("-" * 75)
for k, v in t_keys.items():
    sc = v["scores"]
    mg = v["margins"]
    wn = v["wins"]
    print(f"{k:<25} | {len(sc):<6} | ${np.mean(sc):<13,.1f} | ${np.mean(mg):<13,.1f} | {np.mean(wn)*100:<9.1f}%")
