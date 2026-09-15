import copy
import json
import os
import sys

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(BASE_DIR, "external_repos", "kaggriculture-cppsim"))
sys.path.insert(0, os.path.join(BASE_DIR, "extracted_agents", "dmitrii_lb2800"))
sys.path.insert(0, os.path.join(BASE_DIR, "candidates"))

import kagsim
import router_parent as mod_r
import compiled_v54_plus_residual as v54

BASE_PRICES = {
    "WHEAT": 25,
    "CARROT": 35,
    "TOMATO": 60,
    "STRAWBERRY": 120,
    "MELON": 250,
    "EGG": 50,
    "MILK": 160,
    "WOOL": 200,
    "FERTILIZER": 100,
}

class PriceProtectedPolicy(mod_r.Policy):
    def act(self, observation):
        action = super().act(observation)
        step = int(observation["step"])
        
        # Don't filter sales in terminal liquidation
        if step >= 710:
            return action
            
        prices = observation["market"]["prices"]
        new_market = []
        for order in action.get("market", []):
            if len(order) >= 3 and order[0] == "SELL":
                item = order[1]
                qty = order[2]
                curr_price = prices.get(item, 0)
                base = BASE_PRICES.get(item, 100)
                
                # Rule: For high-value goods (MILK, WOOL, STRAWBERRY), don't sell if price crashed below 50%
                # unless it's an emergency liquidity need
                if item in ("MILK", "WOOL") and curr_price < 0.50 * base:
                    # Hold in shed!
                    continue
                if item == "STRAWBERRY" and curr_price < 0.60 * base:
                    continue
            new_market.append(order)
            
        action["market"] = new_market[:mod_r.MAX_ORDERS]
        return action

def test_price_protection():
    seeds_data = json.load(open("scratch/shop_world_seeds.json"))
    dairy_seeds = seeds_data["SMOOTHIE_SHOP+ICE_CREAM_SHOP"]
    
    results_base = []
    results_protected = []
    
    for s in dairy_seeds[:30]:
        # Base
        p_base = mod_r.Policy("extracted_agents/dmitrii_lb2800")
        g1 = kagsim.Game(s)
        while not g1.done:
            g1.step(p_base.act(g1.observe(0)), v54.agent(g1.observe(1)))
        c1 = g1.reward(0)
        results_base.append(c1)
        
        # Protected
        p_prot = PriceProtectedPolicy("extracted_agents/dmitrii_lb2800")
        g2 = kagsim.Game(s)
        while not g2.done:
            g2.step(p_prot.act(g2.observe(0)), v54.agent(g2.observe(1)))
        c2 = g2.reward(0)
        results_protected.append(c2)
        
    m1 = sum(results_base) / len(results_base)
    m2 = sum(results_protected) / len(results_protected)
    print("============================================================")
    print("PHASE 11 CAUSAL TEST: PRICE PROTECTION LAYER (N=30 SEEDS)")
    print("============================================================")
    print(f"Base Dmitrii Mean:       ${m1:,.2f}")
    print(f"Protected Dmitrii Mean:  ${m2:,.2f}")
    print(f"Net Paired Delta:        ${m2 - m1:+,.2f}")
    wins = sum(1 for a, b in zip(results_protected, results_base) if a > b)
    ties = sum(1 for a, b in zip(results_protected, results_base) if a == b)
    losses = sum(1 for a, b in zip(results_protected, results_base) if a < b)
    print(f"Win/Tie/Loss vs Base:    {wins}W / {ties}T / {losses}L")
    for i, s in enumerate(dairy_seeds[:15]):
        diff = results_protected[i] - results_base[i]
        print(f"  Seed {s}: Base=${results_base[i]:,.2f} | Prot=${results_protected[i]:,.2f} | Delta=${diff:+,.2f}")

if __name__ == "__main__":
    test_price_protection()
