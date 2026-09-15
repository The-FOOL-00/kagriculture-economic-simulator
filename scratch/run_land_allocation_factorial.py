"""
Land Allocation Factorial Screening Suite
Executes 100 Matched Seeds (1000-1099) across Experimental Arms:
- Arm A: CL-Economic-V1 (Baseline Control)
- Arm B: CL-Fixed-Zoning-V1 (Fixed 40/16/26/14 Control)
- Arm C1: Fixed Strawberry-Heavy (48/8/10/14)
- Arm C2: Fixed Melon-Heavy (32/24/10/14)
- Arm C3: Fixed Balanced (36/12/20/14)
- Arm D: CL-Dynamic-Land-V1 (Dynamic Land Allocator)
- Benchmark: Frozen V2 (Slot 2 Aethel Refined)

Records for every match:
- Final Reward
- Commodity Sales (units of Strawberry, Melon, Wool, Milk, Fertilizer, Wheat)
- Action Profile (Productive, Movement, Idle/Pass)
- Occupied Tiles, Workers, Output per Tile, Output per Worker
"""

import sys
import time
import json
import numpy as np
from collections import Counter
from kaggle_environments import make
from concurrent.futures import ProcessPoolExecutor, as_completed

PRODUCTIVE_OPS = frozenset([
    "PLANT", "WATER", "HARVEST", "FERTILIZE", "FEED", "CARE",
    "COLLECT_FERTILIZER", "BUILD_PASTURE", "BUILD_COOP", "PLACE", "DIG"
])
MOVE_OPS = frozenset(["NORTH", "SOUTH", "EAST", "WEST"])

def run_single_match(args):
    agent_path, seed = args
    cfg = {"episodeSteps": 720, "seed": seed}
    env = make("kaggriculture", configuration=cfg, debug=False)
    env.run([agent_path, "starter"])
    
    # Extract final reward
    r = float(env.steps[-1][0].get("reward", 0.0) or 0.0)
    
    # Track sales
    sales = Counter()
    prod_actions = 0
    move_actions = 0
    idle_actions = 0
    
    for s in env.steps:
        act = s[0].get("action", {}) or {}
        for o in act.get("market", []):
            if o[0] == "SELL":
                sales[o[1]] += int(o[2])
                
        farmer_act = act.get("farmer")
        hands_act = act.get("hands", [])
        all_acts = [farmer_act] + hands_act
        for a in all_acts:
            if not a:
                idle_actions += 1
            elif a[0] in PRODUCTIVE_OPS:
                prod_actions += 1
            elif a[0] in MOVE_OPS:
                move_actions += 1
            elif a[0] == "PASS":
                idle_actions += 1
            else:
                prod_actions += 1
                
    # Sample final farm state
    last_obs = env.steps[-1][0]["observation"]
    farm = last_obs["farms"][0]
    tiles = farm["tiles"]
    workers_count = 1 + len(farm.get("hands", []))
    
    occupied_tiles = 0
    for row in tiles:
        for t in row:
            if isinstance(t, dict):
                occupied_tiles += 1
                
    return seed, {
        "reward": r,
        "sales": dict(sales),
        "prod_actions": prod_actions,
        "move_actions": move_actions,
        "idle_actions": idle_actions,
        "workers": workers_count,
        "occupied_tiles": occupied_tiles
    }

def evaluate_arm(name, path, seeds):
    t0 = time.time()
    tasks = [(path, s) for s in seeds]
    results = {}
    
    with ProcessPoolExecutor(max_workers=8) as ex:
        futs = [ex.submit(run_single_match, t) for t in tasks]
        for f in as_completed(futs):
            s, m_res = f.result()
            results[s] = m_res
            
    rewards = [results[s]["reward"] for s in seeds]
    mean_r = float(np.mean(rewards))
    std_r = float(np.std(rewards))
    ci95 = 1.96 * std_r / np.sqrt(len(seeds))
    med_r = float(np.median(rewards))
    
    straws = [results[s]["sales"].get("STRAWBERRY", 0) for s in seeds]
    melons = [results[s]["sales"].get("MELON", 0) for s in seeds]
    wools = [results[s]["sales"].get("WOOL", 0) for s in seeds]
    milks = [results[s]["sales"].get("MILK", 0) for s in seeds]
    ferts = [results[s]["sales"].get("FERTILIZER", 0) for s in seeds]
    wheats = [results[s]["sales"].get("WHEAT", 0) for s in seeds]
    
    prods = [results[s]["prod_actions"] for s in seeds]
    moves = [results[s]["move_actions"] for s in seeds]
    idles = [results[s]["idle_actions"] for s in seeds]
    
    elapsed = time.time() - t0
    summary = {
        "name": name,
        "path": path,
        "n_seeds": len(seeds),
        "mean_reward": mean_r,
        "std_reward": std_r,
        "ci95_reward": ci95,
        "median_reward": med_r,
        "min_reward": float(np.min(rewards)),
        "max_reward": float(np.max(rewards)),
        "mean_straw": float(np.mean(straws)),
        "mean_melon": float(np.mean(melons)),
        "mean_wool": float(np.mean(wools)),
        "mean_milk": float(np.mean(milks)),
        "mean_fert": float(np.mean(ferts)),
        "mean_wheat": float(np.mean(wheats)),
        "mean_prod": float(np.mean(prods)),
        "mean_move": float(np.mean(moves)),
        "mean_idle": float(np.mean(idles)),
        "elapsed_sec": elapsed,
        "seed_results": results
    }
    
    print(f"[{name}] {elapsed:.1f}s | Mean: ${mean_r:10.2f} ± ${ci95:7.2f} | Med: ${med_r:10.2f} | Straw: {np.mean(straws):5.1f} | Wool: {np.mean(wools):5.1f} | Melon: {np.mean(melons):5.1f} | Wheat: {np.mean(wheats):5.1f} | Fert: {np.mean(ferts):5.1f}")
    return summary

if __name__ == "__main__":
    seeds = list(range(1000, 1100)) # 100 seeds
    print(f"Starting 100-Seed Factorial Screening on Seeds {seeds[0]}–{seeds[-1]}...")
    
    arms = [
        ("Arm A: CL-Economic-V1", "candidates/candidate_cl_economic_v1.py"),
        ("Arm B: Fixed Zoning (40/16/26/14)", "candidates/candidate_cl_fixed_zoning_v1.py"),
        ("Arm C1: Fixed Straw-Heavy", "candidates/candidate_cl_fixed_straw_heavy.py"),
        ("Arm C2: Fixed Melon-Heavy", "candidates/candidate_cl_fixed_melon_heavy.py"),
        ("Arm C3: Fixed Balanced", "candidates/candidate_cl_fixed_balanced.py"),
        ("Arm D: Dynamic Land Allocator", "candidates/candidate_cl_dynamic_land_v1.py"),
        ("Benchmark: Frozen V2", "candidates/slot2_aethel_refined_v2.py")
    ]
    
    all_summaries = {}
    for name, path in arms:
        all_summaries[name] = evaluate_arm(name, path, seeds)
        
    with open("scratch/land_allocation_factorial_results.json", "w") as f:
        # Save without raw per-seed full traces to keep JSON clean
        compact_summaries = {}
        for k, v in all_summaries.items():
            compact = dict(v)
            compact.pop("seed_results", None)
            compact_summaries[k] = compact
        json.dump(compact_summaries, f, indent=2)
        
    print("\nFactorial Screening Complete. Saved to scratch/land_allocation_factorial_results.json.")
