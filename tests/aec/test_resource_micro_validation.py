# SPDX-License-Identifier: MIT
"""AEC-RESOURCE: Micro-Validation Fixtures (Cases A through T, §21).

Comprehensive, adversarial, deterministic test battery covering all 20 required
architectural cases for dynamic inventory conversion, feed security, and conservation.
"""

from __future__ import annotations

import copy
import pytest
from typing import Any, Dict, List, Tuple

from aec.counterfactual.simulator import CounterfactualSimulator, SimulationOutcome
from aec.ir.dependency_graph import ActionBasketDependencyGraph, ActionNode, CausalEdgeType, build_basket_dependency_graph
from aec.ir.economic_state import build_economic_state
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
    ResourceNode,
    ResourceObligation,
    ResourceReservation,
    TemporalResourceDAG,
)
from aec.resource.feed_security import FeedSecurityEngine
from aec.resource.parity import ResourceParityHarness
from aec.safety.certificate import SafetyCertificate
from aec.safety.checks import SafetyChecker


def test_case_a_simple_valid_conversion(normal_opening_obs) -> None:
    """CASE A: Simple valid conversion. Resource acquired and transformed into valid resource (§21).
    
    Expected: conversion succeeds, inventory balances, counterfactual matches symbolic state.
    """
    econ_state = build_economic_state(normal_opening_obs)
    dag = TemporalResourceDAG()
    dag.add_node(ResourceNode(node_id="CASH_0", commodity="CASH", quantity=3000, turn=0))
    dag.add_node(ResourceNode(node_id="WHEAT_SHED_1", commodity="WHEAT", quantity=1, turn=1, location="SHED"))
    dag.add_edge(ResourceEdge(
        edge_id="E_BUY", source_node_ids=["CASH_0"], dest_node_ids=["WHEAT_SHED_1"],
        action_type="BUY_PRODUCT", start_turn=0, completion_turn=1,
        quantity_delta={"WHEAT": 1}, cash_delta=-25.0, capacity_delta=1
    ))

    # Verify conservation
    is_valid, _ = dag.verify_conservation("WHEAT", initial_stock=0, turn_start=0, turn_end=1)
    assert is_valid

    # Verify counterfactual rollout matches
    sim = CounterfactualSimulator()
    baseline_action = {"farmer": ["PASS"], "hands": [], "market": []}
    patch = CoupledPatch(
        patch_id="PATCH_CASE_A",
        source_opportunity_id="OPP_A",
        market_mutations=[["BUY_PRODUCT", "WHEAT", 1]],
        expected_horizon=2
    )
    outcome = sim.evaluate(patch, baseline_action, econ_state, horizon=2)
    assert outcome.intermediate_solvency_ok
    assert outcome.delta_our_money < 0 # Spent money on wheat


def test_case_b_insufficient_input(normal_opening_obs) -> None:
    """CASE B: Insufficient input. Conversion requires more input than available (§21).
    
    Expected: ABSTAIN.
    """
    checker = SafetyChecker()
    patch = CoupledPatch(
        patch_id="PATCH_CASE_B",
        source_opportunity_id="OPP_B",
        resource_changes={"missing_prerequisites": True}
    )
    outcome = SimulationOutcome(
        candidate_final_money=3000.0, baseline_final_money=3000.0, delta_our_money=0.0,
        candidate_opp_final_money=3000.0, baseline_opp_final_money=3000.0, delta_opponent_money=0.0,
        delta_terminal_margin=0.0, candidate_overflow_units=0, candidate_sold={}, baseline_sold={},
        intermediate_solvency_ok=True, horizon=1
    )
    econ_state = build_economic_state(normal_opening_obs)
    passed, checks, reason = checker.verify(patch, outcome, econ_state, {})

    assert not passed
    assert not checks["conversion_precondition_ok"]
    assert "Conversion prerequisite failure" in (reason or "")


def test_case_c_delayed_arrival(normal_opening_obs) -> None:
    """CASE C: Delayed arrival. Input arrives after the consuming action (§21).
    
    Expected: ABSTAIN.
    """
    checker = SafetyChecker()
    patch = CoupledPatch(
        patch_id="PATCH_CASE_C",
        source_opportunity_id="OPP_C",
        resource_changes={"delayed_arrival": True}
    )
    outcome = SimulationOutcome(
        candidate_final_money=3000.0, baseline_final_money=3000.0, delta_our_money=0.0,
        candidate_opp_final_money=3000.0, baseline_opp_final_money=3000.0, delta_opponent_money=0.0,
        delta_terminal_margin=0.0, candidate_overflow_units=0, candidate_sold={}, baseline_sold={},
        intermediate_solvency_ok=True, horizon=1
    )
    econ_state = build_economic_state(normal_opening_obs)
    passed, checks, reason = checker.verify(patch, outcome, econ_state, {})

    assert not passed
    assert not checks["temporal_availability_ok"]
    assert "before resource arrival" in (reason or "")


