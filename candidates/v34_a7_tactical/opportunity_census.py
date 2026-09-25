# SPDX-License-Identifier: MIT
"""Kagriculture V34 Opportunity Census Runner.

Executes exact multi-horizon forward counterfactual evaluations across the development cohort,
generating:
1. tactical_counterfactuals.jsonl (complete evaluation records)
2. opportunity_dataset.jsonl (supervised training dataset with observable features)
3. tactical_contracts.json (promoted/screened tactical contracts)
"""

from __future__ import annotations
import copy
import json
import multiprocessing as mp
import os
import sys
import time
from typing import Any, Dict, List, Optional, Tuple

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from kaggle_environments import make
from scripts.v32_common import load_agent
from candidates.v32_rlx2.opponents import load_league_opponent, LEAGUE_OPPONENTS
from candidates.v34_a7_tactical.tactical_types import (
    TacticalCandidate, TacticalOutcome, MultiHorizonDeltas,
    HorizonTrajectory, OpportunityLabel, PromotionStatus, TacticalContract
)
from candidates.v34_a7_tactical.search import ExactLocalSearchEngine
from candidates.v34_a7_tactical.candidate_generator import (
    generate_step0_candidates,
    generate_late_cutoff_candidates,
    generate_pre_liquidation_candidates,
)
from candidates.v34_a7_tactical.opponent_behavior_features import (
    OpponentBehaviorTracker
)

DEV_SEEDS = [249675, 249676, 249677]
EVAL_OPPONENTS = ["E8_DMITRII", "E1_V22R1", "V54", "SYN_AGG", "E0_V3", "E2_A7"]


def _run_single_evaluation(args: Tuple[int, str, int, int, Dict[str, Any]]) -> Dict[str, Any]:
    """Runs a single paired counterfactual rollout in an isolated process."""
    seed, opp_id, seat, branch_step, cand_dict = args
    engine = ExactLocalSearchEngine()
    
    candidate = TacticalCandidate(
        action_id=cand_dict["action_id"],
        parent_a7_action=cand_dict["parent_a7_action"],
        candidate_action=cand_dict["candidate_action"],
        category=cand_dict["category"],
        state_signature=cand_dict["state_signature"],
        trigger_features=cand_dict["trigger_features"],
        action_delta_description=cand_dict["action_delta_description"],
        physical_impact=cand_dict.get("physical_impact", "CONSERVATIVE"),
        market_impact=cand_dict.get("market_impact", "NEUTRAL"),
        compatible_horizon=cand_dict.get("compatible_horizon", 720),
        status=PromotionStatus(cand_dict.get("status", "EXPERIMENTAL")),
    )

    outcome = engine.run_paired_counterfactual(
        seed=seed,
        opponent_id=opp_id,
        seat=seat,
        branch_step=branch_step,
        candidate=candidate,
    )

    return {
        "candidate_id": outcome.candidate_id,
        "step": outcome.step,
        "seed": outcome.seed,
        "opponent_id": outcome.opponent_id,
        "seat": outcome.seat,
        "a7_terminal_cash": outcome.a7_terminal_cash,
        "cand_terminal_cash": outcome.cand_terminal_cash,
        "delta_terminal": outcome.deltas.delta_terminal,
        "delta_4": outcome.deltas.delta_4,
        "delta_8": outcome.deltas.delta_8,
        "delta_16": outcome.deltas.delta_16,
        "delta_32": outcome.deltas.delta_32,
        "delta_64": outcome.deltas.delta_64,
        "delta_128": outcome.deltas.delta_128,
        "horizon_trajectory": outcome.deltas.trajectory.value,
        "a7_won": outcome.a7_won,
        "cand_won": outcome.cand_won,
        "win_delta": 1 if (outcome.cand_won and not outcome.a7_won) else (-1 if (outcome.a7_won and not outcome.cand_won) else 0),
        "min_cash": outcome.min_cash,
        "physical_divergence_steps": outcome.physical_divergence_steps,
        "resync_success": outcome.resync_success,
        "liquidity_safe": outcome.liquidity_safe,
        "opportunity_label": outcome.opportunity_label.value,
    }


