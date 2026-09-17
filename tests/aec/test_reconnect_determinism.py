# SPDX-License-Identifier: MIT
"""AEC-RECONNECT Determinism & Replay Suite (§17 Case T; §7).

Validates:
- Case T: Deterministic replay across 100 repeated invocations
- Bit-level identical bridge paths, targets, and spliced trajectories
- Zero stochasticity, zero route jitter
"""

from __future__ import annotations

import copy
import pytest
from typing import Any, Dict, List, Tuple

from aec.replanning.reconnect import (
    ReconnectRequest,
    ReconnectResult,
    ReconnectionStatus,
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
    def __init__(self, worker_pos: Tuple[int, int] = (2, 2), step: int = 100):
        self.step = step
        self.workers = MockWorkerState([MockWorkerEntity(0, worker_pos)])


def test_case_t_100_repeat_deterministic_reconnection() -> None:
    """CASE T: Run 100 consecutive reconnection passes on identical inputs (§17).
    
    Verifies that every single run yields exact bit-level identical:
    - Status
    - Bridge path
    - Timing shift
    - Reconnect waypoint index
    - Spliced trajectory
    """
    econ_state = MockEconomicState(worker_pos=(3, 3), step=100)
    baseline_continuation = [
        {"farmer": ["EAST"], "hands": [["PASS"]], "market": []},
        {"farmer": ["EAST"], "hands": [["PASS"]], "market": []},
        {"farmer": ["SOUTH"], "hands": [["PASS"]], "market": []},
        {"farmer": ["HARVEST"], "hands": [["PASS"]], "market": [["SELL", "WHEAT", 1]]}
    ]

    base_req = ReconnectRequest(
        worker=0,
        divergence_point=100,
        patched_action=["SOUTH"],
        baseline_continuation=baseline_continuation,
        econ_state=econ_state,
        causal_closure={"DET_CHECK_01"}
    )

    first_result = reconnect_worker_trajectory(base_req)
    assert first_result.safety is True

    for run_idx in range(100):
        req_copy = copy.deepcopy(base_req)
        res = reconnect_worker_trajectory(req_copy)

        assert res.status == first_result.status, f"Status mismatch on iteration {run_idx}"
        assert res.path == first_result.path, f"Path mismatch on iteration {run_idx}"
        assert res.timing_shift == first_result.timing_shift, f"Timing shift mismatch on iteration {run_idx}"
        assert res.reconnect_waypoint_index == first_result.reconnect_waypoint_index, f"Waypoint mismatch on iteration {run_idx}"
        assert res.spliced_trajectory == first_result.spliced_trajectory, f"Spliced trajectory mismatch on iteration {run_idx}"


def test_pathfinder_determinism() -> None:
    """Verify deterministic_find_path produces identical move sequence on repeated calls."""
    start = (1, 1)
    target = (8, 8)

    first_path = deterministic_find_path(start, target, start_step=0, max_steps=30)
    assert first_path is not None

    for _ in range(50):
        path = deterministic_find_path(start, target, start_step=0, max_steps=30)
        assert path == first_path
