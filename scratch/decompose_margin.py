import os
import sys
import json
import numpy as np
from kaggle_environments import make

project_root = r"c:\Users\Sundareswaran\Kagriculture"
apex_path = os.path.join(project_root, "agents", "apex_v2_frozen.py")
ctrl_path = os.path.join(project_root, "agents", "slot4_control_frozen_v2.py")

seeds = [50000 + i for i in range(25)]

epoch_diffs = {
    "Opening (Days 0-2)": [],
    "Early Growth (Days 3-9)": [],
    "First Melon Harvest & Wave-2 (Days 10-13)": [],
    "Livestock Compounding (Days 14-20)": [],
    "Cycle-2 Melons & Endgame (Days 21-29)": []
}

for s in seeds:
    # Run Apex as P0, Ctrl as P1
    env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": s}, debug=False)
    env.run([apex_path, ctrl_path])
    
    steps = env.steps
    # Extract cash at key boundary steps:
    # Day 2 end = step 71
    # Day 9 end = step 239
    # Day 13 end = step 335
    # Day 20 end = step 503
    # Day 29 end = step 719
    
    def get_cash_diff(step_num):
        obs = steps[step_num][0].observation
        farms = obs.get("farms", [])
        c0 = farms[0].get("money", 0.0) if len(farms) > 0 else 0.0
        c1 = farms[1].get("money", 0.0) if len(farms) > 1 else 0.0
        return c0 - c1

    d_d2 = get_cash_diff(71)
    d_d9 = get_cash_diff(239)
    d_d13 = get_cash_diff(335)
    d_d20 = get_cash_diff(503)
    d_d29 = steps[-1][0].reward - steps[-1][1].reward

    # Marginal contributions during each epoch
    e1 = d_d2
    e2 = d_d9 - d_d2
    e3 = d_d13 - d_d9
    e4 = d_d20 - d_d13
    e5 = d_d29 - d_d20

    epoch_diffs["Opening (Days 0-2)"].append(e1)
    epoch_diffs["Early Growth (Days 3-9)"].append(e2)
    epoch_diffs["First Melon Harvest & Wave-2 (Days 10-13)"].append(e3)
    epoch_diffs["Livestock Compounding (Days 14-20)"].append(e4)
    epoch_diffs["Cycle-2 Melons & Endgame (Days 21-29)"].append(e5)

print("=" * 80)
print("PART 10: MARGIN DECOMPOSITION ACROSS GAME EPOCHS (APEX VS CONTROL)")
print("=" * 80)

total_margin = 0.0
for epoch_name, vals in epoch_diffs.items():
    mean_val = float(np.mean(vals))
    total_margin += mean_val
    print(f"{epoch_name:45s} : {mean_val:+7.1f} margin")

print("-" * 80)
print(f"Total Mean Margin Accounted For               : {total_margin:+7.1f}")
print("=" * 80)

with open(os.path.join(project_root, "scratch", "margin_decomposition.json"), "w") as f:
    json.dump({k: float(np.mean(v)) for k, v in epoch_diffs.items()}, f, indent=2)
