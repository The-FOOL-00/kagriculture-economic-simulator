# SPDX-License-Identifier: MIT
"""AEC Checkpoint 001: Stale Backbone Reconnection Validation (§8).

Validates architectural behavior when a tactical AEC patch alters worker trajectory:
CASE A: Worker can reconnect safely -> local continuation
CASE B: Worker cannot reconnect -> ABSTAIN -> backbone
CASE C: Reconnection changes downstream timing -> larger replan
CASE D: Reconnection creates market consequences -> market re-evaluation / larger replan

Enforces:
- No blind continuation of an invalidated tape
- No silent PASS freezing of workers
- Deterministic fail-closed abstention when reconnection is infeasible
"""

from __future__ import annotations

import copy
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
import pytest

from aec.config import BOARD_SIZE, MOVES
from aec.counterfactual.simulator import CounterfactualSimulator, SimulationOutcome
from aec.ir.economic_state import build_economic_state
from aec.patches.patch import CoupledPatch
from aec.safety.checks import SafetyChecker


class ReconnectionStatus(Enum):
    SAFE_RECONNECT = "SAFE_RECONNECT"
    TIMING_SHIFT = "TIMING_SHIFT"
    MARKET_COLLISION = "MARKET_COLLISION"
    INVAL_CANNOT_RECONNECT = "INVAL_CANNOT_RECONNECT"


@dataclass
class ReconnectionPlan:
    status: ReconnectionStatus
    bridge_path: List[str]
    reconnect_step: int
    timing_offset: int
    recommended_action: str             # "LOCAL_CONTINUE", "LARGER_REPLAN", "ABSTAIN"


def compute_reconnection(
    mutated_start_pos: Tuple[int, int],
    target_pos: Tuple[int, int],
    baseline_schedule: List[Dict[str, Any]],
    current_step: int,
    max_bridge_steps: int = 4
) -> ReconnectionPlan:
    """Evaluates whether a diverged worker can reconnect to the baseline trajectory."""
    mx, my = mutated_start_pos
    tx, ty = target_pos
    manhattan_dist = abs(mx - tx) + abs(my - ty)

    # Check bounds
    if not (0 <= mx < BOARD_SIZE and 0 <= my < BOARD_SIZE):
        return ReconnectionPlan(
            status=ReconnectionStatus.INVAL_CANNOT_RECONNECT,
            bridge_path=[],
            reconnect_step=current_step,
            timing_offset=999,
            recommended_action="ABSTAIN"
        )

    # CASE B: Cannot reconnect within allowable bridge steps
    if manhattan_dist > max_bridge_steps:
        return ReconnectionPlan(
            status=ReconnectionStatus.INVAL_CANNOT_RECONNECT,
            bridge_path=[],
            reconnect_step=current_step,
            timing_offset=manhattan_dist,
            recommended_action="ABSTAIN"
        )

    # Generate minimal Manhattan bridge moves toward target
    bridge = []
    cx, cy = mx, my
    while (cx, cy) != (tx, ty):
        if cx < tx:
            cx += 1
            bridge.append("EAST")
        elif cx > tx:
            cx -= 1
            bridge.append("WEST")
        elif cy < ty:
            cy += 1
            bridge.append("SOUTH")
        elif cy > ty:
            cy -= 1
            bridge.append("NORTH")

    # Check timing impact
    timing_offset = len(bridge)
    if timing_offset == 0:
        return ReconnectionPlan(
            status=ReconnectionStatus.SAFE_RECONNECT,
            bridge_path=[],
            reconnect_step=current_step,
            timing_offset=0,
            recommended_action="LOCAL_CONTINUE"
        )

    # CASE C: Reconnection takes extra steps, delaying downstream actions
    if timing_offset > 1:
        return ReconnectionPlan(
            status=ReconnectionStatus.TIMING_SHIFT,
            bridge_path=bridge,
            reconnect_step=current_step + timing_offset,
            timing_offset=timing_offset,
            recommended_action="LARGER_REPLAN"
        )

    # CASE A: Safe local bridge (1 step adjustment)
    return ReconnectionPlan(
        status=ReconnectionStatus.SAFE_RECONNECT,
        bridge_path=bridge,
        reconnect_step=current_step + timing_offset,
        timing_offset=timing_offset,
        recommended_action="LOCAL_CONTINUE"
    )


