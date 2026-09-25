# SPDX-License-Identifier: MIT
"""Kagriculture V44 Full A/B Ladder Tournament Benchmark.

Evaluates the complete lineage across 4 league opponents in both seat positions:
- Ladder A: V35 Baseline (Production Incumbent)
- Ladder B: V39 Baseline (Step 694 full dump)
- Ladder C: V42 Deterministic (Staggered 50/50 liquidation at 694 & 705)
- Ladder D: V43 Sequence Deterministic (40% @ 694, 60% @ 705, 100% @ 716)
- Ladder E: V44 Economic Portfolio Champion (Town Shop Scarcity Arbitrage + Payback Cutoff + Staggered Flush)

Evaluated on clean, unseen DEV seeds (249685..249688) across paired matches.
Strict Zero-Touch on protected holdout seed ranges.
Outputs: research/v44/artifacts/ladder_tournament_results.json
"""

from __future__ import annotations
import copy
import json
import os
import sys
import time
from typing import Any, Callable, Dict, List, Tuple
import numpy as np

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from research.v40.env.fast_sim import FastKagricultureSim
from candidates.v35_a7_opening.main import V35OpeningController
from candidates.v39_live_targeted.main import V39TargetedController
from candidates.v42_alpha_residual.main import V42CandidateController
from candidates.v43_compositional_alpha.main import V43CandidateController
from candidates.v44_economic_portfolio.main import V44CandidateController
from candidates.v32_rlx2.opponents import load_league_opponent

DEV_SEEDS = [249685, 249686, 249687, 249688]  # Clean unseen DEV seeds
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


def _act(agent: Any, obs: Dict[str, Any]) -> Dict[str, Any]:
    if hasattr(agent, "act") and callable(getattr(agent, "act")):
        return agent.act(obs)
    return agent(obs)


def run_paired_match(
    cand_factory: Callable[[], Any],
    base_factory: Callable[[], Any],
    opp_master: Any,
    seed: int,
    opp_id: str
) -> Dict[str, Any]:
    """Runs paired 2-leg match in both seats."""
    # Seat 0
    sim_c0 = FastKagricultureSim(seed=seed)
    cand_c0 = cand_factory()
    opp_c0 = copy.deepcopy(opp_master)
    oc0, oc1 = sim_c0.reset(seed=seed)
    while not sim_c0.done:
        [oc0, oc1], _, _, _ = sim_c0.step([_act(cand_c0, oc0), opp_c0(oc1)])
    cand_cash_s0 = oc0["farms"][0]["money"]
    opp_cash_s0 = oc1["farms"][1]["money"]
    cand_win_s0 = cand_cash_s0 > opp_cash_s0

    sim_b0 = FastKagricultureSim(seed=seed)
    base_b0 = base_factory()
    opp_b0 = copy.deepcopy(opp_master)
    ob0, ob1 = sim_b0.reset(seed=seed)
    while not sim_b0.done:
        [ob0, ob1], _, _, _ = sim_b0.step([_act(base_b0, ob0), opp_b0(ob1)])
    base_cash_s0 = ob0["farms"][0]["money"]
    base_win_s0 = base_cash_s0 > ob1["farms"][1]["money"]

    # Seat 1
    sim_c1 = FastKagricultureSim(seed=seed)
    cand_c1 = cand_factory()
    opp_c1 = copy.deepcopy(opp_master)
    oc0, oc1 = sim_c1.reset(seed=seed)
    while not sim_c1.done:
        [oc0, oc1], _, _, _ = sim_c1.step([opp_c1(oc0), _act(cand_c1, oc1)])
    cand_cash_s1 = oc1["farms"][1]["money"]
    opp_cash_s1 = oc0["farms"][0]["money"]
    cand_win_s1 = cand_cash_s1 > opp_cash_s1

    sim_b1 = FastKagricultureSim(seed=seed)
    base_b1 = base_factory()
    opp_b1 = copy.deepcopy(opp_master)
    ob0, ob1 = sim_b1.reset(seed=seed)
    while not sim_b1.done:
        [ob0, ob1], _, _, _ = sim_b1.step([opp_b1(ob0), _act(base_b1, ob1)])
    base_cash_s1 = ob1["farms"][1]["money"]
    base_win_s1 = base_cash_s1 > ob0["farms"][0]["money"]

    mean_cand_cash = (cand_cash_s0 + cand_cash_s1) / 2.0
    mean_base_cash = (base_cash_s0 + base_cash_s1) / 2.0
    cash_delta = mean_cand_cash - mean_base_cash

    cand_wins = int(cand_win_s0) + int(cand_win_s1)
    base_wins = int(base_win_s0) + int(base_win_s1)

    rescues = (int(not base_win_s0 and cand_win_s0)) + (int(not base_win_s1 and cand_win_s1))
    casualties = (int(base_win_s0 and not cand_win_s0)) + (int(base_win_s1 and not cand_win_s1))

    return {
        "seed": seed,
        "opp_id": opp_id,
        "cash_delta": cash_delta,
        "cand_wins": cand_wins,
        "base_wins": base_wins,
        "rescues": rescues,
        "casualties": casualties,
    }


