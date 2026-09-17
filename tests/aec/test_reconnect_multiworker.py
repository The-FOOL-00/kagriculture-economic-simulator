# SPDX-License-Identifier: MIT
"""AEC-RECONNECT Multi-Worker Coordination Suite (§17 Cases F, G, H, N; §11).

Validates:
- Case F: Worker-worker collision detection & avoidance
- Case G: Worker-hand collision detection & avoidance
- Case H: Shared target tile resolution
- Case N: Multi-worker dependency chain
- SpacetimeReservationTable vertex & swap collision checks
"""

from __future__ import annotations

import pytest
from typing import Any, Dict, List, Tuple

from aec.replanning.reconnect import (
    EscalationScope,
    ReconnectRequest,
    ReconnectResult,
    ReconnectionEngine,
    ReconnectionStatus,
    SpacetimeReservationTable,
    deterministic_find_path,
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
    def __init__(self, workers: List[Tuple[int, Tuple[int, int]]], step: int = 100):
        self.step = step
        self.workers = MockWorkerState([MockWorkerEntity(wid, pos) for wid, pos in workers])


def test_spacetime_reservation_vertex_collision() -> None:
    """Validate vertex collision reservation logic (§11)."""
    table = SpacetimeReservationTable(board_size=10)
    # Worker 1 reserves (4, 4) at step 2
    assert table.reserve_vertex(step=2, pos=(4, 4), worker_id=1) is True

    # Same worker reserving again is allowed (idempotent)
    assert table.reserve_vertex(step=2, pos=(4, 4), worker_id=1) is True

    # Worker 0 trying to reserve same cell at step 2 must fail!
    assert table.reserve_vertex(step=2, pos=(4, 4), worker_id=0) is False
    assert table.is_vertex_available(step=2, pos=(4, 4), worker_id=0) is False


def test_spacetime_reservation_swap_collision() -> None:
    """Validate head-on / swap edge collision prevention (§11).
    
    Worker 1 moves (3, 3) -> (4, 3) at step 1.
    Worker 0 cannot simultaneously move (4, 3) -> (3, 3) at step 1!
    """
    table = SpacetimeReservationTable(board_size=10)
    assert table.reserve_edge(step=1, from_pos=(3, 3), to_pos=(4, 3), worker_id=1) is True

    # Worker 0 swap attempt:
    assert table.reserve_edge(step=1, from_pos=(4, 3), to_pos=(3, 3), worker_id=0) is False
    assert table.is_edge_available(step=1, from_pos=(4, 3), to_pos=(3, 3), worker_id=0) is False


def test_case_f_worker_worker_collision_avoidance() -> None:
    """CASE F: Worker-worker collision detection & detour around co-worker (§17, §11).
    
    Farmer (Worker 0) at (2, 2) wants to reach (4, 2).
    Worker 1 is sitting on cell (3, 2) at step 1.
    Deterministic pathfinder must route around (3, 2) (e.g. SOUTH -> EAST -> EAST -> NORTH)
    without colliding!
    """
    table = SpacetimeReservationTable(board_size=10)
    # Worker 1 occupies (3, 2) at step 1 and step 2
    table.reserve_vertex(step=1, pos=(3, 2), worker_id=1)
    table.reserve_vertex(step=2, pos=(3, 2), worker_id=1)

    path = deterministic_find_path(
        start=(2, 2),
        target=(4, 2),
        start_step=0,
        reservations=table,
        worker_id=0,
        max_steps=10
    )

    assert path is not None
    # Verify path never steps on (3, 2) at step 1 or step 2
    cur = (2, 2)
    step = 0
    from aec.config import MOVES
    for move in path:
        step += 1
        dx, dy = MOVES[move]
        cur = (cur[0] + dx, cur[1] + dy)
        assert not (cur == (3, 2) and step in (1, 2)), f"Collided at step {step} on {cur}!"
    assert cur == (4, 2)


def test_case_g_worker_hand_collision() -> None:
    """CASE G: Farmer and hired hand interaction (§17, §11)."""
    econ_state = MockEconomicState(workers=[(0, (2, 2)), (1, (2, 3))], step=100)
    baseline_continuation = [
        {"farmer": ["EAST"], "hands": [["EAST"]]},
        {"farmer": ["SOUTH"], "hands": [["SOUTH"]]}
    ]

    # Hand is at (2, 3) -> (3, 3) -> (3, 4)
    co_worker_trajectories = {
        1: [(2, 3), (3, 3), (3, 4)]
    }

    req = ReconnectRequest(
        worker=0,
        divergence_point=100,
        patched_action=["EAST"],          # Farmer moves (2, 2) -> (3, 2)
        baseline_continuation=baseline_continuation,
        econ_state=econ_state,
        co_worker_trajectories=co_worker_trajectories
    )

    result = reconnect_worker_trajectory(req)
    assert result.safety is True
    assert 1 in result.affected_workers


def test_case_h_shared_target_tile() -> None:
    """CASE H: Shared target tile resolution (§17, §11).
    
    If co-worker occupies target tile at the exact step,
    reconnection engine waits or detours to avoid simultaneous occupation.
    """
    table = SpacetimeReservationTable(board_size=10)
    # Co-worker occupies (4, 4) at step 2
    table.reserve_vertex(step=2, pos=(4, 4), worker_id=1)

    path = deterministic_find_path(
        start=(3, 4),
        target=(4, 4),
        start_step=1,
        reservations=table,
        worker_id=0,
        max_steps=5,
        allow_pass=True
    )

    # Pathfinder either takes an extra detour or waits (PASS) until step 3
    assert path is not None
    cur = (3, 4)
    from aec.config import MOVES
    step = 1
    for move in path:
        step += 1
        if move in MOVES:
            dx, dy = MOVES[move]
            cur = (cur[0] + dx, cur[1] + dy)
        if step == 2:
            assert cur != (4, 4), "Violated reservation at step 2!"
    assert cur == (4, 4)


def test_case_n_multiworker_dependency_chain() -> None:
    """CASE N: Multi-worker dependency chain with 3 workers (§17, §11)."""
    econ_state = MockEconomicState(workers=[(0, (1, 1)), (1, (2, 2)), (2, (3, 3))], step=50)
    baseline_continuation = [
        {"farmer": ["EAST"], "hands": [["EAST"], ["SOUTH"]]},
        {"farmer": ["SOUTH"], "hands": [["SOUTH"], ["EAST"]]}
    ]

    co_trajectories = {
        1: [(2, 2), (3, 2), (3, 3)],
        2: [(3, 3), (3, 4), (4, 4)]
    }

    req = ReconnectRequest(
        worker=0,
        divergence_point=50,
        patched_action=["SOUTH"],
        baseline_continuation=baseline_continuation,
        econ_state=econ_state,
        co_worker_trajectories=co_trajectories,
        causal_closure={"MULTI_WORKER_COORDINATION"}
    )

    result = reconnect_worker_trajectory(req)
    assert result.safety is True
    assert len(result.affected_workers) >= 2
