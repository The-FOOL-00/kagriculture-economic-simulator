# SPDX-License-Identifier: MIT
"""Exact Counterfactual Fidelity and State Isolation Test Suite for Phase 017 (§30).

Mandatory Section 30 Tests:
1. Baseline continuation equivalence:
   Assert that baseline rollout with dynamic V3 continuation produces identical
   action traces and state trajectories to direct V3 continuation stepping.
2. Candidate continuation equivalence:
   Assert candidate continuation reproducibility across separate runs under identical initial state.
3. Multiple sequential counterfactual evaluations:
   Evaluate multiple candidate rollouts in sequence on the same turn; assert that
   candidate k+1 does not leak state from candidate k.
4. State restoration after long rollouts:
   Snapshot V3 and simulator state before an extended H=72 rollout; assert 100%
   bit-identical state restoration post-rollout.
5. Repeated evaluation determinism:
   Run simulator on same state and candidate 10 times; assert identical terminal margin deltas and telemetry.
6. Candidate perturbation isolation:
   Verify that perturbing candidate parameters (q +/- delta_q) produces isolated,
   non-interfering forward projections without mutating internal V3 policy state.
"""

import copy
import hashlib
import os
import sys
from typing import Any, Dict, List

import pytest

from aec.config import AECConfig
from aec.counterfactual.macro_detector import (
    MacroBoundaryProbeResult,
    MacroRegimeFingerprint,
    MacroRegimeTransitionDetector,
    MacroRegimeType,
)
from aec.counterfactual.simulator import CounterfactualSimulator
from aec.counterfactual.v3_continuation import (
    V3ContinuationPolicy,
    build_simulated_observation,
    restore_v3_state,
    snapshot_v3_state,
)
from aec.ir.economic_state import build_economic_state
from aec.patches.patch import CoupledPatch

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
V3_TARBALL_PATH = os.path.join(REPO_ROOT, "submission_Vj_kc_v3.tar.gz")
V3_EXPECTED_SHA = "845e0d10981b11b06d272048ff5cee30d70a0403dd757651a556a78c8bf18943"


def test_v3_chassis_hash_integrity():
    """Verify frozen V3 tarball hash matches exact expected SHA256 (§2, §30)."""
    assert os.path.exists(V3_TARBALL_PATH), f"V3 tarball not found at {V3_TARBALL_PATH}"
    with open(V3_TARBALL_PATH, "rb") as f:
        actual_sha = hashlib.sha256(f.read()).hexdigest()
    assert actual_sha == V3_EXPECTED_SHA, f"V3 SHA mismatch: expected {V3_EXPECTED_SHA}, got {actual_sha}"


class MockStatefulV3Agent:
    """Mock V3 agent that modifies its internal chassis state on every call."""

    def __init__(self, initial_cash_spent: int = 100):
        self.chassis = type(
            "C",
            (),
            {
                "state": {
                    "player_0": {
                        "cash_spent": initial_cash_spent,
                        "crops_harvested": 10,
                        "expansion_day": 12,
                    },
                    "v233_controller": {
                        "target_crop": "TOMATO",
                        "active_quadrants": ["NW", "NE"],
                    },
                    "call_count": 0,
                    "sim_step": 0,
                }
            },
        )()

    def __call__(self, obs: Dict[str, Any], config: Any = None) -> Dict[str, Any]:
        self.chassis.state["call_count"] += 1
        self.chassis.state["sim_step"] = obs.get("step", 0)
        self.chassis.state["player_0"]["cash_spent"] += 50
        # If cash is above 10,000, schedule capex buy
        farm_money = obs.get("farms", [{}])[0].get("money", 0.0)
        if farm_money >= 10000.0:
            market_act = [["BUY_ANIMAL", "SHEEP", 1]]
        else:
            market_act = []
        return {"farmer": ["PASS"], "hands": [], "market": market_act}


