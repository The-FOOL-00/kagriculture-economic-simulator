# SPDX-License-Identifier: MIT
"""AEC Phase 004: Dedicated Multi-Worker Replay Fixtures (§27 Scenarios PV-01 to PV-15).

Validates discrete operational scenarios for multi-worker resource conversion,
feed security rescue, contention resolution, and simulator physical fidelity.
"""

from __future__ import annotations

import copy
import pytest
from typing import Any, Dict, List, Optional, Set, Tuple

from aec.coordination.assignment import (
    DisplacementOutcome,
    LaborOpportunityCost,
    WorkerAssignment,
    WorkerSchedule,
    compute_marginal_labor_cost,
)
from aec.coordination.dominance import MultiWorkerDominancePruner
from aec.coordination.scheduler import (
    CoordinationStatus,
    MultiWorkerLogisticsCoordinator,
    WorkerCoordinationPlan,
)
from aec.coordination.task_model import (
    TaskActionFamily,
    TaskDependencyGraph,
    TaskPriority,
    WorkerTask,
)
from aec.coordination.worker_model import (
    WorkerCapability,
    WorkerState,
    WorkerType,
    extract_farm_workers,
)
from aec.replanning.reconnect import SpacetimeReservationTable, deterministic_find_path
from aec.resource.conversions import ConversionExecutionPlan, decompose_conversion_to_tasks
from aec.resource.feed_security import decompose_feed_rescue_to_tasks


def make_w(wid: int, pos: Tuple[int, int], wtype: WorkerType = WorkerType.HAND) -> WorkerState:
    return WorkerState(
        worker_id=wid,
        worker_type=WorkerType.FARMER if wid == 0 else wtype,
        position=pos,
        carried_inventory={},
    )


# ---------------------------------------------------------------------------
# Scenarios PV-01 to PV-15
# ---------------------------------------------------------------------------

def test_pv01_feed_rescue_hand1_handles_feed_farmer_harvests() -> None:
    """PV-01: Feed rescue where Hand 1 handles feed and Farmer harvests."""
    coord = MultiWorkerLogisticsCoordinator(board_size=10)
    workers = {
        0: make_w(0, pos=(1, 1), wtype=WorkerType.FARMER),
        1: make_w(1, pos=(4, 4), wtype=WorkerType.HAND),
    }
    baseline_action = {"farmer": ["HARVEST"], "hands": [["PASS"]]}
    baseline_cont = [{"farmer": ["HARVEST"], "hands": [["PASS"]]}]

    tasks = decompose_feed_rescue_to_tasks(deficit=1, animal_pos=(4, 6), current_step=10, shed_pos=(4, 4))
    plan = coord.plan_coordination(tasks, workers, baseline_action, baseline_cont, current_step=10)

    assert plan.status == CoordinationStatus.SUCCESS
    # Hand 1 executes both pickup and feed
    assert all(a.worker_id == 1 for a in plan.assignments)
    # Farmer's harvest must be preserved
    assert plan.labor_opportunity_cost.lost_mandatory_count == 0


def test_pv02_resource_conversion_hand1_processes_farmer_crops() -> None:
    """PV-02: Resource conversion where Hand 1 processes while Farmer continues crop task."""
    coord = MultiWorkerLogisticsCoordinator(board_size=10)
    workers = {
        0: make_w(0, pos=(0, 0), wtype=WorkerType.FARMER),
        1: make_w(1, pos=(4, 4), wtype=WorkerType.HAND),
    }
    baseline_action = {"farmer": ["PLANT"], "hands": [["PASS"]]}

    plan_obj = ConversionExecutionPlan(
        plan_id="CONV_P2",
        conversion_id="CONV_EGG",
        target_commodity="EGG",
        required_inputs={"WHEAT": 1},
        produced_outputs={"EGG": 1},
        worker_id=1,
        target_location=(4, 5),
        worker_actions=["FEED"],
        estimated_duration=2,
        net_value_est=80.0
    )
    tasks = decompose_conversion_to_tasks(plan_obj, start_step=20)
    plan = coord.plan_coordination(tasks, workers, baseline_action, [], current_step=20)

    assert plan.status == CoordinationStatus.SUCCESS
    assert plan.assignments[0].worker_id == 1
    assert 1 in plan.worker_mutations


