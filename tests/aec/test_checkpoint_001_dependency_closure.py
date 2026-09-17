# SPDX-License-Identifier: MIT
"""AEC Checkpoint 001: Dependency Closure Expansion Validation (§6).

Tests that causal dependency closures propagate through actual physical and economic causal graphs:
1. Market Causal Chain:
   MARKET ORDER -> price -> cash -> inventory -> later order feasibility -> production -> terminal state.
2. Worker Causal Chain:
   ROUTE CHANGE -> ETA -> task start -> production -> inventory -> transport -> sale -> cash -> terminal.
3. Resource Causal Chain:
   INPUT CONSUMPTION -> output -> capacity -> market sale -> cash -> future production.
4. Minimal Local vs Expanded Closure dynamics.
"""

from __future__ import annotations

from typing import Set
import pytest

from aec.ir.dependency_graph import (
    ActionBasketDependencyGraph,
    ActionNode,
    CausalEdgeType,
)


def test_market_causal_chain_expansion() -> None:
    """Proves Market Causal Chain expands from seed market order to terminal state.
    
    MARKET ORDER -> price -> cash -> inventory -> later order feasibility -> production -> terminal.
    """
    graph = ActionBasketDependencyGraph()

    n_order = ActionNode(node_id="MKT_SELL_STRAWBERRY", actor_type="MARKET", actor_index=0, action_type="SELL", item="STRAWBERRY", quantity=10, cash_yield_est=1200.0)
    n_price = ActionNode(node_id="PRICE_DROP_STRAWBERRY", actor_type="MARKET", actor_index=0, action_type="PRICE_UPDATE", item="STRAWBERRY")
    n_cash = ActionNode(node_id="LIQUIDITY_SURPLUS", actor_type="FINANCE", actor_index=0, action_type="CASH_UPDATE", cash_yield_est=1200.0)
    n_inv = ActionNode(node_id="SHED_SPACE_FREED", actor_type="FARM", actor_index=0, action_type="SHED_UPDATE", shed_outflow_est=10)
    n_later_order = ActionNode(node_id="MKT_BUY_SEED_MELON", actor_type="MARKET", actor_index=1, action_type="BUY_SEED", item="MELON", quantity=5, cash_required_est=400.0)
    n_prod = ActionNode(node_id="MELON_CROP_PLANTED", actor_type="FARM", actor_index=0, action_type="PLANT", item="MELON", quantity=5)
    n_terminal = ActionNode(node_id="TERMINAL_MARGIN_STATE", actor_type="EVALUATION", actor_index=0, action_type="TERMINAL_SCORE", cash_yield_est=1250.0)

    for n in (n_order, n_price, n_cash, n_inv, n_later_order, n_prod, n_terminal):
        graph.add_node(n)

    # Wire causal edges
    graph.add_edge("MKT_SELL_STRAWBERRY", "PRICE_DROP_STRAWBERRY", CausalEdgeType.SAME_ASSET_MARKET_COUPLING, description="Sell alters clearing price")
    graph.add_edge("MKT_SELL_STRAWBERRY", "LIQUIDITY_SURPLUS", CausalEdgeType.CASH_COUPLING, description="Sale proceeds credit cash balance")
    graph.add_edge("MKT_SELL_STRAWBERRY", "SHED_SPACE_FREED", CausalEdgeType.CAPACITY_COUPLING, description="Depleting shed frees capacity")
    graph.add_edge("LIQUIDITY_SURPLUS", "MKT_BUY_SEED_MELON", CausalEdgeType.CASH_COUPLING, description="Liquidity surplus funds melon seed purchase")
    graph.add_edge("MKT_BUY_SEED_MELON", "MELON_CROP_PLANTED", CausalEdgeType.TIMING_COUPLING, description="Seed purchase enables planting")
    graph.add_edge("MELON_CROP_PLANTED", "TERMINAL_MARGIN_STATE", CausalEdgeType.TIMING_COUPLING, description="Harvested melons contribute to terminal wealth")

    # Compute dependency closure from seed order
    closure = graph.compute_dependency_closure({"MKT_SELL_STRAWBERRY"})

    assert "PRICE_DROP_STRAWBERRY" in closure
    assert "LIQUIDITY_SURPLUS" in closure
    assert "SHED_SPACE_FREED" in closure
    assert "MKT_BUY_SEED_MELON" in closure
    assert "MELON_CROP_PLANTED" in closure
    assert "TERMINAL_MARGIN_STATE" in closure
    assert len(closure) == 7, f"Expected full causal chain of 7 nodes, got {len(closure)}"


