import os
import sys
import json
import csv

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(BASE_DIR, "external_repos", "kaggriculture-cppsim"))
sys.path.insert(0, os.path.join(BASE_DIR, "candidates", "closed_loop_architecture"))

import kagsim
from closed_loop_v2 import ClosedLoopAgentV2
from dev_001_dynamic_portfolio import Dev001DynamicPortfolioAgent

raw_path = "experiments/EXP-DEV-001/EXP-DEV-001_RAW_RESULTS.json"
with open(raw_path, "r") as f:
    raw = json.load(f)

v2_runs = {r["seed"]: r for r in raw["discovery_vs_v2"]}

csv_rows = []
behavior_counts = {
    "Identical to V2": 0,
    "Diverged but tied economically": 0,
    "Diverged and won": 0,
    "Diverged and lost": 0,
}

for seed in range(50000, 50050):
    g = kagsim.Game(seed)
    cand = Dev001DynamicPortfolioAgent()
    v2 = ClosedLoopAgentV2()
    
    shops_by_step = {}
    actions_diverged_steps = []
    
    step = 0
    while not g.done:
        o0 = g.observe(0)
        o1 = g.observe(1)
        
        if step in [72, 144, 216, 288, 360, 432, 504, 576]:
            shops_by_step[step] = list(o0.get("town", {}).get("unlocked_shops", []))
            
        a0_cand = cand.act(o0)
        a0_v2 = v2.act(o0)
        
        if a0_cand != a0_v2:
            actions_diverged_steps.append(step)
            
        g.step(a0_cand, a0_cand)
        step += 1
        
    mode = cand.mode_selected.get(0, "STRAWBERRY")
    r = v2_runs[seed]
    margin = r["paired_margin"]
    
    diverged = len(actions_diverged_steps) > 0
    returned_to_v2 = False
    if diverged:
        # Check if the last steps were identical to V2
        last_div = actions_diverged_steps[-1]
        returned_to_v2 = (last_div < 719)
        
    if not diverged:
        behavior = "Identical to V2"
    elif margin == 0:
        behavior = "Diverged but tied economically"
    elif margin > 0:
        behavior = "Diverged and won"
    else:
        behavior = "Diverged and lost"
        
    behavior_counts[behavior] += 1
    
    csv_rows.append({
        "seed": seed,
        "shop_step72": shops_by_step.get(72, [""])[-1] if len(shops_by_step.get(72, [])) > 0 else "",
        "shop_step144": shops_by_step.get(144, [""])[-1] if len(shops_by_step.get(144, [])) > 1 else "",
        "shop_step216": shops_by_step.get(216, [""])[-1] if len(shops_by_step.get(216, [])) > 2 else "",
        "all_8_shops": ";".join(shops_by_step.get(576, [])),
        "treatment_mode": mode,
        "diverged_from_v2": "YES" if diverged else "NO",
        "divergence_step_count": len(actions_diverged_steps),
        "first_divergence_step": actions_diverged_steps[0] if diverged else "N/A",
        "last_divergence_step": actions_diverged_steps[-1] if diverged else "N/A",
        "returned_to_v2_behavior": "YES" if returned_to_v2 else ("N/A" if not diverged else "NO"),
        "paired_margin_vs_v2": margin,
        "classification": behavior,
    })

# Save CSV in experiments/EXP-DEV-001/ and workspace root
fields = [
    "seed", "shop_step72", "shop_step144", "shop_step216", "all_8_shops",
    "treatment_mode", "diverged_from_v2", "divergence_step_count",
    "first_divergence_step", "last_divergence_step", "returned_to_v2_behavior",
    "paired_margin_vs_v2", "classification"
]

csv_path1 = "experiments/EXP-DEV-001/EXP-DEV-001_SHOP_TRAJECTORY_AUDIT.csv"
csv_path2 = "EXP-DEV-001_SHOP_TRAJECTORY_AUDIT.csv"

for p in [csv_path1, csv_path2]:
    with open(p, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(csv_rows)

print("Generated CSV audit files successfully.")
print("\n=== BEHAVIOR SUMMARY TABLE ===")
for b, count in behavior_counts.items():
    print(f"| {b:30s} | {count:2d} | {count/50*100:5.1f}% |")
