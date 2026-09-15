"""
Robustness and Perturbation Evaluation Suite
Tests candidate agents across 4 distinct macroeconomic perturbations:
1. Capital Shock: Starting Money $2,000 (-33% below baseline)
2. Capital Surplus: Starting Money $4,000 (+33% above baseline)
3. Severe Market Price Depression (Melon $120, Strawberry $60, Wool $100)
4. Fast Town Demand Cycle (Town Shop Interval = 2 days instead of 3 days)
"""

import numpy as np
from kaggle_environments import make

PERTURBATIONS = [
    ("Baseline ($3,000)", {}),
    ("Low Capital ($2,000)", {"startingMoney": 2000}),
    ("High Capital ($4,000)", {"startingMoney": 4000}),
    ("Fast Town Demand (2-day)", {"townShopUnlockInterval": 2}),
]

def run_perturbation_tests(agent_path, agent_name, seeds=[1000, 1001, 1002, 1003, 1004]):
    print(f"\nEvaluating Robustness for {agent_name} across {len(seeds)} seeds...")
    for p_name, p_cfg in PERTURBATIONS:
        rewards = []
        for s in seeds:
            cfg = {"episodeSteps": 720, "seed": s}
            cfg.update(p_cfg)
            env = make("kaggriculture", configuration=cfg, debug=False)
            env.run([agent_path, "starter"])
            r = float(env.steps[-1][0].get("reward", 0.0) or 0.0)
            rewards.append(r)
        print(f"  {p_name:25s}: Mean ${np.mean(rewards):10.2f} ± ${np.std(rewards):8.2f} | Med ${np.median(rewards):10.2f}")

if __name__ == "__main__":
    for name, path in [
        ("CL-Economic-V1 (Baseline)", "candidates/candidate_cl_economic_v1.py"),
        ("CL-Dynamic-Land-V2 (Arm E)", "candidates/candidate_cl_dynamic_land_v2.py"),
        ("Frozen V2 (Benchmark)", "candidates/slot2_aethel_refined_v2.py")
    ]:
        run_perturbation_tests(path, name)
