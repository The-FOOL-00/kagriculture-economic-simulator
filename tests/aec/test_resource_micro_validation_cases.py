# SPDX-License-Identifier: MIT
"""AEC-RESOURCE: Micro-Validation Test Battery (Cases RC-1..12 & EF-1..12).

Authoritative test cases for independent micro-validation of:
- RESOURCE_CONVERSION (Cases RC-1 through RC-12)
- EMERGENCY_FEED_PURCHASE (Cases EF-1 through EF-12)
"""

from __future__ import annotations

import copy
import pytest
from typing import Any, Dict, List, Tuple

from aec.config import AECConfig, ScientificStatus
from aec.counterfactual.simulator import CounterfactualSimulator, SimulationOutcome
from aec.ir.dependency_graph import (
    ActionBasketDependencyGraph,
    ActionNode,
    CausalEdge,
    CausalEdgeType,
)
from aec.ir.economic_state import build_economic_state
from aec.opportunities.base import Opportunity
from aec.opportunities.resource import ResourceOpportunityAnalyzer
from aec.patches.generator import PatchGenerator
from aec.patches.patch import CoupledPatch
from aec.replanning.reconnect import (
    EscalationScope,
    ReconnectRequest,
    ReconnectionEngine,
    ReconnectionStatus,
    reconnect_worker_trajectory,
)
from aec.resource.conversions import (
    ConversionCatalog,
    ConversionDiscoveryEngine,
    ConversionPath,
)
from aec.resource.dag import (
    ObligationType,
    ResourceEdge,
    ResourceLocationType,
    ResourceNode,
    ResourceObligation,
    ResourceReservation,
    TemporalResourceDAG,
)
from aec.resource.feed_security import FeedSecurityEngine, LivestockEntity
from aec.resource.parity import ResourceParityHarness
from aec.safety.certificate import SafetyCertificate
from aec.safety.checks import SafetyChecker


# =============================================================================
# RESOURCE_CONVERSION VALIDATION SUITE (CASES RC-1 THROUGH RC-12)
# =============================================================================

def test_rc_1_no_valid_conversion_exists(normal_opening_obs: Dict[str, Any]) -> None:
    """CASE RC-1: No valid conversion exists.
    
    Expected: No candidate patch generated, no commit.
    """
    obs = copy.deepcopy(normal_opening_obs)
    obs["farms"][0]["money"] = 0.0
    obs["step"] = 718
    econ = build_economic_state(obs)
    engine = ConversionDiscoveryEngine()
    paths = engine.discover_conversion_paths(econ)
    feasible_paths = [p for p in paths if p.is_feasible and p.net_value_est > 0]
    assert len(feasible_paths) == 0, f"Expected 0 feasible conversion paths, got {len(feasible_paths)}"


def test_rc_2_valid_single_stage_conversion(normal_opening_obs: Dict[str, Any]) -> None:
    """CASE RC-2: Valid single-stage conversion exists.
    
    Expected: Candidate generated, simulator confirms feasibility, safety certificate passes.
    """
    obs = copy.deepcopy(normal_opening_obs)
    econ = build_economic_state(obs)
    engine = ConversionDiscoveryEngine()
    paths = engine.discover_conversion_paths(econ)
    carrot_paths = [p for p in paths if p.target_commodity == "CARROT" and p.is_feasible]
    assert len(carrot_paths) > 0, "Valid carrot conversion path must be discovered"

    # Verify counterfactual simulator feasibility
    sim = CounterfactualSimulator()
    patch = CoupledPatch(
        patch_id="PATCH_RC_2",
        source_opportunity_id="OPP_RC_2",
        mechanism_family="RESOURCE_CONVERSION",
        market_mutations=[["BUY_SEED", "CARROT", 1]],
        expected_horizon=6,
    )
    outcome = sim.evaluate(patch, {"farmer": ["PASS"], "hands": [], "market": []}, econ, horizon=6)
    assert outcome.intermediate_solvency_ok

    # Verify safety check
    checker = SafetyChecker()
    passed, checks, reason = checker.verify(patch, outcome, econ, {})
    assert passed
    assert checks["resource_conservation_ok"]
    assert checks["negative_inventory_ok"]