def evaluate_v44_ladder(seeds: List[int] = DEV_SEEDS):
    print("=" * 80)
    print("V44 A/B LADDER TOURNAMENT BENCHMARK")
    print("=" * 80)
    t0 = time.perf_counter()

    ladders = {
        "Ladder A (V35 Baseline)": lambda: V35OpeningController(),
        "Ladder B (V39 Targeted)": lambda: V39TargetedController(),
        "Ladder C (V42-Det)": lambda: V42CandidateController(),
        "Ladder D (V43-Seq Det)": lambda: V43CandidateController(),
        "Ladder E (V44-Economic Portfolio)": lambda: V44CandidateController(),
    }

    opp_masters = {opp_id: load_league_opponent(opp_id) for opp_id in OPPONENTS}
    base_v35_factory = lambda: V35OpeningController()

    tournament_results = {}

    for lad_name, cand_factory in ladders.items():
        print(f"\n--- Evaluating {lad_name} vs V35 Baseline ---")
        lad_matches = []
        for seed in seeds:
            assert_seed_safe(seed)
            for opp_id in OPPONENTS:
                res = run_paired_match(
                    cand_factory=cand_factory,
                    base_factory=base_v35_factory,
                    opp_master=opp_masters[opp_id],
                    seed=seed,
                    opp_id=opp_id
                )
                lad_matches.append(res)
                print(f"  Seed {seed} vs {opp_id:<10} | Delta: ${res['cash_delta']:>+8.1f} | Cand Wins: {res['cand_wins']}/2 | Base Wins: {res['base_wins']}/2 | Cas: {res['casualties']} | Res: {res['rescues']}")

        total_legs = len(lad_matches) * 2
        total_cand_wins = sum(m["cand_wins"] for m in lad_matches)
        total_base_wins = sum(m["base_wins"] for m in lad_matches)
        cand_wr = (total_cand_wins / total_legs) * 100.0
        base_wr = (total_base_wins / total_legs) * 100.0
        mean_delta = float(np.mean([m["cash_delta"] for m in lad_matches]))
        median_delta = float(np.median([m["cash_delta"] for m in lad_matches]))
        total_cas = sum(m["casualties"] for m in lad_matches)
        total_res = sum(m["rescues"] for m in lad_matches)

        summary = {
            "ladder_name": lad_name,
            "total_matchups": len(lad_matches),
            "total_legs": total_legs,
            "candidate_win_rate": round(cand_wr, 1),
            "baseline_win_rate": round(base_wr, 1),
            "mean_cash_delta": round(mean_delta, 2),
            "median_cash_delta": round(median_delta, 2),
            "total_casualties": total_cas,
            "total_rescues": total_res,
        }
        tournament_results[lad_name] = summary

        print(f">> {lad_name} Summary:")
        print(f"   Win Rate: {cand_wr:.1f}% (Base: {base_wr:.1f}%) | Mean Delta: ${mean_delta:>+8.2f} (Med: ${median_delta:>+8.2f}) | Cas: {total_cas} | Res: {total_res}")

    out_file = os.path.join(REPO_ROOT, "research", "v44", "artifacts", "ladder_tournament_results.json")
    with open(out_file, "w") as f:
        json.dump(tournament_results, f, indent=2)
    print(f"\nTournament results saved to {out_file}")

    dur = time.perf_counter() - t0
    print(f"Tournament benchmark completed in {dur:.1f}s.")
    return tournament_results


if __name__ == "__main__":
    evaluate_v44_ladder()
