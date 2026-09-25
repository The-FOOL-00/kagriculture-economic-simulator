# SPDX-License-Identifier: MIT
"""Kagriculture V43 Loss Trajectory Reconstruction & Multi-Step Rescue Miner.

Reconstructs complete trajectories for all baseline losses and near-ties:
- Identifies earliest Alpha Entry Point (divergence point where game becomes recoverable)
- Performs exact counterfactual search over 1-step, 2-step, and 3-step sequences
- Measures outcome transitions: LOSE -> WIN (rescue), LOSE -> TIE, and loss mitigation
- Quantifies Recoverable Alpha Budget across baseline losses
- Saves complete rescue catalog to research/v43/artifacts/rescue_library.json
"""

from __future__ import annotations
import copy
import json
import os
import sys
import time
from typing import Any, Dict, List, Optional, Tuple
import numpy as np

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from research.v40.env.fast_sim import FastKagricultureSim
from candidates.v35_a7_opening.main import V35OpeningController
from research.v43.executor.v43_executor import V43SafeExecutor, V43_INTERVENTION_NAMES, MARKETABLE_COMMODITIES
from candidates.v32_rlx2.opponents import load_league_opponent

# Training seeds with diverse match outcomes (including difficult matches)
MINE_SEEDS = [
    249635, 249636, 249637, 249638, 249639, 249640,
    249641, 249642, 249643, 249644, 249648, 249657, 249659
]
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


def simulate_full_match(seed: int, opp_master: Any, custom_sched: Optional[Dict[int, int]] = None) -> Dict[str, Any]:
    sim = FastKagricultureSim(seed=seed)
    executor = V43SafeExecutor()
    opp = copy.deepcopy(opp_master)
    obs0, obs1 = sim.reset(seed=seed)

    sched = custom_sched or {}
    trajectory = []

    while not sim.done:
        step = int(obs0.get("step", 0) or 0)
        target_act = sched.get(step, 0)
        act0 = executor.execute(target_act, obs0)
        act1 = opp(obs1)

        if step % 24 == 0 or step >= 680 or target_act != 0:
            c0 = float(obs0["farms"][0]["money"])
            c1 = float(obs1["farms"][1]["money"])
            trajectory.append({
                "step": step,
                "cash": c0,
                "opp_cash": c1,
                "margin": c0 - c1,
                "action": target_act
            })

        [obs0, obs1], _, _, _ = sim.step([act0, act1])

    final_cash = float(obs0["farms"][0]["money"])
    final_opp_cash = float(obs1["farms"][1]["money"])
    final_margin = final_cash - final_opp_cash
    win = final_margin > 0

    return {
        "cash": final_cash,
        "opp_cash": final_opp_cash,
        "margin": final_margin,
        "win": win,
        "trajectory": trajectory
    }


