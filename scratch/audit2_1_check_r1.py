import json
import numpy as np

with open('scratch/true_pizza_sweep_results.json', 'r') as f:
    sweep_data = json.load(f)

print(f"Total sweep configurations: {len(sweep_data)}")
for i, r in enumerate(sweep_data):
    print(f"{i+1:2d}: tiles={r.get('tiles')}, cohorts={r.get('cohorts')}, cash={r.get('cash'):.2f}, margin={r.get('margin'):.2f}, delta_v2={r.get('delta_v2'):.2f}")

all_deltas = [r['delta_v2'] for r in sweep_data]
print("All deltas < 0?", all(d < 0 for d in all_deltas))
print(f"Max delta_v2: {max(all_deltas):.2f}")
print(f"Min delta_v2: {min(all_deltas):.2f}")
print(f"Mean delta_v2: {np.mean(all_deltas):.2f}")