def test_worker_route_causal_chain_expansion() -> None:
    """Proves Worker Route Causal Chain expands through physical actions to cash and terminal.
    
    ROUTE CHANGE -> ETA -> task start -> production -> inventory -> transport -> sale -> cash -> terminal.
    """
    graph = ActionBasketDependencyGraph()

    nodes = [
        ActionNode(node_id="W0_DETOUR_WEED_DIG", actor_type="WORKER_FARMER", actor_index=0, action_type="DIG"),
        ActionNode(node_id="W0_ETA_DELAY_TILE_5_5", actor_type="WORKER_FARMER", actor_index=0, action_type="MOVE_DELAY"),
        ActionNode(node_id="TASK_HARVEST_START", actor_type="WORKER_FARMER", actor_index=0, action_type="HARVEST", item="TOMATO", quantity=4),
        ActionNode(node_id="CARGO_LOAD_TOMATO", actor_type="WORKER_FARMER", actor_index=0, action_type="INVENTORY_LOAD", item="TOMATO", quantity=4),
        ActionNode(node_id="TRANSPORT_TO_SHED", actor_type="WORKER_FARMER", actor_index=0, action_type="MOVE_SHED"),
        ActionNode(node_id="DEPOSIT_TO_SHED", actor_type="FARM", actor_index=0, action_type="DROP", item="TOMATO", quantity=4),
        ActionNode(node_id="MARKET_SALE_TOMATO", actor_type="MARKET", actor_index=0, action_type="SELL", item="TOMATO", quantity=4, cash_yield_est=240.0),
        ActionNode(node_id="TERMINAL_CASH_GAIN", actor_type="EVALUATION", actor_index=0, action_type="TERMINAL_SCORE", cash_yield_est=240.0),
    ]
    for n in nodes:
        graph.add_node(n)

    graph.add_edge("W0_DETOUR_WEED_DIG", "W0_ETA_DELAY_TILE_5_5", CausalEdgeType.TIMING_COUPLING, description="Dig adds 1 step detour")
    graph.add_edge("W0_ETA_DELAY_TILE_5_5", "TASK_HARVEST_START", CausalEdgeType.TIMING_COUPLING, description="Delayed arrival shifts harvest start")
    graph.add_edge("TASK_HARVEST_START", "CARGO_LOAD_TOMATO", CausalEdgeType.INVENTORY_COUPLING, description="Harvest yields tomato cargo")
    graph.add_edge("CARGO_LOAD_TOMATO", "TRANSPORT_TO_SHED", CausalEdgeType.TIMING_COUPLING, description="Cargo requires transport to shed")
    graph.add_edge("TRANSPORT_TO_SHED", "DEPOSIT_TO_SHED", CausalEdgeType.CAPACITY_COUPLING, description="Transport reaches shed for deposit")
    graph.add_edge("DEPOSIT_TO_SHED", "MARKET_SALE_TOMATO", CausalEdgeType.INVENTORY_COUPLING, description="Shed stock enables market sale")
    graph.add_edge("MARKET_SALE_TOMATO", "TERMINAL_CASH_GAIN", CausalEdgeType.CASH_COUPLING, description="Sale revenue realizes terminal cash")

    closure = graph.compute_dependency_closure({"W0_DETOUR_WEED_DIG"})

    assert len(closure) == 8
    assert "TASK_HARVEST_START" in closure
    assert "MARKET_SALE_TOMATO" in closure
    assert "TERMINAL_CASH_GAIN" in closure


