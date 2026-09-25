# SPDX-License-Identifier: MIT
"""
V32 P12 Experiment P12-02: SPARSE-OPTION-4
Evaluates closed-loop A7 vs A7 + ONE 4-tick option (F1) across development seeds
against E2_A7 and E8_DMITRII in both Seat 0 and Seat 1.
"""

import copy
import json
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import Any, Dict, List
import numpy as np

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
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


def run_p12_02_leg(params: Dict[str, Any]) -> Dict[str, Any]:
    seed = params["seed"]
    opponent_id = params["opponent_id"]
    seat = params["seat"]

    # 1. Pure A7 Match
    env_a7 = make("kaggriculture", configuration={"seed": seed})
    env_a7.reset()
    a7_agent = load_agent("E9_AST")
    opp_a7 = load_league_opponent(opponent_id)

    while not env_a7.done:
        p_obs = _get_shared_obs(env_a7, seat)
        opp_obs = _get_shared_obs(env_a7, 1 - seat)
        act_p = a7_agent.act(p_obs)
        act_opp = opp_a7(opp_obs)
        if seat == 0:
            env_a7.step([act_p, act_opp])
        else:
            env_a7.step([act_opp, act_p])

    a7_cash = float(env_a7.steps[-1][seat]["reward"] or 0.0)

    # 2. Candidate Match: A7 + ONE 4-tick Option (F1)
    env_cand = make("kaggriculture", configuration={"seed": seed})
    env_cand.reset()
    cfg = OptionControllerConfig(
        max_options_per_episode=1,
        min_separation_ticks=24,
        option_horizon=4,
        require_full_sync=True,
        mode="oracle_search"
    )
    controller = SparseOptionController(cfg)
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
    paired_delta = cand_cash - a7_cash

    return {
        "seed": seed,
        "opponent": opponent_id,
        "seat": seat,
        "a7_cash": a7_cash,
        "cand_cash": cand_cash,
        "paired_delta": paired_delta,
        "options_activated": controller.options_executed_this_episode,
        "mean_ms": float(np.mean(step_times) * 1000.0) if step_times else 0.0,
        "max_ms": float(np.max(step_times) * 1000.0) if step_times else 0.0,
    }


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    # Seeds: Pilot training seeds where headroom was identified (249635, 249636, 249637)
    # plus held-out dev seeds (249675, 249676)
    seeds = [249635, 249636, 249637, 249675, 249676]
    opponents = ["E2_A7", "E8_DMITRII"]
    seats = [0, 1]

    tasks = [
        {"seed": s, "opponent_id": o, "seat": seat}
        for s in seeds for o in opponents for seat in seats
    ]

    print(f"Launching Experiment P12-02 (SPARSE-OPTION-4) across {len(tasks)} legs on 10 workers...")
    t0 = time.time()

    results = []
    with ProcessPoolExecutor(max_workers=10) as pool:
        future_map = {pool.submit(run_p12_02_leg, t): t for t in tasks}
        completed = 0
        for fut in as_completed(future_map):
            completed += 1
            res = fut.result()
            results.append(res)
            print(f"[{completed:2d}/{len(tasks)}] Seed {res['seed']} Opp {res['opponent']} Seat {res['seat']} -> "
                  f"A7: ${res['a7_cash']:7.1f} | Cand: ${res['cand_cash']:7.1f} | "
                  f"Delta: {res['paired_delta']:+8.1f} | Options: {res['options_activated']}",
                  flush=True)

    elapsed = time.time() - t0
    print(f"\nP12-02 complete in {elapsed:.2f}s!")

    out_path = "candidates/v32_p12_options/reports/p12_02_results.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"Saved results to {out_path}")

    # Aggregations
    deltas = [r["paired_delta"] for r in results]
    acts = [r["options_activated"] for r in results]
    print(f"\nAggregate P12-02 Summary ({len(results)} legs):")
    print(f"  Mean Paired Delta vs A7: {np.mean(deltas):+8.2f}")
    print(f"  Median Paired Delta:     {np.median(deltas):+8.2f}")
    print(f"  Min Paired Delta:        {np.min(deltas):+8.2f}")
    print(f"  Max Paired Delta:        {np.max(deltas):+8.2f}")
    print(f"  Total Options Activated: {sum(acts)} across {len(results)} legs (Mean: {np.mean(acts):.2f})")


if __name__ == "__main__":
    main()