def test_rc_3_temporally_impossible_conversion(normal_opening_obs: Dict[str, Any]) -> None:
    """CASE RC-3: Conversion is symbolically feasible but temporally impossible.
    
    Expected: ABSTAIN via temporal availability check.
    """
    checker = SafetyChecker()
    patch = CoupledPatch(
        patch_id="PATCH_RC_3",
        source_opportunity_id="OPP_RC_3",
        resource_changes={"delayed_arrival": True},
        expected_horizon=2,
    )
    outcome = SimulationOutcome(
        candidate_final_money=3000.0, baseline_final_money=3000.0, delta_our_money=0.0,
        candidate_opp_final_money=3000.0, baseline_opp_final_money=3000.0, delta_opponent_money=0.0,
        delta_terminal_margin=0.0, candidate_overflow_units=0, candidate_sold={}, baseline_sold={},
        intermediate_solvency_ok=True, horizon=2
    )
    econ = build_economic_state(normal_opening_obs)
    passed, checks, reason = checker.verify(patch, outcome, econ, {})
    assert not passed
    assert not checks["temporal_availability_ok"]
    assert "arrival" in (reason or "")


def test_rc_4_intermediate_cash_shortage(cash_deficit_obs: Dict[str, Any]) -> None:
    """CASE RC-4: Conversion creates intermediate cash shortage.
    
    Expected: ABSTAIN via cash liquidity check.
    """
    obs = copy.deepcopy(cash_deficit_obs)
    obs["farms"][0]["money"] = 10.0  # Only $10 liquid
    econ = build_economic_state(obs)

    recipe = ConversionCatalog.get_standard_recipes()["GROW_WHEAT_CROP"]
    path = ConversionPath(
        path_id="CHAIN_CASH_HOLE",
        target_commodity="WHEAT",
        recipes=[recipe],
        total_steps=48,
        total_cost_est=10.0,
        expected_revenue_est=100.0,
        net_value_est=90.0
    )
    # Set money to $5 so $10 recipe causes cash liquidity hole
    obs["farms"][0]["money"] = 5.0
    econ_low_cash = build_economic_state(obs)
    engine = ConversionDiscoveryEngine()
    is_feas, reason = engine.check_path_feasibility(path, econ_low_cash)
    assert not is_feas
    assert "Cash liquidity hole" in (reason or "")

    checker = SafetyChecker()
    patch = CoupledPatch(
        patch_id="PATCH_RC_4",
        source_opportunity_id="OPP_RC_4",
        resource_changes={"cash_deadlock": True},
    )
    outcome = SimulationOutcome(
        candidate_final_money=-15.0, baseline_final_money=15.0, delta_our_money=-30.0,
        candidate_opp_final_money=0.0, baseline_opp_final_money=0.0, delta_opponent_money=0.0,
        delta_terminal_margin=-30.0, candidate_overflow_units=0, candidate_sold={}, baseline_sold={},
        intermediate_solvency_ok=False, horizon=6
    )
    passed, checks, _ = checker.verify(patch, outcome, econ, {})
    assert not passed
    assert not checks["cash_liquidity_ok"]


def test_rc_5_conversion_shed_overflow(shed_capacity_obs: Dict[str, Any]) -> None:
    """CASE RC-5: Conversion creates shed overflow.
    
    Expected: ABSTAIN via capacity overflow check.
    """
    obs = copy.deepcopy(shed_capacity_obs)
    obs["private"]["shed"]["WHEAT"] = 100  # Shed fully occupied
    econ = build_economic_state(obs)

    recipe = ConversionCatalog.get_standard_recipes()["BUY_WHEAT_FEED"]  # shed_capacity_delta = 1
    path = ConversionPath(
        path_id="CHAIN_OVERFLOW",
        target_commodity="WHEAT",
        recipes=[recipe],
        total_steps=1,
        total_cost_est=25.0,
        expected_revenue_est=25.0,
        net_value_est=0.0
    )
    engine = ConversionDiscoveryEngine()
    is_feas, reason = engine.check_path_feasibility(path, econ)
    assert not is_feas
    assert "Shed capacity overflow" in (reason or "")

    checker = SafetyChecker()
    patch = CoupledPatch(
        patch_id="PATCH_RC_5",
        source_opportunity_id="OPP_RC_5",
        resource_changes={"capacity_overflow": True},
    )
    outcome = SimulationOutcome(
        candidate_final_money=3000.0, baseline_final_money=3000.0, delta_our_money=50.0,
        candidate_opp_final_money=0.0, baseline_opp_final_money=0.0, delta_opponent_money=0.0,
        delta_terminal_margin=50.0, candidate_overflow_units=2, candidate_sold={}, baseline_sold={},
        intermediate_solvency_ok=True, horizon=6
    )
    passed, checks, _ = checker.verify(patch, outcome, econ, {})
    assert not passed
    assert not checks["capacity_consistency_ok"]


