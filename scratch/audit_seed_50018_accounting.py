import os
import sys
import json

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(BASE_DIR, "external_repos", "kaggriculture-cppsim"))
sys.path.insert(0, os.path.join(BASE_DIR, "candidates", "closed_loop_architecture"))

import kagsim
from closed_loop_v2 import ClosedLoopAgentV2
from dev_001_dynamic_portfolio import Dev001DynamicPortfolioAgent

def audit_seed_accounting(seed):
    print(f"=== DETAILED ECONOMIC ACCOUNTING FOR SEED {seed} (Match 0) ===")
    g = kagsim.Game(seed)
    cand = Dev001DynamicPortfolioAgent()
    v2 = ClosedLoopAgentV2()
    
    cand_sales_revenue = {}
    v2_sales_revenue = {}
    
    step = 0
    while not g.done:
        o0 = g.observe(0)
        o1 = g.observe(1)
        
        s0_before = dict(o0["private"]["shed"])
        s1_before = dict(o1["private"]["shed"])
        
        a0 = cand.act(o0)
        a1 = v2.act(o1)
        
        g.step(a0, a1)
        step += 1
        
        o0_after = g.observe(0)
        o1_after = g.observe(1)
        
        s0_after = dict(o0_after["private"]["shed"])
        s1_after = dict(o1_after["private"]["shed"])
        
        # Track items sold from shed
        for item, q_b in s0_before.items():
            q_a = s0_after.get(item, 0)
            if q_b > q_a and item in o0["market"]["prices"]:
                sold = q_b - q_a
                p = o0["market"]["prices"][item]
                cand_sales_revenue[item] = cand_sales_revenue.get(item, 0) + sold * p
                
        for item, q_b in s1_before.items():
            q_a = s1_after.get(item, 0)
            if q_b > q_a and item in o1["market"]["prices"]:
                sold = q_b - q_a
                p = o1["market"]["prices"][item]
                v2_sales_revenue[item] = v2_sales_revenue.get(item, 0) + sold * p

    cand_cash = g.reward(0)
    v2_cash = g.reward(1)
    diff = cand_cash - v2_cash
    
    print(f"Cand Cash: {cand_cash:.1f}")
    print(f"V2   Cash: {v2_cash:.1f}")
    print(f"Cash Delta (Cand - V2): {diff:.1f}")
    print("\nCandidate Estimated Sales Revenue:")
    for k, v in sorted(cand_sales_revenue.items(), key=lambda x: -x[1]):
        print(f"  {k:12s}: ${v:10.1f}")
    print(f"  TOTAL SALES : ${sum(cand_sales_revenue.values()):10.1f}")
    
    print("\nV2 Estimated Sales Revenue:")
    for k, v in sorted(v2_sales_revenue.items(), key=lambda x: -x[1]):
        print(f"  {k:12s}: ${v:10.1f}")
    print(f"  TOTAL SALES : ${sum(v2_sales_revenue.values()):10.1f}")
    
    print("\nRevenue Delta (Cand - V2):")
    all_keys = set(cand_sales_revenue.keys()) | set(v2_sales_revenue.keys())
    for k in sorted(all_keys):
        c_val = cand_sales_revenue.get(k, 0)
        v_val = v2_sales_revenue.get(k, 0)
        delta = c_val - v_val
        print(f"  {k:12s}: Cand=${c_val:9.1f} | V2=${v_val:9.1f} | Delta=${delta:+9.1f}")

audit_seed_accounting(50018)
print()
audit_seed_accounting(50004)
