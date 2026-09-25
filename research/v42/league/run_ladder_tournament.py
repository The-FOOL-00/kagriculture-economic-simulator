# SPDX-License-Identifier: MIT
"""Kagriculture V42 Full A/B Ladder Tournament Benchmark.

Evaluates the complete A/B Ladder on fresh, unseen DEV seeds:
- Ladder A: V35 Baseline (Live Incumbent)
- Ladder B: V39 Targeted Baseline (Step 694 full liquidation)
- Ladder C: V42-C Deterministic Library (Step 694 & 705 Partial Liquidation)
- Ladder D: V42-D Learned Two-Head Uncertainty-Gated Alpha Model
- Ladder E: V42-E Online Recurrent PPO Champion Policy

Across 4 distinct league opponents (E8_DMITRII, E2_A7, E0_V3, SYN_AGG) in both seat positions.
Strict Zero-Touch on protected holdout seed ranges.
"""

from __future__ import annotations
import copy
import json
import os
import sys
import time
from typing import Any, Callable, Dict, List, Tuple
import numpy as np
import torch

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from research.v40.env.fast_sim import FastKagricultureSim
from candidates.v35_a7_opening.main import V35OpeningController
from candidates.v39_live_targeted.main import V39TargetedController
from research.v42.executor.safe_executor import StateAwareExecutor, NUM_INTERVENTIONS
from research.v42.policy.observation import V42ObservationEncoder
from research.v42.policy.alpha_model import V42TwoHeadAlphaModel
from candidates.v32_rlx2.opponents import load_league_opponent

DEV_SEEDS = [249685, 249686, 249687, 249688]  # Fresh, unseen DEV seeds
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


def make_v42_c_agent():
    """Ladder C: V35 + Deterministic Partial Liquidation at Step 694 & 705."""
    executor = StateAwareExecutor(mode="v35")

    def _agent(obs, cfg=None):
        step = int(obs.get("step", 0) or 0)
        private = obs.get("private", {}) or {}
        shed = dict(private.get("shed", {}) or {})
        marketable = ("STRAWBERRY", "MILK", "WOOL", "MELON")

        # Step 694 partial liquidation
        if step in (693, 694) and any(shed.get(item, 0) >= 2 for item in marketable):
            return executor.execute(2, obs, cfg)

        # Step 705 secondary partial liquidation
        if step in (704, 705) and any(shed.get(item, 0) >= 2 for item in marketable):
            return executor.execute(2, obs, cfg)

        # Step >= 716 final flush
        if step >= 716 and any(shed.get(item, 0) > 0 for item in marketable):
            return executor.execute(1, obs, cfg)

        return executor.execute(0, obs, cfg)

    return _agent


def make_v42_learned_agent(ckpt_path: str, beta: float = 0.1, threshold: float = 10.0):
    """Ladder D & E: Two-Head Uncertainty-Gated Alpha Agent."""
    model = V42TwoHeadAlphaModel()
    model.load_state_dict(torch.load(ckpt_path, weights_only=False))
    model.eval()

    executor = StateAwareExecutor(mode="v35")
    encoder = V42ObservationEncoder()

    def _agent(obs, cfg=None):
        step = int(obs.get("step", 0) or 0)
        if step == 0:
            encoder.reset()
            executor.reset()

        mask = executor.get_safety_mask(obs, player=0)
        # In runtime tournament, mask out destructive actions
        for a in (3, 4, 5, 6, 7):
            mask[a] = False

        obs_vec = encoder.encode(obs, player=0)

        # Only evaluate learned interventions around active liquidation windows
        if (690 <= step <= 696) or (704 <= step <= 712) or (step >= 715):
            act, score, diag, _ = model.score_interventions(
                obs=obs_vec,
                mask=mask,
                beta=beta,
                threshold=threshold,
                rescue_weight=50.0
            )
        else:
            act = 0

        return executor.execute(act, obs, cfg)

    return _agent


