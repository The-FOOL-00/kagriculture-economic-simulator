"""
scratch/analyze_dmitrii_tapes.py
Inspects the 13 tapes in actions.json of Dmitrii-LB2800.
Extracts:
- Animal purchases (Cows, Sheep, Geese) per plan from MARKET orders
- Crops planted (Wheat, Strawberry, Melon, Carrot, Tomato) per plan
- Land purchases per plan
- Farm hand hires per plan
- Fertilization events per plan
- Total sales and product breakdown per plan
"""
import collections
import json
import os
import sys

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ACTIONS_PATH = os.path.join(BASE_DIR, "extracted_agents", "dmitrii_lb2800", "actions.json")

def analyze_tapes():
    with open(ACTIONS_PATH, "r") as f:
        tapes = json.load(f)
        
    print("=" * 95)
    print(f"{'Plan':4} | {'Cows':4} | {'Sheep':5} | {'Geese':5} | {'Straw':5} | {'Wheat':5} | {'Melon':5} | {'Fert':4} | {'Hires':5} | {'Land':4} | Description")
    print("-" * 95)
    
    plan_summaries = {}
    
    for plan_idx, tape in enumerate(tapes):
        cows = 0
        sheep = 0
        geese = 0
        crops = collections.Counter()
        fert_count = 0
        hires = 0
        land = 0
        sales = collections.Counter()
        
        for step, act in enumerate(tape):
            farmer = act.get("farmer", ["PASS"])
            hands = act.get("hands", [])
            market = act.get("market", [])
            
            all_workers = [farmer] + hands
            for w in all_workers:
                if not w: continue
                op = w[0]
                if op == "PLANT" and len(w) >= 2:
                    crops[w[1]] += 1
                elif op == "FERTILIZE":
                    fert_count += 1
                    
            for order in market:
                if not order: continue
                op = order[0]
                if op == "BUY_ANIMAL" and len(order) >= 3:
                    a = order[1]
                    qty = int(order[2])
                    if a == "COW": cows += qty
                    elif a == "SHEEP": sheep += qty
                    elif a == "GOOSE": geese += qty
                elif op == "BUY_LAND":
                    land += 1
                elif op == "HIRE":
                    hires += order[1] if len(order) >= 2 else 1
                elif op == "SELL" and len(order) >= 3:
                    sales[order[1]] += int(order[2])
                    
        desc = "Generic Fallback" if plan_idx == 0 else ("Terminal Route" if plan_idx == 2 else f"Yarn Route {plan_idx}")
        straw = crops.get("STRAWBERRY", 0)
        wheat = crops.get("WHEAT", 0)
        melon = crops.get("MELON", 0)
        
        print(f"{plan_idx:4d} | {cows:4d} | {sheep:5d} | {geese:5d} | {straw:5d} | {wheat:5d} | {melon:5d} | {fert_count:4d} | {hires:5d} | {land:4d} | {desc}")
        
        plan_summaries[plan_idx] = {
            "cows": cows,
            "sheep": sheep,
            "geese": geese,
            "crops": dict(crops),
            "fertilizations": fert_count,
            "hires": hires,
            "land": land,
            "sales": dict(sales)
        }
        
    out_path = os.path.join(BASE_DIR, "results", "dmitrii_tape_profiles.json")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(plan_summaries, f, indent=2)

if __name__ == "__main__":
    analyze_tapes()
