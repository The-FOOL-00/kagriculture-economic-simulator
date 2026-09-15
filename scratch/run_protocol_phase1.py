"""
Protocol Steps 1 - 5 Runner
============================
Step 1: 20 Baseline Seeds (1000-1019) on CL-Economic-V1 vs starter
Step 2: Seed 1000 Full Timestep Forensics
Step 3: Movement Action Classification (A-K) on Seed 1000
Step 4: Cross-Zone Transition Matrix & Forensic Case Studies on Seed 1000
Step 5: 20 Diagnostic Seeds (1020-1039) on CL-Economic-V1 to test 429-turn claim
"""

import sys
import os
import copy
import json
import time
from collections import defaultdict, Counter
import numpy as np
from concurrent.futures import ProcessPoolExecutor, as_completed

PROJECT_ROOT = os.path.abspath(".")
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import kaggle_environments
from candidates.candidate_cl_economic_v1 import ClosedLoopEconomicV1

BOARD = 10
TPD = 24
SHED_ACCESS = frozenset([(4, 4), (5, 4), (4, 5), (5, 5)])
WELL_ACCESS = frozenset([(4, 5), (5, 5), (4, 6), (5, 6)])

def _dist(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])

def _quad(x, y):
    if (x, y) in SHED_ACCESS:
        return "SHED"
    if x < 5 and y < 5: return "NW"
    if x >= 5 and y < 5: return "NE"
    if x < 5 and y >= 5: return "SW"
    return "SE"

PRODUCTIVE_OPS = frozenset([
    "WATER", "HARVEST", "FEED", "CARE", "PLANT", "BUILD_PASTURE",
    "FERTILIZE", "COLLECT_FERTILIZER", "DIG", "DROP", "PICKUP", "PLACE"
])
MOVE_OPS = frozenset(["NORTH", "SOUTH", "EAST", "WEST"])

