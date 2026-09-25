# SPDX-License-Identifier: MIT
import os
import sys
import json
from collections import Counter

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from kaggle_environments import make
from scripts.v32_common import load_agent, assert_frozen

def trace_full_economy(seed=249677):
    a7 = load_agent("E9_AST")
    dmitrii = load_agent("E8_DMITRII")
    
    env = make("kaggriculture", configuration={"seed": seed})
    env.run([lambda o, c=None: a7.act(o, c), lambda o, c=None: dmitrii.act(o, c)])
    
    sales_a7 = Counter()
    sales_dm = Counter()
    rev_a7 = Counter()
    rev_dm = Counter()
    
    buys_a7 = Counter()
    buys_dm = Counter()
    exp_a7 = Counter()
    exp_dm = Counter()
    
    # Track step-by-step transactions
    for step_idx in range(len(env.steps) - 1):
        s0 = env.steps[step_idx]
        s1 = env.steps[step_idx + 1]
        
        m0_before = s0[0]["observation"]["farms"][0]["money"]
        m0_after = s1[0]["observation"]["farms"][0]["money"]
        m1_before = s0[1]["observation"]["farms"][1]["money"]
        m1_after = s1[1]["observation"]["farms"][1]["money"]
        
        act0 = s0[0].get("action") or {}
        act1 = s0[1].get("action") or {}
        
        # Check market actions executed
        for o in act0.get("market", []):
            if o and o[0] == "SELL":
                sales_a7[o[1]] += o[2]
            elif o and o[0] == "BUY_PRODUCT":
                buys_a7[o[1]] += o[2]
            elif o and o[0] == "BUY_SEED":
                buys_a7["SEED_" + o[1]] += o[2]
            elif o and o[0] == "BUY_ANIMAL":
                buys_a7["ANIMAL_" + o[1]] += o[2]
            elif o and o[0] == "BUY_LAND":
                buys_a7["LAND"] += 1
            elif o and o[0] == "HIRE":
                buys_a7["HIRE"] += 1
                
        for o in act1.get("market", []):
            if o and o[0] == "SELL":
                sales_dm[o[1]] += o[2]
            elif o and o[0] == "BUY_PRODUCT":
                buys_dm[o[1]] += o[2]
            elif o and o[0] == "BUY_SEED":
                buys_dm["SEED_" + o[1]] += o[2]
            elif o and o[0] == "BUY_ANIMAL":
                buys_dm["ANIMAL_" + o[1]] += o[2]
            elif o and o[0] == "BUY_LAND":
                buys_dm["LAND"] += 1
            elif o and o[0] == "HIRE":
                buys_dm["HIRE"] += 1

    print("=" * 80)
    print("TOTAL SALES UNITS COMPARISON (Seed 249677):")
    print(f"{'Commodity':15s} | {'A7 Sold':10s} | {'Dm Sold':10s} | {'Diff (A7 - Dm)':15s}")
    print("-" * 60)
    all_commodities = sorted(set(sales_a7.keys()) | set(sales_dm.keys()))
    for c in all_commodities:
        q0 = sales_a7[c]
        q1 = sales_dm[c]
        print(f"{c:15s} | {q0:10d} | {q1:10d} | {q0 - q1:+15d}")

    print("\n" + "=" * 80)
    print("TOTAL PURCHASES / EXPENSES (Seed 249677):")
    all_buys = sorted(set(buys_a7.keys()) | set(buys_dm.keys()))
    for b in all_buys:
        q0 = buys_a7[b]
        q1 = buys_dm[b]
        print(f"{b:15s} | {q0:10d} | {q1:10d} | {q0 - q1:+15d}")

    # Let's inspect price histories for items where quantities or timing differed
    print("\n" + "=" * 80)
    print("CROP AND ANIMAL LIFECYCLE SUMMARY:")
    farm_a7 = env.steps[-1][0]["observation"]["farms"][0]
    farm_dm = env.steps[-1][1]["observation"]["farms"][1]
    
    # Hires
    print(f"A7 Hands Hired: {len(farm_a7['hands'])} | Dmitrii Hands Hired: {len(farm_dm['hands'])}")
    print(f"A7 Land Unlocked: {len(farm_a7['unlocked_quadrants'])} | Dmitrii Land Unlocked: {len(farm_dm['unlocked_quadrants'])}")

if __name__ == "__main__":
    trace_full_economy(249677)
