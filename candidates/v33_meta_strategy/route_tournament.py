# SPDX-License-Identifier: MIT
"""V33 Route Tournament Runner.

Executes a full round-robin tournament across all 6 elite candidate routes over
the DEV seed cohort (seeds 249675..249679) across both seats (Seat 0 & Seat 1),
producing the comprehensive matchup matrix and non-transitivity audit.
"""

from __future__ import annotations
import copy
import json
import multiprocessing as mp
import os
import sys
import time
from typing import Any, Dict, List, Tuple
import numpy as np

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from kaggle_environments import make
from candidates.v33_meta_strategy.route_bank import RouteBank

DEV_SEEDS = [249675, 249676, 249677, 249678, 249679]
ROUTES = ["R0_A7", "R1_V22R1", "R2_DMITRII", "R3_P3090", "R4_V54", "R5_V25P3"]


def _run_single_match(args: Tuple[str, str, int]) -> Dict[str, Any]:
    """Runs a single 2-player match in an isolated process."""
    r_left, r_right, seed = args
    bank = RouteBank()
    agent_left = bank.load_route(r_left)
    agent_right = bank.load_route(r_right)

    env = make("kaggriculture", configuration={"seed": seed, "episodeSteps": 720})
    t0 = time.time()
    env.run([agent_left, agent_right])
    dt = time.time() - t0

    step_final = env.steps[-1]
    p0_reward = float(step_final[0]["reward"] or 0.0)
    p1_reward = float(step_final[1]["reward"] or 0.0)
    delta = p0_reward - p1_reward

    if p0_reward > p1_reward:
        winner = "LEFT"
    elif p1_reward > p0_reward:
        winner = "RIGHT"
    else:
        winner = "TIE"

    return {
        "r_left": r_left,
        "r_right": r_right,
        "seed": seed,
        "p0_cash": p0_reward,
        "p1_cash": p1_reward,
        "delta": delta,
        "winner": winner,
        "duration_sec": dt
    }


def run_tournament(n_workers: int = 8) -> Dict[str, Any]:
    tasks = []
    # All ordered pairs across DEV seeds (gives both seats)
    for r_i in ROUTES:
        for r_j in ROUTES:
            if r_i == r_j:
                continue
            for s in DEV_SEEDS:
                tasks.append((r_i, r_j, s))

    print(f"Starting V33 Route Tournament: {len(tasks)} matches across {n_workers} CPU workers...")
    t_start = time.time()

    with mp.Pool(processes=n_workers) as pool:
        raw_results = pool.map(_run_single_match, tasks)

    total_time = time.time() - t_start
    print(f"Tournament completed in {total_time:.1f}s ({len(raw_results)} matches)!")

    # Aggregate pairwise statistics
    matrix: Dict[str, Dict[str, Any]] = {r1: {r2: {} for r2 in ROUTES} for r1 in ROUTES}

    for r1 in ROUTES:
        for r2 in ROUTES:
            if r1 == r2:
                matrix[r1][r2] = {
                    "matches": 0,
                    "wins": 0,
                    "losses": 0,
                    "ties": 0,
                    "win_rate": 0.5,
                    "mean_cash": 0.0,
                    "opp_mean_cash": 0.0,
                    "mean_delta": 0.0,
                    "worst_delta": 0.0,
                    "seat0_wins": 0,
                    "seat1_wins": 0
                }
                continue

            # r1 as left (seat 0) vs r2 as right (seat 1)
            legs_seat0 = [m for m in raw_results if m["r_left"] == r1 and m["r_right"] == r2]
            # r1 as right (seat 1) vs r2 as left (seat 0)
            legs_seat1 = [m for m in raw_results if m["r_left"] == r2 and m["r_right"] == r1]

            all_legs = legs_seat0 + legs_seat1
            n_matches = len(all_legs)
            if n_matches == 0:
                continue

            r1_cash_list = [m["p0_cash"] for m in legs_seat0] + [m["p1_cash"] for m in legs_seat1]
            r2_cash_list = [m["p1_cash"] for m in legs_seat0] + [m["p0_cash"] for m in legs_seat1]
            deltas = [m["delta"] for m in legs_seat0] + [-m["delta"] for m in legs_seat1]

            s0_wins = sum(1 for m in legs_seat0 if m["winner"] == "LEFT")
            s1_wins = sum(1 for m in legs_seat1 if m["winner"] == "RIGHT")
            wins = s0_wins + s1_wins
            losses = sum(1 for m in legs_seat0 if m["winner"] == "RIGHT") + sum(1 for m in legs_seat1 if m["winner"] == "LEFT")
            ties = n_matches - (wins + losses)

            matrix[r1][r2] = {
                "matches": n_matches,
                "wins": wins,
                "losses": losses,
                "ties": ties,
                "win_rate": float(wins / n_matches),
                "mean_cash": float(np.mean(r1_cash_list)),
                "opp_mean_cash": float(np.mean(r2_cash_list)),
                "median_cash": float(np.median(r1_cash_list)),
                "mean_delta": float(np.mean(deltas)),
                "median_delta": float(np.median(deltas)),
                "worst_delta": float(np.min(deltas)),
                "best_delta": float(np.max(deltas)),
                "seat0_wins": s0_wins,
                "seat1_wins": s1_wins,
                "seat0_matches": len(legs_seat0),
                "seat1_matches": len(legs_seat1)
            }

    tournament_data = {
        "routes": ROUTES,
        "dev_seeds": DEV_SEEDS,
        "n_matches": len(raw_results),
        "duration_sec": total_time,
        "matrix": matrix,
        "raw_matches": raw_results
    }

    with open("route_matchup_matrix.json", "w", encoding="utf-8") as f:
        json.dump(tournament_data, f, indent=2)
    print("Saved route_matchup_matrix.json!")

    return tournament_data


if __name__ == "__main__":
    run_tournament()
