"""
Deep Forensic Analysis of Strawberry & Melon Planting, Spatial Density,
Watering Efficiency, Bush Lifecycle, and Confounders
Across Seeds 1000-1009 for CL-Economic-V1 and Frozen-V2.
"""
import sys
import os
import json
import copy
import math
from collections import defaultdict
import numpy as np
from concurrent.futures import ProcessPoolExecutor, as_completed

PROJECT_ROOT = os.path.abspath(".")
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import kaggle_environments
from candidates.candidate_cl_economic_v1 import ClosedLoopEconomicV1
import candidates.slot2_aethel_refined_v2 as v2_mod

TPD = 24

def dist(p1, p2):
    return abs(p1[0] - p2[0]) + abs(p1[1] - p2[1])

def compute_spatial_metrics(coords):
    """
    coords: list of (x, y) tuples
    Returns dict of metrics
    """
    n = len(coords)
    if n == 0:
        return {
            "count": 0,
            "mean_pairwise": 0.0,
            "median_pairwise": 0.0,
            "max_pairwise": 0.0,
            "mean_nn": 0.0,
            "median_nn": 0.0,
            "bbox_area": 0,
            "cc_count": 0,
            "largest_cc_size": 0
        }
    if n == 1:
        return {
            "count": 1,
            "mean_pairwise": 0.0,
            "median_pairwise": 0.0,
            "max_pairwise": 0.0,
            "mean_nn": 0.0,
            "median_nn": 0.0,
            "bbox_area": 1,
            "cc_count": 1,
            "largest_cc_size": 1
        }
    
    # Pairwise distances
    pw_dists = []
    for i in range(n):
        for j in range(i + 1, n):
            pw_dists.append(dist(coords[i], coords[j]))
            
    # Nearest neighbor distances
    nn_dists = []
    for i in range(n):
        min_d = min(dist(coords[i], coords[j]) for j in range(n) if i != j)
        nn_dists.append(min_d)
        
    # Bounding box area
    xs = [c[0] for c in coords]
    ys = [c[1] for c in coords]
    bbox_area = (max(xs) - min(xs) + 1) * (max(ys) - min(ys) + 1)
    
    # Connected components (4-connected adjacency: dist == 1)
    adj = defaultdict(list)
    coord_set = set(coords)
    for c in coords:
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nb = (c[0] + dx, c[1] + dy)
            if nb in coord_set:
                adj[c].append(nb)
                
    visited = set()
    cc_sizes = []
    for c in coords:
        if c not in visited:
            # BFS/DFS
            comp = []
            queue = [c]
            visited.add(c)
            while queue:
                curr = queue.pop(0)
                comp.append(curr)
                for nb in adj[curr]:
                    if nb not in visited:
                        visited.add(nb)
                        queue.append(nb)
            cc_sizes.append(len(comp))
            
    return {
        "count": n,
        "mean_pairwise": float(np.mean(pw_dists)),
        "median_pairwise": float(np.median(pw_dists)),
        "max_pairwise": float(np.max(pw_dists)),
        "mean_nn": float(np.mean(nn_dists)),
        "median_nn": float(np.median(nn_dists)),
        "bbox_area": int(bbox_area),
        "cc_count": len(cc_sizes),
        "largest_cc_size": max(cc_sizes) if cc_sizes else 0
    }

