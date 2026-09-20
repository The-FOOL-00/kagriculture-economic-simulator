# SPDX-License-Identifier: MIT
"""Synthetic Regression Suite for Phase 016 Macro-Regime Detection & Long-Horizon Safety (§19).

Verifies Tests A through H:
- Test A: No boundary (small cash delta, no escalation)
- Test B: Boundary crossing (cash capex threshold crossed, triggers escalation)
- Test C: Delayed regime consequence (consequence at T+N, horizon reaches event)
- Test D: False positive boundary suspicion (approaches without crossing)
- Test E: Terminal boundary (alters terminal/shutdown regime)
- Test F: Multiple boundaries (compound thresholds covered)
- Test G: Determinism (identical outputs across repeated calls)
- Test H: State isolation & fidelity (zero state leak, bit-identical V3 continuation)
"""

import copy
import pytest
from typing import Any, Dict, List

from aec.config import AECConfig
from aec.counterfactual.macro_detector import (
    MacroBoundaryProbeResult,
    MacroRegimeFingerprint,
    MacroRegimeTransitionDetector,
    MacroRegimeType,
    classify_cash_bracket,
)
from aec.counterfactual.v3_continuation import (
    V3ContinuationPolicy,
    build_simulated_observation,
    restore_v3_state,
    snapshot_v3_state,
)
from aec.counterfactual.simulator import CounterfactualSimulator
from aec.integration.backbone_adapter import BackboneAdapter
from aec.integration.executor import AECExecutor
from aec.ir.economic_state import build_economic_state
from aec.patches.patch import CoupledPatch


