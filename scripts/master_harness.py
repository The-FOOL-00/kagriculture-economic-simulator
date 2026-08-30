import os
import sys
import time
import json
import math
import hashlib
import numpy as np
from concurrent.futures import ProcessPoolExecutor, as_completed
from kaggle_environments import make
import kaggle_environments

sys.stdout.reconfigure(line_buffering=True)

def run_single_match(args):
    agent0_path, agent1_path, seed, max_steps, swapped = args
    cfg = {"episodeSteps": max_steps, "seed": seed}
    env = make("kaggriculture", configuration=cfg, debug=False)
    
    try:
        env.run([agent0_path, agent1_path])
        final_step = env.steps[-1]
        raw_r0 = float(final_step[0].reward or 0.0)
        raw_r1 = float(final_step[1].reward or 0.0)
        status0 = final_step[0].status
        status1 = final_step[1].status
        
        if swapped:
            r0, r1 = raw_r1, raw_r0
            st0, st1 = status1, status0
        else:
            r0, r1 = raw_r0, raw_r1
            st0, st1 = status0, status1

        diff = r0 - r1
        if r0 > r1:
            winner = 0
        elif r1 > r0:
            winner = 1
        else:
            winner = -1
            
        return {
            "seed": seed,
            "r0": r0,
            "r1": r1,
            "diff": diff,
            "winner": winner,
            "status0": st0,
            "status1": st1,
            "swapped": swapped,
            "error": None
        }
    except Exception as e:
        return {
            "seed": seed,
            "r0": 0.0,
            "r1": 0.0,
            "diff": 0.0,
            "winner": -1,
            "status0": "ERROR",
            "status1": "ERROR",
            "swapped": swapped,
            "error": str(e)
        }

def run_paired_tournament(agent0_path, agent1_path, seeds, max_workers=10, show_progress=False):
    """Runs paired symmetric matches (each seed played with swapped sides)."""
    tasks = []
    for s in seeds:
        tasks.append((agent0_path, agent1_path, s, 720, False)) # P0
        tasks.append((agent1_path, agent0_path, s, 720, True))  # P1 (swapped)
    
    results = []
    total_tasks = len(tasks)
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(run_single_match, t) for t in tasks]
        done = 0
        for f in as_completed(futures):
            results.append(f.result())
            done += 1
            if show_progress and (done % max(1, total_tasks // 5) == 0 or done == total_tasks):
                print(f"    ... {done}/{total_tasks} matches complete ({done/total_tasks*100:.0f}%)", flush=True)
            
    p0_matches = [r for r in results if not r["swapped"]]
    p1_matches = [r for r in results if r["swapped"]]
    
    p0_wins = sum(1 for r in p0_matches if r["winner"] == 0)
    p0_wr = p0_wins / len(p0_matches) if p0_matches else 0.0
    
    p1_wins = sum(1 for r in p1_matches if r["winner"] == 0)
    p1_wr = p1_wins / len(p1_matches) if p1_matches else 0.0
    
    total_wins = sum(1 for r in results if r["winner"] == 0)
    total_losses = sum(1 for r in results if r["winner"] == 1)
    total_ties = sum(1 for r in results if r["winner"] == -1)
    pooled_wr = total_wins / len(results) if results else 0.0
    
    diffs = [r["diff"] for r in results]
    r0s = [r["r0"] for r in results]
    r1s = [r["r1"] for r in results]
    
    mean_margin = float(np.mean(diffs))
    median_margin = float(np.median(diffs))
    std_margin = float(np.std(diffs))
    mean_cash = float(np.mean(r0s))
    median_cash = float(np.median(r0s))
    std_cash = float(np.std(r0s))
    catastrophic = sum(1 for d in diffs if d < -10000)
    
    return {
        "n_matches": len(results),
        "n_seeds": len(seeds),
        "p0_wr": p0_wr,
        "p1_wr": p1_wr,
        "pooled_wr": pooled_wr,
        "total_wins": total_wins,
        "total_losses": total_losses,
        "total_ties": total_ties,
        "mean_margin": mean_margin,
        "median_margin": median_margin,
        "std_margin": std_margin,
        "mean_cash": mean_cash,
        "median_cash": median_cash,
        "std_cash": std_cash,
        "catastrophic": catastrophic,
        "p0_cash": float(np.mean([r["r0"] for r in p0_matches])),
        "p1_cash": float(np.mean([r["r0"] for r in p1_matches])),
        "opp_p0_cash": float(np.mean([r["r1"] for r in p0_matches])),
        "opp_p1_cash": float(np.mean([r["r1"] for r in p1_matches])),
    }

if __name__ == "__main__":
    print(f"Master Experiment Suite running under kaggle-environments {kaggle_environments.__version__}")