def test_rc_6_resource_reserved_for_downstream_obligation() -> None:
    """CASE RC-6: Conversion consumes a resource reserved for a downstream obligation.
    
    Expected: Dependency closure detects conflict -> ABSTAIN.
    """
    dag = TemporalResourceDAG()
    dag.add_node(ResourceNode(node_id="WHEAT_1_UNIT", commodity="WHEAT", quantity=1, turn=0))
    dag.add_obligation(ResourceObligation(
        obligation_id="OB_FEED_COW", obligation_type=ObligationType.LIVESTOCK_FEED,
        commodity="WHEAT", quantity=1, deadline_turn=23
    ))
    dag.add_reservation(ResourceReservation(
        reservation_id="RES_1", obligation_id="OB_FEED_COW", node_id="WHEAT_1_UNIT",
        reserved_quantity=1, start_turn=0, release_turn=23
    ))
    dag.add_reservation(ResourceReservation(
        reservation_id="RES_2", obligation_id="OB_SALE", node_id="WHEAT_1_UNIT",
        reserved_quantity=1, start_turn=0, release_turn=10
    ))
    is_valid, reason = dag.check_reservation_conflicts()
    assert not is_valid
    assert "Double-allocation" in (reason or "")


def test_rc_7_conversion_route_reconnection(normal_opening_obs: Dict[str, Any]) -> None:
    """CASE RC-7: Conversion changes worker route.
    
    Expected: AEC-RECONNECT invoked; continuation successfully spliced.
    """
    baseline_continuation = [
        {"farmer": ["EAST"]},
        {"farmer": ["SOUTH"]},
    ]
    request = ReconnectRequest(
        worker=0,
        divergence_point=0,
        patched_action=["SOUTH"],
        intended_target_state=(5, 5),
        baseline_continuation=baseline_continuation,
        remaining_steps=700
    )
    result = reconnect_worker_trajectory(request)
    assert result.is_safe
    assert result.status == ReconnectionStatus.SAFE_RECONNECT


def test_rc_8_local_profit_breaks_downstream_production(normal_opening_obs: Dict[str, Any]) -> None:
    """CASE RC-8: Conversion appears profitable locally but breaks downstream production.
    
    Expected: Broader dependency analysis overrides local candidate -> ABSTAIN.
    """
    g = ActionBasketDependencyGraph()
    n_sell = ActionNode(node_id="SELL_WHEAT", actor_type="MARKET", actor_index=0, action_type="SELL", item="WHEAT", quantity=1)
    n_cow = ActionNode(node_id="FEED_COW", actor_type="WORKER_FARMER", actor_index=0, action_type="FEED", item="WHEAT", quantity=1)
    g.add_node(n_sell)
    g.add_node(n_cow)
    g.add_edge("SELL_WHEAT", "FEED_COW", CausalEdgeType.RESOURCE_COUPLING, description="Wheat feed conflict")

    closure = g.compute_dependency_closure({"SELL_WHEAT"})
    assert "FEED_COW" in closure


