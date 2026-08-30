"""
=============================================================================
TOURNAMENT ENGINE: 12-OPPONENT MULTI-CORE COMPETITIVE BENCHMARK
=============================================================================
Executes large-scale paired matches with symmetric side-swapping, computing:
- Win Probability P(win)
- 95% Wilson Score Confidence Intervals
- Terminal Cash Distribution (Mean, Std, Median, Min, Max, 5th/95th Pct)
- Head-to-Head Net Margin (mu +/- sigma)
- Worst-Case Drawdown & Catastrophic Losses (< -$10k)
- Per-Turn Runtime Profiling (Mean, p95, Max)
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

def wilson_score_interval(wins, total, confidence=0.95):
    if total == 0:
        return 0.0, 0.0
    z = 1.95996  # 95% confidence
    p = wins / total
    denom = 1.0 + (z**2) / total
    center = (p + (z**2) / (2 * total)) / denom
    spread = (z / denom) * math.sqrt((p * (1.0 - p) / total) + ((z**2) / (4 * (total**2))))
    lower = max(0.0, center - spread) * 100.0
    upper = min(1.0, center + spread) * 100.0
    return lower, upper

def _run_single_match(item):
    agent0, agent1, seed, max_steps, swapped = item
    cfg = {"episodeSteps": max_steps, "seed": seed}
    env = make("kaggriculture", configuration=cfg, debug=False)
    
    t0 = time.time()
    try:
        env.run([agent0, agent1])
        elapsed = time.time() - t0
        final_step = env.steps[-1]
        raw_r0 = float(final_step[0].reward or 0.0)
        raw_r1 = float(final_step[1].reward or 0.0)
        status0 = final_step[0].status
        status1 = final_step[1].status

        per_turn_ms = (elapsed / max(1, max_steps)) * 1000.0

        if swapped:
            r_us = raw_r1
            r_opp = raw_r0
            status_us = status1
            status_opp = status0
        else:
            r_us = raw_r0
            r_opp = raw_r1
            status_us = status0
            status_opp = status1

        margin = r_us - r_opp
        win = 1.0 if r_us > r_opp else (0.0 if r_opp > r_us else 0.5)

        return {
            "seed": seed,
            "swapped": swapped,
            "r_us": r_us,
            "r_opp": r_opp,
            "margin": margin,
            "win": win,
            "status_us": status_us,
            "status_opp": status_opp,
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
            "win": 0.0,
            "status_us": "ERROR",
            "status_opp": "ERROR",
            "elapsed": 0.0,
            "per_turn_ms": 0.0,
            "error": str(e)
        }

def run_paired_tournament(agent_us, agent_opp, seeds=None, num_pairs=10, start_seed=10000, max_workers=6):
    """
    Runs symmetric paired matches across specified seeds with side swapping.
    """
    if seeds is None:
        seed_list = [start_seed + i for i in range(num_pairs)]
    else:
        seed_list = list(seeds)[:num_pairs]

    tasks = []
    for s in seed_list:
        # P0 match
        tasks.append((agent_us, agent_opp, s, 720, False))
        # P1 match (swapped)
        tasks.append((agent_opp, agent_us, s, 720, True))

    results = []
    t_start = time.time()
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(_run_single_match, t) for t in tasks]
        for f in as_completed(futures):
            results.append(f.result())

    total_games = len(results)
    wins = sum(1 for r in results if r["win"] == 1.0)
    losses = sum(1 for r in results if r["win"] == 0.0)
    ties = sum(1 for r in results if r["win"] == 0.5)

    win_rate = (wins / total_games) * 100.0 if total_games > 0 else 0.0
    w_low, w_high = wilson_score_interval(wins, total_games)

    scores_us = np.array([r["r_us"] for r in results])
    scores_opp = np.array([r["r_opp"] for r in results])
    margins = np.array([r["margin"] for r in results])
    turn_times = np.array([r["per_turn_ms"] for r in results])

    mean_us = float(np.mean(scores_us))
    std_us = float(np.std(scores_us))
    median_us = float(np.median(scores_us))
    min_us = float(np.min(scores_us))
    max_us = float(np.max(scores_us))
    p5_us = float(np.percentile(scores_us, 5))
    p95_us = float(np.percentile(scores_us, 95))

    mean_opp = float(np.mean(scores_opp))
    std_opp = float(np.std(scores_opp))
    median_opp = float(np.median(scores_opp))

    mean_margin = float(np.mean(margins))
    std_margin = float(np.std(margins))
    worst_drawdown = float(np.min(margins))
    catastrophic_losses = sum(1 for r in results if r["margin"] < -10000)

    p95_turn_ms = float(np.percentile(turn_times, 95))
    max_turn_ms = float(np.max(turn_times))

    return {
        "games": total_games,
        "wins": wins,
        "losses": losses,
        "ties": ties,
        "win_rate": win_rate,
        "ci_95": (w_low, w_high),
        "mean_us": mean_us,
        "std_us": std_us,
        "median_us": median_us,
        "min_us": min_us,
        "max_us": max_us,
        "p5_us": p5_us,
        "p95_us": p95_us,
        "mean_opp": mean_opp,
        "std_opp": std_opp,
        "median_opp": median_opp,
        "margin": mean_margin,
        "std_margin": std_margin,
        "worst_drawdown": worst_drawdown,
        "catastrophic_losses": catastrophic_losses,
        "mean_turn_ms": float(np.mean(turn_times)),
        "p95_turn_ms": p95_turn_ms,
        "max_turn_ms": max_turn_ms,
        "total_time_sec": time.time() - t_start,
        "results": results
    }

def run_ecosystem_tournament(candidate_agent, seeds, opponent_names=None, num_pairs_per_opp=10, max_workers=6):
    """
    Runs candidate against the 12-opponent ecosystem across seed sets.
    """
    import importlib.util
    path = os.path.join(project_root, "agents", "opponent_ecosystem.py")
    spec = importlib.util.spec_from_file_location("opp_eco_mod", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    OPPONENT_ECOSYSTEM = mod.OPPONENT_ECOSYSTEM

    if opponent_names is None:
        target_opps = list(OPPONENT_ECOSYSTEM.keys())
    else:
        target_opps = [o for o in opponent_names if o in OPPONENT_ECOSYSTEM]

    scoreboard = {}
    total_wins = 0
    total_games = 0

    print("=" * 90)
    print(f"RUNNING ECOSYSTEM TOURNAMENT FOR CANDIDATE: {candidate_agent}")
    print(f"Opponents: {len(target_opps)} | Pairs per Opp: {num_pairs_per_opp} ({num_pairs_per_opp*2} games each)")
    print("=" * 90)

    for opp_name in target_opps:
        opp_agent = OPPONENT_ECOSYSTEM[opp_name]
        res = run_paired_tournament(
            candidate_agent,
            opp_agent,
            seeds=seeds,
            num_pairs=num_pairs_per_opp,
            max_workers=max_workers
        )
        scoreboard[opp_name] = res
        total_wins += res["wins"]
        total_games += res["games"]

        print(f"  vs {opp_name:26s} | WR: {res['win_rate']:5.1f}% ({res['wins']:2d}W-{res['losses']:2d}L) | CI: [{res['ci_95'][0]:4.1f}%, {res['ci_95'][1]:4.1f}%] | Margin: {res['margin']:+8,.0f} | Cand: ${res['mean_us']:7,.0f} vs Opp: ${res['mean_opp']:7,.0f}")

    overall_wr = (total_wins / total_games) * 100.0 if total_games > 0 else 0.0
    w_low, w_high = wilson_score_interval(total_wins, total_games)

    print("=" * 90)
    print(f"OVERALL ECOSYSTEM SCORE: {overall_wr:.1f}% ({total_wins}/{total_games}) | 95% CI: [{w_low:.1f}%, {w_high:.1f}%]")
    print("=" * 90)

    return {
        "overall_win_rate": overall_wr,
        "ci_95": (w_low, w_high),
        "total_wins": total_wins,
        "total_games": total_games,
        "scoreboard": scoreboard
    }

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--us", type=str, default="candidates/slot5_hybrid_8c4s.py")
    parser.add_argument("--opp", type=str, default="agents/golden_v1.py")
    parser.add_argument("--pairs", type=int, default=10)
    parser.add_argument("--seed", type=int, default=10000)
    parser.add_argument("--workers", type=int, default=6)
    args = parser.parse_args()

    print(f"Running tournament: {args.us} vs {args.opp} ({args.pairs * 2} matches)")
    res = run_paired_tournament(args.us, args.opp, num_pairs=args.pairs, start_seed=args.seed, max_workers=args.workers)
    print(f"Result: {res['win_rate']:.1f}% ({res['wins']}W-{res['losses']}L-{res['ties']}T) | Cand Cash: ${res['mean_us']:,.2f} | Margin: {res['margin']:+,.2f}")
