# SPDX-License-Identifier: MIT
"""V33 Route Counterfactual Oracle & Transition Safety Tester.

Tests route transitions from source route (R0_A7) to target routes (R1_V22R1, R2_DMITRII, R5_V25P3)
at candidate strategic boundaries t in {24, 48, 72, 144, 288}.
Measures physical consistency, cash impact, legality, and terminal counterfactual cash.
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
from candidates.v33_meta_strategy.route_bank import RouteBank

DEV_SEEDS = [249675, 249676, 249677]
SWITCH_BOUNDARIES = [24, 48, 72, 144, 288]
TARGET_ROUTES = ["R1_V22R1", "R2_DMITRII", "R5_V25P3"]


def _run_single_transition_leg(args: Tuple[int, str, int, float]) -> Dict[str, Any]:
    seed, target, t_switch, base_cash = args
    bank = RouteBank()
    r0_agent = bank.load_route("R0_A7")
    target_agent = bank.load_route(target)

    def hybrid(obs, configuration=None):
        step = int(obs.get("step", 0) or 0)
        if step < t_switch:
            return r0_agent(obs, configuration)
        else:
            return target_agent(obs, configuration)

    opp_agent = bank.load_route("R2_DMITRII")
    env = make("kaggriculture", configuration={"seed": seed, "episodeSteps": 720})
    try:
        env.run([hybrid, opp_agent])
        final_cash = float(env.steps[-1][0]["reward"] or 0.0)
        status = env.steps[-1][0].get("status", "DONE")
        legal = (status == "DONE")
    except Exception:
        final_cash = 0.0
        legal = False

    delta = final_cash - base_cash
    return {
        "seed": seed,
        "target_route": target,
        "switch_step": t_switch,
        "base_a7_cash": base_cash,
        "switched_cash": final_cash,
        "delta_vs_a7": delta,
        "legal": legal,
    }


def run_transition_test(n_workers: int = 8):
    bank = RouteBank()
    print("Evaluating Baseline A7 Cash across DEV seeds...")
    base_cashes = {}
    for s in DEV_SEEDS:
        a7 = bank.load_route("R0_A7")
        opp = bank.load_route("R2_DMITRII")
        env = make("kaggriculture", configuration={"seed": s, "episodeSteps": 720})
        env.run([a7, opp])
        base_cashes[s] = float(env.steps[-1][0]["reward"] or 0.0)
        print(f"Seed {s}: Baseline A7 cash = ${base_cashes[s]:,.0f}")

    tasks = []
    for s in DEV_SEEDS:
        for target in TARGET_ROUTES:
            for t_step in SWITCH_BOUNDARIES:
                tasks.append((s, target, t_step, base_cashes[s]))

    print(f"Running {len(tasks)} counterfactual transition matches across {n_workers} CPU workers...")
    t0 = time.time()
    with mp.Pool(processes=n_workers) as pool:
        results = pool.map(_run_single_transition_leg, tasks)
    print(f"Transitions evaluated in {time.time() - t0:.1f}s!")

    with open("route_counterfactuals.jsonl", "w", encoding="utf-8") as f:
        for r in results:
            f.write(json.dumps(r) + "\n")

    print("\n=================== TRANSITION SUMMARY BY TARGET & STEP ===================")
    for target in TARGET_ROUTES:
        for t_step in SWITCH_BOUNDARIES:
            recs = [r for r in results if r["target_route"] == target and r["switch_step"] == t_step]
            mean_delta = float(np.mean([r["delta_vs_a7"] for r in recs]))
            win_count = sum(1 for r in recs if r["delta_vs_a7"] > 0)
            print(f"Target: {target:<12} | Step {t_step:3d} | Mean Delta vs A7: ${mean_delta:+,.0f} | Positive: {win_count}/{len(recs)}")

    return results


if __name__ == "__main__":
    run_transition_test()