def test_resource_causal_chain_expansion() -> None:
    """Proves Resource Causal Chain expands from input consumption through production to market.
    
    INPUT CONSUMPTION -> output -> capacity -> market sale -> cash -> future production.
    """
    graph = ActionBasketDependencyGraph()

    nodes = [
        ActionNode(node_id="CONSUME_FEED_WHEAT", actor_type="FARM", actor_index=0, action_type="CONSUME", item="WHEAT", quantity=2),
        ActionNode(node_id="PRODUCE_MILK_OUTPUT", actor_type="FARM", actor_index=0, action_type="PRODUCE", item="MILK", quantity=2),
        ActionNode(node_id="CONSUME_SHED_CAPACITY", actor_type="FARM", actor_index=0, action_type="SHED_OCCUPY", item="MILK", quantity=2),
        ActionNode(node_id="MARKET_SALE_MILK", actor_type="MARKET", actor_index=0, action_type="SELL", item="MILK", quantity=2, cash_yield_est=320.0),
        ActionNode(node_id="CASH_REVENUE_MILK", actor_type="FINANCE", actor_index=0, action_type="CASH_UPDATE", cash_yield_est=320.0),
        ActionNode(node_id="FUND_FUTURE_EXPANSION", actor_type="FINANCE", actor_index=0, action_type="BUY_LAND", cash_required_est=1000.0),
    ]
    for n in nodes:
        graph.add_node(n)

    graph.add_edge("CONSUME_FEED_WHEAT", "PRODUCE_MILK_OUTPUT", CausalEdgeType.OBLIGATION_COUPLING)
    graph.add_edge("PRODUCE_MILK_OUTPUT", "CONSUME_SHED_CAPACITY", CausalEdgeType.CAPACITY_COUPLING)
    graph.add_edge("CONSUME_SHED_CAPACITY", "MARKET_SALE_MILK", CausalEdgeType.INVENTORY_COUPLING)
    graph.add_edge("MARKET_SALE_MILK", "CASH_REVENUE_MILK", CausalEdgeType.CASH_COUPLING)
    graph.add_edge("CASH_REVENUE_MILK", "FUND_FUTURE_EXPANSION", CausalEdgeType.CASH_COUPLING)

    closure = graph.compute_dependency_closure({"CONSUME_FEED_WHEAT"})
    assert len(closure) == 6
    assert "PRODUCE_MILK_OUTPUT" in closure
    assert "FUND_FUTURE_EXPANSION" in closure


def test_isolated_local_vs_expanded_closure_boundary() -> None:
    """Proves that purely local mutations retain minimal closure size (cheap fast path),
    while coupled mutations dynamically expand.
    """
    graph = ActionBasketDependencyGraph()

    # Node 1: Purely local order with zero dependencies (e.g. uncoupled small sale)
    graph.add_node(ActionNode(node_id="LOCAL_SELL_EGG", actor_type="MARKET", actor_index=0, action_type="SELL", item="EGG", quantity=1))
    
    # Node 2-4: Coupled network
    graph.add_node(ActionNode(node_id="COUPLED_BUY_WHEAT", actor_type="MARKET", actor_index=1, action_type="BUY_PRODUCT", item="WHEAT", quantity=5))
    graph.add_node(ActionNode(node_id="COUPLED_SELL_WHEAT", actor_type="MARKET", actor_index=2, action_type="SELL", item="WHEAT", quantity=2))
    graph.add_edge("COUPLED_BUY_WHEAT", "COUPLED_SELL_WHEAT", CausalEdgeType.SAME_ASSET_MARKET_COUPLING)

    # Local node closure is exactly 1 (cheap, short horizon)
    local_closure = graph.compute_dependency_closure({"LOCAL_SELL_EGG"})
    assert len(local_closure) == 1

    # Coupled node closure is 2 (escalates to dependency-closure horizon)
    coupled_closure = graph.compute_dependency_closure({"COUPLED_BUY_WHEAT"})
    assert len(coupled_closure) == 2
    assert "COUPLED_SELL_WHEAT" in coupled_closure
