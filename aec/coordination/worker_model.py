# SPDX-License-Identifier: MIT
"""AEC Phase 003: Worker State and Capability Model (§5, §6, §13).

Defines formal worker models derived directly from simulator ground-truth physics:
Farmer (unit 0) and hired hands (units 1..N-1), exact simulator capabilities,
inventories, positions, and operational constraints.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from enum import Enum, IntEnum
from typing import Any, Dict, List, Optional, Set, Tuple

from aec.config import BOARD_SIZE, SHED_TILES


class WorkerType(str, Enum):
    """Authoritative worker entity classification."""
    FARMER = "FARMER"
    HAND = "HAND"


class WorkerCapability(str, Enum):
    """Exact operational capabilities derived from simulator action space (§5)."""
    PASS = "PASS"
    MOVE = "MOVE"
    PICKUP = "PICKUP"
    DROP = "DROP"
    PLACE = "PLACE"
    PLANT = "PLANT"
    WATER = "WATER"
    HARVEST = "HARVEST"
    FERTILIZE = "FERTILIZE"
    DIG = "DIG"
    BUILD_COOP = "BUILD_COOP"
    BUILD_PASTURE = "BUILD_PASTURE"
    FEED = "FEED"
    COLLECT_FERTILIZER = "COLLECT_FERTILIZER"
    CARE = "CARE"


# Full capability set available to any Kagriculture unit in sim.hpp
STANDARD_WORKER_CAPABILITIES: Set[WorkerCapability] = {
    WorkerCapability.PASS,
    WorkerCapability.MOVE,
    WorkerCapability.PICKUP,
    WorkerCapability.DROP,
    WorkerCapability.PLACE,
    WorkerCapability.PLANT,
    WorkerCapability.WATER,
    WorkerCapability.HARVEST,
    WorkerCapability.FERTILIZE,
    WorkerCapability.DIG,
    WorkerCapability.BUILD_COOP,
    WorkerCapability.BUILD_PASTURE,
    WorkerCapability.FEED,
    WorkerCapability.COLLECT_FERTILIZER,
    WorkerCapability.CARE,
}


@dataclass
class WorkerState:
    """Formal representation of a single worker entity and physical operational state (§5)."""
    worker_id: int
    worker_type: WorkerType
    position: Tuple[int, int]
    carried_inventory: Dict[str, int] = field(default_factory=dict)
    availability_turn: int = 0
    current_task: Optional[str] = None
    target_pos: Optional[Tuple[int, int]] = None
    capabilities: Set[WorkerCapability] = field(default_factory=lambda: set(STANDARD_WORKER_CAPABILITIES))
    assigned_obligations: List[str] = field(default_factory=list)
    movement_state: str = "IDLE"  # "IDLE", "TRANSIT", "BUSY"
    is_active: bool = True

    @property
    def total_cargo(self) -> int:
        """Total number of items carried by this unit."""
        return sum(self.carried_inventory.values())

    @property
    def is_farmer(self) -> bool:
        return self.worker_id == 0 and self.worker_type == WorkerType.FARMER

    def has_capability(self, capability: WorkerCapability) -> bool:
        return capability in self.capabilities

    def can_carry(self, item: str, quantity: int = 1) -> bool:
        """Kagriculture simulator units have unbounded per-unit capacity (bounded only by 100 shed cap)."""
        return quantity >= 0

    def copy(self) -> WorkerState:
        return WorkerState(
            worker_id=self.worker_id,
            worker_type=self.worker_type,
            position=self.position,
            carried_inventory=dict(self.carried_inventory),
            availability_turn=self.availability_turn,
            current_task=self.current_task,
            target_pos=self.target_pos,
            capabilities=set(self.capabilities),
            assigned_obligations=list(self.assigned_obligations),
            movement_state=self.movement_state,
            is_active=self.is_active,
        )


def extract_farm_workers(
    farm_state_or_econ: Any,
    current_turn: int = 0
) -> Dict[int, WorkerState]:
    """Extract authoritative WorkerState objects from game state or EconomicState (§5)."""
    workers: Dict[int, WorkerState] = {}

    # Case 1: EconomicState
    if hasattr(farm_state_or_econ, "workers") and hasattr(farm_state_or_econ.workers, "workers"):
        w_collection = farm_state_or_econ.workers.workers
        if isinstance(w_collection, dict):
            w_items = list(w_collection.items())
        else:
            w_items = [(getattr(w, "worker_id", idx), w) for idx, w in enumerate(w_collection)]
        for wid, w in w_items:
            wtype = WorkerType.FARMER if wid == 0 else WorkerType.HAND
            workers[wid] = WorkerState(
                worker_id=wid,
                worker_type=wtype,
                position=getattr(w, "position", (4, 4)),
                carried_inventory=dict(getattr(w, "carried_inventory", {})),
                availability_turn=current_turn,
                current_task=getattr(w, "current_task", None),
                target_pos=getattr(w, "target_pos", None),
                assigned_obligations=list(getattr(w, "assigned_obligations", [])),
                is_active=True,
            )
        return workers

    # Case 2: FarmState object (from golden_v1 / worker_scheduler)
    if hasattr(farm_state_or_econ, "farmer_pos"):
        # Unit 0: Farmer
        farmer_pos = farm_state_or_econ.farmer_pos
        farmer_inv = farm_state_or_econ.inventories[0] if (
            hasattr(farm_state_or_econ, "inventories") and len(farm_state_or_econ.inventories) > 0
        ) else {}
        workers[0] = WorkerState(
            worker_id=0,
            worker_type=WorkerType.FARMER,
            position=farmer_pos,
            carried_inventory=dict(farmer_inv),
            availability_turn=current_turn,
        )

        # Units 1..N-1: Hands
        hands = getattr(farm_state_or_econ, "hands", []) or []
        inventories = getattr(farm_state_or_econ, "inventories", []) or []
        for i, h_pos in enumerate(hands):
            wid = i + 1
            h_inv = inventories[wid] if wid < len(inventories) else {}
            workers[wid] = WorkerState(
                worker_id=wid,
                worker_type=WorkerType.HAND,
                position=h_pos,
                carried_inventory=dict(h_inv),
                availability_turn=current_turn,
            )
        return workers

    # Fallback: single farmer at default center
    workers[0] = WorkerState(
        worker_id=0,
        worker_type=WorkerType.FARMER,
        position=(4, 4),
        availability_turn=current_turn,
    )
    return workers
