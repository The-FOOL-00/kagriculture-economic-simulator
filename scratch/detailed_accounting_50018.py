import os
import sys

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(BASE_DIR, "external_repos", "kaggriculture-cppsim"))
sys.path.insert(0, os.path.join(BASE_DIR, "candidates", "closed_loop_architecture"))

import kagsim
from closed_loop_v2 import ClosedLoopAgentV2
from dev_001_dynamic_portfolio import Dev001DynamicPortfolioAgent

def detailed_accounting(seed):
    print(f"=== DETAILED COMMODITY ACCOUNTING ON SEED {seed} (Match 0) ===")
    g = kagsim.Game(seed)
    cand = Dev001DynamicPortfolioAgent()
    v2 = ClosedLoopAgentV2()
    
    cand_revenue = {}
    v2_revenue = {}
    cand_expenses = {}
    v2_expenses = {}
    
    step = 0
    while not g.done:
        o0 = g.observe(0)
        o1 = g.observe(1)
        
        s0_before = dict(o0["private"]["shed"])
        s1_before = dict(o1["private"]["shed"])
        c0_before = o0["private"]["cash"]
        c1_before = o1["private"]["cash"]
        
        a0 = cand.act(o0)
        a1 = v2.act(o1)
        
        g.step(a0, a1)
        step += 1
        
        o0_after = g.observe(0)
        o1_after = g.observe(1)
        
        s0_after = dict(o0_after["private"]["shed"])
        s1_after = dict(o1_after["private"]["shed"])
        c0_after = o0_after["private"]["cash"]
        c1_after = o1_after["private"]["cash"]
        
        # Check cash diff
        diff0 = c0_after - c0_before
        diff1 = c1_after - c1_before
        
        # Check shed items sold (decreased shed when cash increased)
        if diff0 > 0:
            for item, qty_b in s0_before.items():
                qty_a = s0_after.get(item, 0)
                if qty_b > qty_a:
                    sold = qty_b - qty_a
                    # Approx price
                    cand_revenue[item] = cand_revenue.get(item, 0) + diff0 # if single item
        elif diff0 < 0:
            cand_expenses["net_purchases"] = cand_expenses.get("net_purchases", 0) + abs(diff0)
            
        if diff1 > 0:
            for item, qty_b in s1_before.items():
                qty_a = s1_after.get(item, 0)
                if qty_b > qty_a:
                    sold = qty_b - qty_a
                    v2_revenue[item] = v2_revenue.get(item, 0) + diff1
        elif diff1 < 0:
            v2_expenses["net_purchases"] = v2_expenses.get("net_purchases", 0) + abs(diff1)

    print("Cand final cash:", g.reward(0))
    print("V2 final cash:", g.reward(1))
    print("Diff:", g.reward(0) - g.reward(1))
    print("\nCand Expenses:", cand_expenses)
    print("V2 Expenses:", v2_expenses)
    print("\nCand Revenue by commodity:")
    for k, v in sorted(cand_revenue.items(), key=lambda x: -x[1]):
        print(f"  {k}: {v:.1f}")
    print("\nV2 Revenue by commodity:")
    for k, v in sorted(v2_revenue.items(), key=lambda x: -x[1]):
        print(f"  {k}: {v:.1f}")

detailed_accounting(50018)
