# SPDX-License-Identifier: MIT
"""Phase 5: Adversarial Micro-Checks and Boundary Analysis.

Tests legal perturbations of Step-0 environment and observable state:
1. Legal starting cash variations: [2000, 2500, 2800, 3000, 3200, 3500, 4000]
2. Opponent opening Step-0 market behaviors:
   - PASSIVE / NO_WASH (market = [])
   - SMALL_WASH (10/10)
   - MED_WASH (20/20)
   - MIRROR_V35 (25/25)
   - STANDARD_A7 (30/30)
   - LARGE_WASH (50/50)
   - WHEAT_HOARDER (BUY 50 WHEAT)
   - WHEAT_DUMPER (SELL 50 WHEAT)
3. Seat reversal (Seat 0 vs Seat 1) across all perturbations.
4. Paired comparison: Does V35 (25/25) ever become harmful (paired delta < 0 or win rate drop) compared to A7 (30/30)?
Outputs scratch/phase5_boundary_results.json.
"""

import copy
import json
import multiprocessing as mp
import os
import sys
import time
from typing import Any, Callable, Dict, List, Optional, Tuple
import numpy as np

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from kaggle_environments import make
from scripts.v32_common import load_agent
from candidates.v35_a7_opening.main import V35OpeningController

DEV_SEEDS = [249675, 249676, 249677, 249678, 249679]

