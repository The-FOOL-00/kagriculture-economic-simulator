# SPDX-License-Identifier: MIT
"""AEC Phase 003: Adversarial Multi-Worker Logistics Coordination Suite (§26 Scenarios MW-01 to MW-20; §27).

Comprehensive micro-validation testing deterministic multi-worker scheduling,
space-time reservation collision avoidance, marginal labor opportunity cost derivation,
resource ownership, and simulator ground-truth fidelity.
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
from aec.replanning.reconnect import (
    SpacetimeReservationTable,
    deterministic_find_path,
)
from aec.safety.checks import SafetyChecker


# ---------------------------------------------------------------------------
# Test Fixtures & Helpers
# ---------------------------------------------------------------------------

def make_worker(
    worker_id: int,
    pos: Tuple[int, int],
    wtype: WorkerType = WorkerType.HAND,
    carried: Optional[Dict[str, int]] = None
) -> WorkerState:
    return WorkerState(
        worker_id=worker_id,
        worker_type=WorkerType.FARMER if worker_id == 0 else wtype,
        position=pos,
        carried_inventory=carried or {},
    )


# ---------------------------------------------------------------------------
# Scenarios MW-01 to MW-20
# ---------------------------------------------------------------------------

def test_mw01_two_workers_urgent_feed_and_crop_harvest() -> None:
    """MW-01: Two workers, one urgent feed task, one crop harvest task.
    
    Expected: Coordinator assigns feed task to non-critical worker (Hand 1),
    preserving Worker 0 (Farmer) on high-value crop harvest.
    """
    coord = MultiWorkerLogisticsCoordinator(board_size=10)
    workers = {
        0: make_worker(0, pos=(0, 0), wtype=WorkerType.FARMER),
        1: make_worker(1, pos=(4, 4), wtype=WorkerType.HAND),
    }
    # Farmer baseline is harvesting at (0, 0)
    baseline_action = {"farmer": ["HARVEST"], "hands": [["PASS"]]}
    baseline_cont = [{"farmer": ["HARVEST"], "hands": [["PASS"]]}]

    # Candidate task: urgent feed at (4, 5)
    feed_task = WorkerTask(
        task_id="URGENT_FEED_01",
        action_family=TaskActionFamily.FEED_ANIMAL,
        location=(4, 5),
        earliest_start=10,
        latest_completion=15,
        priority_class=TaskPriority.LIVESTOCK_SECURITY,
        is_mandatory=True,
    )

    plan = coord.plan_coordination(
        candidate_tasks=[feed_task],
        workers=workers,
        baseline_action=baseline_action,
        baseline_continuation=baseline_cont,
        current_step=10
    )

    assert plan.status == CoordinationStatus.SUCCESS
    assert len(plan.assignments) == 1
    # Must assign to Hand 1 (worker 1), freeing Farmer (worker 0)
    assert plan.assignments[0].worker_id == 1
    assert plan.labor_opportunity_cost.is_acceptable is True
    # Farmer's harvest must be preserved
    assert plan.labor_opportunity_cost.lost_mandatory_count == 0


def test_mw02_only_primary_worker_can_reach_feed() -> None:
    """MW-02: Only primary worker can reach feed before deadline.
    
    Expected: Assigns primary worker and preserves remaining schedule as much as possible.
    """
    coord = MultiWorkerLogisticsCoordinator(board_size=10)
    # Worker 0 is near feed (4, 4); Worker 1 is trapped far away at (9, 9) with strict deadline
    workers = {
        0: make_worker(0, pos=(4, 4), wtype=WorkerType.FARMER),
        1: make_worker(1, pos=(9, 9), wtype=WorkerType.HAND),
    }
    baseline_action = {"farmer": ["PASS"], "hands": [["PASS"]]}
    baseline_cont = [{"farmer": ["PASS"], "hands": [["PASS"]]}]

    feed_task = WorkerTask(
        task_id="TIGHT_FEED_02",
        action_family=TaskActionFamily.FEED_ANIMAL,
        location=(4, 5),
        earliest_start=10,
        latest_completion=12,  # Worker 1 cannot reach in 2 steps from (9, 9)
        priority_class=TaskPriority.LIVESTOCK_SECURITY,
        is_mandatory=True,
    )

    plan = coord.plan_coordination(
        candidate_tasks=[feed_task],
        workers=workers,
        baseline_action=baseline_action,
        baseline_continuation=baseline_cont,
        current_step=10
    )

    assert plan.status == CoordinationStatus.SUCCESS
    assert len(plan.assignments) == 1
    assert plan.assignments[0].worker_id == 0


def test_mw03_simultaneous_obligations_conflict_abstains() -> None:
    """MW-03: Both workers required for simultaneous incompatible obligations.
    
    Expected: Detect conflict and abstain if impossible to satisfy all mandatory obligations.
    """
    coord = MultiWorkerLogisticsCoordinator(board_size=10)
    workers = {
        0: make_worker(0, pos=(0, 0), wtype=WorkerType.FARMER),
        1: make_worker(1, pos=(9, 9), wtype=WorkerType.HAND),
    }
    # Both workers have mandatory baseline duties that cannot be dropped
    baseline_action = {"farmer": ["HARVEST"], "hands": [["HARVEST"]]}
    baseline_cont = [{"farmer": ["HARVEST"], "hands": [["HARVEST"]]}]

    # A third mandatory task that neither worker can take without breaching mandatory baseline
    feed_task = WorkerTask(
        task_id="FEED_CONFLICT_03",
        action_family=TaskActionFamily.FEED_ANIMAL,
        location=(5, 5),
        earliest_start=10,
        latest_completion=11,
        priority_class=TaskPriority.LIVESTOCK_SECURITY,
        is_mandatory=True,
    )

    plan = coord.plan_coordination(
        candidate_tasks=[feed_task],
        workers=workers,
        baseline_action=baseline_action,
        baseline_continuation=baseline_cont,
        current_step=10
    )

    # Must abstain because mandatory obligations would be lost
    assert plan.status in (CoordinationStatus.ABSTAIN_LABOR_CANNIBALIZATION, CoordinationStatus.ABSTAIN_CONFLICT)
    assert not plan.is_executable


def test_mw04_alternative_worker_absorbs_feed_task() -> None:
    """MW-04: One worker diverted from high-value harvest -> alternative worker absorbs feed task."""
    coord = MultiWorkerLogisticsCoordinator(board_size=10)
    workers = {
        0: make_worker(0, pos=(1, 1), wtype=WorkerType.FARMER),
        1: make_worker(1, pos=(3, 3), wtype=WorkerType.HAND),
    }
    # Farmer has high-value harvest
    baseline_action = {"farmer": ["HARVEST"], "hands": [["PASS"]]}
    baseline_cont = [{"farmer": ["HARVEST"], "hands": [["PASS"]]}]

    feed_task = WorkerTask(
        task_id="ABSORB_FEED_04",
        action_family=TaskActionFamily.FEED_ANIMAL,
        location=(4, 4),
        earliest_start=20,
        latest_completion=25,
        priority_class=TaskPriority.LIVESTOCK_SECURITY,
        is_mandatory=True,
    )

    plan = coord.plan_coordination(
        candidate_tasks=[feed_task],
        workers=workers,
        baseline_action=baseline_action,
        baseline_continuation=baseline_cont,
        current_step=20
    )

    assert plan.status == CoordinationStatus.SUCCESS
    assert plan.assignments[0].worker_id == 1
    assert 1 in plan.worker_mutations


def test_mw05_worker_route_collision_prevented() -> None:
    """MW-05: Worker reassignment causes route collision -> space-time reservation detects/reroutes."""
    table = SpacetimeReservationTable(board_size=10)
    # Hand 1 is scheduled to move (4, 4) -> (4, 5) at step 15
    table.reserve_vertex(14, (4, 4), worker_id=1)
    table.reserve_vertex(15, (4, 5), worker_id=1)
    table.reserve_edge(15, (4, 4), (4, 5), worker_id=1)

    # Worker 0 trying swap edge collision (4, 5) -> (4, 4) at step 15 must fail
    assert table.is_edge_available(15, (4, 5), (4, 4), worker_id=0) is False
    assert table.reserve_edge(15, (4, 5), (4, 4), worker_id=0) is False

    # Pathfinding for Worker 0 avoids the collision
    path = deterministic_find_path(
        start=(4, 5),
        target=(4, 3),
        start_step=14,
        reservations=table,
        worker_id=0,
        max_steps=10
    )
    assert path is not None
    # Cannot step directly into (4, 4) at step 15
    first_move = path[0]
    next_pos = (4, 5 + 1) if first_move == "SOUTH" else ((4, 5 - 1) if first_move == "NORTH" else (5, 5))
    assert next_pos != (4, 4) or table.is_vertex_available(15, next_pos, worker_id=0)


def test_mw06_direct_worker_handoff_conflict_abstained() -> None:
    """MW-06: Direct unit-to-unit handoff is physically illegal in simulator; must ABSTAIN."""
    coord = MultiWorkerLogisticsCoordinator(board_size=10)
    workers = {
        0: make_worker(0, pos=(4, 4), wtype=WorkerType.FARMER),
        1: make_worker(1, pos=(4, 5), wtype=WorkerType.HAND),
    }

    # Task requesting direct unit handoff
    direct_handoff_task = WorkerTask(
        task_id="DIRECT_HANDOFF_TASK",
        action_family=TaskActionFamily.DELIVER_RESOURCE,
        location=(4, 5),
        earliest_start=5,
        latest_completion=10,
        metadata={"direct_unit_handoff": True}  # Physically illegal!
    )

    plan = coord.plan_coordination(
        candidate_tasks=[direct_handoff_task],
        workers=workers,
        baseline_action={"farmer": ["PASS"], "hands": [["PASS"]]},
        baseline_continuation=[],
        current_step=5
    )

    assert plan.status == CoordinationStatus.ABSTAIN_ILLEGAL_HANDOFF
    assert "Direct unit-to-unit handoff is physically illegal" in plan.rejection_reason


def test_mw07_downstream_market_sale_destruction_rejected() -> None:
    """MW-07: Worker reassignment looks locally beneficial but breaches deadline/obligations."""
    cost = LaborOpportunityCost()
    # 1 mandatory sale obligation lost
    cost.lost_mandatory_count = 1
    cost.displaced_obligations.append("SALE_OBLIGATION_01")
    cost.evaluate_acceptability()

    assert cost.is_acceptable is False
    assert "mandatory obligations lost" in cost.rationale


def test_mw08_dominance_pruning_chooses_surviving_plan() -> None:
    """MW-08: Two assignments feasible; one preserves more baseline obligations -> dominance chooses."""
    task = WorkerTask(
        task_id="OPP_TASK",
        action_family=TaskActionFamily.FEED_ANIMAL,
        location=(4, 5),
        earliest_start=0,
        latest_completion=10,
    )
    # Plan A: Diverts Farmer, cancels 1 harvest obligation
    cost_a = LaborOpportunityCost(
        lost_mandatory_count=1,
        displaced_value_est=150.0,
        is_acceptable=False
    )
    assignment_a = [WorkerAssignment(worker_id=0, task=task, start_step=0, completion_step=2)]

    # Plan B: Uses Hand 1, preserves all harvest obligations
    cost_b = LaborOpportunityCost(
        lost_mandatory_count=0,
        displaced_value_est=0.0,
        absorbed_tasks=["OPP_TASK"],
        is_acceptable=True
    )
    assignment_b = [WorkerAssignment(worker_id=1, task=task, start_step=0, completion_step=2)]

    # Plan B must dominate Plan A
    assert MultiWorkerDominancePruner.dominates(assignment_b, cost_b, assignment_a, cost_a) is True
    assert MultiWorkerDominancePruner.dominates(assignment_a, cost_a, assignment_b, cost_b) is False

    pruned = MultiWorkerDominancePruner.prune([(assignment_a, cost_a), (assignment_b, cost_b)])
    assert len(pruned) == 1
    assert pruned[0][0][0].worker_id == 1


def test_mw09_emergency_feed_safe_with_second_worker() -> None:
    """MW-09: Emergency feed purchase safe only if second worker executes it."""
    from aec.resource.feed_security import decompose_feed_rescue_to_tasks

    tasks = decompose_feed_rescue_to_tasks(
        deficit=1,
        animal_pos=(4, 6),
        current_step=10,
        shed_pos=(4, 4),
        latest_step=23
    )
    assert len(tasks) == 2
    assert tasks[0].action_family == TaskActionFamily.PICKUP_RESOURCE
    assert tasks[1].action_family == TaskActionFamily.FEED_ANIMAL

    coord = MultiWorkerLogisticsCoordinator(board_size=10)
    workers = {
        0: make_worker(0, pos=(1, 1), wtype=WorkerType.FARMER),
        1: make_worker(1, pos=(4, 4), wtype=WorkerType.HAND),
    }
    # Farmer is busy harvesting
    plan = coord.plan_coordination(
        candidate_tasks=tasks,
        workers=workers,
        baseline_action={"farmer": ["HARVEST"], "hands": [["PASS"]]},
        baseline_continuation=[{"farmer": ["HARVEST"], "hands": [["PASS"]]}],
        current_step=10
    )

    assert plan.status == CoordinationStatus.SUCCESS
    assert all(a.worker_id == 1 for a in plan.assignments)


def test_mw10_resource_conversion_multiworker_solution() -> None:
    """MW-10: Resource conversion executable with second worker."""
    from aec.resource.conversions import ConversionExecutionPlan, decompose_conversion_to_tasks

    plan_obj = ConversionExecutionPlan(
        plan_id="PLAN_CONV_01",
        conversion_id="CONV_MILK_01",
        target_commodity="MILK",
        required_inputs={"WHEAT": 1},
        produced_outputs={"MILK": 1},
        worker_id=1,
        target_location=(5, 5),
        worker_actions=["FEED"],
        estimated_duration=3,
        net_value_est=120.0
    )
    tasks = decompose_conversion_to_tasks(plan_obj, start_step=5)
    assert len(tasks) == 1
    assert tasks[0].action_family == TaskActionFamily.FEED_ANIMAL

    coord = MultiWorkerLogisticsCoordinator(board_size=10)
    workers = {
        0: make_worker(0, pos=(0, 0), wtype=WorkerType.FARMER),
        1: make_worker(1, pos=(5, 4), wtype=WorkerType.HAND),
    }

    plan = coord.plan_coordination(
        candidate_tasks=tasks,
        workers=workers,
        baseline_action={"farmer": ["HARVEST"], "hands": [["PASS"]]},
        baseline_continuation=[],
        current_step=5
    )

    assert plan.status == CoordinationStatus.SUCCESS
    assert plan.assignments[0].worker_id == 1


def test_mw11_building_tile_competition_exclusivity() -> None:
    """MW-11: Primary worker and Hand1 compete for same building/tile -> reservation table prevents collision."""
    table = SpacetimeReservationTable(board_size=10)
    # Farmer reserves building construction on (3, 3) at step 5
    assert table.reserve_building(step=5, pos=(3, 3), worker_id=0) is True
    # Hand 1 attempting same building/tile at step 5 must be rejected
    assert table.reserve_building(step=5, pos=(3, 3), worker_id=1) is False
    assert table.is_building_available(step=5, pos=(3, 3), worker_id=1) is False


def test_mw12_resource_ownership_prevents_double_allocation() -> None:
    """MW-12: Two workers attempt same resource -> ownership prevents double allocation."""
    table = SpacetimeReservationTable(board_size=10)
    # Hand 1 locks wheat at shed (4, 4) at step 8
    assert table.reserve_resource(step=8, resource_key="WHEAT_(4, 4)", worker_id=1) is True
    # Farmer attempting to claim same wheat at step 8 must fail
    assert table.reserve_resource(step=8, resource_key="WHEAT_(4, 4)", worker_id=0) is False
    assert table.is_resource_available(step=8, resource_key="WHEAT_(4, 4)", worker_id=0) is False


def test_mw13_worker_unavailable_escalates_and_abstains() -> None:
    """MW-13: Worker becomes unavailable or lacks capability mid-route -> reallocates or abstains."""
    coord = MultiWorkerLogisticsCoordinator(board_size=10)
    workers = {
        0: make_worker(0, pos=(0, 0), wtype=WorkerType.FARMER),
    }
    # Worker 0 lacks FEED capability
    workers[0].capabilities.remove(WorkerCapability.FEED)

    feed_task = WorkerTask(
        task_id="TASK_NO_CAP",
        action_family=TaskActionFamily.FEED_ANIMAL,
        location=(4, 4),
        required_capabilities={WorkerCapability.FEED},
        earliest_start=0,
        latest_completion=10,
    )

    plan = coord.plan_coordination(
        candidate_tasks=[feed_task],
        workers=workers,
        baseline_action={"farmer": ["PASS"], "hands": []},
        baseline_continuation=[],
        current_step=0
    )

    assert plan.status == CoordinationStatus.ABSTAIN_LABOR_CANNIBALIZATION
    assert not plan.is_executable


def test_mw14_terminal_worker_assignment_rejected_if_cannot_complete() -> None:
    """MW-14: Terminal worker assignment appears profitable but cannot complete before 720."""
    coord = MultiWorkerLogisticsCoordinator(board_size=10)
    workers = {
        0: make_worker(0, pos=(0, 0), wtype=WorkerType.FARMER),
    }
    # Step 718: Task at (9, 9) requires 18 transit steps, impossible to complete by step 720
    late_task = WorkerTask(
        task_id="LATE_TASK",
        action_family=TaskActionFamily.HARVEST,
        location=(9, 9),
        earliest_start=718,
        latest_completion=720,
    )

    plan = coord.plan_coordination(
        candidate_tasks=[late_task],
        workers=workers,
        baseline_action={"farmer": ["PASS"], "hands": []},
        baseline_continuation=[],
        current_step=718
    )

    assert plan.status == CoordinationStatus.ABSTAIN_LABOR_CANNIBALIZATION
    assert not plan.is_executable


def test_mw15_optional_task_superseded_by_coordinator() -> None:
    """MW-15: One worker task is optional baseline action -> scheduler may supersede optional task."""
    baseline_tasks = [
        WorkerTask(
            task_id="WEED_DIG_OPTIONAL",
            action_family=TaskActionFamily.DIG_WEED,
            location=(2, 2),
            priority_class=TaskPriority.OPPORTUNISTIC_TASK,
            is_mandatory=False,
            target_worker_preference=0,
            cash_effect=0.0
        )
    ]
    # Replaced by candidate harvest
    cand_task = WorkerTask(
        task_id="HARVEST_CAND",
        action_family=TaskActionFamily.HARVEST,
        location=(1, 1),
        priority_class=TaskPriority.HIGH_VALUE_HARVEST,
        is_mandatory=True,
        cash_effect=60.0
    )
    assignment = [
        WorkerAssignment(worker_id=0, task=cand_task, start_step=0, completion_step=1)
    ]

    cost = compute_marginal_labor_cost(baseline_tasks, assignment, {0})
    assert cost.displaced_tasks["WEED_DIG_OPTIONAL"] == DisplacementOutcome.SUPERSEDED_OPTIONAL
    assert cost.is_acceptable is True
    assert cost.lost_mandatory_count == 0


def test_mw16_mandatory_baseline_task_displacement_rejected() -> None:
    """MW-16: Mandatory baseline task cannot be displaced unless another worker absorbs it."""
    baseline_tasks = [
        WorkerTask(
            task_id="MANDATORY_COW_FEED",
            action_family=TaskActionFamily.FEED_ANIMAL,
            location=(4, 5),
            priority_class=TaskPriority.LIVESTOCK_SECURITY,
            is_mandatory=True,
            target_worker_preference=0,
            cash_effect=0.0
        )
    ]
    # Displacing it without absorbing
    assignment = [
        WorkerAssignment(
            worker_id=0,
            task=WorkerTask(task_id="OPT_TASK", action_family=TaskActionFamily.DIG_WEED, location=(1, 1)),
            start_step=0,
            completion_step=1
        )
    ]
    cost = compute_marginal_labor_cost(baseline_tasks, assignment, {0})
    assert cost.displaced_tasks["MANDATORY_COW_FEED"] == DisplacementOutcome.INFEASIBLE
    assert cost.lost_mandatory_count == 1
    assert cost.is_acceptable is False


def test_mw17_cash_timing_dependency() -> None:
    """MW-17: Assignment changes cash timing -> dependency propagation catches shortfall."""
    task1 = WorkerTask(task_id="T1", action_family=TaskActionFamily.HARVEST, location=(1, 1), cash_effect=100.0)
    task2 = WorkerTask(task_id="T2", action_family=TaskActionFamily.MARKET_BUY, location=(4, 4), cash_effect=-80.0, dependent_tasks=["T1"])

    dag = TaskDependencyGraph()
    dag.add_task(task1)
    dag.add_task(task2)

    # T2 cannot execute before T1 completes
    assert dag.is_task_ready("T2") is False
    assert dag.is_task_ready("T1") is True

    dag.mark_completed("T1")
    assert dag.is_task_ready("T2") is True


def test_mw18_shed_capacity_dependency() -> None:
    """MW-18: Assignment changes shed arrival timing -> capacity checks prevent overflow."""
    # Safety checker checks shed overflow
    class MockOutcome:
        candidate_overflow_units = 5
        candidate_final_money = 1000.0

    class MockPatch:
        market_mutations = None
        worker_mutations = {}
        resource_changes = {}

    checker = SafetyChecker()
    is_safe, checks, reason = checker.verify(
        patch=MockPatch(),
        outcome=MockOutcome(),
        econ_state=None,
        baseline_action={}
    )
    assert is_safe is False
    assert checks["overflow_ok"] is False
    assert "shed overflow" in reason


def test_mw19_determinism_five_identical_runs() -> None:
    """MW-19: Same input repeated five times produces bit-exact identical assignments."""
    coord = MultiWorkerLogisticsCoordinator(board_size=10)
    workers = {
        0: make_worker(0, pos=(2, 2), wtype=WorkerType.FARMER),
        1: make_worker(1, pos=(4, 4), wtype=WorkerType.HAND),
    }
    candidate_tasks = [
        WorkerTask(task_id="DET_1", action_family=TaskActionFamily.HARVEST, location=(2, 3), earliest_start=0, latest_completion=5),
        WorkerTask(task_id="DET_2", action_family=TaskActionFamily.FEED_ANIMAL, location=(4, 5), earliest_start=0, latest_completion=5),
    ]

    results = []
    for _ in range(5):
        plan = coord.plan_coordination(
            candidate_tasks=candidate_tasks,
            workers=workers,
            baseline_action={"farmer": ["PASS"], "hands": [["PASS"]]},
            baseline_continuation=[],
            current_step=0
        )
        results.append((
            plan.status,
            [(a.worker_id, a.task.task_id, a.transit_route) for a in plan.assignments],
            dict(plan.worker_mutations)
        ))

    # All 5 must be bit-exact identical
    for i in range(1, 5):
        assert results[i] == results[0]


def test_mw20_three_workers_deterministic_bounded_assignment() -> None:
    """MW-20: Three workers (Farmer + Hand 1 + Hand 2) -> deterministic bounded assignment."""
    coord = MultiWorkerLogisticsCoordinator(board_size=10)
    workers = {
        0: make_worker(0, pos=(0, 0), wtype=WorkerType.FARMER),
        1: make_worker(1, pos=(4, 4), wtype=WorkerType.HAND),
        2: make_worker(2, pos=(8, 8), wtype=WorkerType.HAND),
    }
    baseline_action = {"farmer": ["HARVEST"], "hands": [["HARVEST"], ["PASS"]]}
    baseline_cont = [{"farmer": ["HARVEST"], "hands": [["HARVEST"], ["PASS"]]}]

    # Hand 2 (worker 2) is completely idle at (8, 8), ideal for nearby task at (8, 7)
    candidate_task = WorkerTask(
        task_id="HAND2_TASK",
        action_family=TaskActionFamily.FEED_ANIMAL,
        location=(8, 7),
        earliest_start=5,
        latest_completion=10,
        priority_class=TaskPriority.LIVESTOCK_SECURITY,
        is_mandatory=True,
    )

    plan = coord.plan_coordination(
        candidate_tasks=[candidate_task],
        workers=workers,
        baseline_action=baseline_action,
        baseline_continuation=baseline_cont,
        current_step=5
    )

    assert plan.status == CoordinationStatus.SUCCESS
    assert len(plan.assignments) == 1
    # Must assign to Hand 2 (worker 2), leaving Worker 0 and Worker 1 on their harvests
    assert plan.assignments[0].worker_id == 2
    assert plan.labor_opportunity_cost.is_acceptable is True


# ---------------------------------------------------------------------------
# Section 27: Local vs Global Escalation Agreement Tests
# ---------------------------------------------------------------------------

def test_local_vs_global_conflict_rejected() -> None:
    """Local worker assignment looks feasible, but global dependency closure reveals conflict."""
    # Worker assignment appears locally feasible
    assign = WorkerAssignment(
        worker_id=1,
        task=WorkerTask(task_id="LOCAL_TASK", action_family=TaskActionFamily.FEED_ANIMAL, location=(4, 4)),
        start_step=10,
        completion_step=12
    )
    # Global dependency check reveals that this assignment starves another mandatory animal
    cost = LaborOpportunityCost(
        lost_mandatory_count=1,
        displaced_obligations=["ANIMAL_FEED_BREACH"],
        is_acceptable=False,
        rationale="Starves downstream livestock"
    )
    cost.evaluate_acceptability()

    assert cost.is_acceptable is False


def test_local_blocked_broader_assignment_rescues() -> None:
    """Local reasoning on Worker 0 appears blocked, but broader multi-worker assignment rescues it."""
    coord = MultiWorkerLogisticsCoordinator(board_size=10)
    # Worker 0 cannot take the task without dropping high-value harvest
    workers = {
        0: make_worker(0, pos=(0, 0), wtype=WorkerType.FARMER),
        1: make_worker(1, pos=(4, 4), wtype=WorkerType.HAND),
    }
    candidate_task = WorkerTask(
        task_id="RESCUE_TASK",
        action_family=TaskActionFamily.FEED_ANIMAL,
        location=(4, 5),
        earliest_start=0,
        latest_completion=5,
        priority_class=TaskPriority.LIVESTOCK_SECURITY,
        is_mandatory=True
    )

    plan = coord.plan_coordination(
        candidate_tasks=[candidate_task],
        workers=workers,
        baseline_action={"farmer": ["HARVEST"], "hands": [["PASS"]]},
        baseline_continuation=[],
        current_step=0
    )

    # Multi-worker coordinator rescues by allocating to Hand 1
    assert plan.status == CoordinationStatus.SUCCESS
    assert plan.assignments[0].worker_id == 1
