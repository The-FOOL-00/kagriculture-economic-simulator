# SPDX-License-Identifier: MIT
"""Phase 012 Group 2 Cross-Mechanism Composition Validation (§27, §28).

Verifies multi-mechanism interactions between rescued Group 2 mechanisms:
1. Town Cycle + Resource Conversion
2. Emergency Recovery + Resource Conversion
3. Opponent Preemption + Town Cycle
4. Emergency Recovery + Town Cycle
5. Emergency Recovery + Opponent Preemption

Ensures strict verification of:
- Worker disjointness & compatibility
- Spatiotemporal collision avoidance
- Market order integration
- Exact counterfactual simulation
- Safety certificate compliance
"""

from __future__ import annotations

import copy
import pytest
from typing import Any, Dict, List

from aec.config import AECConfig, BOARD_SIZE
from aec.counterfactual.simulator import CounterfactualSimulator
from aec.ir.economic_state import build_economic_state
from aec.patches.composition import (
    CompositionRelation,
    PatchCompatibilityReport,
    PatchCompositionEngine,
)
from aec.patches.coupled_patch import CoupledPatch, CoupledPatchState
from aec.patches.generator import PatchGenerator
from aec.safety.checks import SafetyChecker


@pytest.fixture
def group2_comp_obs(normal_opening_obs: Dict[str, Any]) -> Dict[str, Any]:
    """Observation with 1 Farmer at [4, 4] and 1 Hand at [2, 2]."""
    obs = copy.deepcopy(normal_opening_obs)
    obs["step"] = 100
    obs["day"] = 4
    obs["hour"] = 4
    obs["farms"][0]["farmer"] = [4, 4]
    obs["farms"][0]["hands"] = [[2, 2]]
    obs["farms"][0]["hires_today"] = 1
    obs["farms"][0]["money"] = 1000.0
    obs["farms"][0]["tiles"][2][2] = {"animal": "COW"}
    obs["private"]["shed"]["WHEAT"] = 10
    obs["private"]["shed"]["STRAWBERRY"] = 10
    obs["private"]["shed"]["MELON"] = 5
    obs["market"]["prices"]["WHEAT"] = 25
    obs["market"]["prices"]["STRAWBERRY"] = 120
    obs["market"]["prices"]["MELON"] = 250
    obs["market"]["prices"]["MILK"] = 160
    return obs


def test_comp_01_town_cycle_plus_resource_conversion_parallel(group2_comp_obs: Dict[str, Any]) -> None:
    """Town Cycle (market sale) + Resource Conversion (Hand 1 feeding cow) compose in parallel."""
    econ = build_economic_state(group2_comp_obs)
    engine = PatchCompositionEngine()

    patch_tc = CoupledPatch(
        patch_id="PATCH_TC_ADVANCE_SALE",
        source_opportunity_id="TC_01",
        mechanism_family="TOWN_CYCLE",
        worker_ids=[],
        actions=[{"farmer": ["PASS"], "hands": [["PASS"]], "market": [["SELL", "STRAWBERRY", 2]]}],
        locations={},
        worker_mutations={},
        market_mutations=[["SELL", "STRAWBERRY", 2]],
        economic_effect=240.0,
    )

    patch_rc = CoupledPatch(
        patch_id="PATCH_RC_FEED_COW",
        source_opportunity_id="RC_01",
        mechanism_family="RESOURCE_CONVERSION",
        worker_ids=[1],
        actions=[{"farmer": ["PASS"], "hands": [["FEED"]], "market": []}],
        locations={1: [(2, 2)]},
        worker_mutations={1: ["FEED"]},
        economic_effect=135.0,
    )

    report = engine.analyze_pair(patch_tc, patch_rc)
    assert report.compatible
    assert report.relation == CompositionRelation.PARALLEL

    composite = engine.compose(patch_tc, patch_rc)
    assert composite is not None
    assert composite.worker_ids == [1]
    assert 1 in composite.worker_mutations
    assert len(composite.actions) == 1
    assert composite.actions[0]["market"] == [["SELL", "STRAWBERRY", 2]]
    assert composite.actions[0]["hands"][0] == ["FEED"]


