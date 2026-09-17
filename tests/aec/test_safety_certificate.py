# SPDX-License-Identifier: MIT
"""Test K — Safety Certificate Generation and Invariant Enforcements."""

from aec.counterfactual.simulator import SimulationOutcome
from aec.ir import build_economic_state
from aec.patches import CoupledPatch
from aec.safety import SafetyCertificate, SafetyChecker


def test_safety_check_passes_valid_proposal(terminal_proximity_obs):
    state = build_economic_state(terminal_proximity_obs)
    patch = CoupledPatch(
        patch_id="SAFE_P",
        source_opportunity_id="OPP_SAFE",
        market_mutations=[["SELL", "STRAWBERRY", 10]]
    )
    outcome = SimulationOutcome(
        candidate_final_money=16200.0,
        baseline_final_money=15000.0,
        delta_our_money=1200.0,
        candidate_opp_final_money=14000.0,
        baseline_opp_final_money=14000.0,
        delta_opponent_money=0.0,
        delta_terminal_margin=1200.0,
        candidate_overflow_units=0,
        candidate_sold={"STRAWBERRY": 10},
        baseline_sold={},
        intermediate_solvency_ok=True,
        horizon=2
    )
    
    checker = SafetyChecker()
    passed, checks, reason = checker.verify(
        patch, outcome, state, {"farmer": ["PASS"], "hands": [], "market": []}
    )
    
    assert passed is True
    assert checks["overflow_ok"] is True
    assert checks["solvency_ok"] is True
    assert reason is None


def test_safety_check_rejects_overflow(terminal_proximity_obs):
    state = build_economic_state(terminal_proximity_obs)
    patch = CoupledPatch(
        patch_id="UNSAFE_P",
        source_opportunity_id="OPP_UNSAFE",
        market_mutations=[["SELL", "STRAWBERRY", 10]]
    )
    # Outcome with shed overflow
    outcome = SimulationOutcome(
        candidate_final_money=16200.0,
        baseline_final_money=15000.0,
        delta_our_money=1200.0,
        candidate_opp_final_money=14000.0,
        baseline_opp_final_money=14000.0,
        delta_opponent_money=0.0,
        delta_terminal_margin=1200.0,
        candidate_overflow_units=5,  # 5 units overflow discarded!
        candidate_sold={"STRAWBERRY": 10},
        baseline_sold={},
        intermediate_solvency_ok=True,
        horizon=2
    )
    
    checker = SafetyChecker()
    passed, checks, reason = checker.verify(
        patch, outcome, state, {"farmer": ["PASS"], "hands": [], "market": []}
    )
    
    assert passed is False
    assert checks["overflow_ok"] is False
    assert "overflow" in reason.lower()


def test_safety_check_rejects_failed_fidelity(terminal_proximity_obs):
    """Verifies that SafetyChecker rejects any outcome with FAILED fidelity (§14)."""
    state = build_economic_state(terminal_proximity_obs)
    patch = CoupledPatch(
        patch_id="UNVERIFIED_P",
        source_opportunity_id="OPP_UNVERIFIED",
        market_mutations=[["SELL", "STRAWBERRY", 10]]
    )
    outcome = SimulationOutcome(
        candidate_final_money=16200.0,
        baseline_final_money=15000.0,
        delta_our_money=1200.0,
        candidate_opp_final_money=14000.0,
        baseline_opp_final_money=14000.0,
        delta_opponent_money=0.0,
        delta_terminal_margin=1200.0,
        candidate_overflow_units=0,
        candidate_sold={"STRAWBERRY": 10},
        baseline_sold={},
        intermediate_solvency_ok=True,
        horizon=2,
        fidelity="FAILED",
        fidelity_reasons=["Semantic parity divergence detected"]
    )

    checker = SafetyChecker()
    passed, checks, reason = checker.verify(
        patch, outcome, state, {"farmer": ["PASS"], "hands": [], "market": []}
    )

    assert passed is False
    assert checks["fidelity_ok"] is False
    assert "fidelity failed" in reason.lower()


def test_safety_check_rejects_unknown_fidelity(terminal_proximity_obs):
    """Verifies that SafetyChecker rejects any outcome with UNKNOWN fidelity (§7, §28)."""
    state = build_economic_state(terminal_proximity_obs)
    patch = CoupledPatch(
        patch_id="UNKNOWN_P",
        source_opportunity_id="OPP_UNKNOWN",
        market_mutations=[["SELL", "STRAWBERRY", 10]]
    )
    outcome = SimulationOutcome(
        candidate_final_money=16200.0,
        baseline_final_money=15000.0,
        delta_our_money=1200.0,
        candidate_opp_final_money=14000.0,
        baseline_opp_final_money=14000.0,
        delta_opponent_money=0.0,
        delta_terminal_margin=1200.0,
        candidate_overflow_units=0,
        candidate_sold={"STRAWBERRY": 10},
        baseline_sold={},
        intermediate_solvency_ok=True,
        horizon=2,
        fidelity="UNKNOWN",
        fidelity_reasons=["Unmodelled state interaction"]
    )

    checker = SafetyChecker()
    passed, checks, reason = checker.verify(
        patch, outcome, state, {"farmer": ["PASS"], "hands": [], "market": []}
    )

    assert passed is False
    assert checks["fidelity_ok"] is False
    assert "fidelity unknown" in reason.lower()
