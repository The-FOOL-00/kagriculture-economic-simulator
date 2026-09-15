import os
import sys
import json

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(BASE_DIR, "external_repos", "kaggriculture-cppsim"))
sys.path.insert(0, os.path.join(BASE_DIR, "candidates", "closed_loop_architecture"))

import kagsim
from closed_loop_v2 import ClosedLoopAgentV2
from dev_001_dynamic_portfolio import Dev001DynamicPortfolioAgent

def trace_market_and_harvests(seed):
    print(f"==================================================")
    print(f"MARKET & HARVEST TRACE FOR SEED {seed}")
    print(f"==================================================")
    
    g = kagsim.Game(seed)
    cand = Dev001DynamicPortfolioAgent()
    v2 = ClosedLoopAgentV2()
    
    cand_sales = {}
    v2_sales = {}
    cand_buys = {}
    v2_buys = {}
    
    step = 0
    while not g.done:
        o0 = g.observe(0)
        o1 = g.observe(1)
        
        a0 = cand.act(o0)
        a1 = v2.act(o1)
        
        # Track market orders
        for m in a0.get("market", []):
            if m[0] == "SELL":
                cand_sales[m[1]] = cand_sales.get(m[1], 0) + m[2]
            elif m[0] == "BUY_SEED":
                cand_buys[m[1]] = cand_buys.get(m[1], 0) + m[2]
        for m in a1.get("market", []):
            if m[0] == "SELL":
                v2_sales[m[1]] = v2_sales.get(m[1], 0) + m[2]
            elif m[0] == "BUY_SEED":
                v2_buys[m[1]] = v2_buys.get(m[1], 0) + m[2]
                
        g.step(a0, a1)
        step += 1
        
    print(f"Match 0: Cand Cash = {g.reward(0)}, V2 Cash = {g.reward(1)}, Diff = {g.reward(0) - g.reward(1)}")
    print(f"Cand Seed Buys: {cand_buys}")
    print(f"V2   Seed Buys: {v2_buys}")
    print(f"Cand Sales: {cand_sales}")
    print(f"V2   Sales: {v2_sales}")

trace_market_and_harvests(50018)
print()
trace_market_and_harvests(50004)
