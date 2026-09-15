"""
100-Seed Matched Benchmark for Candidate CL-Temporal-V3 vs Starter
Seeds 1000-1099
"""
import sys
import os
import time
import json
import numpy as np
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor, as_completed

PROJECT_ROOT = os.path.abspath(".")
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import kaggle_environments
from candidates.candidate_cl_temporal_v3 import agent_fn as v3_agent

SEEDS = list(range(1000, 1100))

def _run_seed(seed):
    cfg = {"episodeSteps": 720, "seed": seed}
    env = kaggle_environments.make("kaggriculture", configuration=cfg)
    try:
        env.run([v3_agent, "starter"])
        steps = env.steps
        r = float(steps[-1][0].get("reward") or 0.0)
        
        units_sold = defaultdict(int)
        for s_idx in range(1, len(steps)):
            act = steps[s_idx][0].get("action") or {}
            for o in act.get("market") or []:
                if o and isinstance(o, list) and o[0] == "SELL":
                    item = o[1]
                    qty = int(o[2]) if len(o) > 2 else 1
                    units_sold[item] += qty
                    
        return {"seed": seed, "reward": r, "units_sold": dict(units_sold), "error": None}
    except Exception as e:
        return {"seed": seed, "reward": 0.0, "units_sold": {}, "error": str(e)}

def run_bench(max_workers=10):
    print("=" * 85)
    print("100-SEED BENCHMARK: CANDIDATE CL-TEMPORAL-V3 (Seeds 1000-1099)")
    print("=" * 85)
    t0 = time.time()
    results = []
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(_run_seed, s) for s in SEEDS]
        completed = 0
        for f in as_completed(futures):
            results.append(f.result())
            completed += 1
            if completed % 25 == 0 or completed == len(SEEDS):
                print(f"Progress: {completed}/{len(SEEDS)} in {time.time()-t0:.1f}s")
                
    rewards = [r["reward"] for r in results if r["error"] is None]
    straw = np.mean([r["units_sold"].get("STRAWBERRY", 0) for r in results])
    wool = np.mean([r["units_sold"].get("WOOL", 0) for r in results])
    milk = np.mean([r["units_sold"].get("MILK", 0) for r in results])
    wheat = np.mean([r["units_sold"].get("WHEAT", 0) for r in results])
    melon = np.mean([r["units_sold"].get("MELON", 0) for r in results])
    fert = np.mean([r["units_sold"].get("FERTILIZER", 0) for r in results])
    
    mean_r = float(np.mean(rewards))
    std_r = float(np.std(rewards))
    med_r = float(np.median(rewards))
    
    print("\n" + "=" * 85)
    print(f"Mean Reward:   ${mean_r:10,.2f} +/- ${std_r:8,.2f}")
    print(f"Median Reward: ${med_r:10,.2f}")
    print(f"Min / Max:     ${np.min(rewards):10,.2f} / ${np.max(rewards):10,.2f}")
    print(f"Strawberry:    {straw:6.1f} units")
    print(f"Wool:          {wool:6.1f} units")
    print(f"Milk:          {milk:6.1f} units")
    print(f"Wheat:         {wheat:6.1f} units")
    print(f"Melon:         {melon:6.1f} units")
    print(f"Fertilizer:    {fert:6.1f} units")
    print("=" * 85)
    
    with open("scratch/cl_temporal_v3_100seed_results.json", "w") as f:
        json.dump({
            "mean_reward": mean_r,
            "std_reward": std_r,
            "median_reward": med_r,
            "straw": straw,
            "wool": wool,
            "milk": milk,
            "wheat": wheat,
            "melon": melon,
            "fert": fert
        }, f, indent=2)

if __name__ == "__main__":
    run_bench()