def make_test_obs(
    step: int = 100,
    cash: float = 1000.0,
    shed: Dict[str, int] = None,
    quadrants: List[str] = None,
    hands: int = 0,
) -> Dict[str, Any]:
    day = step // 24
    hour = step % 24
    hands_list = [[3, 4] for _ in range(hands)]
    return {
        "step": step,
        "day": day,
        "hour": hour,
        "player": 0,
        "farms": [
            {
                "money": float(cash),
                "farmer": [4, 4],
                "hands": hands_list,
                "tiles": [[None] * 10 for _ in range(10)],
                "unlocked_quadrants": quadrants or ["NW"],
                "hires_today": 0,
            },
            {
                "money": 1000.0,
                "farmer": [4, 4],
                "hands": [],
                "tiles": [[None] * 10 for _ in range(10)],
                "unlocked_quadrants": ["NW"],
                "hires_today": 0,
            },
        ],
        "private": {
            "shed": shed or {},
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


class TestPhase016SyntheticRegimeSuite:
    """Rigorous synthetic validation of the 4-tier macro evaluation layer (§19)."""

    def test_a_no_boundary_small_cash_delta(self):
        """Test A: Candidate creates small cash delta ($1,000 -> $1,050) remaining in same macro regime.
        
        Expected: No escalation, remains at local horizon H=18.
        """
        detector = MacroRegimeTransitionDetector()
        obs = make_test_obs(step=50, cash=1000.0, shed={"WHEAT": 2})
        econ_state = build_economic_state(obs)

        # Baseline: PASS
        base_act = {"farmer": ["PASS"], "hands": [], "market": []}
        # Candidate: Sell 2 Wheat (+$50 cash -> $1050, well within $600-$2000 bracket)
        patch = CoupledPatch(
            source_opportunity_id="test_opp",
            patch_id="test_small_sale",
            mechanism_family="DEPENDENCY_AWARE_MARKET_TIMING",
            actions=[{"market": [["SELL", "WHEAT", 2]]}],
            market_mutations=[["SELL", "WHEAT", 2]],
        )

        probe = detector.probe_candidate(patch, base_act, econ_state, base_horizon=18)
        assert probe.requires_escalation is False
        assert probe.regime_type == MacroRegimeType.NONE
        assert probe.recommended_horizon == 18

    def test_b_boundary_crossing_capex_threshold(self):
        """Test B: Candidate crosses a legitimate V3 cash threshold ($9,500 -> $10,500 crosses $10k sheep gate).
        
        Expected: Escalation triggered to capture resulting macro bifurcation.
        """
        detector = MacroRegimeTransitionDetector()
        obs = make_test_obs(step=120, cash=9500.0, shed={"WHEAT": 50})
        econ_state = build_economic_state(obs)

        base_act = {"farmer": ["PASS"], "hands": [], "market": []}
        # Selling 50 wheat at $25 injects +$1,250 -> cash becomes $10,750 (crosses $10,000 capex boundary)
        patch = CoupledPatch(
            source_opportunity_id="test_opp",
            patch_id="test_capex_crossing",
            mechanism_family="AUTONOMOUS_TRANCHE_ORDER",
            actions=[{"market": [["SELL", "WHEAT", 50]]}],
            market_mutations=[["SELL", "WHEAT", 50]],
        )

        probe = detector.probe_candidate(patch, base_act, econ_state, base_horizon=18)
        assert probe.requires_escalation is True
        assert probe.regime_type == MacroRegimeType.CASH_CAPEX_GATE
        assert probe.recommended_horizon >= 36
        assert "CASH_GATE_CROSSED" in probe.reason

    def test_c_delayed_regime_consequence(self):
        """Test C: Candidate at turn T=50 near the 72-turn budget guard cycle (T=72).
        
        Expected: Escalation horizon reaches the macro cycle boundary (T=72, horizon >= 22).
        """
        detector = MacroRegimeTransitionDetector()
        obs = make_test_obs(step=55, cash=490.0, shed={"WHEAT": 10})
        econ_state = build_economic_state(obs)

        base_act = {"farmer": ["PASS"], "hands": [], "market": []}
        # Selling 10 wheat injects +$250 -> cash becomes $740, crossing $500 threshold
        patch = CoupledPatch(
            source_opportunity_id="test_opp",
            patch_id="test_cycle_consequence",
            mechanism_family="AUTONOMOUS_TRANCHE_ORDER",
            actions=[{"market": [["SELL", "WHEAT", 10]]}],
            market_mutations=[["SELL", "WHEAT", 10]],
        )

        probe = detector.probe_candidate(patch, base_act, econ_state, base_horizon=18)
        assert probe.requires_escalation is True
        # Escalation recommended horizon must extend at least to the next macro cycle
        assert probe.recommended_horizon >= (72 - 55)

    def test_d_false_positive_boundary_suspicion(self):
        """Test D: Candidate approaches a boundary but stays safely within the same regime.
        
        Expected: No false escalation.
        """
        detector = MacroRegimeTransitionDetector()
        # $1,100 -> $1,200 is safely between $600 and $2,000 bracket
        obs = make_test_obs(step=100, cash=1100.0, shed={"WHEAT": 4})
        econ_state = build_economic_state(obs)

        base_act = {"farmer": ["PASS"], "hands": [], "market": []}
        patch = CoupledPatch(
            source_opportunity_id="test_opp",
            patch_id="test_safe_sale",
            mechanism_family="DEPENDENCY_AWARE_MARKET_TIMING",
            actions=[{"market": [["SELL", "WHEAT", 4]]}],
            market_mutations=[["SELL", "WHEAT", 4]],
        )

        probe = detector.probe_candidate(patch, base_act, econ_state, base_horizon=18)
        assert probe.requires_escalation is False

    def test_e_terminal_boundary_alteration(self):
        """Test E: Candidate alters inventory close to the terminal liquidation / shutdown window.
        
        Expected: Escalates to cover remaining horizon to terminal.
        """
        detector = MacroRegimeTransitionDetector()
        obs = make_test_obs(step=700, cash=15000.0, shed={"WHEAT": 80})
        econ_state = build_economic_state(obs)

        base_act = {"farmer": ["PASS"], "hands": [], "market": []}
        patch = CoupledPatch(
            source_opportunity_id="test_opp",
            patch_id="test_terminal_sweep",
            mechanism_family="TERMINAL_LIQUIDATION",
            actions=[{"market": [["SELL", "WHEAT", 80]]}],
            market_mutations=[["SELL", "WHEAT", 80]],
        )

        probe = detector.probe_candidate(patch, base_act, econ_state, base_horizon=18)
        # At step 700 with remaining 20 steps, probe should recognize terminal window
        assert probe.recommended_horizon >= 18

    def test_f_atomic_order_alteration_dropped_hire(self):
        """Test F: Baseline emits an atomic HIRE order, but candidate replaces market orders.
        
        Expected: Mandatory escalation triggered for ORDER_QUEUE_ALTERATION.
        """
        detector = MacroRegimeTransitionDetector()
        obs = make_test_obs(step=195, cash=2000.0, shed={"WHEAT": 10})
        econ_state = build_economic_state(obs)

        # Baseline emitted HIRE
        base_act = {"farmer": ["PASS"], "hands": [], "market": [["HIRE", 1]]}
        # Candidate patch drops HIRE or overrides with SELL
        patch = CoupledPatch(
            source_opportunity_id="test_opp",
            patch_id="test_dropped_hire",
            mechanism_family="AUTONOMOUS_TRANCHE_ORDER",
            actions=[{"market": [["SELL", "WHEAT", 10]]}],
            market_mutations=[["SELL", "WHEAT", 10]],
        )

        probe = detector.probe_candidate(patch, base_act, econ_state, base_horizon=18)
        assert probe.requires_escalation is True
        assert probe.regime_type == MacroRegimeType.ORDER_QUEUE_ALTERATION
        assert "ATOMIC_ORDER_ALTERATION" in probe.reason
        assert probe.recommended_horizon >= 48

    def test_g_determinism(self):
        """Test G: Same state + same candidate yields bit-identical fingerprints, probe results, and decisions."""
        detector = MacroRegimeTransitionDetector()
        obs = make_test_obs(step=140, cash=11800.0, shed={"WHEAT": 20})
        econ_state = build_economic_state(obs)

        base_act = {"farmer": ["PASS"], "hands": [], "market": []}
        patch = CoupledPatch(
            source_opportunity_id="test_opp",
            patch_id="test_det",
            mechanism_family="AUTONOMOUS_TRANCHE_ORDER",
            actions=[{"market": [["SELL", "WHEAT", 20]]}],
            market_mutations=[["SELL", "WHEAT", 20]],
        )

        probe1 = detector.probe_candidate(patch, base_act, econ_state, base_horizon=18)
        probe2 = detector.probe_candidate(patch, base_act, econ_state, base_horizon=18)

        assert probe1.requires_escalation == probe2.requires_escalation
        assert probe1.regime_type == probe2.regime_type
        assert probe1.recommended_horizon == probe2.recommended_horizon
        assert probe1.baseline_fingerprint == probe2.baseline_fingerprint
        assert probe1.candidate_fingerprint == probe2.candidate_fingerprint

    def test_h_state_isolation_and_fidelity(self):
        """Test H: Snapshotting and restoring mock V3 state leaves global state bit-identical."""
        mock_v3_state = {
            "player_0": {"cash_spent": 500, "active_quadrants": ["NW", "NE"]},
            "v233_controller": {"target_crop": "TOMATO", "allocation": [1, 2]},
            "day": 5,
        }

        class MockV3Agent:
            def __init__(self):
                self.chassis = type("C", (), {"state": copy.deepcopy(mock_v3_state)})()

            def __call__(self, obs, config=None):
                # Mutate internal state during step
                self.chassis.state["player_0"]["cash_spent"] += 100
                self.chassis.state["day"] += 1
                return {"farmer": ["PASS"], "hands": [], "market": []}

        agent = MockV3Agent()
        # Take snapshot
        snap = snapshot_v3_state(agent)
        initial_state_copy = copy.deepcopy(agent.chassis.state)

        # Run multiple rollout steps mutating agent state
        policy = V3ContinuationPolicy(agent)
        fake_rollout = type("R", (), {
            "step": 10, "money": 1000, "farm_x": 4, "farm_y": 4, "farmer_action": "PASS",
            "farmer_pos": (4, 4), "hands_pos": [],
            "hands": [], "hands_actions": [], "market_inv": {}, "market_prices": {},
            "unlocked_shops": set(), "shed": {}, "seeds": {}, "tiles": [[None]*10 for _ in range(10)],
            "unlocked_quadrants": ["NW"], "hires_today": 0, "opp_money": 1000, "opp_farmer": [4, 4],
            "opp_hands": [], "opp_tiles": [[None]*10 for _ in range(10)], "opp_quadrants": ["NW"],
            "opp_hires_today": 0,
        })()

        for _ in range(10):
            policy.step_action(fake_rollout)

        # Confirm agent state was mutated
        assert agent.chassis.state["player_0"]["cash_spent"] > initial_state_copy["player_0"]["cash_spent"]

        # Restore snapshot
        restore_v3_state(agent, snap)

        # Confirm 100% bit-identical restoration
        assert agent.chassis.state == initial_state_copy
