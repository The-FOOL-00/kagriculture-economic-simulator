# SPDX-License-Identifier: MIT
"""Phase 6: Broader Opponent Validation.

Evaluates A7 vs V35 paired head-to-head across the entire repository opponent ecosystem:
1. E0_V3: Frozen base (older route)
2. E1_V22R1: Portfolio champion (strongest known candidate)
3. E2_A7: Incumbent benchmark
4. E3_V25P3: V25 P3 unified (distinct older route family)
5. E4_A1: A1 ablation (no opening wash / PASS)
6. E5_A2: A2 ablation (small 10/10 opening wash)
7. E6_W72: Delayed wash at step 72
8. E7_W2015: Asymmetric wash (20 buy / 15 sell)
9. E8_DMITRII: Frontier competitor (LB 2800+)
10. V54: Declarative reference
11. SYN_AGG: Synthetic hostile market stressor
12. PASSIVE: Passive baseline

Seed panel: 5 diverse non-holdout seeds [249675, 249676, 249677, 249678, 249679] across both seats (Seat 0 & 1).
Total: 12 opponents x 5 seeds x 2 seats x 2 policies = 240 matches.
Outputs scratch/phase6_broad_validation_results.json.
"""

import json
import multiprocessing as mp
import os
import sys
import time
from typing import Any, Dict, List, Tuple
import numpy as np

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from kaggle_environments import make
from scripts.v32_common import load_agent
from candidates.v32_rlx2.opponents import load_league_opponent
from candidates.v35_a7_opening.main import V35OpeningController

DEV_SEEDS = [249675, 249676, 249677, 249678, 249679]

ALL_OPPONENTS = [
    "E0_V3",
    "E1_V22R1",
    "E2_A7",
    "E3_V25P3",
    "E4_A1",
    "E5_A2",
    "E6_W72",
    "E7_W2015",
    "E8_DMITRII",
    "V54",
    "SYN_AGG",
    "PASSIVE",
]

def _eval_broad_leg(args: Tuple[str, str, int, int]) -> Dict[str, Any]:
    pol_name, opp_id, seed, seat = args
    if pol_name == "A7":
        a7 = load_agent("E9_AST")
        cand_fn = lambda o, c=None: a7.act(o, c)
    else:
        ctrl = V35OpeningController(25, 25)
        cand_fn = ctrl

    opp_fn = load_league_opponent(opp_id)
    env = make("kaggriculture", configuration={"seed": seed, "episodeSteps": 720})

    if seat == 0:
        env.run([cand_fn, opp_fn])
        c_cash = float(env.steps[-1][0]["reward"] or 0.0)
        o_cash = float(env.steps[-1][1]["reward"] or 0.0)
    else:
        env.run([opp_fn, cand_fn])
        c_cash = float(env.steps[-1][1]["reward"] or 0.0)
        o_cash = float(env.steps[-1][0]["reward"] or 0.0)

    win = 1.0 if c_cash > o_cash else (0.5 if c_cash == o_cash else 0.0)
    return {
        "policy": pol_name,
        "opponent": opp_id,
        "seed": seed,
        "seat": seat,
        "cand_cash": c_cash,
        "opp_cash": o_cash,
        "win": win,
    }


def main():
    tasks = []
    for pol in ["A7", "V35"]:
        for opp in ALL_OPPONENTS:
            for s in DEV_SEEDS:
                for seat in (0, 1):
                    tasks.append((pol, opp, s, seat))

    print(f"Executing Phase 6 Broader Opponent Tournament: {len(tasks)} matches across 8 workers...")
    t0 = time.time()
    with mp.Pool(processes=8) as pool:
        raw_results = pool.map(_eval_broad_leg, tasks)
    elapsed = time.time() - t0
    print(f"Phase 6 completed in {elapsed:.1f}s.")

    a7_legs = {(r["opponent"], r["seed"], r["seat"]): r for r in raw_results if r["policy"] == "A7"}
    v35_legs = {(r["opponent"], r["seed"], r["seat"]): r for r in raw_results if r["policy"] == "V35"}

    opp_summary = {}
    for opp in ALL_OPPONENTS:
        keys = [k for k in a7_legs if k[0] == opp]
        tot = len(keys)
        a7_pts = sum(a7_legs[k]["win"] for k in keys)
        v35_pts = sum(v35_legs[k]["win"] for k in keys)

        deltas = [v35_legs[k]["cand_cash"] - a7_legs[k]["cand_cash"] for k in keys]
        cas = sum(1 for k in keys if a7_legs[k]["win"] == 1.0 and v35_legs[k]["win"] < 1.0)
        res = sum(1 for k in keys if a7_legs[k]["win"] < 1.0 and v35_legs[k]["win"] == 1.0)

        in_120_bm = opp in ["E2_A7", "E1_V22R1", "E0_V3", "E8_DMITRII", "V54", "SYN_AGG"]

        opp_summary[opp] = {
            "opponent": opp,
            "in_original_benchmark": in_120_bm,
            "matches": tot,
            "a7_points": a7_pts,
            "v35_points": v35_pts,
            "a7_win_rate": a7_pts / tot,
            "v35_win_rate": v35_pts / tot,
            "rescues": res,
            "casualties": cas,
            "mean_paired_delta": float(np.mean(deltas)),
            "median_paired_delta": float(np.median(deltas)),
            "worst_paired_delta": float(np.min(deltas)),
            "max_paired_delta": float(np.max(deltas)),
        }

    with open("scratch/phase6_broad_validation_results.json", "w") as f:
        json.dump(opp_summary, f, indent=2)

    print("\n--- PHASE 6 BROADER OPPONENT SUMMARY ---")
    print(f"{'Opponent':<12} | {'InBM':<5} | {'A7 WR':<8} | {'V35 WR':<8} | {'Rescues':<8} | {'Cas':<5} | {'MeanDelta':<12} | {'WorstDelta':<12}")
    print("-" * 85)
    for opp in ALL_OPPONENTS:
        s = opp_summary[opp]
        in_bm_str = "YES" if s["in_original_benchmark"] else "NO"
        print(f"{s['opponent']:<12} | {in_bm_str:<5} | {s['a7_win_rate']*100:<7.1f}% | {s['v35_win_rate']*100:<7.1f}% | {s['rescues']:<8d} | {s['casualties']:<5d} | {s['mean_paired_delta']:<+11.2f} | {s['worst_paired_delta']:<+11.2f}")

if __name__ == "__main__":
    main()
