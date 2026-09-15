import json
import os
import sys
import numpy as np
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor

PROJECT_ROOT = os.path.abspath(".")
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import kaggle_environments
from candidates.candidate_cl_fert_gated import agent as m1_agent
from candidates.slot2_aethel_refined_v2 import agent as v2_agent

SEEDS = list(range(1000, 1050)) # 50 seeds

def profile_match(args):
    agent_type, seed = args
    agent_fn = m1_agent if agent_type == "M1" else v2_agent
    
    env = kaggle_environments.make("kaggriculture", configuration={"seed": seed})
    steps = env.run([agent_fn, "starter"])
    
    actions = defaultdict(int)
    
    # Wheat tracking
    wheat_plots_planted = 0
    wheat_harvested_units = 0
    wheat_decayed_units = 0
    wheat_bought = 0
    wheat_sold = 0
    
    # Strawberry tracking
    straw_plots_planted = 0
    straw_plant_days = []
    straw_harvested_units = 0
    straw_sold = 0
    straw_pot_cycles = 0
    straw_fert_cycles = 0
    straw_unfert_cycles = 0
    
    # Melon tracking
    melon_plots_planted = 0
    melon_harvested_units = 0
    melon_sold = 0
    
    # Wool & Sheep tracking
    sheep_bought = 0
    sheep_buy_days = []
    cows_bought = 0
    wool_shears = 0
    wool_units_harvested = 0
    wool_sold = 0
    feed_actions_sheep = 0
    feed_actions_cow = 0
    care_actions_sheep = 0
    care_actions_cow = 0
    
    # Movement & Logistics
    moves_total = 0
    moves_with_cargo = 0
    moves_empty = 0
    shed_drops = 0
    shed_units_dropped = 0
    worker_passes = 0
    
    # Cash over time (at end of each day)
    daily_cash = {}
    
    prev_quads = len(steps[0][0]["observation"]["farms"][0].get("unlocked_quadrants") or ["NW"])
    
    for s_idx in range(1, len(steps)):
        prev_obs = steps[s_idx-1][0]["observation"]
        curr_obs = steps[s_idx][0]["observation"]
        act = steps[s_idx][0].get("action") or {}
        
        day = prev_obs["day"]
        hour = prev_obs["hour"]
        prev_farm = prev_obs["farms"][0]
        curr_farm = curr_obs["farms"][0]
        
        prev_tiles = prev_farm["tiles"]
        curr_tiles = curr_farm["tiles"]
        prev_workers = ([prev_farm["farmer"]] if prev_farm["farmer"] else []) + [h for h in prev_farm["hands"] if h]
        prev_invs = prev_obs["private"]["inventories"]
        
        # Track daily cash at midnight
        if prev_obs["day"] != curr_obs["day"] or s_idx == len(steps) - 1:
            daily_cash[day] = prev_farm["money"]
            
        # Detect Plantings
        for y in range(10):
            for x in range(10):
                pt = prev_tiles[y][x]
                ct = curr_tiles[y][x]
                was_plant = isinstance(pt, dict) and pt.get("kind") == "PLANT"
                is_plant = isinstance(ct, dict) and ct.get("kind") == "PLANT"
                if is_plant and not was_plant:
                    crop = ct.get("crop")
                    if crop == "WHEAT":
                        wheat_plots_planted += 1
                    elif crop == "STRAWBERRY":
                        straw_plots_planted += 1
                        p_day = ct.get("planted_day", day)
                        straw_plant_days.append(p_day)
                        # Potential cycles
                        for k in range(4):
                            if p_day + 10 + 2 * k <= 29:
                                straw_pot_cycles += 1
                    elif crop == "MELON":
                        melon_plots_planted += 1
                        
                # Detect harvest and decay
                if was_plant and is_plant and pt.get("crop") == ct.get("crop"):
                    py = int(pt.get("yield_units", 0) or 0)
                    cy = int(ct.get("yield_units", 0) or 0)
                    if py > cy:
                        delta_y = py - cy
                        crop = pt.get("crop")
                        if crop == "WHEAT": wheat_harvested_units += delta_y
                        elif crop == "STRAWBERRY": straw_harvested_units += delta_y
                        elif crop == "MELON": melon_harvested_units += delta_y
                elif was_plant and not is_plant:
                    # Tile cleared (harvest of final crop or rot)
                    py = int(pt.get("yield_units", 0) or 0)
                    crop = pt.get("crop")
                    if crop == "WHEAT":
                        wheat_harvested_units += py

        # Detect strawberry production nights
        if prev_obs["day"] != curr_obs["day"]:
            night_day = prev_obs["day"]
            for y in range(10):
                for x in range(10):
                    pt = prev_tiles[y][x]
                    ct = curr_tiles[y][x]
                    if isinstance(pt, dict) and pt.get("crop") == "STRAWBERRY" and isinstance(ct, dict):
                        p_day = int(pt.get("planted_day", 0) or 0)
                        if night_day in [p_day + 9, p_day + 11, p_day + 13, p_day + 15]:
                            was_watered = bool(pt.get("watered_today"))
                            fert_until = int(pt.get("fertilized_until_day", -1) or -1)
                            if was_watered and fert_until >= night_day:
                                straw_fert_cycles += 1
                            else:
                                straw_unfert_cycles += 1

        # Check worker actions
        all_acts = ([act.get("farmer")] if act.get("farmer") else []) + [h for h in act.get("hands", []) if h]
        for w_idx, w_act in enumerate(all_acts):
            if not w_act: continue
            cmd = w_act[0]
            actions[cmd] += 1
            
            w_inv = prev_invs[w_idx] if w_idx < len(prev_invs) else {}
            cargo_qty = sum(w_inv.values())
            
            if cmd in ("NORTH", "SOUTH", "EAST", "WEST"):
                moves_total += 1
                if cargo_qty > 0:
                    moves_with_cargo += 1
                else:
                    moves_empty += 1
            elif cmd == "PASS":
                worker_passes += 1
            elif cmd == "DROP":
                shed_drops += 1
                shed_units_dropped += cargo_qty
            elif cmd == "PLANT":
                p_crop = w_act[1] if len(w_act) > 1 else "UNKNOWN"
                actions[f"PLANT_{p_crop}"] += 1
            elif cmd == "CARE":
                # Check tile underneath worker
                if w_idx < len(prev_workers) and prev_workers[w_idx]:
                    wx, wy = prev_workers[w_idx]
                    t = prev_tiles[wy][wx]
                    if isinstance(t, dict):
                        an = t.get("animal")
                        if an == "SHEEP":
                            care_actions_sheep += 1
                            wool_shears += 1
                            wool_units_harvested += 4 # Sheep shears give 4 wool
                        elif an == "COW":
                            care_actions_cow += 1
            elif cmd == "FEED":
                if w_idx < len(prev_workers) and prev_workers[w_idx]:
                    wx, wy = prev_workers[w_idx]
                    t = prev_tiles[wy][wx]
                    if isinstance(t, dict):
                        an = t.get("animal")
                        if an == "SHEEP": feed_actions_sheep += 1
                        elif an == "COW": feed_actions_cow += 1

        # Market orders
        for order in act.get("market") or []:
            if not order: continue
            cmd = order[0]
            item = order[1] if len(order) > 1 else None
            qty = int(order[2]) if len(order) > 2 else 1
            actions[cmd] += qty
            if cmd == "BUY_ANIMAL":
                if item == "SHEEP":
                    sheep_bought += qty
                    sheep_buy_days.extend([day] * qty)
                elif item == "COW":
                    cows_bought += qty
            elif cmd == "BUY_PRODUCT" and item == "WHEAT":
                wheat_bought += qty
            elif cmd == "SELL":
                if item == "WHEAT": wheat_sold += qty
                elif item == "STRAWBERRY": straw_sold += qty
                elif item == "MELON": melon_sold += qty
                elif item == "WOOL": wool_sold += qty

    term_obs = steps[-1][0]["observation"]
    term_shed = term_obs["private"]["shed"]
    term_invs = term_obs["private"]["inventories"]
    
    term_wheat_shed = term_shed.get("WHEAT", 0)
    term_wheat_pockets = sum(inv.get("WHEAT", 0) for inv in term_invs)
    
    term_reward = float(steps[-1][0]["reward"])
    
    return {
        "agent": agent_type,
        "seed": seed,
        "reward": term_reward,
        "actions": dict(actions),
        "wheat": {
            "planted_plots": wheat_plots_planted,
            "harvested_units": wheat_harvested_units,
            "bought_units": wheat_bought,
            "sold_units": wheat_sold,
            "term_shed": term_wheat_shed,
            "term_pockets": term_wheat_pockets,
        },
        "strawberry": {
            "planted_plots": straw_plots_planted,
            "mean_plant_day": float(np.mean(straw_plant_days)) if straw_plant_days else 0.0,
            "harvested_units": straw_harvested_units,
            "sold_units": straw_sold,
            "potential_cycles": straw_pot_cycles,
            "fert_cycles": straw_fert_cycles,
            "unfert_cycles": straw_unfert_cycles,
        },
        "melon": {
            "planted_plots": melon_plots_planted,
            "harvested_units": melon_harvested_units,
            "sold_units": melon_sold,
        },
        "sheep_wool": {
            "sheep_bought": sheep_bought,
            "first_sheep_day": float(min(sheep_buy_days)) if sheep_buy_days else -1.0,
            "last_sheep_day": float(max(sheep_buy_days)) if sheep_buy_days else -1.0,
            "mean_sheep_day": float(np.mean(sheep_buy_days)) if sheep_buy_days else -1.0,
            "cows_bought": cows_bought,
            "wool_shears": wool_shears,
            "wool_units_harvested": wool_units_harvested,
            "wool_sold": wool_sold,
            "feed_sheep": feed_actions_sheep,
            "feed_cow": feed_actions_cow,
            "care_sheep": care_actions_sheep,
            "care_cow": care_actions_cow,
        },
        "logistics": {
            "moves_total": moves_total,
            "moves_with_cargo": moves_with_cargo,
            "moves_empty": moves_empty,
            "shed_drops": shed_drops,
            "shed_units_dropped": shed_units_dropped,
            "worker_passes": worker_passes,
            "avg_drop_size": shed_units_dropped / max(1, shed_drops)
        },
        "daily_cash": daily_cash
    }

def main():
    print(f"Launching Deep Behavioral & Lifecycle Profiling: M1 vs V2 (Seeds 1000-1049, N=50)...")
    tasks = []
    for s in SEEDS:
        tasks.append(("M1", s))
        tasks.append(("V2", s))
        
    results = {"M1": [], "V2": []}
    with ProcessPoolExecutor(max_workers=8) as executor:
        for res in executor.map(profile_match, tasks):
            results[res["agent"]].append(res)
            
    out_path = "scratch/deep_behavioral_fingerprint_m1_v2.json"
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Deep profiling complete. Results saved to {out_path}.")

if __name__ == "__main__":
    main()
