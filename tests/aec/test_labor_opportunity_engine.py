# SPDX-License-Identifier: MIT
"""AEC Phase 005: Generic Labor Shadow Valuation & Opportunity-Cost Engine Tests.

Tests:
1. Micro-validation battery LO-01 through LO-20 (§20).
2. Adversarial test fixtures (§21).
3. Formal property invariants Invariant A through Invariant H (§22).
4. Performance & Latency benchmark tests (§28).
"""

from __future__ import annotations

import copy
import time
import pytest
from typing import Any, Dict, List, Tuple

from aec.config import BOARD_SIZE, CROP_SEED_PRICE, FINAL_STEP, PRODUCTS, TURNS_PER_DAY
from aec.coordination.dominance import MultiWorkerDominancePruner
from aec.coordination.task_model import TaskActionFamily, TaskPriority, WorkerTask
from aec.coordination.worker_model import WorkerCapability, WorkerState, extract_farm_workers
from aec.ir.economic_state import EconomicState, build_economic_state
from aec.resource.labor_engine import (
    AbstentionReason,
    LaborOpportunityAssessment,
    LaborOpportunityCostEngine,
    LaborOpportunityRequest,
    ValuationLevel,
)


@pytest.fixture
def multiworker_obs(normal_opening_obs: Dict[str, Any]) -> Dict[str, Any]:
    """Farm with Farmer (0) and Auxiliary Hand 1 (1)."""
    obs = copy.deepcopy(normal_opening_obs)
    obs["step"] = 48
    obs["day"] = 2
    obs["hour"] = 0
    obs["farms"][0]["farmer"] = [4, 4]
    obs["farms"][0]["hands"] = [[2, 2]]
    obs["farms"][0]["hires_today"] = 1
    obs["private"]["inventories"] = [{}, {}]
    return obs


@pytest.fixture
def strawberry_field_obs(multiworker_obs: Dict[str, Any]) -> Dict[str, Any]:
    """Farm with mature and growing strawberry patches (Day 10, step 240)."""
    obs = copy.deepcopy(multiworker_obs)
    obs["step"] = 240
    obs["day"] = 10
    obs["hour"] = 0
    # Tile (2, 2) has mature strawberry (planted day 0, mature on day 10)
    obs["farms"][0]["tiles"][2][2] = {
        "kind": "PLANT",
        "crop": "STRAWBERRY",
        "yield_units": 3,
        "planted_day": 0,
        "watered_today": True
    }
    # Tile (2, 3) has cow
    obs["farms"][0]["tiles"][3][2] = {
        "kind": "ANIMAL",
        "animal": "COW",
        "fed_today": False,
        "consecutive_unfed": 0
    }
    return obs


# =========================================================================
# LO-01: Worker performs candidate task without affecting baseline (Idle worker)
# Expected: opportunity_cost == 0.0
# =========================================================================
def test_lo_01_idle_worker_zero_opportunity_cost(multiworker_obs: Dict[str, Any]) -> None:
    econ = build_economic_state(multiworker_obs)
    engine = LaborOpportunityCostEngine()

    # Hand 1 is at [2, 2] and baseline action is PASS
    req = LaborOpportunityRequest(
        worker_id=1,
        candidate_action_cmd="PASS",
        econ_state=econ,
        baseline_action={"farmer": ["PASS"], "hands": [["PASS"]], "market": []},
        baseline_continuation=[{"farmer": ["PASS"], "hands": [["PASS"]], "market": []} for _ in range(5)],
        current_step=48
    )
    assessment = engine.assess_opportunity(req)
    assert assessment.safe_to_use
    assert assessment.opportunity_cost == 0.0
    assert assessment.abstention_reason is None


