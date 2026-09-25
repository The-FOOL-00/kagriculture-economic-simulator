# SPDX-License-Identifier: MIT
"""Kagriculture V43 Boundary Liquidation Grid Search.

Systematic exploration of multi-point liquidation schedules:
- First liquidation timing t1 in (692, 694, 696)
- First fraction f1 in (0.30, 0.40, 0.50, 0.60, 0.70)
- Second liquidation timing t2 in (700, 704, 705, 708)
- Second fraction f2 in (0.50, 0.70, 1.00)
- Final flush at t3 = 716 (100% of remaining)
Evaluated to terminal step 719 across diverse opponents and seeds.
"""

from __future__ import annotations
import copy
import json
import os
import sys
import time
from typing import Any, Dict, List, Tuple
import numpy as np

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from research.v40.env.fast_sim import FastKagricultureSim
from candidates.v35_a7_opening.main import V35OpeningController
from research.v43.executor.v43_executor import V43SafeExecutor, MARKETABLE_COMMODITIES
from candidates.v32_rlx2.opponents import load_league_opponent

# Safe training seeds (includes known loss seeds 249657 and close matches)
TEST_SEEDS = [249635, 249636, 249637, 249638, 249640, 249644, 249648, 249657]
OPPONENTS = ["E8_DMITRII", "E2_A7", "E0_V3", "SYN_AGG"]

PROTECTED_RANGES = [
    (214200, 214249),
    (340090, 340199),
    (249695, 249734),
]


def assert_seed_safe(seed: int):
    for low, high in PROTECTED_RANGES:
        if low <= seed <= high:
            raise ValueError(f"FATAL: Attempted access to protected holdout seed {seed}!")


def make_custom_liquidation_agent(t1: int, f1: float, t2: int, f2: float, t3: int = 716):
    executor = V43SafeExecutor()

    def _agent(obs, cfg=None):
        step = int(obs.get("step", 0) or 0)
        private = obs.get("private", {}) or {}
        shed = dict(private.get("shed", {}) or {})

        if step == t1 and any(shed.get(item, 0) >= 2 for item in MARKETABLE_COMMODITIES):
            return executor.execute(1, obs, cfg, custom_fraction=f1)
        elif step == t2 and any(shed.get(item, 0) >= 2 for item in MARKETABLE_COMMODITIES):
            return executor.execute(1, obs, cfg, custom_fraction=f2)
        elif step >= t3 and any(shed.get(item, 0) > 0 for item in MARKETABLE_COMMODITIES):
            return executor.execute(4, obs, cfg)

        return executor.execute(0, obs, cfg)

    return _agent


