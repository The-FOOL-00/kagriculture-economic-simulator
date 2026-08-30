"""
Mechanics, Sweeps, Hardcoding, and Subsystem Forensics
(Parts 14, 15, 16, 17, 18, 19, 20, 21, 22, 23)
"""

import os
import sys
import math
import json
import importlib.util
import numpy as np
from kaggle_environments import make

project_root = r"c:\Users\Sundareswaran\Kagriculture"
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def load_module_from_path(module_name, file_path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = mod
    spec.loader.exec_module(mod)
    return mod

hybrid_mod = load_module_from_path("hybrid_agent_module", os.path.join(project_root, "agents/hybrid_6c3s_10m.py"))
Hybrid6C3S10MAgent = hybrid_mod.Hybrid6C3S10MAgent

# 1. Part 14: Market Execution & Batch Size Testing
def test_market_batch_sizes(seeds=[10001, 10002, 10003, 10004, 10005]):
    print("\n" + "="*80)
    print("PART 14 — VERIFYING MARKET EXECUTION & BATCH SIZES (1, 5, 10, 14, 25, 50, ALL)")
    print("="*80)
    
    batch_sizes = [1, 5, 10, 14, 25, 50, 999]
    print(f"{'Batch Size':12} | {'Mean Cash':12} | {'Median Cash':12} | {'Std Dev':10}")
    print("-" * 55)
    
    for bs in batch_sizes:
        cashes = []
        for s in seeds:
            agent_inst = Hybrid6C3S10MAgent(sell_batch=bs)
            env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": s}, debug=False)
            env.run([agent_inst, "starter"])
            cashes.append(env.steps[-1][0].reward)
        label = f"{bs} units" if bs < 999 else "ALL (Unbounded)"
        print(f"{label:12} | ${np.mean(cashes):10,.2f} | ${np.median(cashes):10,.2f} | ${np.std(cashes):8,.2f}")

# 2. Part 16: Fertilizer Policy Verification
def test_fertilizer_policy(seeds=[10001, 10002, 10003, 10004, 10005]):
    print("\n" + "="*80)
    print("PART 16 — VERIFYING FERTILIZER POLICY (SELL DIRECT VS APPLY TO MELONS)")
    print("="*80)
    
    # 1. Sell direct (use_fert=False)
    cashes_sell = []
    for s in seeds:
        agent_inst = Hybrid6C3S10MAgent(use_fert=False)
        env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": s}, debug=False)
        env.run([agent_inst, "starter"])
        cashes_sell.append(env.steps[-1][0].reward)
        
    # 2. Apply on Melons (use_fert=True)
    cashes_apply = []
    for s in seeds:
        agent_inst = Hybrid6C3S10MAgent(use_fert=True)
        env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": s}, debug=False)
        env.run([agent_inst, "starter"])
        cashes_apply.append(env.steps[-1][0].reward)
        
    print(f"Policy: Sell Fertilizer Direct  -> Mean: ${np.mean(cashes_sell):10,.2f} | Median: ${np.median(cashes_sell):10,.2f}")
    print(f"Policy: Apply Fert on Melons    -> Mean: ${np.mean(cashes_apply):10,.2f} | Median: ${np.median(cashes_apply):10,.2f}")
    print(f"Delta (Apply - Sell Direct):       ${np.mean(cashes_apply) - np.mean(cashes_sell):+10,.2f}")

# 3. Part 17: Melon Tile Count Parameter Sweep
def test_melon_sweep(seeds=[10001, 10002, 10003, 10004, 10005]):
    print("\n" + "="*80)
    print("PART 17 — VERIFYING MELON TILE PARAMETER SWEEP (5, 8, 10, 12, 15, 20, 25)")
    print("="*80)
    
    melon_counts = [5, 8, 10, 12, 15, 20, 25]
    print(f"{'Melon Tiles':12} | {'Mean Cash':12} | {'Median Cash':12} | {'Std Dev':10}")
    print("-" * 55)
    
    for mc in melon_counts:
        cashes = []
        for s in seeds:
            agent_inst = Hybrid6C3S10MAgent(target_melons=mc)
            env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": s}, debug=False)
            env.run([agent_inst, "starter"])
            cashes.append(env.steps[-1][0].reward)
        print(f"{mc:12d} | ${np.mean(cashes):10,.2f} | ${np.median(cashes):10,.2f} | ${np.std(cashes):8,.2f}")

# 4. Part 18: Herd Ratio Parameter Sweep
def test_herd_ratios(seeds=[10001, 10002, 10003, 10004, 10005]):
    print("\n" + "="*80)
    print("PART 18 — HERD RATIO PARAMETER SWEEP (COWS: 4-8, SHEEP: 0-4, GEESE: 0-2)")
    print("="*80)
    
    configs = [
        (4, 0, 0), (4, 2, 0),
        (6, 0, 0), (6, 2, 0), (6, 3, 0), (6, 4, 0), (6, 3, 1),
        (8, 0, 0), (8, 2, 0), (8, 4, 0), (8, 4, 2),
    ]
    
    print(f"{'Herd Config (C/S/G)':22} | {'Mean Cash':12} | {'Median Cash':12} | {'Std Dev':10}")
    print("-" * 65)
    
    for c, s, g in configs:
        cashes = []
        for seed in seeds:
            agent_inst = Hybrid6C3S10MAgent(target_cows=c, target_sheep=s, target_geese=g)
            env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed}, debug=False)
            env.run([agent_inst, "starter"])
            cashes.append(env.steps[-1][0].reward)
        lbl = f"{c} Cows, {s} Sheep, {g} Geese"
        print(f"{lbl:22} | ${np.mean(cashes):10,.2f} | ${np.median(cashes):10,.2f} | ${np.std(cashes):8,.2f}")

