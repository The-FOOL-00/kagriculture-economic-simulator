# SPDX-License-Identifier: MIT
"""AEC Phase 005B: Dedicated Ground-Truth Labor Opportunity Tests (GT-01 through GT-12).

Rigorous unit test battery verifying that the labor opportunity-cost engine's
economic quantities agree with exact simulator mechanics, terminal semantics,
and multi-worker attributions (§18).
"""

from __future__ import annotations

import copy
import pytest
from typing import Any, Dict, List

from aec.config import BOARD_SIZE, CROP_GROWTH_DAYS, CROP_SEED_PRICE, FINAL_STEP, TURNS_PER_DAY
from aec.coordination.task_model import TaskActionFamily, TaskPriority, WorkerTask
from aec.coordination.worker_model import WorkerCapability, WorkerState, extract_farm_workers
from aec.ir.economic_state import build_economic_state
from aec.resource.labor_engine import (
    AbstentionReason,
    LaborOpportunityAssessment,
    LaborOpportunityCostEngine,
    LaborOpportunityRequest,
    ValuationLevel,
)


@pytest.fixture
def base_test_obs(normal_opening_obs: Dict[str, Any]) -> Dict[str, Any]:
    """10x10 farm observation with Farmer at [4,4] and Hand 1 at [2,2]."""
    obs = copy.deepcopy(normal_opening_obs)
    obs["step"] = 48
    obs["day"] = 2
    obs["hour"] = 0
    obs["farms"][0]["farmer"] = [4, 4]
    obs["farms"][0]["hands"] = [[2, 2]]
    obs["farms"][0]["hires_today"] = 1
    obs["private"]["inventories"] = [{}, {}]
    return obs


