"""
=============================================================================
Kaggriculture Professional Benchmarking & Experimentation Harness
=============================================================================
Provides large-scale, high-speed multi-core benchmarking across deterministic
seeds. Records wealth distribution, win/loss/tie ratios, margins, and percentiles.
=============================================================================
"""

import sys
import os
import time
import argparse
import numpy as np
from concurrent.futures import ProcessPoolExecutor, as_completed
from kaggle_environments import make


def _run_single_seed_match(item):
    agent0_path, agent1_path, seed, max_steps, swapped = item
    
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
            r0 = raw_r1
            r1 = raw_r0
        else:
            r0 = raw_r0
            r1 = raw_r1

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
            "status0": status0,
            "status1": status1,
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
            "error": str(e)
        }


def run_benchmark(agent0, agent1, num_matches=20, start_seed=1000, max_workers=None, swap_sides=False):
    print("=" * 75)
    print(f"KAGGRICULTURE BENCHMARK: {agent0} vs {agent1}")
    print(f"Total Matches: {num_matches} | Start Seed: {start_seed} | Swap Sides: {swap_sides}")
    print("=" * 75)

    tasks = []
    for i in range(num_matches):
        seed = start_seed + i
        if swap_sides and (i % 2 == 1):
            tasks.append((agent1, agent0, seed, 720, True))
        else:
            tasks.append((agent0, agent1, seed, 720, False))

    results = []
    t_start = time.time()

    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(_run_single_seed_match, t) for t in tasks]
        completed = 0
        for f in as_completed(futures):
            res = f.result()
            results.append(res)
            completed += 1
            if completed % max(1, num_matches // 10) == 0 or completed == num_matches:
                print(f"Progress: {completed}/{num_matches} matches ({completed/num_matches*100:.1f}%) in {time.time()-t_start:.1f}s")

    elapsed = time.time() - t_start
    
    # Aggregate statistics
    r0_scores = np.array([r["r0"] for r in results])
    r1_scores = np.array([r["r1"] for r in results])
    diffs = np.array([r["diff"] for r in results])
    
    wins = sum(1 for r in results if r["winner"] == 0)
    losses = sum(1 for r in results if r["winner"] == 1)
    ties = sum(1 for r in results if r["winner"] == -1)
    
    win_rate = wins / num_matches * 100.0
    loss_rate = losses / num_matches * 100.0
    tie_rate = ties / num_matches * 100.0

    print("\n" + "=" * 75)
    print(f"MATCHUP RESULT: {agent0} vs {agent1}")
    print("=" * 75)
    print(f"Matches Played: {num_matches} in {elapsed:.2f}s ({elapsed/num_matches:.2f}s/match)")
    print(f"Wins:   {wins:4d} ({win_rate:5.1f}%)")
    print(f"Losses: {losses:4d} ({loss_rate:5.1f}%)")
    print(f"Ties:   {ties:4d} ({tie_rate:5.1f}%)")
    print("-" * 75)
    print(f"{agent0} (P0):")
    print(f"  Mean Final Cash:   ${np.mean(r0_scores):10.2f} (±${np.std(r0_scores):8.2f})")
    print(f"  Median Final Cash: ${np.median(r0_scores):10.2f}")
    print(f"  Min / Max Cash:    ${np.min(r0_scores):10.2f} / ${np.max(r0_scores):10.2f}")
    print(f"  5th / 95th Pct:    ${np.percentile(r0_scores, 5):10.2f} / ${np.percentile(r0_scores, 95):10.2f}")
    print("-" * 75)
    print(f"{agent1} (P1):")
    print(f"  Mean Final Cash:   ${np.mean(r1_scores):10.2f} (±${np.std(r1_scores):8.2f})")
    print(f"  Median Final Cash: ${np.median(r1_scores):10.2f}")
    print("-" * 75)
    print(f"Head-to-Head Margin:")
    print(f"  Mean Advantage:    ${np.mean(diffs):+10.2f} (±${np.std(diffs):8.2f})")
    print(f"  Median Advantage:  ${np.median(diffs):+10.2f}")
    print("=" * 75 + "\n")

    return {
        "agent0": agent0,
        "agent1": agent1,
        "matches": num_matches,
        "wins": wins,
        "losses": losses,
        "ties": ties,
        "win_rate": win_rate,
        "mean_r0": float(np.mean(r0_scores)),
        "median_r0": float(np.median(r0_scores)),
        "std_r0": float(np.std(r0_scores)),
        "mean_r1": float(np.mean(r1_scores)),
        "mean_diff": float(np.mean(diffs)),
        "results": results
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Kaggriculture Benchmarking Harness")
    parser.add_argument("--agent0", type=str, default="agents/golden_v1.py", help="Path to Agent 0")
    parser.add_argument("--agent1", type=str, default="starter", help="Path to Agent 1 or 'starter'")
    parser.add_argument("--matches", type=int, default=10, help="Number of benchmark matches")
    parser.add_argument("--seed", type=int, default=1000, help="Start seed")
    parser.add_argument("--swap", action="store_true", help="Swap player sides every match")
    parser.add_argument("--workers", type=int, default=None, help="Max parallel workers")
    
    args = parser.parse_args()
    run_benchmark(
        agent0=args.agent0,
        agent1=args.agent1,
        num_matches=args.matches,
        start_seed=args.seed,
        max_workers=args.workers,
        swap_sides=args.swap
    )