def test_case_a_worker_safe_reconnect() -> None:
    """CASE A: Worker mutates 1 move, then reconnects safely to baseline tape.
    
    Mutated position is adjacent to target; minimal 1-step bridge reconnects.
    Outcome: SAFE_RECONNECT -> LOCAL_CONTINUE.
    """
    start_pos = (4, 4)
    # Patch moves SOUTH to (4, 5) instead of EAST to (5, 4)
    mutated_pos = (4, 5)
    # Baseline next scheduled waypoint is (5, 5)
    target_pos = (5, 5)

    baseline_schedule = [
        {"farmer": ["EAST"]},
        {"farmer": ["SOUTH"]},
        {"farmer": ["PLANT", "WHEAT"]}
    ]

    plan = compute_reconnection(
        mutated_start_pos=mutated_pos,
        target_pos=target_pos,
        baseline_schedule=baseline_schedule,
        current_step=0,
        max_bridge_steps=3
    )

    assert plan.status == ReconnectionStatus.SAFE_RECONNECT
    assert plan.recommended_action == "LOCAL_CONTINUE"
    assert plan.bridge_path == ["EAST"]
    assert plan.timing_offset == 1


def test_case_b_worker_cannot_reconnect_abstains() -> None:
    """CASE B: Worker cannot reconnect (diverged too far or out-of-bounds).
    
    Expected behavior: INVAL_CANNOT_RECONNECT -> ABSTAIN -> BACKBONE.
    System MUST NOT emit silent PASS or freeze worker.
    """
    mutated_pos = (0, 0)
    target_pos = (9, 9)  # Distance 18 > max_bridge_steps 4

    plan = compute_reconnection(
        mutated_start_pos=mutated_pos,
        target_pos=target_pos,
        baseline_schedule=[],
        current_step=0,
        max_bridge_steps=4
    )

    assert plan.status == ReconnectionStatus.INVAL_CANNOT_RECONNECT
    assert plan.recommended_action == "ABSTAIN"
    assert len(plan.bridge_path) == 0


def test_case_c_reconnection_changes_downstream_timing() -> None:
    """CASE C: Reconnection takes 3 steps, causing downstream harvest/plant to be delayed.
    
    Expected behavior: TIMING_SHIFT -> LARGER_REPLAN (Level 3/4).
    """
    mutated_pos = (2, 2)
    target_pos = (4, 3)  # Distance 3

    baseline_schedule = [
        {"farmer": ["PASS"]},
        {"farmer": ["HARVEST"]}  # Scheduled for step 1, but worker arrives at step 3!
    ]

    plan = compute_reconnection(
        mutated_start_pos=mutated_pos,
        target_pos=target_pos,
        baseline_schedule=baseline_schedule,
        current_step=0,
        max_bridge_steps=4
    )

    assert plan.status == ReconnectionStatus.TIMING_SHIFT
    assert plan.recommended_action == "LARGER_REPLAN"
    assert plan.timing_offset == 3


def test_case_d_reconnection_creates_market_consequences(normal_opening_obs: Dict[str, Any]) -> None:
    """CASE D: Reconnection delay prevents crop from reaching shed before scheduled market sell.
    
    Baseline schedule has SELL WHEAT at turn 4.
    If worker detour delays wheat deposit to turn 6, shed has 0 wheat at turn 4.
    Simulator detects intermediate insolvency: fidelity = FAILED -> ABSTAIN.
    """
    obs = copy.deepcopy(normal_opening_obs)
    obs["private"]["shed"] = {"WHEAT": 0}  # No wheat currently in shed
    state = build_economic_state(obs)

    # Baseline action schedules harvest, then deposit, then sell
    baseline_action = {
        "farmer": ["EAST"],
        "hands": [],
        "market": []
    }

    continuation_with_scheduled_sell = [
        {"farmer": ["HARVEST"], "hands": [], "market": []},
        {"farmer": ["MOVE_SHED"], "hands": [], "market": []},
        {"farmer": ["DROP"], "hands": [], "market": [["SELL", "WHEAT", 5]]},  # scheduled sell
    ]

    # Patch causes worker to step WEST (away from shed), delaying harvest/deposit
    detour_patch = CoupledPatch(
        patch_id="PATCH_DETOUR_DELAY",
        source_opportunity_id="OPP_DETOUR",
        worker_mutations={0: ["WEST"]},
        expected_horizon=4
    )

    simulator = CounterfactualSimulator()
    outcome = simulator.evaluate(
        candidate_patch=detour_patch,
        baseline_action=baseline_action,
        econ_state=state,
        horizon=4,
        continuation_trajectory=continuation_with_scheduled_sell
    )

    # The diverged route leads to spatial desynchronization / missing shed deposit
    assert outcome.spatial_consistency_ok is False or outcome.intermediate_solvency_ok is False

    # Safety checker verifies this is caught and rejected
    checker = SafetyChecker()
    passed, checks, reason = checker.verify(detour_patch, outcome, state, baseline_action)
    assert passed is False
    assert checks["spatial_consistency_ok"] is False or checks["obligation_ok"] is False
    assert "spatial" in reason.lower() or "intermediate" in reason.lower()
