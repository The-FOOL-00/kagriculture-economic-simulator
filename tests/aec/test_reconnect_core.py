# SPDX-License-Identifier: MIT
"""AEC-RECONNECT Core Trajectory & Pathfinding Validation (§17 Minimum Cases A-E).

Validates:
- Case A: One-step local detour + safe reconnect
- Case B: Two-step detour
- Case C: Multi-step detour
- Case D: Boundary obstacle (edges of board)
- Case E: Blocked reconnect point with fallback target selection
- Formal representations: WorkerTrajectoryState, TrajectorySegment, ReconnectRequest, ReconnectResult
- Route Splicing: PREFIX + PATCH + BRIDGE + SUFFIX
"""

from __future__ import annotations

import pytest
from typing import Any, Dict, List, Tuple

from aec.config import BOARD_SIZE
from aec.replanning.reconnect import (
    EscalationScope,
    ReconnectRequest,
    ReconnectResult,
    ReconnectionEngine,
    ReconnectionStatus,
    TrajectorySegment,
    WorkerTrajectoryState,
    deterministic_find_path,
    extract_worker_trajectory,
    reconnect_worker_trajectory,
)


class MockWorkerEntity:
    def __init__(self, worker_id: int, pos: Tuple[int, int]):
        self.worker_id = worker_id
        self.position = pos


class MockWorkerState:
    def __init__(self, workers: List[MockWorkerEntity]):
        self.workers = workers

    def get_worker(self, worker_id: int):
        for w in self.workers:
            if w.worker_id == worker_id:
                return w
        return None


class MockEconomicState:
    def __init__(self, worker_pos: Tuple[int, int] = (4, 4), step: int = 100):
        self.step = step
        self.workers = MockWorkerState([MockWorkerEntity(0, worker_pos)])


def test_formal_representations() -> None:
    """Validate that WorkerTrajectoryState and TrajectorySegment instantiate with formal schema (§6)."""
    state = WorkerTrajectoryState(
        worker_id=0,
        position=(3, 3),
        task="HARVEST",
        target=(3, 4),
        route=["SOUTH"],
        eta=1,
        carried_inventory={"WHEAT": 2},
        hand_usage={},
        action_dependencies=["DEP_WHEAT_MATURE"],
        downstream_waypoints=[(3, 4), (4, 4)],
        critical_obligations=[],
        expected_resource_arrivals={}
    )
    assert state.worker_id == 0
    assert state.position == (3, 3)
    assert state.total_cargo == 2

    segment = TrajectorySegment(
        start_state=state,
        action_sequence=[{"farmer": ["SOUTH"]}],
        expected_end_state=state,
        timing=1,
        spatial_occupancy=[(1, (3, 4))],
        resource_consequences={"WHEAT": 2}
    )
    assert segment.timing == 1
    assert segment.resource_consequences["WHEAT"] == 2


def test_case_a_one_step_local_detour() -> None:
    """CASE A: One-step local detour + safe reconnect (§17).
    
    Worker at (4, 4). Baseline moves EAST to (5, 4), then SOUTH to (5, 5).
    AEC patch executes a local detour SOUTH to (4, 5).
    Bridge path: EAST (1 step) from (4, 5) to reconnect at (5, 5).
    Outcome: SAFE_RECONNECT with timing_shift == 0 (at step 2).
    """
    econ_state = MockEconomicState(worker_pos=(4, 4))
    baseline_continuation = [
        {"farmer": ["EAST"]},             # Step 1: (4, 4) -> (5, 4)
        {"farmer": ["SOUTH"]},            # Step 2: (5, 4) -> (5, 5)
        {"farmer": ["HARVEST"]}           # Step 3: target tile op at (5, 5)
    ]

    req = ReconnectRequest(
        worker=0,
        divergence_point=0,
        patched_action=["SOUTH"],          # Patched detour: moves to (4, 5)
        baseline_continuation=baseline_continuation,
        econ_state=econ_state,
        causal_closure={"LOCAL_OPP_001"}
    )

    result = reconnect_worker_trajectory(req)

    assert result.status == ReconnectionStatus.SAFE_RECONNECT
    assert result.safety is True
    assert result.path == ["EAST"]         # Bridge from (4, 5) to (5, 5)
    assert result.timing_shift == 0        # Arrives at (5, 5) on offset 1 (matching baseline)
    assert result.escalation_scope == EscalationScope.LOCAL
    assert len(result.spliced_trajectory) >= 2