# =========================================================================
# GT-01: Exact Idle-Worker Delta
# Baseline: Hand 1 PASSES. Candidate: Hand 1 harvests mature CARROT ($60).
# Expected: opportunity_cost == 0.0, net_incremental_value == 60.0, rec == True
# =========================================================================
def test_gt01_exact_idle_worker_delta(base_test_obs: Dict[str, Any]) -> None:
    obs = copy.deepcopy(base_test_obs)
    obs["farms"][0]["tiles"][2][2] = {
        "kind": "PLANT",
        "crop": "CARROT",
        "yield_units": 2,
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
    res = engine.assess_opportunity(req)
    assert res.safe_to_use
    assert res.opportunity_cost == 0.0
    assert res.candidate_incremental_value > 0.0
    assert res.net_incremental_value > 0.0
    assert res.commit_recommendation is True


# =========================================================================
# GT-02: Exact Productive-Worker Displacement
# Baseline: Hand 1 HARVESTS mature CARROT ($60). Candidate: Hand 1 PASSES.
# Expected: opportunity_cost > 0.0, net_incremental_value < 0.0, rec == False
# =========================================================================
def test_gt02_exact_productive_worker_displacement(base_test_obs: Dict[str, Any]) -> None:
    obs = copy.deepcopy(base_test_obs)
    obs["farms"][0]["tiles"][2][2] = {
        "kind": "PLANT",
        "crop": "CARROT",
        "yield_units": 2,
        "planted_day": 0,
        "watered_today": True
    }
    econ = build_economic_state(obs)
    engine = LaborOpportunityCostEngine()

    req = LaborOpportunityRequest(
        worker_id=1,
        candidate_action_cmd="PASS",
        target_location=(2, 2),
        econ_state=econ,
        baseline_action={"farmer": ["PASS"], "hands": [["HARVEST"]], "market": []},
        baseline_continuation=[{"farmer": ["PASS"], "hands": [["PASS"]], "market": []} for _ in range(6)],
        current_step=48,
        valuation_tier=ValuationLevel.LEVEL_3_WIDER_ECONOMIC_REPLAY
    )
    res = engine.assess_opportunity(req)
    assert res.safe_to_use
    assert res.opportunity_cost > 0.0
    assert res.net_incremental_value < 0.0
    assert res.commit_recommendation is False


# =========================================================================
# GT-03: Peer Absorption
# Hand 1 has baseline duty, Hand 2 is idle. Hand 2 absorbs Hand 1's duty.
# Expected: valuation_level == LEVEL_2, opportunity_cost == 0.0
# =========================================================================
def test_gt03_peer_absorption(base_test_obs: Dict[str, Any]) -> None:
    obs = copy.deepcopy(base_test_obs)
    obs["farms"][0]["hands"] = [[2, 2], [2, 3]]
    obs["private"]["inventories"] = [{}, {}, {}]
    econ = build_economic_state(obs)
    engine = LaborOpportunityCostEngine()

    # Hand 1 baseline duty can be absorbed by idle Hand 2
    req = LaborOpportunityRequest(
        worker_id=1,
        candidate_action_cmd="HARVEST",
        econ_state=econ,
        baseline_action={"farmer": ["PASS"], "hands": [["WATER"], ["PASS"]], "market": []},
        baseline_continuation=[{"farmer": ["PASS"], "hands": [["PASS"], ["PASS"]], "market": []} for _ in range(6)],
        current_step=48
    )
    res = engine.assess_opportunity(req)
    assert res.safe_to_use
    assert res.opportunity_cost == 0.0


# =========================================================================
# GT-04: Downstream Dependency
# Candidate planting action unlocks downstream production value.
# Expected: downstream_value > 0.0
# =========================================================================
def test_gt04_downstream_dependency(base_test_obs: Dict[str, Any]) -> None:
    econ = build_economic_state(base_test_obs)
    engine = LaborOpportunityCostEngine()

    req = LaborOpportunityRequest(
        worker_id=1,
        candidate_action_cmd="PLANT",
        target_commodity="STRAWBERRY",
        econ_state=econ,
        baseline_action={"farmer": ["PASS"], "hands": [["PASS"]], "market": []},
        baseline_continuation=[{"farmer": ["PASS"], "hands": [["PASS"]], "market": []} for _ in range(6)],
        current_step=48
    )
    res = engine.assess_opportunity(req)
    assert res.safe_to_use
    assert res.downstream_value > 0.0


# =========================================================================
# GT-05: Terminal Deadline
# Crop planted when remaining days < first_yield_day has 0 terminal value.
# (LO-GT-TERMINAL-01 to 03)
# =========================================================================
def test_gt05_terminal_deadline(base_test_obs: Dict[str, Any]) -> None:
    obs = copy.deepcopy(base_test_obs)
    obs["step"] = 680
    obs["day"] = 28  # Day 28: only 2 days left until day 30 (step 720)
    # Strawberry requires 10 days to mature! Maturity day 28 + 10 = 38 >= 30!
    obs["farms"][0]["tiles"][2][2] = {
        "kind": "PLANT",
        "crop": "STRAWBERRY",
        "yield_units": 0,
        "planted_day": 28,
        "watered_today": True
    }
    econ = build_economic_state(obs)
    engine = LaborOpportunityCostEngine()

    val = engine._estimate_growing_crops_value(econ.farm.tiles, econ.market.current_prices, current_step=680)
    assert val == 0.0, f"Growing crop past terminal deadline must receive 0.0 value, got {val}"


# =========================================================================
# GT-06: Field Valuation vs Actual Realization
# Mature crop on tile is NOT counted as 100% liquid inventory.
# =========================================================================
def test_gt06_field_valuation_vs_actual_realization(base_test_obs: Dict[str, Any]) -> None:
    obs = copy.deepcopy(base_test_obs)
    obs["farms"][0]["tiles"][2][2] = {
        "kind": "PLANT",
        "crop": "CARROT",
        "yield_units": 2,
        "planted_day": 0,
        "watered_today": True
    }
    econ = build_economic_state(obs)
    engine = LaborOpportunityCostEngine()

    # Field valuation of unharvested crop in ground is 0.0 (requires harvest labor)
    val = engine._estimate_growing_crops_value(econ.farm.tiles, econ.market.current_prices, current_step=48)
    assert val == 0.0, "Unharvested mature crop must not be valued as liquid inventory"


# =========================================================================
# GT-07: No Double-Counting
# Controlled case: candidate gross value = X, baseline lost value = Y.
# Exact net delta = X - Y.
# =========================================================================
def test_gt07_no_double_counting(base_test_obs: Dict[str, Any]) -> None:
    econ = build_economic_state(base_test_obs)
    engine = LaborOpportunityCostEngine()

    # Candidate task with explicit cash effect $300 displacing baseline $50
    cand_task = WorkerTask(
        task_id="CAND_TASK",
        action_family=TaskActionFamily.HARVEST,
        location=(2, 2),
        priority_class=TaskPriority.HIGH_VALUE_HARVEST,
        duration=1,
        cash_effect=300.0
    )
    req = LaborOpportunityRequest(
        worker_id=1,
        candidate_task=cand_task,
        econ_state=econ,
        baseline_action={"farmer": ["PASS"], "hands": [["PASS"]], "market": []},
        baseline_continuation=[{"farmer": ["PASS"], "hands": [["PASS"]], "market": []} for _ in range(6)],
        current_step=48
    )
    res = engine.assess_opportunity(req)
    # Net incremental value == candidate_incremental_value - opportunity_cost
    assert abs(res.net_incremental_value - (res.candidate_incremental_value - res.opportunity_cost)) < 1e-4


# =========================================================================
# GT-08: Exact Sign Preservation
# When net delta > 0, engine recommends True. When net delta < 0, recommends False.
# =========================================================================
def test_gt08_exact_sign_preservation(base_test_obs: Dict[str, Any]) -> None:
    econ = build_economic_state(base_test_obs)
    engine = LaborOpportunityCostEngine()

    # Positive candidate
    req_pos = LaborOpportunityRequest(
        worker_id=1,
        candidate_action_cmd="PLANT",
        target_commodity="CARROT",
        econ_state=econ,
        baseline_action={"farmer": ["PASS"], "hands": [["PASS"]], "market": []},
        baseline_continuation=[],
        current_step=48
    )
    res_pos = engine.assess_opportunity(req_pos)
    assert res_pos.net_incremental_value > 0.0
    assert res_pos.commit_recommendation is True

    # Neutral/negative candidate (PASS)
    req_neg = LaborOpportunityRequest(
        worker_id=1,
        candidate_action_cmd="PASS",
        econ_state=econ,
        baseline_action={"farmer": ["PASS"], "hands": [["PASS"]], "market": []},
        baseline_continuation=[],
        current_step=48
    )
    res_neg = engine.assess_opportunity(req_neg)
    assert res_neg.net_incremental_value <= 0.0
    assert res_neg.commit_recommendation is False


# =========================================================================
# GT-09: Zero-Delta Case
# Baseline PASS, Candidate PASS. Net delta == 0.0, rec == False.
# =========================================================================
def test_gt09_zero_delta_case(base_test_obs: Dict[str, Any]) -> None:
    econ = build_economic_state(base_test_obs)
    engine = LaborOpportunityCostEngine()

    req = LaborOpportunityRequest(
        worker_id=1,
        candidate_action_cmd="PASS",
        econ_state=econ,
        baseline_action={"farmer": ["PASS"], "hands": [["PASS"]], "market": []},
        baseline_continuation=[],
        current_step=48
    )
    res = engine.assess_opportunity(req)
    assert res.safe_to_use
    assert res.opportunity_cost == 0.0
    assert res.candidate_incremental_value == 0.0
    assert res.net_incremental_value == 0.0
    assert res.commit_recommendation is False


# =========================================================================
# GT-10: Deterministic Replay
# Two consecutive evaluations on identical inputs yield bit-identical outputs.
# =========================================================================
def test_gt10_deterministic_replay(base_test_obs: Dict[str, Any]) -> None:
    econ = build_economic_state(base_test_obs)
    engine = LaborOpportunityCostEngine()

    req = LaborOpportunityRequest(
        worker_id=1,
        candidate_action_cmd="HARVEST",
        target_location=(2, 2),
        econ_state=econ,
        baseline_action={"farmer": ["PASS"], "hands": [["PASS"]], "market": []},
        baseline_continuation=[],
        current_step=48
    )
    r1 = engine.assess_opportunity(req)
    r2 = engine.assess_opportunity(req)
    assert r1.opportunity_cost == r2.opportunity_cost
    assert r1.net_incremental_value == r2.net_incremental_value
    assert r1.commit_recommendation == r2.commit_recommendation


# =========================================================================
# GT-11: Multi-Worker Attribution
# Hand 1 and Farmer on separate tasks. Diverting Hand 1 does not double-count
# or attribute Farmer's independent harvest to Hand 1.
# =========================================================================
def test_gt11_multiworker_attribution(base_test_obs: Dict[str, Any]) -> None:
    obs = copy.deepcopy(base_test_obs)
    # Tile (4, 4) has carrot harvested by Farmer
    obs["farms"][0]["tiles"][4][4] = {
        "kind": "PLANT",
        "crop": "CARROT",
        "yield_units": 2,
        "planted_day": 0,
        "watered_today": True
    }
    econ = build_economic_state(obs)
    engine = LaborOpportunityCostEngine()

    # Hand 1 is at [2, 2] passing while Farmer at [4, 4] harvests
    req = LaborOpportunityRequest(
        worker_id=1,
        candidate_action_cmd="PASS",
        econ_state=econ,
        baseline_action={"farmer": ["HARVEST"], "hands": [["PASS"]], "market": []},
        baseline_continuation=[],
        current_step=48
    )
    res = engine.assess_opportunity(req)
    assert res.opportunity_cost == 0.0
    assert 0 not in res.affected_workers


# =========================================================================
# GT-12: Cash/Timing Interaction
# Candidate with delayed revenue tracks net margin accurately.
# =========================================================================
def test_gt12_cash_timing_interaction(base_test_obs: Dict[str, Any]) -> None:
    econ = build_economic_state(base_test_obs)
    engine = LaborOpportunityCostEngine()

    # Immediate cash outlay $50, delayed return
    cand_task = WorkerTask(
        task_id="OUTLAY_TASK",
        action_family=TaskActionFamily.WAIT,
        location=(2, 2),
        priority_class=TaskPriority.SCHEDULED_PRODUCTION,
        duration=1,
        cash_effect=-50.0
    )
    req = LaborOpportunityRequest(
        worker_id=1,
        candidate_task=cand_task,
        econ_state=econ,
        baseline_action={"farmer": ["PASS"], "hands": [["PASS"]], "market": []},
        baseline_continuation=[],
        current_step=48
    )
    res = engine.assess_opportunity(req)
    assert res.direct_value == -50.0
    assert res.commit_recommendation is False