def make_test_economic_obs(
    step: int = 200,
    cash: float = 9500.0,
    shed: Dict[str, int] = None,
) -> Dict[str, Any]:
    day = step // 24
    hour = step % 24
    return {
        "step": step,
        "day": day,
        "hour": hour,
        "player": 0,
        "farms": [
            {
                "money": float(cash),
                "farmer": [4, 4],
                "hands": [],
                "tiles": [[None] * 10 for _ in range(10)],
                "unlocked_quadrants": ["NW"],
                "hires_today": 0,
            },
            {
                "money": 9500.0,
                "farmer": [4, 4],
                "hands": [],
                "tiles": [[None] * 10 for _ in range(10)],
                "unlocked_quadrants": ["NW"],
                "hires_today": 0,
            },
        ],
        "private": {
            "shed": shed or {"WHEAT": 50, "TOMATO": 20},
            "seeds": {},
            "inventories": [{}],
        },
        "market": {
            "prices": {
                "WHEAT": 25,
                "CARROT": 35,
                "TOMATO": 60,
                "STRAWBERRY": 120,
                "MELON": 250,
                "EGG": 50,
                "MILK": 160,
                "WOOL": 200,
                "FERTILIZER": 100,
            },
            "inventory": {
                "WHEAT": 10000,
                "CARROT": 10000,
                "TOMATO": 10000,
                "STRAWBERRY": 10000,
                "MELON": 10000,
                "EGG": 10000,
                "MILK": 10000,
                "WOOL": 10000,
                "FERTILIZER": 10000,
            },
        },
        "town": {"unlocked_shops": []},
    }


