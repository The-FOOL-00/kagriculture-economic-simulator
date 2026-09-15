import sys
import os
import json

base_dir = os.path.abspath(".")
sys.path.insert(0, os.path.join(base_dir, "external_repos", "kaggriculture-cppsim"))
sys.path.insert(0, os.path.join(base_dir, "candidates", "closed_loop_architecture"))
sys.path.insert(0, os.path.join(base_dir, "extracted_agents", "dmitrii_lb2800"))

import kagsim
from closed_loop_v2 import ClosedLoopAgentV2
from dev_002_hedged_portfolio import Dev002HedgedPortfolioAgent

def audit_seed(seed):
    print(f"\n==================== DETAILED AUDIT FOR SEED {seed} ====================")
    cand = Dev002HedgedPortfolioAgent()
    ctrl = ClosedLoopAgentV2()

    # Match 0: cand is p0, ctrl is p1
    g0 = kagsim.Game(seed)
    
    cand_tom_buys_m0 = 0
    cand_straw_buys_m0 = 0
    cand_tom_plants_m0 = 0
    cand_straw_plants_m0 = 0
    cand_tom_sales_m0 = 0
    cand_straw_sales_m0 = 0
    cand_tom_revenue_m0 = 0
    cand_straw_revenue_m0 = 0
    
    ctrl_tom_buys_m0 = 0
    ctrl_straw_buys_m0 = 0
    ctrl_straw_sales_m0 = 0
    ctrl_straw_revenue_m0 = 0
    
    shops_unlocked = []
    
    while not g0.done:
        step = g0.observe(0)["step"]
        obs0 = g0.observe(0)
        obs1 = g0.observe(1)
        
        shops = obs0.get("town", {}).get("unlocked_shops", [])
        if len(shops) > len(shops_unlocked):
            shops_unlocked = list(shops)
            print(f"Step {step} (Day {step//24}): Shop unlocked -> {shops_unlocked}")
            
        a0 = cand.act(obs0)
        a1 = ctrl.act(obs1)
        
        # Track market orders for cand
        for m in a0.get("market", []):
            if m[0] == "BUY_SEED":
                if m[1] == "TOMATO":
                    cand_tom_buys_m0 += int(m[2])
                elif m[1] == "STRAWBERRY":
                    cand_straw_buys_m0 += int(m[2])
            elif m[0] == "SELL":
                if m[1] == "TOMATO":
                    cand_tom_sales_m0 += int(m[2])
                elif m[1] == "STRAWBERRY":
                    cand_straw_sales_m0 += int(m[2])
                    
        # Track farmer/hand plants for cand
        if a0.get("farmer") and a0["farmer"][0] == "PLANT":
            if a0["farmer"][1] == "TOMATO":
                cand_tom_plants_m0 += 1
            elif a0["farmer"][1] == "STRAWBERRY":
                cand_straw_plants_m0 += 1
        for h in a0.get("hands", []):
            if h and h[0] == "PLANT":
                if h[1] == "TOMATO":
                    cand_tom_plants_m0 += 1
                elif h[1] == "STRAWBERRY":
                    cand_straw_plants_m0 += 1
                    
        # Track ctrl buys/sells
        for m in a1.get("market", []):
            if m[0] == "BUY_SEED":
                if m[1] == "STRAWBERRY":
                    ctrl_straw_buys_m0 += int(m[2])
            elif m[0] == "SELL":
                if m[1] == "STRAWBERRY":
                    ctrl_straw_sales_m0 += int(m[2])
                    
        g0.step(a0, a1)
        
    r0_cand = g0.reward(0)
    r0_ctrl = g0.reward(1)
    m0_delta = r0_cand - r0_ctrl
    
    # Match 1: ctrl is p0, cand is p1
    g1 = kagsim.Game(seed)
    cand1 = Dev002HedgedPortfolioAgent()
    ctrl1 = ClosedLoopAgentV2()
    
    while not g1.done:
        obs0 = g1.observe(0)
        obs1 = g1.observe(1)
        a0 = ctrl1.act(obs0)
        a1 = cand1.act(obs1)
        g1.step(a0, a1)
        
    r1_ctrl = g1.reward(0)
    r1_cand = g1.reward(1)
    m1_delta = r1_cand - r1_ctrl
    paired_margin = m0_delta + m1_delta
    
    print(f"\nMatch 0: Cand={r0_cand:.1f}, Ctrl={r0_ctrl:.1f}, Delta={m0_delta:.1f}")
    print(f"Match 1: Cand={r1_cand:.1f}, Ctrl={r1_ctrl:.1f}, Delta={m1_delta:.1f}")
    print(f"Total Paired Margin: {paired_margin:.1f}")
    print(f"\nCand Physical Tracking (Match 0):")
    print(f"  Tomato seeds bought: {cand_tom_buys_m0}")
    print(f"  Strawberry seeds bought: {cand_straw_buys_m0}")
    print(f"  Tomato planted: {cand_tom_plants_m0}")
    print(f"  Strawberry planted: {cand_straw_plants_m0}")
    print(f"  Tomato sold: {cand_tom_sales_m0}")
    print(f"  Strawberry sold: {cand_straw_sales_m0}")
    print(f"Ctrl Physical Tracking (Match 0):")
    print(f"  Strawberry seeds bought: {ctrl_straw_buys_m0}")
    print(f"  Strawberry sold: {ctrl_straw_sales_m0}")

audit_seed(50018)
audit_seed(50004)
