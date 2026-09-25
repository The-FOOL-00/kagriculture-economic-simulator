# SPDX-License-Identifier: MIT
"""V33 Meta Selector Benchmark & Ablation Harness.

Evaluates the integrated V33 Route Selector across the 6-opponent league:
1. Pure A7 (Incumbent Baseline)
2. Best Static Alternative (R1_V22R1)
3. Unconditional Switch (Always switch to R2_DMITRII at t=48)
4. V33 Selective Gated Meta-Controller (R0_A7 default + Gated R2_DMITRII switch)
5. V33 Midgame Meta Reset (Checkpoints at t in {48, 144})

Generates selector_dataset.jsonl, selector_predictions.jsonl, and benchmark_results.json.
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
from candidates.v32_rlx2.opponents import load_league_opponent, LEAGUE_OPPONENTS
from candidates.v33_meta_strategy.route_bank import RouteBank
from candidates.v33_meta_strategy.selector import RouteSelector

DEV_SEEDS = [249675, 249676, 249677, 249678, 249679]


def _build_meta_agent(
    policy_type: str,
    bank: RouteBank,
) -> Tuple[Callable, List[Dict[str, Any]]]:
    """Constructs an executable agent callable according to the designated policy archetype."""
    r0_a7 = bank.load_route("R0_A7")
    r1_v22 = bank.load_route("R1_V22R1")
    r2_dmitrii = bank.load_route("R2_DMITRII")

    if policy_type == "PURE_A7":
        return r0_a7, []

    elif policy_type == "STATIC_R1_V22R1":
        return r1_v22, []

    elif policy_type == "UNCONDITIONAL_SWITCH_R2":
        def uncod_agent(obs, cfg=None):
            step = int(obs.get("step", 0) or 0)
            if step < 48:
                return r0_a7(obs, cfg)
            return r2_dmitrii(obs, cfg)
        return uncod_agent, []

    elif policy_type == "V33_SELECTIVE_META":
        selector = RouteSelector(decision_steps=(24, 48, 72), min_gain_threshold=2500.0)
        logs = []

        def selective_agent(obs, cfg=None):
            step = int(obs.get("step", 0) or 0)
            decision = selector.evaluate(obs)
            if decision == "SWITCH_R2_DMITRII":
                logs.append({"step": step, "event": "SWITCH_R2_DMITRII"})
            
            if selector.current_route == "R2_DMITRII":
                try:
                    return r2_dmitrii(obs, cfg)
                except Exception:
                    return r0_a7(obs, cfg)
            return r0_a7(obs, cfg)

        return selective_agent, logs

    elif policy_type == "V33_MIDGAME_RESET":
        # Evaluates at checkpoints t in {48, 144}
        selector = RouteSelector(decision_steps=(48, 144), min_gain_threshold=2500.0)
        logs = []

        def reset_agent(obs, cfg=None):
            step = int(obs.get("step", 0) or 0)
            decision = selector.evaluate(obs)
            if decision == "SWITCH_R2_DMITRII":
                logs.append({"step": step, "event": "RESET_R2_DMITRII"})

            if selector.current_route == "R2_DMITRII":
                try:
                    return r2_dmitrii(obs, cfg)
                except Exception:
                    return r0_a7(obs, cfg)
            return r0_a7(obs, cfg)

        return reset_agent, logs

    else:
        raise ValueError(f"Unknown policy_type: {policy_type}")


def _eval_single_leg(args: Tuple[str, str, int, int]) -> Dict[str, Any]:
    policy_type, opp_id, seed, seat = args
    bank = RouteBank()
    opp_agent = load_league_opponent(opp_id)
    cand_agent, logs = _build_meta_agent(policy_type, bank)

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
    return {
        "policy": policy_type,
        "opp": opp_id,
        "seed": seed,
        "seat": seat,
        "cand_cash": cand_cash,
        "opp_cash": opp_cash,
        "win": win,
        "switches": len(logs),
        "logs": logs,
    }


def run_benchmark_panel(policies: List[str], n_workers: int = 10) -> Dict[str, Any]:
    tasks = []
    for pol in policies:
        for opp in LEAGUE_OPPONENTS:
            for s in DEV_SEEDS:
                for seat in (0, 1):
                    tasks.append((pol, opp, s, seat))

    print(f"Launching V33 Meta Selector Benchmark: {len(tasks)} matches across {n_workers} CPU workers...")
    t0 = time.time()
    with mp.Pool(processes=n_workers) as pool:
        raw_results = pool.map(_eval_single_leg, tasks)
    print(f"Completed {len(raw_results)} legs in {time.time() - t0:.1f}s!")

    # Aggregate by policy
    from collections import defaultdict
    by_policy = defaultdict(list)
    for r in raw_results:
        by_policy[r["policy"]].append(r)

    summary = {}
    for pol, legs in by_policy.items():
        total = len(legs)
        wins = sum(l["win"] for l in legs)
        cashes = [l["cand_cash"] for l in legs]
        switches = sum(l["switches"] for l in legs)
        summary[pol] = {
            "total_legs": total,
            "wins": wins,
            "win_rate": wins / total if total > 0 else 0.0,
            "mean_cash": float(np.mean(cashes)),
            "median_cash": float(np.median(cashes)),
            "p25_cash": float(np.percentile(cashes, 25)),
            "p75_cash": float(np.percentile(cashes, 75)),
            "min_cash": float(np.min(cashes)),
            "max_cash": float(np.max(cashes)),
            "total_switches": switches,
            "switch_frequency": switches / total if total > 0 else 0.0,
        }
        print(f"\n--- Policy: {pol} ---")
        print(f"  Win Rate:       {wins}/{total} ({wins/total*100:.1f}%)")
        print(f"  Mean Cash:      ${np.mean(cashes):,.2f}")
        print(f"  Median Cash:    ${np.median(cashes):,.2f}")
        print(f"  Min / Max Cash: ${np.min(cashes):,.2f} / ${np.max(cashes):,.2f}")
        print(f"  Total Switches: {switches}")

    # Save outputs
    with open("benchmark_results.json", "w", encoding="utf-8") as f:
        json.dump({"summary": summary, "raw_legs": raw_results}, f, indent=2)
    print("\nSaved benchmark_results.json!")

    # Save selector datasets
    with open("selector_predictions.jsonl", "w", encoding="utf-8") as f:
        for r in raw_results:
            if "SELECTIVE" in r["policy"] or "RESET" in r["policy"]:
                f.write(json.dumps(r) + "\n")
    print("Saved selector_predictions.jsonl!")

    return summary


if __name__ == "__main__":
    POLICIES = [
        "PURE_A7",
        "STATIC_R1_V22R1",
        "UNCONDITIONAL_SWITCH_R2",
        "V33_SELECTIVE_META",
        "V33_MIDGAME_RESET",
    ]
    run_benchmark_panel(POLICIES)
