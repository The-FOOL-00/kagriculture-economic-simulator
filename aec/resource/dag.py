# SPDX-License-Identifier: MIT
"""AEC-RESOURCE: Formal Time-Expanded Resource DAG (§2, §3, §4, §7).

Implements temporal resource nodes, transformation edges, obligations,
reservations, and conservation law validation.
"""

from __future__ import annotations

import copy
from collections import defaultdict, deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

from aec.config import SHED_CAPACITY


class ResourceLocationType(str, Enum):
    SHED = "SHED"
    HAND = "HAND"
    TILE = "TILE"
    MARKET = "MARKET"
    SEEDS = "SEEDS"


class ObligationType(str, Enum):
    LIVESTOCK_FEED = "LIVESTOCK_FEED"
    COMMITTED_SALE = "COMMITTED_SALE"
    PLANNED_SEED = "PLANNED_SEED"
    SHED_DELIVERY = "SHED_DELIVERY"
    TERMINAL_LIQUIDATION = "TERMINAL_LIQUIDATION"


@dataclass
class ResourceNode:
    """Represents a discrete temporal resource stock at a specific location and turn (§4)."""
    node_id: str
    commodity: str                      # e.g. "WHEAT", "MILK", "EGG", "CARROT", "MONEY"
    quantity: int                       # Units available
    unit: str = "UNITS"                 # "UNITS" or "DOLLARS"
    turn: int = 0                       # Timestamp / turn
    location: str = "SHED"              # "SHED", "HAND_0", "HAND_1", "TILE_x_y", "SEEDS", "MARKET"
    capacity_domain: str = "SHED"       # "SHED", "HAND", "NONE"
    provenance: str = "INITIAL"         # "INITIAL", "PURCHASED", "HARVESTED", "PRODUCED", "TRANSFERRED"
    reservation_state: str = "AVAILABLE"# "AVAILABLE", "RESERVED", "COMMITTED", "CONSUMED"
    perishability_turns: Optional[int] = None
    availability_turn: int = 0
    terminal_usability: bool = True

    @property
    def is_available(self) -> bool:
        return self.reservation_state in ("AVAILABLE", "RESERVED") and self.quantity > 0


@dataclass
class ResourceEdge:
    """Represents a causal transformation, movement, or consumption action (§4)."""
    edge_id: str
    source_node_ids: List[str]          # Inflow node IDs consumed or transferred
    dest_node_ids: List[str]            # Outflow node IDs generated
    action_type: str                    # "BUY_PRODUCT", "BUY_SEED", "PLANT", "WATER", "HARVEST", "FEED", "DROP", "PICKUP", "SELL"
    start_turn: int
    completion_turn: int
    quantity_delta: Dict[str, int]      # Net quantity delta by commodity
    cash_delta: float = 0.0             # Cost (-) or revenue (+)
    capacity_delta: int = 0             # Net shed space delta
    worker_req: Optional[int] = None    # Worker ID required (0 for farmer, 1..N for hands)
    prerequisite_actions: List[str] = field(default_factory=list)
    is_irreversible: bool = True
    obligation_dependencies: List[str] = field(default_factory=list)
    terminal_compatibility: bool = True


@dataclass
class ResourceObligation:
    """Formal obligation reserving resources for critical operations (§4, §5)."""
    obligation_id: str
    obligation_type: ObligationType
    commodity: str
    quantity: int
    deadline_turn: int
    priority: int = 100                 # Higher = more critical
    is_critical: bool = True            # True if breaching causes fatal failure (e.g. animal death)
    target_entity: Optional[str] = None # e.g. "ANIMAL_COW_3_4"
    assigned_reservations: List[str] = field(default_factory=list)


@dataclass
class ResourceReservation:
    """Earmarks a specific resource stock for an obligation (§4)."""
    reservation_id: str
    obligation_id: str
    node_id: str
    reserved_quantity: int
    start_turn: int
    release_turn: int


