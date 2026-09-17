# SPDX-License-Identifier: MIT
"""Test G & Test P — Counterfactual State Isolation and Multi-Candidate Purity."""

import copy
from aec.counterfactual import CounterfactualSimulator
from aec.ir import build_economic_state
from aec.patches import CoupledPatch


def test_simulation_state_isolation(terminal_proximity_obs):
    state = build_economic_state(terminal_proximity_obs)
    baseline_action = {"farmer": ["PASS"], "hands": [["PASS"]], "market": []}
    
    # Take snapshots before simulation
    cash_before = state.farm.cash
    shed_before = copy.deepcopy(state.farm.shed_inventory)
    baseline_copy = copy.deepcopy(baseline_action)
    
    patch = CoupledPatch(
        patch_id="PATCH_TEST",
        source_opportunity_id="OPP_TEST",
        market_mutations=[["SELL", "STRAWBERRY", 10]],
        expected_horizon=6
    )
    
    simulator = CounterfactualSimulator()
    outcome = simulator.evaluate(patch, baseline_action, state, horizon=6)
    
    # 1. State must not be mutated
    assert state.farm.cash == cash_before
    assert state.farm.shed_inventory == shed_before
    assert baseline_action == baseline_copy
    
    # 2. Outcome must reflect simulated changes
    assert outcome.candidate_final_money > outcome.baseline_final_money
    assert outcome.delta_our_money > 0


def test_multi_candidate_independence(terminal_proximity_obs):
    state = build_economic_state(terminal_proximity_obs)
    baseline_action = {"farmer": ["PASS"], "hands": [["PASS"]], "market": []}
    
    patch_A = CoupledPatch(
        patch_id="PATCH_A",
        source_opportunity_id="OPP_A",
        market_mutations=[["SELL", "STRAWBERRY", 5]],
        expected_horizon=4
    )
    patch_B = CoupledPatch(
        patch_id="PATCH_B",
        source_opportunity_id="OPP_B",
        market_mutations=[["SELL", "WOOL", 8]],
        expected_horizon=4
    )
    
    simulator = CounterfactualSimulator()
    
    # Evaluate A then B, then A again
    outcome_A1 = simulator.evaluate(patch_A, baseline_action, state, horizon=4)
    outcome_B = simulator.evaluate(patch_B, baseline_action, state, horizon=4)
    outcome_A2 = simulator.evaluate(patch_A, baseline_action, state, horizon=4)
    
    # A1 and A2 must be bit-exact identical
    assert outcome_A1.candidate_final_money == outcome_A2.candidate_final_money
    assert outcome_A1.delta_terminal_margin == outcome_A2.delta_terminal_margin
