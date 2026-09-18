# SPDX-License-Identifier: MIT
"""AEC Phase 003: Worker Assignment and Marginal Labor Opportunity Cost (§7, §8, §9, §21).

Models assignments of workers to tasks, timeline schedules, and formal
marginal labor opportunity cost derivation without arbitrary hourly wages.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

from aec.coordination.task_model import TaskPriority, WorkerTask


class DisplacementOutcome(str, Enum):
    """Categorical consequence to an existing baseline task when labor is reallocated (§8, §21)."""
    PRESERVED_BY_SELF = "PRESERVED_BY_SELF"        # Assigned worker still executes task on time
    ABSORBED_BY_PEER = "ABSORBED_BY_PEER"          # Another worker assumes ownership and executes
    DELAYED_FEASIBLE = "DELAYED_FEASIBLE"          # Executed later by worker, within deadline
    SUPERSEDED_OPTIONAL = "SUPERSEDED_OPTIONAL"    # Low-priority/optional task replaced by higher value
    CANCELLED = "CANCELLED"                        # Dropped without execution
    INFEASIBLE = "INFEASIBLE"                      # Deadline breached or prerequisites unavailable


@dataclass
class WorkerAssignment:
    """Concrete mapping of a specific worker to a task with spatio-temporal route (§7)."""
    worker_id: int
    task: WorkerTask
    start_step: int
    completion_step: int
    transit_route: List[str] = field(default_factory=list)
    action_cmd: str = "PASS"
    full_action_sequence: List[str] = field(default_factory=list)
    trajectory_points: List[Tuple[int, Tuple[int, int]]] = field(default_factory=list)
    is_valid: bool = True
    invalidation_reason: Optional[str] = None

    @property
    def total_steps(self) -> int:
        return len(self.full_action_sequence)


@dataclass
class WorkerSchedule:
    """Timeline schedule of assignments and route states for a single worker (§7, §9)."""
    worker_id: int
    assignments: List[WorkerAssignment] = field(default_factory=list)
    start_position: Tuple[int, int] = (4, 4)
    active_steps: Set[int] = field(default_factory=set)

    def is_worker_available(self, start_step: int, end_step: int) -> bool:
        """Check if worker has no assigned duties in [start_step, end_step]."""
        for s in range(start_step, end_step + 1):
            if s in self.active_steps:
                return False
        return True

    def add_assignment(self, assignment: WorkerAssignment) -> None:
        self.assignments.append(assignment)
        for s in range(assignment.start_step, assignment.completion_step + 1):
            self.active_steps.add(s)


@dataclass
class LaborOpportunityCost:
    """Formal marginal labor opportunity cost accounting for baseline displacement (§8, §21).
    
    CRITICAL ARCHITECTURAL PRINCIPLE:
    Derived directly from the actual baseline schedule and downstream obligations,
    NEVER from an arbitrary constant shadow-price (such as hire_cost / 24).
    """
    displaced_tasks: Dict[str, DisplacementOutcome] = field(default_factory=dict)
    displaced_value_est: float = 0.0
    displaced_obligations: List[str] = field(default_factory=list)
    absorbed_tasks: List[str] = field(default_factory=list)
    delayed_tasks: List[str] = field(default_factory=list)
    lost_mandatory_count: int = 0
    is_acceptable: bool = True
    rationale: str = "No baseline displacement"

    def evaluate_acceptability(self) -> bool:
        """Acceptable only if zero mandatory obligations are cancelled or breached (§8)."""
        if self.lost_mandatory_count > 0:
            self.is_acceptable = False
            self.rationale = f"Unacceptable: {self.lost_mandatory_count} mandatory obligations lost"
            return False
        for tid, outcome in self.displaced_tasks.items():
            if outcome in (DisplacementOutcome.CANCELLED, DisplacementOutcome.INFEASIBLE):
                # Only optional tasks may be cancelled
                pass
        self.is_acceptable = True
        return True


def compute_marginal_labor_cost(
    baseline_tasks: List[WorkerTask],
    proposed_assignments: List[WorkerAssignment],
    active_workers: Set[int]
) -> LaborOpportunityCost:
    """Compute exact marginal labor consequence of candidate assignment on baseline schedule (§8, §21).
    
    Traces:
    baseline worker task
            ↓
    candidate task replaces it
            ↓
    what baseline obligations move?
            ↓
    what value is displaced?
            ↓
    can another worker absorb the task?
            ↓
    does downstream schedule remain feasible?
    """
    cost = LaborOpportunityCost()
    
    # Map which tasks are executed in the proposed plan
    executed_task_ids: Dict[str, int] = {
        a.task.task_id: a.worker_id for a in proposed_assignments if a.is_valid
    }

    # Workers diverted to candidate tasks
    diverted_workers: Set[int] = {
        a.worker_id for a in proposed_assignments if a.is_valid
    }

    for b_task in baseline_tasks:
        tid = b_task.task_id
        original_wid = b_task.target_worker_preference

        # Case 1: original worker is NOT diverted; baseline task is preserved by original worker
        if original_wid is not None and original_wid not in diverted_workers:
            cost.displaced_tasks[tid] = DisplacementOutcome.PRESERVED_BY_SELF
            continue

        # Case 2: task is explicitly executed in proposed plan
        if tid in executed_task_ids:
            new_wid = executed_task_ids[tid]
            if original_wid is None or new_wid == original_wid:
                cost.displaced_tasks[tid] = DisplacementOutcome.PRESERVED_BY_SELF
            else:
                cost.displaced_tasks[tid] = DisplacementOutcome.ABSORBED_BY_PEER
                cost.absorbed_tasks.append(tid)
        else:
            # Case 3: original worker was diverted and task was not executed in proposed plan
            if b_task.is_mandatory:
                cost.displaced_tasks[tid] = DisplacementOutcome.INFEASIBLE
                cost.lost_mandatory_count += 1
                cost.displaced_obligations.append(tid)
                cost.displaced_value_est += max(100.0, b_task.cash_effect)
            elif b_task.priority_class == TaskPriority.OPPORTUNISTIC_TASK:
                cost.displaced_tasks[tid] = DisplacementOutcome.SUPERSEDED_OPTIONAL
                cost.displaced_value_est += b_task.cash_effect
            else:
                cost.displaced_tasks[tid] = DisplacementOutcome.CANCELLED
                cost.displaced_value_est += b_task.cash_effect

    cost.evaluate_acceptability()
    return cost