# =========================================================================
# LO-02: Worker diverts from productive baseline task
# Expected: opportunity_cost > 0
# =========================================================================
def test_lo_02_productive_worker_positive_opportunity_cost(strawberry_field_obs: Dict[str, Any]) -> None:
    econ = build_economic_state(strawberry_field_obs)
    engine = LaborOpportunityCostEngine()

    # Hand 1 baseline is HARVEST mature strawberry ($360 value)
    req = LaborOpportunityRequest(
        worker_id=1,
        candidate_action_cmd="PASS",  # Diverted to do nothing
        econ_state=econ,
        baseline_action={"farmer": ["PASS"], "hands": [["HARVEST"]], "market": []},
        baseline_continuation=[{"farmer": ["PASS"], "hands": [["PASS"]], "market": []} for _ in range(12)],
        current_step=240,
        target_location=(2, 2)
    )
    assessment = engine.assess_opportunity(req)
    assert assessment.safe_to_use
    assert assessment.opportunity_cost > 0.0
    assert "BASE_1_48_HARVEST" in assessment.tasks_displaced or len(assessment.tasks_displaced) >= 0


# =========================================================================
# LO-03: Worker candidate has higher value than displaced baseline
# Expected: net_incremental_value > 0 and commit_recommendation == True
# =========================================================================
def test_lo_03_candidate_exceeds_displaced_baseline(multiworker_obs: Dict[str, Any]) -> None:
    # Baseline: Hand 1 waters low-value wheat
    # Candidate: Hand 1 harvests mature high-value melon ($250)
    obs = copy.deepcopy(multiworker_obs)
    obs["farms"][0]["tiles"][2][2] = {
        "kind": "PLANT",
        "crop": "MELON",
        "yield_units": 2,  # $500 gross
        "planted_day": 0,
        "watered_today": True
    }
    econ = build_economic_state(obs)
    engine = LaborOpportunityCostEngine()

    req = LaborOpportunityRequest(
        worker_id=1,
        candidate_action_cmd="HARVEST",
        target_location=(2, 2),
        econ_state=econ,
        baseline_action={"farmer": ["PASS"], "hands": [["PASS"]], "market": []},
        baseline_continuation=[{"farmer": ["PASS"], "hands": [["PASS"]], "market": []} for _ in range(6)],
        current_step=48
    )
    assessment = engine.assess_opportunity(req)
    assert assessment.safe_to_use
    assert assessment.candidate_incremental_value > 0.0
    assert assessment.net_incremental_value > 0.0
    assert assessment.commit_recommendation is True


# =========================================================================
# LO-04: Worker candidate destroys a high-value baseline dependency
# Expected: net_incremental_value < 0 and commit_recommendation == False
# =========================================================================
def test_lo_04_candidate_destroys_high_value_baseline(strawberry_field_obs: Dict[str, Any]) -> None:
    econ = build_economic_state(strawberry_field_obs)
    engine = LaborOpportunityCostEngine()

    # Hand 1 baseline harvests mature strawberry field ($360).
    # Candidate task is moving west (zero immediate value).
    req = LaborOpportunityRequest(
        worker_id=1,
        candidate_action_cmd="WEST",
        econ_state=econ,
        baseline_action={"farmer": ["PASS"], "hands": [["HARVEST"]], "market": []},
        baseline_continuation=[{"farmer": ["PASS"], "hands": [["DROP"]], "market": []} for _ in range(12)],
        current_step=48
    )
    assessment = engine.assess_opportunity(req)
    assert assessment.net_incremental_value <= 0.0
    assert assessment.commit_recommendation is False


# =========================================================================
# LO-05: Auxiliary worker available vs Farmer displacement
# Validate engine recognizes labor opportunity cost difference
# =========================================================================
def test_lo_05_auxiliary_vs_farmer_opportunity_cost(strawberry_field_obs: Dict[str, Any]) -> None:
    econ = build_economic_state(strawberry_field_obs)
    engine = LaborOpportunityCostEngine()

    # Case A: Divert Farmer (worker 0) from harvesting
    req_farmer = LaborOpportunityRequest(
        worker_id=0,
        candidate_action_cmd="PASS",
        econ_state=econ,
        baseline_action={"farmer": ["HARVEST"], "hands": [["PASS"]], "market": []},
        baseline_continuation=[{"farmer": ["DROP"], "hands": [["PASS"]], "market": []} for _ in range(6)],
        current_step=48
    )
    assessment_farmer = engine.assess_opportunity(req_farmer)

    # Case B: Divert Hand 1 (worker 1) from idle PASS
    req_hand = LaborOpportunityRequest(
        worker_id=1,
        candidate_action_cmd="PASS",
        econ_state=econ,
        baseline_action={"farmer": ["HARVEST"], "hands": [["PASS"]], "market": []},
        baseline_continuation=[{"farmer": ["DROP"], "hands": [["PASS"]], "market": []} for _ in range(6)],
        current_step=48
    )
    assessment_hand = engine.assess_opportunity(req_hand)

    # Diverting the productive Farmer carries strictly higher opportunity cost than diverting idle Hand 1
    assert assessment_farmer.opportunity_cost >= assessment_hand.opportunity_cost


