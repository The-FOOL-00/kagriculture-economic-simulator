# SPDX-License-Identifier: MIT
"""AEC-RECONNECT Adversarial Test Suite (§18, §19).

Critical Negative Adversarial Cases (local looks profitable, full-system negative -> MUST escalate or abstain):
1. Detour saves immediate action but misses a scheduled market sale.
2. Route change reaches resource but causes another worker to miss its target / collide.
3. Local harvest fills shed before higher-value shipment.
4. Route reconnect succeeds spatially but misses production/decay deadline.
5. Route succeeds locally but terminal obligation becomes impossible.

Positive Adversarial Cases (local-only would abstain, but route splicing finds safe profitable continuation):
6. Small detour -> reconnect -> preserves downstream sale.
7. Small harvest deviation -> bridge route -> maintains market timing.
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
    def __init__(self, worker_pos: Tuple[int, int] = (3, 3), step: int = 50):
        self.step = step
        self.workers = MockWorkerState([MockWorkerEntity(0, worker_pos)])


def test_adversarial_1_detour_misses_market_sale() -> None:
    """ADVERSARIAL 1: Detour saves immediate action but misses scheduled market sale (§18).
    
    A worker takes a detour that arrives at step 55.
    A scheduled market sale of WHEAT is locked at step 52.
    Arrival after step 52 causes market sale failure.
    Result MUST NOT commit: INVAL_DOWNSTREAM_CONFLICT -> ABSTAIN.
    """
    econ_state = MockEconomicState(worker_pos=(3, 3), step=50)
    baseline_continuation = [
        {"farmer": ["EAST"]},
        {"farmer": ["EAST"]},
        {"farmer": ["HARVEST"]}
    ]

    req = ReconnectRequest(
        worker=0,
        divergence_point=50,
        patched_action=["SOUTH"],  # Detour takes 4 extra steps to reconnect
        baseline_continuation=baseline_continuation,
        econ_state=econ_state,
        scheduled_market_sales=[{
            "step": 52,             # Hard market order deadline!
            "commodity": "WHEAT"
        }]
    )

    result = reconnect_worker_trajectory(req)

    assert result.safety is False
    assert result.status == ReconnectionStatus.INVAL_DOWNSTREAM_CONFLICT
    assert "market sale" in result.rejection_reason.lower()


def test_adversarial_2_route_change_collides_with_coworker() -> None:
    """ADVERSARIAL 2: Route change reaches resource but collides with another worker (§18).
    
    Worker 0 detours onto (4, 3) at step 51.
    Worker 1 is already scheduled to occupy (4, 3) at step 51.
    Multi-worker collision must be detected -> INVAL_SPATIAL_CONFLICT -> ABSTAIN.
    """
    econ_state = MockEconomicState(worker_pos=(3, 3), step=50)
    baseline_continuation = [{"farmer": ["EAST"]}, {"farmer": ["SOUTH"]}]

    # Co-worker 1 is traversing (4, 3) at offset 0 (step 50 -> 51)
    co_worker_trajectories = {
        1: [(4, 2), (4, 3), (4, 4)]
    }

    req = ReconnectRequest(
        worker=0,
        divergence_point=50,
        patched_action=["EAST"],     # Moves to (4, 3) where worker 1 arrives!
        baseline_continuation=baseline_continuation,
        econ_state=econ_state,
        co_worker_trajectories=co_worker_trajectories
    )

    result = reconnect_worker_trajectory(req)

    # Must detect collision and reject
    assert result.safety is False
    assert result.status in (ReconnectionStatus.INVAL_SPATIAL_CONFLICT, ReconnectionStatus.INVAL_CANNOT_RECONNECT)


def test_adversarial_3_shed_capacity_overflow_conflict() -> None:
    """ADVERSARIAL 3: Local harvest profitable but shed overflows before high-value shipment (§18).
    
    The detour causes an extra shed inflow that exceeds capacity before a high-value shipment.
    Fails closed via downstream obligation check.
    """
    econ_state = MockEconomicState(worker_pos=(4, 4), step=100)
    baseline_continuation = [{"farmer": ["PASS"]}, {"farmer": ["DROP"]}]

    req = ReconnectRequest(
        worker=0,
        divergence_point=100,
        patched_action=["SOUTH"],
        baseline_continuation=baseline_continuation,
        econ_state=econ_state,
        critical_obligations=[{
            "deadline_step": 101,
            "description": "High-value shipment reservation in shed"
        }]
    )

    result = reconnect_worker_trajectory(req)

    # Detour causes arrival after deadline 101
    assert result.safety is False
    assert result.status == ReconnectionStatus.INVAL_DOWNSTREAM_CONFLICT


def test_adversarial_4_production_timing_missed() -> None:
    """ADVERSARIAL 4: Spatially connects, but misses plant/decay production timing deadline (§18)."""
    econ_state = MockEconomicState(worker_pos=(1, 1), step=200)
    baseline_continuation = [
        {"farmer": ["EAST"]},
        {"farmer": ["EAST"]},
        {"farmer": ["WATER"]}      # Unwatered plant decays if not watered by step 202
    ]

    req = ReconnectRequest(
        worker=0,
        divergence_point=200,
        patched_action=["SOUTH"],
        baseline_continuation=baseline_continuation,
        econ_state=econ_state,
        critical_obligations=[{
            "deadline_step": 202,
            "description": "Plant decay watering deadline"
        }]
    )

    result = reconnect_worker_trajectory(req)
    assert result.safety is False
    assert result.status == ReconnectionStatus.INVAL_DOWNSTREAM_CONFLICT


def test_adversarial_5_terminal_obligation_impossible() -> None:
    """ADVERSARIAL 5: Detour in terminal endgame makes final harvest/sale impossible (§18)."""
    econ_state = MockEconomicState(worker_pos=(5, 5), step=710)
    baseline_continuation = [{"farmer": ["NORTH"]}, {"farmer": ["DROP"]}]

    req = ReconnectRequest(
        worker=0,
        divergence_point=710,
        patched_action=["SOUTH"],
        baseline_continuation=baseline_continuation,
        econ_state=econ_state,
        remaining_steps=10,        # Endgame boundary
        critical_obligations=[{
            "deadline_step": 712,
            "description": "Terminal market liquidation"
        }]
    )

    result = reconnect_worker_trajectory(req)
    # Bridge cannot satisfy deadline 712 -> fails closed
    assert result.safety is False
    assert result.status == ReconnectionStatus.INVAL_DOWNSTREAM_CONFLICT


def test_positive_adversarial_1_small_detour_preserves_later_sale() -> None:
    """POSITIVE ADVERSARIAL 1: Small detour reconnects and preserves downstream market sale (§19).
    
    Local-only naive check without reconnection would abstain due to spatial desync.
    Route-splicing connects via 1-step bridge in time for sale at step 60.
    Outcome: SAFE_RECONNECT.
    """
    econ_state = MockEconomicState(worker_pos=(2, 2), step=50)
    baseline_continuation = [
        {"farmer": ["EAST"]},             # Step 51: (3, 2)
        {"farmer": ["SOUTH"]},            # Step 52: (3, 3)
        {"farmer": ["DROP"]},             # Step 53: (3, 3)
    ]

    req = ReconnectRequest(
        worker=0,
        divergence_point=50,
        patched_action=["SOUTH"],          # Detour to (2, 3) at step 51
        baseline_continuation=baseline_continuation,
        econ_state=econ_state,
        scheduled_market_sales=[{
            "step": 60,                    # Sale is comfortably at step 60
            "commodity": "WHEAT"
        }]
    )

    result = reconnect_worker_trajectory(req)

    assert result.safety is True
    assert result.status == ReconnectionStatus.SAFE_RECONNECT
    assert result.path == ["EAST"]         # Moves from (2, 3) to (3, 3)
    assert result.timing_shift == 0
    assert len(result.spliced_trajectory) >= 2


def test_positive_adversarial_2_harvest_deviation_maintains_timing() -> None:
    """POSITIVE ADVERSARIAL 2: Local harvest deviation bridges cleanly, maintaining market timing (§19)."""
    econ_state = MockEconomicState(worker_pos=(5, 4), step=120)
    baseline_continuation = [
        {"farmer": ["EAST"]},
        {"farmer": ["SOUTH"]},
        {"farmer": ["DROP"]}
    ]

    req = ReconnectRequest(
        worker=0,
        divergence_point=120,
        patched_action=["SOUTH"],
        baseline_continuation=baseline_continuation,
        econ_state=econ_state,
        causal_closure={"HARVEST_OPP_01"}
    )

    result = reconnect_worker_trajectory(req)
    assert result.safety is True
    assert result.is_safe is True
    assert len(result.spliced_trajectory) > 0
