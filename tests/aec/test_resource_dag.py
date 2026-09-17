# SPDX-License-Identifier: MIT
"""Unit tests for AEC-RESOURCE Temporal Resource DAG (§2, §3, §4, §7)."""

from __future__ import annotations

import pytest

from aec.resource.dag import (
    ObligationType,
    ResourceEdge,
    ResourceLocationType,
    ResourceNode,
    ResourceObligation,
    ResourceReservation,
    TemporalResourceDAG,
)


def test_resource_node_and_edge_instantiation() -> None:
    """Validate formal schema of ResourceNode and ResourceEdge (§4)."""
    node = ResourceNode(
        node_id="NODE_WHEAT_SHED_0",
        commodity="WHEAT",
        quantity=10,
        turn=0,
        location=ResourceLocationType.SHED.value,
        capacity_domain="SHED",
        provenance="INITIAL",
        reservation_state="AVAILABLE",
        availability_turn=0
    )
    assert node.node_id == "NODE_WHEAT_SHED_0"
    assert node.commodity == "WHEAT"
    assert node.quantity == 10
    assert node.is_available

    edge = ResourceEdge(
        edge_id="EDGE_BUY_WHEAT_0",
        source_node_ids=["NODE_MONEY_0"],
        dest_node_ids=["NODE_WHEAT_SHED_0"],
        action_type="BUY_PRODUCT",
        start_turn=0,
        completion_turn=1,
        quantity_delta={"WHEAT": 1},
        cash_delta=-25.0,
        capacity_delta=1
    )
    assert edge.edge_id == "EDGE_BUY_WHEAT_0"
    assert edge.cash_delta == -25.0
    assert edge.capacity_delta == 1


def test_conservation_law_exact_balance() -> None:
    """Validate conservation law: Initial + Inflows - Outflows == Final (§7)."""
    dag = TemporalResourceDAG()
    # Initial: 10 wheat
    dag.add_node(ResourceNode(
        node_id="WHEAT_T0",
        commodity="WHEAT",
        quantity=10,
        turn=0,
        location="SHED"
    ))
    # Edge: buy 5 wheat, sell 3 wheat -> net +2
    dag.add_edge(ResourceEdge(
        edge_id="E_BUY",
        source_node_ids=["WHEAT_T0"],
        dest_node_ids=["WHEAT_T1"],
        action_type="BUY_PRODUCT",
        start_turn=0,
        completion_turn=1,
        quantity_delta={"WHEAT": 5}
    ))
    dag.add_edge(ResourceEdge(
        edge_id="E_SELL",
        source_node_ids=["WHEAT_T0"],
        dest_node_ids=["WHEAT_T1"],
        action_type="SELL",
        start_turn=0,
        completion_turn=1,
        quantity_delta={"WHEAT": -3}
    ))
    # Expected final at turn 1: 10 + 5 - 3 = 12
    dag.add_node(ResourceNode(
        node_id="WHEAT_T1",
        commodity="WHEAT",
        quantity=12,
        turn=1,
        location="SHED"
    ))

    is_valid, reason = dag.verify_conservation("WHEAT", initial_stock=10, turn_start=0, turn_end=1)
    assert is_valid, f"Conservation failed: {reason}"


def test_conservation_law_detects_imbalance() -> None:
    """Verify conservation check detects unexplained inventory leakage (§7)."""
    dag = TemporalResourceDAG()
    dag.add_node(ResourceNode(
        node_id="WHEAT_T0",
        commodity="WHEAT",
        quantity=10,
        turn=0,
        location="SHED"
    ))
    # Inflow +5, expected final = 15, but node reports 13 (leakage of 2)
    dag.add_edge(ResourceEdge(
        edge_id="E_BUY",
        source_node_ids=["WHEAT_T0"],
        dest_node_ids=["WHEAT_T1"],
        action_type="BUY_PRODUCT",
        start_turn=0,
        completion_turn=1,
        quantity_delta={"WHEAT": 5}
    ))
    dag.add_node(ResourceNode(
        node_id="WHEAT_T1",
        commodity="WHEAT",
        quantity=13,
        turn=1,
        location="SHED"
    ))

    is_valid, reason = dag.verify_conservation("WHEAT", initial_stock=10, turn_start=0, turn_end=1)
    assert not is_valid
    assert "Resource conservation violation" in (reason or "")


def test_negative_inventory_detection() -> None:
    """Verify DAG detects impossible negative inventory nodes (§7, §18)."""
    dag = TemporalResourceDAG()
    dag.add_node(ResourceNode(
        node_id="WHEAT_DEFICIT",
        commodity="WHEAT",
        quantity=-2,
        turn=5,
        location="SHED"
    ))
    is_valid, reason = dag.check_negative_inventory()
    assert not is_valid
    assert "Negative inventory detected" in (reason or "")


