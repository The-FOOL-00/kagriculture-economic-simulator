import os
import sys
import json

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(BASE_DIR, "external_repos", "kaggriculture-cppsim"))
sys.path.insert(0, os.path.join(BASE_DIR, "extracted_agents", "dmitrii_lb2800"))

import kagsim
import main as dmitrii_main

def trace_realized_economics(seed=50007):
    game = kagsim.Game(seed)
    idle = {"farmer": ["PASS"], "hands": [], "market": []}
    
    dmitrii_agent = dmitrii_main.agent
    
    units_sold = {}
    revenue_by_product = {}
    
    step = 0
    while not game.done:
        obs0 = game.observe(0)
        farm0 = obs0["farms"][0]
        money0 = farm0["money"]
        shed0 = dict(obs0["private"]["shed"])
        
        act = dmitrii_agent(obs0)
        game.step(act, idle)
        
        obs1 = game.observe(0)
        farm1 = obs1["farms"][0]
        money1 = farm1["money"]
        shed1 = dict(obs1["private"]["shed"])
        
        # Calculate sales
        delta_money = money1 - money0
        # If any market sell was submitted, see what changed
        # We can also check obs0['market']['prices']
        for item, count in shed0.items():
            diff = count - shed1.get(item, 0)
            # If diff > 0 and a sell order was present
            if diff > 0:
                # check if there was a sell order for item
                for o in act.get("market", []):
                    if len(o) >= 3 and o[0] == "SELL" and o[1] == item:
                        units_sold[item] = units_sold.get(item, 0) + diff
                        # Approximate revenue at that step's price
                        price = obs0["market"]["prices"].get(item, 0)
                        rev = diff * price
                        revenue_by_product[item] = revenue_by_product.get(item, 0) + rev
                        break
                        
        step += 1

    final_obs = game.observe(0)
    final_cash = final_obs["farms"][0]["money"]
    final_shed = final_obs["private"]["shed"]
    print(f"============================================================")
    print(f"Seed {seed} (Dairy: SMOOTHIE + ICE CREAM) - Dmitrii Plan 0")
    print(f"============================================================")
    print(f"Final Cash: ${final_cash:.2f}")
    print(f"\nUnits Sold & Realized Revenue:")
    for item in sorted(units_sold.keys()):
        u = units_sold[item]
        r = revenue_by_product.get(item, 0)
        avg_p = r / u if u > 0 else 0
        print(f"  {item:12}: {u:4d} units sold | ${r:10,.2f} revenue (avg ${avg_p:.2f}/unit)")
    print(f"\nFinal Unsold Inventory in Shed:")
    for item, qty in final_shed.items():
        if qty > 0:
            print(f"  {item:12}: {qty:4d} units unsold")

if __name__ == "__main__":
    seeds_data = json.load(open("scratch/shop_world_seeds.json"))
    dairy_seeds = seeds_data["SMOOTHIE_SHOP+ICE_CREAM_SHOP"]
    for s in dairy_seeds[:3]:
        trace_realized_economics(s)
