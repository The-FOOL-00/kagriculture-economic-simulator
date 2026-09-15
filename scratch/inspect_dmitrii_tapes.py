"""
scratch/inspect_dmitrii_tapes.py
Inspect the 13 action tapes in Dmitrii-LB2800 actions.json.
Extracts:
- Tape count and step count
- Crop planting actions per tape (Wheat, Carrot, Tomato, Strawberry, Melon)
- Fertilize actions per tape
- Animal purchases per tape (Cow, Sheep, Goose)
- Buildings constructed (Coop, Pasture)
- Hands hired per tape
- Actions distribution
"""
import json
import os
from collections import Counter

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ACTIONS_PATH = os.path.join(BASE_DIR, "extracted_agents", "dmitrii_lb2800", "actions.json")

def analyze_tapes():
    with open(ACTIONS_PATH, "r", encoding="utf-8") as f:
        tapes = json.load(f)
        
    print(f"Total action tapes: {len(tapes)}")
    tape_lengths = [len(tape) for tape in tapes]
    print(f"Tape lengths: {set(tape_lengths)} (min={min(tape_lengths)}, max={max(tape_lengths)})")
    
    summary = []
    
    for idx, tape in enumerate(tapes):
        stats = {
            "tape": idx,
            "length": len(tape),
            "FERTILIZE": 0,
            "WATER": 0,
            "PLANT_WHEAT": 0,
            "PLANT_CARROT": 0,
            "PLANT_TOMATO": 0,
            "PLANT_STRAWBERRY": 0,
            "PLANT_MELON": 0,
            "BUY_COW": 0,
            "BUY_SHEEP": 0,
            "BUY_GOOSE": 0,
            "BUILD_COOP": 0,
            "BUILD_PASTURE": 0,
            "HIRE_HAND": 0,
            "total_worker_actions": 0,
            "action_types": Counter()
        }
        
        for step, act in enumerate(tape):
            # Market actions
            market = act.get("market", [])
            for order in market:
                if not order: continue
                cmd = order[0]
                if cmd == "BUY":
                    item = order[1]
                    if item == "COW": stats["BUY_COW"] += order[2] if len(order) > 2 else 1
                    elif item == "SHEEP": stats["BUY_SHEEP"] += order[2] if len(order) > 2 else 1
                    elif item == "GOOSE": stats["BUY_GOOSE"] += order[2] if len(order) > 2 else 1
                    
            # Worker actions
            farmer = act.get("farmer")
            hands = act.get("hands", [])
            all_workers = ([farmer] if farmer else []) + (hands or [])
            
            for w in all_workers:
                if not w: continue
                stats["total_worker_actions"] += 1
                op = w[0]
                stats["action_types"][op] += 1
                if op == "FERTILIZE":
                    stats["FERTILIZE"] += 1
                elif op == "WATER":
                    stats["WATER"] += 1
                elif op == "HIRE":
                    stats["HIRE_HAND"] += 1
                elif op == "BUILD_COOP":
                    stats["BUILD_COOP"] += 1
                elif op == "BUILD_PASTURE":
                    stats["BUILD_PASTURE"] += 1
                elif op == "PLANT":
                    crop = w[1] if len(w) > 1 else "UNKNOWN"
                    key = f"PLANT_{crop}"
                    if key in stats:
                        stats[key] += 1
                    else:
                        stats[key] = 1
                        
        summary.append(stats)
        
    print("\n" + "=" * 110)
    print(f"{'Tape':<5} | {'Fert':<5} | {'Water':<6} | {'Strawb':<6} | {'Wheat':<6} | {'Carrot':<6} | {'Melon':<6} | {'Tomat':<6} | {'Cow':<4} | {'Sheep':<5} | {'Goose':<5} | {'Coop':<4} | {'Past':<4} | {'Hands':<5}")
    print("-" * 110)
    for s in summary:
        print(f"{s['tape']:<5d} | {s['FERTILIZE']:<5d} | {s['WATER']:<6d} | {s['PLANT_STRAWBERRY']:<6d} | {s['PLANT_WHEAT']:<6d} | {s['PLANT_CARROT']:<6d} | {s['PLANT_MELON']:<6d} | {s['PLANT_TOMATO']:<6d} | {s['BUY_COW']:<4d} | {s['BUY_SHEEP']:<5d} | {s['BUY_GOOSE']:<5d} | {s['BUILD_COOP']:<4d} | {s['BUILD_PASTURE']:<4d} | {s['HIRE_HAND']:<5d}")
    print("=" * 110)

if __name__ == "__main__":
    analyze_tapes()
