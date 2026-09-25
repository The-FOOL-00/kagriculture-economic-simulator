# SPDX-License-Identifier: MIT
"""Phase 4: Opening-Wash Robustness Sweep across wash values 20..30."""

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
from candidates.v32_rlx2.opponents import load_league_opponent, LEAGUE_OPPONENTS
from candidates.v35_a7_opening.main import V35OpeningController

VALIDATION_SEEDS = [
    249675, 249676, 249677, 249678, 249679,  # Dev
    249680, 249681, 249682, 249683, 249684   # Fresh
]

WASH_VALUES = [20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30]

def _eval_leg(args: Tuple[int, str, int, int]) -> Dict[str, Any]:
    wash, opp_id, seed, seat = args
    cand = V35OpeningController(wash_buy=wash, wash_sell=wash)
    opp = load_league_opponent(opp_id)
    
    env = make("kaggriculture", configuration={"seed": seed, "episodeSteps": 720})
    if seat == 0:
        env.run([cand, opp])
        c_cash = float(env.steps[-1][0]["reward"] or 0.0)
        o_cash = float(env.steps[-1][1]["reward"] or 0.0)
    else:
        env.run([opp, cand])
        c_cash = float(env.steps[-1][1]["reward"] or 0.0)
        o_cash = float(env.steps[-1][0]["reward"] or 0.0)
        
    win = 1.0 if c_cash > o_cash else (0.5 if c_cash == o_cash else 0.0)
    return {
        "wash": wash,
        "opponent": opp_id,
        "seed": seed,
        "seat": seat,
        "cand_cash": c_cash,
        "opp_cash": o_cash,
        "win": win
    }

def main():
    # Load A7 baseline legs from benchmark_results.json
    with open("benchmark_results.json", "r") as f:
        bm = json.load(f)
    a7_lookup = {(l["seed"], l["opponent"], l["seat"]): l for l in bm["raw_legs"] if l["policy"] == "A7_BASELINE"}
    assert len(a7_lookup) == 120

    tasks = []
    for w in WASH_VALUES:
        for opp in LEAGUE_OPPONENTS:
            for s in VALIDATION_SEEDS:
                for seat in (0, 1):
                    tasks.append((w, opp, s, seat))

    print(f"Executing Phase 4 Sweep: {len(tasks)} matches ({len(WASH_VALUES)} wash values x 120 matches) using mp.Pool(8)...")
    t0 = time.time()
    with mp.Pool(processes=8) as pool:
        results = pool.map(_eval_leg, tasks)
    elapsed = time.time() - t0
    print(f"Phase 4 sweep completed in {elapsed:.1f}s ({elapsed/len(tasks)*1000:.1f} ms/match).")

    # Aggregate by wash value
    by_wash = {w: [] for w in WASH_VALUES}
    for r in results:
        by_wash[r["wash"]].append(r)

    summary_by_wash = {}
    for w in WASH_VALUES:
        w_legs = by_wash[w]
        tot = len(w_legs)
        pts = sum(x["win"] for x in w_legs)
        pure_w = sum(1 for x in w_legs if x["cand_cash"] > x["opp_cash"])
        pure_t = sum(1 for x in w_legs if x["cand_cash"] == x["opp_cash"])
        pure_l = sum(1 for x in w_legs if x["cand_cash"] < x["opp_cash"])
        
        cashes = [x["cand_cash"] for x in w_legs]
        deltas = [x["cand_cash"] - a7_lookup[(x["seed"], x["opponent"], x["seat"])]["cand_cash"] for x in w_legs]
        
        rescued = sum(1 for x in w_legs if a7_lookup[(x["seed"], x["opponent"], x["seat"])]["win"] < 1.0 and x["win"] == 1.0)
        casualties = sum(1 for x in w_legs if a7_lookup[(x["seed"], x["opponent"], x["seat"])]["win"] == 1.0 and x["win"] < 1.0)
        
        # Seat breakdown
        seat0 = [x for x in w_legs if x["seat"] == 0]
        seat1 = [x for x in w_legs if x["seat"] == 1]
        s0_pts = sum(x["win"] for x in seat0)
        s1_pts = sum(x["win"] for x in seat1)
        
        # Opponent breakdown
        opp_perf = {}
        for opp in LEAGUE_OPPONENTS:
            o_legs = [x for x in w_legs if x["opponent"] == opp]
            o_pts = sum(x["win"] for x in o_legs)
            opp_perf[opp] = {"pts": o_pts, "wr": o_pts / len(o_legs)}

        summary_by_wash[w] = {
            "wash": f"{w}/{w}",
            "matches": tot,
            "pts": pts,
            "win_rate": pts / tot,
            "pure_wins": pure_w,
            "pure_ties": pure_t,
            "pure_losses": pure_l,
            "mean_cash": float(np.mean(cashes)),
            "mean_paired_delta": float(np.mean(deltas)),
            "median_paired_delta": float(np.median(deltas)),
            "worst_paired_delta": float(np.min(deltas)),
            "max_paired_delta": float(np.max(deltas)),
            "rescued": rescued,
            "casualties": casualties,
            "seat0_wr": s0_pts / len(seat0),
            "seat1_wr": s1_pts / len(seat1),
            "opp_perf": opp_perf
        }

    # Save to json
    with open("scratch/phase4_wash_sweep_results.json", "w") as f:
        json.dump(summary_by_wash, f, indent=2)

    print("\n--- PHASE 4 SUMMARY TABLE ---")
    print(f"{'Wash':<6} | {'Pts':<6} | {'WinRate':<8} | {'Rescued':<8} | {'Cas':<5} | {'MeanDelta':<12} | {'WorstDelta':<12} | {'Seat0':<7} | {'Seat1':<7}")
    print("-" * 80)
    for w in WASH_VALUES:
        s = summary_by_wash[w]
        print(f"{s['wash']:<6} | {s['pts']:<6.1f} | {s['win_rate']*100:<7.2f}% | {s['rescued']:<8d} | {s['casualties']:<5d} | {s['mean_paired_delta']:<+11.2f} | {s['worst_paired_delta']:<+11.2f} | {s['seat0_wr']*100:<6.1f}% | {s['seat1_wr']*100:<6.1f}%")

if __name__ == "__main__":
    main()
