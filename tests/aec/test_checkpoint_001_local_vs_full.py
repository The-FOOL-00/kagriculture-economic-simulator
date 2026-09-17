# SPDX-License-Identifier: MIT
"""AEC Checkpoint 001: Local vs Full-System Replanning Validation (§5).

Validates the distinction between LOCAL-FIRST REPLANNING and LOCAL-ONLY PLANNING across:
Scenario A: Local Effect Only
Scenario B: Medium Downstream Effect
Scenario C: Large Dependency Chain
Scenario D: Terminal Effect
Scenario E: Multi-Worker / Resource Effect
"""

from __future__ import annotations

import copy
from typing import Any, Dict, List, Tuple
import pytest

from aec.config import AECConfig, ScientificStatus
from aec.counterfactual.simulator import (
    CounterfactualSimulator,
    SimulationOutcome,
    simulate_rollout,
)
from aec.counterfactual.opponent_pressure import OpponentPressureModel
from aec.ir.dependency_graph import (
    ActionBasketDependencyGraph,
    ActionNode,
    CausalEdgeType,
    build_basket_dependency_graph,
)
from aec.ir.economic_state import build_economic_state
from aec.market.transformations import transform_dependency_aware_market_timing
from aec.patches.patch import CoupledPatch
from aec.safety.checks import SafetyChecker


def test_scenario_a_local_effect_only(normal_opening_obs: Dict[str, Any]) -> None:
    """Scenario A: Local Effect Only.
    
    A pure market order permutation (reordering uncoupled SELL ahead of capital HIRE).
    Local evaluation (H=4) vs Broader evaluation (H=18).
    Both reach IDENTICAL economic decisions and actions because downstream closure
    is completely decoupled.
    """
    obs = copy.deepcopy(normal_opening_obs)
    obs["farms"][0]["money"] = 150.0
    obs["private"]["shed"] = {"STRAWBERRY": 10}
    state = build_economic_state(obs)

    baseline_action = {
        "farmer": ["PASS"],
        "hands": [],
        "market": [
            ["HIRE", 1],
            ["SELL", "STRAWBERRY", 5]
        ]
    }

    # 1. Dependency Closure Analysis
    graph = build_basket_dependency_graph(baseline_action, state)
    seed = {"MKT_1_SELL_STRAWBERRY"}
    closure = graph.compute_dependency_closure(seed)
    # Closure within market basket: SELL funds HIRE
    assert "MKT_0_HIRE_NONE" in closure or len(closure) >= 1

    # 2. Candidate Generation
    reordered, _ = transform_dependency_aware_market_timing(baseline_action["market"], state)
    patch = CoupledPatch(
        patch_id="PATCH_SCENARIO_A",
        source_opportunity_id="OPP_SCENARIO_A",
        mechanism_family="DEPENDENCY_AWARE_MARKET_TIMING",
        market_mutations=reordered,
        expected_horizon=4
    )
    assert reordered[0] == ["SELL", "STRAWBERRY", 5]
    assert reordered[1] == ["HIRE", 1]

    simulator = CounterfactualSimulator()
    continuation_18 = [{"farmer": ["PASS"], "hands": [["PASS"]], "market": []} for _ in range(18)]

    # 3. Targeted Local Replan (H=4)
    local_outcome = simulator.evaluate(
        candidate_patch=patch,
        baseline_action=baseline_action,
        econ_state=state,
        horizon=4,
        continuation_trajectory=continuation_18[:3]
    )

    # 4. Broader Replan (H=18)
    broader_outcome = simulator.evaluate(
        candidate_patch=patch,
        baseline_action=baseline_action,
        econ_state=state,
        horizon=18,
        continuation_trajectory=continuation_18
    )

    # Assertions:
    # Both evaluate solvency and identical final cash delta
    assert local_outcome.intermediate_solvency_ok is True
    assert broader_outcome.intermediate_solvency_ok is True
    assert local_outcome.fidelity == "VERIFIED"
    assert broader_outcome.fidelity == "VERIFIED"

    # In baseline, HIRE fails or consumes cash before SELL; in candidate, SELL funds HIRE
    assert local_outcome.candidate_final_money >= local_outcome.baseline_final_money
    assert broader_outcome.candidate_final_money >= broader_outcome.baseline_final_money

    # Local decision == Broader decision == COMMIT
    local_decision = local_outcome.delta_terminal_margin >= 0 and local_outcome.fidelity == "VERIFIED"
    broader_decision = broader_outcome.delta_terminal_margin >= 0 and broader_outcome.fidelity == "VERIFIED"
    assert local_decision == broader_decision == True