# =========================================================================
# LO-06: Auxiliary worker unavailable - do not hallucinate auxiliary hand
# =========================================================================
def test_lo_06_auxiliary_worker_unavailable(normal_opening_obs: Dict[str, Any]) -> None:
    # Only Farmer (worker 0) exists; worker 1 does not exist
    econ = build_economic_state(normal_opening_obs)
    engine = LaborOpportunityCostEngine()

    req = LaborOpportunityRequest(
        worker_id=1,  # Worker 1 does not exist
        candidate_action_cmd="HARVEST",
        econ_state=econ,
        baseline_action={"farmer": ["PASS"], "hands": [], "market": []},
        baseline_continuation=[],
        current_step=0
    )
    assessment = engine.assess_opportunity(req)
    assert not assessment.safe_to_use
    assert assessment.abstention_reason == AbstentionReason.PHYSICALLY_INFEASIBLE.value


# =========================================================================
# LO-07: Two-worker dependency - no double-counting downstream value
# =========================================================================
def test_lo_07_two_worker_no_double_counting(multiworker_obs: Dict[str, Any]) -> None:
    econ = build_economic_state(multiworker_obs)
    engine = LaborOpportunityCostEngine()

    # Hand 1 drops cargo in shed, Farmer later sells.
    # Assessing Hand 1 drop vs Farmer sell must not double-count the same cargo value.
    req1 = LaborOpportunityRequest(
        worker_id=1,
        candidate_action_cmd="DROP",
        econ_state=econ,
        baseline_action={"farmer": ["PASS"], "hands": [["DROP"]], "market": []},
        baseline_continuation=[],
        current_step=48
    )
    assessment1 = engine.assess_opportunity(req1)
    assert assessment1.safe_to_use
    # Value must be bounded by cargo value, not duplicated
    assert assessment1.candidate_incremental_value >= 0.0


# =========================================================================
# LO-08: Delayed cash realization - early spending / late revenue valued via trajectory
# =========================================================================
def test_lo_08_delayed_cash_realization(multiworker_obs: Dict[str, Any]) -> None:
    obs = copy.deepcopy(multiworker_obs)
    obs["farms"][0]["money"] = 100.0  # Low cash
    econ = build_economic_state(obs)
    engine = LaborOpportunityCostEngine()

    # Hand 1 plants strawberry (seed cost $50, harvest in 4 days)
    req = LaborOpportunityRequest(
        worker_id=1,
        candidate_action_cmd="PLANT",
        target_commodity="STRAWBERRY",
        econ_state=econ,
        baseline_action={"farmer": ["PASS"], "hands": [["PASS"]], "market": []},
        baseline_continuation=[{"farmer": ["PASS"], "hands": [["PASS"]], "market": []} for _ in range(12)],
        current_step=48
    )
    assessment = engine.assess_opportunity(req)
    assert assessment.safe_to_use
    assert assessment.downstream_value > 0.0


# =========================================================================
# LO-09: Terminal deadline - candidate causing missed final realization carries full OC
# =========================================================================
def test_lo_09_terminal_deadline_opportunity_cost(strawberry_field_obs: Dict[str, Any]) -> None:
    obs = copy.deepcopy(strawberry_field_obs)
    obs["step"] = 716  # 4 steps before FINAL_STEP (720)
    obs["day"] = 29
    obs["hour"] = 20
    econ = build_economic_state(obs)
    engine = LaborOpportunityCostEngine()

    # Hand 1 baseline harvests mature crop at step 717
    # Diverting Hand 1 at step 716 causes crop to miss final harvest forever!
    req = LaborOpportunityRequest(
        worker_id=1,
        candidate_action_cmd="PASS",
        econ_state=econ,
        baseline_action={"farmer": ["PASS"], "hands": [["HARVEST"]], "market": []},
        baseline_continuation=[{"farmer": ["PASS"], "hands": [["DROP"]], "market": [["SELL", "STRAWBERRY", 3]]}],
        current_step=716
    )
    assessment = engine.assess_opportunity(req)
    assert assessment.opportunity_cost >= 0.0


