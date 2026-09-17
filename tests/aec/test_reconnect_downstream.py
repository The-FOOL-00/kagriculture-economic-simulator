# SPDX-License-Identifier: MIT
"""AEC-RECONNECT Downstream Dependencies & Escalation Suite (§17 Cases I, J, K, L, M, O, P, Q, R, S).

Validates:
- Case I: Timing shift without economic effect
- Case J: Timing shift with downstream economic effect
- Case K: Harvest -> deposit dependency
- Case L: Harvest -> market-sale dependency
- Case M: Resource availability dependency
- Case O: Terminal/endgame route change
- Case P: No safe reconnect -> fail closed abstain
- Case Q: Escalation from local -> medium
- Case R: Escalation from medium -> extended
- Case S: Full-replan recovery
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
    def __init__(self, worker_pos: Tuple[int, int] = (2, 2), step: int = 150):
        self.step = step
        self.workers = MockWorkerState([MockWorkerEntity(0, worker_pos)])


def test_case_i_timing_shift_without_economic_effect() -> None:
    """CASE I: Timing shift occurs, but downstream has no tight deadlines (§17).
    
    Status: RECONNECT_WITH_TIMING_SHIFT.
    Safe continuation is generated without economic penalty.
    """
    econ_state = MockEconomicState(worker_pos=(2, 2), step=100)
    baseline_continuation = [
        {"farmer": ["EAST"]},
        {"farmer": ["EAST"]},
        {"farmer": ["PASS"]},
        {"farmer": ["PASS"]}
    ]

    req = ReconnectRequest(
        worker=0,
        divergence_point=100,
        patched_action=["SOUTH"],
        baseline_continuation=baseline_continuation,
        econ_state=econ_state
    )

    result = reconnect_worker_trajectory(req)
    assert result.safety is True
    assert result.status in (ReconnectionStatus.SAFE_RECONNECT, ReconnectionStatus.RECONNECT_WITH_TIMING_SHIFT)
    assert result.reconnect_waypoint_index >= 0


def test_case_j_timing_shift_with_downstream_economic_effect() -> None:
    """CASE J: Timing shift causes arrival after a tight downstream economic deadline (§17).
    
    Status: INVAL_DOWNSTREAM_CONFLICT -> ABSTAIN.
    """
    econ_state = MockEconomicState(worker_pos=(2, 2), step=100)
    baseline_continuation = [
        {"farmer": ["EAST"]},
        {"farmer": ["EAST"]},
        {"farmer": ["HARVEST"]}
    ]

    req = ReconnectRequest(
        worker=0,
        divergence_point=100,
        patched_action=["SOUTH"],
        baseline_continuation=baseline_continuation,
        econ_state=econ_state,
        scheduled_market_sales=[{
            "step": 101,  # Strict deadline before detour can arrive
            "commodity": "WHEAT"
        }]
    )

    result = reconnect_worker_trajectory(req)
    assert result.safety is False
    assert result.status == ReconnectionStatus.INVAL_DOWNSTREAM_CONFLICT


def test_case_k_harvest_to_deposit_dependency() -> None:
    """CASE K: Harvest -> deposit dependency chain (§17, §10).
    
    Worker harvests cargo and must deposit at shed.
    Reconnection engine verifies the deposit target boundary is preserved.
    """
    econ_state = MockEconomicState(worker_pos=(3, 3), step=80)
    baseline_continuation = [
        {"farmer": ["EAST"]},
        {"farmer": ["EAST"]},
        {"farmer": ["DROP"]}   # Shed deposit boundary
    ]

    req = ReconnectRequest(
        worker=0,
        divergence_point=80,
        patched_action=["SOUTH"],
        baseline_continuation=baseline_continuation,
        econ_state=econ_state,
        causal_closure={"DEP_HARVEST", "DEP_SHED_DEPOSIT"}
    )

    result = reconnect_worker_trajectory(req)
    assert result.safety is True
    assert len(result.spliced_trajectory) >= 2


def test_case_l_harvest_to_market_sale_dependency() -> None:
    """CASE L: Harvest -> market-sale dependency (§17, §10)."""
    econ_state = MockEconomicState(worker_pos=(4, 4), step=90)
    baseline_continuation = [
        {"farmer": ["EAST"]},
        {"farmer": ["SOUTH"]},
        {"farmer": ["DROP"], "market": [["SELL", "WHEAT", 1]]}
    ]

    req = ReconnectRequest(
        worker=0,
        divergence_point=90,
        patched_action=["SOUTH"],
        baseline_continuation=baseline_continuation,
        econ_state=econ_state,
        scheduled_market_sales=[{"step": 110, "commodity": "WHEAT"}]
    )

    result = reconnect_worker_trajectory(req)
    assert result.safety is True
    assert result.status == ReconnectionStatus.SAFE_RECONNECT


def test_case_m_resource_availability_dependency() -> None:
    """CASE M: Resource availability dependency (§17)."""
    econ_state = MockEconomicState(worker_pos=(1, 1), step=50)
    baseline_continuation = [
        {"farmer": ["EAST"]},
        {"farmer": ["SOUTH"]},
        {"farmer": ["FEED", "COW"]}
    ]

    req = ReconnectRequest(
        worker=0,
        divergence_point=50,
        patched_action=["SOUTH"],
        baseline_continuation=baseline_continuation,
        econ_state=econ_state,
        critical_obligations=[{"deadline_step": 53, "description": "Feed cow"}]
    )

    result = reconnect_worker_trajectory(req)
    assert result.safety is True


def test_case_o_terminal_endgame_route_change() -> None:
    """CASE O: Route change in final turns (remaining_steps <= 24) escalates to FULL_REPLAN (§17, §5)."""
    econ_state = MockEconomicState(worker_pos=(5, 5), step=710)
    baseline_continuation = [{"farmer": ["EAST"]}, {"farmer": ["SOUTH"]}]

    req = ReconnectRequest(
        worker=0,
        divergence_point=710,
        patched_action=["NORTH"],
        baseline_continuation=baseline_continuation,
        econ_state=econ_state,
        remaining_steps=10
    )

    result = reconnect_worker_trajectory(req)
    assert result.escalation_scope == EscalationScope.FULL_REPLAN


def test_case_p_no_safe_reconnect_abstains() -> None:
    """CASE P: Impossibly far divergence beyond max bridge steps fails closed (§17, §12)."""
    # Worker at (5, 5)
    econ_state = MockEconomicState(worker_pos=(5, 5), step=10)
    # Baseline moves NORTH rapidly towards (5, 2)
    baseline_continuation = [
        {"farmer": ["NORTH"]},  # offset 0 -> (5, 4)
        {"farmer": ["NORTH"]},  # offset 1 -> (5, 3)
        {"farmer": ["NORTH"]}   # offset 2 -> (5, 2)
    ]

    # Worker diverged in opposite direction SOUTH to (5, 6)
    req = ReconnectRequest(
        worker=0,
        divergence_point=10,
        patched_action=["SOUTH"],
        baseline_continuation=baseline_continuation,
        econ_state=econ_state,
        max_bridge_steps=1  # Distance to nearest target is 2 > max_bridge_steps 1
    )

    result = reconnect_worker_trajectory(req)

    assert result.safety is False
    assert result.status == ReconnectionStatus.INVAL_CANNOT_RECONNECT
    assert "could not find any valid bridge" in result.rejection_reason


def test_case_q_escalation_local_to_medium() -> None:
    """CASE Q: Escalation from local to medium when closure contains 3-4 nodes (§17, §5)."""
    econ_state = MockEconomicState(worker_pos=(3, 3), step=100)
    baseline_continuation = [
        {"farmer": ["EAST"]}, {"farmer": ["EAST"]}, {"farmer": ["SOUTH"]}
    ]

    req = ReconnectRequest(
        worker=0,
        divergence_point=100,
        patched_action=["SOUTH"],
        baseline_continuation=baseline_continuation,
        econ_state=econ_state,
        causal_closure={"NODE_1", "NODE_2", "NODE_3"}
    )

    result = reconnect_worker_trajectory(req)
    assert result.safety is True
    assert result.escalation_scope in (EscalationScope.DEPENDENCY_CLOSURE, EscalationScope.MEDIUM_REPLAN)


def test_case_r_escalation_medium_to_extended() -> None:
    """CASE R: Escalation to extended replan when closure size >= 5 (§17, §5)."""
    econ_state = MockEconomicState(worker_pos=(3, 3), step=100)
    baseline_continuation = [
        {"farmer": ["EAST"]}, {"farmer": ["EAST"]}, {"farmer": ["SOUTH"]},
        {"farmer": ["SOUTH"]}, {"farmer": ["EAST"]}
    ]

    req = ReconnectRequest(
        worker=0,
        divergence_point=100,
        patched_action=["SOUTH"],
        baseline_continuation=baseline_continuation,
        econ_state=econ_state,
        causal_closure={"N1", "N2", "N3", "N4", "N5", "N6"}
    )

    result = reconnect_worker_trajectory(req)
    assert result.safety is True
    assert result.escalation_scope == EscalationScope.EXTENDED_REPLAN


def test_case_s_full_replan_recovery() -> None:
    """CASE S: Full replan recovery flag when unresolvable conflict triggers escalation (§17, §5)."""
    econ_state = MockEconomicState(worker_pos=(0, 0), step=705)
    baseline_continuation = [{"farmer": ["PASS"]}]

    req = ReconnectRequest(
        worker=0,
        divergence_point=705,
        patched_action=["SOUTH"],
        baseline_continuation=baseline_continuation,
        econ_state=econ_state,
        remaining_steps=15
    )

    result = reconnect_worker_trajectory(req)
    assert result.escalation_scope == EscalationScope.FULL_REPLAN