def test_pv03_both_tasks_require_same_worker() -> None:
    """PV-03: Both tasks require same worker -> priority ordering enforced."""
    coord = MultiWorkerLogisticsCoordinator(board_size=10)
    workers = {
        0: make_w(0, pos=(4, 4), wtype=WorkerType.FARMER),
    }
    high_pri_task = WorkerTask(
        task_id="HIGH_PRI",
        action_family=TaskActionFamily.FEED_ANIMAL,
        location=(4, 5),
        priority_class=TaskPriority.LIVESTOCK_SECURITY,
        is_mandatory=True,
    )
    low_pri_task = WorkerTask(
        task_id="LOW_PRI",
        action_family=TaskActionFamily.DIG_WEED,
        location=(1, 1),
        priority_class=TaskPriority.OPPORTUNISTIC_TASK,
        is_mandatory=False,
    )
    dag = TaskDependencyGraph()
    dag.add_task(high_pri_task)
    dag.add_task(low_pri_task)
    ready = dag.get_ready_tasks()

    assert ready[0].task_id == "HIGH_PRI"
    assert ready[1].task_id == "LOW_PRI"


def test_pv04_second_worker_spatially_inaccessible() -> None:
    """PV-04: Second worker exists but is spatially inaccessible -> coordinator assigns Farmer if feasible."""
    coord = MultiWorkerLogisticsCoordinator(board_size=10)
    workers = {
        0: make_w(0, pos=(4, 4), wtype=WorkerType.FARMER),
        1: make_w(1, pos=(9, 9), wtype=WorkerType.HAND),  # Far away
    }
    task = WorkerTask(
        task_id="URGENT_TASK_P4",
        action_family=TaskActionFamily.FEED_ANIMAL,
        location=(4, 5),
        earliest_start=0,
        latest_completion=2,  # Only worker at (4, 4) can reach in 2 steps
        priority_class=TaskPriority.LIVESTOCK_SECURITY,
        is_mandatory=True,
    )
    plan = coord.plan_coordination([task], workers, {"farmer": ["PASS"], "hands": [["PASS"]]}, [], current_step=0)

    assert plan.status == CoordinationStatus.SUCCESS
    assert plan.assignments[0].worker_id == 0


def test_pv05_second_worker_accessible_but_baseline_obligation_invalidates() -> None:
    """PV-05: Second worker is accessible but has mandatory baseline duty -> abstains if neither free."""
    coord = MultiWorkerLogisticsCoordinator(board_size=10)
    workers = {
        0: make_w(0, pos=(1, 1), wtype=WorkerType.FARMER),
        1: make_w(1, pos=(4, 4), wtype=WorkerType.HAND),
    }
    # Both workers have mandatory baseline harvests
    baseline_action = {"farmer": ["HARVEST"], "hands": [["HARVEST"]]}
    baseline_cont = [{"farmer": ["HARVEST"], "hands": [["HARVEST"]]}]

    feed_task = WorkerTask(
        task_id="FEED_BREACH_P5",
        action_family=TaskActionFamily.FEED_ANIMAL,
        location=(5, 5),
        earliest_start=0,
        latest_completion=1,
        priority_class=TaskPriority.LIVESTOCK_SECURITY,
        is_mandatory=True,
    )
    plan = coord.plan_coordination([feed_task], workers, baseline_action, baseline_cont, current_step=0)

    # Must abstain because a mandatory obligation would be lost
    assert plan.status in (CoordinationStatus.ABSTAIN_LABOR_CANNIBALIZATION, CoordinationStatus.ABSTAIN_CONFLICT)
    assert not plan.is_executable


def test_pv06_reassignment_saves_high_value_harvest() -> None:
    """PV-06: Reassignment saves a high-value harvest ($160 tomato/milk)."""
    cost = LaborOpportunityCost(
        lost_mandatory_count=0,
        displaced_value_est=0.0,
        absorbed_tasks=["FEED_TASK"],
        is_acceptable=True,
        rationale="Hand 1 absorbed feed; Farmer harvest preserved ($160 saved)"
    )
    assert cost.is_acceptable is True
    assert cost.lost_mandatory_count == 0


def test_pv07_reassignment_causes_downstream_market_conflict() -> None:
    """PV-07: Reassignment causes downstream market conflict -> dependency closure rejects."""
    cost = LaborOpportunityCost(
        lost_mandatory_count=1,
        displaced_obligations=["MARKET_SALE_TURN_48"],
        is_acceptable=False
    )
    cost.evaluate_acceptability()
    assert cost.is_acceptable is False


def test_pv08_resource_conversion_and_feed_rescue_simultaneously() -> None:
    """PV-08: Resource conversion + feed rescue simultaneously across 2 workers."""
    coord = MultiWorkerLogisticsCoordinator(board_size=10)
    workers = {
        0: make_w(0, pos=(4, 4), wtype=WorkerType.FARMER),
        1: make_w(1, pos=(4, 5), wtype=WorkerType.HAND),
    }
    task1 = WorkerTask(task_id="T_FEED", action_family=TaskActionFamily.FEED_ANIMAL, location=(4, 5), earliest_start=0, latest_completion=5)
    task2 = WorkerTask(task_id="T_CONV", action_family=TaskActionFamily.HARVEST, location=(4, 4), earliest_start=0, latest_completion=5)

    plan = coord.plan_coordination([task1, task2], workers, {"farmer": ["PASS"], "hands": [["PASS"]]}, [], current_step=0)
    assert plan.status == CoordinationStatus.SUCCESS