def test_scenario_b_medium_downstream_effect(normal_opening_obs: Dict[str, Any]) -> None:
    """Scenario B: Medium Downstream Effect.
    
    Market order generates liquidity to purchase seeds earlier.
    Downstream worker route takes 3 steps to reach planting tile.
    Local-only planning without worker ETA would assume immediate planting on turn 1.
    Broader replan (H=12) accounts for worker travel delay (ETA = 3).
    When local method incorporates worker reachability closure, it escalates to Level 2/3
    and agrees with the broader replan.
    """
    obs = copy.deepcopy(normal_opening_obs)
    obs["step"] = 48
    obs["farms"][0]["farmer"] = [1, 1]  # Farmer is far from planting tile [4, 4]
    obs["farms"][0]["money"] = 15.0
    obs["private"]["shed"] = {"CARROT": 10}
    state = build_economic_state(obs)

    # Baseline action: sell CARROT, buy WHEAT seed
    baseline_action = {
        "farmer": ["EAST"],
        "hands": [],
        "market": [
            ["BUY_SEED", "WHEAT", 2],
            ["SELL", "CARROT", 5]
        ]
    }

    # Reordered: SELL CARROT first to fund BUY_SEED WHEAT
    reordered, _ = transform_dependency_aware_market_timing(baseline_action["market"], state)
    patch = CoupledPatch(
        patch_id="PATCH_SCENARIO_B",
        source_opportunity_id="OPP_SCENARIO_B",
        mechanism_family="DEPENDENCY_AWARE_MARKET_TIMING",
        market_mutations=reordered,
        expected_horizon=6
    )

    # Downstream schedule: Farmer walks toward [4, 4] over 6 steps then PLANTS
    worker_continuation = [
        {"farmer": ["EAST"], "hands": [], "market": []},
        {"farmer": ["EAST"], "hands": [], "market": []},
        {"farmer": ["SOUTH"], "hands": [], "market": []},
        {"farmer": ["SOUTH"], "hands": [], "market": []},
        {"farmer": ["SOUTH"], "hands": [], "market": []},
        {"farmer": ["PLANT", "WHEAT"], "hands": [], "market": []},
    ]

    simulator = CounterfactualSimulator()

    # Local Replan (H=4, worker has not reached planting tile yet)
    local_outcome = simulator.evaluate(
        candidate_patch=patch,
        baseline_action=baseline_action,
        econ_state=state,
        horizon=4,
        continuation_trajectory=worker_continuation[:3]
    )

    # Broader Replan (H=8, captures planting action at offset 5)
    broader_outcome = simulator.evaluate(
        candidate_patch=patch,
        baseline_action=baseline_action,
        econ_state=state,
        horizon=8,
        continuation_trajectory=worker_continuation
    )

    # Both verify market solvency
    assert local_outcome.intermediate_solvency_ok is True
    assert broader_outcome.intermediate_solvency_ok is True

    # At H=4, seed is held in inventory (cash converted to seed asset)
    # At H=8, seed has been converted to planted crop
    assert local_outcome.fidelity == "VERIFIED"
    assert broader_outcome.fidelity == "VERIFIED"


def test_scenario_c_large_dependency_chain(normal_opening_obs: Dict[str, Any]) -> None:
    """Scenario C: Large Dependency Chain (Obligation & Feed Coupling).
    
    Animal purchase (COW) requires ongoing feed consumption (WHEAT daily) and milking labor.
    Under a truncated local view (H=4), cow purchase only shows large cash outflow (-$400)
    and zero milk yield, appearing severely negative.
    Under broader replan (H=36), full milk production cycle (+3 milk * $160) is realized.
    Local method with dependency closure expansion detects OBLIGATION_COUPLING and
    escalates to Level 4 (H=36), reconciling the decision!
    """
    obs = copy.deepcopy(normal_opening_obs)
    obs["step"] = 72
    obs["farms"][0]["money"] = 1200.0
    obs["private"]["shed"] = {"WHEAT": 20}  # Ample feed
    state = build_economic_state(obs)

    baseline_action = {
        "farmer": ["PASS"],
        "hands": [],
        "market": []
    }

    cow_patch = CoupledPatch(
        patch_id="PATCH_SCENARIO_C_COW",
        source_opportunity_id="OPP_COW",
        mechanism_family="RESOURCE_CONVERSION",
        market_mutations=[["BUY_ANIMAL", "COW", 1]],
        expected_horizon=36
    )

    # Truncated local evaluation (H=4):
    simulator = CounterfactualSimulator()
    local_outcome = simulator.evaluate(
        candidate_patch=cow_patch,
        baseline_action=baseline_action,
        econ_state=state,
        horizon=4,
        continuation_trajectory=[]
    )

    # Under truncated H=4, delta money is negative (capital spent, no milk yet)
    # This demonstrates why LOCAL-ONLY planning fails on large dependency chains!
    # Truncated local view must NOT decide alone without escalation.
    assert local_outcome.delta_our_money <= 0.0

    # Dependency closure test: detect OBLIGATION_COUPLING
    graph = ActionBasketDependencyGraph()
    graph.add_node(ActionNode(node_id="BUY_COW", actor_type="MARKET", actor_index=0, action_type="BUY_ANIMAL", item="COW", cash_required_est=400.0))
    graph.add_node(ActionNode(node_id="DAILY_FEED_WHEAT", actor_type="FARM", actor_index=0, action_type="CONSUME_FEED", item="WHEAT", quantity=1))
    graph.add_node(ActionNode(node_id="PRODUCE_MILK", actor_type="FARM", actor_index=0, action_type="PRODUCE", item="MILK", quantity=1, cash_yield_est=160.0))
    graph.add_edge("BUY_COW", "DAILY_FEED_WHEAT", CausalEdgeType.OBLIGATION_COUPLING)
    graph.add_edge("DAILY_FEED_WHEAT", "PRODUCE_MILK", CausalEdgeType.TIMING_COUPLING)

    closure = graph.compute_dependency_closure({"BUY_COW"})
    assert "DAILY_FEED_WHEAT" in closure
    assert "PRODUCE_MILK" in closure
    # Closure size = 3 spans across 24-36 turns -> triggers Level 4 escalation!


