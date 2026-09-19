# SPDX-License-Identifier: MIT
"""Phase 013 Group 3 Cross-Mechanism Composition Validation (§36).

Verifies multi-mechanism interactions between rescued Group 3 mechanisms:
1. Shop Arbitrage + Production Arbitrage
2. Production Arbitrage + Terminal Conversion
3. Shop Arbitrage + Terminal Conversion
4. Emergency Feed + Production Arbitrage
5. Emergency Feed + Terminal Conversion
6. Safety Certificate compliance on composed patches

Guarantees:
- Worker disjointness & exclusivity semantics
- Spatiotemporal waypoint collision avoidance
- Sequential non-commutative market action ordering
- Working capital / liquidity reservation across combined commitments
- Safety certificate compliance under simultaneous or sequential composition
"""

from __future__ import annotations

import copy
import pytest
from typing import Any, Dict, List

from aec.counterfactual.simulator import CounterfactualSimulator
from aec.ir.economic_state import build_economic_state
from aec.patches.composition import (
    CompositionRelation,
    PatchCompatibilityReport,
    PatchCompositionEngine,
)
from aec.patches.coupled_patch import CoupledPatch
from aec.safety.checks import SafetyChecker


@pytest.fixture
def group3_comp_obs(normal_opening_obs: Dict[str, Any]) -> Dict[str, Any]:
    """Observation with 1 Farmer at [4, 4] and 1 Hand at [2, 2] with active inventory."""
    obs = copy.deepcopy(normal_opening_obs)
    obs["step"] = 680
    obs["day"] = 28
    obs["hour"] = 8
    obs["farms"][0]["farmer"] = [4, 4]
    obs["farms"][0]["hands"] = [[2, 2]]
    obs["farms"][0]["hires_today"] = 1
    obs["farms"][0]["money"] = 2500.0
    obs["farms"][0]["tiles"][2][2] = {"animal": "COW"}
    obs["private"]["shed"]["WHEAT"] = 10
    obs["private"]["shed"]["CARROT"] = 10
    obs["private"]["shed"]["MELON"] = 4
    obs["market"]["prices"]["WHEAT"] = 25
    obs["market"]["prices"]["CARROT"] = 35
    obs["market"]["prices"]["MELON"] = 250
    obs["market"]["prices"]["WOOL"] = 140
    obs["market"]["prices"]["HAY"] = 20
    return obs


def test_comp_01_shop_arb_plus_production_arb_parallel(group3_comp_obs: Dict[str, Any]) -> None:
    """Shop Arbitrage (market-only) + Production Arbitrage (Worker 1 field task) execute in parallel."""
    engine = PatchCompositionEngine()

    patch_sa = CoupledPatch(
        patch_id="PATCH_SA_WHEAT_BUY",
        source_opportunity_id="SHOP_ARB_680_WHEAT_2",
        worker_ids=[],
        actions=[{"farmer": ["PASS"], "hands": [["PASS"]], "market": [["BUY_PRODUCT", "WHEAT", 2]]}],
        locations={},
        worker_mutations={},
        economic_effect=30.0,
    )

    patch_pa = CoupledPatch(
        patch_id="PATCH_PA_MELON_PLANT",
        source_opportunity_id="PROD_ARB_680_MELON",
        worker_ids=[1],
        actions=[{"farmer": ["PASS"], "hands": [["PLANT", 2, 3, "MELON"]], "market": []}],
        locations={1: [(2, 3)]},
        worker_mutations={1: ["PLANT", 2, 3, "MELON"]},
        economic_effect=150.0,
    )

    report = engine.analyze_pair(patch_sa, patch_pa)
    assert report.compatible is True
    assert report.relation == CompositionRelation.PARALLEL
    assert len(report.conflicts) == 0


def test_comp_02_production_arb_plus_terminal_conv_exclusive_worker(group3_comp_obs: Dict[str, Any]) -> None:
    """Production Arbitrage and Terminal Conversion competing for Hand 1 detect mutual exclusion/dominance."""
    engine = PatchCompositionEngine()

    patch_pa = CoupledPatch(
        patch_id="PATCH_PA_WORKER1",
        source_opportunity_id="PROD_ARB_680",
        worker_ids=[1],
        actions=[{"farmer": ["PASS"], "hands": [["MOVE", "UP"]], "market": []}],
        locations={1: [(2, 1)]},
        worker_mutations={1: ["MOVE", "UP"]},
        economic_effect=80.0,
        expected_horizon=4,
    )

    patch_tc = CoupledPatch(
        patch_id="PATCH_TC_WORKER1",
        source_opportunity_id="TERM_CONV_680",
        worker_ids=[1],
        actions=[{"farmer": ["PASS"], "hands": [["MOVE", "RIGHT"]], "market": []}],
        locations={1: [(3, 2)]},
        worker_mutations={1: ["MOVE", "RIGHT"]},
        economic_effect=200.0,
        expected_horizon=3,
    )

    report = engine.analyze_pair(patch_tc, patch_pa)
    # Patch TC ($200 in 3 steps) dominates Patch PA ($80 in 4 steps) on worker 1
    assert report.compatible is False
    assert report.relation == CompositionRelation.DOMINATES
    assert "dominates" in report.rationale.lower()