def test_comp_02_town_cycle_plus_resource_conversion_same_worker_conflict(group2_comp_obs: Dict[str, Any]) -> None:
    """If Town Cycle requires Farmer 0 to walk and Resource Conversion also demands Farmer 0, detect conflict."""
    engine = PatchCompositionEngine()

    patch_tc = CoupledPatch(
        patch_id="PATCH_TC_WALK",
        source_opportunity_id="TC_02",
        mechanism_family="TOWN_CYCLE",
        worker_ids=[0],
        worker_mutations={0: ["NORTH"]},
        economic_effect=50.0,
        expected_horizon=3,
    )

    patch_rc = CoupledPatch(
        patch_id="PATCH_RC_WALK",
        source_opportunity_id="RC_02",
        mechanism_family="RESOURCE_CONVERSION",
        worker_ids=[0],
        worker_mutations={0: ["SOUTH"]},
        economic_effect=40.0,
        expected_horizon=3,
    )

    report = engine.analyze_pair(patch_tc, patch_rc)
    assert not report.compatible
    assert report.relation in (CompositionRelation.MUTUALLY_EXCLUSIVE, CompositionRelation.DOMINATES)

    composite = engine.compose(patch_tc, patch_rc)
    assert composite is None


def test_comp_03_emergency_recovery_dominates_resource_conversion(group2_comp_obs: Dict[str, Any]) -> None:
    """Emergency feed delivery strictly dominates discretionary resource conversion on same worker."""
    engine = PatchCompositionEngine()

    patch_emergency = CoupledPatch(
        patch_id="PATCH_EMERGENCY_FEED",
        source_opportunity_id="EMR_01",
        mechanism_family="EMERGENCY_RECOVERY",
        worker_ids=[1],
        worker_mutations={1: ["FEED"]},
        economic_effect=300.0,  # Avoids high animal death penalty
        expected_horizon=1,
    )

    patch_conversion = CoupledPatch(
        patch_id="PATCH_DISCRETIONARY_RC",
        source_opportunity_id="RC_03",
        mechanism_family="RESOURCE_CONVERSION",
        worker_ids=[1],
        worker_mutations={1: ["PICKUP", "WHEAT", 1]},
        economic_effect=25.0,
        expected_horizon=2,
    )

    report = engine.analyze_pair(patch_emergency, patch_conversion)
    assert not report.compatible
    assert report.relation == CompositionRelation.DOMINATES
    assert "dominates" in report.rationale.lower()


def test_comp_04_opponent_preemption_plus_town_cycle_market_fusion(group2_comp_obs: Dict[str, Any]) -> None:
    """Opponent Preemption selling MELON and Town Cycle advancing STRAWBERRY merge market orders."""
    engine = PatchCompositionEngine()

    patch_preempt = CoupledPatch(
        patch_id="PATCH_OPP_PREEMPT_MELON",
        source_opportunity_id="OPP_01",
        mechanism_family="OPPONENT_PREEMPT_SELL",
        worker_ids=[],
        actions=[{"farmer": ["PASS"], "hands": [["PASS"]], "market": [["SELL", "MELON", 3]]}],
        market_mutations=[["SELL", "MELON", 3]],
        economic_effect=750.0,
    )

    patch_town = CoupledPatch(
        patch_id="PATCH_TOWN_CYCLE_STRAWBERRY",
        source_opportunity_id="TC_03",
        mechanism_family="TOWN_CYCLE",
        worker_ids=[],
        actions=[{"farmer": ["PASS"], "hands": [["PASS"]], "market": [["SELL", "STRAWBERRY", 4]]}],
        market_mutations=[["SELL", "STRAWBERRY", 4]],
        economic_effect=480.0,
    )

    report = engine.analyze_pair(patch_preempt, patch_town)
    assert report.compatible
    assert report.relation == CompositionRelation.PARALLEL

    composite = engine.compose(patch_preempt, patch_town)
    assert composite is not None
    mkt = composite.actions[0]["market"]
    assert ["SELL", "MELON", 3] in mkt
    assert ["SELL", "STRAWBERRY", 4] in mkt
    assert composite.economic_effect == 1230.0