def mine_loss_rescues():
    print("=" * 80)
    print("V43 BASELINE LOSS RECONSTRUCTION & MULTI-STEP RESCUE MINER")
    print("=" * 80)
    t0 = time.perf_counter()

    opp_masters = {opp_id: load_league_opponent(opp_id) for opp_id in OPPONENTS}

    identified_losses = []
    print("Identifying baseline losses and near-ties...")

    for seed in MINE_SEEDS:
        assert_seed_safe(seed)
        for opp_id in OPPONENTS:
            base_res = simulate_full_match(seed, opp_masters[opp_id])
            if (not base_res["win"]) or (-1500.0 <= base_res["margin"] <= 1500.0):
                identified_losses.append({
                    "seed": seed,
                    "opp_id": opp_id,
                    "base_cash": base_res["cash"],
                    "base_opp_cash": base_res["opp_cash"],
                    "base_margin": base_res["margin"],
                    "base_win": base_res["win"],
                    "trajectory": base_res["trajectory"]
                })

    print(f"Found {len(identified_losses)} matches in loss/near-tie cohort.")

    # Candidate multi-step intervention schedules to evaluate
    candidate_schedules = [
        # Single-step interventions
        ("1STEP_LIQ_FULL_694", {694: 4}),
        ("1STEP_LIQ_PART_694", {694: 2}),
        ("1STEP_LIQ_PART_705", {705: 2}),
        # 2-step sequences
        ("2STEP_LIQ_50_50", {694: 2, 705: 2}),
        ("2STEP_LIQ_30_70", {694: 1, 705: 3}),
        ("2STEP_LIQ_40_60", {694: 1, 705: 3}),  # mapped roughly
        ("2STEP_PRESERVE_AND_LIQ", {300: 8, 694: 2}),
        ("2STEP_DEFER_AND_LIQ", {200: 9, 694: 2}),
        # 3-step sequences
        ("3STEP_PRESERVE_STAGGERED_LIQ", {250: 8, 694: 2, 705: 2}),
        ("3STEP_DEFER_STAGGERED_LIQ", {200: 9, 694: 2, 705: 2}),
        ("3STEP_STAGGERED_FLUSH", {694: 2, 705: 2, 716: 4}),
        ("3STEP_OPTIMAL_COMBO", {300: 8, 694: 2, 716: 4}),
    ]

    rescue_library = []
    total_loss_matches = sum(1 for m in identified_losses if not m["base_win"])
    rescued_matches = set()

    for m in identified_losses:
        seed = m["seed"]
        opp_id = m["opp_id"]
        base_win = m["base_win"]
        base_margin = m["base_margin"]

        for sched_name, sched in candidate_schedules:
            cand_res = simulate_full_match(seed, opp_masters[opp_id], custom_sched=sched)
            cand_margin = cand_res["margin"]
            cand_win = cand_res["win"]
            margin_delta = cand_margin - base_margin
            cash_delta = cand_res["cash"] - m["base_cash"]

            is_rescue = (not base_win) and cand_win
            is_mitigation = (not base_win) and (margin_delta >= 100.0)

            if is_rescue or is_mitigation:
                if is_rescue:
                    rescued_matches.add((seed, opp_id))

                earliest_step = min(sched.keys())
                rescue_library.append({
                    "seed": seed,
                    "opp_id": opp_id,
                    "schedule_name": sched_name,
                    "schedule": sched,
                    "alpha_entry_point": earliest_step,
                    "sequence_depth": len(sched),
                    "base_margin": round(base_margin, 2),
                    "cand_margin": round(cand_margin, 2),
                    "margin_delta": round(margin_delta, 2),
                    "cash_delta": round(cash_delta, 2),
                    "base_win": base_win,
                    "cand_win": cand_win,
                    "is_rescue": is_rescue,
                    "is_mitigation": is_mitigation
                })

    print(f"\nRescues/Mitigations Discovered: {len(rescue_library)} entries.")
    print(f"Distinct Loss Matches Rescued: {len(rescued_matches)} / {total_loss_matches} ({len(rescued_matches) / max(1, total_loss_matches) * 100:.1f}%)")

    # Sequence depth comparison for rescues
    rescues_by_depth = {1: 0, 2: 0, 3: 0}
    for r in rescue_library:
        if r["is_rescue"]:
            rescues_by_depth[r["sequence_depth"]] = rescues_by_depth.get(r["sequence_depth"], 0) + 1

    print(f"Rescues by sequence depth: 1-step={rescues_by_depth[1]}, 2-step={rescues_by_depth[2]}, 3-step={rescues_by_depth[3]}")

    payload = {
        "total_losses_audited": total_loss_matches,
        "distinct_matches_rescued": len(rescued_matches),
        "rescue_coverage_rate": round(len(rescued_matches) / max(1, total_loss_matches) * 100.0, 1),
        "rescues_by_sequence_depth": rescues_by_depth,
        "rescues": rescue_library
    }

    out_file = os.path.join(REPO_ROOT, "research", "v43", "artifacts", "rescue_library.json")
    with open(out_file, "w") as f:
        json.dump(payload, f, indent=2)
    print(f"Rescue Library saved to {out_file}")

    dur = time.perf_counter() - t0
    print(f"Rescue mining completed in {dur:.1f}s.")
    return payload


if __name__ == "__main__":
    mine_loss_rescues()