# 5. Part 19: Endgame Trace (Steps 700-719)
def test_endgame_trace(seed=10001):
    print("\n" + "="*80)
    print(f"PART 19 — VERIFYING ENDGAME LOGIC (STEPS 700-719 FOR SEED {seed})")
    print("="*80)
    env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed}, debug=False)
    env.run(["agents/hybrid_6c3s_10m.py", "starter"])
    
    print(f"{'Step':5} | {'Day':4} | {'Hour':4} | {'Money':11} | {'Shed Inv':35} | {'Market Orders'}")
    print("-" * 90)
    for step_num in range(700, 720):
        s = env.steps[step_num][0]
        obs = s.get("observation", {})
        act = s.get("action", {})
        farms = obs.get("farms", [{}])
        money = farms[0].get("money", 0.0) if farms else 0.0
        private = obs.get("private", {}) or {}
        shed = private.get("shed", {})
        orders = act.get("market", [])
        day = step_num // 24
        hr = step_num % 24
        shed_str = ", ".join(f"{k}:{v}" for k,v in shed.items() if v > 0) or "EMPTY"
        print(f"{step_num:5d} | {day:4d} | {hr:4d} | ${money:9,.2f} | {shed_str:35} | {orders}")

# 6. Part 21: Dynamic Allocator Synthetic State Test (State A vs State B)
def test_dynamic_allocator():
    print("\n" + "="*80)
    print("PART 21 — DYNAMIC ALLOCATOR SYNTHETIC STATES (STATE A: MELON BOOM vs STATE B: MELON GLUT)")
    print("="*80)
    try:
        from engine.dynamic_allocator import DynamicEconomicAllocator
        allocator = DynamicEconomicAllocator()
        
        # State A: Melon price high ($300), high demand
        state_a = {
            "day": 0, "money": 3000,
            "market_prices": {"MELON": 300, "CARROT": 35, "WHEAT": 25, "MILK": 160, "WOOL": 200},
            "market_inventory": {"MELON": 5000, "CARROT": 10000, "WHEAT": 10000},
            "opp_crops": {"CARROT": 15, "MELON": 0}
        }
        dec_a = allocator.allocate_portfolio(state_a)
        
        # State B: Melon price crashed ($50), market flooded (inv 25000)
        state_b = {
            "day": 0, "money": 3000,
            "market_prices": {"MELON": 50, "CARROT": 35, "WHEAT": 25, "MILK": 160, "WOOL": 200},
            "market_inventory": {"MELON": 25000, "CARROT": 10000, "WHEAT": 10000},
            "opp_crops": {"MELON": 25, "CARROT": 0}
        }
        dec_b = allocator.allocate_portfolio(state_b)
        
        print("State A Allocation (Melon Boom):", dec_a)
        print("State B Allocation (Melon Glut):", dec_b)
        if dec_a != dec_b:
            print("  -> Dynamic allocator successfully altered portfolio allocation based on market state!")
        else:
            print("  -> WARNING: Dynamic allocator returned IDENTICAL allocations despite price collapse!")
    except Exception as e:
        print("Dynamic Allocator test exception:", e)

# 7. Part 22: Lookahead Search Inspection
def test_lookahead_planner():
    print("\n" + "="*80)
    print("PART 22 — LOOKAHEAD PLANNER EVALUATION (agents/hybrid_lookahead.py)")
    print("="*80)
    la_mod = load_module_from_path("hybrid_lookahead_mod", os.path.join(project_root, "agents/hybrid_lookahead.py"))
    HybridLookaheadAgent = la_mod.HybridLookaheadAgent
    agent_inst = HybridLookaheadAgent()
    print(f"Lookahead agent instantiated: {type(agent_inst)}")
    print(f"Horizon: {agent_inst.lookahead_horizon} days")
    print(f"Cows: {agent_inst.target_cows}, Sheep: {agent_inst.target_sheep}, Melons: {agent_inst.target_melons}")

if __name__ == "__main__":
    test_market_batch_sizes()
    test_fertilizer_policy()
    test_melon_sweep()
    test_herd_ratios()
    test_endgame_trace()
    test_dynamic_allocator()
    test_lookahead_planner()