def run_liquidation_grid_search():
    print("=" * 80)
    print("V43 GENERALIZED STAGGERED LIQUIDATION BOUNDARY SEARCH")
    print("=" * 80)
    t0 = time.perf_counter()

    opp_masters = {opp_id: load_league_opponent(opp_id) for opp_id in OPPONENTS}

    # Schedules to evaluate: (t1, f1, t2, f2)
    schedules = [
        # V42 baseline: (694, 0.50, 705, 0.50)
        ("V42_50_50", 694, 0.50, 705, 0.50),
        # Fraction variations at (694, 705)
        ("SCHED_30_70", 694, 0.30, 705, 0.70),
        ("SCHED_40_60", 694, 0.40, 705, 0.60),
        ("SCHED_60_40", 694, 0.60, 705, 0.40),
        ("SCHED_70_30", 694, 0.70, 705, 0.30),
        ("SCHED_40_100", 694, 0.40, 705, 1.00),
        ("SCHED_50_100", 694, 0.50, 705, 1.00),
        # Timing variations
        ("TIMING_692_704", 692, 0.50, 704, 0.50),
        ("TIMING_692_705", 692, 0.50, 705, 0.50),
        ("TIMING_694_704", 694, 0.50, 704, 0.50),
        ("TIMING_694_708", 694, 0.50, 708, 0.50),
        ("TIMING_696_705", 696, 0.50, 705, 0.50),
        # Optimal candidate: 40% at 694 (preserves more depth), 60% at 705
        ("SCHED_40_60_704", 694, 0.40, 704, 0.60),
    ]

    # Pre-simulate baseline across all seeds and opponents to avoid recomputing
    baseline_cache = {}
    print("Computing baseline outcomes...")
    for seed in TEST_SEEDS:
        assert_seed_safe(seed)
        for opp_id in OPPONENTS:
            sim = FastKagricultureSim(seed=seed)
            base_agent = V35OpeningController()
            opp = copy.deepcopy(opp_masters[opp_id])
            obs0, obs1 = sim.reset(seed=seed)
            while not sim.done:
                [obs0, obs1], _, _, _ = sim.step([base_agent.act(obs0), opp(obs1)])
            b_cash = obs0["farms"][0]["money"]
            b_opp_cash = obs1["farms"][1]["money"]
            baseline_cache[(seed, opp_id)] = {
                "cash": b_cash,
                "opp_cash": b_opp_cash,
                "margin": b_cash - b_opp_cash,
                "win": (b_cash > b_opp_cash)
            }

    print(f"Baselines computed across {len(baseline_cache)} matches. Starting grid search...\n")

    grid_results = {}

    for sched_name, t1, f1, t2, f2 in schedules:
        deltas = []
        margin_deltas = []
        rescues = 0
        casualties = 0

        for seed in TEST_SEEDS:
            for opp_id in OPPONENTS:
                base = baseline_cache[(seed, opp_id)]
                sim = FastKagricultureSim(seed=seed)
                cand_agent = make_custom_liquidation_agent(t1, f1, t2, f2)
                opp = copy.deepcopy(opp_masters[opp_id])
                obs0, obs1 = sim.reset(seed=seed)
                while not sim.done:
                    [obs0, obs1], _, _, _ = sim.step([cand_agent(obs0), opp(obs1)])
                c_cash = obs0["farms"][0]["money"]
                c_opp_cash = obs1["farms"][1]["money"]
                c_margin = c_cash - c_opp_cash
                c_win = (c_cash > c_opp_cash)

                dc = c_cash - base["cash"]
                dm = c_margin - base["margin"]
                deltas.append(dc)
                margin_deltas.append(dm)

                if (not base["win"]) and c_win:
                    rescues += 1
                if base["win"] and (not c_win):
                    casualties += 1

        mean_dc = float(np.mean(deltas))
        med_dc = float(np.median(deltas))
        p5_dc = float(np.percentile(deltas, 5))
        p95_dc = float(np.percentile(deltas, 95))
        pos_rate = float(np.mean([d > 0 for d in deltas]) * 100.0)

        grid_results[sched_name] = {
            "schedule": sched_name,
            "t1": t1, "f1": f1, "t2": t2, "f2": f2,
            "mean_delta_cash": round(mean_dc, 2),
            "median_delta_cash": round(med_dc, 2),
            "p5_delta_cash": round(p5_dc, 2),
            "p95_delta_cash": round(p95_dc, 2),
            "positive_rate": round(pos_rate, 1),
            "rescues": rescues,
            "casualties": casualties,
        }

        print(f"[{sched_name:<16}] Mean: ${mean_dc:>+7.2f} | Med: ${med_dc:>+6.2f} | P5: ${p5_dc:>+7.2f} | P95: ${p95_dc:>+7.2f} | Pos: {pos_rate:>4.1f}% | Res: {rescues} | Cas: {casualties}")

    dur = time.perf_counter() - t0
    print(f"\nGrid search completed in {dur:.1f}s.")

    out_file = os.path.join(REPO_ROOT, "research", "v43", "artifacts", "liquidation_grid_search.json")
    with open(out_file, "w") as f:
        json.dump(grid_results, f, indent=2)
    print(f"Results saved to {out_file}")
    return grid_results


if __name__ == "__main__":
    run_liquidation_grid_search()
