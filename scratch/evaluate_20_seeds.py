import sys
import time
import numpy as np
from collections import Counter
from kaggle_environments import make
from concurrent.futures import ProcessPoolExecutor, as_completed

def run_match(args):
    agent0, seed = args
    cfg = {"episodeSteps": 720, "seed": seed}
    env = make("kaggriculture", configuration=cfg, debug=False)
    env.run([agent0, "starter"])
    r = float(env.steps[-1][0].reward or 0.0)
    
    # Track sales
    sales = Counter()
    for s in env.steps:
        act = s[0].get("action", {}) or {}
        for o in act.get("market", []):
            if o[0] == "SELL":
                sales[o[1]] += int(o[2])
    return seed, r, dict(sales)

if __name__ == "__main__":
    seeds = list(range(1000, 1020)) # 20 seeds
    print(f"Running 20-seed comparison across Seeds {seeds[0]}–{seeds[-1]}...")
    
    for agent_name, agent_path in [
        ("CL-Economic-V1", "candidates/candidate_cl_economic_v1.py"),
        ("CL-Economic-V3", "candidates/candidate_cl_economic_v3.py"),
        ("Frozen V2", "candidates/slot2_aethel_refined_v2.py")
    ]:
        t0 = time.time()
        tasks = [(agent_path, s) for s in seeds]
        results = {}
        with ProcessPoolExecutor(max_workers=8) as ex:
            futs = [ex.submit(run_match, t) for t in tasks]
            for f in as_completed(futs):
                s, r, sales = f.result()
                results[s] = (r, sales)
                
        rewards = [results[s][0] for s in seeds]
        straws = [results[s][1].get("STRAWBERRY", 0) for s in seeds]
        melons = [results[s][1].get("MELON", 0) for s in seeds]
        wools = [results[s][1].get("WOOL", 0) for s in seeds]
        milks = [results[s][1].get("MILK", 0) for s in seeds]
        ferts = [results[s][1].get("FERTILIZER", 0) for s in seeds]
        wheats = [results[s][1].get("WHEAT", 0) for s in seeds]
        
        print(f"{agent_name:15s} ({time.time()-t0:.1f}s):")
        print(f"  Mean Reward:   ${np.mean(rewards):10.2f} ± ${np.std(rewards):8.2f}")
        print(f"  Median Reward: ${np.median(rewards):10.2f}")
        print(f"  Min / Max:     ${np.min(rewards):10.2f} / ${np.max(rewards):10.2f}")
        print(f"  Mean Straw:    {np.mean(straws):6.1f} units")
        print(f"  Mean Melon:    {np.mean(melons):6.1f} units")
        print(f"  Mean Wool:     {np.mean(wools):6.1f} units")
        print(f"  Mean Milk:     {np.mean(milks):6.1f} units")
        print(f"  Mean Fert:     {np.mean(ferts):6.1f} units")
        print(f"  Mean Wheat:    {np.mean(wheats):6.1f} units")
        print("-" * 65)