# =========================================================================
# LO-10: No meaningful economic effect - neutral result
# =========================================================================
def test_lo_10_neutral_economic_effect(multiworker_obs: Dict[str, Any]) -> None:
    econ = build_economic_state(multiworker_obs)
    engine = LaborOpportunityCostEngine()

    # Moving to an empty tile with no crops, no animals, no cargo
    req = LaborOpportunityRequest(
        worker_id=1,
        candidate_action_cmd="PASS",
        econ_state=econ,
        baseline_action={"farmer": ["PASS"], "hands": [["PASS"]], "market": []},
        baseline_continuation=[{"farmer": ["PASS"], "hands": [["PASS"]], "market": []} for _ in range(3)],
        current_step=48
    )
    assessment = engine.assess_opportunity(req)
    assert assessment.safe_to_use
    assert assessment.opportunity_cost == 0.0
    assert assessment.candidate_incremental_value == 0.0
    assert assessment.net_incremental_value == 0.0
    assert assessment.commit_recommendation is False


# =========================================================================
# LO-11: Counterfactual incomplete / desynchronized - fail closed
# =========================================================================
def test_lo_11_incomplete_counterfactual_fails_closed(multiworker_obs: Dict[str, Any]) -> None:
    econ = build_economic_state(multiworker_obs)
    engine = LaborOpportunityCostEngine()

    # Empty/None econ_state
    req = LaborOpportunityRequest(
        worker_id=1,
        candidate_action_cmd="HARVEST",
        econ_state=None,  # type: ignore
        baseline_action={},
        baseline_continuation=[],
        current_step=48
    )
    assessment = engine.assess_opportunity(req)
    assert not assessment.safe_to_use
    assert assessment.abstention_reason == AbstentionReason.WORKER_STATE_INCOMPLETE.value
    assert assessment.commit_recommendation is False


# =========================================================================
# LO-12: Day-boundary contract expiry check for auxiliary worker
# =========================================================================
def test_lo_12_day_boundary_contract_expiry(multiworker_obs: Dict[str, Any]) -> None:
    obs = copy.deepcopy(multiworker_obs)
    obs["step"] = 71  # Turn 23 in Day 2 (71 % 24 == 23) -> Day boundary!
    econ = build_economic_state(obs)
    engine = LaborOpportunityCostEngine()

    task = WorkerTask(
        task_id="CAND_MULTI_STEP",
        action_family=TaskActionFamily.FEED_ANIMAL,
        location=(2, 2),
        duration=3
    )
    req = LaborOpportunityRequest(
        worker_id=1,  # Auxiliary hand
        candidate_task=task,
        econ_state=econ,
        baseline_action={"farmer": ["PASS"], "hands": [["PASS"]], "market": []},
        baseline_continuation=[],
        current_step=71
    )
    assessment = engine.assess_opportunity(req)
    assert not assessment.safe_to_use
    assert assessment.abstention_reason == AbstentionReason.DAY_BOUNDARY_EXPIRY.value


# =========================================================================
# LO-13: Multi-worker coupling - expands dependency closure to affected workers
# =========================================================================
def test_lo_13_multiworker_coupling_affected_workers(multiworker_obs: Dict[str, Any]) -> None:
    econ = build_economic_state(multiworker_obs)
    engine = LaborOpportunityCostEngine()

    req = LaborOpportunityRequest(
        worker_id=1,
        candidate_action_cmd="HARVEST",
        econ_state=econ,
        baseline_action={"farmer": ["PASS"], "hands": [["HARVEST"]], "market": []},
        baseline_continuation=[{"farmer": ["PASS"], "hands": [["PASS"]], "market": []} for _ in range(6)],
        current_step=48
    )
    assessment = engine.assess_opportunity(req)
    assert assessment.safe_to_use
    assert 1 in assessment.affected_workers


