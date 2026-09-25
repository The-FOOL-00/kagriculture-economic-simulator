# SPDX-License-Identifier: MIT
"""Kagriculture V35 Dense Opening Wash Sweep Engine.

Evaluates dense symmetric and asymmetric opening wheat wash configurations:
Symmetric:
  40/40, 38/38, 36/36, 34/34, 32/32, 31/31, 30/30 (A7 baseline),
  29/29, 28/28, 27/27, 26/26, 25/25, 24/24, 23/23, 22/22, 21/21,
  20/20, 18/18, 16/16, 14/14, 12/12, 10/10, 0/0 (NO_WASH)
Asymmetric:
  30/25, 25/30, 30/20, 20/30, 28/25, 25/28, 27/25, 25/27, 26/24, 24/26

Outputs opening_wash_sweep.json.
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

SYMMETRIC_WASHES = [
    (40, 40), (38, 38), (36, 36), (34, 34), (32, 32), (31, 31),
    (30, 30), (29, 29), (28, 28), (27, 27), (26, 26), (25, 25),
    (24, 24), (23, 23), (22, 22), (21, 21), (20, 20), (18, 18),
    (16, 16), (14, 14), (12, 12), (10, 10), (0, 0)
]

ASYMMETRIC_WASHES = [
    (30, 25), (25, 30), (30, 20), (20, 30),
    (28, 25), (25, 28), (27, 25), (25, 27),
    (26, 24), (24, 26)
]

ALL_SWEEP_CONFIGS = SYMMETRIC_WASHES + ASYMMETRIC_WASHES


class ParametricWashAgent:
    """A7 agent with parametric Step 0 wheat wash override."""
    def __init__(self, buy_qty: int, sell_qty: int):
        self.buy_qty = buy_qty
        self.sell_qty = sell_qty
        self.a7 = load_agent("E9_AST")
        self.min_cash_day1 = 1000.0

    def reset(self):
        self.a7 = load_agent("E9_AST")
        self.min_cash_day1 = 1000.0

    def __call__(self, obs: Dict[str, Any], cfg: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return self.act(obs, cfg)

    def act(self, obs: Dict[str, Any], cfg: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        step = int(obs.get("step", 0) or 0)
        player = int(obs.get("player", 0) or 0)
        farms = obs.get("farms", []) or []
        if len(farms) > player:
            money = float(farms[player].get("money", 0.0) or 0.0)
            if step <= 24:
                self.min_cash_day1 = min(self.min_cash_day1, money)

        base_act = self.a7.act(obs, cfg)
        if step == 0:
            act = copy.deepcopy(base_act)
            if self.buy_qty == 0 and self.sell_qty == 0:
                act["market"] = []
            elif self.buy_qty > 0 and self.sell_qty == 0:
                act["market"] = [["BUY_PRODUCT", "WHEAT", self.buy_qty]]
            elif self.buy_qty == 0 and self.sell_qty > 0:
                act["market"] = [["SELL", "WHEAT", self.sell_qty]]
            else:
                act["market"] = [
                    ["BUY_PRODUCT", "WHEAT", self.buy_qty],
                    ["SELL", "WHEAT", self.sell_qty]
                ]
            return act
        return base_act


def _eval_sweep_leg(args: Tuple[int, int, str, int, int]) -> Dict[str, Any]:
    buy_q, sell_q, opp_id, seed, seat = args
    agent_inst = ParametricWashAgent(buy_qty=buy_q, sell_qty=sell_q)
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
        "buy_qty": buy_q,
        "sell_qty": sell_q,
        "opponent": opp_id,
        "seed": seed,
        "seat": seat,
        "cand_cash": cand_cash,
        "opp_cash": opp_cash,
        "delta": cand_cash - opp_cash,
        "win": win,
        "min_cash_day1": agent_inst.min_cash_day1,
    }


def run_opening_wash_sweep(
    configs: Optional[List[Tuple[int, int]]] = None,
    seeds: Optional[List[int]] = None,
    opponents: Optional[List[str]] = None,
    n_workers: int = 8,
    output_filename: str = "opening_wash_sweep.json",
) -> Dict[str, Any]:
    if configs is None:
        configs = ALL_SWEEP_CONFIGS
    if seeds is None:
        # 3 seeds across both seats for high-precision response curve mapping
        seeds = [249675, 249676, 249677]
    if opponents is None:
        # Focus on the two non-trivial opponents where A7 experiences ties and losses
        opponents = ["E2_A7", "E8_DMITRII"]

    tasks = []
    for (bq, sq) in configs:
        for opp in opponents:
            for s in seeds:
                for seat in (0, 1):
                    tasks.append((bq, sq, opp, s, seat))

    print(f"Executing Opening Wash Sweep: {len(tasks)} matches ({len(configs)} configs x {len(seeds)} seeds x {len(opponents)} opps x 2 seats) across {n_workers} CPU workers...")
    t0 = time.time()
    with mp.Pool(processes=n_workers) as pool:
        raw_results = pool.map(_eval_sweep_leg, tasks)
    elapsed = time.time() - t0
    print(f"Sweep completed in {elapsed:.1f}s.")

    # Group by configuration
    by_config: Dict[str, List[Dict[str, Any]]] = {}
    for r in raw_results:
        key = f"{r['buy_qty']}/{r['sell_qty']}"
        by_config.setdefault(key, []).append(r)

    # Establish baseline A7 (30/30) lookup
    a7_lookup = {}
    if "30/30" in by_config:
        for r in by_config["30/30"]:
            a7_lookup[(r["opponent"], r["seed"], r["seat"])] = r

    summary: Dict[str, Any] = {}
    for cfg_key, legs in by_config.items():
        tot = len(legs)
        wins = sum(x["win"] for x in legs)
        cashes = [x["cand_cash"] for x in legs]
        min_cash_d1 = [x["min_cash_day1"] for x in legs]

        paired_deltas = []
        rescued_losses = 0
        casualty_wins = 0

        for x in legs:
            a7_leg = a7_lookup.get((x["opponent"], x["seed"], x["seat"]))
            if a7_leg is not None:
                delta = x["cand_cash"] - a7_leg["cand_cash"]
                paired_deltas.append(delta)
                if a7_leg["win"] < 1.0 and x["win"] == 1.0:
                    rescued_losses += 1
                elif a7_leg["win"] == 1.0 and x["win"] < 1.0:
                    casualty_wins += 1
            else:
                paired_deltas.append(0.0)

        summary[cfg_key] = {
            "buy_qty": legs[0]["buy_qty"],
            "sell_qty": legs[0]["sell_qty"],
            "total_matches": tot,
            "wins": wins,
            "losses": tot - int(wins),
            "ties": sum(1 for x in legs if x["win"] == 0.5),
            "win_rate": wins / tot if tot > 0 else 0.0,
            "mean_cash": float(np.mean(cashes)),
            "median_cash": float(np.median(cashes)),
            "min_cash": float(np.min(cashes)),
            "max_cash": float(np.max(cashes)),
            "mean_paired_delta": float(np.mean(paired_deltas)),
            "median_paired_delta": float(np.median(paired_deltas)),
            "worst_paired_delta": float(np.min(paired_deltas)),
            "mean_day1_min_cash": float(np.mean(min_cash_d1)),
            "min_day1_min_cash": float(np.min(min_cash_d1)),
            "rescued_losses": rescued_losses,
            "casualty_wins": casualty_wins,
        }

    out_file = os.path.join(REPO_ROOT, output_filename)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump({
            "summary": summary,
            "configs": [f"{b}/{s}" for b, s in configs],
            "raw_results": raw_results,
        }, f, indent=2)
    print(f"Saved {out_file}")

    return summary


if __name__ == "__main__":
    run_opening_wash_sweep(n_workers=8)
