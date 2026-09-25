# SPDX-License-Identifier: MIT
"""Kagriculture V44 Full-Horizon Alpha Family Counterfactual Search Engine.

Evaluates all candidate interventions across the economic taxonomy using FULL TERMINAL ROLLOUTS (to Step 719):
- Family A: Land Economics (Advance Land 1, Advance Land 2, Purchase Land 3, Defer Land 3)
- Family B: Labor Economics (Hire Early Surge, Cap Late Hiring)
- Family C: Livestock Economics (Extra Cow Early, Extra Sheep Early, Payback Cutoff)
- Family D: Town Shop Scarcity Arbitrage (Shop Consumption Tick, Town Center Tick)
- Family E: Liquidity Management (Cash Buffer Shield)
- Family F: Composition with V43 (Intervention + Terminal Staggered Flush)

Outputs: research/v44/artifacts/alpha_family_results.json
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
from research.v44.executor.v44_executor import (
    V44SafeExecutor,
    V44_INTERVENTIONS,
    V44_INTERVENTION_NAMES,
    NUM_V44_INTERVENTIONS
)
from candidates.v32_rlx2.opponents import load_league_opponent

DEV_SEEDS = [249675, 249676, 249677, 249678, 249679, 249680]
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


def simulate_full_match(
    seed: int,
    opp_master: Any,
    scheduled_interventions: Dict[int, int],
    player: int = 0
) -> Dict[str, Any]:
    """Runs simulation from Step 0 to terminal Step 719 with scheduled interventions."""
    assert_seed_safe(seed)
    sim = FastKagricultureSim(seed=seed)
    executor = V44SafeExecutor()
    opp = copy.deepcopy(opp_master)
    obs0, obs1 = sim.reset(seed=seed)

    while not sim.done:
        step = int(obs0.get("step", 0) or 0)
        # Check if intervention is scheduled for this step
        act_id = scheduled_interventions.get(step, 0)

        # In composite mode, add terminal flush if scheduled
        if scheduled_interventions.get("COMPOSITE_V43", False):
            if step in (693, 694, 704, 705) or step >= 716:
                act_id = 13  # TERMINAL_STAGGERED_FLUSH

        my_obs = obs0 if player == 0 else obs1
        opp_obs = obs1 if player == 0 else obs0

        act_my = executor.execute(act_id, my_obs, player=player)
        act_opp = opp(opp_obs)

        if player == 0:
            [obs0, obs1], _, _, _ = sim.step([act_my, act_opp])
        else:
            [obs0, obs1], _, _, _ = sim.step([act_opp, act_my])

    my_cash = float(obs0["farms"][player]["money"]) if player == 0 else float(obs1["farms"][player]["money"])
    opp_cash = float(obs1["farms"][1 - player]["money"]) if player == 0 else float(obs0["farms"][1 - player]["money"])
    margin = my_cash - opp_cash
    win = margin > 0

    return {
        "cash": my_cash,
        "opp_cash": opp_cash,
        "margin": margin,
        "win": win
    }


def run_family_search():
    print("=" * 80)
    print("V44 SYSTEMATIC ECONOMIC ALPHA FAMILY COUNTERFACTUAL SEARCH")
    print("=" * 80)
    t0 = time.perf_counter()

    opp_masters = {opp_id: load_league_opponent(opp_id) for opp_id in OPPONENTS}

    # Define test schedules for each candidate intervention
    candidate_tests = [
        # Family A: Land Economics
        ("ADVANCE_LAND_1", "LAND", {125: 1}),
        ("ADVANCE_LAND_2", "LAND", {230: 2}),
        ("PURCHASE_LAND_3", "LAND", {350: 3}),
        ("DEFER_LAND_3", "LAND", {s: 4 for s in range(450, 680, 10)}),

        # Family B: Labor Economics
        ("HIRE_EARLY_SURGE", "LABOR", {25: 5, 49: 5}),
        ("CAP_LATE_HIRING", "LABOR", {s: 6 for s in range(550, 680, 10)}),

        # Family C: Livestock Economics
        ("BUY_EXTRA_COW_EARLY", "LIVESTOCK", {80: 7}),
        ("BUY_EXTRA_SHEEP_EARLY", "LIVESTOCK", {80: 8}),
        ("INVESTMENT_PAYBACK_CUTOFF", "LIVESTOCK", {s: 9 for s in range(520, 680, 10)}),

        # Family D: Town Shop & Scarcity Arbitrage
        ("TOWN_SHOP_ARBITRAGE", "MARKET", {s: 10 for s in range(250, 680, 4)}),
        ("TOWN_CENTER_ARBITRAGE", "MARKET", {s: 11 for s in range(252, 680, 12)}),

        # Family E: Liquidity Management
        ("LIQUIDITY_BUFFER_SHIELD", "LIQUIDITY", {s: 12 for s in range(100, 400, 10)}),

        # Family F: Known Terminal Liquidation (Reference)
        ("TERMINAL_STAGGERED_FLUSH", "TERMINAL", {694: 13, 705: 13, 716: 13}),

        # Compositions: New Alpha + Terminal Liquidation
        ("COMPOSITE_ADVANCE_LAND_2", "COMPOSITE", {230: 2, "COMPOSITE_V43": True}),
        ("COMPOSITE_TOWN_SHOP_ARBITRAGE", "COMPOSITE", {**{s: 10 for s in range(250, 680, 4)}, "COMPOSITE_V43": True}),
        ("COMPOSITE_PAYBACK_CUTOFF", "COMPOSITE", {**{s: 9 for s in range(520, 680, 10)}, "COMPOSITE_V43": True}),
        ("COMPOSITE_EARLY_SURGE", "COMPOSITE", {25: 5, 49: 5, "COMPOSITE_V43": True}),
    ]

    results = []

    # First, evaluate baselines across all seeds and opponents
    baseline_cache = {}
    print("Computing baseline V35 rollouts...")
    for seed in DEV_SEEDS:
        for opp_id in OPPONENTS:
            base_res = simulate_full_match(seed, opp_masters[opp_id], {}, player=0)
            baseline_cache[(seed, opp_id)] = base_res

    print(f"Computed {len(baseline_cache)} baseline rollouts.\nEvaluating candidate economic families...")

    for cand_name, family, sched in candidate_tests:
        t_cand = time.perf_counter()
        cash_deltas = []
        margin_deltas = []
        cand_wins = 0
        base_wins = 0
        casualties = 0
        rescues = 0

        for seed in DEV_SEEDS:
            for opp_id in OPPONENTS:
                base_res = baseline_cache[(seed, opp_id)]
                cand_res = simulate_full_match(seed, opp_masters[opp_id], sched, player=0)

                d_cash = cand_res["cash"] - base_res["cash"]
                d_margin = cand_res["margin"] - base_res["margin"]

                cash_deltas.append(d_cash)
                margin_deltas.append(d_margin)

                if cand_res["win"]:
                    cand_wins += 1
                if base_res["win"]:
                    base_wins += 1

                if base_res["win"] and not cand_res["win"]:
                    casualties += 1
                if not base_res["win"] and cand_res["win"]:
                    rescues += 1

        mean_dc = float(np.mean(cash_deltas))
        med_dc = float(np.median(cash_deltas))
        mean_dm = float(np.mean(margin_deltas))
        p5_dc = float(np.percentile(cash_deltas, 5))
        worst_dc = float(np.min(cash_deltas))
        best_dc = float(np.max(cash_deltas))
        pos_rate = float(np.mean([1.0 if d > 0 else 0.0 for d in cash_deltas])) * 100.0

        dur_cand = time.perf_counter() - t_cand

        record = {
            "candidate_name": cand_name,
            "economic_family": family,
            "total_matches": len(cash_deltas),
            "mean_cash_delta": round(mean_dc, 2),
            "median_cash_delta": round(med_dc, 2),
            "mean_margin_delta": round(mean_dm, 2),
            "p5_downside_risk": round(p5_dc, 2),
            "worst_delta": round(worst_dc, 2),
            "best_delta": round(best_dc, 2),
            "positive_hit_rate_pct": round(pos_rate, 1),
            "candidate_win_rate_pct": round(cand_wins / len(cash_deltas) * 100.0, 1),
            "baseline_win_rate_pct": round(base_wins / len(cash_deltas) * 100.0, 1),
            "casualties": casualties,
            "rescues": rescues,
            "evaluation_duration_sec": round(dur_cand, 2)
        }
        results.append(record)

        print(f"[{family:<10}] {cand_name:<30} | Mean Delta: ${mean_dc:>+8.1f} | Med: ${med_dc:>+6.1f} | P5: ${p5_dc:>+6.1f} | Cas: {casualties} | Res: {rescues} | Hit: {pos_rate:>5.1f}%")

    out_file = os.path.join(REPO_ROOT, "research", "v44", "artifacts", "alpha_family_results.json")
    with open(out_file, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nAll alpha family results saved to {out_file}")

    dur_tot = time.perf_counter() - t0
    print(f"Total search duration: {dur_tot:.1f}s.")
    return results


if __name__ == "__main__":
    run_family_search()