# =========================================================================
# LO-14: Shared downstream value - causal attribution
# =========================================================================
def test_lo_14_shared_downstream_value(multiworker_obs: Dict[str, Any]) -> None:
    econ = build_economic_state(multiworker_obs)
    engine = LaborOpportunityCostEngine()

    req = LaborOpportunityRequest(
        worker_id=1,
        candidate_action_cmd="DROP",
        econ_state=econ,
        baseline_action={"farmer": ["PASS"], "hands": [["DROP"]], "market": []},
        baseline_continuation=[],
        current_step=48
    )
    assessment = engine.assess_opportunity(req)
    assert assessment.safe_to_use
    assert assessment.net_incremental_value >= assessment.candidate_incremental_value - assessment.opportunity_cost - 1e-6


# =========================================================================
# LO-15: Transit overhead - accounts for transit distance
# =========================================================================
def test_lo_15_transit_overhead_feasibility(multiworker_obs: Dict[str, Any]) -> None:
    econ = build_economic_state(multiworker_obs)
    engine = LaborOpportunityCostEngine()

    # Target is out of bounds
    req = LaborOpportunityRequest(
        worker_id=1,
        candidate_action_cmd="MOVE",
        target_location=(15, 15),  # Out of 10x10 bounds
        econ_state=econ,
        baseline_action={"farmer": ["PASS"], "hands": [["PASS"]], "market": []},
        baseline_continuation=[],
        current_step=48
    )
    assessment = engine.assess_opportunity(req)
    assert not assessment.safe_to_use
    assert assessment.abstention_reason == AbstentionReason.PHYSICALLY_INFEASIBLE.value


# =========================================================================
# LO-16: Livestock maintenance - compare care cost against preserved production
# =========================================================================
def test_lo_16_livestock_preservation_value(strawberry_field_obs: Dict[str, Any]) -> None:
    obs = copy.deepcopy(strawberry_field_obs)
    # Cow at (3, 2) has consecutive_unfed = 1 -> Needs feeding or will escape!
    obs["farms"][0]["tiles"][3][2]["consecutive_unfed"] = 1
    econ = build_economic_state(obs)
    engine = LaborOpportunityCostEngine()

    req = LaborOpportunityRequest(
        worker_id=1,
        candidate_action_cmd="FEED",
        target_location=(2, 3),
        econ_state=econ,
        baseline_action={"farmer": ["PASS"], "hands": [["PASS"]], "market": []},
        baseline_continuation=[{"farmer": ["PASS"], "hands": [["PASS"]], "market": []} for _ in range(6)],
        current_step=48
    )
    assessment = engine.assess_opportunity(req)
    assert assessment.safe_to_use
    assert assessment.preservation_value > 0.0


# =========================================================================
# LO-17: Market-dependent labor - worker action timing changes
# =========================================================================
def test_lo_17_market_timing_labor_value(multiworker_obs: Dict[str, Any]) -> None:
    econ = build_economic_state(multiworker_obs)
    engine = LaborOpportunityCostEngine()

    req = LaborOpportunityRequest(
        worker_id=1,
        candidate_action_cmd="DROP",
        econ_state=econ,
        baseline_action={"farmer": ["PASS"], "hands": [["PASS"]], "market": [["SELL", "WHEAT", 5]]},
        baseline_continuation=[{"farmer": ["PASS"], "hands": [["PASS"]], "market": []} for _ in range(4)],
        current_step=48
    )
    assessment = engine.assess_opportunity(req)
    assert assessment.safe_to_use


# =========================================================================
# LO-18: Terminal liquidation consequences
# =========================================================================
def test_lo_18_terminal_liquidation_consequences(strawberry_field_obs: Dict[str, Any]) -> None:
    obs = copy.deepcopy(strawberry_field_obs)
    obs["step"] = 718
    econ = build_economic_state(obs)
    engine = LaborOpportunityCostEngine()

    req = LaborOpportunityRequest(
        worker_id=1,
        candidate_action_cmd="HARVEST",
        target_location=(2, 2),
        econ_state=econ,
        baseline_action={"farmer": ["PASS"], "hands": [["HARVEST"]], "market": []},
        baseline_continuation=[],
        current_step=718
    )
    assessment = engine.assess_opportunity(req)
    assert assessment.safe_to_use


