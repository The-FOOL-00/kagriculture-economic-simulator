"""
Analyze Day-by-Day Watering Patterns between CL-Economic-V1 and Frozen V2
"""
import sys
import os
from collections import defaultdict, Counter
import kaggle_environments

PROJECT_ROOT = os.path.abspath(".")
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from candidates.slot2_aethel_refined_v2 import agent as v2
from candidates.candidate_cl_economic_v1 import agent as cl

def get_daily_crops_watered(agent_fn, seed=1000):
    env = kaggle_environments.make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed})
    env.run([agent_fn, "starter"])
    daily = defaultdict(lambda: Counter())
    daily_plant_counts = defaultdict(lambda: Counter())
    
    for s_idx in range(1, len(env.steps)):
        day = (s_idx - 1) // 24
        prev_f = env.steps[s_idx - 1][0]["observation"]["farms"][0]
        act = env.steps[s_idx][0].get("action", {})
        all_acts = [act.get("farmer", [])] + act.get("hands", [])
        workers = [prev_f["farmer"]] + prev_f["hands"]
        
        for w_idx, a in enumerate(all_acts):
            if a and a[0] == "WATER":
                pos = workers[w_idx]
                t = prev_f["tiles"][pos[1]][pos[0]]
                if isinstance(t, dict):
                    daily[day][t.get("crop", "UNKNOWN")] += 1
                    
        if (s_idx % 24) == 23:
            for row in prev_f["tiles"]:
                for t in row:
                    if isinstance(t, dict) and t.get("kind") == "PLANT":
                        daily_plant_counts[day][t.get("crop")] += 1
                        
    return daily, daily_plant_counts

if __name__ == "__main__":
    v2_d, v2_p = get_daily_crops_watered(v2, 1000)
    cl_d, cl_p = get_daily_crops_watered(cl, 1000)
    
    print(f"{'Day':<4} | {'CL Str (W/Tot)':<15} | {'V2 Str (W/Tot)':<15} | {'CL Wht':<8} | {'V2 Wht':<8} | {'CL Mel':<8} | {'V2 Mel':<8}")
    print("-" * 80)
    for d in range(30):
        cl_str_w = cl_d[d]["STRAWBERRY"]
        cl_str_tot = cl_p[d]["STRAWBERRY"]
        v2_str_w = v2_d[d]["STRAWBERRY"]
        v2_str_tot = v2_p[d]["STRAWBERRY"]
        
        cl_wht = cl_d[d]["WHEAT"]
        v2_wht = v2_d[d]["WHEAT"]
        
        cl_mel = cl_d[d]["MELON"]
        v2_mel = v2_d[d]["MELON"]
        
        print(f"{d:4d} | {cl_str_w:2d} / {cl_str_tot:2d}        | {v2_str_w:2d} / {v2_str_tot:2d}        | {cl_wht:8d} | {v2_wht:8d} | {cl_mel:8d} | {v2_mel:8d}")
