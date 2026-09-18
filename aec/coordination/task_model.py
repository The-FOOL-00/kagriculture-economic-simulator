# SPDX-License-Identifier: MIT
"""AEC Phase 003: Worker Task Model and Dependency Graph (§6, §10, §17).

Represents discrete units of physical/economic work, task priorities,
resource transformations, and dependency constraints between tasks.
"""

from __future__ import annotations

import copy
from collections import defaultdict, deque
from dataclasses import dataclass, field
from enum import Enum, IntEnum
from typing import Any, Dict, List, Optional, Set, Tuple

from aec.coordination.worker_model import WorkerCapability


class TaskPriority(IntEnum):
    """Authoritative task priority classes (§10).
    
    Higher integer represents strictly higher priority during contention resolution.
    """
    HARD_OBLIGATION = 1000
    TERMINAL_OBLIGATION = 900
    LIVESTOCK_SECURITY = 800
    RESOURCE_SECURITY = 700
    HIGH_VALUE_HARVEST = 600
    SCHEDULED_PRODUCTION = 500
    MARKET_ACTION = 400
    OPPORTUNISTIC_TASK = 100


class TaskActionFamily(str, Enum):
    """Action category representing physical or market task types."""
    FEED_ANIMAL = "FEED_ANIMAL"
    PICKUP_RESOURCE = "PICKUP_RESOURCE"
    DELIVER_RESOURCE = "DELIVER_RESOURCE"
    DROP_RESOURCE = "DROP_RESOURCE"
    HARVEST = "HARVEST"
    WATER = "WATER"
    PLANT = "PLANT"
    DIG_WEED = "DIG_WEED"
    CARE = "CARE"
    FERTILIZE = "FERTILIZE"
    BUILD = "BUILD"
    MARKET_BUY = "MARKET_BUY"
    MARKET_SELL = "MARKET_SELL"
    WAIT = "WAIT"


@dataclass
class WorkerTask:
    """Explicit, discrete work item with temporal, spatial, and resource bounds (§6)."""
    task_id: str
    action_family: TaskActionFamily
    location: Tuple[int, int]
    earliest_start: int = 0
    latest_completion: int = 720
    required_capabilities: Set[WorkerCapability] = field(
        default_factory=lambda: {WorkerCapability.MOVE}
    )
    duration: int = 1                     # Action execution duration on site (excluding transit)
    resource_inputs: Dict[str, int] = field(default_factory=dict)
    resource_outputs: Dict[str, int] = field(default_factory=dict)
    cash_effect: float = 0.0
    dependent_tasks: List[str] = field(default_factory=list)  # Prerequisites
    terminal_relevance: bool = False
    priority_class: TaskPriority = TaskPriority.SCHEDULED_PRODUCTION
    is_mandatory: bool = False
    target_commodity: Optional[str] = None
    target_entity: Optional[str] = None
    target_worker_preference: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_obligation(self) -> bool:
        return self.is_mandatory or self.priority_class in (
            TaskPriority.HARD_OBLIGATION,
            TaskPriority.TERMINAL_OBLIGATION,
            TaskPriority.LIVESTOCK_SECURITY,
        )

    def is_feasible_at(self, step: int) -> bool:
        return self.earliest_start <= step <= self.latest_completion

    def copy(self) -> WorkerTask:
        return WorkerTask(
            task_id=self.task_id,
            action_family=self.action_family,
            location=self.location,
            earliest_start=self.earliest_start,
            latest_completion=self.latest_completion,
            required_capabilities=set(self.required_capabilities),
            duration=self.duration,
            resource_inputs=dict(self.resource_inputs),
            resource_outputs=dict(self.resource_outputs),
            cash_effect=self.cash_effect,
            dependent_tasks=list(self.dependent_tasks),
            terminal_relevance=self.terminal_relevance,
            priority_class=self.priority_class,
            is_mandatory=self.is_mandatory,
            target_commodity=self.target_commodity,
            target_entity=self.target_entity,
            target_worker_preference=self.target_worker_preference,
            metadata=dict(self.metadata),
        )


class TaskDependencyGraph:
    """Directed Acyclic Graph of worker tasks and causal dependencies (§17)."""

    def __init__(self) -> None:
        self.tasks: Dict[str, WorkerTask] = {}
        self.predecessors: Dict[str, Set[str]] = defaultdict(set)
        self.successors: Dict[str, Set[str]] = defaultdict(set)
        self.completed_tasks: Set[str] = set()

    def add_task(self, task: WorkerTask) -> None:
        self.tasks[task.task_id] = task
        for dep in task.dependent_tasks:
            self.predecessors[task.task_id].add(dep)
            self.successors[dep].add(task.task_id)

    def add_dependency(self, prerequisite_id: str, dependent_id: str) -> None:
        if dependent_id in self.tasks and prerequisite_id not in self.tasks[dependent_id].dependent_tasks:
            self.tasks[dependent_id].dependent_tasks.append(prerequisite_id)
        self.predecessors[dependent_id].add(prerequisite_id)
        self.successors[prerequisite_id].add(dependent_id)

    def mark_completed(self, task_id: str) -> None:
        self.completed_tasks.add(task_id)

    def is_task_ready(self, task_id: str) -> bool:
        if task_id in self.completed_tasks:
            return False
        preds = self.predecessors.get(task_id, set())
        return preds.issubset(self.completed_tasks)

    def get_ready_tasks(self, step: Optional[int] = None) -> List[WorkerTask]:
        ready: List[WorkerTask] = []
        for tid, task in self.tasks.items():
            if self.is_task_ready(tid):
                if step is None or (task.earliest_start <= step <= task.latest_completion):
                    ready.append(task)
        # Sort by priority descending
        ready.sort(key=lambda t: (-t.priority_class.value, t.earliest_start))
        return ready

    def topological_sort(self) -> List[WorkerTask]:
        """Compute valid deterministic topological execution sequence."""
        in_degree = {tid: len(self.predecessors[tid]) for tid in self.tasks}
        queue: deque = deque(sorted([tid for tid, deg in in_degree.items() if deg == 0]))
        result: List[WorkerTask] = []

        while queue:
            tid = queue.popleft()
            result.append(self.tasks[tid])
            for succ in sorted(self.successors[tid]):
                in_degree[succ] -= 1
                if in_degree[succ] == 0:
                    queue.append(succ)

        if len(result) != len(self.tasks):
            raise ValueError("Cycle detected in TaskDependencyGraph")

        return result
