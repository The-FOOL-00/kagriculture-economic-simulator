import json
import os
from collections import Counter

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
tapes_path = os.path.join(BASE_DIR, "scratch", "yhay81_three_day_router_tapes.json")
with open(tapes_path, encoding="utf-8") as f:
    tapes = json.load(f)

def analyze_tape(tape, label):
    animals_bought = Counter()
    crops_planted = Counter()
    fert_count = 0
    hires = 0
    land = 0
    sells = Counter()
    buys = Counter()
    
    for step, act in enumerate(tape):
        # Market orders
        for order in act.get("market", []):
            if not order: continue
            op = order[0]
            if op == "BUY_ANIMAL":
                animals_bought[order[1]] += int(order[2]) if len(order) > 2 else 1
            elif op == "BUY_LAND":
                land += 1
            elif op == "HIRE":
                hires += 1
            elif op == "SELL":
                sells[order[1]] += int(order[2]) if len(order) > 2 else 1
            elif op == "BUY_PRODUCT":
                buys[order[1]] += int(order[2]) if len(order) > 2 else 1
                
        # Worker actions
        workers = [act.get("farmer", ["PASS"])] + act.get("hands", [])
        for w in workers:
            if not w: continue
            op = w[0]
            if op == "PLANT":
                crop = w[1] if len(w) > 1 else "UNKNOWN"
                crops_planted[crop] += 1
            elif op == "FERTILIZE":
                fert_count += 1
                
    print(f"=== {label} ===")
    print(f"  Animals Bought: {dict(animals_bought)}")
    print(f"  Crops Planted: {dict(crops_planted)}")
    print(f"  Fertilizations: {fert_count}")
    print(f"  Hires: {hires} | Land Unlocks: {land}")
    print(f"  Feed Bought: {dict(buys)}")
    print(f"  Total Sells: {dict(sells)}")
    print()

analyze_tape(tapes[0], "Yusuke Hayashi Three-Day Router - Route 0 (Base)")
analyze_tape(tapes[1], "Yusuke Hayashi Three-Day Router - Route 1 (Bakery/Pet Cafe Switch)")

# Compare with Dmitrii Plan 0
dmitrii_tapes_path = os.path.join(BASE_DIR, "extracted_agents", "dmitrii_lb2800", "actions.json")
with open(dmitrii_tapes_path, encoding="utf-8") as f:
    dmitrii_tapes = json.load(f)

analyze_tape(dmitrii_tapes[0], "Dmitrii Plan 0 (Generic Fallback)")
analyze_tape(dmitrii_tapes[8], "Dmitrii Plan 8 (Smoothie+Yarn)")
