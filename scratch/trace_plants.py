import sys, os
sys.path.insert(0, os.path.abspath('.'))
import kaggle_environments
from candidates.candidate_cl_aethel_grandmaster import agent as gm_agent
from candidates.candidate_closed_loop_execution_v1 import agent as v1_agent

def trace_plants(seed=42):
    gm_plants = []
    def wrapped_gm(obs, config=None):
        step = int(obs.get("step", 0) or 0)
        farm = obs["farms"][0]
        act = gm_agent(obs)
        all_ops = [act.get("farmer", ["PASS"])] + (act.get("hands", []) or [])
        for w_i, a in enumerate(all_ops):
            if a and a[0] == "PLANT":
                pos = tuple(farm["farmer"]) if w_i == 0 else tuple(farm["hands"][w_i - 1])
                gm_plants.append((step, step//24, step%24, w_i, a[1], pos))
        return act
    env = kaggle_environments.make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed})
    env.run([wrapped_gm, "starter"])
    
    v1_plants = []
    def wrapped_v1(obs, config=None):
        step = int(obs.get("step", 0) or 0)
        farm = obs["farms"][0]
        act = v1_agent(obs)
        all_ops = [act.get("farmer", ["PASS"])] + (act.get("hands", []) or [])
        for w_i, a in enumerate(all_ops):
            if a and a[0] == "PLANT":
                pos = tuple(farm["farmer"]) if w_i == 0 else tuple(farm["hands"][w_i - 1])
                v1_plants.append((step, step//24, step%24, w_i, a[1], pos))
        return act
    env = kaggle_environments.make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed})
    env.run([wrapped_v1, "starter"])
    
    print(f"Total GM Plants: {len(gm_plants)}")
    print(f"Total V1 Plants: {len(v1_plants)}")
    print("\nFirst 10 GM Plants:")
    for p in gm_plants[:10]:
        print(f"  Step {p[0]:3d} (D{p[1]:02d}:H{p[2]:02d}) W{p[3]}: {p[4]} at {p[5]}")
    print("\nFirst 10 V1 Plants:")
    for p in v1_plants[:10]:
        print(f"  Step {p[0]:3d} (D{p[1]:02d}:H{p[2]:02d}) W{p[3]}: {p[4]} at {p[5]}")
        
    print("\nGM Plants by Day:")
    from collections import Counter
    gm_by_day = Counter(p[1] for p in gm_plants)
    v1_by_day = Counter(p[1] for p in v1_plants)
    for d in range(30):
        if gm_by_day[d] or v1_by_day[d]:
            print(f"  Day {d:02d}: GM={gm_by_day[d]:2d} | V1={v1_by_day[d]:2d}")

if __name__ == "__main__":
    trace_plants()