def test_comp_05_emergency_recovery_plus_town_cycle_simulation_fidelity(group2_comp_obs: Dict[str, Any]) -> None:
    """Composed Emergency Recovery + Town Cycle evaluated under exact CounterfactualSimulator."""
    econ = build_economic_state(group2_comp_obs)
    engine = PatchCompositionEngine()

    patch_emr = CoupledPatch(
        patch_id="PATCH_EMR_FEED",
        source_opportunity_id="EMR_02",
        mechanism_family="EMERGENCY_RECOVERY",
        worker_ids=[1],
        actions=[{"farmer": ["PASS"], "hands": [["FEED"]], "market": []}],
        worker_mutations={1: ["FEED"]},
        economic_effect=200.0,
    )

    patch_tc = CoupledPatch(
        patch_id="PATCH_TC_SELL",
        source_opportunity_id="TC_04",
        mechanism_family="TOWN_CYCLE",
        worker_ids=[],
        actions=[{"farmer": ["PASS"], "hands": [["PASS"]], "market": [["SELL", "STRAWBERRY", 2]]}],
        market_mutations=[["SELL", "STRAWBERRY", 2]],
        economic_effect=240.0,
    )

    composite = engine.compose(patch_emr, patch_tc)
    assert composite is not None

    baseline_action = {"farmer": ["PASS"], "hands": [["PASS"]], "market": []}
    sim = CounterfactualSimulator()
    outcome = sim.evaluate(composite, baseline_action, econ, horizon=6)
    assert outcome.fidelity == "VERIFIED"
    assert outcome.spatial_consistency_ok

    checker = SafetyChecker()
    is_safe, violates, _ = checker.verify(composite, outcome, econ, baseline_action)
    assert is_safe
    assert all(violates.values())


def test_comp_06_emergency_recovery_plus_opponent_preemption_disjoint(group2_comp_obs: Dict[str, Any]) -> None:
    """Emergency Recovery on field (Hand 1) + Opponent Preemption in town market compose disjointly."""
    engine = PatchCompositionEngine()

    patch_emr = CoupledPatch(
        patch_id="PATCH_EMR_WAGE",
        source_opportunity_id="EMR_03",
        mechanism_family="EMERGENCY_RECOVERY",
        worker_ids=[1],
        actions=[{"farmer": ["PASS"], "hands": [["PASS"]], "market": [["SELL", "WHEAT", 1]]}],
        market_mutations=[["SELL", "WHEAT", 1]],
        economic_effect=25.0,
    )

    patch_opp = CoupledPatch(
        patch_id="PATCH_OPP_SEED",
        source_opportunity_id="OPP_02",
        mechanism_family="OPPONENT_PREEMPT_SELL",
        worker_ids=[0],
        actions=[{"farmer": ["NORTH"], "hands": [["PASS"]], "market": [["BUY_SEED", "CARROT", 1]]}],
        worker_mutations={0: ["NORTH"]},
        market_mutations=[["BUY_SEED", "CARROT", 1]],
        economic_effect=50.0,
    )

    report = engine.analyze_pair(patch_emr, patch_opp)
    assert report.compatible
    assert report.relation == CompositionRelation.PARALLEL

    composite = engine.compose(patch_emr, patch_opp)
    assert composite is not None
    assert 0 in composite.worker_mutations
    assert composite.actions[0]["farmer"] == ["NORTH"]
    mkt = composite.actions[0]["market"]
    assert ["SELL", "WHEAT", 1] in mkt
    assert ["BUY_SEED", "CARROT", 1] in mkt
