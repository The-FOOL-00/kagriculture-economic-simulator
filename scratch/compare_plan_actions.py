"""
scratch/compare_plan_actions.py
Compare actions between Plan 0 (Generic Fallback) and Plan 8 / Plan 11 / Plan 6 after Step 144.
"""
import collections
import json
import os
import sys

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ACTIONS_PATH = os.path.join(BASE_DIR, "extracted_agents", "dmitrii_lb2800", "actions.json")

def compare():
    with open(ACTIONS_PATH, "r") as f:
        tapes = json.load(f)
        
    plans = [0, 6, 8, 11]
    
    print("=" * 80)
    print("ACTION COMPARISON AFTER STEP 144 (POST-SHOP ROUTE DIVERGENCE)")
    print("=" * 80)
    
    for p in plans:
        tape = tapes[p]
        cows = 0
        sheep = 0
        geese = 0
        hires = 0
        sales = collections.Counter()
        crops = collections.Counter()
        fert = 0
        
        # Look at steps 144 to 718
        for step in range(144, 719):
            act = tape[step]
            farmer = act.get("farmer", ["PASS"])
            hands = act.get("hands", [])
            market = act.get("market", [])
            all_w = [farmer] + hands
            
            for w in all_w:
                if not w: continue
                if w[0] == "PLANT" and len(w) >= 2: crops[w[1]] += 1
                elif w[0] == "FERTILIZE": fert += 1
                
            for order in market:
                if not order: continue
                op = order[0]
                if op == "BUY_ANIMAL" and len(order) >= 3:
                    a = order[1]
                    qty = int(order[2])
                    if a == "COW": cows += qty
                    elif a == "SHEEP": sheep += qty
                    elif a == "GOOSE": geese += qty
                elif op == "HIRE":
                    hires += order[1] if len(order) >= 2 else 1
                elif op == "SELL" and len(order) >= 3:
                    sales[order[1]] += int(order[2])
                    
        print(f"\n--- PLAN {p} (Steps 144-718) ---")
        print(f"Animals Bought after step 144: Cows={cows}, Sheep={sheep}, Geese={geese}")
        print(f"Crops Planted after step 144 : Straw={crops['STRAWBERRY']}, Wheat={crops['WHEAT']}, Melon={crops['MELON']}")
        print(f"Fertilizations: {fert}, Hires: {hires}")
        print(f"Total Sales after step 144   : {dict(sales)}")

if __name__ == "__main__":
    compare()
