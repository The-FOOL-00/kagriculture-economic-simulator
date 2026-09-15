import json
import os
import sys
import time
from collections import defaultdict
import numpy as np
from concurrent.futures import ProcessPoolExecutor

PROJECT_ROOT = os.path.abspath(".")
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import kaggle_environments

from candidates.candidate_cl_fert_gated import agent as m1_agent
from candidates.candidate_cl_m1_wheat_expansion import agent as m1_wheat_agent
from candidates.slot2_aethel_refined_v2 import agent as v2_agent

SEEDS_50 = list(range(1000, 1050))
CROPS = ("STRAWBERRY", "MELON", "WHEAT", "CARROT", "TOMATO")

def run_telemetry_episode(args):
    arm_name, seed = args
    if arm_name == "M1":
        agent_fn = m1_agent
    elif arm_name == "M1_Wheat":
        agent_fn = m1_wheat_agent
    elif arm_name == "V2":
        agent_fn = v2_agent
    else:
        raise ValueError(f"Unknown arm {arm_name}")

    cfg = {"episodeSteps": 720, "seed": seed}
    env = kaggle_environments.make("kaggriculture", configuration=cfg)
    steps = env.run([agent_fn, "starter"])
    p = 0
    total_steps = len(steps)

    # 1. Action counters
    actions_count = {
        "PLANT": 0, "HARVEST": 0, "WATER": 0, "FERTILIZE": 0, "FEED": 0,
        "CARE": 0, "COLLECT_FERTILIZER": 0, "DROP": 0, "PICKUP": 0,
        "MOVE": 0, "PASS": 0, "DIG": 0, "BUILD_PASTURE": 0, "PLACE": 0, "OTHER": 0
    }
    
    # Granular actions of interest
    straw_harvest_actions = 0
    wheat_harvest_actions = 0
    animal_care_actions = 0
    animal_feed_actions = 0

    # 2. Financial tracking
    rev_by_item = {
        "STRAWBERRY": 0.0, "MELON": 0.0, "MILK": 0.0, "WOOL": 0.0,
        "WHEAT": 0.0, "FERTILIZER": 0.0, "EGG": 0.0
    }
    qty_sold = {k: 0 for k in rev_by_item}
    exp_seeds = 0.0
    exp_feed = 0.0
    wheat_seed_spent = 0.0
    wheat_seed_bought = 0

    # 3. Wheat physical mass balance
    wheat_planted_plots = 0
    wheat_planting_events = 0
    failed_wheat_planting = 0
    wheat_harvest_events = 0
    wheat_units_harvested = 0
    wheat_units_purchased = 0
    wheat_units_eaten = 0
    wheat_units_sold = 0
    
    # Wave tracking: day -> count of wheat plantings
    wheat_plantings_by_day = defaultdict(int)
    wheat_harvests_by_day = defaultdict(int)
    wheat_harvest_yield_by_day = defaultdict(int)

    # Predecessor tracking for wheat plots: tile -> last crop/kind before wheat
    tile_history = {}  # (x, y) -> str ("MELON", "WHEAT", "STRAWBERRY", "PASTURE", "INITIAL_EMPTY", "UNLOCKED_EMPTY")
    predecessors_of_wheat = defaultdict(int)

    # Strawberry metrics
    straw_planted_events = 0
    straw_harvested_units = 0
    straw_fertilized_events = 0

    # Initialize tile history at step 0
    initial_farm = steps[0][p]["observation"]["farms"][p]
    init_tiles = initial_farm.get("tiles") or []
    for r in range(len(init_tiles)):
        for c in range(len(init_tiles[r])):
            t = init_tiles[r][c]
            if t == "LOCKED":
                tile_history[(c, r)] = "LOCKED"
            elif t is None:
                tile_history[(c, r)] = "INITIAL_EMPTY"
            elif isinstance(t, dict):
                tile_history[(c, r)] = t.get("crop") or t.get("kind") or "UNKNOWN"

    for s_idx in range(1, total_steps):
        prev_obs = steps[s_idx - 1][p]["observation"]
        curr_obs = steps[s_idx][p]["observation"]
        prev_farm = prev_obs["farms"][p]
        curr_farm = curr_obs["farms"][p]
        prev_priv = prev_obs.get("private") or {}
        curr_priv = curr_obs.get("private") or {}

        day = s_idx // 24
        hr = s_idx % 24
        
        act = steps[s_idx][p].get("action") or {}
        market_orders = act.get("market") or []
        prev_prices = (prev_obs.get("market") or {}).get("prices") or {}

        # Track market orders
        for order in market_orders:
            if not isinstance(order, list) or len(order) < 2:
                continue
            cmd = order[0]
            item = order[1]
            qty = int(order[2]) if len(order) > 2 else 1
            if cmd == "SELL" and item in rev_by_item:
                p_val = float(prev_prices.get(item, 0.0))
                rev_by_item[item] += qty * p_val
                qty_sold[item] += qty
                if item == "WHEAT":
                    wheat_units_sold += qty
            elif cmd == "BUY_SEED":
                cost = 10 if item == "WHEAT" else (100 if item == "STRAWBERRY" else (80 if item == "MELON" else 50))
                exp_seeds += qty * cost
                if item == "WHEAT":
                    wheat_seed_spent += qty * cost
                    wheat_seed_bought += qty
            elif cmd == "BUY_PRODUCT" and item == "WHEAT":
                exp_feed += qty * 30
                wheat_units_purchased += qty

        # Track worker actions
        all_wacts = [act.get("farmer")] + (act.get("hands") or [])
        positions = [prev_farm.get("farmer")] + (prev_farm.get("hands") or [])
        for w_idx, wact in enumerate(all_wacts):
            if not wact:
                actions_count["PASS"] += 1
                continue
            op = wact[0] if isinstance(wact, list) and len(wact) > 0 else (wact if isinstance(wact, str) else "PASS")
            if op in ("NORTH", "SOUTH", "EAST", "WEST"):
                actions_count["MOVE"] += 1
            elif op in actions_count:
                actions_count[op] += 1
            else:
                actions_count["OTHER"] += 1

            # Detailed checks
            wpos = positions[w_idx] if w_idx < len(positions) else None
            if op == "FEED":
                animal_feed_actions += 1
                wheat_units_eaten += 1
            elif op == "CARE":
                animal_care_actions += 1
            elif op == "HARVEST":
                if wpos:
                    wx, wy = wpos
                    pt = prev_farm["tiles"][wy][wx] if 0 <= wy < len(prev_farm["tiles"]) and 0 <= wx < len(prev_farm["tiles"][0]) else None
                    if isinstance(pt, dict):
                        if pt.get("crop") == "STRAWBERRY":
                            straw_harvest_actions += 1
                        elif pt.get("crop") == "WHEAT":
                            wheat_harvest_actions += 1
            elif op == "PLANT":
                plant_crop = wact[1] if len(wact) > 1 else None
                if plant_crop == "WHEAT":
                    # Check if valid
                    if wpos:
                        wx, wy = wpos
                        pt = prev_farm["tiles"][wy][wx] if 0 <= wy < len(prev_farm["tiles"]) and 0 <= wx < len(prev_farm["tiles"][0]) else None
                        w_seeds = int(prev_priv.get("seeds", {}).get("WHEAT", 0) or 0)
                        if pt is None and w_seeds > 0:
                            wheat_planting_events += 1
                        else:
                            failed_wheat_planting += 1
                elif plant_crop == "STRAWBERRY":
                    straw_planted_events += 1

        # Tile state transitions
        p_tiles = prev_farm.get("tiles") or []
        c_tiles = curr_farm.get("tiles") or []
        for r in range(len(p_tiles)):
            for c in range(len(p_tiles[r])):
                pos = (c, r)
                pt = p_tiles[r][c]
                ct = c_tiles[r][c]

                # Tile unlock
                if pt == "LOCKED" and ct != "LOCKED":
                    tile_history[pos] = "UNLOCKED_EMPTY"

                # Check wheat planting
                p_crop = pt.get("crop") if isinstance(pt, dict) else None
                c_crop = ct.get("crop") if isinstance(ct, dict) else None

                if p_crop != "WHEAT" and c_crop == "WHEAT":
                    wheat_planted_plots += 1
                    wheat_plantings_by_day[day] += 1
                    pred = tile_history.get(pos, "INITIAL_EMPTY")
                    predecessors_of_wheat[pred] += 1

                # Check strawberry fertilization
                if isinstance(pt, dict) and pt.get("crop") == "STRAWBERRY":
                    p_fert = pt.get("fertilized_until_day", -1)
                    c_fert = ct.get("fertilized_until_day", -1) if isinstance(ct, dict) else -1
                    if c_fert > p_fert and c_fert >= day:
                        straw_fertilized_events += 1

                # Check harvests vs decay
                if isinstance(pt, dict) and pt.get("crop") == "WHEAT":
                    py = int(pt.get("yield_units", 0) or 0)
                    cy = int(ct.get("yield_units", 0) or 0) if isinstance(ct, dict) and ct.get("crop") == "WHEAT" else 0
                    if py > cy:
                        yield_diff = py - cy
                        wheat_units_harvested += yield_diff
                        wheat_harvest_events += 1
                        wheat_harvests_by_day[day] += 1
                        wheat_harvest_yield_by_day[day] += yield_diff

                if isinstance(pt, dict) and pt.get("crop") == "STRAWBERRY":
                    py = int(pt.get("yield_units", 0) or 0)
                    cy = int(ct.get("yield_units", 0) or 0) if isinstance(ct, dict) and ct.get("crop") == "STRAWBERRY" else 0
                    if py > cy:
                        straw_harvested_units += (py - cy)

                # Update tile history
                if isinstance(ct, dict):
                    tile_history[pos] = ct.get("crop") or ct.get("kind") or "UNKNOWN"
                elif ct is None:
                    if pos in tile_history and tile_history[pos] not in ("INITIAL_EMPTY", "UNLOCKED_EMPTY"):
                        tile_history[pos] = f"CLEARED_{tile_history[pos]}"

    # Terminal state
    last_farm = steps[-1][p]["observation"]["farms"][p]
    last_priv = steps[-1][p]["observation"].get("private") or {}
    terminal_reward = float(last_farm.get("money") or 0.0)
    terminal_shed_wheat = int(last_priv.get("shed", {}).get("WHEAT", 0) or 0)
    terminal_pocket_wheat = sum(int(inv.get("WHEAT", 0) or 0) for inv in (last_priv.get("inventories") or []))
    
    # Unharvested wheat yield remaining on tiles
    unharvested_wheat_yield = 0
    for r in range(len(last_farm.get("tiles") or [])):
        for c in range(len(last_farm["tiles"][r])):
            t = last_farm["tiles"][r][c]
            if isinstance(t, dict) and t.get("crop") == "WHEAT":
                unharvested_wheat_yield += int(t.get("yield_units", 0) or 0)

    # Mass balance equation:
    # Harvested + Purchased = Eaten + Sold + Terminal Shed + Terminal Pockets
    total_inflow = wheat_units_harvested + wheat_units_purchased
    total_outflow = wheat_units_eaten + wheat_units_sold + terminal_shed_wheat + terminal_pocket_wheat
    residual = total_inflow - total_outflow

    return {
        "arm": arm_name,
        "seed": seed,
        "terminal_reward": terminal_reward,
        "wheat_planted_plots": wheat_planted_plots,
        "wheat_planting_events": wheat_planting_events,
        "failed_wheat_planting": failed_wheat_planting,
        "wheat_harvest_events": wheat_harvest_events,
        "wheat_units_harvested": wheat_units_harvested,
        "wheat_units_purchased": wheat_units_purchased,
        "wheat_units_eaten": wheat_units_eaten,
        "wheat_units_sold": wheat_units_sold,
        "terminal_shed_wheat": terminal_shed_wheat,
        "terminal_pocket_wheat": terminal_pocket_wheat,
        "unharvested_wheat_yield": unharvested_wheat_yield,
        "total_inflow": total_inflow,
        "total_outflow": total_outflow,
        "residual": residual,
        "wheat_rev": rev_by_item["WHEAT"],
        "straw_rev": rev_by_item["STRAWBERRY"],
        "melon_rev": rev_by_item["MELON"],
        "milk_rev": rev_by_item["MILK"],
        "wool_rev": rev_by_item["WOOL"],
        "fert_rev": rev_by_item["FERTILIZER"],
        "straw_sold": qty_sold["STRAWBERRY"],
        "melon_sold": qty_sold["MELON"],
        "milk_sold": qty_sold["MILK"],
        "wool_sold": qty_sold["WOOL"],
        "fert_sold": qty_sold["FERTILIZER"],
        "wheat_sold": qty_sold["WHEAT"],
        "exp_seeds": exp_seeds,
        "exp_feed": exp_feed,
        "wheat_seed_spent": wheat_seed_spent,
        "wheat_seed_bought": wheat_seed_bought,
        "straw_planted_events": straw_planted_events,
        "straw_harvested_units": straw_harvested_units,
        "straw_fertilized_events": straw_fertilized_events,
        "actions_count": actions_count,
        "straw_harvest_actions": straw_harvest_actions,
        "wheat_harvest_actions": wheat_harvest_actions,
        "animal_care_actions": animal_care_actions,
        "animal_feed_actions": animal_feed_actions,
        "wheat_plantings_by_day": dict(wheat_plantings_by_day),
        "wheat_harvests_by_day": dict(wheat_harvests_by_day),
        "wheat_harvest_yield_by_day": dict(wheat_harvest_yield_by_day),
        "predecessors_of_wheat": dict(predecessors_of_wheat)
    }

def main():
    print(f"Executing Phase 3-5 Deep Forensics across 50 matched seeds (1000-1049)...")
    tasks = []
    for s in SEEDS_50:
        tasks.append(("M1", s))
        tasks.append(("M1_Wheat", s))
        tasks.append(("V2", s))

    results = []
    t0 = time.time()
    with ProcessPoolExecutor(max_workers=10) as executor:
        for res in executor.map(run_telemetry_episode, tasks):
            results.append(res)
            if len(results) % 30 == 0:
                print(f"Processed {len(results)}/{len(tasks)} runs ({time.time()-t0:.1f}s)...")

    out_path = "scratch/wheat_forensics_50seeds_results.json"
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Saved results to {out_path} in {time.time()-t0:.1f}s")

if __name__ == "__main__":
    main()