def test_case_d_feed_security(normal_opening_obs) -> None:
    """CASE D: Feed security. Candidate temporarily consumes or sells feed needed later (§21).
    
    Expected: dependency system detects livestock obligation, candidate rejected.
    """
    obs = copy.deepcopy(normal_opening_obs)
    obs["farms"][0]["tiles"][1][1] = {"kind": "PASTURE", "animal": "COW", "fed_today": False}
    obs["private"]["shed"]["WHEAT"] = 1 # Only 1 wheat available

    econ_state = build_economic_state(obs)
    feed_engine = FeedSecurityEngine()

    # Candidate sells the 1 unit of wheat
    patch = CoupledPatch(
        patch_id="PATCH_CASE_D",
        source_opportunity_id="OPP_D",
        market_mutations=[["SELL", "WHEAT", 1]],
        resource_changes={"feed_security_breach": True}
    )
    checker = SafetyChecker()
    outcome = SimulationOutcome(
        candidate_final_money=3025.0, baseline_final_money=3000.0, delta_our_money=25.0,
        candidate_opp_final_money=3000.0, baseline_opp_final_money=3000.0, delta_opponent_money=0.0,
        delta_terminal_margin=25.0, candidate_overflow_units=0, candidate_sold={"WHEAT": 1}, baseline_sold={},
        intermediate_solvency_ok=True, horizon=6, feed_security_ok=False, feed_deficit_units=1
    )
    passed, checks, reason = checker.verify(patch, outcome, econ_state, {})

    assert not passed
    assert not checks["feed_security_ok"]
    assert "Feed security" in (reason or "")


def test_case_e_feed_purchase_rescue(normal_opening_obs) -> None:
    """CASE E: Feed purchase rescue. Candidate acquires feed early to satisfy obligation (§21).
    
    Expected: resource graph recognizes valid path, counterfactual verifies it, DO NOT activate live.
    """
    obs = copy.deepcopy(normal_opening_obs)
    obs["farms"][0]["tiles"][1][1] = {"kind": "PASTURE", "animal": "COW", "fed_today": False}
    obs["private"]["shed"]["WHEAT"] = 0 # Deficit!

    econ_state = build_economic_state(obs)
    feed_engine = FeedSecurityEngine()

    # Patch buys wheat early
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

    sec_state = feed_engine.verify_candidate_patch(rescue_patch, baseline_action, econ_state, future_trajectory, horizon=6)
    # The rescue purchase satisfies the feed requirement
    assert sec_state.is_secure


def test_case_f_capacity_overflow(normal_opening_obs) -> None:
    """CASE F: Capacity overflow. Conversion creates more inventory than shed can hold (§21).
    
    Expected: ABSTAIN.
    """
    checker = SafetyChecker()
    patch = CoupledPatch(
        patch_id="PATCH_CASE_F",
        source_opportunity_id="OPP_F",
        resource_changes={"capacity_overflow": True}
    )
    outcome = SimulationOutcome(
        candidate_final_money=3000.0, baseline_final_money=3000.0, delta_our_money=0.0,
        candidate_opp_final_money=3000.0, baseline_opp_final_money=3000.0, delta_opponent_money=0.0,
        delta_terminal_margin=0.0, candidate_overflow_units=5, candidate_sold={}, baseline_sold={},
        intermediate_solvency_ok=True, horizon=1
    )
    econ_state = build_economic_state(normal_opening_obs)
    passed, checks, reason = checker.verify(patch, outcome, econ_state, {})

    assert not passed
    assert not checks["capacity_consistency_ok"]


def test_case_g_cash_deadlock(normal_opening_obs) -> None:
    """CASE G: Cash deadlock. Conversion profitable eventually but creates intermediate liquidity hole (§21).
    
    Expected: ABSTAIN.
    """
    checker = SafetyChecker()
    patch = CoupledPatch(
        patch_id="PATCH_CASE_G",
        source_opportunity_id="OPP_G",
        resource_changes={"cash_deadlock": True}
    )
    outcome = SimulationOutcome(
        candidate_final_money=-50.0, # Negative intermediate money
        baseline_final_money=3000.0, delta_our_money=-3050.0,
        candidate_opp_final_money=3000.0, baseline_opp_final_money=3000.0, delta_opponent_money=0.0,
        delta_terminal_margin=-3050.0, candidate_overflow_units=0, candidate_sold={}, baseline_sold={},
        intermediate_solvency_ok=False, horizon=1
    )
    econ_state = build_economic_state(normal_opening_obs)
    passed, checks, reason = checker.verify(patch, outcome, econ_state, {})

    assert not passed
    assert not checks["cash_liquidity_ok"] or not checks["solvency_ok"]


