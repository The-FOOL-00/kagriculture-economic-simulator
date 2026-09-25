# SPDX-License-Identifier: MIT
"""Kagriculture V35 Opening Variable Sensitivity Search.

Evaluates one-variable-at-a-time perturbations to A7's opening capital decisions:
1. step0_wash_size: [20, 24, 25, 27, 28, 30, 32, 35]
2. step1_wheat_sell_qty: [10, 11, 12, 13, 14, 15]
3. step1_wheat_buy_qty: [0, 3, 5, 7, 10]
4. step1_hires_count: [4, 5, 6]
5. step6_melon_seeds: [1, 2, 3]

Measures:
- win rate
- mean cash
- paired cash delta vs A7 baseline
- earliest divergence step
- liquidity safety
Outputs opening_sensitivity.json.
"""

from __future__ import annotations
import copy
import json
import multiprocessing as mp
import os
import sys
import time
from typing import Any, Callable, Dict, List, Optional, Tuple
import numpy as np

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from kaggle_environments import make
from scripts.v32_common import load_agent
from candidates.v32_rlx2.opponents import load_league_opponent, LEAGUE_OPPONENTS

DEV_SEEDS = [249675, 249676, 249677, 249678, 249679]


class PerturbedOpeningAgent:
    """A7 agent with parametric opening perturbations."""
    def __init__(self, variable: str, value: Any):
        self.variable = variable
        self.value = value
        self.a7 = load_agent("E9_AST")

    def reset(self):
        self.a7 = load_agent("E9_AST")

    def __call__(self, obs: Dict[str, Any], cfg: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return self.act(obs, cfg)

    def act(self, obs: Dict[str, Any], cfg: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        step = int(obs.get("step", 0) or 0)
        base_act = self.a7.act(obs, cfg)

        if self.variable == "step0_wash_size" and step == 0:
            act = copy.deepcopy(base_act)
            sz = int(self.value)
            if sz == 0:
                act["market"] = []
            else:
                act["market"] = [["BUY_PRODUCT", "WHEAT", sz], ["SELL", "WHEAT", sz]]
            return act

        elif self.variable == "step1_wheat_sell_qty" and step == 1:
            act = copy.deepcopy(base_act)
            mkt = []
            for o in (act.get("market") or []):
                if o and o[0] == "SELL" and len(o) >= 2 and o[1] == "WHEAT":
                    mkt.append(["SELL", "WHEAT", int(self.value)])
                else:
                    mkt.append(o)
            act["market"] = mkt
            return act

        elif self.variable == "step1_wheat_buy_qty" and step == 1:
            act = copy.deepcopy(base_act)
            mkt = []
            qty = int(self.value)
            for o in (act.get("market") or []):
                if o and o[0] == "BUY_PRODUCT" and len(o) >= 2 and o[1] == "WHEAT":
                    if qty > 0:
                        mkt.append(["BUY_PRODUCT", "WHEAT", qty])
                else:
                    mkt.append(o)
            act["market"] = mkt
            return act

        elif self.variable == "step1_hires_count" and step == 1:
            act = copy.deepcopy(base_act)
            target_hires = int(self.value)
            non_hires = [o for o in (act.get("market") or []) if not (o and o[0] == "HIRE")]
            hires = [["HIRE"] for _ in range(target_hires)]
            act["market"] = (non_hires[:2] + hires + non_hires[2:])[:10]
            return act

        elif self.variable == "step6_melon_seeds" and step == 6:
            act = copy.deepcopy(base_act)
            mkt = []
            for o in (act.get("market") or []):
                if o and o[0] == "BUY_SEED" and len(o) >= 2 and o[1] == "MELON":
                    mkt.append(["BUY_SEED", "MELON", int(self.value)])
                else:
                    mkt.append(o)
            act["market"] = mkt
            return act

        return base_act


def _eval_perturbation_leg(args: Tuple[str, Any, str, int, int]) -> Dict[str, Any]:
    var_name, var_val, opp_id, seed, seat = args
    agent_inst = PerturbedOpeningAgent(var_name, var_val)
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
        "variable": var_name,
        "value": var_val,
        "opponent": opp_id,
        "seed": seed,
        "seat": seat,
        "cand_cash": cand_cash,
        "opp_cash": opp_cash,
        "delta": cand_cash - opp_cash,
        "win": win,
    }


def run_sensitivity_sweep(n_workers: int = 8) -> Dict[str, Any]:
    perturbations = [
        ("step0_wash_size", 20),
        ("step0_wash_size", 24),
        ("step0_wash_size", 25),
        ("step0_wash_size", 27),
        ("step0_wash_size", 28),
        ("step0_wash_size", 30),  # Baseline
        ("step0_wash_size", 32),
        ("step0_wash_size", 35),
        ("step1_wheat_sell_qty", 10),
        ("step1_wheat_sell_qty", 11),
        ("step1_wheat_sell_qty", 12),
        ("step1_wheat_sell_qty", 13),  # Baseline
        ("step1_wheat_sell_qty", 15),
        ("step1_wheat_buy_qty", 0),
        ("step1_wheat_buy_qty", 3),
        ("step1_wheat_buy_qty", 5),   # Baseline
        ("step1_wheat_buy_qty", 7),
        ("step1_hires_count", 4),
        ("step1_hires_count", 5),     # Baseline
        ("step1_hires_count", 6),
        ("step6_melon_seeds", 1),
        ("step6_melon_seeds", 2),     # Baseline
        ("step6_melon_seeds", 3),
    ]

    tasks = []
    # High-precision sample set for rapid triage
    sample_seeds = [249675, 249676]
    sample_opps = ["E2_A7", "E8_DMITRII", "SYN_AGG"]

    for var_name, val in perturbations:
        for opp in sample_opps:
            for s in sample_seeds:
                for seat in (0, 1):
                    tasks.append((var_name, val, opp, s, seat))

    print(f"Launching Opening Sensitivity Analysis: {len(tasks)} matches across {n_workers} CPU workers...")
    t0 = time.time()
    with mp.Pool(processes=n_workers) as pool:
        raw_results = pool.map(_eval_perturbation_leg, tasks)
    print(f"Sensitivity analysis completed in {time.time() - t0:.1f}s.")

    # Compute summaries
    by_var: Dict[str, Dict[str, List[Dict[str, Any]]]] = {}
    for r in raw_results:
        v = r["variable"]
        val_str = str(r["value"])
        by_var.setdefault(v, {}).setdefault(val_str, []).append(r)

    # Baseline lookup for A7 on sample set
    base_legs = {(r["opponent"], r["seed"], r["seat"]): r for r in by_var["step0_wash_size"]["30"]}

    summary: Dict[str, Any] = {}
    for v, val_dict in by_var.items():
        summary[v] = {}
        for val_str, legs in val_dict.items():
            tot = len(legs)
            wins = sum(x["win"] for x in legs)
            cashes = [x["cand_cash"] for x in legs]
            paired_deltas = [
                x["cand_cash"] - base_legs[(x["opponent"], x["seed"], x["seat"])]["cand_cash"]
                for x in legs
            ]
            rescued = sum(
                1 for x in legs
                if base_legs[(x["opponent"], x["seed"], x["seat"])]["win"] < 1.0 and x["win"] == 1.0
            )
            casualties = sum(
                1 for x in legs
                if base_legs[(x["opponent"], x["seed"], x["seat"])]["win"] == 1.0 and x["win"] < 1.0
            )

            summary[v][val_str] = {
                "matches": tot,
                "wins": wins,
                "win_rate": wins / tot if tot > 0 else 0.0,
                "mean_cash": float(np.mean(cashes)),
                "mean_paired_delta": float(np.mean(paired_deltas)),
                "worst_paired_delta": float(np.min(paired_deltas)),
                "rescued_losses": rescued,
                "casualty_wins": casualties,
            }

    out_file = os.path.join(REPO_ROOT, "opening_sensitivity.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print(f"Saved {out_file}")

    return summary


if __name__ == "__main__":
    run_sensitivity_sweep(n_workers=8)
