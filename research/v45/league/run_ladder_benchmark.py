# SPDX-License-Identifier: MIT
"""V45 Comprehensive Full A/B Ladder Tournament Benchmark.

Evaluates the complete lineage across 4 league opponents in both seat positions:
- Ladder A: V35 Baseline (Production Incumbent)
- Ladder B: V39 Live Targeted (Single-step 694 flush)
- Ladder C: V42 Alpha Residual (2-point staggered flush 694 & 705)
- Ladder D: V43 Compositional Alpha (3-point staggered flush 694, 705, 716)
- Ladder E: V44 Economic Portfolio (Payback cutoff + staggered flush)
- Ladder F: V45 Adversarial Market Candidate (Fail-closed market intelligence)

Outputs: research/v45/artifacts/final_ladder_results.json
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

from research.v45.governance import assert_seed_safe, assert_protected_artifacts
from research.v40.env.fast_sim import FastKagricultureSim
from candidates.v35_a7_opening.main import V35OpeningController
from candidates.v39_live_targeted.main import V39TargetedController
from candidates.v42_alpha_residual.main import V42CandidateController
from candidates.v43_compositional_alpha.main import V43CandidateController
from candidates.v44_economic_portfolio.main import V44CandidateController
from candidates.v45_adversarial_market.main import V45CandidateController
from candidates.v32_rlx2.opponents import load_league_opponent

TOURNAMENT_SEEDS = [
    249635, 249636, 249637, 249638,
    249645, 249646, 249647, 249648,
    249655, 249656, 249657, 249658,
    249685, 249686, 249687, 249688
]
OPPONENTS = ["E8_DMITRII", "E2_A7", "E0_V3", "SYN_AGG"]


def _act(agent: Any, obs: Dict[str, Any]) -> Dict[str, Any]:
    if hasattr(agent, "act") and callable(getattr(agent, "act")):
        return agent.act(obs)
    return agent(obs)


def run_ladder_benchmark():
    print("=" * 80)
    print("V45 FULL A/B LADDER TOURNAMENT BENCHMARK")
    print("=" * 80)
    assert_protected_artifacts()
    for s in TOURNAMENT_SEEDS:
        assert_seed_safe(s)

    ladders = {
        "Ladder A (V35 Baseline)": lambda: V35OpeningController(),
        "Ladder B (V39 Live Targeted)": lambda: V39TargetedController(),
        "Ladder C (V42 Alpha Residual)": lambda: V42CandidateController(),
        "Ladder D (V43 Compositional)": lambda: V43CandidateController(),
        "Ladder E (V44 Economic Portfolio)": lambda: V44CandidateController(),
        "Ladder F (V45 Adversarial Market)": lambda: V45CandidateController(),
    }

    opp_masters = {opp_id: load_league_opponent(opp_id) for opp_id in OPPONENTS}
    base_v35_factory = lambda: V35OpeningController()

    tournament_results = {}
    t0 = time.perf_counter()

    for lad_name, cand_factory in ladders.items():
        print(f"\n--- Evaluating {lad_name} vs V35 Baseline ---")
        lad_matches = []
        t_lad = time.perf_counter()

        for seed in TOURNAMENT_SEEDS:
            for opp_id in OPPONENTS:
                opp_master = opp_masters[opp_id]

                # Seat 0
                sim_c0 = FastKagricultureSim(seed=seed)
                cand_c0 = cand_factory()
                opp_c0 = copy.deepcopy(opp_master)
                oc0, oc1 = sim_c0.reset(seed=seed)
                while not sim_c0.done:
                    [oc0, oc1], _, _, _ = sim_c0.step([_act(cand_c0, oc0), opp_c0(oc1)])
                c_cash_s0 = float(oc0["farms"][0]["money"])
                o_cash_s0 = float(oc1["farms"][1]["money"])
                c_win_s0 = c_cash_s0 > o_cash_s0

                sim_b0 = FastKagricultureSim(seed=seed)
                base_b0 = base_v35_factory()
                opp_b0 = copy.deepcopy(opp_master)
                ob0, ob1 = sim_b0.reset(seed=seed)
                while not sim_b0.done:
                    [ob0, ob1], _, _, _ = sim_b0.step([_act(base_b0, ob0), opp_b0(ob1)])
                b_cash_s0 = float(ob0["farms"][0]["money"])
                b_opp_s0 = float(ob1["farms"][1]["money"])
                b_win_s0 = b_cash_s0 > b_opp_s0

                # Seat 1
                sim_c1 = FastKagricultureSim(seed=seed)
                cand_c1 = cand_factory()
                opp_c1 = copy.deepcopy(opp_master)
                oc0, oc1 = sim_c1.reset(seed=seed)
                while not sim_c1.done:
                    [oc0, oc1], _, _, _ = sim_c1.step([opp_c1(oc0), _act(cand_c1, oc1)])
                c_cash_s1 = float(oc1["farms"][1]["money"])
                o_cash_s1 = float(oc0["farms"][0]["money"])
                c_win_s1 = c_cash_s1 > o_cash_s1

                sim_b1 = FastKagricultureSim(seed=seed)
                base_b1 = base_v35_factory()
                opp_b1 = copy.deepcopy(opp_master)
                ob0, ob1 = sim_b1.reset(seed=seed)
                while not sim_b1.done:
                    [ob0, ob1], _, _, _ = sim_b1.step([opp_b1(ob0), _act(base_b1, ob1)])
                b_cash_s1 = float(ob1["farms"][1]["money"])
                b_opp_s1 = float(ob0["farms"][0]["money"])
                b_win_s1 = b_cash_s1 > b_opp_s1

                # Metrics for this seed x opp pair
                delta_s0 = c_cash_s0 - b_cash_s0
                delta_s1 = c_cash_s1 - b_cash_s1
                margin_delta_s0 = (c_cash_s0 - o_cash_s0) - (b_cash_s0 - b_opp_s0)
                margin_delta_s1 = (c_cash_s1 - o_cash_s1) - (b_cash_s1 - b_opp_s1)

                res = int(not b_win_s0 and c_win_s0) + int(not b_win_s1 and c_win_s1)
                cas = int(b_win_s0 and not c_win_s0) + int(b_win_s1 and not c_win_s1)

                lad_matches.append({
                    "seed": seed, "opp_id": opp_id,
                    "cand_wins": int(c_win_s0) + int(c_win_s1),
                    "base_wins": int(b_win_s0) + int(b_win_s1),
                    "cash_deltas": [delta_s0, delta_s1],
                    "margin_deltas": [margin_delta_s0, margin_delta_s1],
                    "rescues": res,
                    "casualties": cas,
                })

        total_legs = len(lad_matches) * 2
        cand_wins = sum(m["cand_wins"] for m in lad_matches)
        base_wins = sum(m["base_wins"] for m in lad_matches)
        all_cash_deltas = [d for m in lad_matches for d in m["cash_deltas"]]
        all_margin_deltas = [d for m in lad_matches for d in m["margin_deltas"]]
        total_rescues = sum(m["rescues"] for m in lad_matches)
        total_casualties = sum(m["casualties"] for m in lad_matches)

        summary = {
            "ladder": lad_name,
            "total_legs": total_legs,
            "candidate_wins": cand_wins,
            "candidate_win_rate_pct": round(cand_wins / total_legs * 100, 2),
            "baseline_win_rate_pct": round(base_wins / total_legs * 100, 2),
            "mean_cash_delta": round(float(np.mean(all_cash_deltas)), 2),
            "median_cash_delta": round(float(np.median(all_cash_deltas)), 2),
            "mean_margin_delta": round(float(np.mean(all_margin_deltas)), 2),
            "worst_cash_delta": round(float(np.min(all_cash_deltas)), 2),
            "p5_cash_delta": round(float(np.percentile(all_cash_deltas, 5)), 2),
            "total_rescues": total_rescues,
            "total_casualties": total_casualties,
        }
        tournament_results[lad_name] = summary
        dur_lad = time.perf_counter() - t_lad
        print(f"  Summary: Win Rate: {summary['candidate_win_rate_pct']}% | Mean Delta: ${summary['mean_cash_delta']:>+7.2f} (Med: ${summary['median_cash_delta']:>+7.2f}) | Margin Delta: ${summary['mean_margin_delta']:>+7.2f} | Res: {total_rescues} | Cas: {total_casualties} ({dur_lad:.1f}s)")

    dur = time.perf_counter() - t0
    out_file = os.path.join(REPO_ROOT, "research", "v45", "artifacts", "final_ladder_results.json")
    with open(out_file, "w") as f:
        json.dump(tournament_results, f, indent=2)

    print(f"\nFinal tournament results saved to {out_file} ({dur:.1f}s)")
    return tournament_results


if __name__ == "__main__":
    run_ladder_benchmark()
