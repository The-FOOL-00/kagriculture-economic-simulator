"""
Phase 1 & Phase 2: Comprehensive Watering Forensics & Comparative Reconstruction
================================================================================
Instruments Frozen V2 and CL-Economic-V1 across Seeds 1000–1009 to:
1. Reconstruct every single watering event (ledger).
2. Decompose watering actions by crop type, crop age, yield status, and maturity state.
3. Detect skipped watering opportunities (unwatered days on active crops).
4. Measure movement turns directly preceding watering actions vs other actions.
5. Provide the definitive answer to: Does V2 actually water fewer crops?
"""

import sys
import os
import copy
import json
import time
from collections import defaultdict, Counter
import numpy as np

PROJECT_ROOT = os.path.abspath(".")
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import kaggle_environments
from candidates.slot2_aethel_refined_v2 import agent as v2_agent
from candidates.candidate_cl_economic_v1 import agent as cl_agent, CROPS_DEF

BOARD = 10
TPD = 24
SHED_ACCESS = frozenset([(4, 4), (5, 4), (4, 5), (5, 5)])

def _dist(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])

def instrument_watering_run(agent_fn, agent_name, seed):
    cfg = {"episodeSteps": 720, "seed": seed}
    env = kaggle_environments.make("kaggriculture", configuration=cfg, debug=False)
    env.run([agent_fn, "starter"])
    
    steps = env.steps
    total_steps = len(steps)
    
    watering_ledger = []
    skipped_opportunities = []
    
    # Aggregates
    crop_water_counts = Counter()
    crop_age_at_water = defaultdict(list)
    crop_yield_at_water = defaultdict(list)
    
    water_decision_categories = Counter()
    
    # Movement tracking
    worker_last_productive_pos = {}
    moves_preceding_water = []
    moves_preceding_other = []
    worker_consecutive_moves = defaultdict(int)
    
    # General metrics
    total_moves = 0
    total_productive = 0
    total_idle = 0
    water_actions_total = 0
    
    straw_harvested = 0
    wool_harvested = 0
    wheat_harvested = 0
    milk_harvested = 0
    
    daily_water_completion = []
    
    for s_idx in range(1, total_steps):
        step = s_idx - 1
        day = step // TPD
        hour = step % TPD
        
        prev_f = steps[s_idx - 1][0]["observation"]["farms"][0]
        curr_f = steps[s_idx][0]["observation"]["farms"][0]
        
        act = steps[s_idx][0].get("action") or {}
        farmer_act = act.get("farmer") or ["PASS"]
        hands_act = act.get("hands") or []
        all_acts = [farmer_act] + hands_act
        
        prev_farmer = tuple(prev_f["farmer"])
        prev_hands = [tuple(h) for h in prev_f["hands"]]
        prev_workers = [prev_farmer] + prev_hands
        
        # Check active crops on farm before actions
        prev_tiles = prev_f["tiles"]
        active_crop_tiles = []
        for y in range(BOARD):
            for x in range(BOARD):
                t = prev_tiles[y][x]
                if isinstance(t, dict) and t.get("kind") == "PLANT":
                    active_crop_tiles.append((x, y, t))
                    
        # Check daily unwatered tiles at hour 23
        if hour == 23:
            unwatered_crops = [(x, y, t) for x, y, t in active_crop_tiles if not t.get("watered_today")]
            daily_water_completion.append(1.0 - (len(unwatered_crops) / max(1, len(active_crop_tiles))))
            for x, y, t in unwatered_crops:
                crop = t.get("crop")
                age = day - int(t.get("planted_day", 0) or 0)
                yu = int(t.get("yield_units", 0) or 0)
                skipped_opportunities.append({
                    "day": day,
                    "pos": (x, y),
                    "crop": crop,
                    "age": age,
                    "yield": yu,
                    "reason": "D. skipped despite apparently needing water"
                })

        for w_idx, a in enumerate(all_acts):
            if not a:
                total_idle += 1
                worker_consecutive_moves[w_idx] = 0
                continue
            op = a[0]
            
            if op in ("NORTH", "SOUTH", "EAST", "WEST"):
                total_moves += 1
                worker_consecutive_moves[w_idx] += 1
            elif op in ("WATER", "HARVEST", "FEED", "CARE", "PLANT", "BUILD_PASTURE", "FERTILIZE", "COLLECT_FERTILIZER", "DIG", "DROP", "PICKUP", "PLACE"):
                total_productive += 1
                dist_traveled = worker_consecutive_moves[w_idx]
                worker_consecutive_moves[w_idx] = 0
                
                pos = prev_workers[w_idx] if w_idx < len(prev_workers) else (0, 0)
                
                if op == "WATER":
                    water_actions_total += 1
                    moves_preceding_water.append(dist_traveled)
                    
                    t = prev_tiles[pos[1]][pos[0]] if 0 <= pos[1] < BOARD and 0 <= pos[0] < BOARD else {}
                    crop = t.get("crop", "UNKNOWN") if isinstance(t, dict) else "UNKNOWN"
                    p_day = int(t.get("planted_day", 0) or 0) if isinstance(t, dict) else 0
                    crop_age = day - p_day
                    yield_u = int(t.get("yield_units", 0) or 0) if isinstance(t, dict) else 0
                    fert = bool(t.get("fertilized_until_day", -1) >= day) if isinstance(t, dict) else False
                    
                    c_def = CROPS_DEF.get(crop, {})
                    first_yd = c_def.get("first_yield_day", 2)
                    max_yd = c_def.get("max_yield_day", 4)
                    ongoing = c_def.get("ongoing", False)
                    
                    # Category classification
                    if crop_age < first_yd:
                        cat = "A. actively growing (pre-yield)"
                    elif first_yd <= crop_age < max_yd:
                        cat = "B. near maturity (producing early yield)"
                    elif crop_age >= max_yd:
                        if ongoing:
                            cat = "A. ongoing mature production (strawberry/tomato)"
                        else:
                            cat = "C. mature non-ongoing crop (post-max yield)"
                    else:
                        cat = "E. unclear"
                        
                    water_decision_categories[cat] += 1
                    crop_water_counts[crop] += 1
                    crop_age_at_water[crop].append(crop_age)
                    crop_yield_at_water[crop].append(yield_u)
                    
                    last_pos = worker_last_productive_pos.get(w_idx, pos)
                    dist_from_last = _dist(last_pos, pos)
                    
                    watering_ledger.append({
                        "step": step,
                        "day": day,
                        "hour": hour,
                        "worker": w_idx,
                        "crop": crop,
                        "pos": pos,
                        "crop_age": crop_age,
                        "yield": yield_u,
                        "fertilized": fert,
                        "dist_traveled": dist_traveled,
                        "dist_from_last_prod": dist_from_last,
                        "category": cat
                    })
                else:
                    moves_preceding_other.append(dist_traveled)
                    if op == "HARVEST":
                        t = prev_tiles[pos[1]][pos[0]] if 0 <= pos[1] < BOARD and 0 <= pos[0] < BOARD else {}
                        if isinstance(t, dict):
                            yu = int(t.get("yield_units", 0) or 0)
                            k = t.get("kind")
                            if k == "PLANT":
                                if t.get("crop") == "STRAWBERRY": straw_harvested += yu
                                elif t.get("crop") == "WHEAT": wheat_harvested += yu
                            elif k == "PASTURE":
                                if t.get("animal") == "SHEEP": wool_harvested += yu
                                elif t.get("animal") == "COW": milk_harvested += yu
                                
                worker_last_productive_pos[w_idx] = pos
            else:
                total_idle += 1
                worker_consecutive_moves[w_idx] = 0

    reward = float(steps[-1][0].get("reward") or 0.0)
    
    return {
        "agent": agent_name,
        "seed": seed,
        "reward": reward,
        "total_moves": total_moves,
        "total_productive": total_productive,
        "total_idle": total_idle,
        "water_actions_total": water_actions_total,
        "crop_water_counts": dict(crop_water_counts),
        "mean_crop_age_at_water": {k: float(np.mean(v)) if v else 0.0 for k, v in crop_age_at_water.items()},
        "mean_crop_yield_at_water": {k: float(np.mean(v)) if v else 0.0 for k, v in crop_yield_at_water.items()},
        "water_decision_categories": dict(water_decision_categories),
        "mean_moves_preceding_water": float(np.mean(moves_preceding_water)) if moves_preceding_water else 0.0,
        "mean_moves_preceding_other": float(np.mean(moves_preceding_other)) if moves_preceding_other else 0.0,
        "total_moves_for_water": int(np.sum(moves_preceding_water)),
        "total_moves_for_other": int(np.sum(moves_preceding_other)),
        "watering_completion_pct": float(np.mean(daily_water_completion)) * 100.0 if daily_water_completion else 100.0,
        "total_skipped_opportunities": len(skipped_opportunities),
        "straw_harvested": straw_harvested,
        "wool_harvested": wool_harvested,
        "wheat_harvested": wheat_harvested,
        "milk_harvested": milk_harvested,
        "ledger_sample": watering_ledger[:50]
    }