def run_paired_tournament_match(
    cand_factory: Callable[[], Any],
    base_factory: Callable[[], Any],
    opp_master: Any,
    seed: int,
    opp_id: str
) -> Dict[str, Any]:
    """Runs paired 2-leg match between candidate and baseline vs opponent in both seats."""
    # Leg 1: Seat 0
    sim_c0 = FastKagricultureSim(seed=seed)
    cand_c0 = cand_factory()
    opp_c0 = copy.deepcopy(opp_master)
    oc0, oc1 = sim_c0.reset(seed=seed)
    while not sim_c0.done:
        [oc0, oc1], _, _, _ = sim_c0.step([cand_c0(oc0), opp_c0(oc1)])
    cand_cash_s0 = oc0["farms"][0]["money"]
    opp_cash_s0 = oc1["farms"][1]["money"]
    cand_win_s0 = cand_cash_s0 > opp_cash_s0

    sim_b0 = FastKagricultureSim(seed=seed)
    base_b0 = base_factory()
    opp_b0 = copy.deepcopy(opp_master)
    ob0, ob1 = sim_b0.reset(seed=seed)
    while not sim_b0.done:
        [ob0, ob1], _, _, _ = sim_b0.step([base_b0(ob0), opp_b0(ob1)])
    base_cash_s0 = ob0["farms"][0]["money"]
    base_win_s0 = base_cash_s0 > ob1["farms"][1]["money"]

    # Leg 2: Seat 1
    sim_c1 = FastKagricultureSim(seed=seed)
    cand_c1 = cand_factory()
    opp_c1 = copy.deepcopy(opp_master)
    oc0, oc1 = sim_c1.reset(seed=seed)
    while not sim_c1.done:
        [oc0, oc1], _, _, _ = sim_c1.step([opp_c1(oc0), cand_c1(oc1)])
    cand_cash_s1 = oc1["farms"][1]["money"]
    opp_cash_s1 = oc0["farms"][0]["money"]
    cand_win_s1 = cand_cash_s1 > opp_cash_s1

    sim_b1 = FastKagricultureSim(seed=seed)
    base_b1 = base_factory()
    opp_b1 = copy.deepcopy(opp_master)
    ob0, ob1 = sim_b1.reset(seed=seed)
    while not sim_b1.done:
        [ob0, ob1], _, _, _ = sim_b1.step([opp_b1(ob0), base_b1(ob1)])
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
        "opponent": opp_id,
        "cash_delta": cash_delta,
        "cand_wins": cand_wins,
        "base_wins": base_wins,
        "rescues": rescues,
        "casualties": casualties,
        "cand_cash_seat0": cand_cash_s0,
        "base_cash_seat0": base_cash_s0,
        "cand_cash_seat1": cand_cash_s1,
        "base_cash_seat1": base_cash_s1
    }


def evaluate_ladder():
    print("=" * 80)
    print("V42 COMPREHENSIVE A/B LADDER TOURNAMENT BENCHMARK")
    print("=" * 80)

    ckpt_alpha = os.path.join(REPO_ROOT, "research", "v42", "checkpoints", "v42_alpha_model.pt")
    ckpt_ppo = os.path.join(REPO_ROOT, "research", "v42", "checkpoints", "v42_ppo_champion.pt")

    ladders = {
        "Ladder C (V42-Det)": make_v42_c_agent,
        "Ladder D (V42-Alpha)": lambda: make_v42_learned_agent(ckpt_alpha, beta=0.1, threshold=10.0),
        "Ladder E (V42-PPO)": lambda: make_v42_learned_agent(ckpt_ppo, beta=0.1, threshold=10.0),
    }

    base_v35_factory = lambda: V35OpeningController()
    opp_masters = {opp_id: load_league_opponent(opp_id) for opp_id in OPPONENTS}

    tournament_results = {}

    for lad_name, cand_factory in ladders.items():
        print(f"\n--- Evaluating {lad_name} vs V35 Baseline ---")
        lad_matches = []
        t0 = time.perf_counter()

        for seed in DEV_SEEDS:
            assert_seed_safe(seed)
            for opp_id in OPPONENTS:
                res = run_paired_tournament_match(
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
        dur = time.perf_counter() - t0

        summary = {
            "ladder_name": lad_name,
            "total_matchups": len(lad_matches),
            "total_legs": total_legs,
            "candidate_win_rate": round(cand_wr, 1),
            "baseline_win_rate": round(base_wr, 1),
            "win_rate_delta": round(cand_wr - base_wr, 1),
            "mean_cash_delta": round(mean_delta, 2),
            "median_cash_delta": round(median_delta, 2),
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

    out_json = os.path.join(REPO_ROOT, "research", "v42", "artifacts", "ladder_tournament_results.json")
    with open(out_json, "w") as f:
        json.dump(tournament_results, f, indent=2, default=str)
    print(f"\nTournament results saved to {out_json}")

    return tournament_results


if __name__ == "__main__":
    evaluate_ladder()