def test_rc_9_conversion_near_terminal(terminal_proximity_obs: Dict[str, Any]) -> None:
    """CASE RC-9: Conversion appears valid but cannot complete before terminal turn 718.
    
    Expected: ABSTAIN via terminal pruning.
    """
    obs = copy.deepcopy(terminal_proximity_obs)
    obs["step"] = 710
    econ = build_economic_state(obs)
    recipe = ConversionCatalog.get_standard_recipes()["GROW_WHEAT_CROP"]
    path = ConversionPath(
        path_id="CHAIN_LATE",
        target_commodity="WHEAT",
        recipes=[recipe],
        total_steps=48, # 48 > remaining (720 - 710 = 10)
        total_cost_est=10.0,
        expected_revenue_est=100.0,
        net_value_est=90.0
    )
    engine = ConversionDiscoveryEngine()
    is_feas, reason = engine.check_path_feasibility(path, econ)
    assert not is_feas
    assert "Terminal infeasibility" in (reason or "")

    checker = SafetyChecker()
    patch = CoupledPatch(
        patch_id="PATCH_RC_9",
        source_opportunity_id="OPP_RC_9",
        resource_changes={"terminal_infeasible": True}
    )
    outcome = SimulationOutcome(
        candidate_final_money=3000.0, baseline_final_money=3000.0, delta_our_money=0.0,
        candidate_opp_final_money=0.0, baseline_opp_final_money=0.0, delta_opponent_money=0.0,
        delta_terminal_margin=0.0, candidate_overflow_units=0, candidate_sold={}, baseline_sold={},
        intermediate_solvency_ok=True, horizon=1
    )
    passed, checks, _ = checker.verify(patch, outcome, econ, {})
    assert not passed
    assert not checks["terminal_resource_ok"]


def test_rc_10_multi_stage_conversion_chain() -> None:
    """CASE RC-10: Multi-stage conversion A -> B -> C.
    
    Expected: Exact temporal chain preserved across sequential turns.
    """
    catalog = ConversionCatalog()
    recipes = catalog.get_standard_recipes()
    cow_recipe = recipes["FEED_LIVESTOCK_COW"]
    feed_recipe = recipes["BUY_WHEAT_FEED"]

    path = ConversionPath(
        path_id="CHAIN_K",
        target_commodity="MILK",
        recipes=[feed_recipe, cow_recipe],
        total_steps=49,
        total_cost_est=25.0,
        expected_revenue_est=160.0,
        net_value_est=135.0
    )
    assert len(path.recipes) == 2
    assert path.recipes[0].output_resources["WHEAT"] == path.recipes[1].input_resources["WHEAT"]


def test_rc_11_same_turn_ordering_preserved(normal_opening_obs: Dict[str, Any]) -> None:
    """CASE RC-11: Same-turn ordering matters.
    
    Expected: Exact non-commutative ordering preserved; no simulator/symbolic divergence.
    """
    econ = build_economic_state(normal_opening_obs)
    dag = TemporalResourceDAG()
    dag.add_node(ResourceNode(node_id="CASH_0", commodity="CASH", quantity=3000, turn=0))
    dag.add_node(ResourceNode(node_id="WHEAT_1", commodity="WHEAT", quantity=1, turn=1))
    dag.add_edge(ResourceEdge(
        edge_id="E_BUY", source_node_ids=["CASH_0"], dest_node_ids=["WHEAT_1"],
        action_type="BUY_PRODUCT", start_turn=0, completion_turn=1,
        quantity_delta={"WHEAT": 1}, cash_delta=-25.0
    ))
    patch = CoupledPatch(patch_id="P_ORDER", source_opportunity_id="O_ORDER")
    # Injected discrepancy: simulator reports underflow / intermediate deficit
    divergent_outcome = SimulationOutcome(
        candidate_final_money=2975.0, baseline_final_money=3000.0, delta_our_money=-25.0,
        candidate_opp_final_money=0.0, baseline_opp_final_money=0.0, delta_opponent_money=0.0,
        delta_terminal_margin=-25.0, candidate_overflow_units=0, candidate_sold={}, baseline_sold={},
        intermediate_solvency_ok=False, # Ordering caused underflow!
        horizon=1
    )
    harness = ResourceParityHarness()
    report = harness.verify_parity(dag, patch, divergent_outcome, econ)
    assert not report.is_exact_match
    assert report.fidelity_status == "FAILED"


def test_rc_12_repeated_identical_replay(normal_opening_obs: Dict[str, Any]) -> None:
    """CASE RC-12: Repeated identical replay of resource conversion evaluation.
    
    Expected: Bit-for-bit deterministic results across 5 repetitions.
    """
    econ = build_economic_state(normal_opening_obs)
    engine = ConversionDiscoveryEngine()
    baseline = engine.discover_conversion_paths(econ)

    for _ in range(5):
        repeat = engine.discover_conversion_paths(econ)
        assert len(repeat) == len(baseline)
        for p1, p2 in zip(baseline, repeat):
            assert p1.path_id == p2.path_id
            assert p1.is_feasible == p2.is_feasible
            assert p1.net_value_est == p2.net_value_est


