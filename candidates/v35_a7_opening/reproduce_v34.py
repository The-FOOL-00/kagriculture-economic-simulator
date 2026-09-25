# SPDX-License-Identifier: MIT
"""Kagriculture V35: Exact V34 Reproduction Benchmark.

Evaluates A7 baseline (30/30 wash) vs V34 Full (25/25 wash) across:
- 5 Dev Seeds: 249675, 249676, 249677, 249678, 249679
- 6 League Opponents: E2_A7, E1_V22R1, E0_V3, E8_DMITRII, V54, SYN_AGG
- 2 Seats: Seat 0, Seat 1
Total: 60 paired legs (120 games).

Verifies target results:
A7: 53/60 (88.3%)
V34: 57/60 (95.0%)
Outputs v34_reproduction.json.
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
from scripts.v32_common import load_agent
from candidates.v32_rlx2.opponents import load_league_opponent, LEAGUE_OPPONENTS
from candidates.v34_a7_tactical.main import V34TacticalController

DEV_SEEDS = [249675, 249676, 249677, 249678, 249679]


def _eval_match(args: Tuple[str, str, int, int]) -> Dict[str, Any]:
    policy_name, opp_id, seed, seat = args

    cand_ctrl = None
    if policy_name == "A7_BASELINE":
        a7 = load_agent("E9_AST")
        cand_agent = lambda o, c=None: a7.act(o, c)
    elif policy_name == "V34_WASH25":
        cand_ctrl = V34TacticalController(enable_tactical=True)
        cand_agent = cand_ctrl
    else:
        raise ValueError(f"Unknown policy {policy_name}")

    opp_agent = load_league_opponent(opp_id)
    env = make("kaggriculture", configuration={"seed": seed, "episodeSteps": 720})

    if seat == 0:
        env.run([cand_agent, opp_agent])
        cand_cash = float(env.steps[-1][0]["reward"] or 0.0)
        opp_cash = float(env.steps[-1][1]["reward"] or 0.0)
    else:
        env.run([opp_agent, cand_agent])
        cand_cash = float(env.steps[-1][1]["reward"] or 0.0)
        opp_cash = float(env.steps[-1][0]["reward"] or 0.0)

    win = 1.0 if cand_cash > opp_cash else (0.5 if cand_cash == opp_cash else 0.0)
    interventions = getattr(cand_ctrl, "interventions_count", 0) if cand_ctrl is not None else 0

    return {
        "policy": policy_name,
        "opponent": opp_id,
        "seed": seed,
        "seat": seat,
        "cand_cash": cand_cash,
        "opp_cash": opp_cash,
        "delta": cand_cash - opp_cash,
        "win": win,
        "interventions": interventions,
    }


def run_v34_reproduction(n_workers: int = 8) -> Dict[str, Any]:
    tasks = []
    for pol in ["A7_BASELINE", "V34_WASH25"]:
        for opp in LEAGUE_OPPONENTS:
            for s in DEV_SEEDS:
                for seat in (0, 1):
                    tasks.append((pol, opp, s, seat))

    print(f"Executing V34 Reproduction Benchmark: {len(tasks)} matches across {n_workers} CPU workers...")
    t0 = time.time()
    with mp.Pool(processes=n_workers) as pool:
        results = pool.map(_eval_match, tasks)
    elapsed = time.time() - t0
    print(f"Reproduction benchmark completed in {elapsed:.1f}s.")

    by_policy: Dict[str, List[Dict[str, Any]]] = {"A7_BASELINE": [], "V34_WASH25": []}
    for r in results:
        by_policy[r["policy"]].append(r)

    a7_lookup = {(r["opponent"], r["seed"], r["seat"]): r for r in by_policy["A7_BASELINE"]}

    summary = {}
    for pol in ["A7_BASELINE", "V34_WASH25"]:
        legs = by_policy[pol]
        tot = len(legs)
        wins = sum(x["win"] for x in legs)
        cashes = [x["cand_cash"] for x in legs]
        paired_deltas = [
            x["cand_cash"] - a7_lookup[(x["opponent"], x["seed"], x["seat"])]["cand_cash"]
            for x in legs
        ]
        interventions = sum(x["interventions"] for x in legs)

        summary[pol] = {
            "total_matches": tot,
            "wins": wins,
            "win_rate": wins / tot if tot > 0 else 0.0,
            "mean_cash": float(np.mean(cashes)),
            "median_cash": float(np.median(cashes)),
            "mean_paired_delta": float(np.mean(paired_deltas)),
            "worst_paired_delta": float(np.min(paired_deltas)),
            "total_interventions": interventions,
            "interventions_per_match": interventions / tot if tot > 0 else 0.0,
        }
        print(f"\nPolicy {pol}:")
        print(f"  Wins: {wins}/{tot} ({wins/tot*100:.1f}%)")
        print(f"  Mean Cash: ${np.mean(cashes):,.2f}")
        print(f"  Mean Paired Delta: ${np.mean(paired_deltas):+,.2f}")
        print(f"  Worst Paired Delta: ${np.min(paired_deltas):+,.2f}")

    # Compute flip transitions
    rescued_losses = 0
    casualties = 0
    for v in by_policy["V34_WASH25"]:
        a = a7_lookup[(v["opponent"], v["seed"], v["seat"])]
        if a["win"] < 1.0 and v["win"] == 1.0:
            rescued_losses += 1
        elif a["win"] == 1.0 and v["win"] < 1.0:
            casualties += 1

    summary["flips"] = {
        "rescued_losses": rescued_losses,
        "casualties": casualties,
    }
    print(f"\nRescued A7 Losses: {rescued_losses}")
    print(f"Casualty A7 Wins: {casualties}")

    out_file = os.path.join(REPO_ROOT, "v34_reproduction.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump({
            "summary": summary,
            "raw_legs": results,
            "verified": (summary["A7_BASELINE"]["wins"] == 53.0 and summary["V34_WASH25"]["wins"] == 57.0)
        }, f, indent=2)
    print(f"Saved {out_file}")

    return summary


if __name__ == "__main__":
    run_v34_reproduction(n_workers=8)
