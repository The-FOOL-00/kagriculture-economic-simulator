import sys
import os
import json
from collections import defaultdict, Counter
import numpy as np
import kaggle_environments

PROJECT_ROOT = os.path.abspath(".")
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from candidates.candidate_cl_economic_v1 import ClosedLoopEconomicV1
import candidates.slot2_aethel_refined_v2 as v2_mod

def build_daily_divergence(seeds=list(range(1000, 1010))):
    print("Building day-by-day behavioral matrix for CL vs V2 across Seeds 1000-1009...")
    
    cl_daily = defaultdict(lambda: defaultdict(list))
    v2_daily = defaultdict(lambda: defaultdict(list))
    
    for s in seeds:
        cfg = {"episodeSteps": 720, "seed": s}
        
        # 1. Run CL
        env_cl = kaggle_environments.make("kaggriculture", configuration=cfg)
        env_cl.run([ClosedLoopEconomicV1(), "starter"])
        
        # 2. Run V2
        env_v2 = kaggle_environments.make("kaggriculture", configuration=cfg)
        env_v2.run([v2_mod.agent, "starter"])
        
        for agent_label, env_inst, daily_store in [("CL", env_cl, cl_daily), ("V2", env_v2, v2_daily)]:
            steps = env_inst.steps
            
            for step_idx in range(1, len(steps)):
                day = step_idx // 24
                prev_f = steps[step_idx - 1][0]["observation"]["farms"][0]
                act = steps[step_idx][0].get("action") or {}
                all_acts = [act.get("farmer") or ["PASS"]] + (act.get("hands") or [])
                workers = [tuple(prev_f["farmer"])] + [tuple(h) for h in prev_f["hands"]]
                
                # Count actions on this day
                for w_idx, a in enumerate(all_acts):
                    if not a:
                        daily_store[day]["idles"].append(1)
                        continue
                    op = a[0]
                    if op in ("NORTH", "SOUTH", "EAST", "WEST"):
                        daily_store[day]["moves"].append(1)
                    elif op == "WATER":
                        daily_store[day]["waters"].append(1)
                    elif op == "FERTILIZE":
                        daily_store[day]["fert"].append(1)
                    elif op == "PLANT":
                        crop = a[1] if len(a) > 1 else "UNKNOWN"
                        daily_store[day][f"plant_{crop}"].append(1)
                        daily_store[day]["plant_total"].append(1)
                    elif op == "HARVEST":
                        pos = workers[w_idx] if w_idx < len(workers) else (0, 0)
                        t = prev_f["tiles"][pos[1]][pos[0]] if 0 <= pos[1] < 10 and 0 <= pos[0] < 10 else None
                        if isinstance(t, dict):
                            k = t.get("kind")
                            if k == "PLANT":
                                c = t.get("crop", "UNKNOWN")
                                daily_store[day][f"harv_{c}"].append(1)
                            elif k == "PASTURE":
                                an = t.get("animal", "UNKNOWN")
                                daily_store[day][f"harv_{an}"].append(1)
                        daily_store[day]["harv_total"].append(1)
                        
                # Market investments
                m_orders = act.get("market") or []
                for mo in m_orders:
                    if isinstance(mo, list) and len(mo) >= 2:
                        m_type = mo[0]
                        if m_type == "BUY_SEED":
                            daily_store[day]["seed_buys"].append(mo[1])
                        elif m_type == "BUY_ANIMAL":
                            daily_store[day]["animal_buys"].append(mo[1])
                        elif m_type == "BUY_LAND":
                            daily_store[day]["land_buys"].append(1)
                        elif m_type == "HIRE":
                            daily_store[day]["hires"].append(1)

    # Summarize day-by-day
    summary = []
    print("\n" + "="*100)
    print(f"{'Day':<4} | {'CL Plants (W/M/S)':<20} | {'V2 Plants (W/M/S)':<20} | {'CL Harvs':<9} | {'V2 Harvs':<9} | {'CL Seed Buys':<15} | {'V2 Seed Buys':<15}")
    print("-" * 100)
    
    first_divergence_day = None
    
    for day in range(30):
        cl_pw = sum(cl_daily[day]["plant_WHEAT"]) / len(seeds)
        cl_pm = sum(cl_daily[day]["plant_MELON"]) / len(seeds)
        cl_ps = sum(cl_daily[day]["plant_STRAWBERRY"]) / len(seeds)
        
        v2_pw = sum(v2_daily[day]["plant_WHEAT"]) / len(seeds)
        v2_pm = sum(v2_daily[day]["plant_MELON"]) / len(seeds)
        v2_ps = sum(v2_daily[day]["plant_STRAWBERRY"]) / len(seeds)
        
        cl_h = sum(cl_daily[day]["harv_total"]) / len(seeds)
        v2_h = sum(v2_daily[day]["harv_total"]) / len(seeds)
        
        cl_sb = len(cl_daily[day]["seed_buys"]) / len(seeds)
        v2_sb = len(v2_daily[day]["seed_buys"]) / len(seeds)
        
        cl_str = f"{cl_pw:.1f}/{cl_pm:.1f}/{cl_ps:.1f}"
        v2_str = f"{v2_pw:.1f}/{v2_pm:.1f}/{v2_ps:.1f}"
        
        plant_diff = abs((cl_pw + cl_pm + cl_ps) - (v2_pw + v2_pm + v2_ps))
        if plant_diff >= 3.0 and first_divergence_day is None and day > 0:
            first_divergence_day = day
            
        print(f"{day:<4} | {cl_str:<20} | {v2_str:<20} | {cl_h:<9.1f} | {v2_h:<9.1f} | {cl_sb:<15.1f} | {v2_sb:<15.1f}")
        
    print("\nEarliest Day of Material Succession Divergence (plant diff >= 3.0): Day", first_divergence_day)
    return first_divergence_day

if __name__ == "__main__":
    build_daily_divergence()