class PerturbedOpponent:
    """A7 opponent with custom Step-0 market action."""
    def __init__(self, mode: str):
        self.mode = mode
        self.a7 = load_agent("E9_AST")

    def reset(self):
        self.a7 = load_agent("E9_AST")

    def __call__(self, obs: Dict[str, Any], cfg: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return self.act(obs, cfg)

    def act(self, obs: Dict[str, Any], cfg: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        step = int(obs.get("step", 0) or 0)
        base = self.a7.act(obs, cfg)
        if step == 0:
            act = copy.deepcopy(base)
            if self.mode == "NO_WASH":
                act["market"] = []
            elif self.mode == "WASH_10":
                act["market"] = [["BUY_PRODUCT", "WHEAT", 10], ["SELL", "WHEAT", 10]]
            elif self.mode == "WASH_20":
                act["market"] = [["BUY_PRODUCT", "WHEAT", 20], ["SELL", "WHEAT", 20]]
            elif self.mode == "WASH_25":
                act["market"] = [["BUY_PRODUCT", "WHEAT", 25], ["SELL", "WHEAT", 25]]
            elif self.mode == "WASH_30":
                act["market"] = [["BUY_PRODUCT", "WHEAT", 30], ["SELL", "WHEAT", 30]]
            elif self.mode == "WASH_50":
                act["market"] = [["BUY_PRODUCT", "WHEAT", 50], ["SELL", "WHEAT", 50]]
            elif self.mode == "BUY_50":
                act["market"] = [["BUY_PRODUCT", "WHEAT", 50]]
            elif self.mode == "SELL_50":
                act["market"] = [["SELL", "WHEAT", 50]]
            return act
        return base


def _eval_adversarial_leg(args: Tuple[str, str, int, int, float, str]) -> Dict[str, Any]:
    test_type, pol_name, seed, seat, starting_cash, opp_mode = args
    if pol_name == "A7":
        cand = load_agent("E9_AST")
        cand_fn = lambda o, c=None: cand.act(o, c)
    else:
        ctrl = V35OpeningController(25, 25)
        cand_fn = ctrl

    opp = PerturbedOpponent(opp_mode)
    cfg = {"seed": seed, "episodeSteps": 720, "startingMoney": starting_cash}
    env = make("kaggriculture", configuration=cfg)

    if seat == 0:
        env.run([cand_fn, opp])
        c_cash = float(env.steps[-1][0]["reward"] or 0.0)
        o_cash = float(env.steps[-1][1]["reward"] or 0.0)
    else:
        env.run([opp, cand_fn])
        c_cash = float(env.steps[-1][1]["reward"] or 0.0)
        o_cash = float(env.steps[-1][0]["reward"] or 0.0)

    win = 1.0 if c_cash > o_cash else (0.5 if c_cash == o_cash else 0.0)
    return {
        "test_type": test_type,
        "policy": pol_name,
        "seed": seed,
        "seat": seat,
        "starting_cash": starting_cash,
        "opp_mode": opp_mode,
        "cand_cash": c_cash,
        "opp_cash": o_cash,
        "win": win,
    }


def main():
    tasks = []

    # Experiment 1: Starting Cash Sensitivity
    cash_levels = [2000.0, 2500.0, 2800.0, 3000.0, 3200.0, 3500.0, 4000.0]
    for c in cash_levels:
        for pol in ["A7", "V35"]:
            for s in DEV_SEEDS:
                for seat in (0, 1):
                    tasks.append(("cash_sensitivity", pol, s, seat, c, "WASH_30"))

    # Experiment 2: Opponent Opening Behaviors
    opp_modes = ["NO_WASH", "WASH_10", "WASH_20", "WASH_25", "WASH_30", "WASH_50", "BUY_50", "SELL_50"]
    for m in opp_modes:
        for pol in ["A7", "V35"]:
            for s in DEV_SEEDS:
                for seat in (0, 1):
                    tasks.append(("opp_behavior", pol, s, seat, 3000.0, m))

    print(f"Executing Phase 5 Adversarial Micro-Checks: {len(tasks)} matches across 8 workers...")
    t0 = time.time()
    with mp.Pool(processes=8) as pool:
        raw_results = pool.map(_eval_adversarial_leg, tasks)
    elapsed = time.time() - t0
    print(f"Phase 5 checks completed in {elapsed:.1f}s.")

    # Organize paired comparisons
    # 1. Cash Sensitivity
    cash_summary = {}
    for c in cash_levels:
        c_legs = [r for r in raw_results if r["test_type"] == "cash_sensitivity" and r["starting_cash"] == c]
        a7_legs = {(r["seed"], r["seat"]): r for r in c_legs if r["policy"] == "A7"}
        v35_legs = {(r["seed"], r["seat"]): r for r in c_legs if r["policy"] == "V35"}
        
        a7_pts = sum(r["win"] for r in a7_legs.values())
        v35_pts = sum(r["win"] for r in v35_legs.values())
        tot = len(a7_legs)
        
        deltas = [v35_legs[k]["cand_cash"] - a7_legs[k]["cand_cash"] for k in a7_legs]
        cas = sum(1 for k in a7_legs if a7_legs[k]["win"] == 1.0 and v35_legs[k]["win"] < 1.0)
        res = sum(1 for k in a7_legs if a7_legs[k]["win"] < 1.0 and v35_legs[k]["win"] == 1.0)
        
        cash_summary[str(int(c))] = {
            "starting_cash": c,
            "matches": tot,
            "a7_win_rate": a7_pts / tot,
            "v35_win_rate": v35_pts / tot,
            "mean_delta": float(np.mean(deltas)),
            "min_delta": float(np.min(deltas)),
            "rescued": res,
            "casualties": cas,
        }

    # 2. Opponent Behavior Sensitivity
    opp_summary = {}
    for m in opp_modes:
        m_legs = [r for r in raw_results if r["test_type"] == "opp_behavior" and r["opp_mode"] == m]
        a7_legs = {(r["seed"], r["seat"]): r for r in m_legs if r["policy"] == "A7"}
        v35_legs = {(r["seed"], r["seat"]): r for r in m_legs if r["policy"] == "V35"}
        
        a7_pts = sum(r["win"] for r in a7_legs.values())
        v35_pts = sum(r["win"] for r in v35_legs.values())
        tot = len(a7_legs)
        
        deltas = [v35_legs[k]["cand_cash"] - a7_legs[k]["cand_cash"] for k in a7_legs]
        cas = sum(1 for k in a7_legs if a7_legs[k]["win"] == 1.0 and v35_legs[k]["win"] < 1.0)
        res = sum(1 for k in a7_legs if a7_legs[k]["win"] < 1.0 and v35_legs[k]["win"] == 1.0)
        
        opp_summary[m] = {
            "opp_mode": m,
            "matches": tot,
            "a7_win_rate": a7_pts / tot,
            "v35_win_rate": v35_pts / tot,
            "mean_delta": float(np.mean(deltas)),
            "min_delta": float(np.min(deltas)),
            "rescued": res,
            "casualties": cas,
        }

    out_data = {
        "cash_sensitivity": cash_summary,
        "opp_behavior": opp_summary,
    }
    with open("scratch/phase5_boundary_results.json", "w") as f:
        json.dump(out_data, f, indent=2)

    print("\n--- CASH SENSITIVITY SUMMARY ---")
    for k, v in cash_summary.items():
        print(f"Cash ${k}: A7 WR={v['a7_win_rate']*100:.1f}%, V35 WR={v['v35_win_rate']*100:.1f}%, Rescues={v['rescued']}, Cas={v['casualties']}, MeanDelta={v['mean_delta']:+.1f}, MinDelta={v['min_delta']:+.1f}")

    print("\n--- OPPONENT BEHAVIOR SUMMARY ---")
    for k, v in opp_summary.items():
        print(f"Opp {k:<10}: A7 WR={v['a7_win_rate']*100:.1f}%, V35 WR={v['v35_win_rate']*100:.1f}%, Rescues={v['rescued']}, Cas={v['casualties']}, MeanDelta={v['mean_delta']:+.1f}, MinDelta={v['min_delta']:+.1f}")

if __name__ == "__main__":
    main()