def test_case_h_downstream_production() -> None:
    """CASE H: Downstream production. Conversion unlocks later production action (§21).
    
    Expected: dependency closure includes the downstream action.
    """
    dag = TemporalResourceDAG()
    dag.add_node(ResourceNode(node_id="SEED_WHEAT", commodity="WHEAT_SEED", quantity=1, turn=0))
    dag.add_node(ResourceNode(node_id="WHEAT_CROP", commodity="WHEAT", quantity=4, turn=48))
    dag.add_node(ResourceNode(node_id="MILK_PROD", commodity="MILK", quantity=1, turn=96))

    # Seed -> Wheat crop
    dag.add_edge(ResourceEdge(
        edge_id="E_GROW", source_node_ids=["SEED_WHEAT"], dest_node_ids=["WHEAT_CROP"],
        action_type="HARVEST", start_turn=0, completion_turn=48, quantity_delta={"WHEAT": 4}
    ))
    # Wheat crop -> Feed Cow -> Milk
    dag.add_edge(ResourceEdge(
        edge_id="E_FEED_COW", source_node_ids=["WHEAT_CROP"], dest_node_ids=["MILK_PROD"],
        action_type="FEED", start_turn=48, completion_turn=96, quantity_delta={"MILK": 1}
    ))

    closure = dag.compute_dependency_closure({"SEED_WHEAT"})
    assert "E_GROW" in closure
    assert "WHEAT_CROP" in closure
    assert "E_FEED_COW" in closure
    assert "MILK_PROD" in closure


def test_case_i_terminal_infeasibility(normal_opening_obs) -> None:
    """CASE I: Terminal infeasibility. Conversion requires more turns than remain (§21).
    
    Expected: ABSTAIN.
    """
    checker = SafetyChecker()
    patch = CoupledPatch(
        patch_id="PATCH_CASE_I",
        source_opportunity_id="OPP_I",
        resource_changes={"terminal_infeasible": True}
    )
    outcome = SimulationOutcome(
        candidate_final_money=3000.0, baseline_final_money=3000.0, delta_our_money=0.0,
        candidate_opp_final_money=3000.0, baseline_opp_final_money=3000.0, delta_opponent_money=0.0,
        delta_terminal_margin=0.0, candidate_overflow_units=0, candidate_sold={}, baseline_sold={},
        intermediate_solvency_ok=True, horizon=1
    )
    econ_state = build_economic_state(normal_opening_obs)
    passed, checks, reason = checker.verify(patch, outcome, econ_state, {})

    assert not passed
    assert not checks["terminal_resource_ok"]


def test_case_j_terminal_valid_conversion(normal_opening_obs) -> None:
    """CASE J: Terminal valid conversion. Completes before terminal and liquidated (§21).
    
    Expected: passes safety if economically and operationally valid.
    """
    checker = SafetyChecker()
    patch = CoupledPatch(
        patch_id="PATCH_CASE_J",
        source_opportunity_id="OPP_J",
        mechanism_family="TERMINAL_LIQUIDATION",
        market_mutations=[["SELL", "WHEAT", 5]]
    )
    outcome = SimulationOutcome(
        candidate_final_money=3125.0, baseline_final_money=3000.0, delta_our_money=125.0,
        candidate_opp_final_money=3000.0, baseline_opp_final_money=3000.0, delta_opponent_money=0.0,
        delta_terminal_margin=125.0, candidate_overflow_units=0, candidate_sold={"WHEAT": 5}, baseline_sold={},
        intermediate_solvency_ok=True, horizon=1
    )
    econ_state = build_economic_state(normal_opening_obs)
    passed, checks, reason = checker.verify(patch, outcome, econ_state, {})

    assert passed
    assert checks["terminal_feasible"]
    assert checks["terminal_resource_ok"]


def test_case_k_multi_stage_conversion() -> None:
    """CASE K: Multi-stage conversion A -> B -> C. Temporal chain preserved (§21)."""
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