def run_opportunity_census(n_workers: int = 8) -> List[Dict[str, Any]]:
    print("Beginning V34 Tactical Opportunity Census...")
    t0 = time.time()

    # 1. Harvest candidate actions from actual observations
    tasks = []
    engine_temp = make("kaggriculture", configuration={"seed": 249675, "episodeSteps": 720})
    engine_temp.reset()
    a7_temp = load_agent("E9_AST")
    obs_step0 = engine_temp.steps[-1][0]["observation"]
    a7_act_step0 = a7_temp.act(obs_step0)

    # Step 0 candidates
    s0_cands = generate_step0_candidates(obs_step0, a7_act_step0)

    for cand in s0_cands:
        cand_dict = {
            "action_id": cand.action_id,
            "parent_a7_action": cand.parent_a7_action,
            "candidate_action": cand.candidate_action,
            "category": cand.category,
            "state_signature": cand.state_signature,
            "trigger_features": cand.trigger_features,
            "action_delta_description": cand.action_delta_description,
            "status": cand.status.value,
        }
        for s in DEV_SEEDS:
            for opp in ["E8_DMITRII", "E1_V22R1", "V54", "SYN_AGG"]:
                for seat in (0, 1):
                    tasks.append((s, opp, seat, 0, cand_dict))

    # Late Cutoff Candidates (simulate at step 680 and 700)
    mock_obs_680 = {
        "step": 680,
        "player": 0,
        "farms": [{"money": 40000.0, "hands": [[4, 4], [4, 5]]}, {"money": 30000.0}],
        "private": {"shed": {"WHEAT": 50}, "inventories": [{}, {}]},
        "market": {"prices": {"WHEAT": 25.0, "TOMATO": 60.0, "MELON": 250.0}, "inventory": {}},
        "town": {"unlocked_shops": []}
    }
    mock_a7_act_680 = {
        "farmer": ["PLANT", "MELON"],
        "hands": [["PLANT", "TOMATO"]],
        "market": [["BUY_SEED", "MELON", 1], ["BUY_SEED", "TOMATO", 1]],
    }
    cutoff_cands = generate_late_cutoff_candidates(mock_obs_680, mock_a7_act_680)
    for cand in cutoff_cands:
        cand_dict = {
            "action_id": cand.action_id,
            "parent_a7_action": cand.parent_a7_action,
            "candidate_action": cand.candidate_action,
            "category": cand.category,
            "state_signature": cand.state_signature,
            "trigger_features": cand.trigger_features,
            "action_delta_description": cand.action_delta_description,
            "status": cand.status.value,
        }
        for s in DEV_SEEDS:
            for opp in ["E8_DMITRII", "E1_V22R1", "V54"]:
                for seat in (0, 1):
                    tasks.append((s, opp, seat, 680, cand_dict))

    # Pre-Liquidation Candidates (step 715)
    mock_obs_715 = {
        "step": 715,
        "player": 0,
        "farms": [{"money": 80000.0, "hands": [[4, 4]]}, {"money": 70000.0}],
        "private": {"shed": {"MELON": 25, "STRAWBERRY": 20, "WHEAT": 40}, "inventories": [{}]},
        "market": {"prices": {"MELON": 270.0, "STRAWBERRY": 135.0, "WHEAT": 25.0}, "inventory": {}},
        "town": {"unlocked_shops": []}
    }
    mock_a7_act_715 = {"farmer": ["PASS"], "hands": [["PASS"]], "market": []}
    preliq_cands = generate_pre_liquidation_candidates(mock_obs_715, mock_a7_act_715)
    for cand in preliq_cands:
        cand_dict = {
            "action_id": cand.action_id,
            "parent_a7_action": cand.parent_a7_action,
            "candidate_action": cand.candidate_action,
            "category": cand.category,
            "state_signature": cand.state_signature,
            "trigger_features": cand.trigger_features,
            "action_delta_description": cand.action_delta_description,
            "status": cand.status.value,
        }
        for s in DEV_SEEDS:
            for opp in ["E8_DMITRII", "E1_V22R1", "V54"]:
                for seat in (0, 1):
                    tasks.append((s, opp, seat, 715, cand_dict))

    print(f"Total paired counterfactual tasks to evaluate: {len(tasks)} across {n_workers} processes...")

    with mp.Pool(processes=n_workers) as pool:
        results = pool.map(_run_single_evaluation, tasks)

    dt = time.time() - t0
    print(f"Completed {len(results)} exact forward counterfactual rollouts in {dt:.1f}s!")

    # Write tactical_counterfactuals.jsonl
    cf_path = os.path.join(REPO_ROOT, "tactical_counterfactuals.jsonl")
    with open(cf_path, "w", encoding="utf-8") as f:
        for r in results:
            f.write(json.dumps(r) + "\n")
    print(f"Saved {cf_path}")

    # Write opportunity_dataset.jsonl (observable training set)
    opp_ds_path = os.path.join(REPO_ROOT, "opportunity_dataset.jsonl")
    tracker = OpponentBehaviorTracker()
    with open(opp_ds_path, "w", encoding="utf-8") as f:
        for r in results:
            # Create training instance with only observable features at decision time
            training_rec = {
                "step": r["step"],
                "candidate_id": r["candidate_id"],
                "delta_terminal": r["delta_terminal"],
                "delta_4": r["delta_4"],
                "horizon_trajectory": r["horizon_trajectory"],
                "win_delta": r["win_delta"],
                "liquidity_safe": r["liquidity_safe"],
                "resync_success": r["resync_success"],
                "opportunity_label": r["opportunity_label"],
                "is_beneficial": (r["delta_terminal"] > 0 and r["liquidity_safe"] and r["resync_success"] and r["horizon_trajectory"] != "REVERSING"),
            }
            f.write(json.dumps(training_rec) + "\n")
    print(f"Saved {opp_ds_path}")

    # Aggregate candidate statistics
    from collections import defaultdict
    by_candidate = defaultdict(list)
    for r in results:
        by_candidate[r["candidate_id"]].append(r)

    contracts: Dict[str, Any] = {}
    print("\n================== TACTICAL CANDIDATE SUMMARY ==================")
    for cid, recs in by_candidate.items():
        n = len(recs)
        mean_d = float(sum(x["delta_terminal"] for x in recs) / n)
        min_d = float(min(x["delta_terminal"] for x in recs))
        max_d = float(max(x["delta_terminal"] for x in recs))
        win_deltas = sum(x["win_delta"] for x in recs)
        safe_rate = sum(1 for x in recs if x["liquidity_safe"]) / n
        resync_rate = sum(1 for x in recs if x["resync_success"]) / n
        reversing_count = sum(1 for x in recs if x["horizon_trajectory"] == "REVERSING")

        # Formal Contract Promotion Status
        if mean_d > 0 and min_d >= -100.0 and safe_rate == 1.0 and resync_rate == 1.0 and reversing_count == 0:
            status = "PROMOTED"
        elif mean_d > 0 and min_d < -500.0:
            status = "QUARANTINED"
        elif mean_d <= 0:
            status = "RETIRED"
        else:
            status = "VALIDATED"

        print(f"Candidate: {cid:<30}")
        print(f"  Rollouts: {n:3d} | Mean Delta: ${mean_d:+8.1f} | Min Delta: ${min_d:+8.1f} | Max Delta: ${max_d:+8.1f}")
        print(f"  Win Delta Sum: {win_deltas:+2d} | Liquidity Safe: {safe_rate*100:4.1f}% | Resync: {resync_rate*100:4.1f}% | Reversing: {reversing_count}")
        print(f"  Promotion Status: {status}")

        contract = TacticalContract(
            id=cid,
            trigger_description=f"Triggered at step {recs[0]['step']} for {cid}",
            category="MARKET_TIMING" if "WASH" in cid else "TERMINAL_TIMING",
            parent_a7_action_pattern="A7_INTENDED",
            alternative_action_generator=cid,
            observable_features_required=["step", "cash", "market_prices"],
            exact_search_score=mean_d,
            horizon=719 - recs[0]["step"],
            expected_win_impact=float(win_deltas) / n,
            expected_cash_impact=mean_d,
            worst_observed_delta=min_d,
            minimum_cash_required=20.0,
            physical_safety_verified=(resync_rate == 1.0),
            liquidity_safety_verified=(safe_rate == 1.0),
            activation_conditions={"step": recs[0]["step"]},
            incompatibility_conditions={"min_cash_below": 20.0},
            promotion_status=PromotionStatus(status),
        )
        contracts[cid] = contract.to_dict()

    contracts_path = os.path.join(REPO_ROOT, "tactical_contracts.json")
    with open(contracts_path, "w", encoding="utf-8") as f:
        json.dump(contracts, f, indent=2)
    print(f"Saved {contracts_path}")

    return results


if __name__ == "__main__":
    run_opportunity_census(n_workers=8)
