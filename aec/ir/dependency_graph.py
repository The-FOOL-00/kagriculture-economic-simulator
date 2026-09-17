# SPDX-License-Identifier: MIT
"""Action Basket Dependency Graph and Causal Edge Representation (§7, §8, §9)."""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

from aec.config import PRODUCTS, SHED_CAPACITY, CROP_SEED_PRICE


class CausalEdgeType(Enum):
    """Authoritative taxonomy of economic and physical coupling edges."""
    SAME_ASSET_MARKET_COUPLING = "SAME_ASSET_MARKET_COUPLING"
    CROSS_ASSET_MARKET_COUPLING = "CROSS_ASSET_MARKET_COUPLING"
    CASH_COUPLING = "CASH_COUPLING"
    INVENTORY_COUPLING = "INVENTORY_COUPLING"
    CAPACITY_COUPLING = "CAPACITY_COUPLING"
    OBLIGATION_COUPLING = "OBLIGATION_COUPLING"
    TIMING_COUPLING = "TIMING_COUPLING"


@dataclass
class ActionNode:
    """Represents a discrete action entity within an action basket or worker schedule."""
    node_id: str
    actor_type: str                     # "MARKET", "WORKER_FARMER", "WORKER_HAND"
    actor_index: int                    # Worker index (0 for farmer, 1..N for hands), or order index in queue
    action_type: str                    # "BUY_PRODUCT", "SELL", "HIRE", "BUY_LAND", "MOVE", "HARVEST", etc.
    item: Optional[str] = None          # e.g. "WHEAT", "FERTILIZER"
    quantity: int = 1                   # Units ordered or handled
    target_pos: Optional[Tuple[int, int]] = None

    # Preconditions and effects
    cash_required_est: float = 0.0
    cash_yield_est: float = 0.0
    shed_inflow_est: int = 0
    shed_outflow_est: int = 0
    raw_order: Optional[List[Any]] = None


@dataclass
class CausalEdge:
    """Directed edge representing causal dependency from source node to target node."""
    source_id: str
    target_id: str
    edge_type: CausalEdgeType
    weight: float = 1.0
    description: str = ""


class ActionBasketDependencyGraph:
    """Constructs and queries the causal dependency DAG of a full-turn action basket."""

    def __init__(self) -> None:
        self.nodes: Dict[str, ActionNode] = {}
        self.edges: List[CausalEdge] = []
        self._adjacency: Dict[str, List[CausalEdge]] = {}
        self._reverse_adjacency: Dict[str, List[CausalEdge]] = {}

    def add_node(self, node: ActionNode) -> None:
        self.nodes[node.node_id] = node
        self._adjacency.setdefault(node.node_id, [])
        self._reverse_adjacency.setdefault(node.node_id, [])

    def add_edge(
        self,
        source_id: str,
        target_id: str,
        edge_type: CausalEdgeType,
        weight: float = 1.0,
        description: str = ""
    ) -> None:
        edge = CausalEdge(
            source_id=source_id,
            target_id=target_id,
            edge_type=edge_type,
            weight=weight,
            description=description
        )
        self.edges.append(edge)
        self._adjacency.setdefault(source_id, []).append(edge)
        self._reverse_adjacency.setdefault(target_id, []).append(edge)

    def get_downstream_edges(self, node_id: str) -> List[CausalEdge]:
        return self._adjacency.get(node_id, [])

    def get_upstream_edges(self, node_id: str) -> List[CausalEdge]:
        return self._reverse_adjacency.get(node_id, [])

    def compute_dependency_closure(self, seed_node_ids: Set[str]) -> Set[str]:
        """Compute the transitive closure of all nodes causally affected by seed mutations."""
        closure = set(seed_node_ids)
        frontier = list(seed_node_ids)

        while frontier:
            curr = frontier.pop(0)
            for edge in self._adjacency.get(curr, []):
                if edge.target_id not in closure:
                    closure.add(edge.target_id)
                    frontier.append(edge.target_id)

        return closure

    def are_coupled(self, node_a_id: str, node_b_id: str) -> bool:
        """Check if node_a and node_b have any direct or indirect causal path between them."""
        closure_a = self.compute_dependency_closure({node_a_id})
        if node_b_id in closure_a:
            return True
        closure_b = self.compute_dependency_closure({node_b_id})
        return node_a_id in closure_b

    def get_same_asset_couplings(self) -> List[Tuple[str, str, str]]:
        """Return all pairs (node_a, node_b, commodity) sharing same-asset market coupling."""
        pairs = []
        for edge in self.edges:
            if edge.edge_type == CausalEdgeType.SAME_ASSET_MARKET_COUPLING:
                src = self.nodes.get(edge.source_id)
                tgt = self.nodes.get(edge.target_id)
                item = src.item if src else (tgt.item if tgt else None)
                if item:
                    pairs.append((edge.source_id, edge.target_id, item))
        return pairs