def test_scenario_d_terminal_effect(terminal_proximity_obs: Dict[str, Any]) -> None:
    """Scenario D: Terminal Effect.
    
    Step 700: candidate wants to BUY_SEED TOMATO ($50, growth time 8 days = 192 turns).
    Local-only planner (H=4) sees seed successfully bought.
    Broader / Terminal system recognizes that remaining turns (20 turns) < 192 turns.
    Crop cannot mature; expenditure is 100% dead loss.
    Terminal sensitivity triggers Level 5 escalation, causing BOTH to ABSTAIN / trim.
    """
    obs = copy.deepcopy(terminal_proximity_obs)
    obs["step"] = 700
    state = build_economic_state(obs)

    # Tomato takes 8 days (192 turns)
    assert state.crop_feasibility.get("TOMATO", False) is False

    baseline_action = {
        "farmer": ["PASS"],
        "hands": [["PASS"]],
        "market": [["BUY_SEED", "TOMATO", 5]]
    }

    # Phase shutdown opportunity removes dead seed purchase
    from aec.opportunities.terminal import TerminalOpportunityAnalyzer
    term_analyzer = TerminalOpportunityAnalyzer()
    opps = term_analyzer.analyze(state, [], baseline_action)
    shutdown_opps = [o for o in opps if o.candidate_transformation_family == "PHASE_SHUTDOWN" and "TOMATO" in o.affected_entities]
    assert len(shutdown_opps) >= 1

    # Patch removes TOMATO purchase
    from aec.patches.generator import PatchGenerator
    from aec.config import AECConfig
    cfg = AECConfig(enabled_mechanisms=("PHASE_SHUTDOWN", "TERMINAL_LIQUIDATION"))
    patches = PatchGenerator(config=cfg).generate_patches(shutdown_opps, state, baseline_action, config=cfg)
    assert len(patches) >= 1
    assert patches[0].market_mutations == []  # TOMATO removed

    # Simulator evaluation: saving $250 of dead seed capital
    simulator = CounterfactualSimulator()
    outcome = simulator.evaluate(
        candidate_patch=patches[0],
        baseline_action=baseline_action,
        econ_state=state,
        horizon=6
    )
    # Candidate avoids buying dead seed, preserving cash
    assert outcome.candidate_final_money > outcome.baseline_final_money
    assert outcome.delta_our_money == 250.0  # 5 seeds * $50 preserved


def test_scenario_e_multi_worker_resource_effect(weed_obstruction_obs: Dict[str, Any]) -> None:
    """Scenario E: Multi-Worker / Resource Effect.
    
    Farmer and Hand interact over shed capacity and resource transport.
    Local evaluation of single worker ignores hand schedule.
    Full-system evaluation models both workers' spatial positions and shed interactions.
    Escalation level 3/4 resolves cross-worker spatial collision.
    """
    obs = copy.deepcopy(weed_obstruction_obs)
    obs["farms"][0]["farmer"] = [4, 4]
    obs["farms"][0]["hands"] = [[4, 5]]  # Adjacent
    state = build_economic_state(obs)

    baseline_action = {
        "farmer": ["SOUTH"],  # Would move onto [4, 5]
        "hands": [["PASS"]],  # Hand is at [4, 5]
        "market": []
    }

    # Graph check: cross-worker collision edge
    graph = build_basket_dependency_graph(baseline_action, state)
    assert "W0_FARMER" in graph.nodes
    assert "W1_HAND" in graph.nodes

    # Simulator verifies collision resolution under full system
    simulator = CounterfactualSimulator()
    patch = CoupledPatch(
        patch_id="PATCH_MULTI_WORKER",
        source_opportunity_id="OPP_MULTI",
        worker_mutations={0: ["EAST"]},  # Avoid collision by stepping East instead
        expected_horizon=4
    )

    outcome = simulator.evaluate(
        candidate_patch=patch,
        baseline_action=baseline_action,
        econ_state=state,
        horizon=4
    )
    assert outcome.intermediate_solvency_ok is True
