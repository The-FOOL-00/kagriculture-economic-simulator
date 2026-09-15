"""
scratch/run_step301_counterfactual_matrix.py
============================================
Runs paired counterfactuals R0..R10 against Canonical V66 across:
- 7 Large V66 Loss Seeds (14 matches)
- 10 Medium V66 Loss Seeds (20 matches)
- 15 Close Game Seeds (30 matches)
- 15 V54++ Win Seeds (30 matches)
Total: 47 seeds x 2 seats = 94 matches per arm x 11 arms = 1,034 matches.
Computes bootstrap CIs, tail risk probabilities, and route selection breakdown.
Outputs:
- research/step301_counterfactual_raw.json
- research/step301_counterfactual_summary.json
"""

import os
import sys
import copy
import time
import json
import numpy as np
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor
import importlib.util
from kaggle_environments import make

BASE_DIR = os.path.abspath(".")
CANDIDATE_PATHS = {
    "V66": os.path.join(BASE_DIR, "external_repos", "kaggriculture-v66-agent", "main.py"),
}

for p in [BASE_DIR, os.path.dirname(CANDIDATE_PATHS["V66"]), os.path.join(BASE_DIR, "scratch")]:
    if p not in sys.path:
        sys.path.insert(0, p)

from step301_counterfactual_arms import get_route_arm

def run_single_match(args):
    arm_id, seed, seat = args
    
    # Load V66
    spec = importlib.util.spec_from_file_location("v66_eval_r", CANDIDATE_PATHS["V66"])
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    fn_v66 = getattr(mod, "agent", getattr(mod, "kaggle_agent", None))
    
    arm_fn = get_route_arm(arm_id)
    
    p0 = arm_fn if seat == 0 else fn_v66
    p1 = fn_v66 if seat == 0 else arm_fn
    arm_idx = seat
    v66_idx = 1 - seat
    
    env = make("kaggriculture", configuration={"seed": seed, "episodeSteps": 720})
    env.reset()
    
    for s in range(719):
        o0, o1 = env.state[0].observation, env.state[1].observation
        o0["step"], o1["step"] = s, s
        a0 = p0(o0, env.configuration)
        a1 = p1(o1, env.configuration)
        env.step([a0, a1])
        
    arm_reward = float(env.state[arm_idx].reward)
    v66_reward = float(env.state[v66_idx].reward)
    
    return {
        "arm_id": arm_id,
        "seed": seed,
        "seat": seat,
        "arm_reward": arm_reward,
        "v66_reward": v66_reward,
        "margin": arm_reward - v66_reward
    }

def bootstrap_ci(deltas, n_boot=2000, alpha=0.05):
    if len(deltas) == 0:
        return 0.0, 0.0
    means = []
    arr = np.array(deltas)
    for _ in range(n_boot):
        sample = np.random.choice(arr, size=len(arr), replace=True)
        means.append(np.mean(sample))
    return float(np.percentile(means, 100 * (alpha / 2))), float(np.percentile(means, 100 * (1 - alpha / 2)))

def main():
    large_loss_seeds = [1542, 1609, 1773, 1871, 1948, 1949, 1969]
    med_loss_seeds = [1501, 1502, 1530, 1545, 1560, 1580, 1620, 1650, 1710, 1750]
    close_seeds = [1503, 1504, 1505, 1506, 1507, 1508, 1509, 1510, 1511, 1512, 1513, 1514, 1515, 1516, 1517]
    win_seeds = [1518, 1519, 1520, 1521, 1522, 1523, 1524, 1525, 1526, 1527, 1528, 1529, 1531, 1532, 1533]
    
    seed_categories = {}
    for s in large_loss_seeds: seed_categories[s] = "Large V66 Losses"
    for s in med_loss_seeds: seed_categories[s] = "Medium V66 Losses"
    for s in close_seeds: seed_categories[s] = "Close Games"
    for s in win_seeds: seed_categories[s] = "Large V54++ Wins"
    
    all_seeds = list(seed_categories.keys())
    arms = ["R0", "R1", "R2", "R3", "R4", "R5", "R6", "R7", "R8", "R9", "R10"]
    
    tasks = []
    for arm in arms:
        for seed in all_seeds:
            for seat in [0, 1]:
                tasks.append((arm, seed, seat))
                
    print(f"Total tasks to run: {len(tasks)} (47 seeds x 2 seats x 11 arms = 1,034 matches)")
    t0 = time.time()
    
    results_by_arm = defaultdict(list)
    
    with ProcessPoolExecutor(max_workers=8) as executor:
        for idx, res in enumerate(executor.map(run_single_match, tasks)):
            results_by_arm[res["arm_id"]].append(res)
            if (idx + 1) % 50 == 0 or (idx + 1) == len(tasks):
                elapsed = time.time() - t0
                print(f"Progress: [{idx+1}/{len(tasks)}] matches done in {elapsed:.1f}s ({elapsed/(idx+1):.2f}s/match)")
                
    # Save raw results
    with open("research/step301_counterfactual_raw.json", "w") as f:
        json.dump(results_by_arm, f, indent=2)
        
    # Map R0 rewards: (seed, seat) -> r0_reward
    r0_map = {}
    for r in results_by_arm["R0"]:
        r0_map[(r["seed"], r["seat"])] = r["arm_reward"]
        
    summary_report = {}
    
    for arm in arms:
        summary_report[arm] = {}
        cat_deltas = defaultdict(list)
        all_deltas = []
        
        for r in results_by_arm[arm]:
            key = (r["seed"], r["seat"])
            r0_rew = r0_map[key]
            delta = r["arm_reward"] - r0_rew
            cat = seed_categories[r["seed"]]
            cat_deltas[cat].append(delta)
            all_deltas.append(delta)
            
        cat_deltas["All Seeds"] = all_deltas
        
        for cat, deltas in cat_deltas.items():
            arr = np.array(deltas)
            ci_low, ci_high = bootstrap_ci(deltas)
            summary_report[arm][cat] = {
                "n_matches": len(deltas),
                "mean_delta": float(np.mean(arr)),
                "median_delta": float(np.median(arr)),
                "std_delta": float(np.std(arr)),
                "ci_low": ci_low,
                "ci_high": ci_high,
                "wins": int(np.sum(arr > 0)),
                "losses": int(np.sum(arr < 0)),
                "ties": int(np.sum(arr == 0)),
                "p_loss_500": float(np.mean(arr < -500.0)),
                "p_loss_1000": float(np.mean(arr < -1000.0)),
                "p_gain_2000": float(np.mean(arr > 2000.0)),
            }
            
    print("\nWriting research/step301_counterfactual_summary.json...")
    with open("research/step301_counterfactual_summary.json", "w") as f:
        json.dump(summary_report, f, indent=2)
        
    print("\nSummary Report Preview:")
    for arm in arms:
        st = summary_report[arm]["All Seeds"]
        print(f"Arm {arm:4s} (All Seeds): mean={st['mean_delta']:+8.1f}, med={st['median_delta']:+8.1f}, 95CI=[{st['ci_low']:+8.1f}, {st['ci_high']:+8.1f}], W/L/T={st['wins']:2d}/{st['losses']:2d}/{st['ties']:2d}, P(<-1k)={st['p_loss_1000']*100:4.1f}%, P(>2k)={st['p_gain_2000']*100:4.1f}%")

if __name__ == "__main__":
    main()