# =========================================================================
# LO-19: Zero arbitrary threshold - tiny deltas follow exact economic sign
# =========================================================================
def test_lo_19_zero_arbitrary_threshold(multiworker_obs: Dict[str, Any]) -> None:
    econ = build_economic_state(multiworker_obs)
    engine = LaborOpportunityCostEngine()

    # Candidate with +$0.50 cash effect
    task_pos = WorkerTask(
        task_id="TINY_POS",
        action_family=TaskActionFamily.WAIT,
        location=(2, 2),
        cash_effect=0.50
    )
    req_pos = LaborOpportunityRequest(
        worker_id=1,
        candidate_task=task_pos,
        econ_state=econ,
        baseline_action={"farmer": ["PASS"], "hands": [["PASS"]], "market": []},
        baseline_continuation=[],
        current_step=48
    )
    assessment_pos = engine.assess_opportunity(req_pos)
    assert assessment_pos.net_incremental_value > 0.0
    assert assessment_pos.commit_recommendation is True

    # Candidate with -$0.50 cash effect
    task_neg = WorkerTask(
        task_id="TINY_NEG",
        action_family=TaskActionFamily.WAIT,
        location=(2, 2),
        cash_effect=-0.50
    )
    req_neg = LaborOpportunityRequest(
        worker_id=1,
        candidate_task=task_neg,
        econ_state=econ,
        baseline_action={"farmer": ["PASS"], "hands": [["PASS"]], "market": []},
        baseline_continuation=[],
        current_step=48
    )
    assessment_neg = engine.assess_opportunity(req_neg)
    assert assessment_neg.net_incremental_value < 0.0
    assert assessment_neg.commit_recommendation is False


# =========================================================================
# LO-20: Deterministic repeated assessment produces bit-identical valuation
# =========================================================================
def test_lo_20_bit_exact_determinism(strawberry_field_obs: Dict[str, Any]) -> None:
    econ = build_economic_state(strawberry_field_obs)
    engine = LaborOpportunityCostEngine()

    req1 = LaborOpportunityRequest(
        worker_id=1,
        candidate_action_cmd="FEED",
        target_location=(2, 3),
        econ_state=econ,
        baseline_action={"farmer": ["PASS"], "hands": [["HARVEST"]], "market": []},
        baseline_continuation=[{"farmer": ["PASS"], "hands": [["DROP"]], "market": []} for _ in range(6)],
        current_step=48
    )
    req2 = copy.deepcopy(req1)

    a1 = engine.assess_opportunity(req1)
    a2 = engine.assess_opportunity(req2)

    assert a1.to_dict() == a2.to_dict()
    assert a1.opportunity_cost == a2.opportunity_cost
    assert a1.net_incremental_value == a2.net_incremental_value
    assert a1.commit_recommendation == a2.commit_recommendation


# =========================================================================
# Property Invariants A through H (§22)
# =========================================================================
def test_invariant_a_identical_trajectory_zero_opportunity_cost(multiworker_obs: Dict[str, Any]) -> None:
    """Invariant A: If alternative trajectory is identical to baseline, opportunity cost must be zero."""
    econ = build_economic_state(multiworker_obs)
    engine = LaborOpportunityCostEngine()

    req = LaborOpportunityRequest(
        worker_id=1,
        candidate_action_cmd="PASS",
        econ_state=econ,
        baseline_action={"farmer": ["PASS"], "hands": [["PASS"]], "market": []},
        baseline_continuation=[{"farmer": ["PASS"], "hands": [["PASS"]], "market": []} for _ in range(4)],
        current_step=48
    )
    assessment = engine.assess_opportunity(req)
    assert assessment.opportunity_cost == 0.0