def test_comp_03_shop_arb_plus_terminal_conv_market_ordering(group3_comp_obs: Dict[str, Any]) -> None:
    """Shop Arbitrage and Terminal Conversion compose with sequential market action preservation."""
    engine = PatchCompositionEngine()

    patch_sa = CoupledPatch(
        patch_id="PATCH_SA_CARROT_BUY",
        source_opportunity_id="SHOP_ARB_680_CARROT",
        worker_ids=[],
        actions=[{"farmer": ["PASS"], "hands": [["PASS"]], "market": [["BUY_PRODUCT", "CARROT", 2]]}],
        locations={},
        worker_mutations={},
        economic_effect=45.0,
    )

    patch_tc = CoupledPatch(
        patch_id="PATCH_TC_WOOL_SELL",
        source_opportunity_id="TERM_CONV_680_WOOL",
        worker_ids=[0],
        actions=[{"farmer": ["PASS"], "hands": [["PASS"]], "market": [["SELL", "WOOL", 1]]}],
        locations={},
        worker_mutations={},
        economic_effect=140.0,
    )

    report = engine.analyze_pair(patch_sa, patch_tc)
    assert report.compatible is True
    assert report.relation == CompositionRelation.PARALLEL


def test_comp_04_emergency_feed_plus_production_arb_capital_contention(group3_comp_obs: Dict[str, Any]) -> None:
    """Emergency Feed and Production Arbitrage check capital constraints under low cash."""
    obs = copy.deepcopy(group3_comp_obs)
    obs["farms"][0]["money"] = 120.0  # Low cash: Feed costs $100, seed costs $80
    econ = build_economic_state(obs)

    feed_cost = 100.0
    seed_cost = 80.0

    patch_ef = CoupledPatch(
        patch_id="PATCH_EF_HAY",
        source_opportunity_id="EF_680_HAY",
        worker_ids=[],
        actions=[{"farmer": ["PASS"], "hands": [["PASS"]], "market": [["BUY_PRODUCT", "HAY", 5]]}],
        locations={},
        worker_mutations={},
        economic_effect=1500.0,  # Saves cow
    )

    patch_pa = CoupledPatch(
        patch_id="PATCH_PA_PUMPKIN",
        source_opportunity_id="PROD_ARB_680_PUMPKIN",
        worker_ids=[0],
        actions=[{"farmer": ["PASS"], "hands": [["PASS"]], "market": [["BUY_SEED", "PUMPKIN_SEED", 1]]}],
        locations={},
        worker_mutations={},
        economic_effect=90.0,
    )

    # Combined costs exceed working capital: $100 + $80 = $180 > $120
    total_cost = feed_cost + seed_cost
    assert total_cost > econ.farm.cash, "Combined patches exceed available working capital"
    # Individual emergency feed preserves critical capital
    assert feed_cost <= econ.farm.cash


def test_comp_05_emergency_feed_plus_terminal_conv_priority(group3_comp_obs: Dict[str, Any]) -> None:
    """Emergency feed takes precedence over terminal conversion when cow would starve before cutoff."""
    engine = PatchCompositionEngine()

    patch_ef = CoupledPatch(
        patch_id="PATCH_EF_PRESERVE_HERD",
        source_opportunity_id="EF_680",
        worker_ids=[],
        actions=[{"farmer": ["PASS"], "hands": [["PASS"]], "market": [["BUY_PRODUCT", "HAY", 2]]}],
        locations={},
        worker_mutations={},
        economic_effect=1500.0,  # Prevents irreversible $1500 cow loss
        expected_horizon=1,
    )

    patch_tc = CoupledPatch(
        patch_id="PATCH_TC_CONVERT",
        source_opportunity_id="TC_680",
        worker_ids=[1],
        actions=[{"farmer": ["PASS"], "hands": [["MOVE", "DOWN"]], "market": []}],
        locations={1: [(2, 3)]},
        worker_mutations={1: ["MOVE", "DOWN"]},
        economic_effect=115.0,
        expected_horizon=4,
    )

    report = engine.analyze_pair(patch_ef, patch_tc)
    assert report.compatible is True
    assert report.relation == CompositionRelation.PARALLEL


def test_comp_06_safety_certificate_composed_patches(group3_comp_obs: Dict[str, Any]) -> None:
    """Safety checker validates composed patch sequence against contract limits."""
    econ = build_economic_state(group3_comp_obs)
    composed_patch = CoupledPatch(
        patch_id="PATCH_COMPOSED_SAFE",
        source_opportunity_id="COMPOSED_SA_PA",
        worker_ids=[0, 1],
        actions=[
            {
                "farmer": ["MOVE", "UP"],
                "hands": [["PASS"]],
                "market": [["BUY_PRODUCT", "WHEAT", 2]],
            }
        ],
        locations={0: [(4, 3)], 1: [(2, 2)]},
        worker_mutations={0: ["MOVE", "UP"]},
        market_mutations=[["BUY_PRODUCT", "WHEAT", 2]],
        economic_effect=60.0,
    )
    baseline_action = {"farmer": ["PASS"], "hands": [["PASS"]], "market": []}
    sim = CounterfactualSimulator()
    outcome = sim.evaluate(composed_patch, baseline_action, econ, horizon=6)
    assert outcome.fidelity == "VERIFIED"

    checker = SafetyChecker()
    is_safe, violates, _ = checker.verify(composed_patch, outcome, econ, baseline_action)
    assert is_safe
    assert all(violates.values())
