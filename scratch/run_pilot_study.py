"""
Full 40-Match Pilot Study (Seeds 1040–1049) across 4 Arms
=========================================================
Arm A: Baseline CL-Economic-V1 Dispatcher
Arm B: Low Lambda (lambda = 3.0)
Arm C: Med Lambda (lambda = 8.0)
Arm D: High Lambda (lambda = 15.0)
"""
import sys
import os
import copy
import json
import time
from collections import defaultdict
import numpy as np
from concurrent.futures import ProcessPoolExecutor, as_completed

PROJECT_ROOT = os.path.abspath(".")
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from scratch.dispatch_harness import run_pilot_match

def run_pilot():
    seeds = list(range(1040, 1050))
    arms = [
        ("BASELINE", 0.0),
        ("LOW_LAMBDA", 3.0),
        ("MED_LAMBDA", 8.0),
        ("HIGH_LAMBDA", 15.0),
    ]

    tasks = []
    for arm_name, lam in arms:
        for s in seeds:
            tasks.append((arm_name, lam, s))

    print(f"Running 40-match pilot across Seeds {seeds[0]}–{seeds[-1]}...")
    t0 = time.time()
    results_by_arm = defaultdict(list)
    with ProcessPoolExecutor(max_workers=10) as ex:
        futs = [ex.submit(run_pilot_match, t) for t in tasks]
        for f in as_completed(futs):
            res = f.result()
            results_by_arm[res["arm"]].append(res)

    print(f"Pilot execution finished in {time.time()-t0:.1f}s.")

    # Save raw results
    with open("scratch/pilot_40seeds_results.json", "w") as f:
        # Convert to serializable format
        save_dict = {arm: [r for r in res_list] for arm, res_list in results_by_arm.items()}
        json.dump(save_dict, f, indent=2)

    # Compile Summary Table
    print("\n" + "=" * 105)
    print(f"{'ARM':<15} | {'Reward ($)':<16} | {'Moves':<8} | {'Prod':<8} | {'Idle':<8} | {'Straw':<7} | {'Wool':<7} | {'Milk':<7} | {'Water%':<7} | {'Care%':<7}")
    print("-" * 105)

    summary = {}
    for arm_name, _ in arms:
        res_list = results_by_arm[arm_name]
        # Sort by seed
        res_list.sort(key=lambda x: x["seed"])
        rewards = [r["reward"] for r in res_list]
        moves = [r["movement_turns"] for r in res_list]
        prods = [r["productive_turns"] for r in res_list]
        idles = [r["idle_turns"] for r in res_list]
        straws = [r["strawberry_harvested"] for r in res_list]
        wools = [r["wool_harvested"] for r in res_list]
        wheats = [r["wheat_harvested"] for r in res_list]
        milks = [r["milk_harvested"] for r in res_list]
        waters = [r["watering_completion"] * 100 for r in res_list]
        cares = [r["animal_care_completion"] * 100 for r in res_list]
        feed = [r["feed_bought"] for r in res_list]
        cash = [r["terminal_cash"] for r in res_list]

        # Efficiency ratios
        mean_reward = float(np.mean(rewards))
        mean_moves = float(np.mean(moves))
        mean_prods = float(np.mean(prods))
        mean_straw = float(np.mean(straws))
        mean_wool = float(np.mean(wools))

        rew_per_prod = mean_reward / max(1.0, mean_prods)
        prod_per_move = mean_prods / max(1.0, mean_moves)
        straw_per_100_moves = (mean_straw / max(1.0, mean_moves)) * 100.0
        wool_per_100_moves = (mean_wool / max(1.0, mean_moves)) * 100.0

        summary[arm_name] = {
            "mean_reward": mean_reward,
            "std_reward": float(np.std(rewards)),
            "median_reward": float(np.median(rewards)),
            "mean_moves": mean_moves,
            "mean_prods": mean_prods,
            "mean_idles": float(np.mean(idles)),
            "mean_straw": mean_straw,
            "mean_wool": mean_wool,
            "mean_wheat": float(np.mean(wheats)),
            "mean_milk": float(np.mean(milks)),
            "mean_water_pct": float(np.mean(waters)),
            "mean_care_pct": float(np.mean(cares)),
            "mean_feed": float(np.mean(feed)),
            "mean_cash": float(np.mean(cash)),
            "rew_per_prod": rew_per_prod,
            "prod_per_move": prod_per_move,
            "straw_per_100_moves": straw_per_100_moves,
            "wool_per_100_moves": wool_per_100_moves
        }

        print(f"{arm_name:<15} | ${mean_reward:10.2f} ± ${np.std(rewards):5.0f} | {mean_moves:8.1f} | {mean_prods:8.1f} | {float(np.mean(idles)):8.1f} | {mean_straw:7.1f} | {mean_wool:7.1f} | {float(np.mean(milks)):7.1f} | {float(np.mean(waters)):6.1f}% | {float(np.mean(cares)):6.1f}%")

    print("\n--- EFFICIENCY RATIOS ---")
    print(f"{'ARM':<15} | {'Reward / Prod Turn':<20} | {'Prod / Move':<12} | {'Straw / 100 Moves':<18} | {'Wool / 100 Moves':<18}")
    print("-" * 90)
    for arm_name, _ in arms:
        s = summary[arm_name]
        print(f"{arm_name:<15} | ${s['rew_per_prod']:18.2f} | {s['prod_per_move']:12.3f} | {s['straw_per_100_moves']:18.2f} | {s['wool_per_100_moves']:18.2f}")

    with open("scratch/pilot_summary.json", "w") as f:
        json.dump(summary, f, indent=2)

if __name__ == "__main__":
    run_pilot()