def test_capacity_overflow_detection() -> None:
    """Verify DAG detects shed capacity overflow (> 100 units) (§7, §11)."""
    dag = TemporalResourceDAG()
    dag.add_node(ResourceNode(
        node_id="SHED_OVERFLOW",
        commodity="WHEAT",
        quantity=105,
        turn=10,
        location="SHED",
        capacity_domain="SHED"
    ))
    is_valid, reason = dag.check_capacity_overflow(max_capacity=100)
    assert not is_valid
    assert "Shed capacity overflow" in (reason or "")


def test_temporal_availability_check() -> None:
    """Verify consumption before availability turn is rejected (§7, §18)."""
    dag = TemporalResourceDAG()
    dag.add_node(ResourceNode(
        node_id="WHEAT_GROWING",
        commodity="WHEAT",
        quantity=6,
        turn=0,
        location="TILE_2_3",
        availability_turn=48 # Matures at turn 48
    ))
    # Action attempts harvest at turn 24 (before maturity)
    dag.add_edge(ResourceEdge(
        edge_id="E_PREMATURE_HARVEST",
        source_node_ids=["WHEAT_GROWING"],
        dest_node_ids=["WHEAT_HARVESTED"],
        action_type="HARVEST",
        start_turn=24,
        completion_turn=25,
        quantity_delta={"WHEAT": 6}
    ))

    is_valid, reason = dag.check_temporal_availability()
    assert not is_valid
    assert "Temporal violation" in (reason or "")


def test_double_allocation_reservation_conflict() -> None:
    """Verify single unit allocated to two conflicting obligations is caught (§7, §18)."""
    dag = TemporalResourceDAG()
    dag.add_node(ResourceNode(
        node_id="WHEAT_1_UNIT",
        commodity="WHEAT",
        quantity=1,
        turn=0,
        location="SHED"
    ))
    # Obligation 1 reserves 1 unit
    dag.add_obligation(ResourceObligation(
        obligation_id="OB_FEED_COW",
        obligation_type=ObligationType.LIVESTOCK_FEED,
        commodity="WHEAT",
        quantity=1,
        deadline_turn=23
    ))
    dag.add_reservation(ResourceReservation(
        reservation_id="RES_1",
        obligation_id="OB_FEED_COW",
        node_id="WHEAT_1_UNIT",
        reserved_quantity=1,
        start_turn=0,
        release_turn=23
    ))
    # Obligation 2 also reserves 1 unit from the same single unit
    dag.add_obligation(ResourceObligation(
        obligation_id="OB_SALE",
        obligation_type=ObligationType.COMMITTED_SALE,
        commodity="WHEAT",
        quantity=1,
        deadline_turn=10
    ))
    dag.add_reservation(ResourceReservation(
        reservation_id="RES_2",
        obligation_id="OB_SALE",
        node_id="WHEAT_1_UNIT",
        reserved_quantity=1,
        start_turn=0,
        release_turn=10
    ))

    is_valid, reason = dag.check_reservation_conflicts()
    assert not is_valid
    assert "Double-allocation conflict" in (reason or "")


def test_dependency_closure_propagation() -> None:
    """Validate transitive causal closure downstream (§13)."""
    dag = TemporalResourceDAG()
    dag.add_node(ResourceNode(node_id="A", commodity="CASH", quantity=100, turn=0))
    dag.add_node(ResourceNode(node_id="B", commodity="SEED", quantity=5, turn=1))
    dag.add_node(ResourceNode(node_id="C", commodity="CROP", quantity=20, turn=48))
    dag.add_node(ResourceNode(node_id="D", commodity="MONEY", quantity=500, turn=49))

    dag.add_edge(ResourceEdge(
        edge_id="E1", source_node_ids=["A"], dest_node_ids=["B"],
        action_type="BUY_SEED", start_turn=0, completion_turn=1, quantity_delta={}
    ))
    dag.add_edge(ResourceEdge(
        edge_id="E2", source_node_ids=["B"], dest_node_ids=["C"],
        action_type="HARVEST", start_turn=47, completion_turn=48, quantity_delta={}
    ))
    dag.add_edge(ResourceEdge(
        edge_id="E3", source_node_ids=["C"], dest_node_ids=["D"],
        action_type="SELL", start_turn=48, completion_turn=49, quantity_delta={}
    ))

    closure = dag.compute_dependency_closure({"A"})
    assert "E1" in closure
    assert "B" in closure
    assert "E2" in closure
    assert "C" in closure
    assert "E3" in closure
    assert "D" in closure