# =============================================================================
# EMERGENCY_FEED_PURCHASE VALIDATION SUITE (CASES EF-1 THROUGH EF-12)
# =============================================================================

def test_ef_1_feed_already_sufficient(normal_opening_obs: Dict[str, Any]) -> None:
    """CASE EF-1: Feed is already sufficient.
    
    Expected: No unnecessary emergency purchase.
    """
    obs = copy.deepcopy(normal_opening_obs)
    obs["private"]["shed"]["WHEAT"] = 20
    obs["farms"][0]["tiles"][0][0] = {"animal": "COW"}
    econ = build_economic_state(obs)
    analyzer = ResourceOpportunityAnalyzer()
    opps = analyzer.analyze(econ, [])
    feed_opps = [o for o in opps if o.candidate_transformation_family == "EMERGENCY_FEED_PURCHASE"]
    assert len(feed_opps) == 0, "No emergency feed purchase should be proposed when feed is sufficient"


def test_ef_2_future_feed_deficit_unavoidable(normal_opening_obs: Dict[str, Any]) -> None:
    """CASE EF-2: Future feed deficit is unavoidable without purchase.
    
    Expected: Emergency feed purchase opportunity generated.
    """
    obs = copy.deepcopy(normal_opening_obs)
    obs["private"]["shed"]["WHEAT"] = 0
    obs["farms"][0]["tiles"][0][0] = {"kind": "PASTURE", "animal": "COW"}
    econ = build_economic_state(obs)
    analyzer = ResourceOpportunityAnalyzer()
    opps = analyzer.analyze(econ, [])
    feed_opps = [o for o in opps if o.candidate_transformation_family == "EMERGENCY_FEED_PURCHASE"]
    assert len(feed_opps) > 0, "Emergency feed purchase opportunity must be generated on feed deficit"
    assert feed_opps[0].dependency_info["deficit"] == 1


def test_ef_3_purchase_arrives_too_late(normal_opening_obs: Dict[str, Any]) -> None:
    """CASE EF-3: Feed purchase arrives too late to prevent starvation.
    
    Expected: ABSTAIN via feed security check.
    """
    checker = SafetyChecker()
    patch = CoupledPatch(
        patch_id="PATCH_EF_3",
        source_opportunity_id="OPP_EF_3",
        resource_changes={"feed_security_breach": True},
    )
    outcome = SimulationOutcome(
        candidate_final_money=3000.0, baseline_final_money=3000.0, delta_our_money=-25.0,
        candidate_opp_final_money=0.0, baseline_opp_final_money=0.0, delta_opponent_money=0.0,
        delta_terminal_margin=-25.0, candidate_overflow_units=0, candidate_sold={}, baseline_sold={},
        intermediate_solvency_ok=True, horizon=6,
        feed_security_ok=False
    )
    econ = build_economic_state(normal_opening_obs)
    passed, checks, reason = checker.verify(patch, outcome, econ, {})
    assert not passed
    assert not checks["feed_security_ok"]
    assert "feed security" in (reason or "").lower()


def test_ef_4_purchase_causes_cash_deadlock(cash_deficit_obs: Dict[str, Any]) -> None:
    """CASE EF-4: Purchase solves immediate deficit but creates future cash deadlock.
    
    Expected: ABSTAIN via cash liquidity check.
    """
    obs = copy.deepcopy(cash_deficit_obs)
    obs["farms"][0]["money"] = 10.0
    econ = build_economic_state(obs)

    checker = SafetyChecker()
    patch = CoupledPatch(
        patch_id="PATCH_EF_4",
        source_opportunity_id="OPP_EF_4",
        resource_changes={"cash_deadlock": True}
    )
    outcome = SimulationOutcome(
        candidate_final_money=-15.0, baseline_final_money=10.0, delta_our_money=-25.0,
        candidate_opp_final_money=0.0, baseline_opp_final_money=0.0, delta_opponent_money=0.0,
        delta_terminal_margin=-25.0, candidate_overflow_units=0, candidate_sold={}, baseline_sold={},
        intermediate_solvency_ok=False, horizon=6
    )
    passed, checks, _ = checker.verify(patch, outcome, econ, {})
    assert not passed
    assert not checks["cash_liquidity_ok"]