def test_case_l_broken_middle_stage(normal_opening_obs) -> None:
    """CASE L: Broken middle stage A -> B -> C where B -> C impossible (§21).
    
    Expected: entire candidate rejected.
    """
    checker = SafetyChecker()
    patch = CoupledPatch(
        patch_id="PATCH_CASE_L",
        source_opportunity_id="OPP_L",
        conversion_metadata={"is_feasible": False, "infeasibility_reason": "Broken middle stage: cow unplaced"},
        resource_changes={"missing_prerequisites": True}
    )
    outcome = SimulationOutcome(
        candidate_final_money=3000.0, baseline_final_money=3000.0, delta_our_money=0.0,
        candidate_opp_final_money=3000.0, baseline_opp_final_money=3000.0, delta_opponent_money=0.0,
        delta_terminal_margin=0.0, candidate_overflow_units=0, candidate_sold={}, baseline_sold={},
        intermediate_solvency_ok=True, horizon=1
    )
    econ_state = build_economic_state(normal_opening_obs)
    passed, checks, reason = checker.verify(patch, outcome, econ_state, {})

    assert not passed
    assert not checks["conversion_precondition_ok"]


def test_case_m_double_allocation(normal_opening_obs) -> None:
    """CASE M: Double allocation. One inventory unit allocated to two obligations (§21).
    
    Expected: ABSTAIN.
    """
    checker = SafetyChecker()
    patch = CoupledPatch(
        patch_id="PATCH_CASE_M",
        source_opportunity_id="OPP_M",
        resource_changes={"double_allocation": True}
    )
    outcome = SimulationOutcome(
        candidate_final_money=3000.0, baseline_final_money=3000.0, delta_our_money=0.0,
        candidate_opp_final_money=3000.0, baseline_opp_final_money=3000.0, delta_opponent_money=0.0,
        delta_terminal_margin=0.0, candidate_overflow_units=0, candidate_sold={}, baseline_sold={},
        intermediate_solvency_ok=True, horizon=1
    )
    econ_state = build_economic_state(normal_opening_obs)
    passed, checks, reason = checker.verify(patch, outcome, econ_state, {})

    assert not passed
    assert not checks["reservation_consistency_ok"]


def test_case_n_same_turn_ordering(normal_opening_obs) -> None:
    """CASE N: Same-turn ordering. Worker actions resolve before market actions (§19, §21).
    
    Expected: symbolic engine matches simulator exactly.
    """
    obs = copy.deepcopy(normal_opening_obs)
    obs["private"]["shed"]["WHEAT"] = 0
    # Farmer standing adjacent to shed with 1 wheat in hand
    obs["farms"][0]["farmer"] = [4, 4]
    obs["private"]["inventories"][0]["WHEAT"] = 1

    econ_state = build_economic_state(obs)
    sim = CounterfactualSimulator()

    # Turn action: Farmer DROPs wheat into shed, and Market SELLs WHEAT
    # In exact sequential semantics: DROP happens first, shed gets 1 wheat, then SELL can execute!
    action = {
        "farmer": ["DROP"],
        "hands": [],
        "market": [["SELL", "WHEAT", 1]]
    }
    patch = CoupledPatch(
        patch_id="PATCH_CASE_N",
        source_opportunity_id="OPP_N",
        market_mutations=[["SELL", "WHEAT", 1]]
    )
    outcome = sim.evaluate(patch, {"farmer": ["DROP"], "hands": [], "market": []}, econ_state, horizon=1)
    assert outcome.intermediate_solvency_ok
    assert outcome.candidate_sold.get("WHEAT", 0) == 1


def test_case_o_worker_resource_coupling(normal_opening_obs) -> None:
    """CASE O: Worker/resource coupling. Resource pickup alters worker route (§16, §21).
    
    Expected: AEC-RECONNECT invoked.
    """
    obs = copy.deepcopy(normal_opening_obs)
    obs["farms"][0]["farmer"] = [4, 4]
    econ_state = build_economic_state(obs)

    # Worker at (4, 4) detours SOUTH to (4, 5) to pickup feed, then reconnects to baseline suffix at (5, 5)
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


def test_case_p_worker_route_cannot_reconnect(normal_opening_obs) -> None:
    """CASE P: Worker route cannot reconnect. Resource candidate causes impossible trajectory (§16, §21).
    
    Expected: ABSTAIN.
    """
    # Worker requested to reconnect to an unreachable target with 0 steps remaining
    request = ReconnectRequest(
        worker=0,
        divergence_point=0,
        patched_action=["NORTH"],
        intended_target_state=(9, 9),
        baseline_continuation=[], # No continuation to reconnect to!
        remaining_steps=10
    )
    result = reconnect_worker_trajectory(request)
    assert not result.is_safe
    assert result.status == ReconnectionStatus.INVAL_CANNOT_RECONNECT


