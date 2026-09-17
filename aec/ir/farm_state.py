# SPDX-License-Identifier: MIT
"""Farm State Representation within Economic IR."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from aec.config import SHED_CAPACITY


@dataclass
class PipelineItem:
    """A crop or animal currently growing/producing on the farm."""
    item_type: str  # "PLANT" or "ANIMAL"
    subtype: str    # "STRAWBERRY", "MELON", "COW", "SHEEP", etc.
    position: Tuple[int, int]
    days_to_next_yield: int
    yield_quantity: int
    is_ongoing: bool
    requires_input: bool = False  # e.g., animal requires feed


@dataclass
class FarmState:
    """Complete economic state of our own farm."""
    cash: float = 0.0
    carried_inventory: Dict[str, int] = field(default_factory=dict)
    shed_inventory: Dict[str, int] = field(default_factory=dict)
    capacity: int = SHED_CAPACITY
    seeds: Dict[str, int] = field(default_factory=dict)
    production_pipeline: List[PipelineItem] = field(default_factory=list)
    expected_harvests: Dict[str, int] = field(default_factory=dict)
    expected_sales: Dict[str, int] = field(default_factory=dict)
    expected_purchases: Dict[str, int] = field(default_factory=dict)
    obligations: Dict[str, int] = field(default_factory=dict)
    terminal_stock: Dict[str, int] = field(default_factory=dict)
    unlocked_quadrants: List[str] = field(default_factory=lambda: ["NW"])
    tiles: List[List[Any]] = field(default_factory=list)

    @property
    def shed_total_units(self) -> int:
        return sum(self.shed_inventory.values())

    @property
    def shed_free_space(self) -> int:
        return max(0, self.capacity - self.shed_total_units)

    @property
    def total_carried_units(self) -> int:
        return sum(self.carried_inventory.values())

    @property
    def total_physical_inventory(self) -> int:
        return self.shed_total_units + self.total_carried_units

    def get_shed_qty(self, item: str) -> int:
        return self.shed_inventory.get(item, 0)
