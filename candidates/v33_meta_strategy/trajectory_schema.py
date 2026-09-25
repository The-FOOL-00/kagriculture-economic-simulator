# SPDX-License-Identifier: MIT
"""V33 Canonical Trajectory Schema.

Standardized time-indexed trajectory representation preserving exact tick
timing, action sequence, market orders, worker states, and economic observables.
"""

from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional


@dataclass
class StepRecord:
    step: int
    cash: float
    land_count: int
    worker_count: int
    worker_states: List[Dict[str, Any]]
    crops: Dict[str, int]
    livestock: Dict[str, int]
    inventory: Dict[str, int]
    market_prices: Dict[str, float]
    action: Dict[str, Any]
    market_orders: List[List[Any]]
    opponent_observable: Dict[str, Any]
    events: List[str] = field(default_factory=list)


@dataclass
class NormalizedTrajectory:
    episode_id: str
    seed: int
    seat: int
    agent_id: str
    opponent_id: str
    terminal_cash: float
    opponent_cash: float
    outcome: str  # "W", "L", "T"
    steps: List[StepRecord] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> NormalizedTrajectory:
        steps_raw = data.pop("steps", [])
        steps = [StepRecord(**s) if isinstance(s, dict) else s for s in steps_raw]
        return cls(steps=steps, **data)
