import os, sys, json

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(BASE_DIR, "external_repos", "kaggriculture-cppsim"))
sys.path.insert(0, os.path.join(BASE_DIR, "extracted_agents", "dmitrii_lb2800"))
sys.path.insert(0, os.path.join(BASE_DIR, "candidates", "closed_loop_architecture"))

import kagsim
import router_parent as mod_r
from closed_loop_v2 import ClosedLoopAgentV2

def track_realized_sales(seed=50266):
    g = kagsim.Game(seed)
    p0 = ClosedLoopAgentV2()
    p1 = mod_r.Policy(os.path.join(BASE_DIR, "extracted_agents", "dmitrii_lb2800"))
    
    prev_money = 3000.0
    sales_by_item = {}
    
    while not g.done:
        obs0 = g.observe(0)
        priv0 = obs0["private"]
        prev_shed = dict(priv0["shed"])
        prev_cash = float(obs0["farms"][0]["money"])
        
        a0 = p0.act(obs0)
        a1 = p1.act(g.observe(1))
        
        g.step(a0, a1)
        
        post_obs0 = g.observe(0)
        post_priv0 = post_obs0["private"]
        post_cash = float(post_obs0["farms"][0]["money"])
        
        # If cash increased from sales
        cash_delta = post_cash - prev_cash
        if cash_delta > 0:
            # Check what items decreased in shed
            sold_items = []
            for it, q in prev_shed.items():
                diff = q - post_priv0["shed"].get(it, 0)
                if diff > 0:
                    sold_items.append((it, diff))
            if sold_items:
                for it, diff in sold_items:
                    sales_by_item[it] = sales_by_item.get(it, 0) + diff
                    
    print(f"Seed {seed} Realized Units Sold by ClosedLoopV2:")
    for it, q in sorted(sales_by_item.items()):
        print(f"  {it:<12}: {q:4d} units")
    print(f"Final Reward: ${g.reward(0):,.0f}")

if __name__ == "__main__":
    track_realized_sales(50266)
