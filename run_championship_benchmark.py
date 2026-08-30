"""
=============================================================================
CHAMPIONSHIP BENCHMARK & MULTI-CORE EXPERIMENTAL TOURNAMENT HARNESS
=============================================================================
Parallelized evaluation engine executing paired matches with side swapping,
95% Wilson score confidence intervals, margin calculations, and per-turn profiling.
=============================================================================
"""

import sys
import os
import time
import math
import argparse
import numpy as np
from concurrent.futures import ProcessPoolExecutor, as_completed
from kaggle_environments import make

project_root = r"c:\Users\Sundareswaran\Kagriculture"
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def wilson_score_interval(k, n, confidence=0.95):
    if n == 0:
        return 0.0, 0.0
    z = 1.95996  # 95% confidence
    p = k / n
    denom = 1.0 + (z**2) / n
    center = (p + (z**2) / (2 * n)) / denom
    spread = (z / denom) * math.sqrt((p * (1.0 - p) / n) + ((z**2) / (4 * (n**2))))
    lower = max(0.0, center - spread) * 100.0
    upper = min(1.0, center + spread) * 100.0
    return lower, upper

def _run_single_match(item):
    a0_path, a1_path, seed, max_steps, swapped = item
    cfg = {"episodeSteps": max_steps, "seed": seed}
    env = make("kaggriculture", configuration=cfg, debug=False)
    
    t0 = time.time()
    try:
        env.run([a0_path, a1_path])
        elapsed = time.time() - t0
        final_step = env.steps[-1]
        raw_r0 = float(final_step[0].reward or 0.0)
        raw_r1 = float(final_step[1].reward or 0.0)
        
        # Calculate per turn time estimate
        per_turn_ms = (elapsed / max_steps) * 1000.0

        if swapped:
            r_us = raw_r1
            r_opp = raw_r0
        else:
            r_us = raw_r0
            r_opp = raw_r1

        margin = r_us - r_opp
        win = 1 if r_us > r_opp else (0 if r_opp > r_us else 0.5)

        return {
            "seed": seed,
            "swapped": swapped,
            "r_us": r_us,
            "r_opp": r_opp,
            "margin": margin,
            "win": win,
            "elapsed": elapsed,
            "per_turn_ms": per_turn_ms,
            "error": None
        }
    except Exception as e:
        return {
            "seed": seed,
            "swapped": swapped,
            "r_us": 0.0,
            "r_opp": 0.0,
            "margin": 0.0,
            "win": 0,
            "elapsed": 0.0,
            "per_turn_ms": 0.0,
            "error": str(e)
        }

def run_tournament(agent_us, agent_opp, num_pairs=10, start_seed=10001, max_workers=6):
    """
    Runs `num_pairs` paired matches (total 2 * num_pairs matches with side-swapping).
    """
    tasks = []
    for i in range(num_pairs):
        seed = start_seed + i
        # Match 1: Us as P0
        tasks.append((agent_us, agent_opp, seed, 720, False))
        # Match 2: Us as P1 (swapped)
        tasks.append((agent_opp, agent_us, seed, 720, True))

    results = []
    t_start = time.time()
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(_run_single_match, t) for t in tasks]
        for f in as_completed(futures):
            results.append(f.result())

    total_games = len(results)
    wins = sum(1 for r in results if r["win"] == 1)
    losses = sum(1 for r in results if r["win"] == 0)
    ties = sum(1 for r in results if r["win"] == 0.5)

    win_rate = (wins / total_games) * 100.0 if total_games > 0 else 0.0
    w_low, w_high = wilson_score_interval(wins, total_games)

    scores_us = [r["r_us"] for r in results]
    scores_opp = [r["r_opp"] for r in results]
    margins = [r["margin"] for r in results]
    turn_times = [r["per_turn_ms"] for r in results]

    mean_us = float(np.mean(scores_us))
    median_us = float(np.median(scores_us))
    mean_opp = float(np.mean(scores_opp))
    mean_margin = float(np.mean(margins))
    catastrophic_losses = sum(1 for r in results if r["margin"] < -10000)

    p95_time = float(np.percentile(turn_times, 95))
    max_time = float(np.max(turn_times))

    return {
        "games": total_games,
        "wins": wins,
        "losses": losses,
        "ties": ties,
        "win_rate": win_rate,
        "ci_95": (w_low, w_high),
        "mean_us": mean_us,
        "median_us": median_us,
        "mean_opp": mean_opp,
        "margin": mean_margin,
        "catastrophic_losses": catastrophic_losses,
        "mean_turn_ms": float(np.mean(turn_times)),
        "p95_turn_ms": p95_time,
        "max_turn_ms": max_time,
        "total_time_sec": time.time() - t_start
    }

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--us", type=str, default="main.py")
    parser.add_argument("--opp", type=str, default="agents/golden_v1.py")
    parser.add_argument("--pairs", type=int, default=5)
    parser.add_argument("--seed", type=int, default=10001)
    parser.add_argument("--workers", type=int, default=6)
    args = parser.parse_args()

    print(f"Executing Tournament: {args.us} vs {args.opp} ({args.pairs*2} matches)")
    res = run_tournament(args.us, args.opp, num_pairs=args.pairs, start_seed=args.seed, max_workers=args.workers)
    
    print("\n" + "=" * 80)
    print("TOURNAMENT RESULTS")
    print("=" * 80)
    print(f"Total Matches:    {res['games']} (Paired with side swaps)")
    print(f"Record (W/L/T):   {res['wins']}W - {res['losses']}L - {res['ties']}T")
    print(f"Win Rate:         {res['win_rate']:.1f}% (95% Wilson CI: [{res['ci_95'][0]:.1f}%, {res['ci_95'][1]:.1f}%])")
    print(f"Mean Final Cash:  ${res['mean_us']:,.2f} vs Opp: ${res['mean_opp']:,.2f}")
    print(f"Net Margin:       {res['margin']:+,.2f}")
    print(f"Median Cash:      ${res['median_us']:,.2f}")
    print(f"Catastrophic Losses (< -$10k): {res['catastrophic_losses']}")
    print(f"Per-Turn Runtime: Mean={res['mean_turn_ms']:.2f}ms | p95={res['p95_turn_ms']:.2f}ms | Max={res['max_turn_ms']:.2f}ms")
    print(f"Total Execution Time: {res['total_time_sec']:.2f}s")
    print("=" * 80)
