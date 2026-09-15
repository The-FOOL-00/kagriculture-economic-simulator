"""
scratch/audit_dmitrii_exact_economy.py
Exact extraction of physical actions and market orders across all 13 tapes in Dmitrii LB2800 actions.json.
"""
import json
import os
from collections import Counter

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ACTIONS_PATH = os.path.join(BASE_DIR, "extracted_agents", "dmitrii_lb2800", "actions.json")

def main():
    with open(ACTIONS_PATH, "r", encoding="utf-8") as f:
        tapes = json.load(f)

    print("=" * 105)
    print("DMITRII LB2800: EXACT 13 ACTION TAPES FORENSIC SUMMARY")
    print("=" * 105)
    
    rows = []
    for t_idx, tape in enumerate(tapes):
        stats = {
            "tape": t_idx,
            "COW": 0, "SHEEP": 0, "GOOSE": 0,
            "COOP": 0, "PASTURE": 0,
            "FERT_ACT": 0, "WATER_ACT": 0, "FEED_ACT": 0, "CARE_ACT": 0, "COLL_FERT": 0,
            "PLANT_STR": 0, "PLANT_WHT": 0, "PLANT_CAR": 0, "PLANT_MEL": 0, "PLANT_TOM": 0,
            "BUY_FERT": 0, "BUY_LAND": 0
        }
        for act in tape:
            # Market
            for order in act.get("market", []):
                if not order: continue
                cmd = order[0]
                if cmd == "BUY_ANIMAL":
                    animal = order[1]
                    qty = order[2] if len(order) > 2 else 1
                    stats[animal] = stats.get(animal, 0) + qty
                elif cmd == "BUY_PRODUCT" and len(order) > 1 and order[1] == "FERTILIZER":
                    qty = order[2] if len(order) > 2 else 1
                    stats["BUY_FERT"] += qty
                elif cmd == "BUY_LAND":
                    stats["BUY_LAND"] += 1
            # Workers
            workers = ([act.get("farmer")] if act.get("farmer") else []) + (act.get("hands") or [])
            for w in workers:
                if not w: continue
                op = w[0]
                if op == "FERTILIZE": stats["FERT_ACT"] += 1
                elif op == "WATER": stats["WATER_ACT"] += 1
                elif op == "FEED": stats["FEED_ACT"] += 1
                elif op == "CARE": stats["CARE_ACT"] += 1
                elif op == "COLLECT_FERTILIZER": stats["COLL_FERT"] += 1
                elif op == "BUILD_COOP": stats["COOP"] += 1
                elif op == "BUILD_PASTURE": stats["PASTURE"] += 1
                elif op == "PLANT":
                    crop = w[1] if len(w) > 1 else ""
                    if crop == "STRAWBERRY": stats["PLANT_STR"] += 1
                    elif crop == "WHEAT": stats["PLANT_WHT"] += 1
                    elif crop == "CARROT": stats["PLANT_CAR"] += 1
                    elif crop == "MELON": stats["PLANT_MEL"] += 1
                    elif crop == "TOMATO": stats["PLANT_TOM"] += 1
        rows.append(stats)

    print(f"{'Tape':<5} | {'Cow':<4} | {'Shp':<4} | {'Gse':<4} | {'Coop':<5} | {'Past':<5} | {'Fert':<5} | {'Watr':<6} | {'Feed':<5} | {'Care':<5} | {'CollF':<5} | {'Straw':<5} | {'Wheat':<6} | {'Carrot':<6} | {'Melon':<5}")
    print("-" * 105)
    for r in rows:
        print(f"{r['tape']:<5d} | {r['COW']:<4d} | {r['SHEEP']:<4d} | {r['GOOSE']:<4d} | {r['COOP']:<5d} | {r['PASTURE']:<5d} | {r['FERT_ACT']:<5d} | {r['WATER_ACT']:<6d} | {r['FEED_ACT']:<5d} | {r['CARE_ACT']:<5d} | {r['COLL_FERT']:<5d} | {r['PLANT_STR']:<5d} | {r['PLANT_WHT']:<6d} | {r['PLANT_CAR']:<6d} | {r['PLANT_MEL']:<5d}")
    print("=" * 105)

if __name__ == "__main__":
    main()