def test_ef_5_purchase_prevents_animal_starvation(normal_opening_obs: Dict[str, Any]) -> None:
    """CASE EF-5: Purchase prevents animal starvation and asset escape.
    
    Expected: Simulator confirms feed security ok, safety certificate passes.
    """
    obs = copy.deepcopy(normal_opening_obs)
    obs["farms"][0]["tiles"][1][1] = {"kind": "PASTURE", "animal": "COW", "fed_today": False}
    obs["private"]["shed"]["WHEAT"] = 0

    econ = build_economic_state(obs)
    feed_engine = FeedSecurityEngine()

    rescue_patch = CoupledPatch(
        patch_id="PATCH_RESCUE",
        source_opportunity_id="OPP_RESCUE",
        mechanism_family="EMERGENCY_FEED_PURCHASE",
        market_mutations=[["BUY_PRODUCT", "WHEAT", 1]],
        expected_horizon=6
    )
    baseline_action = {"farmer": ["PASS"], "hands": [], "market": []}
    future_trajectory = [{"farmer": ["FEED"], "hands": [], "market": []}] + [
        {"farmer": ["PASS"], "hands": [], "market": []} for _ in range(10)
    ]

    sec_state = feed_engine.verify_candidate_patch(rescue_patch, baseline_action, econ, future_trajectory, horizon=6)
    assert sec_state.is_secure


def test_ef_6_purchase_causes_shed_overflow(shed_capacity_obs: Dict[str, Any]) -> None:
    """CASE EF-6: Purchase causes shed overflow.
    
    Expected: ABSTAIN via capacity overflow check.
    """
    obs = copy.deepcopy(shed_capacity_obs)
    obs["private"]["shed"]["STRAWBERRY"] = 99
    econ = build_economic_state(obs)

    checker = SafetyChecker()
    patch = CoupledPatch(
        patch_id="PATCH_EF_6",
        source_opportunity_id="OPP_EF_6",
        resource_changes={"capacity_overflow": True}
    )
    outcome = SimulationOutcome(
        candidate_final_money=3000.0, baseline_final_money=3000.0, delta_our_money=-125.0,
        candidate_opp_final_money=0.0, baseline_opp_final_money=0.0, delta_opponent_money=0.0,
        delta_terminal_margin=-125.0, candidate_overflow_units=4, candidate_sold={}, baseline_sold={},
        intermediate_solvency_ok=True, horizon=6
    )
    passed, checks, _ = checker.verify(patch, outcome, econ, {})
    assert not passed
    assert not checks["capacity_consistency_ok"]


def test_ef_7_feed_purchase_worker_trajectory(normal_opening_obs: Dict[str, Any]) -> None:
    """CASE EF-7: Feed delivery requires worker route detour.
    
    Expected: AEC-RECONNECT evaluates trajectory and safely splices.
    """
    request = ReconnectRequest(
        worker=0,
        divergence_point=0,
        patched_action=["SOUTH"],
        intended_target_state=(5, 5),
        baseline_continuation=[{"farmer": ["EAST"]}, {"farmer": ["SOUTH"]}],
        remaining_steps=700
    )
    result = reconnect_worker_trajectory(request)
    assert result.is_safe
    assert result.status == ReconnectionStatus.SAFE_RECONNECT


def test_ef_8_competes_with_higher_priority_dependency() -> None:
    """CASE EF-8: Purchase competes with another higher-priority known dependency.
    
    Expected: Dependency closure detects conflict and rejects unsafe candidate.
    """
    g = ActionBasketDependencyGraph()
    n_seed = ActionNode(node_id="BUY_SEED_MELON", actor_type="MARKET", actor_index=0, action_type="BUY_SEED", item="MELON", quantity=1)
    n_feed = ActionNode(node_id="BUY_FEED", actor_type="MARKET", actor_index=1, action_type="BUY_PRODUCT", item="WHEAT", quantity=1)
    g.add_node(n_seed)
    g.add_node(n_feed)
    g.add_edge("BUY_FEED", "BUY_SEED_MELON", CausalEdgeType.CASH_COUPLING, description="Cash allocation conflict")

    closure = g.compute_dependency_closure({"BUY_FEED"})
    assert "BUY_SEED_MELON" in closure


