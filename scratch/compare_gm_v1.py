import sys, os
sys.path.insert(0, os.path.abspath('.'))
import kaggle_environments
from candidates.candidate_cl_aethel_grandmaster import agent as gm_agent
from candidates.candidate_closed_loop_execution_v1 import agent as v1_agent
from collections import Counter

def compare_gm_v1(seed=42):
    # Run GM
    gm_acts = []
    def wrapped_gm(obs, config=None):
        act = gm_agent(obs)
        gm_acts.append(act)
        return act
    env = kaggle_environments.make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed})
    env.run([wrapped_gm, "starter"])
    r_gm = env.steps[-1][0]["reward"]
    
    # Run V1
    v1_acts = []
    def wrapped_v1(obs, config=None):
        act = v1_agent(obs)
        v1_acts.append(act)
        return act
    env = kaggle_environments.make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed})
    env.run([wrapped_v1, "starter"])
    r_v1 = env.steps[-1][0]["reward"]
    
    print(f"Seed {seed}: GM Reward = {r_gm}, V1 Reward = {r_v1}")
    
    # Count worker action types
    def count_types(acts):
        cnt = Counter()
        for a in acts:
            f = a.get("farmer", ["PASS"])[0]
            cnt[f] += 1
            for h in a.get("hands", []) or []:
                if h: cnt[h[0]] += 1
        return cnt
        
    cnt_gm = count_types(gm_acts)
    cnt_v1 = count_types(v1_acts)
    
    print("\n--- Worker Operations Comparison ---")
    all_ops = sorted(set(cnt_gm.keys()) | set(cnt_v1.keys()))
    for op in all_ops:
        print(f"  {op:<20}: GM={cnt_gm[op]:>5d} | V1={cnt_v1[op]:>5d} (Delta: {cnt_v1[op] - cnt_gm[op]:>+5d})")

if __name__ == "__main__":
    compare_gm_v1()
