import os, sys, importlib.util
base_dir = r"c:\Users\Sundareswaran\Kagriculture"
sys.path.insert(0, os.path.join(base_dir, "external_repos", "kaggriculture-cppsim"))
sys.path.insert(0, os.path.join(base_dir, "candidates", "closed_loop_architecture"))

import kagsim
import pandas as pd

pe = pd.read_csv('experiments/EXP-DEV-004/PLAN_EVENTS.csv')
pe['match'] = [0 if i % 8 < 4 else 1 for i in range(len(pe))]

for s in [246028, 246005, 246022, 246030, 246007]:
    sub = pe[(pe['seed'] == s) & (pe['match'] == 0)]
    print(f"\n=== Seed {s} ===")
    for _, row in sub.iterrows():
        print(f"Step {row['step']:3d}: shops={row['unlocked_shops']} | cash={row['cash']:7.1f} | best={row['best_candidate_plan']} | delta={row['best_candidate_delta']:7.1f} | sel={row['selected_plan']}")