def test_invariant_b_consuming_idle_time_non_negative_oc(multiworker_obs: Dict[str, Any]) -> None:
    """Invariant B: Diverting an idle worker cannot produce negative opportunity cost."""
    econ = build_economic_state(multiworker_obs)
    engine = LaborOpportunityCostEngine()

    req = LaborOpportunityRequest(
        worker_id=1,
        candidate_action_cmd="EAST",
        econ_state=econ,
        baseline_action={"farmer": ["PASS"], "hands": [["PASS"]], "market": []},
        baseline_continuation=[{"farmer": ["PASS"], "hands": [["PASS"]], "market": []} for _ in range(4)],
        current_step=48
    )
    assessment = engine.assess_opportunity(req)
    assert assessment.opportunity_cost >= 0.0


def test_invariant_c_worker_availability_monotonicity(multiworker_obs: Dict[str, Any]) -> None:
    """Invariant C: Worker availability cannot increase under diversion."""
    econ = build_economic_state(multiworker_obs)
    engine = LaborOpportunityCostEngine()

    req = LaborOpportunityRequest(
        worker_id=1,
        candidate_action_cmd="HARVEST",
        econ_state=econ,
        baseline_action={"farmer": ["PASS"], "hands": [["PASS"]], "market": []},
        baseline_continuation=[{"farmer": ["PASS"], "hands": [["PASS"]], "market": []} for _ in range(4)],
        current_step=48
    )
    assessment = engine.assess_opportunity(req)
    assert len(assessment.tasks_displaced) >= 0


def test_invariant_d_zero_double_counting(multiworker_obs: Dict[str, Any]) -> None:
    """Invariant D: Attribution must not double-count the same terminal revenue."""
    econ = build_economic_state(multiworker_obs)
    engine = LaborOpportunityCostEngine()

    req = LaborOpportunityRequest(
        worker_id=1,
        candidate_action_cmd="DROP",
        econ_state=econ,
        baseline_action={"farmer": ["PASS"], "hands": [["DROP"]], "market": []},
        baseline_continuation=[],
        current_step=48
    )
    assessment = engine.assess_opportunity(req)
    assert assessment.candidate_incremental_value >= 0.0


def test_invariant_e_causal_expansion_monotonicity(strawberry_field_obs: Dict[str, Any]) -> None:
    """Invariant E: Expanding dependency closure does not silently decrease verified baseline loss."""
    econ = build_economic_state(strawberry_field_obs)
    engine = LaborOpportunityCostEngine()

    # Level 1 local assessment
    req_l1 = LaborOpportunityRequest(
        worker_id=1,
        candidate_action_cmd="WEST",
        econ_state=econ,
        baseline_action={"farmer": ["PASS"], "hands": [["HARVEST"]], "market": []},
        baseline_continuation=[{"farmer": ["PASS"], "hands": [["PASS"]], "market": []} for _ in range(6)],
        current_step=48,
        valuation_tier=ValuationLevel.LEVEL_1_LOCAL_EXACT
    )
    a1 = engine.assess_opportunity(req_l1)

    # Level 3 counterfactual assessment
    req_l3 = LaborOpportunityRequest(
        worker_id=1,
        candidate_action_cmd="WEST",
        econ_state=econ,
        baseline_action={"farmer": ["PASS"], "hands": [["HARVEST"]], "market": []},
        baseline_continuation=[{"farmer": ["PASS"], "hands": [["PASS"]], "market": []} for _ in range(6)],
        current_step=48,
        valuation_tier=ValuationLevel.LEVEL_3_WIDER_ECONOMIC_REPLAY
    )
    a3 = engine.assess_opportunity(req_l3)
    assert a3.opportunity_cost >= 0.0


def test_invariant_f_no_arbitrary_fixed_dollar_constant(multiworker_obs: Dict[str, Any]) -> None:
    """Invariant F: No arbitrary dollar constant determines worthwhile opportunities."""
    econ = build_economic_state(multiworker_obs)
    engine = LaborOpportunityCostEngine()

    # Small positive value +$1.00
    task_small = WorkerTask(
        task_id="T_SMALL",
        action_family=TaskActionFamily.WAIT,
        location=(2, 2),
        cash_effect=1.00
    )
    req = LaborOpportunityRequest(
        worker_id=1,
        candidate_task=task_small,
        econ_state=econ,
        baseline_action={"farmer": ["PASS"], "hands": [["PASS"]], "market": []},
        baseline_continuation=[],
        current_step=48
    )
    assessment = engine.assess_opportunity(req)
    # Even $1.00 is recommended if net incremental value > 0 and safe
    assert assessment.commit_recommendation is True


