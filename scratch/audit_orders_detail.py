import os
import sys
import json

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(BASE_DIR, "external_repos", "kaggriculture-cppsim"))
sys.path.insert(0, os.path.join(BASE_DIR, "candidates", "closed_loop_architecture"))

import kagsim
from closed_loop_v2 import ClosedLoopAgentV2
from dev_001_dynamic_portfolio import Dev001DynamicPortfolioAgent

# Let's inspect step-by-step all market orders on seed 50018 for Cand (Seat 0) and V2 (Seat 1)
g = kagsim.Game(50018)
cand = Dev001DynamicPortfolioAgent()
v2 = ClosedLoopAgentV2()

cand_orders_by_item = {}
v2_orders_by_item = {}

cand_executed_sales = {}
v2_executed_sales = {}

step = 0
while not g.done:
    o0 = g.observe(0)
    o1 = g.observe(1)
    
    a0 = cand.act(o0)
    a1 = v2.act(o1)
    
    for m in a0.get("market", []):
        cand_orders_by_item[m[0]] = cand_orders_by_item.get(m[0], {})
        item = m[1] if len(m) > 1 else "OTHER"
        cand_orders_by_item[m[0]][item] = cand_orders_by_item[m[0]].get(item, 0) + (m[2] if len(m) > 2 else 1)
        
    for m in a1.get("market", []):
        v2_orders_by_item[m[0]] = v2_orders_by_item.get(m[0], {})
        item = m[1] if len(m) > 1 else "OTHER"
        v2_orders_by_item[m[0]][item] = v2_orders_by_item[m[0]].get(item, 0) + (m[2] if len(m) > 2 else 1)
        
    g.step(a0, a1)
    step += 1

print("=== CANDIDATE MARKET ORDERS BY ITEM ===")
print(json.dumps(cand_orders_by_item, indent=2))
print("\n=== V2 MARKET ORDERS BY ITEM ===")
print(json.dumps(v2_orders_by_item, indent=2))
