# SPDX-License-Identifier: MIT
"""Kagriculture V35 Two-Variable Opening Interaction Search.

Evaluates factorial combinations of:
Variable A: step0_wash_size in [20, 24, 25, 27, 30]
Variable B: step1_wheat_sell_qty in [10, 12, 13, 15]

Measures:
- individual effect A
- individual effect B
- joint combined effect
- interaction synergy = Combined - (Effect_A + Effect_B)
Outputs opening_interactions.json.
"""

from __future__ import annotations
import copy
import json
import multiprocessing as mp
import os
import sys
import time
from typing import Any, Dict, List, Optional, Tuple
import numpy as np

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from kaggle_environments import make
from scripts.v32_common import load_agent
from candidates.v32_rlx2.opponents import load_league_opponent, LEAGUE_OPPONENTS

SAMPLE_SEEDS = [249675, 249676, 249677]
SAMPLE_OPPS = ["E2_A7", "E8_DMITRII", "E1_V22R1", "SYN_AGG"]

WASH_VALS = [20, 24, 25, 27, 30]
SELL_VALS = [10, 12, 13, 15]


class JointOpeningAgent:
    def __init__(self, wash_size: int, sell_qty: int):
        self.wash_size = wash_size
        self.sell_qty = sell_qty
        self.a7 = load_agent("E9_AST")

    def reset(self):
        self.a7 = load_agent("E9_AST")

    def __call__(self, obs: Dict[str, Any], cfg: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return self.act(obs, cfg)

    def act(self, obs: Dict[str, Any], cfg: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        step = int(obs.get("step", 0) or 0)
        base_act = self.a7.act(obs, cfg)

        if step == 0:
            act = copy.deepcopy(base_act)
            if self.wash_size == 0:
                act["market"] = []
            else:
                act["market"] = [["BUY_PRODUCT", "WHEAT", self.wash_size], ["SELL", "WHEAT", self.wash_size]]
            return act

        elif step == 1:
            act = copy.deepcopy(base_act)
            mkt = []
            for o in (act.get("market") or []):
                if o and o[0] == "SELL" and len(o) >= 2 and o[1] == "WHEAT":
                    mkt.append(["SELL", "WHEAT", self.sell_qty])
                else:
                    mkt.append(o)
            act["market"] = mkt
            return act

        return base_act


def _eval_joint_leg(args: Tuple[int, int, str, int, int]) -> Dict[str, Any]:
    wash, sell, opp_id, seed, seat = args
    agent_inst = JointOpeningAgent(wash, sell)
    opp_agent = load_league_opponent(opp_id)

    env = make("kaggriculture", configuration={"seed": seed, "episodeSteps": 720})
    if seat == 0:
        env.run([agent_inst, opp_agent])
        cand_cash = float(env.steps[-1][0]["reward"] or 0.0)
        opp_cash = float(env.steps[-1][1]["reward"] or 0.0)
    else:
        env.run([opp_agent, agent_inst])
        cand_cash = float(env.steps[-1][1]["reward"] or 0.0)
        opp_cash = float(env.steps[-1][0]["reward"] or 0.0)

    win = 1.0 if cand_cash > opp_cash else (0.5 if cand_cash == opp_cash else 0.0)
    return {
        "wash_size": wash,
        "sell_qty": sell,
        "opponent": opp_id,
        "seed": seed,
        "seat": seat,
        "cand_cash": cand_cash,
        "opp_cash": opp_cash,
        "delta": cand_cash - opp_cash,
        "win": win,
    }


def run_interaction_grid(n_workers: int = 8) -> Dict[str, Any]:
    tasks = []
    for w in WASH_VALS:
        for s in SELL_VALS:
            for opp in SAMPLE_OPPS:
                for sd in SAMPLE_SEEDS:
                    for seat in (0, 1):
                        tasks.append((w, s, opp, sd, seat))

    print(f"Launching Opening Two-Variable Interaction Grid: {len(tasks)} matches ({len(WASH_VALS)}x{len(SELL_VALS)} grid) across {n_workers} CPU workers...")
    t0 = time.time()
    with mp.Pool(processes=n_workers) as pool:
        raw_results = pool.map(_eval_joint_leg, tasks)
    print(f"Interaction grid completed in {time.time() - t0:.1f}s.")

    # Group by (wash, sell)
    by_cell: Dict[Tuple[int, int], List[Dict[str, Any]]] = {}
    for r in raw_results:
        key = (r["wash_size"], r["sell_qty"])
        by_cell.setdefault(key, []).append(r)

    # Baseline: (30, 13)
    base_legs = {(r["opponent"], r["seed"], r["seat"]): r for r in by_cell[(30, 13)]}
    base_mean_cash = float(np.mean([r["cand_cash"] for r in by_cell[(30, 13)]]))
    base_win_rate = float(np.mean([r["win"] for r in by_cell[(30, 13)]]))

    cell_summary: Dict[str, Any] = {}
    for (w, s), legs in by_cell.items():
        cashes = [r["cand_cash"] for r in legs]
        wins = sum(r["win"] for r in legs)
        tot = len(legs)
        deltas = [r["cand_cash"] - base_legs[(r["opponent"], r["seed"], r["seat"])]["cand_cash"] for r in legs]

        cell_summary[f"WASH_{w}_SELL_{s}"] = {
            "wash_size": w,
            "sell_qty": s,
            "matches": tot,
            "wins": wins,
            "win_rate": wins / tot if tot > 0 else 0.0,
            "mean_cash": float(np.mean(cashes)),
            "mean_paired_delta": float(np.mean(deltas)),
            "worst_paired_delta": float(np.min(deltas)),
        }

    # Compute synergy
    grid_matrix = {}
    for w in WASH_VALS:
        grid_matrix[w] = {}
        delta_A = cell_summary[f"WASH_{w}_SELL_13"]["mean_paired_delta"]
        for s in SELL_VALS:
            delta_B = cell_summary[f"WASH_30_SELL_{s}"]["mean_paired_delta"]
            delta_AB = cell_summary[f"WASH_{w}_SELL_{s}"]["mean_paired_delta"]
            synergy = delta_AB - (delta_A + delta_B)
            grid_matrix[w][s] = {
                "delta_AB": delta_AB,
                "delta_A": delta_A,
                "delta_B": delta_B,
                "synergy": synergy,
                "win_rate": cell_summary[f"WASH_{w}_SELL_{s}"]["win_rate"],
            }

    out_file = os.path.join(REPO_ROOT, "opening_interactions.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump({
            "cell_summary": cell_summary,
            "interaction_matrix": grid_matrix,
        }, f, indent=2)
    print(f"Saved {out_file}")

    return cell_summary


if __name__ == "__main__":
    run_interaction_grid(n_workers=8)