def build_basket_dependency_graph(
    action: Dict[str, Any],
    econ_state: Any
) -> ActionBasketDependencyGraph:
    """Builds a complete causal dependency DAG from a live action dict and economic state."""
    graph = ActionBasketDependencyGraph()
    market_orders = action.get("market", []) or []

    # 1. Add Market Order Nodes
    market_nodes: List[ActionNode] = []
    for idx, order in enumerate(market_orders):
        if not isinstance(order, (list, tuple)) or not order:
            continue
        op = str(order[0])
        item = str(order[1]) if len(order) > 1 else None
        qty = 1
        if len(order) > 2:
            try:
                qty = int(order[2])
            except (ValueError, TypeError):
                qty = 1

        node_id = f"MKT_{idx}_{op}_{item or 'NONE'}"
        node = ActionNode(
            node_id=node_id,
            actor_type="MARKET",
            actor_index=idx,
            action_type=op,
            item=item,
            quantity=qty,
            raw_order=list(order)
        )

        # Estimate cash/inventory impacts
        if op == "BUY_PRODUCT" and item:
            cur_p = float(econ_state.market.get_price(item)) if hasattr(econ_state, "market") else 30.0
            node.cash_required_est = cur_p * qty
            node.shed_inflow_est = qty
        elif op == "SELL" and item:
            cur_p = float(econ_state.market.get_price(item)) if hasattr(econ_state, "market") else 30.0
            node.cash_yield_est = cur_p * qty
            node.shed_outflow_est = qty
        elif op == "BUY_SEED" and item:
            seed_p = float(CROP_SEED_PRICE.get(item, 20))
            node.cash_required_est = seed_p * qty
        elif op == "HIRE":
            node.cash_required_est = 100.0

        graph.add_node(node)
        market_nodes.append(node)

    # 2. Build Market Causal Edges
    for i in range(len(market_nodes)):
        node_i = market_nodes[i]
        for j in range(i + 1, len(market_nodes)):
            node_j = market_nodes[j]

            # (a) Same-Asset Market Coupling (BUY <-> SELL or multiple BUYs of same commodity)
            if node_i.item and node_j.item and node_i.item == node_j.item:
                desc = (
                    f"Order {i} ({node_i.action_type} {node_i.item} x{node_i.quantity}) directly alters "
                    f"market clearing price for Order {j} ({node_j.action_type} {node_j.item} x{node_j.quantity})"
                )
                graph.add_edge(
                    source_id=node_i.node_id,
                    target_id=node_j.node_id,
                    edge_type=CausalEdgeType.SAME_ASSET_MARKET_COUPLING,
                    weight=1.0,
                    description=desc
                )

            # (b) Cash Coupling (earlier purchase consumes liquidity needed by later purchase)
            if node_i.cash_required_est > 0 and node_j.cash_required_est > 0:
                desc = f"Order {i} expenditure (${node_i.cash_required_est:.0f}) constrains cash for Order {j}"
                graph.add_edge(
                    source_id=node_i.node_id,
                    target_id=node_j.node_id,
                    edge_type=CausalEdgeType.CASH_COUPLING,
                    weight=0.8,
                    description=desc
                )
            elif node_i.cash_yield_est > 0 and node_j.cash_required_est > 0:
                desc = f"Order {i} revenue (${node_i.cash_yield_est:.0f}) funds Order {j}"
                graph.add_edge(
                    source_id=node_i.node_id,
                    target_id=node_j.node_id,
                    edge_type=CausalEdgeType.CASH_COUPLING,
                    weight=0.9,
                    description=desc
                )

            # (c) Inventory / Shed Capacity Coupling
            if node_i.shed_inflow_est > 0 and node_j.shed_inflow_est > 0:
                desc = f"Order {i} shed inflow ({node_i.shed_inflow_est}) consumes shed capacity for Order {j}"
                graph.add_edge(
                    source_id=node_i.node_id,
                    target_id=node_j.node_id,
                    edge_type=CausalEdgeType.CAPACITY_COUPLING,
                    weight=0.7,
                    description=desc
                )

    # 3. Add Worker Action Nodes (Farmer & Hands)
    farmer_cmd = action.get("farmer", ["PASS"]) or ["PASS"]
    f_op = farmer_cmd[0] if farmer_cmd else "PASS"
    f_node = ActionNode(
        node_id="W0_FARMER",
        actor_type="WORKER_FARMER",
        actor_index=0,
        action_type=f_op
    )
    graph.add_node(f_node)

    hands_cmds = action.get("hands", []) or []
    for h_idx, h_cmd in enumerate(hands_cmds):
        h_op = h_cmd[0] if (h_cmd and isinstance(h_cmd, (list, tuple))) else "PASS"
        h_node = ActionNode(
            node_id=f"W{h_idx + 1}_HAND",
            actor_type="WORKER_HAND",
            actor_index=h_idx + 1,
            action_type=h_op
        )
        graph.add_node(h_node)

    return graph
