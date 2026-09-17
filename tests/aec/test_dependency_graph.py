# SPDX-License-Identifier: MIT
"""Unit Tests for Action Basket Dependency Graph (§7, §8, §9)."""

from __future__ import annotations

import pytest
from aec.ir.dependency_graph import (
    ActionBasketDependencyGraph,
    ActionNode,
    CausalEdgeType,
    build_basket_dependency_graph,
)
from aec.ir.economic_state import build_economic_state


def test_dependency_graph_same_asset_coupling(normal_opening_obs):
    """Verifies that BUY and SELL of same commodity are recognized as causally coupled."""
    state = build_economic_state(normal_opening_obs)
    action = {
        "farmer": ["PASS"],
        "hands": [],
        "market": [
            ["BUY_PRODUCT", "WHEAT", 16],
            ["SELL", "WHEAT", 2],
            ["BUY_PRODUCT", "FERTILIZER", 11]
        ]
    }

    graph = build_basket_dependency_graph(action, state)
    same_asset_pairs = graph.get_same_asset_couplings()

    # Must find coupling between BUY WHEAT and SELL WHEAT
    assert len(same_asset_pairs) >= 1
    found_wheat = any(item == "WHEAT" for _, _, item in same_asset_pairs)
    assert found_wheat, "Expected same-asset market coupling for WHEAT"


def test_dependency_closure_transitive(normal_opening_obs):
    """Verifies that transitive dependency closure encompasses causally linked nodes."""
    state = build_economic_state(normal_opening_obs)
    action = {
        "farmer": ["PASS"],
        "hands": [],
        "market": [
            ["BUY_PRODUCT", "WHEAT", 10],
            ["SELL", "WHEAT", 5],
            ["BUY_PRODUCT", "FERTILIZER", 5]
        ]
    }

    graph = build_basket_dependency_graph(action, state)
    # Seed closure from order 0 (BUY WHEAT)
    seed = {"MKT_0_BUY_PRODUCT_WHEAT"}
    closure = graph.compute_dependency_closure(seed)

    # Order 1 (SELL WHEAT) must be in closure due to price feedback
    assert "MKT_1_SELL_WHEAT" in closure
    # Order 2 (BUY FERT) must be in closure due to cash coupling
    assert "MKT_2_BUY_PRODUCT_FERTILIZER" in closure


def test_independent_actions_no_same_asset_coupling(normal_opening_obs):
    """Verifies that orders on different commodities have no same-asset market edge."""
    state = build_economic_state(normal_opening_obs)
    action = {
        "farmer": ["PASS"],
        "hands": [],
        "market": [
            ["BUY_PRODUCT", "WHEAT", 5],
            ["BUY_PRODUCT", "FERTILIZER", 5]
        ]
    }

    graph = build_basket_dependency_graph(action, state)
    same_asset_pairs = graph.get_same_asset_couplings()
    assert len(same_asset_pairs) == 0
