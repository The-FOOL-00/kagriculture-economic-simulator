import json
import os
import sys
from concurrent.futures import ProcessPoolExecutor

PROJECT_ROOT = os.path.abspath(".")
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import kaggle_environments
from candidates.slot2_aethel_refined_v2 import agent as v2_agent

SEEDS_200 = list(range(1000, 1200))

def run_single_match_v2(seed):
    env = kaggle_environments.make("kaggriculture", configuration={"seed": seed})
    steps = env.run([v2_agent, "starter"])
    
    rev_by_item = {
        "STRAWBERRY": 0.0, "MELON": 0.0, "MILK": 0.0, "WOOL": 0.0,
        "WHEAT": 0.0, "FERTILIZER": 0.0, "EGG": 0.0
    }
    qty_sold = {k: 0 for k in rev_by_item}
    
    exp_animals = 0.0
    exp_seeds = 0.0
    exp_feed = 0.0
    exp_land = 0.0
    
    actions_count = {
        "FERTILIZE": 0, "HARVEST_STRAW": 0, "HARVEST_OTHER": 0,
        "WATER": 0, "CARE": 0, "FEED": 0, "COLLECT_FERT": 0,
        "DROP": 0, "MOVE": 0, "PASS": 0
    }
    
    straw_harvested = 0
    max_shed_fill = 0
    
    prev_quads = len(steps[0][0]["observation"]["farms"][0].get("unlocked_quadrants") or ["NW"])
    initial_money = steps[0][0]["observation"]["farms"][0]["money"]
    
    for s_idx in range(1, len(steps)):
        prev_obs = steps[s_idx-1][0]["observation"]
        curr_obs = steps[s_idx][0]["observation"]
        
        shed = curr_obs["private"]["shed"]
        sf = sum(shed.values())
        if sf > max_shed_fill: max_shed_fill = sf
        
        quads = len(curr_obs["farms"][0].get("unlocked_quadrants") or [])
        if quads > prev_quads:
            if quads == 2: exp_land += 1000.0
            elif quads == 3: exp_land += 2000.0
            elif quads == 4: exp_land += 4000.0
            prev_quads = quads
            
        act = steps[s_idx][0].get("action") or {}
        prev_prices = (prev_obs.get("market") or {}).get("prices") or {}
        
        all_wacts = [act.get("farmer", [])] + act.get("hands", [])
        all_wpos = [prev_obs["farms"][0]["farmer"]] + prev_obs["farms"][0]["hands"]
        for wpos, wact in zip(all_wpos, all_wacts):
            if not wact: continue
            c = wact[0]
            if c == "FERTILIZE": actions_count["FERTILIZE"] += 1
            elif c == "WATER": actions_count["WATER"] += 1
            elif c == "CARE": actions_count["CARE"] += 1
            elif c == "FEED": actions_count["FEED"] += 1
            elif c == "COLLECT_FERTILIZER": actions_count["COLLECT_FERT"] += 1
            elif c == "DROP": actions_count["DROP"] += 1
            elif c == "PASS": actions_count["PASS"] += 1
            elif c in ("NORTH", "SOUTH", "EAST", "WEST"): actions_count["MOVE"] += 1
            elif c == "HARVEST":
                x, y = wpos
                t = prev_obs["farms"][0]["tiles"][y][x]
                if isinstance(t, dict) and t.get("crop") == "STRAWBERRY":
                    actions_count["HARVEST_STRAW"] += 1
                else:
                    actions_count["HARVEST_OTHER"] += 1
                    
        prev_tiles = prev_obs["farms"][0]["tiles"]
        curr_tiles = curr_obs["farms"][0]["tiles"]
        for y in range(len(prev_tiles)):
            for x in range(len(prev_tiles[y])):
                pt = prev_tiles[y][x]
                ct = curr_tiles[y][x]
                if isinstance(pt, dict) and pt.get("crop") == "STRAWBERRY":
                    py = int(pt.get("yield_units", 0) or 0)
                    cy = int(ct.get("yield_units", 0) or 0) if isinstance(ct, dict) else 0
                    if py > cy:
                        straw_harvested += (py - cy)

        for order in act.get("market") or []:
            if not order: continue
            cmd = order[0]
            item = order[1] if len(order) > 1 else None
            qty = int(order[2]) if len(order) > 2 else 1
            p = float(prev_prices.get(item, 0.0))
            if cmd == "SELL":
                if item in rev_by_item:
                    rev_by_item[item] += qty * p
                    qty_sold[item] += qty
            elif cmd == "BUY_ANIMAL":
                exp_animals += qty * (600.0 if item == "COW" else (500.0 if item == "SHEEP" else 300.0))
            elif cmd == "BUY_SEED":
                sc = {"WHEAT": 10.0, "CARROT": 20.0, "TOMATO": 50.0, "STRAWBERRY": 100.0, "MELON": 80.0}
                exp_seeds += qty * sc.get(item, 0.0)
            elif cmd == "BUY_PRODUCT":
                exp_feed += qty * p
                
    terminal_reward = float(steps[-1][0]["reward"])
    total_rev = sum(rev_by_item.values())
    total_buys = exp_animals + exp_seeds + exp_feed + exp_land
    exp_hires = initial_money + total_rev - total_buys - terminal_reward
    total_exp = total_buys + exp_hires
    
    term_obs = steps[-1][0]["observation"]
    term_shed = dict(term_obs["private"]["shed"])
    term_shed_inv = sum(term_shed.values())
    final_shops = list(term_obs.get("town", {}).get("unlocked_shops", []))
    
    return {
        "agent": "Frozen_V2",
        "seed": seed,
        "reward": terminal_reward,
        "straw_harvested": straw_harvested,
        "straw_sold": qty_sold["STRAWBERRY"],
        "straw_rev": rev_by_item["STRAWBERRY"],
        "milk_rev": rev_by_item["MILK"],
        "wool_rev": rev_by_item["WOOL"],
        "wheat_rev": rev_by_item["WHEAT"],
        "melon_rev": rev_by_item["MELON"],
        "fert_rev": rev_by_item["FERTILIZER"],
        "egg_rev": rev_by_item["EGG"],
        "qty_sold": qty_sold,
        "rev_by_item": rev_by_item,
        "exp_animals": exp_animals,
        "exp_seeds": exp_seeds,
        "exp_feed": exp_feed,
        "exp_land": exp_land,
        "exp_hires": exp_hires,
        "total_exp": total_exp,
        "total_rev": total_rev,
        "term_shed_inv": term_shed_inv,
        "max_shed_fill": max_shed_fill,
        "straw_avg_p": rev_by_item["STRAWBERRY"] / qty_sold["STRAWBERRY"] if qty_sold["STRAWBERRY"] > 0 else 0.0,
        "milk_avg_p": rev_by_item["MILK"] / qty_sold["MILK"] if qty_sold["MILK"] > 0 else 0.0,
        "actions_count": actions_count,
        "unlocked_shops": final_shops
    }

def main():
    print("Evaluating Frozen V2 across Seeds 1000-1199 (N=200)...")
    results = {}
    with ProcessPoolExecutor(max_workers=8) as executor:
        for res in executor.map(run_single_match_v2, SEEDS_200):
            results[str(res["seed"])] = res
            
    out_path = "scratch/v2_200seed_raw.json"
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Frozen V2 200-seed benchmark complete. Saved to {out_path}.")

if __name__ == "__main__":
    main()
