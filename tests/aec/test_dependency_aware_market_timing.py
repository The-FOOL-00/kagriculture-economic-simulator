# SPDX-License-Identifier: MIT
"""Unit and adversarial test suite for DEPENDENCY_AWARE_MARKET_TIMING (§6, §8, §9)."""

import pytest
from aec.config import AECConfig, ScientificStatus
from aec.ir.dependency_graph import (
    ActionBasketDependencyGraph,
    ActionNode,
    CausalEdgeType,
    build_basket_dependency_graph,
)
from aec.market.transformations import transform_dependency_aware_market_timing
from aec.opportunities.market import MarketOpportunityAnalyzer
from aec.patches.generator import PatchGenerator
from aec.safety.checks import SafetyChecker
from aec.counterfactual.simulator import SimulationOutcome


def test_adversarial_turn_575_fixture_no_inversion():
    """Turn 575 failure mode from EXP-AEC-002: BUY_PRODUCT WHEAT followed by SELL WHEAT.
    
    Verifies that DEPENDENCY_AWARE_MARKET_TIMING detects the SAME_ASSET_MARKET_COUPLING
    and strictly refuses to invert BUY -> SELL, preventing the -$9.00 price degradation.
    """
    orders = [
        ["BUY_PRODUCT", "WHEAT", 16],
        ["SELL", "WHEAT", 2]
    ]
    reordered, status = transform_dependency_aware_market_timing(orders)
    
    # Must preserve exact order: BUY must remain before SELL
    assert reordered == orders, "Must not invert BUY_PRODUCT before SELL for the same asset"
    assert status == ScientificStatus.EXPERIMENTAL


def test_uncoupled_sell_promoted_ahead_of_capital():
    """Uncoupled SELL (e.g. CARROT) precedes capital orders (HIRE, BUY_LAND, BUY_SEED)."""
    orders = [
        ["HIRE", 1],
        ["BUY_LAND"],
        ["SELL", "CARROT", 25]
    ]
    reordered, _ = transform_dependency_aware_market_timing(orders)
    
    # SELL CARROT should be placed at index 0 to generate cash for HIRE and BUY_LAND
    assert reordered[0] == ["SELL", "CARROT", 25]
    assert reordered[1:] == [["HIRE", 1], ["BUY_LAND"]]


def test_cross_asset_order_independence():
    """Different commodities: SELL CARROT can precede BUY_PRODUCT WHEAT."""
    orders = [
        ["BUY_PRODUCT", "WHEAT", 10],
        ["SELL", "CARROT", 5]
    ]
    reordered, _ = transform_dependency_aware_market_timing(orders)
    
    # Uncoupled CARROT sell moves ahead of WHEAT buy to generate cash
    assert reordered[0] == ["SELL", "CARROT", 5]
    assert reordered[1] == ["BUY_PRODUCT", "WHEAT", 10]


def test_multi_order_same_asset_transitive_preservation():
    """Multiple orders on same commodity preserve queue order."""
    orders = [
        ["BUY_PRODUCT", "WHEAT", 10],
        ["BUY_PRODUCT", "WHEAT", 5],
        ["SELL", "WHEAT", 2],
        ["HIRE", 1]
    ]
    reordered, _ = transform_dependency_aware_market_timing(orders)
    
    # WHEAT orders must maintain internal relative order
    wheat_ops = [o[0] for o in reordered if len(o) > 1 and o[1] == "WHEAT"]
    assert wheat_ops == ["BUY_PRODUCT", "BUY_PRODUCT", "SELL"]
    # HIRE remains after
    assert reordered[-1] == ["HIRE", 1]


def test_dependency_graph_same_asset_edge_construction():
    """Verifies that ActionBasketDependencyGraph constructs SAME_ASSET_MARKET_COUPLING."""
    action = {
        "market": [
            ["BUY_PRODUCT", "WHEAT", 16],
            ["SELL", "WHEAT", 2]
        ],
        "farmer": ["PASS"],
        "hands": []
    }
    graph = build_basket_dependency_graph(action, None)
    
    same_asset_pairs = graph.get_same_asset_couplings()
    assert len(same_asset_pairs) == 1
    src, tgt, item = same_asset_pairs[0]
    assert item == "WHEAT"
    assert "MKT_0_BUY_PRODUCT_WHEAT" in src
    assert "MKT_1_SELL_WHEAT" in tgt


def test_malformed_and_edge_case_orders_safe_fail():
    """Ensures parser and transformer fail closed without unhandled exceptions."""
    malformed_orders = [
        [],
        ["INVALID_OP"],
        ["SELL"],  # missing item
        None,
        ["BUY_PRODUCT", "WHEAT", "NOT_A_NUMBER"]
    ]
    reordered, _ = transform_dependency_aware_market_timing(malformed_orders)
    # Should not crash, returns valid list
    assert isinstance(reordered, list)


def test_market_opportunity_analyzer_rejects_turn_575_pattern():
    """Verifies that MarketOpportunityAnalyzer does not emit an opportunity for Turn 575 pattern."""
    class MockEcon:
        step = 575
        market = None

    analyzer = MarketOpportunityAnalyzer()
    action = {
        "market": [
            ["BUY_PRODUCT", "WHEAT", 16],
            ["SELL", "WHEAT", 2]
        ]
    }
    opps = analyzer.analyze(MockEcon(), [], action)
    # Because reordered == orders, no opportunity should be emitted
    assert len(opps) == 0, "Should not propose reordering when same-asset coupling prevents inversion"


def test_safety_checker_rejects_unknown_and_failed_fidelity():
    """Verifies SafetyChecker hard-rejects UNKNOWN and FAILED fidelity."""
    checker = SafetyChecker()
    patch = PatchGenerator().generate_patches([], None, {"market": []})
    from aec.patches.patch import CoupledPatch
    p = CoupledPatch(patch_id="P1", source_opportunity_id="OPP1", mechanism_family="DEPENDENCY_AWARE_MARKET_TIMING")
    
    # UNKNOWN fidelity
    outcome_unknown = SimulationOutcome(
        candidate_final_money=3500.0,
        baseline_final_money=3000.0,
        delta_our_money=500.0,
        candidate_opp_final_money=3000.0,
        baseline_opp_final_money=3000.0,
        delta_opponent_money=0.0,
        delta_terminal_margin=500.0,
        candidate_overflow_units=0,
        candidate_sold={},
        baseline_sold={},
        intermediate_solvency_ok=True,
        horizon=4,
        fidelity="UNKNOWN"
    )
    passed_unknown, checks_u, reason_u = checker.verify(p, outcome_unknown, None, {"market": []})
    assert passed_unknown is False
    assert checks_u["fidelity_ok"] is False

    # FAILED fidelity
    outcome_failed = SimulationOutcome(
        candidate_final_money=3500.0,
        baseline_final_money=3000.0,
        delta_our_money=500.0,
        candidate_opp_final_money=3000.0,
        baseline_opp_final_money=3000.0,
        delta_opponent_money=0.0,
        delta_terminal_margin=500.0,
        candidate_overflow_units=0,
        candidate_sold={},
        baseline_sold={},
        intermediate_solvency_ok=True,
        horizon=4,
        fidelity="FAILED"
    )
    passed_failed, checks_f, reason_f = checker.verify(p, outcome_failed, None, {"market": []})
    assert passed_failed is False
    assert checks_f["fidelity_ok"] is False
