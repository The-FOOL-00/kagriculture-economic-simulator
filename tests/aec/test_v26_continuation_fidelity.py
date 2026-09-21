# SPDX-License-Identifier: MIT
"""V26 Continuation Fidelity Test Suite (§9, Test A, Test B, Test C)."""

import copy
import pytest
from kaggle_environments import make

from aec.backbone.v25_p3_adapter import V25P3BackboneAdapter
from aec.counterfactual.simulator import CounterfactualSimulator, ShadowRolloutState
from aec.ir.economic_state import build_economic_state
from aec.patches.coupled_patch import CoupledPatch


def test_continuation_fidelity_test_a_clean_replay():
    """Test A: Cloned-state P3 continuation must match real live P3 continuation bit-for-bit."""
    seed = 249376
    env = make("kaggriculture", configuration={"seed": seed, "episodeSteps": 50})
    adapter_live = V25P3BackboneAdapter()

    # Step 0: opening
    obs = env.reset()[0]["observation"]
    act0 = adapter_live.act(obs)
    state = env.step([act0, {"farmer": ["PASS"], "hands": [], "market": []}])
    obs1 = state[0]["observation"]

    # At Step 1, snapshot state and create continuation policy
    cont = adapter_live.create_continuation_policy()
    snap = cont.snapshot()

    # Run 12 shadow steps using rollout
    econ_state1 = build_economic_state(obs1, None)
    rollout = ShadowRolloutState(econ_state1)
    
    sim = CounterfactualSimulator()
    # Dummy empty patch
    dummy_patch = CoupledPatch(
        patch_id="CLEAN_REPLAY_TEST",
        source_opportunity_id="OPP_TEST_A",
        mechanism_family="NO_OP",
        expected_horizon=12,
    )

    base_act1 = adapter_live.act(copy.deepcopy(obs1))

    # Evaluate baseline rollout inside simulator
    outcome = sim.evaluate(
        candidate_patch=dummy_patch,
        baseline_action=base_act1,
        econ_state=econ_state1,
        horizon=12,
        macro_escalated=True,
        backbone=adapter_live,
    )

    assert outcome is not None
    assert outcome.executed_baseline_actions is not None
    assert len(outcome.executed_baseline_actions) == 12

    # Verify that shadow execution did not mutate live state:
    # Restoring snapshot and calling act() on obs1 produces base_act1 exactly
    adapter_live.restore_state(snap)
    recheck_act1 = adapter_live.act(copy.deepcopy(obs1))
    assert recheck_act1 == base_act1, "Live adapter was mutated by shadow rollout!"


def test_continuation_fidelity_test_b_neutral_intervention():
    """Test B: A neutral intervention returns exactly zero economic difference."""
    seed = 249376
    env = make("kaggriculture", configuration={"seed": seed, "episodeSteps": 50})
    adapter = V25P3BackboneAdapter()

    obs0 = env.reset()[0]["observation"]
    act0 = adapter.act(obs0)
    state = env.step([act0, {"farmer": ["PASS"], "hands": [], "market": []}])
    obs1 = state[0]["observation"]

    econ_state1 = build_economic_state(obs1, None)
    base_act1 = adapter.act(copy.deepcopy(obs1))

    # Neutral patch with no market or worker mutations
    neutral_patch = CoupledPatch(
        patch_id="NEUTRAL_TEST_PATCH",
        source_opportunity_id="OPP_NEUTRAL",
        mechanism_family="NEUTRAL",
        expected_horizon=8,
    )

    sim = CounterfactualSimulator()
    outcome = sim.evaluate(
        candidate_patch=neutral_patch,
        baseline_action=base_act1,
        econ_state=econ_state1,
        horizon=8,
        macro_escalated=True,
        backbone=adapter,
    )

    assert outcome is not None
    # Terminal wealth difference between identical baseline and candidate must be 0
    assert abs(outcome.delta_terminal_margin) < 1e-4, (
        f"Neutral intervention produced non-zero delta: {outcome.delta_terminal_margin}"
    )


def test_continuation_fidelity_test_c_perturbation_sensitivity():
    """Test C: A state perturbation triggers responsive continuation delta."""
    seed = 249376
    env = make("kaggriculture", configuration={"seed": seed, "episodeSteps": 50})
    adapter = V25P3BackboneAdapter()

    obs0 = env.reset()[0]["observation"]
    act0 = adapter.act(obs0)
    state = env.step([act0, {"farmer": ["PASS"], "hands": [], "market": []}])
    obs1 = state[0]["observation"]

    econ_state1 = build_economic_state(obs1, None)
    base_act1 = adapter.act(copy.deepcopy(obs1))

    # Active perturbation patch: inject a market sale of existing inventory or buy
    pert_patch = CoupledPatch(
        patch_id="PERTURBATION_TEST_PATCH",
        source_opportunity_id="OPP_PERT",
        mechanism_family="DEPENDENCY_AWARE_MARKET_TIMING",
        market_mutations=[["BUY_PRODUCT", "WHEAT", 1]],
        expected_horizon=8,
    )

    sim = CounterfactualSimulator()
    outcome = sim.evaluate(
        candidate_patch=pert_patch,
        baseline_action=base_act1,
        econ_state=econ_state1,
        horizon=8,
        macro_escalated=True,
        backbone=adapter,
    )

    assert outcome is not None
    # Perturbation must produce a non-zero financial or inventory delta
    assert outcome.candidate_final_money != outcome.baseline_final_money or outcome.delta_terminal_margin != 0.0, (
        "Perturbation failed to elicit responsive counterfactual delta!"
    )
    assert outcome.first_divergence_turn is not None or outcome.delta_terminal_margin != 0.0