def run_single_seed_metrics(seed, agent_cls_factory=ClosedLoopEconomicV1):
    agent_inst = agent_cls_factory()
    cfg = {"episodeSteps": 720, "seed": seed}
    env = kaggle_environments.make("kaggriculture", configuration=cfg, debug=False)
    env.run([agent_inst, "starter"])
    
    steps = env.steps
    total_steps = len(steps)
    
    # Track statistics
    straw_harvested = 0
    wool_harvested = 0
    wheat_harvested = 0
    milk_harvested = 0
    
    feed_bought = 0
    fertilizer_applied = 0
    fertilizer_sold = 0
    
    movement_turns = 0
    productive_turns = 0
    idle_turns = 0
    
    water_completion_daily = []
    care_completion_daily = []
    
    cross_zone_moves = 0
    
    for s_idx in range(1, total_steps):
        prev_f = steps[s_idx - 1][0]["observation"]["farms"][0]
        curr_f = steps[s_idx][0]["observation"]["farms"][0]
        
        act = steps[s_idx][0].get("action") or {}
        farmer_act = act.get("farmer") or ["PASS"]
        hands_act = act.get("hands") or []
        all_acts = [farmer_act] + hands_act
        
        prev_farmer = tuple(prev_f["farmer"])
        prev_hands = [tuple(h) for h in prev_f["hands"]]
        prev_workers = [prev_farmer] + prev_hands
        
        # Track market orders
        for o in act.get("market") or []:
            if isinstance(o, list) and len(o) > 2:
                if o[0] == "BUY_PRODUCT" and o[1] == "WHEAT":
                    feed_bought += int(o[2])
                elif o[0] == "SELL" and o[1] == "FERTILIZER":
                    fertilizer_sold += int(o[2])
                    
        # Track worker actions
        for w_idx, a in enumerate(all_acts):
            if not a:
                idle_turns += 1
                continue
            op = a[0]
            if op in MOVE_OPS:
                movement_turns += 1
                if w_idx < len(prev_workers):
                    p0 = prev_workers[w_idx]
                    dx, dy = 0, 0
                    if op == "NORTH": dy = -1
                    elif op == "SOUTH": dy = 1
                    elif op == "EAST": dx = 1
                    elif op == "WEST": dx = -1
                    p1 = (p0[0] + dx, p0[1] + dy)
                    if _quad(p0[0], p0[1]) != _quad(p1[0], p1[1]):
                        cross_zone_moves += 1
            elif op in PRODUCTIVE_OPS:
                productive_turns += 1
                if op == "FERTILIZE":
                    fertilizer_applied += 1
                elif op == "HARVEST":
                    if w_idx < len(prev_workers):
                        pos = prev_workers[w_idx]
                        t = prev_f["tiles"][pos[1]][pos[0]]
                        if isinstance(t, dict):
                            yu = int(t.get("yield_units", 0) or 0)
                            k = t.get("kind")
                            if k == "PLANT":
                                crop = t.get("crop")
                                if crop == "STRAWBERRY": straw_harvested += yu
                                elif crop == "WHEAT": wheat_harvested += yu
                            elif k == "PASTURE":
                                anim = t.get("animal")
                                if anim == "SHEEP": wool_harvested += yu
                                elif anim == "COW": milk_harvested += yu
            else:
                idle_turns += 1
                
        # Daily completion rates at end of day (hour 23)
        if (s_idx % TPD) == (TPD - 1):
            f_tiles = curr_f["tiles"]
            plants = [t for row in f_tiles for t in row if isinstance(t, dict) and t.get("kind") == "PLANT"]
            if plants:
                watered = sum(1 for t in plants if t.get("watered_today"))
                water_completion_daily.append(watered / len(plants))
            animals = [t for row in f_tiles for t in row if isinstance(t, dict) and t.get("kind") == "PASTURE" and t.get("animal")]
            if animals:
                cared = sum(1 for t in animals if t.get("cared_today"))
                care_completion_daily.append(cared / len(animals))
                
    final_f = steps[-1][0]["observation"]["farms"][0]
    final_reward = float(steps[-1][0].get("reward") or 0.0)
    terminal_cash = float(final_f.get("money") or 0.0)
    num_workers = len(final_f.get("hands") or []) + 1
    
    # Terminal inventory
    priv = steps[-1][0]["observation"].get("private") or {}
    shed = priv.get("shed") or {}
    invs = priv.get("inventories") or []
    total_inv = defaultdict(int)
    for k, v in shed.items():
        total_inv[k] += int(v or 0)
    for inv in invs:
        for k, v in inv.items():
            total_inv[k] += int(v or 0)
            
    return {
        "seed": seed,
        "reward": final_reward,
        "strawberry_harvested": straw_harvested,
        "wool_harvested": wool_harvested,
        "wheat_harvested": wheat_harvested,
        "milk_harvested": milk_harvested,
        "feed_bought": feed_bought,
        "fertilizer_applied": fertilizer_applied,
        "fertilizer_sold": fertilizer_sold,
        "movement_turns": movement_turns,
        "productive_turns": productive_turns,
        "idle_turns": idle_turns,
        "num_workers": num_workers,
        "terminal_cash": terminal_cash,
        "terminal_inventory": dict(total_inv),
        "watering_completion": float(np.mean(water_completion_daily)) if water_completion_daily else 1.0,
        "animal_care_completion": float(np.mean(care_completion_daily)) if care_completion_daily else 1.0,
        "cross_zone_moves": cross_zone_moves
    }

def run_seed_worker(args):
    seed = args
    return run_single_seed_metrics(seed)

def execute_batch(seeds, max_workers=10):
    results = {}
    with ProcessPoolExecutor(max_workers=max_workers) as ex:
        futs = {ex.submit(run_seed_worker, s): s for s in seeds}
        for f in as_completed(futs):
            res = f.result()
            results[res["seed"]] = res
    return [results[s] for s in seeds]

if __name__ == "__main__":
    print("Testing single seed 1000...")
    t0 = time.time()
    res1000 = run_single_seed_metrics(1000)
    print(f"Seed 1000 finished in {time.time()-t0:.2f}s:")
    print(json.dumps(res1000, indent=2))
