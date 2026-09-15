"""
Evaluates Arm E (CL-Dynamic-Land-V2) across 100 matched seeds (1000-1099)
and compares with Arm A (CL-Economic-V1) and Benchmark (Frozen V2).
"""

import sys
import time
import json
import numpy as np
from collections import Counter
from kaggle_environments import make
from concurrent.futures import ProcessPoolExecutor, as_completed

def run_match(args):
    agent_path, seed = args
    cfg = {"episodeSteps": 720, "seed": seed}
    env = make("kaggriculture", configuration=cfg, debug=False)
    env.run([agent_path, "starter"])
    
    r = float(env.steps[-1][0].get("reward", 0.0) or 0.0)
    sales = Counter()
    for s in env.steps:
        act = s[0].get("action", {}) or {}
        for o in act.get("market", []):
            if o[0] == "SELL":
                sales[o[1]] += int(o[2])
    return seed, r, dict(sales)

if __name__ == "__main__":
    seeds = list(range(1000, 1100))
    print(f"Running Arm E on {len(seeds)} Seeds ({seeds[0]}–{seeds[-1]})...")
    
    tasks = [("candidates/candidate_cl_dynamic_land_v2.py", s) for s in seeds]
    results = {}
    t0 = time.time()
    
    with ProcessPoolExecutor(max_workers=8) as ex:
        futs = [ex.submit(run_match, t) for t in tasks]
        for f in as_completed(futs):
            s, r, sales = f.result()
            results[s] = (r, sales)
            
    rewards = [results[s][0] for s in seeds]
    mean_r = float(np.mean(rewards))
    std_r = float(np.std(rewards))
    ci95 = 1.96 * std_r / np.sqrt(len(seeds))
    med_r = float(np.median(rewards))
    
    straws = [results[s][1].get("STRAWBERRY", 0) for s in seeds]
    melons = [results[s][1].get("MELON", 0) for s in seeds]
    wools = [results[s][1].get("WOOL", 0) for s in seeds]
    milks = [results[s][1].get("MILK", 0) for s in seeds]
    ferts = [results[s][1].get("FERTILIZER", 0) for s in seeds]
    wheats = [results[s][1].get("WHEAT", 0) for s in seeds]
    
    print("\n" + "=" * 65)
    print("ARM E: CL-Dynamic-Land-V2 (100 Seeds 1000–1099)")
    print("=" * 65)
    print(f"Mean Reward:   ${mean_r:10.2f} ± ${ci95:7.2f}")
    print(f"Median Reward: ${med_r:10.2f}")
    print(f"Min / Max:     ${np.min(rewards):10.2f} / ${np.max(rewards):10.2f}")
    print(f"Mean Straw:    {np.mean(straws):6.1f} units")
    print(f"Mean Wool:     {np.mean(wools):6.1f} units")
    print(f"Mean Melon:    {np.mean(melons):6.1f} units")
    print(f"Mean Milk:     {np.mean(milks):6.1f} units")
    print(f"Mean Fert:     {np.mean(ferts):6.1f} units")
    print(f"Mean Wheat:    {np.mean(wheats):6.1f} units")
    print(f"Elapsed Time:  {time.time()-t0:.1f}s")
    print("=" * 65)
    
    # Save to json
    summary = {
        "name": "Arm E: CL-Dynamic-Land-V2",
        "mean_reward": mean_r,
        "std_reward": std_r,
        "ci95": ci95,
        "median_reward": med_r,
        "mean_straw": float(np.mean(straws)),
        "mean_wool": float(np.mean(wools)),
        "mean_melon": float(np.mean(melons)),
        "mean_milk": float(np.mean(milks)),
        "mean_fert": float(np.mean(ferts)),
        "mean_wheat": float(np.mean(wheats))
    }
    with open("scratch/arm_e_100seed_results.json", "w") as f:
        json.dump(summary, f, indent=2)
