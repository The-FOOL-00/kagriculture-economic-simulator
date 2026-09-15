import sys
import numpy as np
from collections import Counter
from kaggle_environments import make

def run_single(agent_path, seed):
    cfg = {"episodeSteps": 720, "seed": seed}
    env = make("kaggriculture", configuration=cfg, debug=False)
    env.run([agent_path, "starter"])
    steps = env.steps
    r = float(steps[-1][0].reward or 0.0)
    
    # Check key end-of-game statistics
    last_obs = steps[-1][0].get("observation", {})
    last_farm = last_obs.get("farms", [{}])[0]
    last_priv = last_obs.get("private", {})
    
    tiles = last_farm.get("tiles", [])
    crops = Counter()
    animals = Counter()
    for row in tiles:
        for t in row:
            if isinstance(t, dict):
                if t.get("crop"): crops[t["crop"]] += 1
                if t.get("animal"): animals[t["animal"]] += 1
                
    # Count sales by commodity
    sales = Counter()
    for s in steps:
        act = s[0].get("action", {}) or {}
        for o in act.get("market", []):
            if o[0] == "SELL":
                sales[o[1]] += int(o[2])
                
    return r, dict(crops), dict(animals), dict(sales)

seeds = [1000, 1001, 1002, 1003, 1004]
print(f"EVALUATING CL-Economic-V2 vs CL-Economic-V1 vs Frozen V2 on Seeds {seeds}")
print("=" * 75)

v1_scores = []
v2_scores = []
cl2_scores = []

for s in seeds:
    r_v1, c_v1, a_v1, s_v1 = run_single("candidates/candidate_cl_economic_v1.py", s)
    r_cl2, c_cl2, a_cl2, s_cl2 = run_single("candidates/candidate_cl_economic_v2.py", s)
    r_v2, c_v2, a_v2, s_v2 = run_single("candidates/slot2_aethel_refined_v2.py", s)
    
    v1_scores.append(r_v1)
    cl2_scores.append(r_cl2)
    v2_scores.append(r_v2)
    
    print(f"Seed {s}:")
    print(f"  CL-Economic-V1: ${r_v1:,.0f} | Straw sales={s_v1.get('STRAWBERRY', 0)}, Wool={s_v1.get('WOOL', 0)}, Milk={s_v1.get('MILK', 0)}, Fert={s_v1.get('FERTILIZER', 0)}")
    print(f"  CL-Economic-V2: ${r_cl2:,.0f} | Straw sales={s_cl2.get('STRAWBERRY', 0)}, Wool={s_cl2.get('WOOL', 0)}, Milk={s_cl2.get('MILK', 0)}, Fert={s_cl2.get('FERTILIZER', 0)}")
    print(f"  Frozen V2:      ${r_v2:,.0f} | Straw sales={s_v2.get('STRAWBERRY', 0)}, Wool={s_v2.get('WOOL', 0)}, Milk={s_v2.get('MILK', 0)}, Fert={s_v2.get('FERTILIZER', 0)}")
    print(f"  Lift (V2 - V1): ${r_cl2 - r_v1:+,.0f}")
    print("-" * 75)

print("\nSUMMARY (5 SEEDS):")
print(f"CL-Economic-V1 Mean: ${np.mean(v1_scores):,.2f}")
print(f"CL-Economic-V2 Mean: ${np.mean(cl2_scores):,.2f}  (Mean Lift: ${np.mean(cl2_scores) - np.mean(v1_scores):+,.2f})")
print(f"Frozen V2 Mean:      ${np.mean(v2_scores):,.2f}")