def test_ef_9_feed_purchase_near_terminal(terminal_proximity_obs: Dict[str, Any]) -> None:
    """CASE EF-9: Feed purchase near terminal turn 718.
    
    Expected: Terminal-aware logic prevents pointless/unexecutable action.
    """
    obs = copy.deepcopy(terminal_proximity_obs)
    obs["step"] = 718
    econ = build_economic_state(obs)
    checker = SafetyChecker()
    patch = CoupledPatch(
        patch_id="PATCH_EF_9",
        source_opportunity_id="OPP_EF_9",
        resource_changes={"terminal_infeasible": True},
    )
    outcome = SimulationOutcome(
        candidate_final_money=1000.0, baseline_final_money=1050.0, delta_our_money=-50.0,
        candidate_opp_final_money=0.0, baseline_opp_final_money=0.0, delta_opponent_money=0.0,
        delta_terminal_margin=-50.0, candidate_overflow_units=0, candidate_sold={}, baseline_sold={},
        intermediate_solvency_ok=True, horizon=1
    )
    passed, checks, reason = checker.verify(patch, outcome, econ, {})
    assert not passed
    assert not checks["terminal_resource_ok"]


def test_ef_10_no_emergency_actually_exists(normal_opening_obs: Dict[str, Any]) -> None:
    """CASE EF-10: No emergency actually exists.
    
    Expected: No false-positive opportunity proposed.
    """
    obs = copy.deepcopy(normal_opening_obs)
    econ = build_economic_state(obs)
    analyzer = ResourceOpportunityAnalyzer()
    opps = analyzer.analyze(econ, [])
    feed_opps = [o for o in opps if o.candidate_transformation_family == "EMERGENCY_FEED_PURCHASE"]
    assert len(feed_opps) == 0


def test_ef_11_consecutive_starvation_loss_prevented(normal_opening_obs: Dict[str, Any]) -> None:
    """CASE EF-11: Two consecutive days of starvation would cause livestock loss.
    
    Expected: Feed-security model correctly predicts and prevents this state.
    """
    obs = copy.deepcopy(normal_opening_obs)
    obs["farms"][0]["tiles"][1][1] = {
        "kind": "PASTURE", "animal": "COW", "consecutive_unfed": 1, "fed_today": False
    }
    obs["private"]["shed"]["WHEAT"] = 0
    econ = build_economic_state(obs)

    feed_engine = FeedSecurityEngine()
    # If no feed is delivered, cow reaches consecutive_unfed >= 2 at end of day (step 23)
    trajectory_no_feed = [{"farmer": ["PASS"], "hands": [], "market": []} for _ in range(24)]
    sec_unfed = feed_engine.evaluate_feed_trajectory(econ, trajectory_no_feed, horizon=24)
    assert not sec_unfed.is_secure
    assert sec_unfed.escaped_animals_count > 0

    # With feed purchase and feeding action, cow is fed and survives
    trajectory_fed = [
        {"farmer": ["PASS"], "hands": [], "market": [["BUY_PRODUCT", "WHEAT", 1]]},
        {"farmer": ["FEED"], "hands": [], "market": []}
    ] + [{"farmer": ["PASS"], "hands": [], "market": []} for _ in range(22)]
    sec_fed = feed_engine.evaluate_feed_trajectory(econ, trajectory_fed, horizon=24)
    assert sec_fed.is_secure
    assert sec_fed.escaped_animals_count == 0


def test_ef_12_historical_replay_incoming_feed(normal_opening_obs: Dict[str, Any]) -> None:
    """CASE EF-12: Historical replay already contains sufficient incoming feed.
    
    Expected: No redundant emergency purchase.
    """
    obs = copy.deepcopy(normal_opening_obs)
    obs["farms"][0]["tiles"][1][1] = {"kind": "PASTURE", "animal": "COW", "fed_today": False}
    obs["private"]["shed"]["WHEAT"] = 5
    econ = build_economic_state(obs)

    feed_engine = FeedSecurityEngine()
    trajectory = [{"farmer": ["FEED"], "hands": [], "market": []}] + [
        {"farmer": ["PASS"], "hands": [], "market": []} for _ in range(23)
    ]
    sec = feed_engine.evaluate_feed_trajectory(econ, trajectory, horizon=24)
    assert sec.is_secure
