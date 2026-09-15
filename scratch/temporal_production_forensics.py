"""
Temporal Production Forensics & Phase Divergence Tracker
Analyzes Day-by-Day Cash & Commodity Curves between CL-Economic-V1 and Frozen V2
"""
import sys
import os
import json
from collections import defaultdict
import numpy as np

PROJECT_ROOT = os.path.abspath(".")
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import kaggle_environments
from candidates.slot2_aethel_refined_v2 import agent as v2_agent
from candidates.candidate_cl_economic_v1 import agent as cl_econ_agent

CHECKPOINT_DAYS = [0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30]

def trace_agent_timeline(agent_fn, agent_name, seeds=[1000, 1001, 1002, 1003, 1004]):
    day_cash = defaultdict(list)
    day_workers = defaultdict(list)
    straw_planted_day = defaultdict(list)
    wheat_planted_day = defaultdict(list)
    sheep_bought_day = defaultdict(list)
    cows_bought_day = defaultdict(list)
    final_rewards = []
    
    for seed in seeds:
        cfg = {"episodeSteps": 720, "seed": seed}
        env = kaggle_environments.make("kaggriculture", configuration=cfg)
        env.run([agent_fn, "starter"])
        steps = env.steps
        
        # Track timeline
        curr_money = 3000.0
        for d in CHECKPOINT_DAYS:
            step_idx = min(d * 24, len(steps) - 1)
            f = steps[step_idx][0]["observation"]["farms"][0]
            day_cash[d].append(float(f["money"]))
            day_workers[d].append(len(f["hands"]) + 1)
            
        final_rewards.append(float(steps[-1][0]["reward"] or 0.0))
        
        # Track actions per day
        straw_p = defaultdict(int)
        wheat_p = defaultdict(int)
        sheep_b = defaultdict(int)
        cow_b = defaultdict(int)
        
        for s_idx in range(1, len(steps)):
            day = (s_idx - 1) // 24
            act = steps[s_idx][0].get("action") or {}
            market = act.get("market") or []
            farmer_act = act.get("farmer") or ["PASS"]
            hands_acts = act.get("hands") or []
            
            for o in market:
                if isinstance(o, list) and len(o) > 1:
                    if o[0] == "BUY_ANIMAL":
                        qty = int(o[2]) if len(o) > 2 else 1
                        if o[1] == "SHEEP": sheep_b[day] += qty
                        elif o[1] == "COW": cow_b[day] += qty
                        
            # Track planting from tile state changes
            prev_tiles = steps[s_idx - 1][0]["observation"]["farms"][0]["tiles"]
            curr_tiles = steps[s_idx][0]["observation"]["farms"][0]["tiles"]
            for r in range(10):
                for c in range(10):
                    pt = prev_tiles[r][c] if isinstance(prev_tiles[r][c], dict) else {}
                    ct = curr_tiles[r][c] if isinstance(curr_tiles[r][c], dict) else {}
                    if not pt.get("crop") and ct.get("crop"):
                        crop = ct["crop"]
                        if crop == "STRAWBERRY": straw_p[day] += 1
                        elif crop == "WHEAT": wheat_p[day] += 1
                        
        for d in range(30):
            straw_planted_day[d].append(straw_p[d])
            wheat_planted_day[d].append(wheat_p[d])
            sheep_bought_day[d].append(sheep_b[d])
            cows_bought_day[d].append(cow_b[d])
            
    return {
        "name": agent_name,
        "mean_final_reward": float(np.mean(final_rewards)),
        "day_cash": {d: float(np.mean(day_cash[d])) for d in CHECKPOINT_DAYS},
        "day_workers": {d: float(np.mean(day_workers[d])) for d in CHECKPOINT_DAYS},
        "straw_planted_day": {d: float(np.mean(straw_planted_day[d])) for d in range(30)},
        "wheat_planted_day": {d: float(np.mean(wheat_planted_day[d])) for d in range(30)},
        "sheep_bought_day": {d: float(np.mean(sheep_bought_day[d])) for d in range(30)},
        "cows_bought_day": {d: float(np.mean(cows_bought_day[d])) for d in range(30)},
    }

if __name__ == "__main__":
    print("Running 5-seed timeline trace for Frozen V2...")
    v2_data = trace_agent_timeline(v2_agent, "Frozen V2")
    print(f"V2 Mean Reward: ${v2_data['mean_final_reward']:,.2f}")
    
    print("Running 5-seed timeline trace for CL-Economic-V1...")
    cl_data = trace_agent_timeline(cl_econ_agent, "CL-Economic-V1")
    print(f"CL Mean Reward: ${cl_data['mean_final_reward']:,.2f}")
    
    print("\n" + "="*80)
    print("DAY-BY-DAY CUMULATIVE CASH CURVE COMPARISON (5 Seeds)")
    print("="*80)
    print(f"{'Day':<6} | {'V2 Cash ($)':<15} | {'CL Cash ($)':<15} | {'Cash Delta (V2 - CL)':<20} | {'V2 Workers':<12} | {'CL Workers':<12}")
    print("-"*80)
    for d in CHECKPOINT_DAYS:
        v_c = v2_data["day_cash"][d]
        c_c = cl_data["day_cash"][d]
        delta = v_c - c_c
        vw = v2_data["day_workers"][d]
        cw = cl_data["day_workers"][d]
        print(f"Day {d:<2} | ${v_c:13,.1f} | ${c_c:13,.1f} | ${delta:+18,.1f} | {vw:10.1f} | {cw:10.1f}")
        
    print("\n" + "="*80)
    print("STRAWBERRY PLANTING DAY DISTRIBUTION")
    print("="*80)
    print(f"{'Day':<6} | {'V2 Planted':<12} | {'CL Planted':<12} | {'V2 Cumul':<12} | {'CL Cumul':<12}")
    print("-"*80)
    v_cum = 0
    c_cum = 0
    for d in range(30):
        vp = v2_data["straw_planted_day"][d]
        cp = cl_data["straw_planted_day"][d]
        v_cum += vp
        c_cum += cp
        if vp > 0 or cp > 0 or d in (4, 8, 10, 12, 14, 16, 18, 20):
            print(f"Day {d:<2} | {vp:10.1f} | {cp:10.1f} | {v_cum:10.1f} | {c_cum:10.1f}")
            
    print("\n" + "="*80)
    print("SHEEP ACQUISITION DAY DISTRIBUTION")
    print("="*80)
    print(f"{'Day':<6} | {'V2 Sheep Bought':<16} | {'CL Sheep Bought':<16}")
    print("-"*80)
    for d in range(30):
        vs = v2_data["sheep_bought_day"][d]
        cs = cl_data["sheep_bought_day"][d]
        if vs > 0 or cs > 0:
            print(f"Day {d:<2} | {vs:14.1f} | {cs:14.1f}")

    print("\n" + "="*80)
    print("WHEAT PLANTING DAY DISTRIBUTION")
    print("="*80)
    print(f"{'Day':<6} | {'V2 Wheat Planted':<16} | {'CL Wheat Planted':<16}")
    print("-"*80)
    for d in range(30):
        vw = v2_data["wheat_planted_day"][d]
        cw = cl_data["wheat_planted_day"][d]
        if vw > 0 or cw > 0:
            print(f"Day {d:<2} | {vw:14.1f} | {cw:14.1f}")
            
    with open("scratch/phase_forensics_summary.json", "w") as f:
        json.dump({"v2": v2_data, "cl": cl_data}, f, indent=2)
    print("\nSaved trace to scratch/phase_forensics_summary.json")
