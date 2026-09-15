import json
import os
import sys
import copy
import random
import numpy as np
from concurrent.futures import ProcessPoolExecutor

sys.path.insert(0, os.getcwd())
import kaggle_environments

# Import agents
from candidates.candidate_cl_economic_v1 import agent as cl_baseline
from candidates.candidate_cl_fert_gated import agent as cl_gated
from candidates.candidate_cl_harvest_priority import agent as cl_harvest_prio
from candidates.candidate_cl_pair_m1_m3 import agent as cl_pair

SEEDS_50 = list(range(1000, 1050))
SEEDS_10 = list(range(1000, 1010))

def run_single_match(agent_fn, seed, forced_shops=None):
    env = kaggle_environments.make("kaggriculture", configuration={"seed": seed})
    
    # Custom runner if forced_shops is provided
    if forced_shops is not None:
        # Run step-by-step and override town shops
        env.reset()
        agent0 = agent_fn
        agent1 = "starter"
        # We can run using env.step
        # Let's inspect if we need step-by-step
        pass
        
    steps = env.run([agent_fn, "starter"])
    
    # Extract complete telemetry
    rev_by_item = {
        "STRAWBERRY": 0.0, "MELON": 0.0, "MILK": 0.0, "WOOL": 0.0,
        "WHEAT": 0.0, "FERTILIZER": 0.0, "EGG": 0.0
    }
    qty_sold = {k: 0 for k in rev_by_item}
    straw_prices = []
    milk_prices = []
    
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
    town_shops_timeline = {}
    
    prev_quads = len(steps[0][0]["observation"]["farms"][0].get("unlocked_quadrants") or ["NW"])
    initial_money = steps[0][0]["observation"]["farms"][0]["money"]
    
    for s_idx in range(1, len(steps)):
        prev_obs = steps[s_idx-1][0]["observation"]
        curr_obs = steps[s_idx][0]["observation"]
        
        day = curr_obs["day"]
        hour = curr_obs["hour"]
        step = curr_obs["step"]
        
        # Track town shops
        town = curr_obs.get("town") or {}
        unlocked = list(town.get("unlocked_shops") or [])
        town_shops_timeline[day] = unlocked
        
        # Track prices
        m = curr_obs.get("market") or {}
        pr = m.get("prices") or {}
        sp = pr.get("STRAWBERRY", 120)
        mp = pr.get("MILK", 160)
        straw_prices.append(sp)
        milk_prices.append(mp)
        
        # Track shed fill
        shed = curr_obs["private"]["shed"]
        sf = sum(shed.values())
        if sf > max_shed_fill: max_shed_fill = sf
        
        # Track land
        quads = len(curr_obs["farms"][0].get("unlocked_quadrants") or [])
        if quads > prev_quads:
            if quads == 2: exp_land += 1000.0
            elif quads == 3: exp_land += 2000.0
            elif quads == 4: exp_land += 4000.0
            prev_quads = quads
            
        act = steps[s_idx-1][0].get("action") or {}
        prev_prices = (prev_obs.get("market") or {}).get("prices") or {}
        
        # Worker actions
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
                    
        # Track physical strawberry harvested from tiles
        prev_tiles = prev_obs["farms"][0]["tiles"]
        curr_tiles = curr_obs["farms"][0]["tiles"]
        for r in range(len(prev_tiles)):
            for c in range(len(prev_tiles[r])):
                pt = prev_tiles[r][c]
                ct = curr_tiles[r][c]
                if isinstance(pt, dict) and pt.get("crop") == "STRAWBERRY":
                    py = int(pt.get("yield_units", 0) or 0)
                    cy = int(ct.get("yield_units", 0) or 0) if isinstance(ct, dict) else 0
                    if py > cy:
                        # Yield decreased: check if worker harvested
                        for wpos, wact in zip(all_wpos, all_wacts):
                            if tuple(wpos) == (c, r) and wact and wact[0] == "HARVEST":
                                straw_harvested += (py - cy)
                                break

        # Track market transactions
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
    
    term_obs = steps[-1][0]["observation"]
    term_shed = dict(term_obs["private"]["shed"])
    term_shed_inv = sum(term_shed.values())
    
    return {
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
        "total_exp": total_buys + exp_hires,
        "total_rev": total_rev,
        "term_shed_inv": term_shed_inv,
        "max_shed_fill": max_shed_fill,
        "straw_avg_p": float(np.mean(straw_prices)),
        "straw_min_p": int(min(straw_prices)),
        "milk_avg_p": float(np.mean(milk_prices)),
        "milk_min_p": int(min(milk_prices)),
        "actions_count": actions_count,
        "town_shops_timeline": town_shops_timeline
    }

def run_worker_task(args):
    arm_name, agent_fn, seed = args
    res = run_single_match(agent_fn, seed)
    return arm_name, seed, res

def execute_50seed_suite():
    arms = {
        "A_Baseline": cl_baseline,
        "B_Gated_M1": cl_gated,
        "C_Prio_M3": cl_harvest_prio,
        "D_Pair_M1_M3": cl_pair
    }
    
    tasks = []
    for arm_name, agent_fn in arms.items():
        for s in SEEDS_50:
            tasks.append((arm_name, agent_fn, s))
            
    print(f"Launching 50-Seed Benchmark: {len(tasks)} matches across {len(arms)} arms on 10 parallel processes...")
    
    results = {arm_name: {} for arm_name in arms}
    with ProcessPoolExecutor(max_workers=10) as executor:
        for arm_name, seed, res in executor.map(run_worker_task, tasks):
            results[arm_name][seed] = res
            
    with open("scratch/50seed_hostile_audit_raw.json", "w") as f:
        json.dump(results, f, indent=2)
        
    print("50-Seed Benchmark Complete! Processing paired statistics...")
    return results

if __name__ == "__main__":
    execute_50seed_suite()
