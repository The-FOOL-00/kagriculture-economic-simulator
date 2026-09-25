# SPDX-License-Identifier: MIT
"""Unit and integration tests for Kagriculture V32 P12 Sparse Option Architecture."""

import copy
import os
import sys
import pytest
import numpy as np

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from candidates.v32_p12_options.incumbent import (
    EXPECTED_A7_SHA256,
    A7Incumbent,
    verify_a7_integrity,
)
from candidates.v32_p12_options.option_library import (
    OPTION_LIBRARY,
    OptionContract,
    OptionStatus,
)
from candidates.v32_p12_options.option_executor import OptionExecutor, OptionExecutionStatus
from candidates.v32_p12_options.resync import (
    ResyncState,
    SyncStatus,
    compute_manhattan,
    evaluate_resync,
)
from candidates.v32_p12_options.opportunity_detector import OpportunityDetector
from candidates.v32_p12_options.acceptance import OptionAcceptanceGate
from candidates.v32_p12_options.selector import (
    OptionControllerConfig,
    SparseOptionController,
)


def test_a7_incumbent_integrity():
    """Verify A7 hash matches exact required SHA-256."""
    assert verify_a7_integrity() is True


def test_option_library_contracts():
    """Verify all options O01..O06 are well-formed contracts."""
    assert len(OPTION_LIBRARY) >= 6
    for opt_id, contract in OPTION_LIBRARY.items():
        assert contract.option_id == opt_id
        assert contract.duration == 4  # Strict H=4 invariant
        assert contract.candidate_action in range(1, 10)
        assert contract.termination_condition != ""


def test_resync_state_evaluation():
    """Verify resynchronization evaluation correctly identifies SYNCED vs DESYNCED."""
    dummy_obs_a = {
        "farms": [
            {
                "farmer": [4, 4],
                "hands": [[4, 5], [5, 4]],
                "money": 1000.0,
                "unlocked_quadrants": [[0, 0]],
            }
        ],
        "private": {"shed": {"WHEAT": 20}},
    }
    dummy_obs_b = copy.deepcopy(dummy_obs_a)

    # Identical state -> SYNCED
    res_synced = evaluate_resync(100, dummy_obs_a, dummy_obs_b, player=0)
    assert res_synced.status == SyncStatus.SYNCED
    assert res_synced.state_distance < 0.01
    assert res_synced.is_synced is True

    # Displaced farmer -> PARTIALLY_SYNCED / DESYNCED
    dummy_obs_b["farms"][0]["farmer"] = [4, 6]  # Manhattan distance 2
    res_disp = evaluate_resync(100, dummy_obs_a, dummy_obs_b, player=0)
    assert res_disp.status in (SyncStatus.PARTIALLY_SYNCED, SyncStatus.RECOVERING)
    assert res_disp.total_manhattan_displacement == 2
    assert res_disp.is_synced is False


def test_option_executor_lifecycle():
    """Verify OptionExecutor enforces H=4 ticks, non-stacking, and mandatory return."""
    executor = OptionExecutor()
    opt = OPTION_LIBRARY["O01"]  # EXPAND_LAND

    # Start option
    assert executor.is_active is False
    started = executor.start_option(opt, current_step=288)
    assert started is True
    assert executor.is_active is True

    # Non-stacking invariant: cannot start second option while active
    assert executor.start_option(OPTION_LIBRARY["O02"], current_step=289) is False

    dummy_obs = {"farms": [{"money": 5000.0, "hands": []}], "private": {}}
    from candidates.v32_rlx2.state import EconomicFeatures
    dummy_feat = EconomicFeatures(
        cash=5000.0,
        wage_runway_days=5.0,
        liquid_inventory_value=0.0,
        committed_wages_today=0.0,
        active_workers=1,
        hires_today=0,
        next_hire_cost=1,
        idle_hands_count=0,
        chore_backlog=0,
        planted_crop_counts={},
        unwatered_crops_count=0,
        vacant_arable_count=5,
        weed_count=0,
        cow_count=0,
        sheep_count=0,
        goose_count=0,
        unfed_animals_count=0,
        uncared_animals_count=0,
        empty_pastures_count=0,
        feed_reserve_days=5.0,
        wheat_in_shed=20,
        unlocked_quadrants=1,
        next_land_cost=1000,
        spot_prices={},
        price_deltas={},
        market_inventory={},
        shed_inventory={},
        unlocked_shops=[],
        step=288,
        day=12,
        hour=0,
        remaining_steps=432,
        is_terminal_window=False,
        opp_cash=1000.0,
        opp_workers=1,
        opp_cows=0,
        opp_sheep=0,
        opp_geese=0,
        opp_crops=0,
        opp_quadrants=1,
    )

    base_act = {"farmer": ["PASS"], "hands": [], "market": []}

    # Tick 1
    _, st1 = executor.execute_step(dummy_obs, dummy_feat, base_act)
    assert st1.is_active is True
    assert st1.ticks_elapsed == 1

    # Tick 2
    _, st2 = executor.execute_step(dummy_obs, dummy_feat, base_act)
    assert st2.ticks_elapsed == 2

    # Tick 3
    _, st3 = executor.execute_step(dummy_obs, dummy_feat, base_act)
    assert st3.ticks_elapsed == 3

    # Tick 4 (Final tick of H=4 duration)
    _, st4 = executor.execute_step(dummy_obs, dummy_feat, base_act)
    assert st4.is_active is False
    assert st4.ticks_elapsed == 4
    assert st4.termination_reason == "DURATION_EXPIRED_MANDATORY_RETURN"

    # Executor is now inactive -> mandatory return to A7
    assert executor.is_active is False


def test_acceptance_gate_rules():
    """Verify OptionAcceptanceGate accepts good options and rejects bad ones."""
    gate = OptionAcceptanceGate(min_terminal_delta=200.0, require_exact_sync=True)
    opt = OPTION_LIBRARY["O01"]

    dummy_sync = ResyncState(
        step=292,
        status=SyncStatus.SYNCED,
        expected_farmer_pos=(4, 4),
        actual_farmer_pos=(4, 4),
        expected_hand_positions=[],
        actual_hand_positions=[],
        expected_worker_count=0,
        actual_worker_count=0,
        displaced_worker_count=0,
        total_manhattan_displacement=0,
        expected_cash=1000.0,
        actual_cash=500.0,
        cash_delta=-500.0,
        expected_shed={},
        actual_shed={},
        shed_unit_discrepancy=0,
        expected_quadrants=1,
        actual_quadrants=2,
        state_distance=0.25,
        is_next_a7_action_feasible=True,
    )

    # Positive delta + SYNCED -> ACCEPTED
    decision = gate.evaluate(opt, local_delta=-4000.0, resync_delta=-4000.0, terminal_delta=11179.0, resync_state=dummy_sync)
    assert decision.accepted is True

    # Low delta -> REJECTED
    decision_low = gate.evaluate(opt, local_delta=10.0, resync_delta=10.0, terminal_delta=50.0, resync_state=dummy_sync)
    assert decision_low.accepted is False

    # Desynced -> REJECTED
    dummy_desync = copy.deepcopy(dummy_sync)
    dummy_desync.status = SyncStatus.DESYNCED
    decision_desync = gate.evaluate(opt, local_delta=1000.0, resync_delta=1000.0, terminal_delta=5000.0, resync_state=dummy_desync)
    assert decision_desync.accepted is False