class TemporalResourceDAG:
    """Formal time-expanded dependency DAG representing multi-turn resource causality (§3, §7)."""

    def __init__(self) -> None:
        self.nodes: Dict[str, ResourceNode] = {}
        self.edges: Dict[str, ResourceEdge] = {}
        self.obligations: Dict[str, ResourceObligation] = {}
        self.reservations: Dict[str, ResourceReservation] = {}

        # Adjacency structures
        self._node_out_edges: Dict[str, List[str]] = defaultdict(list)
        self._node_in_edges: Dict[str, List[str]] = defaultdict(list)
        self._edge_out_nodes: Dict[str, List[str]] = defaultdict(list)
        self._edge_in_nodes: Dict[str, List[str]] = defaultdict(list)

    def add_node(self, node: ResourceNode) -> None:
        self.nodes[node.node_id] = node

    def add_edge(self, edge: ResourceEdge) -> None:
        self.edges[edge.edge_id] = edge
        for src_id in edge.source_node_ids:
            self._node_out_edges[src_id].append(edge.edge_id)
            self._edge_in_nodes[edge.edge_id].append(src_id)
        for dst_id in edge.dest_node_ids:
            self._node_in_edges[dst_id].append(edge.edge_id)
            self._edge_out_nodes[edge.edge_id].append(dst_id)

    def add_obligation(self, obligation: ResourceObligation) -> None:
        self.obligations[obligation.obligation_id] = obligation

    def add_reservation(self, reservation: ResourceReservation) -> None:
        self.reservations[reservation.reservation_id] = reservation
        if reservation.node_id in self.nodes:
            self.nodes[reservation.node_id].reservation_state = "RESERVED"
        if reservation.obligation_id in self.obligations:
            self.obligations[reservation.obligation_id].assigned_reservations.append(
                reservation.reservation_id
            )

    def get_node(self, node_id: str) -> Optional[ResourceNode]:
        return self.nodes.get(node_id)

    def get_edge(self, edge_id: str) -> Optional[ResourceEdge]:
        return self.edges.get(edge_id)

    def compute_inventory_at_turn(self, commodity: str, location: str, turn: int) -> int:
        """Compute total physical quantity of a commodity at a given location at or before turn."""
        total = 0
        for node in self.nodes.values():
            if node.commodity == commodity and node.location == location:
                if node.availability_turn <= turn and node.turn <= turn:
                    if node.reservation_state != "CONSUMED":
                        total += node.quantity
        return total

    def compute_dependency_closure(self, seed_edge_or_node_ids: Set[str]) -> Set[str]:
        """Compute the transitive closure of all causal nodes and edges reachable downstream (§13)."""
        closure = set(seed_edge_or_node_ids)
        queue = deque(list(seed_edge_or_node_ids))

        while queue:
            curr = queue.popleft()
            if curr in self.nodes:
                for edge_id in self._node_out_edges.get(curr, []):
                    if edge_id not in closure:
                        closure.add(edge_id)
                        queue.append(edge_id)
            elif curr in self.edges:
                for node_id in self._edge_out_nodes.get(curr, []):
                    if node_id not in closure:
                        closure.add(node_id)
                        queue.append(node_id)

        return closure

    def verify_conservation(
        self,
        commodity: str,
        initial_stock: int,
        turn_start: int,
        turn_end: int
    ) -> Tuple[bool, Optional[str]]:
        """Validate conservation law: Initial + Inflows - Outflows == Final (§7)."""
        inflows = 0
        outflows = 0

        for edge in self.edges.values():
            if turn_start <= edge.completion_turn <= turn_end:
                delta = edge.quantity_delta.get(commodity, 0)
                if delta > 0:
                    inflows += delta
                elif delta < 0:
                    outflows += abs(delta)

        expected_final = initial_stock + inflows - outflows
        actual_final = sum(
            n.quantity for n in self.nodes.values()
            if n.commodity == commodity and n.turn == turn_end and n.reservation_state != "CONSUMED"
        )

        if actual_final != expected_final:
            return False, (
                f"Resource conservation violation for {commodity}: "
                f"initial={initial_stock} + in={inflows} - out={outflows} = {expected_final}, "
                f"but actual node stock={actual_final}"
            )
        return True, None

    def check_negative_inventory(self) -> Tuple[bool, Optional[str]]:
        """Verify no node holds negative inventory at any turn (§7, §18)."""
        for node in self.nodes.values():
            if node.quantity < 0:
                return False, f"Negative inventory detected on node {node.node_id}: {node.commodity}={node.quantity}"
        return True, None

    def check_capacity_overflow(self, max_capacity: int = SHED_CAPACITY) -> Tuple[bool, Optional[str]]:
        """Verify shed storage does not overflow max_capacity at any turn (§7, §11)."""
        turns = sorted(list({n.turn for n in self.nodes.values()}))
        for t in turns:
            shed_total = sum(
                n.quantity for n in self.nodes.values()
                if n.location == "SHED" and n.capacity_domain == "SHED"
                and n.turn == t and n.reservation_state != "CONSUMED"
            )
            if shed_total > max_capacity:
                return False, f"Shed capacity overflow at turn {t}: {shed_total} units exceeds max {max_capacity}"
        return True, None

    def check_temporal_availability(self) -> Tuple[bool, Optional[str]]:
        """Verify no edge consumes an input before it becomes available (§7, §18)."""
        for edge in self.edges.values():
            for src_id in edge.source_node_ids:
                src_node = self.nodes.get(src_id)
                if src_node is None:
                    return False, f"Edge {edge.edge_id} references missing source node {src_id}"
                if edge.start_turn < src_node.availability_turn:
                    return False, (
                        f"Temporal violation on edge {edge.edge_id}: starts at turn {edge.start_turn} "
                        f"before source node {src_id} is available at turn {src_node.availability_turn}"
                    )
        return True, None

    def check_reservation_conflicts(self) -> Tuple[bool, Optional[str]]:
        """Verify no single inventory unit is double-allocated to conflicting obligations (§7, §18)."""
        allocated_by_node: Dict[str, int] = defaultdict(int)
        for res in self.reservations.values():
            allocated_by_node[res.node_id] += res.reserved_quantity

        for node_id, total_alloc in allocated_by_node.items():
            node = self.nodes.get(node_id)
            if node is None:
                return False, f"Reservation references missing node {node_id}"
            if total_alloc > node.quantity:
                return False, (
                    f"Double-allocation conflict on node {node_id}: total reserved={total_alloc} "
                    f"exceeds available stock={node.quantity}"
                )
        return True, None

    def detect_cycles(self) -> bool:
        """Check for causal cycles in the time-expanded graph."""
        in_degree: Dict[str, int] = defaultdict(int)
        all_entities = list(self.nodes.keys()) + list(self.edges.keys())
        for e in all_entities:
            in_degree[e] = 0

        for edge_id, edge in self.edges.items():
            for src_id in edge.source_node_ids:
                in_degree[edge_id] += 1
            for dst_id in edge.dest_node_ids:
                in_degree[dst_id] += 1

        queue = deque([e for e in all_entities if in_degree[e] == 0])
        visited_count = 0

        while queue:
            curr = queue.popleft()
            visited_count += 1

            if curr in self.nodes:
                for out_edge in self._node_out_edges.get(curr, []):
                    in_degree[out_edge] -= 1
                    if in_degree[out_edge] == 0:
                        queue.append(out_edge)
            elif curr in self.edges:
                for out_node in self._edge_out_nodes.get(curr, []):
                    in_degree[out_node] -= 1
                    if in_degree[out_node] == 0:
                        queue.append(out_node)

        return visited_count < len(all_entities)