class TestPhase017CounterfactualFidelity:
    """Suite validating all 6 core fidelity and isolation invariants (§30)."""

    def test_1_baseline_continuation_equivalence(self):
        """Invariant 1: Baseline rollout with dynamic V3 continuation produces identical
        action traces and state trajectories to direct V3 continuation stepping.
        """
        obs = make_test_economic_obs(step=100, cash=5000.0, shed={"WHEAT": 20})
        econ_state = build_economic_state(obs)
        base_act = {"farmer": ["PASS"], "hands": [], "market": []}

        patch = CoupledPatch(
            patch_id="PATCH_DUMMY",
            source_opportunity_id="OPP_DUMMY",
            market_mutations=[["SELL", "WHEAT", 1]],
        )

        agent_direct = MockStatefulV3Agent(initial_cash_spent=200)
        agent_sim = MockStatefulV3Agent(initial_cash_spent=200)

        # Direct stepping via V3ContinuationPolicy
        from aec.counterfactual.simulator import ShadowRolloutState
        rollout_direct = ShadowRolloutState(econ_state)
        rollout_direct.step = 101
        rollout_direct.money = 5000.0
        policy_direct = V3ContinuationPolicy(agent_direct)
        direct_action = policy_direct.step_action(rollout_direct, player=econ_state.player)

        # Simulation stepping via CounterfactualSimulator
        simulator = CounterfactualSimulator()
        outcome = simulator.evaluate(
            candidate_patch=patch,
            baseline_action=base_act,
            econ_state=econ_state,
            horizon=18,
            v3_agent_callable=agent_sim,
            macro_escalated=True,
            macro_regime_type="BUDGET_GUARD_BLOCK",
        )

        # Baseline executed actions must contain the exact direct step
        assert outcome.executed_baseline_actions is not None
        assert len(outcome.executed_baseline_actions) > 1
        assert outcome.executed_baseline_actions[1] == direct_action

    def test_2_candidate_continuation_equivalence(self):
        """Invariant 2: Assert candidate continuation reproducibility across separate runs
        under identical initial state.
        """
        obs = make_test_economic_obs(step=120, cash=9500.0, shed={"WHEAT": 50})
        econ_state = build_economic_state(obs)
        base_act = {"farmer": ["PASS"], "hands": [], "market": []}

        patch = CoupledPatch(
            patch_id="PATCH_CAND",
            source_opportunity_id="OPP_CAND",
            market_mutations=[["SELL", "WHEAT", 30]],
        )

        agent1 = MockStatefulV3Agent(initial_cash_spent=500)
        agent2 = MockStatefulV3Agent(initial_cash_spent=500)

        sim = CounterfactualSimulator()
        outcome1 = sim.evaluate(
            candidate_patch=patch,
            baseline_action=base_act,
            econ_state=econ_state,
            horizon=36,
            v3_agent_callable=agent1,
            macro_escalated=True,
        )
        outcome2 = sim.evaluate(
            candidate_patch=patch,
            baseline_action=base_act,
            econ_state=econ_state,
            horizon=36,
            v3_agent_callable=agent2,
            macro_escalated=True,
        )

        # Action traces, money, and delta margins must be bit-exact identical
        assert outcome1.executed_candidate_actions == outcome2.executed_candidate_actions
        assert outcome1.executed_baseline_actions == outcome2.executed_baseline_actions
        assert outcome1.candidate_final_money == outcome2.candidate_final_money
        assert outcome1.delta_terminal_margin == outcome2.delta_terminal_margin
        assert outcome1.direct_intervention_effect == outcome2.direct_intervention_effect
        assert outcome1.macro_induced_continuation_delta == outcome2.macro_induced_continuation_delta

    def test_3_multiple_sequential_counterfactual_evaluations(self):
        """Invariant 3: Evaluate multiple candidate rollouts in sequence on the same turn;
        assert that candidate k+1 does not leak state from candidate k.
        """
        obs = make_test_economic_obs(step=150, cash=8000.0, shed={"WHEAT": 40, "TOMATO": 30})
        econ_state = build_economic_state(obs)
        base_act = {"farmer": ["PASS"], "hands": [], "market": []}

        patch_A = CoupledPatch(
            patch_id="PATCH_A",
            source_opportunity_id="OPP_A",
            market_mutations=[["SELL", "WHEAT", 10]],
        )
        patch_B = CoupledPatch(
            patch_id="PATCH_B",
            source_opportunity_id="OPP_B",
            market_mutations=[["SELL", "TOMATO", 15]],
        )
        patch_C = CoupledPatch(
            patch_id="PATCH_C",
            source_opportunity_id="OPP_C",
            market_mutations=[["SELL", "WHEAT", 25]],
        )

        agent = MockStatefulV3Agent(initial_cash_spent=1000)
        initial_agent_state = copy.deepcopy(agent.chassis.state)

        sim = CounterfactualSimulator()

        # Sequence 1: Evaluate A, then B, then C
        out_A = sim.evaluate(patch_A, base_act, econ_state, horizon=24, v3_agent_callable=agent, macro_escalated=True)
        out_B = sim.evaluate(patch_B, base_act, econ_state, horizon=24, v3_agent_callable=agent, macro_escalated=True)
        out_C_seq = sim.evaluate(patch_C, base_act, econ_state, horizon=24, v3_agent_callable=agent, macro_escalated=True)

        # Fresh agent evaluated on C directly
        agent_fresh = MockStatefulV3Agent(initial_cash_spent=1000)
        out_C_direct = sim.evaluate(patch_C, base_act, econ_state, horizon=24, v3_agent_callable=agent_fresh, macro_escalated=True)

        # Bit-exact equivalence between sequenced C and direct C
        assert out_C_seq.delta_terminal_margin == out_C_direct.delta_terminal_margin
        assert out_C_seq.candidate_final_money == out_C_direct.candidate_final_money
        assert out_C_seq.executed_candidate_actions == out_C_direct.executed_candidate_actions

        # Agent state after all evaluations must match initial snapshot
        assert agent.chassis.state == initial_agent_state

    def test_4_state_restoration_after_long_rollouts(self):
        """Invariant 4: Snapshot V3 and simulator state before an extended H=72 rollout;
        assert 100% bit-identical state restoration post-rollout.
        """
        obs = make_test_economic_obs(step=200, cash=11500.0, shed={"WHEAT": 80})
        econ_state = build_economic_state(obs)
        base_act = {"farmer": ["PASS"], "hands": [], "market": []}

        patch = CoupledPatch(
            patch_id="PATCH_LONG",
            source_opportunity_id="OPP_LONG",
            market_mutations=[["SELL", "WHEAT", 40]],
        )

        agent = MockStatefulV3Agent(initial_cash_spent=3500)
        snap = snapshot_v3_state(agent)
        state_dict_before = copy.deepcopy(agent.chassis.state)

        sim = CounterfactualSimulator()
        outcome = sim.evaluate(
            candidate_patch=patch,
            baseline_action=base_act,
            econ_state=econ_state,
            horizon=72,  # Extended long-horizon rollout
            v3_agent_callable=agent,
            macro_escalated=True,
            macro_regime_type="CASH_CAPEX_GATE",
        )

        # Invariant: agent chassis state must be 100% bit-identical to before rollout
        assert agent.chassis.state == state_dict_before
        assert snapshot_v3_state(agent) == snap
        assert outcome.horizon == 72

    def test_5_repeated_evaluation_determinism(self):
        """Invariant 5: Run simulator on same state and candidate 10 times;
        assert identical terminal margin deltas and telemetry.
        """
        obs = make_test_economic_obs(step=144, cash=6200.0, shed={"TOMATO": 25})
        econ_state = build_economic_state(obs)
        base_act = {"farmer": ["PASS"], "hands": [], "market": []}

        patch = CoupledPatch(
            patch_id="PATCH_REPEAT",
            source_opportunity_id="OPP_REPEAT",
            market_mutations=[["SELL", "TOMATO", 10]],
        )

        agent = MockStatefulV3Agent(initial_cash_spent=800)
        sim = CounterfactualSimulator()

        outcomes = []
        for _ in range(10):
            out = sim.evaluate(
                candidate_patch=patch,
                baseline_action=base_act,
                econ_state=econ_state,
                horizon=24,
                v3_agent_callable=agent,
                macro_escalated=True,
            )
            outcomes.append(out)

        reference = outcomes[0]
        for i, out in enumerate(outcomes[1:], start=1):
            assert out.delta_terminal_margin == reference.delta_terminal_margin, f"Delta mismatch on iter {i}"
            assert out.candidate_final_money == reference.candidate_final_money, f"Money mismatch on iter {i}"
            assert out.fidelity == reference.fidelity, f"Fidelity mismatch on iter {i}"
            assert out.direct_intervention_effect == reference.direct_intervention_effect
            assert out.macro_induced_continuation_delta == reference.macro_induced_continuation_delta

    def test_6_candidate_perturbation_isolation(self):
        """Invariant 6: Verify that perturbing candidate parameters (q +/- delta_q) produces
        isolated, non-interfering forward projections without mutating internal V3 policy state.
        """
        obs = make_test_economic_obs(step=168, cash=9200.0, shed={"WHEAT": 40})
        econ_state = build_economic_state(obs)
        base_act = {"farmer": ["PASS"], "hands": [], "market": []}

        # Perturbation family: q = 5, q = 10, q = 20
        quantities = [5, 10, 20]
        agent = MockStatefulV3Agent(initial_cash_spent=1500)
        initial_state = copy.deepcopy(agent.chassis.state)

        sim = CounterfactualSimulator()
        results = []

        for q in quantities:
            patch = CoupledPatch(
                patch_id=f"PATCH_PERTURB_q{q}",
                source_opportunity_id=f"OPP_q{q}",
                market_mutations=[["SELL", "WHEAT", q]],
            )
            out = sim.evaluate(
                candidate_patch=patch,
                baseline_action=base_act,
                econ_state=econ_state,
                horizon=36,
                v3_agent_callable=agent,
                macro_escalated=True,
            )
            results.append((q, out))
            # Verify agent state is untouched after every perturbation
            assert agent.chassis.state == initial_state

        # Assert monotonic direct cash injection
        assert results[0][1].direct_intervention_effect < results[1][1].direct_intervention_effect < results[2][1].direct_intervention_effect
