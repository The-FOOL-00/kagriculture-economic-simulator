# SPDX-License-Identifier: MIT
"""Kagriculture V32 P12 League & Match Evaluator.

Runs paired, mirrored evaluations across opponent leagues, seeds, and seats,
computing statistical metrics (mean, median, P25, P75, min, max, paired delta, W/L/T).
"""

from __future__ import annotations
import copy
import json
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import Any, Dict, List, Optional, Tuple
import numpy as np

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from kaggle_environments import make
from scripts.v32_common import load_agent
from candidates.v32_rlx2.opponents import load_league_opponent
from candidates.v32_p12_options.selector import SparseOptionController, OptionControllerConfig


def _get_shared_obs(env: Any, pos: int) -> Dict[str, Any]:
    obs = copy.deepcopy(env.steps[-1][pos]["observation"])
    for k in ("step", "market", "town", "day", "hour"):
        if k in env.steps[-1][0]["observation"] and k not in obs:
            obs[k] = env.steps[-1][0]["observation"][k]
    return obs


def run_paired_leg(
    seed: int,
    opponent_id: str,
    seat: int,
    controller_config: Optional[OptionControllerConfig] = None
) -> Dict[str, Any]:
    """Runs a paired match leg:

    1. A7 baseline vs opponent
    2. Candidate policy vs opponent
    under the exact same seed, seat, and opponent trajectory.
    """
    # 1. Baseline A7
    env_base = make("kaggriculture", configuration={"seed": seed})
    env_base.reset()
    a7_agent = load_agent("E9_AST")
    opp_base = load_league_opponent(opponent_id)

    while not env_base.done:
        p_obs = _get_shared_obs(env_base, seat)
        opp_obs = _get_shared_obs(env_base, 1 - seat)
        act_p = a7_agent.act(p_obs)
        act_opp = opp_base(opp_obs)
        if seat == 0:
            env_base.step([act_p, act_opp])
        else:
            env_base.step([act_opp, act_p])

    a7_cash = float(env_base.steps[-1][seat]["reward"] or 0.0)
    opp_cash_base = float(env_base.steps[-1][1 - seat]["reward"] or 0.0)

    # 2. Candidate Policy
    env_cand = make("kaggriculture", configuration={"seed": seed})
    env_cand.reset()
    controller = SparseOptionController(controller_config or OptionControllerConfig())
    opp_cand = load_league_opponent(opponent_id)

    step_times = []
    while not env_cand.done:
        p_obs = _get_shared_obs(env_cand, seat)
        opp_obs = _get_shared_obs(env_cand, 1 - seat)
        
        t0 = time.time()
        act_p = controller.act(p_obs)
        step_times.append(time.time() - t0)
        
        act_opp = opp_cand(opp_obs)
        if seat == 0:
            env_cand.step([act_p, act_opp])
        else:
            env_cand.step([act_opp, act_p])

    cand_cash = float(env_cand.steps[-1][seat]["reward"] or 0.0)
    opp_cash_cand = float(env_cand.steps[-1][1 - seat]["reward"] or 0.0)

    paired_delta = cand_cash - a7_cash
    win = 1 if cand_cash > opp_cash_cand else 0
    loss = 1 if cand_cash < opp_cash_cand else 0
    tie = 1 if cand_cash == opp_cash_cand else 0

    return {
        "seed": seed,
        "opponent": opponent_id,
        "seat": seat,
        "a7_cash": a7_cash,
        "cand_cash": cand_cash,
        "opp_cash_cand": opp_cash_cand,
        "paired_delta": paired_delta,
        "win": win,
        "loss": loss,
        "tie": tie,
        "options_activated": controller.options_executed_this_episode,
        "mean_step_time_ms": float(np.mean(step_times) * 1000.0) if step_times else 0.0,
        "max_step_time_ms": float(np.max(step_times) * 1000.0) if step_times else 0.0,
    }


def aggregate_benchmark_results(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not results:
        return {}
    cand_scores = [r["cand_cash"] for r in results]
    a7_scores = [r["a7_cash"] for r in results]
    deltas = [r["paired_delta"] for r in results]
    wins = sum(r["win"] for r in results)
    losses = sum(r["loss"] for r in results)
    ties = sum(r["tie"] for r in results)
    activations = sum(r["options_activated"] for r in results)

    return {
        "legs": len(results),
        "cand_mean": float(np.mean(cand_scores)),
        "cand_median": float(np.median(cand_scores)),
        "cand_p25": float(np.percentile(cand_scores, 25)),
        "cand_p75": float(np.percentile(cand_scores, 75)),
        "cand_min": float(np.min(cand_scores)),
        "cand_max": float(np.max(cand_scores)),
        "a7_mean": float(np.mean(a7_scores)),
        "a7_median": float(np.median(a7_scores)),
        "paired_delta_mean": float(np.mean(deltas)),
        "paired_delta_median": float(np.median(deltas)),
        "paired_delta_min": float(np.min(deltas)),
        "paired_delta_max": float(np.max(deltas)),
        "wins": wins,
        "losses": losses,
        "ties": ties,
        "win_rate": float(wins / len(results)),
        "total_activations": activations,
        "mean_activations_per_game": float(activations / len(results)),
    }