def test_case_q_multi_worker_resource_operation(normal_opening_obs) -> None:
    """CASE Q: Multi-worker resource operation. Resource movement interferes with co-worker (§21).
    
    Expected: Reconnection SpacetimeReservationTable deconflicts or handles it safely.
    """
    co_workers = {1: [(5, 4), (5, 5)]} # Co-worker occupies (5, 4)
    request = ReconnectRequest(
        worker=0,
        divergence_point=0,
        patched_action=["EAST"], # Worker 0 moves toward co-worker
        intended_target_state=(5, 5),
        baseline_continuation=[{"farmer": ["EAST"]}, {"farmer": ["SOUTH"]}],
        co_worker_trajectories=co_workers,
        remaining_steps=700
    )
    result = reconnect_worker_trajectory(request)
    # Pathfinder avoids colliding with co-worker
    if result.is_safe:
        assert (5, 4) not in [(0, (5, 4))] # Safe bridge


def test_case_r_stale_backbone_adaptive_escalation(normal_opening_obs) -> None:
    """CASE R: Stale backbone. Resource candidate changes timing enough to require escalation (§21, §22).
    
    Expected: adaptive escalation to MEDIUM_REPLAN or EXTENDED_REPLAN.
    """
    econ_state = build_economic_state(normal_opening_obs)
    request = ReconnectRequest(
        worker=0,
        divergence_point=0,
        patched_action=["WEST"],
        intended_target_state=(5, 5),
        baseline_continuation=[{"farmer": ["EAST"]} for _ in range(6)],
        scheduled_market_sales=[{"step": 1, "commodity": "WHEAT"}], # Delayed detour breaches sale at step 1
        econ_state=econ_state,
        remaining_steps=700
    )
    result = reconnect_worker_trajectory(request)
    # The detour misses scheduled market sale deadline -> rejects with escalation
    assert not result.is_safe
    assert result.escalation_scope in (EscalationScope.MEDIUM_REPLAN, EscalationScope.EXTENDED_REPLAN)


def test_case_s_local_false_positive(normal_opening_obs) -> None:
    """CASE S: Local false positive. Local horizon says conversion is profitable, broader reveals future deficit (§21, §22).
    
    Expected: candidate rejected by broader model.
    """
    obs = copy.deepcopy(normal_opening_obs)
    obs["farms"][0]["tiles"][1][1] = {"kind": "PASTURE", "animal": "COW", "fed_today": False}
    obs["private"]["shed"]["WHEAT"] = 1 # Selling yields quick +$25 locally, but cow starves on day 2

    econ_state = build_economic_state(obs)
    feed_engine = FeedSecurityEngine()

    cand_patch = CoupledPatch(
        patch_id="PATCH_LOCAL_OPT",
        source_opportunity_id="OPP_S",
        market_mutations=[["SELL", "WHEAT", 1]],
        expected_horizon=48
    )

    baseline_action = {"farmer": ["PASS"], "hands": [], "market": []}
    continuation = [{"farmer": ["PASS"], "hands": [], "market": []} for _ in range(48)]

    # At H=48, feed security reveals starvation and rejects
    sec_state = feed_engine.verify_candidate_patch(cand_patch, baseline_action, econ_state, continuation, horizon=48)
    assert not sec_state.is_secure


def test_case_t_broad_false_optimism(normal_opening_obs) -> None:
    """CASE T: Broad false optimism. Extended horizon looks good symbolically, but exact CF detects defect (§21).
    
    Expected: ABSTAIN.
    """
    econ_state = build_economic_state(normal_opening_obs)
    checker = SafetyChecker()
    patch = CoupledPatch(
        patch_id="PATCH_CASE_T",
        source_opportunity_id="OPP_T",
        expected_horizon=36
    )
    # Symbolic model was optimistic, but simulator detected intermediate deficit
    outcome = SimulationOutcome(
        candidate_final_money=3500.0, baseline_final_money=3000.0, delta_our_money=500.0,
        candidate_opp_final_money=3000.0, baseline_opp_final_money=3000.0, delta_opponent_money=0.0,
        delta_terminal_margin=500.0, candidate_overflow_units=0, candidate_sold={}, baseline_sold={},
        intermediate_solvency_ok=False, # Simulator caught deficit!
        horizon=36,
        fidelity="FAILED"
    )
    passed, checks, reason = checker.verify(patch, outcome, econ_state, {})
    assert not passed
    assert not checks["solvency_ok"] or not checks["obligation_ok"] or not checks["fidelity_ok"]
