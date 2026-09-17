# SPDX-License-Identifier: MIT
"""Worker State Representation within Economic IR."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from aec.config import SHED_TILES


def manhattan_distance(p1: Tuple[int, int], p2: Tuple[int, int]) -> int:
    return abs(p1[0] - p2[0]) + abs(p1[1] - p2[1])


def min_distance_to_shed(pos: Tuple[int, int]) -> int:
    return min(manhattan_distance(pos, s) for s in SHED_TILES)


@dataclass
class WorkerEntity:
    """Detailed economic model of a single worker (farmer or hired hand)."""
    worker_id: int
    position: Tuple[int, int]
    task: str = "PASS"
    target: Optional[Tuple[int, int]] = None
    eta: int = 0
    cargo: Dict[str, int] = field(default_factory=dict)
    expected_output: Dict[str, int] = field(default_factory=dict)
    deposit_path_len: int = 0
    available_slack_steps: int = 0
    marginal_opportunity_value: float = 0.0

    @property
    def total_cargo_units(self) -> int:
        return sum(self.cargo.values())

    @property
    def is_carrying_cargo(self) -> bool:
        return self.total_cargo_units > 0


@dataclass
class WorkerState:
    """Aggregate state of all workers on the farm."""
    workers: List[WorkerEntity] = field(default_factory=list)

    @property
    def total_workers(self) -> int:
        return len(self.workers)

    @property
    def total_cargo_carried(self) -> int:
        return sum(w.total_cargo_units for w in self.workers)

    def get_worker(self, worker_id: int) -> Optional[WorkerEntity]:
        for w in self.workers:
            if w.worker_id == worker_id:
                return w
        return None