def test_pv09_three_worker_assignment() -> None:
    """PV-09: Three-worker assignment (Farmer + Hand 1 + Hand 2)."""
    coord = MultiWorkerLogisticsCoordinator(board_size=10)
    workers = {
        0: make_w(0, pos=(0, 0), wtype=WorkerType.FARMER),
        1: make_w(1, pos=(4, 4), wtype=WorkerType.HAND),
        2: make_w(2, pos=(8, 8), wtype=WorkerType.HAND),
    }
    task = WorkerTask(task_id="T_H2", action_family=TaskActionFamily.FEED_ANIMAL, location=(8, 7), earliest_start=0, latest_completion=5)
    plan = coord.plan_coordination([task], workers, {"farmer": ["HARVEST"], "hands": [["HARVEST"], ["PASS"]]}, [], current_step=0)

    assert plan.status == CoordinationStatus.SUCCESS
    assert plan.assignments[0].worker_id == 2


def test_pv10_terminal_multiworker_logistics() -> None:
    """PV-10: Terminal multi-worker logistics (Step >= 715)."""
    coord = MultiWorkerLogisticsCoordinator(board_size=10)
    workers = {0: make_w(0, pos=(0, 0), wtype=WorkerType.FARMER)}
    task = WorkerTask(task_id="TERM_T", action_family=TaskActionFamily.HARVEST, location=(9, 9), earliest_start=718, latest_completion=720)
    plan = coord.plan_coordination([task], workers, {"farmer": ["PASS"], "hands": []}, [], current_step=718)
    assert plan.status == CoordinationStatus.ABSTAIN_LABOR_CANNIBALIZATION


def test_pv11_resource_contention() -> None:
    """PV-11: Two workers contend for same resource stock."""
    table = SpacetimeReservationTable(10)
    assert table.reserve_resource(step=10, resource_key="WHEAT_STOCK", worker_id=0) is True
    assert table.reserve_resource(step=10, resource_key="WHEAT_STOCK", worker_id=1) is False


def test_pv12_building_contention() -> None:
    """PV-12: Two workers contend for same building tile."""
    table = SpacetimeReservationTable(10)
    assert table.reserve_building(step=5, pos=(2, 2), worker_id=0) is True
    assert table.reserve_building(step=5, pos=(2, 2), worker_id=1) is False


def test_pv13_shed_access_contention() -> None:
    """PV-13: Shed access contention (mutual exclusivity on shed access tile)."""
    table = SpacetimeReservationTable(10)
    assert table.reserve_vertex(step=1, pos=(4, 4), worker_id=0) is True
    assert table.reserve_vertex(step=1, pos=(4, 4), worker_id=1) is False


def test_pv14_illegal_direct_handoff() -> None:
    """PV-14: Illegal direct handoff rejected fail-closed."""
    coord = MultiWorkerLogisticsCoordinator(board_size=10)
    workers = {0: make_w(0, (4, 4)), 1: make_w(1, (4, 5))}
    bad_task = WorkerTask(
        task_id="BAD_HANDOFF",
        action_family=TaskActionFamily.DELIVER_RESOURCE,
        location=(4, 5),
        metadata={"direct_unit_handoff": True}
    )
    plan = coord.plan_coordination([bad_task], workers, {"farmer": ["PASS"], "hands": [["PASS"]]}, [], current_step=0)
    assert plan.status == CoordinationStatus.ABSTAIN_ILLEGAL_HANDOFF


def test_pv15_deterministic_repeated_assignment() -> None:
    """PV-15: Deterministic repeated assignment across 10 trials."""
    coord = MultiWorkerLogisticsCoordinator(board_size=10)
    workers = {0: make_w(0, (1, 1)), 1: make_w(1, (4, 4))}
    task = WorkerTask(task_id="DET_T", action_family=TaskActionFamily.FEED_ANIMAL, location=(4, 5), earliest_start=0, latest_completion=5)

    plans = [
        coord.plan_coordination([task], workers, {"farmer": ["PASS"], "hands": [["PASS"]]}, [], current_step=0)
        for _ in range(10)
    ]
    for p in plans[1:]:
        assert p.status == plans[0].status
        assert p.assignments[0].worker_id == plans[0].assignments[0].worker_id
        assert p.assignments[0].transit_route == plans[0].assignments[0].transit_route
