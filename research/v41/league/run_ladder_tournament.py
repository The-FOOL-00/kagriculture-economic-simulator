# SPDX-License-Identifier: MIT
"""Kagriculture V41 Full A/B Ladder Tournament Benchmark.

Evaluates the complete A/B Ladder on fresh, unseen DEV seeds:
- Ladder A: V35 Baseline
- Ladder B: V39 Targeted Baseline
- Ladder C: V41-C Deterministic Safe Intervention Library
- Ladder D: V41-D Learned Offline Strategic Value Scorer
- Ladder E: V41-E Online Recurrent PPO Champion Policy

Across 4 distinct opponents (E8_DMITRII, E2_A7, E0_V3, SYN_AGG) in both seat positions.
Strict Zero-Touch on protected holdout seed ranges.
"""

from __future__ import annotations
import json
import os
import sys
import time
from typing import Any, Callable, Dict, List, Tuple
import numpy as np

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from candidates.v35_a7_opening.main import V35OpeningController
from candidates.v39_live_targeted.main import V39TargetedController
from research.v41.executor.safe_executor import StateAwareExecutor
from research.v41.league.evaluator import run_paired_matchup, make_v41_agent, assert_seed_safe

DEV_SEEDS = [249685, 249686, 249687, 249688]  # Fresh, unseen DEV seeds
OPPONENTS = ["E8_DMITRII", "E2_A7", "E0_V3", "SYN_AGG"]


def make_v41_c_agent():
    """Ladder C: V35 + Deterministic Safe Intervention Library."""
    executor = StateAwareExecutor(mode="v35")

    def _agent(obs, cfg=None):
        step = int(obs.get("step", 0) or 0)
        private = obs.get("private", {}) or {}
        shed = dict(private.get("shed", {}) or {})
        market = obs.get("market", {}) or {}
        prices = dict(market.get("prices", {}) or {})

        # Rule 1: Step 693-694 liquidation
        if step in (693, 694):
            return executor.execute(1, obs, cfg)

        # Rule 2: Endgame full flush
        if step >= 710:
            return executor.execute(2, obs, cfg)

        # Rule 3: Peak spot price milk/wool
        if float(prices.get("MILK", 0) or 0) >= 35.0 and shed.get("MILK", 0) >= 2:
            return executor.execute(3, obs, cfg)
        if float(prices.get("WOOL", 0) or 0) >= 38.0 and shed.get("WOOL", 0) >= 2:
            return executor.execute(4, obs, cfg)

        # Default: V35
        return executor.execute(0, obs, cfg)

    return _agent


def evaluate_ladder():
    print("================================================================================")
    print("                      V41 FULL A/B LADDER TOURNAMENT BENCHMARK                  ")
    print("================================================================================")

    ckpt_offline = os.path.join(REPO_ROOT, "research", "v41", "checkpoints", "v41_offline_model.pt")
    ckpt_ppo = os.path.join(REPO_ROOT, "research", "v41", "checkpoints", "v41_ppo_champion.pt")

    ladders = {
        "V41_C (Det. Library)": make_v41_c_agent,
        "V41_D (Offline Scorer)": lambda: make_v41_agent(ckpt_offline, confidence_threshold=30.0),
        "V41_E (Online PPO)": lambda: make_v41_agent(ckpt_ppo, confidence_threshold=30.0),
    }

    base_v35_factory = lambda: V35OpeningController()

    tournament_results = {}

    for lad_name, cand_factory in ladders.items():
        print(f"\n--- Evaluating {lad_name} vs V35 Baseline ---")
        lad_matches = []
        t0 = time.perf_counter()

        for seed in DEV_SEEDS:
            assert_seed_safe(seed)
            for opp_id in OPPONENTS:
                res = run_paired_matchup(
                    candidate_fn_factory=cand_factory,
                    baseline_fn_factory=base_v35_factory,
                    opponent_id=opp_id,
                    seed=seed
                )
                lad_matches.append(res)
                print(f"  Seed {seed} vs {opp_id:<10} | Delta: ${res['cash_delta']:>+8.1f} | Cand Wins: {res['cand_wins']}/2 | Base Wins: {res['base_wins']}/2 | Cas: {res['casualties']} | Res: {res['rescues']}")

        total_legs = len(lad_matches) * 2  # 2 candidate legs per matchup
        total_cand_wins = sum(m["cand_wins"] for m in lad_matches)
        total_base_wins = sum(m["base_wins"] for m in lad_matches)
        cand_wr = total_cand_wins / total_legs * 100
        base_wr = total_base_wins / total_legs * 100
        mean_delta = np.mean([m["cash_delta"] for m in lad_matches])
        median_delta = np.median([m["cash_delta"] for m in lad_matches])
        total_cas = sum(m["casualties"] for m in lad_matches)
        total_res = sum(m["rescues"] for m in lad_matches)
        dur = time.perf_counter() - t0

        summary = {
            "ladder_name": lad_name,
            "total_matchups": len(lad_matches),
            "total_legs": total_legs,
            "candidate_win_rate": round(cand_wr, 1),
            "baseline_win_rate": round(base_wr, 1),
            "win_rate_delta": round(cand_wr - base_wr, 1),
            "mean_cash_delta": round(float(mean_delta), 2),
            "median_cash_delta": round(float(median_delta), 2),
            "total_casualties": total_cas,
            "total_rescues": total_res,
            "duration_seconds": round(dur, 1),
            "match_details": lad_matches
        }
        tournament_results[lad_name] = summary

        print(f"\n>> {lad_name} Summary:")
        print(f"   Win Rate: {cand_wr:.1f}% (Base: {base_wr:.1f}%, Delta: {cand_wr - base_wr:+.1f}%)")
        print(f"   Mean Cash Delta: ${mean_delta:>+8.2f} (Median: ${median_delta:>+8.2f})")
        print(f"   Casualties: {total_cas} | Rescues: {total_res}")

    # Save detailed JSON artifact
    out_json = os.path.join(REPO_ROOT, "research", "v41", "artifacts", "ladder_tournament_results.json")
    with open(out_json, "w") as f:
        # Convert non-serializable elements
        json.dump(tournament_results, f, indent=2, default=str)
    print(f"\nTournament results saved to {out_json}")

    return tournament_results


if __name__ == "__main__":
    evaluate_ladder()