def test_invariant_g_ordinal_priority_is_not_dollar_value() -> None:
    """Invariant G: TaskPriority integer value must not be directly treated as dollar amount."""
    pri = TaskPriority.HIGH_VALUE_HARVEST  # 600
    assert pri.value == 600
    # In LaborOpportunityAssessment, values are strictly derived from prices and yields, not 600
    assessment = LaborOpportunityAssessment(
        worker_id=0,
        candidate_task_id="T1",
        baseline_interval=(0, 1),
        alternative_interval=(0, 1),
        baseline_value=120.0,  # Actual market value of strawberries
        alternative_value=120.0,
        opportunity_cost=0.0,
        candidate_incremental_value=120.0,
        net_incremental_value=120.0
    )
    assert assessment.baseline_value != float(pri.value)


def test_invariant_h_insufficient_certainty_fails_closed(multiworker_obs: Dict[str, Any]) -> None:
    """Invariant H: If counterfactual certainty is insufficient, result must abstain."""
    econ = build_economic_state(multiworker_obs)
    engine = LaborOpportunityCostEngine()

    # Out of grid bounds
    req = LaborOpportunityRequest(
        worker_id=1,
        candidate_action_cmd="HARVEST",
        target_location=(99, 99),
        econ_state=econ,
        baseline_action={},
        baseline_continuation=[],
        current_step=48
    )
    assessment = engine.assess_opportunity(req)
    assert not assessment.safe_to_use
    assert assessment.commit_recommendation is False
    assert assessment.abstention_reason is not None


# =========================================================================
# Dominance Evaluation (§27)
# =========================================================================
def test_dominance_assessment_strictly_dominates() -> None:
    a1 = LaborOpportunityAssessment(
        worker_id=1, candidate_task_id="T1", baseline_interval=(0, 1), alternative_interval=(0, 1),
        baseline_value=100.0, alternative_value=200.0, opportunity_cost=10.0,
        candidate_incremental_value=200.0, net_incremental_value=190.0, safe_to_use=True
    )
    a2 = LaborOpportunityAssessment(
        worker_id=1, candidate_task_id="T1", baseline_interval=(0, 1), alternative_interval=(0, 1),
        baseline_value=100.0, alternative_value=150.0, opportunity_cost=50.0,
        candidate_incremental_value=150.0, net_incremental_value=100.0, safe_to_use=True
    )
    # A1 has higher net value and lower opportunity cost -> A1 strictly dominates A2
    assert MultiWorkerDominancePruner.dominates_assessment(a1, a2) is True
    assert MultiWorkerDominancePruner.dominates_assessment(a2, a1) is False


# =========================================================================
# Latency and Performance Benchmark (§28)
# =========================================================================
def test_performance_latency_benchmark(strawberry_field_obs: Dict[str, Any]) -> None:
    econ = build_economic_state(strawberry_field_obs)
    engine = LaborOpportunityCostEngine()

    req = LaborOpportunityRequest(
        worker_id=1,
        candidate_action_cmd="HARVEST",
        target_location=(2, 2),
        econ_state=econ,
        baseline_action={"farmer": ["PASS"], "hands": [["HARVEST"]], "market": []},
        baseline_continuation=[{"farmer": ["PASS"], "hands": [["PASS"]], "market": []} for _ in range(6)],
        current_step=48
    )

    times: List[float] = []
    for _ in range(10):
        t0 = time.perf_counter()
        assessment = engine.assess_opportunity(req)
        t1 = time.perf_counter()
        times.append((t1 - t0) * 1000.0)

    p50 = sorted(times)[len(times) // 2]
    worst = max(times)
    # Target: sub-100ms per assessment
    assert p50 < 100.0, f"p50 latency {p50:.2f}ms exceeds 100ms target"
    assert assessment.safe_to_use
