# SPDX-License-Identifier: MIT
"""AEC Phase 003: Multi-Worker Logistics Coordinator (§7, §8, §9, §12, §14, §15, §16, §20).

The deterministic, dependency-aware, exact-simulator-compatible multi-worker logistics
compiler that optimally allocates tasks across available workers without spatial collisions,
resource conflicts, temporal conflicts, or labor cannibalization.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

from aec.config import BOARD_SIZE, MOVES, SHED_TILES
from aec.coordination.assignment import (
    DisplacementOutcome,
    LaborOpportunityCost,
    WorkerAssignment,
    WorkerSchedule,
    compute_marginal_labor_cost,
)
from aec.coordination.dominance import MultiWorkerDominancePruner
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
    CANONICAL_DIRECTIONS,
    SpacetimeReservationTable,
    compute_next_pos,
    deterministic_find_path,
    extract_worker_trajectory,
    is_within_bounds,
    manhattan,
)


class CoordinationStatus(str, Enum):
    """Authoritative outcome status of multi-worker logistics coordination."""
    SUCCESS = "SUCCESS"
    ABSTAIN_CONFLICT = "ABSTAIN_CONFLICT"
    ABSTAIN_LABOR_CANNIBALIZATION = "ABSTAIN_LABOR_CANNIBALIZATION"
    ABSTAIN_ROUTING_INFEASIBLE = "ABSTAIN_ROUTING_INFEASIBLE"
    ABSTAIN_RESOURCE_CONTENTION = "ABSTAIN_RESOURCE_CONTENTION"
    ABSTAIN_ILLEGAL_HANDOFF = "ABSTAIN_ILLEGAL_HANDOFF"
    ABSTAIN_DEADLINE_BREACH = "ABSTAIN_DEADLINE_BREACH"
    ABSTAIN_NO_CANDIDATE = "ABSTAIN_NO_CANDIDATE"


@dataclass
class WorkerCoordinationPlan:
    """Formal output certificate of multi-worker logistics coordination (§5, §7)."""
    status: CoordinationStatus
    assignments: List[WorkerAssignment] = field(default_factory=list)
    labor_opportunity_cost: LaborOpportunityCost = field(default_factory=LaborOpportunityCost)
    worker_mutations: Dict[int, List[str]] = field(default_factory=dict)
    rejection_reason: Optional[str] = None
    affected_workers: Set[int] = field(default_factory=set)
    reservation_table: Optional[SpacetimeReservationTable] = None

    @property
    def is_executable(self) -> bool:
        return self.status == CoordinationStatus.SUCCESS and self.labor_opportunity_cost.is_acceptable


class MultiWorkerLogisticsCoordinator:
    """Deterministic Multi-Worker Logistics Compiler (§7, §8, §9, §12, §14, §15, §16, §20)."""

    def __init__(self, board_size: int = BOARD_SIZE) -> None:
        self.board_size = board_size

    def extract_baseline_tasks(
        self,
        workers: Dict[int, WorkerState],
        baseline_action: Dict[str, Any],
        baseline_continuation: List[Dict[str, Any]],
        current_step: int
    ) -> List[WorkerTask]:
        """Extract baseline duties across all active workers to evaluate displacement opportunity cost (§9)."""
        tasks: List[WorkerTask] = []
        full_seq = [baseline_action] + list(baseline_continuation)

        for wid, w_state in workers.items():
            curr_pos = w_state.position
            for step_offset, act in enumerate(full_seq):
                step = current_step + step_offset
                if wid == 0:
                    cmd_list = act.get("farmer", ["PASS"]) or ["PASS"]
                else:
                    hands = act.get("hands", []) or []
                    h_idx = wid - 1
                    cmd_list = hands[h_idx] if h_idx < len(hands) else ["PASS"]

                cmd = cmd_list[0] if cmd_list else "PASS"

                if cmd in MOVES:
                    curr_pos = compute_next_pos(curr_pos, cmd, self.board_size)
                elif cmd in ("HARVEST", "WATER", "PLANT", "FEED", "CARE", "FERTILIZE", "DIG"):
                    # Map to discrete WorkerTask
                    family = {
                        "HARVEST": TaskActionFamily.HARVEST,
                        "WATER": TaskActionFamily.WATER,
                        "PLANT": TaskActionFamily.PLANT,
                        "FEED": TaskActionFamily.FEED_ANIMAL,
                        "CARE": TaskActionFamily.CARE,
                        "FERTILIZE": TaskActionFamily.FERTILIZE,
                        "DIG": TaskActionFamily.DIG_WEED,
                    }.get(cmd, TaskActionFamily.WAIT)

                    # Priority derivation
                    if family == TaskActionFamily.FEED_ANIMAL:
                        pri = TaskPriority.LIVESTOCK_SECURITY
                        is_mand = True
                    elif family == TaskActionFamily.HARVEST:
                        pri = TaskPriority.HIGH_VALUE_HARVEST
                        is_mand = True
                    elif family in (TaskActionFamily.WATER, TaskActionFamily.PLANT):
                        pri = TaskPriority.SCHEDULED_PRODUCTION
                        is_mand = False
                    else:
                        pri = TaskPriority.OPPORTUNISTIC_TASK
                        is_mand = False

                    task = WorkerTask(
                        task_id=f"BASE_{wid}_{step}_{family.value}",
                        action_family=family,
                        location=curr_pos,
                        earliest_start=step,
                        latest_completion=step + 2,
                        priority_class=pri,
                        is_mandatory=is_mand,
                        target_worker_preference=wid,
                        cash_effect=50.0 if family == TaskActionFamily.HARVEST else 0.0,
                    )
                    tasks.append(task)

        return tasks

    def plan_coordination(
        self,
        candidate_tasks: List[WorkerTask],
        workers: Dict[int, WorkerState],
        baseline_action: Dict[str, Any],
        baseline_continuation: List[Dict[str, Any]],
        current_step: int,
        dependency_graph: Optional[TaskDependencyGraph] = None
    ) -> WorkerCoordinationPlan:
        """Deterministically solve multi-worker task allocation, routing, and baseline preservation (§7, §8)."""
        if not candidate_tasks:
            return WorkerCoordinationPlan(
                status=CoordinationStatus.ABSTAIN_NO_CANDIDATE,
                rejection_reason="No candidate tasks provided"
            )

        baseline_tasks = self.extract_baseline_tasks(
            workers=workers,
            baseline_action=baseline_action,
            baseline_continuation=baseline_continuation,
            current_step=current_step
        )

        active_worker_ids = sorted(workers.keys())

        # Check for illegal direct handoff specifications (§13, §37)
        # Direct unit-to-unit handoff is physically non-existent in sim.hpp
        for t in candidate_tasks:
            if t.metadata.get("direct_unit_handoff", False):
                return WorkerCoordinationPlan(
                    status=CoordinationStatus.ABSTAIN_ILLEGAL_HANDOFF,
                    rejection_reason="Direct unit-to-unit handoff is physically illegal in simulator; must route via shed"
                )

        candidate_evaluations: List[Tuple[List[WorkerAssignment], LaborOpportunityCost]] = []

        # Enumerate bounded assignment alternatives across active workers (§7, §20)
        # For a candidate task set (e.g. [PICKUP, FEED]), try allocating to available workers
        for primary_wid in active_worker_ids:
            assignments: List[WorkerAssignment] = []
            res_table = SpacetimeReservationTable(self.board_size)
            all_valid = True
            inval_reason: Optional[str] = None

            # 1. First reserve baseline trajectories of workers NOT involved in candidate tasks
            for other_wid in active_worker_ids:
                if other_wid == primary_wid:
                    continue
                # Extract baseline path for other_wid
                other_traj = extract_worker_trajectory(
                    action_sequence=[baseline_action] + baseline_continuation,
                    start_pos=workers[other_wid].position,
                    worker_id=other_wid,
                    board_size=self.board_size
                )
                for step_offset, (pos, cmd) in enumerate(other_traj):
                    step_t = current_step + step_offset
                    if not res_table.reserve_vertex(step_t, pos, other_wid):
                        # Potential baseline-on-baseline collision
                        pass

            # 2. Route the primary worker through candidate tasks in topological order
            worker_curr_pos = workers[primary_wid].position
            worker_curr_step = current_step

            for task in candidate_tasks:
                # Check capability
                for req_cap in task.required_capabilities:
                    if not workers[primary_wid].has_capability(req_cap):
                        all_valid = False
                        inval_reason = f"Worker {primary_wid} lacks capability {req_cap.value}"
                        break
                if not all_valid:
                    break

                # Pathfind to task location
                path_to_loc = deterministic_find_path(
                    start=worker_curr_pos,
                    target=task.location,
                    start_step=worker_curr_step,
                    reservations=res_table,
                    worker_id=primary_wid,
                    max_steps=20,
                    board_size=self.board_size,
                    allow_pass=True
                )

                if path_to_loc is None:
                    all_valid = False
                    inval_reason = f"Routing failed for worker {primary_wid} to {task.location} (collision or bounds)"
                    break

                # Trace trajectory and check deadline
                arrival_step = worker_curr_step + len(path_to_loc)
                completion_step = arrival_step + task.duration

                if completion_step > task.latest_completion:
                    all_valid = False
                    inval_reason = f"Task {task.task_id} breaches deadline {task.latest_completion} (completion at {completion_step})"
                    break

                # Check task and resource exclusivity (§11)
                for s in range(arrival_step, completion_step + 1):
                    if not res_table.reserve_task(s, task.task_id, primary_wid):
                        all_valid = False
                        inval_reason = f"Task {task.task_id} contention with another worker"
                        break
                    if task.target_commodity:
                        res_key = f"{task.target_commodity}_{task.location}"
                        if not res_table.reserve_resource(s, res_key, primary_wid):
                            all_valid = False
                            inval_reason = f"Resource {res_key} contention/double allocation"
                            break
                if not all_valid:
                    break

                # Derive action command on arrival
                action_op = self._task_family_to_op(task.action_family)
                full_actions = list(path_to_loc) + [action_op] * task.duration

                # Trace trajectory points
                traj_pts: List[Tuple[int, Tuple[int, int]]] = []
                t_pos = worker_curr_pos
                t_step = worker_curr_step
                traj_pts.append((t_step, t_pos))
                for m in path_to_loc:
                    t_step += 1
                    t_pos = compute_next_pos(t_pos, m, self.board_size)
                    traj_pts.append((t_step, t_pos))
                for _ in range(task.duration):
                    t_step += 1
                    traj_pts.append((t_step, t_pos))

                # Reserve in table
                if not res_table.reserve_trajectory(traj_pts, primary_wid):
                    all_valid = False
                    inval_reason = f"Trajectory collision for worker {primary_wid}"
                    break

                assignment = WorkerAssignment(
                    worker_id=primary_wid,
                    task=task,
                    start_step=worker_curr_step,
                    completion_step=completion_step,
                    transit_route=path_to_loc,
                    action_cmd=action_op,
                    full_action_sequence=full_actions,
                    trajectory_points=traj_pts,
                    is_valid=True
                )
                assignments.append(assignment)
                worker_curr_pos = task.location
                worker_curr_step = completion_step

            if not all_valid:
                continue

            # 3. Compute marginal labor opportunity cost for this candidate assignment (§8, §21)
            labor_cost = compute_marginal_labor_cost(
                baseline_tasks=baseline_tasks,
                proposed_assignments=assignments,
                active_workers=set(active_worker_ids)
            )

            # Accept candidate if it doesn't cause unacceptable mandatory obligation loss
            if labor_cost.is_acceptable:
                candidate_evaluations.append((assignments, labor_cost))

        if not candidate_evaluations:
            return WorkerCoordinationPlan(
                status=CoordinationStatus.ABSTAIN_LABOR_CANNIBALIZATION,
                rejection_reason="No candidate assignment could preserve mandatory baseline obligations without conflict"
            )

        # 4. Multi-Worker Dominance Pruning (§22)
        survivors = MultiWorkerDominancePruner.prune(candidate_evaluations)
        if not survivors:
            survivors = candidate_evaluations

        # Pick best surviving plan (deterministic: first survivor)
        best_assignments, best_cost = survivors[0]

        # 5. Build worker mutations for immediate turn
        worker_mutations: Dict[int, List[str]] = {}
        affected: Set[int] = set()
        for a in best_assignments:
            if a.full_action_sequence:
                worker_mutations[a.worker_id] = [a.full_action_sequence[0]]
                affected.add(a.worker_id)

        return WorkerCoordinationPlan(
            status=CoordinationStatus.SUCCESS,
            assignments=best_assignments,
            labor_opportunity_cost=best_cost,
            worker_mutations=worker_mutations,
            affected_workers=affected
        )

    def _task_family_to_op(self, family: TaskActionFamily) -> str:
        mapping = {
            TaskActionFamily.FEED_ANIMAL: "FEED",
            TaskActionFamily.PICKUP_RESOURCE: "PICKUP",
            TaskActionFamily.DROP_RESOURCE: "DROP",
            TaskActionFamily.DELIVER_RESOURCE: "DROP",
            TaskActionFamily.HARVEST: "HARVEST",
            TaskActionFamily.WATER: "WATER",
            TaskActionFamily.PLANT: "PLANT",
            TaskActionFamily.DIG_WEED: "DIG",
            TaskActionFamily.CARE: "CARE",
            TaskActionFamily.FERTILIZE: "FERTILIZE",
            TaskActionFamily.BUILD: "BUILD_COOP",
            TaskActionFamily.WAIT: "PASS",
        }
        return mapping.get(family, "PASS")
