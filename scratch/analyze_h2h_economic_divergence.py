"""
Head-to-Head Economic Divergence Forensics
Compares transaction-by-transaction market sales, realized prices,
feed competition, and volume when Frozen V2 and CL-Coordinated-V1 share the same board.
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
from candidates.candidate_cl_coordinated_v1 import agent as cl_agent

def analyze_h2h_game(seed=5000, cl_seat=0):
    cfg = {"episodeSteps": 720, "seed": seed}
    env = kaggle_environments.make("kaggriculture", configuration=cfg)
    
    if cl_seat == 0:
        agents = [cl_agent, v2_agent]
        p_cl, p_v2 = 0, 1
    else:
        agents = [v2_agent, cl_agent]
        p_cl, p_v2 = 1, 0
        
    env.run(agents)
    steps = env.steps
    total_steps = len(steps)
    
    cl_sales = defaultdict(lambda: {"units": 0, "rev": 0.0})
    v2_sales = defaultdict(lambda: {"units": 0, "rev": 0.0})
    
    cl_money_hist = [float(s[p_cl]["observation"]["farms"][p_cl]["money"]) for s in steps]
    v2_money_hist = [float(s[p_v2]["observation"]["farms"][p_v2]["money"]) for s in steps]
    
    cl_reward = float(steps[-1][p_cl].get("reward") or 0.0)
    v2_reward = float(steps[-1][p_v2].get("reward") or 0.0)
    
    for s_idx in range(1, total_steps):
        prev_obs = steps[s_idx-1][0]["observation"]
        curr_obs = steps[s_idx][0]["observation"]
        prices = prev_obs.get("market", {}).get("prices", {})
        
        act_cl = steps[s_idx][p_cl].get("action") or {}
        act_v2 = steps[s_idx][p_v2].get("action") or {}
        
        for o in act_cl.get("market", []):
            if o and o[0] == "SELL":
                item = o[1]
                qty = int(o[2]) if len(o) > 2 else 1
                p = float(prices.get(item, 1))
                cl_sales[item]["units"] += qty
                cl_sales[item]["rev"] += p * qty
                
        for o in act_v2.get("market", []):
            if o and o[0] == "SELL":
                item = o[1]
                qty = int(o[2]) if len(o) > 2 else 1
                p = float(prices.get(item, 1))
                v2_sales[item]["units"] += qty
                v2_sales[item]["rev"] += p * qty

    print("=" * 80)
    print(f"DIRECT HEAD-TO-HEAD FORENSICS (Seed {seed}, CL Seat={cl_seat})")
    print("=" * 80)
    print(f"Final Reward:  V2: ${v2_reward:10,.2f}  |  CL: ${cl_reward:10,.2f}  | Margin (CL - V2): ${cl_reward - v2_reward:10,.2f}")
    print("-" * 80)
    print(f"{'PRODUCT':<12} | {'V2 UNITS':<9} | {'V2 REV':<11} | {'V2 PRICE':<9} | {'CL UNITS':<9} | {'CL REV':<11} | {'CL PRICE':<9}")
    print("-" * 80)
    all_items = sorted(set(list(v2_sales.keys()) + list(cl_sales.keys())))
    for it in all_items:
        vu = v2_sales[it]["units"]
        vr = v2_sales[it]["rev"]
        vp = vr / vu if vu > 0 else 0
        cu = cl_sales[it]["units"]
        cr = cl_sales[it]["rev"]
        cp = cr / cu if cu > 0 else 0
        print(f"{it:<12} | {vu:9d} | ${vr:9,.1f} | ${vp:7.1f} | {cu:9d} | ${cr:9,.1f} | ${cp:7.1f}")
    print("=" * 80)

if __name__ == "__main__":
    analyze_h2h_game(seed=5000, cl_seat=0)
    analyze_h2h_game(seed=5000, cl_seat=1)