def run_single_episode(seed, agent_name):
    if agent_name == "CL":
        agent_inst = ClosedLoopEconomicV1()
        agent_fn = agent_inst
    else:
        agent_fn = v2_mod.agent

    cfg = {"episodeSteps": 720, "seed": seed}
    env = kaggle_environments.make("kaggriculture", configuration=cfg, debug=False)
    env.run([agent_fn, "starter"])
    steps = env.steps
    total_steps = len(steps)

    plant_events = []
    harvest_events = []
    water_events = []
    
    # Track bushlifecycle: key = (tile_x, tile_y, planted_step)
    bushes = {}
    active_bushes = {} # (x, y) -> bush_key
    tile_last_occupant = {} # (x, y) -> crop
    
    # Worker travel tracking
    worker_last_productive_pos = {} # w_idx -> pos
    worker_last_pos = {} # w_idx -> pos
    total_travel_before_water = []
    total_travel_before_straw_water = []

    # Market / Inventory counters
    feed_bought = 0
    cows_bought = 0
    sheep_bought = 0

    for s_idx in range(1, total_steps):
        prev_obs = steps[s_idx - 1][0]["observation"]
        curr_obs = steps[s_idx][0]["observation"]
        act = steps[s_idx][0].get("action") or {}

        prev_f = prev_obs["farms"][0]
        curr_f = curr_obs["farms"][0]
        prev_priv = prev_obs["private"]
        curr_priv = curr_obs["private"]

        step = prev_obs.get("step", s_idx - 1)
        day = prev_obs.get("day", step // TPD)
        hour = prev_obs.get("hour", step % TPD)
        money = float(prev_f.get("money", 0))
        quads = list(prev_f.get("unlocked_quadrants", []))

        prev_farmer = tuple(prev_f["farmer"])
        prev_hands = [tuple(h) for h in (prev_f.get("hands") or [])]
        prev_workers = [prev_farmer] + prev_hands

        farmer_act = act.get("farmer") or ["PASS"]
        hands_act = act.get("hands") or []
        all_acts = [farmer_act] + hands_act

        prev_tiles = prev_f["tiles"]
        curr_tiles = curr_f["tiles"]

        # Track livestock from tiles or shed
        cow_count = 0
        sheep_count = 0
        for y in range(10):
            for x in range(10):
                t = prev_tiles[y][x]
                if isinstance(t, dict) and "animal" in t:
                    if t["animal"] == "COW": cow_count += 1
                    elif t["animal"] == "SHEEP": sheep_count += 1

        feed_stock = prev_priv.get("shed", {}).get("WHEAT", 0)
        fert_stock = prev_priv.get("shed", {}).get("FERTILIZER", 0)

        # Process actions
        for w_idx, a in enumerate(all_acts):
            if not a:
                continue
            op = a[0]
            w_pos = prev_workers[w_idx] if w_idx < len(prev_workers) else (4, 4)

            # Measure distance from last position
            last_p = worker_last_pos.get(w_idx, w_pos)
            dist_moved = dist(last_p, w_pos)

            if op == "PLANT":
                crop = a[1] if len(a) > 1 else "UNKNOWN"
                fx, fy = w_pos
                prev_t = prev_tiles[fy][fx]
                prev_crop = tile_last_occupant.get((fx, fy))
                is_succession = (prev_crop is not None)

                pevent = {
                    "seed": seed,
                    "agent": agent_name,
                    "step": step,
                    "day": day,
                    "hour": hour,
                    "worker_idx": w_idx,
                    "coordinate": [fx, fy],
                    "crop": crop,
                    "previous_tile_state": copy.deepcopy(prev_t),
                    "is_succession": is_succession,
                    "previous_crop": prev_crop,
                    "cash_before": money,
                    "cow_count": cow_count,
                    "sheep_count": sheep_count,
                    "num_workers": len(prev_workers),
                    "unlocked_quads": list(quads),
                    "feed_stock": feed_stock,
                    "fert_stock": fert_stock
                }
                plant_events.append(pevent)
                tile_last_occupant[(fx, fy)] = crop

                if crop == "STRAWBERRY":
                    bkey = (fx, fy, step)
                    bushes[bkey] = {
                        "coord": (fx, fy),
                        "planted_step": step,
                        "planted_day": day,
                        "water_ticks": 0,
                        "water_on_prod_days": 0,
                        "water_on_off_days": 0,
                        "harvest_events": [],
                        "total_harvested": 0,
                        "production_events": [],
                        "overflow_lost": 0,
                        "decay_lost": 0,
                        "fertilized_at_least_once": False,
                        "steps_with_yield_gt_0": 0,
                        "steps_at_capacity_4": 0
                    }
                    active_bushes[(fx, fy)] = bkey

                worker_last_productive_pos[w_idx] = w_pos

            elif op == "WATER":
                fx, fy = w_pos
                t = prev_tiles[fy][fx]
                crop_on_tile = t.get("crop") if (isinstance(t, dict) and t.get("kind") == "PLANT") else None
                was_watered = t.get("watered_today", False) if isinstance(t, dict) else False

                # Travel from last productive action
                last_prod_p = worker_last_productive_pos.get(w_idx, w_pos)
                travel_from_last_prod = dist(last_prod_p, w_pos)
                total_travel_before_water.append(travel_from_last_prod)

                is_strawberry = (crop_on_tile == "STRAWBERRY")
                if is_strawberry:
                    total_travel_before_straw_water.append(travel_from_last_prod)
                    bkey = active_bushes.get((fx, fy))
                    if bkey and bkey in bushes:
                        bushes[bkey]["water_ticks"] += 1
                        # Is today a production day for this bush?
                        # In engine: STRAWBERRY produces at transition day -> day + 1
                        # if (day + 1 - planted_day - 10) >= 0 and (day + 1 - planted_day - 10) % 2 == 0
                        # that means today is day: (day + 1 - planted_day - 10) % 2 == 0
                        pday = bushes[bkey]["planted_day"]
                        days_since_first = (day + 1) - pday - 10
                        if days_since_first >= 0 and days_since_first % 2 == 0 and (days_since_first // 2 + 1) <= 4:
                            bushes[bkey]["water_on_prod_days"] += 1
                        else:
                            bushes[bkey]["water_on_off_days"] += 1

                wevent = {
                    "seed": seed,
                    "agent": agent_name,
                    "step": step,
                    "day": day,
                    "hour": hour,
                    "worker_idx": w_idx,
                    "coordinate": [fx, fy],
                    "crop": crop_on_tile,
                    "was_watered_today": was_watered,
                    "travel_from_last_prod": travel_from_last_prod
                }
                water_events.append(wevent)
                worker_last_productive_pos[w_idx] = w_pos

            elif op == "HARVEST":
                fx, fy = w_pos
                t = prev_tiles[fy][fx]
                crop_on_tile = None
                yunits = 0
                if isinstance(t, dict):
                    crop_on_tile = t.get("crop") or t.get("animal")
                    yunits = t.get("yield_units", 0)

                hevent = {
                    "seed": seed,
                    "agent": agent_name,
                    "step": step,
                    "day": day,
                    "hour": hour,
                    "worker_idx": w_idx,
                    "coordinate": [fx, fy],
                    "crop": crop_on_tile,
                    "yield_units": yunits
                }
                harvest_events.append(hevent)
                worker_last_productive_pos[w_idx] = w_pos

                if crop_on_tile == "STRAWBERRY":
                    bkey = active_bushes.get((fx, fy))
                    if bkey and bkey in bushes:
                        bushes[bkey]["harvest_events"].append((step, day, hour, yunits))
                        bushes[bkey]["total_harvested"] += yunits

            elif op in ["FEED", "CARE", "FERTILIZE", "COLLECT_FERTILIZER", "BUILD_PASTURE"]:
                worker_last_productive_pos[w_idx] = w_pos

            worker_last_pos[w_idx] = w_pos

        # Track active strawberry bushes status across time
        for (bx, by), bkey in list(active_bushes.items()):
            currt = curr_tiles[by][bx]
            if not (isinstance(currt, dict) and currt.get("crop") == "STRAWBERRY"):
                # Bush removed or turned to weed
                del active_bushes[(bx, by)]
                continue
            
            # Check fertilization
            if currt.get("fertilized_until_day", -1) >= day:
                bushes[bkey]["fertilized_at_least_once"] = True

            yu = currt.get("yield_units", 0)
            if yu > 0:
                bushes[bkey]["steps_with_yield_gt_0"] += 1
            if yu >= 4:
                bushes[bkey]["steps_at_capacity_4"] += 1

    final_reward = float(steps[-1][0].get("reward") or 0.0)

    # Aggregate harvest totals
    crop_harvest_totals = defaultdict(int)
    for h in harvest_events:
        if h["crop"]:
            crop_harvest_totals[h["crop"]] += h["yield_units"]

    return {
        "seed": seed,
        "agent": agent_name,
        "reward": final_reward,
        "plant_events": plant_events,
        "harvest_events": harvest_events,
        "water_events": water_events,
        "bushes": bushes,
        "crop_harvest_totals": dict(crop_harvest_totals),
        "total_travel_before_water": total_travel_before_water,
        "total_travel_before_straw_water": total_travel_before_straw_water
    }

def run_all_seeds_parallel(seeds=list(range(1000, 1010))):
    tasks = []
    with ProcessPoolExecutor(max_workers=10) as executor:
        for s in seeds:
            tasks.append(executor.submit(run_single_episode, s, "CL"))
            tasks.append(executor.submit(run_single_episode, s, "V2"))
            
        results = {"CL": {}, "V2": {}}
        for fut in as_completed(tasks):
            res = fut.result()
            s = res["seed"]
            a = res["agent"]
            results[a][s] = res
            print(f"Finished {a} Seed {s}: Reward={res['reward']:.2f}, Strawberries={res['crop_harvest_totals'].get('STRAWBERRY', 0)}")
            
    return results

if __name__ == "__main__":
    print("Starting 10-seed deep extraction (Seeds 1000-1009)...")
    res = run_all_seeds_parallel(list(range(1000, 1010)))
    
    # Save raw results summary to JSON (without heavy nested bushes for fast loading, but with core data)
    summary_path = "scratch/deep_telemetry_seeds1000_1009.json"
    
    # Prepare serializable dict
    serializable = {"CL": {}, "V2": {}}
    for a in ["CL", "V2"]:
        for s in sorted(res[a].keys()):
            r = res[a][s]
            # convert bushes dict keys to str
            bushes_clean = {}
            for k, b in r["bushes"].items():
                bushes_clean[f"{k[0]}_{k[1]}_{k[2]}"] = b

            serializable[a][s] = {
                "reward": r["reward"],
                "crop_harvest_totals": r["crop_harvest_totals"],
                "plant_events": r["plant_events"],
                "harvest_events": r["harvest_events"],
                "water_events_count": len(r["water_events"]),
                "bushes": bushes_clean,
                "mean_travel_water": float(np.mean(r["total_travel_before_water"])) if r["total_travel_before_water"] else 0.0,
                "mean_travel_straw_water": float(np.mean(r["total_travel_before_straw_water"])) if r["total_travel_before_straw_water"] else 0.0
            }
            
    with open(summary_path, "w") as f:
        json.dump(serializable, f)
    print(f"Successfully saved to {summary_path}")