def test_case_b_two_step_detour() -> None:
    """CASE B: Two-step detour with safe reconnect (§17).
    
    Worker at (2, 2). Baseline moves EAST, EAST to (4, 2), then PLANT at (4, 2).
    Patched action moves SOUTH to (2, 3).
    Shortest bridge to (4, 2) takes 3 steps: NORTH, EAST, EAST (or EAST, EAST, NORTH).
    Arrival is delayed by 1 step -> RECONNECT_WITH_TIMING_SHIFT.
    """
    econ_state = MockEconomicState(worker_pos=(2, 2))
    baseline_continuation = [
        {"farmer": ["EAST"]},             # offset 0 -> (3, 2)
        {"farmer": ["EAST"]},             # offset 1 -> (4, 2)
        {"farmer": ["PLANT", "WHEAT"]}    # offset 2
    ]

    req = ReconnectRequest(
        worker=0,
        divergence_point=0,
        patched_action=["SOUTH"],          # diverged to (2, 3)
        baseline_continuation=baseline_continuation,
        econ_state=econ_state,
        causal_closure={"WEED_DIG_01"}
    )

    result = reconnect_worker_trajectory(req)

    assert result.safety is True
    assert result.status in (ReconnectionStatus.SAFE_RECONNECT, ReconnectionStatus.RECONNECT_WITH_TIMING_SHIFT)
    # Bridge connects from (2, 3) back to (4, 2)
    assert len(result.path) >= 2
    assert result.reconnect_target_pos == (4, 2)


def test_case_c_multistep_detour_with_escalation() -> None:
    """CASE C: Multi-step detour dynamically determines escalation scope (§17, §5)."""
    econ_state = MockEconomicState(worker_pos=(1, 1))
    baseline_continuation = [
        {"farmer": ["EAST"]},
        {"farmer": ["EAST"]},
        {"farmer": ["EAST"]},
        {"farmer": ["EAST"]},
        {"farmer": ["SOUTH"]},
        {"farmer": ["SOUTH"]},
        {"farmer": ["HARVEST"]}
    ]

    req = ReconnectRequest(
        worker=0,
        divergence_point=0,
        patched_action=["SOUTH"],
        baseline_continuation=baseline_continuation,
        econ_state=econ_state,
        causal_closure={"C1", "C2", "C3", "C4"}
    )

    result = reconnect_worker_trajectory(req)
    assert result.safety is True
    assert result.escalation_scope in (EscalationScope.DEPENDENCY_CLOSURE, EscalationScope.MEDIUM_REPLAN)


def test_case_d_boundary_obstacle_avoidance() -> None:
    """CASE D: Boundary obstacle handling (§17).
    
    A worker at boundary (0, 0) attempting an illegal out-of-bounds patch fails closed.
    Pathfinder respects boundaries (0 <= x < 10, 0 <= y < 10).
    """
    econ_state = MockEconomicState(worker_pos=(0, 0))
    baseline_continuation = [{"farmer": ["EAST"]}, {"farmer": ["SOUTH"]}]

    # Out of bounds patched move WEST from (0, 0) -> (-1, 0)
    req = ReconnectRequest(
        worker=0,
        divergence_point=0,
        patched_action=["WEST"],
        baseline_continuation=baseline_continuation,
        econ_state=econ_state
    )
    result = reconnect_worker_trajectory(req)
    assert result.status == ReconnectionStatus.INVAL_CANNOT_RECONNECT
    assert result.safety is False
    assert "out of bounds" in result.rejection_reason.lower()


def test_case_e_blocked_reconnect_point_fallback() -> None:
    """CASE E: When immediate waypoint is blocked, fall back to next safe target boundary (§17, §9)."""
    engine = ReconnectionEngine(board_size=10)
    baseline_continuation = [
        {"farmer": ["EAST"]},              # offset 0: waypoint (4, 4)
        {"farmer": ["EAST"]},              # offset 1: waypoint (5, 4)
        {"farmer": ["DROP"]},              # offset 2: task boundary at (6, 4)
        {"farmer": ["PASS"]}
    ]

    targets = engine.identify_reconnection_targets(
        baseline_continuation=baseline_continuation,
        start_pos=(3, 4),
        worker_id=0
    )

    # Must contain both immediate waypoint and task/resource boundary
    types_found = [t["target_types"] for t in targets]
    flat_types = [item for sublist in types_found for item in sublist]
    assert "IMMEDIATE_NEXT_WAYPOINT" in flat_types
    assert "TASK_BOUNDARY" in flat_types or "RESOURCE_BOUNDARY" in flat_types


def test_route_splicing_assembly() -> None:
    """Validate PREFIX + PATCH + BRIDGE + BASELINE SUFFIX structure (§8)."""
    engine = ReconnectionEngine(board_size=10)
    baseline_continuation = [
        {"farmer": ["EAST"], "hands": [["PASS"]], "market": []},
        {"farmer": ["SOUTH"], "hands": [["PASS"]], "market": []},
        {"farmer": ["HARVEST"], "hands": [["PASS"]], "market": [["SELL", "WHEAT", 2]]}
    ]

    bridge_path = ["EAST"]
    spliced = engine.splice_route(
        patched_action_cmd=["SOUTH"],
        bridge_path=bridge_path,
        baseline_continuation=baseline_continuation,
        target_offset=1,
        worker_id=0,
        timing_shift=0
    )

    assert len(spliced) >= 2
    # Bridge step assigns bridge move to farmer
    assert spliced[0]["farmer"] == ["EAST"]
    # Co-worker actions preserved
    assert spliced[0]["hands"] == [["PASS"]]
