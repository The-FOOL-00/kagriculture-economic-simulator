# SPDX-License-Identifier: MIT
"""V33 Market Overlay Benchmark.

Compares pure A7 against A7 + Market Overlay across DEV seeds against the 6 league opponents.
Measures win rate, mean cash, paired delta, and reordered turn frequency.
"""

from __future__ import annotations
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
from candidates.v32_rlx2.opponents import load_league_opponent, LEAGUE_OPPONENTS
from candidates.v33_meta_strategy.market_overlay import wrap_market_overlay

DEV_SEEDS = [249675, 249676, 249677, 249678, 249679]


def _eval_match_pair(args: Tuple[str, int, int]) -> Dict[str, Any]:
    opp_id, seed, seat = args
    opp_agent_1 = load_league_opponent(opp_id)
    opp_agent_2 = load_league_opponent(opp_id)
    a7_pure = load_league_opponent("E2_A7")
    a7_market = wrap_market_overlay(load_league_opponent("E2_A7"), demand_alpha=0.25)

    # 1. Run pure A7
    env_pure = make("kaggriculture", configuration={"seed": seed, "episodeSteps": 720})
    if seat == 0:
        env_pure.run([a7_pure, opp_agent_1])
        pure_cash = float(env_pure.steps[-1][0]["reward"] or 0.0)
        pure_opp_cash = float(env_pure.steps[-1][1]["reward"] or 0.0)
    else:
        env_pure.run([opp_agent_1, a7_pure])
        pure_cash = float(env_pure.steps[-1][1]["reward"] or 0.0)
        pure_opp_cash = float(env_pure.steps[-1][0]["reward"] or 0.0)

    # 2. Run A7 + Market Overlay
    env_mkt = make("kaggriculture", configuration={"seed": seed, "episodeSteps": 720})
    if seat == 0:
        env_mkt.run([a7_market, opp_agent_2])
        mkt_cash = float(env_mkt.steps[-1][0]["reward"] or 0.0)
        mkt_opp_cash = float(env_mkt.steps[-1][1]["reward"] or 0.0)
    else:
        env_mkt.run([opp_agent_2, a7_market])
        mkt_cash = float(env_mkt.steps[-1][1]["reward"] or 0.0)
        mkt_opp_cash = float(env_mkt.steps[-1][0]["reward"] or 0.0)

    delta = mkt_cash - pure_cash
    pure_win = 1 if pure_cash > pure_opp_cash else (0.5 if pure_cash == pure_opp_cash else 0)
    mkt_win = 1 if mkt_cash > mkt_opp_cash else (0.5 if mkt_cash == mkt_opp_cash else 0)

    return {
        "opp": opp_id,
        "seed": seed,
        "seat": seat,
        "pure_cash": pure_cash,
        "mkt_cash": mkt_cash,
        "delta": delta,
        "pure_win": pure_win,
        "mkt_win": mkt_win,
    }


def run_market_benchmark(n_workers: int = 8):
    tasks = []
    for opp in LEAGUE_OPPONENTS:
        for s in DEV_SEEDS:
            for seat in (0, 1):
                tasks.append((opp, s, seat))

    print(f"Running Market Overlay Benchmark: {len(tasks)} legs across {n_workers} workers...")
    t0 = time.time()
    with mp.Pool(processes=n_workers) as pool:
        results = pool.map(_eval_match_pair, tasks)

    print(f"Benchmark finished in {time.time() - t0:.1f}s!")

    total_legs = len(results)
    pure_wins = sum(r["pure_win"] for r in results)
    mkt_wins = sum(r["mkt_win"] for r in results)
    mean_delta = float(np.mean([r["delta"] for r in results]))
    mean_pure_cash = float(np.mean([r["pure_cash"] for r in results]))
    mean_mkt_cash = float(np.mean([r["mkt_cash"] for r in results]))

    print(f"Pure A7 Mean Cash:            ${mean_pure_cash:,.2f}")
    print(f"A7 + Market Overlay Cash:     ${mean_mkt_cash:,.2f}")
    print(f"Mean Paired Delta vs A7:      ${mean_delta:+,.2f}")
    print(f"Pure A7 Win Rate:             {pure_wins}/{total_legs} ({pure_wins/total_legs*100:.1f}%)")
    print(f"A7 + Market Overlay Win Rate: {mkt_wins}/{total_legs} ({mkt_wins/total_legs*100:.1f}%)")

    summary = {
        "total_legs": total_legs,
        "pure_wins": pure_wins,
        "mkt_wins": mkt_wins,
        "mean_pure_cash": mean_pure_cash,
        "mean_mkt_cash": mean_mkt_cash,
        "mean_delta": mean_delta,
        "detailed_results": results
    }

    with open("market_timing_results.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print("Saved market_timing_results.json!")
    return summary


if __name__ == "__main__":
    run_market_benchmark()
