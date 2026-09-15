import os
import sys
import json

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(BASE_DIR, "external_repos", "kaggriculture-cppsim"))
sys.path.insert(0, os.path.join(BASE_DIR, "extracted_agents", "dmitrii_lb2800"))
sys.path.insert(0, os.path.join(BASE_DIR, "candidates"))

import kagsim
import main as dmitrii_main
import compiled_v54_plus_residual as v54

def trace_competitive_economics(seed=50009):
    game = kagsim.Game(seed)
    
    dmitrii_agent = dmitrii_main.agent
    v54_agent = v54.agent
    
    units_sold = {}
    revenue_by_product = {}
    
    step = 0
    while not game.done:
        obs0 = game.observe(0)
        obs1 = game.observe(1)
        farm0 = obs0["farms"][0]
        money0 = farm0["money"]
        shed0 = dict(obs0["private"]["shed"])
        
        act0 = dmitrii_agent(obs0)
        act1 = v54_agent(obs1)
        game.step(act0, act1)
        
        obs0_after = game.observe(0)
        farm0_after = obs0_after["farms"][0]
        money0_after = farm0_after["money"]
        shed0_after = dict(obs0_after["private"]["shed"])
        
        for item, count in shed0.items():
            diff = count - shed0_after.get(item, 0)
            if diff > 0:
                for o in act0.get("market", []):
                    if len(o) >= 3 and o[0] == "SELL" and o[1] == item:
                        units_sold[item] = units_sold.get(item, 0) + diff
                        price = obs0["market"]["prices"].get(item, 0)
                        rev = diff * price
                        revenue_by_product[item] = revenue_by_product.get(item, 0) + rev
                        break
                        
        step += 1

    final_cash0 = game.reward(0)
    final_cash1 = game.reward(1)
    print(f"============================================================")
    print(f"COMPETITIVE MATCH: Seed {seed} vs V54++ Residual")
    print(f"Dmitrii Cash: ${final_cash0:,.2f} | V54 Cash: ${final_cash1:,.2f} | Margin: ${final_cash0 - final_cash1:+,.2f}")
    print(f"============================================================")
    for item in sorted(units_sold.keys()):
        u = units_sold[item]
        r = revenue_by_product.get(item, 0)
        avg_p = r / u if u > 0 else 0
        print(f"  {item:12}: {u:4d} units sold | ${r:10,.2f} revenue (avg ${avg_p:6.2f}/unit)")

if __name__ == "__main__":
    for s in [50007, 50009, 50027, 50573]:
        trace_competitive_economics(s)