def run_comparative_watering_study(seeds=list(range(1000, 1010))):
    print(f"Running Phase 1 & 2 Watering Study across {len(seeds)} Seeds ({seeds[0]}–{seeds[-1]})...")
    
    v2_runs = []
    cl_runs = []
    
    t0 = time.time()
    for s in seeds:
        print(f"  Simulating Seed {s}...")
        v2_res = instrument_watering_run(v2_agent, "Frozen V2", s)
        cl_res = instrument_watering_run(cl_agent, "CL-Economic-V1", s)
        v2_runs.append(v2_res)
        cl_runs.append(cl_res)
        
    print(f"Completed simulations in {time.time()-t0:.1f}s.")
    
    # Save full forensic dump
    with open("scratch/watering_study_raw.json", "w") as f:
        json.dump({"v2": v2_runs, "cl": cl_runs}, f, indent=2)
        
    # Aggregate Comparative Table
    print("\n" + "=" * 80)
    print("PHASE 2 DIRECT COMPARISON: CL-ECONOMIC-V1 vs FROZEN V2 (SEEDS 1000–1009)")
    print("=" * 80)
    print(f"{'Metric':<36} | {'CL-Economic-V1':<18} | {'Frozen V2':<18} | {'Delta':<15}")
    print("-" * 92)
    
    metrics_to_compare = [
        ("Terminal Reward ($)", lambda r: r["reward"]),
        ("Total Water Actions", lambda r: r["water_actions_total"]),
        ("Watering Completion Rate (%)", lambda r: r["watering_completion_pct"]),
        ("Total Skipped Water Opportunities", lambda r: r["total_skipped_opportunities"]),
        ("Moves Preceding Water (Turns)", lambda r: r["total_moves_for_water"]),
        ("Moves Preceding Other (Turns)", lambda r: r["total_moves_for_other"]),
        ("Total Movement Turns", lambda r: r["total_moves"]),
        ("Total Productive Turns", lambda r: r["total_productive"]),
        ("Total Idle Turns", lambda r: r["total_idle"]),
        ("Strawberry Waterings", lambda r: r["crop_water_counts"].get("STRAWBERRY", 0)),
        ("Wheat Waterings", lambda r: r["crop_water_counts"].get("WHEAT", 0)),
        ("Melon Waterings", lambda r: r["crop_water_counts"].get("MELON", 0)),
        ("Strawberry Harvested (units)", lambda r: r["straw_harvested"]),
        ("Wool Harvested (units)", lambda r: r["wool_harvested"]),
        ("Wheat Harvested (units)", lambda r: r["wheat_harvested"]),
        ("Milk Harvested (units)", lambda r: r["milk_harvested"]),
    ]
    
    for label, fn in metrics_to_compare:
        cl_vals = [fn(r) for r in cl_runs]
        v2_vals = [fn(r) for r in v2_runs]
        cl_m = np.mean(cl_vals)
        v2_m = np.mean(v2_vals)
        delta = v2_m - cl_m
        print(f"{label:<36} | {cl_m:18.1f} | {v2_m:18.1f} | {delta:+15.1f}")
        
    print("\n--- WATERING DECISION CATEGORIES (MEAN PER RUN) ---")
    all_cats = set()
    for r in cl_runs + v2_runs:
        all_cats.update(r["water_decision_categories"].keys())
        
    print(f"{'Category':<45} | {'CL-Economic-V1':<15} | {'Frozen V2':<15} | {'Delta':<12}")
    print("-" * 92)
    for cat in sorted(all_cats):
        cl_cat = np.mean([r["water_decision_categories"].get(cat, 0) for r in cl_runs])
        v2_cat = np.mean([r["water_decision_categories"].get(cat, 0) for r in v2_runs])
        delta = v2_cat - cl_cat
        print(f"{cat:<45} | {cl_cat:15.1f} | {v2_cat:15.1f} | {delta:+12.1f}")

if __name__ == "__main__":
    run_comparative_watering_study()
