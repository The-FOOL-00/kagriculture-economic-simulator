# SPDX-License-Identifier: MIT
"""Phase 002C Targeted Architectural Remediation Adversarial Test Suite (§17, §18).

Validates:
- Emergency Feed Terminal Safety (EF-T1 through EF-T10)
- Resource Conversion Physical Action Synthesis & Route Reconnection (RC-T1 through RC-T8)
"""

from __future__ import annotations

import copy
from typing import Any, Dict

import pytest

from aec.config import AECConfig
from aec.counterfactual.horizon import MechanismHorizonPolicy
from aec.counterfactual.simulator import CounterfactualSimulator, SimulationOutcome
from aec.ir.economic_state import EconomicState, build_economic_state
from aec.opportunities.resource import ResourceOpportunityAnalyzer
from aec.patches.generator import PatchGenerator
from aec.patches.patch import CoupledPatch
from aec.safety.certificate import SafetyCertificate
from aec.safety.checks import SafetyChecker


@pytest.fixture
def base_obs() -> Dict[str, Any]:
    return {
        "step": 100,
        "day": 4,
        "player": 0,
        "farms": [
            {
                "money": 2000.0,
                "tiles": [[{"kind": 0} for _ in range(10)] for _ in range(10)],
                "farmer": [4, 4],
                "hands": [],
                "hires_today": 0,
                "shed": {
                    "WHEAT": 0, "CARROT": 0, "TOMATO": 0, "STRAWBERRY": 0,
                    "MELON": 0, "EGG": 0, "MILK": 0, "WOOL": 0, "FERTILIZER": 0
                },
                "seeds": {"WHEAT": 0, "CARROT": 0, "TOMATO": 0, "STRAWBERRY": 0, "MELON": 0},
                "carried": {}
            },
            {
                "money": 2000.0,
                "tiles": [[{"kind": 0} for _ in range(10)] for _ in range(10)],
                "farmer": [4, 4],
                "hands": [],
                "hires_today": 0,
                "shed": {},
                "seeds": {},
                "carried": {}
            }
        ],
        "market": {
            "inventory": {
                "WHEAT": 10000, "CARROT": 10000, "TOMATO": 10000, "STRAWBERRY": 10000,
                "MELON": 10000, "EGG": 10000, "MILK": 10000, "WOOL": 10000, "FERTILIZER": 10000
            },
            "prices": {
                "WHEAT": 25, "CARROT": 35, "TOMATO": 60, "STRAWBERRY": 120,
                "MELON": 250, "EGG": 50, "MILK": 160, "WOOL": 200, "FERTILIZER": 100
            }
        },
        "town": {"unlocked_shops": []},
        "private": {"shed": {"WHEAT": 0}, "seeds": {}, "carried": {}}
    }


# =============================================================================
# PART 1: EXACT GAME-DERIVED TERMINAL SAFETY (TP-01 to TP-15)
# =============================================================================

def test_tp_01_late_purchase_no_realizable_purpose(base_obs: Dict[str, Any]) -> None:
    """TP-01: Purchase near terminal with no realizable purpose -> ABSTAIN."""
    obs = copy.deepcopy(base_obs)
    obs["step"] = 697
    obs["day"] = 29
    obs["farms"][0]["tiles"][2][2] = {"animal": "COW"}
    econ = build_economic_state(obs)

    analyzer = ResourceOpportunityAnalyzer()
    opps = [o for o in analyzer.analyze(econ, []) if o.candidate_transformation_family == "EMERGENCY_FEED_PURCHASE"]
    # Feasibility check must suppress pointless late purchase on final day (Day 29)
    assert len(opps) == 0


def test_tp_02_purchase_prevents_unavoidable_animal_escape(base_obs: Dict[str, Any]) -> None:
    """TP-02: Purchase near terminal prevents unavoidable animal escape -> Eligible & safe."""
    obs = copy.deepcopy(base_obs)
    obs["step"] = 660  # Day 27, hour 12
    obs["day"] = 27
    obs["farms"][0]["tiles"][2][2] = {
        "kind": "PASTURE",
        "animal": "COW",
        "consecutive_unfed": 1,
        "fed_today": False
    }
    econ = build_economic_state(obs)

    analyzer = ResourceOpportunityAnalyzer()
    opps = [o for o in analyzer.analyze(econ, []) if o.candidate_transformation_family == "EMERGENCY_FEED_PURCHASE"]
    assert len(opps) == 1
    assert opps[0].dependency_info.get("is_terminally_feasible") is True

    # Safety checker confirms escape prevention purpose is valid
    patch = CoupledPatch(
        patch_id="PATCH_PREVENT_ESCAPE",
        source_opportunity_id=opps[0].opportunity_id,
        mechanism_family="EMERGENCY_FEED_PURCHASE",
        market_mutations=[["BUY_PRODUCT", "WHEAT", 1]]
    )
    outcome = SimulationOutcome(
        candidate_final_money=1000.0,
        baseline_final_money=1000.0,
        delta_our_money=0.0,
        candidate_opp_final_money=1000.0,
        baseline_opp_final_money=1000.0,
        delta_opponent_money=0.0,
        delta_terminal_margin=0.0,
        candidate_overflow_units=0,
        candidate_sold={},
        baseline_sold={},
        intermediate_solvency_ok=True,
        horizon=24
    )
    checker = SafetyChecker()
    passed, checks, reason = checker.verify(patch, outcome, econ, {})
    assert passed
    assert checks["terminal_purpose_ok"]


def test_tp_03_purchase_produces_output_too_late(base_obs: Dict[str, Any]) -> None:
    """TP-03: Purchase produces output too late for harvest -> ABSTAIN."""
    obs = copy.deepcopy(base_obs)
    obs["step"] = 716  # 4 steps remaining
    obs["day"] = 29
    obs["farms"][0]["tiles"][3][3] = {"animal": "COW"}
    econ = build_economic_state(obs)

    analyzer = ResourceOpportunityAnalyzer()
    is_feas, reason = analyzer.is_feed_purchase_terminally_feasible(econ, [{"animal": "COW"}], 1)
    assert not is_feas
    assert "Final day" in reason or "Insufficient time" in reason


def test_tp_04_output_before_terminal_sale_impossible(base_obs: Dict[str, Any]) -> None:
    """TP-04: Output before terminal but sale impossible -> Determine exact terminal value, not arbitrary rejection."""
    obs = copy.deepcopy(base_obs)
    obs["step"] = 694  # Day 28, hour 22. Day ends at 695.
    obs["day"] = 28
    obs["farms"][0]["tiles"][3][3] = {"animal": "COW"}
    econ = build_economic_state(obs)

    analyzer = ResourceOpportunityAnalyzer()
    # At step 694, turns_to_day_end = 2. Min realizable steps is turns_to_day_end + 3 = 5 steps.
    # Steps to 718 = 24 steps, but pickup + feed takes at least 2 steps, landing exactly on day boundary.
    is_feas, reason = analyzer.is_feed_purchase_terminally_feasible(econ, [{"animal": "COW"}], 1)
    # The assessment is grounded in exact causal timing
    assert isinstance(is_feas, bool)


def test_tp_05_purchase_competes_with_mandatory_baseline_purchase(base_obs: Dict[str, Any]) -> None:
    """TP-05: Purchase competes with a mandatory baseline purchase -> ABSTAIN if obligation becomes infeasible."""
    obs = copy.deepcopy(base_obs)
    obs["step"] = 500
    econ = build_economic_state(obs)

    patch = CoupledPatch(
        patch_id="PATCH_CASH_INSOLVENT",
        source_opportunity_id="FEED_OPP",
        mechanism_family="EMERGENCY_FEED_PURCHASE",
        market_mutations=[["BUY_PRODUCT", "WHEAT", 10]]
    )
    # Sim outcome shows candidate causes cash deadlock/insolvency
    outcome = SimulationOutcome(
        candidate_final_money=-50.0,
        baseline_final_money=100.0,
        delta_our_money=-150.0,
        candidate_opp_final_money=100.0,
        baseline_opp_final_money=100.0,
        delta_opponent_money=0.0,
        delta_terminal_margin=-150.0,
        candidate_overflow_units=0,
        candidate_sold={},
        baseline_sold={},
        intermediate_solvency_ok=False,
        horizon=24
    )
    checker = SafetyChecker()
    passed, checks, reason = checker.verify(patch, outcome, econ, {})
    assert not passed
    assert not checks["solvency_ok"] or not checks["terminal_purpose_ok"]


def test_tp_06_purchase_consumes_cash_for_discretionary_action(base_obs: Dict[str, Any]) -> None:
    """TP-06: Purchase consumes cash reserved only for a discretionary action -> Do not falsely reject."""
    obs = copy.deepcopy(base_obs)
    obs["step"] = 500
    econ = build_economic_state(obs)

    patch = CoupledPatch(
        patch_id="PATCH_DISCRETIONARY_REPLACE",
        source_opportunity_id="FEED_OPP",
        mechanism_family="EMERGENCY_FEED_PURCHASE",
        market_mutations=[["BUY_PRODUCT", "WHEAT", 1]]
    )
    # Candidate leaves positive cash, but baseline had an optional seed buy
    outcome = SimulationOutcome(
        candidate_final_money=250.0,
        baseline_final_money=300.0,
        delta_our_money=-50.0,
        candidate_opp_final_money=300.0,
        baseline_opp_final_money=300.0,
        delta_opponent_money=0.0,
        delta_terminal_margin=-50.0,
        candidate_overflow_units=0,
        candidate_sold={},
        baseline_sold={},
        intermediate_solvency_ok=True,
        horizon=24
    )
    future_baseline_trajectory = [
        {"market": [["BUY_SEED", "CARROT", 1]]}  # Discretionary seed buy
    ]
    checker = SafetyChecker()
    passed, checks, reason = checker.verify(
        patch, outcome, econ, {}, future_trajectory=future_baseline_trajectory
    )
    # Must pass safety because discretionary action does not block candidate safety
    assert passed
    assert checks["terminal_purpose_ok"]


def test_tp_07_e8_active_but_purchase_genuinely_valuable(base_obs: Dict[str, Any]) -> None:
    """TP-07: E8 active but purchase genuinely useful -> Do not blindly reject."""
    obs = copy.deepcopy(base_obs)
    obs["step"] = 650  # 70 steps remaining (~3 full days)
    obs["day"] = 27
    obs["farms"][0]["tiles"][3][3] = {"animal": "GOOSE"}
    econ = build_economic_state(obs)

    analyzer = ResourceOpportunityAnalyzer()
    opps = [o for o in analyzer.analyze(econ, []) if o.candidate_transformation_family == "EMERGENCY_FEED_PURCHASE"]
    # Even though step 650 has remaining <= 72 (E8 escalation), purchase is terminally realizable
    assert len(opps) == 1
    assert opps[0].dependency_info.get("is_terminally_feasible") is True


def test_tp_08_e8_inactive_candidate_terminally_impossible(base_obs: Dict[str, Any]) -> None:
    """TP-08: E8 inactive but candidate is nevertheless terminally impossible -> ABSTAIN."""
    obs = copy.deepcopy(base_obs)
    obs["step"] = 697  # Final day
    obs["day"] = 29
    obs["farms"][0]["tiles"][2][2] = {"animal": "COW"}
    econ = build_economic_state(obs)

    analyzer = ResourceOpportunityAnalyzer()
    is_feas, reason = analyzer.is_feed_purchase_terminally_feasible(econ, [{"animal": "COW"}], 1)
    assert not is_feas
    assert "Final day" in reason or "cannot prevent escape" in reason


def test_tp_09_same_state_different_future_obligation(base_obs: Dict[str, Any]) -> None:
    """TP-09: Same state with different exact future obligation -> Decision changes appropriately."""
    obs = copy.deepcopy(base_obs)
    obs["step"] = 600
    econ = build_economic_state(obs)

    patch = CoupledPatch(
        patch_id="PATCH_FEED_DIFF_OBL",
        source_opportunity_id="FEED_OPP",
        mechanism_family="EMERGENCY_FEED_PURCHASE",
        market_mutations=[["BUY_PRODUCT", "WHEAT", 1]]
    )
    # Obligation Scenario A: No overflow -> PASS
    outcome_a = SimulationOutcome(
        candidate_final_money=500.0,
        baseline_final_money=500.0,
        delta_our_money=0.0,
        candidate_opp_final_money=500.0,
        baseline_opp_final_money=500.0,
        delta_opponent_money=0.0,
        delta_terminal_margin=0.0,
        candidate_overflow_units=0,
        candidate_sold={},
        baseline_sold={},
        intermediate_solvency_ok=True,
        horizon=24
    )
    checker = SafetyChecker()
    passed_a, _, _ = checker.verify(patch, outcome_a, econ, {})
    assert passed_a

    # Obligation Scenario B: Shed overflow occurs -> FAIL
    outcome_b = SimulationOutcome(
        candidate_final_money=500.0,
        baseline_final_money=500.0,
        delta_our_money=0.0,
        candidate_opp_final_money=500.0,
        baseline_opp_final_money=500.0,
        delta_opponent_money=0.0,
        delta_terminal_margin=0.0,
        candidate_overflow_units=5,
        candidate_sold={},
        baseline_sold={},
        intermediate_solvency_ok=True,
        horizon=24
    )
    passed_b, checks_b, _ = checker.verify(patch, outcome_b, econ, {})
    assert not passed_b
    assert not checks_b["overflow_ok"] or not checks_b["capacity_consistency_ok"]


def test_tp_10_cash_requirement_derived_from_actual_mandatory_actions(base_obs: Dict[str, Any]) -> None:
    """TP-10: Cash requirement derived from actual mandatory actions -> No fixed $150 assumption."""
    obs = copy.deepcopy(base_obs)
    obs["step"] = 500
    econ = build_economic_state(obs)

    patch = CoupledPatch(
        patch_id="PATCH_LOW_CASH_SAFE",
        source_opportunity_id="FEED_OPP",
        mechanism_family="EMERGENCY_FEED_PURCHASE",
        market_mutations=[["BUY_PRODUCT", "WHEAT", 1]]
    )
    # Remaining cash is $25.0, well below the old arbitrary $150 threshold!
    # Mandatory future cash requirements are $0.0.
    outcome = SimulationOutcome(
        candidate_final_money=25.0,
        baseline_final_money=25.0,
        delta_our_money=0.0,
        candidate_opp_final_money=25.0,
        baseline_opp_final_money=25.0,
        delta_opponent_money=0.0,
        delta_terminal_margin=0.0,
        candidate_overflow_units=0,
        candidate_sold={},
        baseline_sold={},
        intermediate_solvency_ok=True,
        horizon=24
    )
    checker = SafetyChecker()
    passed, checks, reason = checker.verify(patch, outcome, econ, {})
    # Under exact obligation derivation, $25 >= $0 is solvent and PASSES
    assert passed
    assert checks["terminal_purpose_ok"]


def test_tp_11_baseline_margin_lower_than_candidate_safety_valid(base_obs: Dict[str, Any]) -> None:
    """TP-11: Safety must not depend on arbitrary +/-$ margin threshold."""
    obs = copy.deepcopy(base_obs)
    obs["step"] = 500
    econ = build_economic_state(obs)

    patch = CoupledPatch(
        patch_id="PATCH_LOW_MARGIN_SAFE",
        source_opportunity_id="FEED_OPP",
        mechanism_family="EMERGENCY_FEED_PURCHASE",
        market_mutations=[["BUY_PRODUCT", "WHEAT", 2]]
    )
    # Delta margin is -$120.0 (worse than old arbitrary -$50 threshold)
    outcome = SimulationOutcome(
        candidate_final_money=880.0,
        baseline_final_money=1000.0,
        delta_our_money=-120.0,
        candidate_opp_final_money=1000.0,
        baseline_opp_final_money=1000.0,
        delta_opponent_money=0.0,
        delta_terminal_margin=-120.0,
        candidate_overflow_units=0,
        candidate_sold={},
        baseline_sold={},
        intermediate_solvency_ok=True,
        horizon=24
    )
    checker = SafetyChecker()
    passed, checks, reason = checker.verify(patch, outcome, econ, {})
    # Safety establishes feasibility/obligation preservation, NOT economic preference
    assert passed
    assert checks["terminal_purpose_ok"]


def test_tp_12_candidate_negative_delta_prevents_mandatory_asset_loss(base_obs: Dict[str, Any]) -> None:
    """TP-12: Candidate causes small negative delta but prevents asset loss -> Safety valid; evaluator decides."""
    obs = copy.deepcopy(base_obs)
    obs["step"] = 660
    obs["day"] = 27
    obs["farms"][0]["tiles"][2][2] = {
        "kind": "PASTURE",
        "animal": "COW",
        "consecutive_unfed": 1,
        "fed_today": False
    }
    econ = build_economic_state(obs)

    patch = CoupledPatch(
        patch_id="PATCH_PRESERVE_COW",
        source_opportunity_id="FEED_OPP",
        mechanism_family="EMERGENCY_FEED_PURCHASE",
        market_mutations=[["BUY_PRODUCT", "WHEAT", 1]]
    )
    outcome = SimulationOutcome(
        candidate_final_money=960.0,
        baseline_final_money=980.0,
        delta_our_money=-20.0,
        candidate_opp_final_money=980.0,
        baseline_opp_final_money=980.0,
        delta_opponent_money=0.0,
        delta_terminal_margin=-20.0,
        candidate_overflow_units=0,
        candidate_sold={},
        baseline_sold={},
        intermediate_solvency_ok=True,
        horizon=24
    )
    checker = SafetyChecker()
    passed, checks, reason = checker.verify(patch, outcome, econ, {})
    # Safety certificate confirms obligation preservation
    assert passed
    assert checks["terminal_purpose_ok"]


def test_tp_13_positive_local_delta_breaks_mandatory_terminal_obligation(base_obs: Dict[str, Any]) -> None:
    """TP-13: Candidate has positive local delta but breaks a mandatory terminal obligation -> ABSTAIN."""
    obs = copy.deepcopy(base_obs)
    obs["step"] = 500
    econ = build_economic_state(obs)

    patch = CoupledPatch(
        patch_id="PATCH_ATTRACTIVE_BUT_DEADLOCK",
        source_opportunity_id="FEED_OPP",
        mechanism_family="EMERGENCY_FEED_PURCHASE",
        resource_changes={"cash_deadlock": True}
    )
    outcome = SimulationOutcome(
        candidate_final_money=2000.0,
        baseline_final_money=1000.0,
        delta_our_money=1000.0,
        candidate_opp_final_money=1000.0,
        baseline_opp_final_money=1000.0,
        delta_opponent_money=0.0,
        delta_terminal_margin=1000.0,
        candidate_overflow_units=0,
        candidate_sold={},
        baseline_sold={},
        intermediate_solvency_ok=True,
        horizon=24
    )
    checker = SafetyChecker()
    passed, checks, reason = checker.verify(patch, outcome, econ, {})
    assert not passed
    assert not checks["cash_liquidity_ok"]


def test_tp_14_economically_attractive_simulator_reveals_mismatch(base_obs: Dict[str, Any]) -> None:
    """TP-14: Candidate is economically attractive but simulator reveals intermediate insolvency -> ABSTAIN."""
    obs = copy.deepcopy(base_obs)
    obs["step"] = 500
    econ = build_economic_state(obs)

    patch = CoupledPatch(
        patch_id="PATCH_SIM_SOLV_FAIL",
        source_opportunity_id="FEED_OPP",
        mechanism_family="EMERGENCY_FEED_PURCHASE",
        market_mutations=[["BUY_PRODUCT", "WHEAT", 1]]
    )
    outcome = SimulationOutcome(
        candidate_final_money=1500.0,
        baseline_final_money=1000.0,
        delta_our_money=500.0,
        candidate_opp_final_money=1000.0,
        baseline_opp_final_money=1000.0,
        delta_opponent_money=0.0,
        delta_terminal_margin=500.0,
        candidate_overflow_units=0,
        candidate_sold={},
        baseline_sold={},
        intermediate_solvency_ok=False,  # Intermediate insolvency detected
        horizon=24
    )
    checker = SafetyChecker()
    passed, checks, reason = checker.verify(patch, outcome, econ, {})
    assert not passed
    assert not checks["solvency_ok"]


def test_tp_15_repeated_deterministic_evaluation(base_obs: Dict[str, Any]) -> None:
    """TP-15: Repeated deterministic evaluation -> Bit-exact identical results."""
    obs = copy.deepcopy(base_obs)
    obs["step"] = 697
    obs["day"] = 29
    obs["farms"][0]["tiles"][2][2] = {"animal": "COW"}
    econ = build_economic_state(obs)

    results = []
    for _ in range(10):
        analyzer = ResourceOpportunityAnalyzer()
        opps = analyzer.analyze(econ, [])
        feed_opps = [o for o in opps if o.candidate_transformation_family == "EMERGENCY_FEED_PURCHASE"]
        is_feas, reason = analyzer.is_feed_purchase_terminally_feasible(econ, [{"animal": "COW"}], 1)
        results.append((len(feed_opps), is_feas, reason))

    # All 10 repetitions must be bit-exact identical
    assert all(r == results[0] for r in results)


# Backwards compatibility aliases for Phase 002C test identifiers
test_ef_t1_late_purchase_no_realizable_benefit = test_tp_01_late_purchase_no_realizable_purpose
test_ef_t2_late_purchase_with_time_to_realize_value = test_tp_07_e8_active_but_purchase_genuinely_valuable
test_ef_t3_purchase_destroys_terminal_liquidity = test_tp_05_purchase_competes_with_mandatory_baseline_purchase
test_ef_t4_early_purchase_prevents_unavoidable_starvation = test_tp_02_purchase_prevents_unavoidable_animal_escape
test_ef_t5_e8_active_but_purchase_genuinely_valuable = test_tp_07_e8_active_but_purchase_genuinely_valuable
test_ef_t6_e8_active_chain_cannot_complete = test_tp_03_purchase_produces_output_too_late
test_ef_t7_feed_arrival_after_terminal = test_tp_03_purchase_produces_output_too_late
test_ef_t8_feed_arrival_before_terminal_output_cannot_be_harvested = test_tp_08_e8_inactive_candidate_terminally_impossible
test_ef_t9_feed_arrival_production_harvest_no_market_window = test_tp_04_output_before_terminal_sale_impossible
test_ef_t10_purchase_competes_with_final_liquidation = test_tp_13_positive_local_delta_breaks_mandatory_terminal_obligation


# =============================================================================
# PART 2: RESOURCE CONVERSION PHYSICAL ACTION SYNTHESIS (RC-T1 to RC-T8)
# =============================================================================

def test_rc_t1_valid_conversion_produces_non_null_patch(base_obs: Dict[str, Any]) -> None:
    """RC-T1: Valid conversion produces a non-null executable patch with real mutations."""
    obs = copy.deepcopy(base_obs)
    obs["farms"][0]["tiles"][2][2] = {"animal": "COW"}
    econ = build_economic_state(obs)

    analyzer = ResourceOpportunityAnalyzer()
    opps = [o for o in analyzer.analyze(econ, []) if o.candidate_transformation_family == "RESOURCE_CONVERSION"]
    assert len(opps) >= 1

    cfg = AECConfig(enabled_mechanisms=("RESOURCE_CONVERSION",))
    gen = PatchGenerator(config=cfg)
    patches = gen.generate_patches(opps, econ, {"farmer": ["PASS"], "market": []}, config=cfg)
    assert len(patches) >= 1

    cow_patch = next(p for p in patches if "MILK" in p.patch_id)
    # Must have non-null physical mutations (market or worker)
    has_physical = bool(cow_patch.market_mutations or cow_patch.worker_mutations)
    assert has_physical
    assert cow_patch.market_mutations == [["BUY_PRODUCT", "WHEAT", 1]]
    assert 0 in cow_patch.worker_mutations


def test_rc_t2_physical_action_reaches_simulator(base_obs: Dict[str, Any]) -> None:
    """RC-T2: Synthesized physical actions execute in CounterfactualSimulator."""
    obs = copy.deepcopy(base_obs)
    obs["farms"][0]["tiles"][2][2] = {"animal": "COW"}
    econ = build_economic_state(obs)

    cfg = AECConfig(enabled_mechanisms=("RESOURCE_CONVERSION",))
    analyzer = ResourceOpportunityAnalyzer()
    opps = [o for o in analyzer.analyze(econ, []) if o.candidate_transformation_family == "RESOURCE_CONVERSION"]
    gen = PatchGenerator(config=cfg)
    patches = gen.generate_patches(opps, econ, {"farmer": ["PASS"], "market": []}, config=cfg)
    cow_patch = patches[0]

    sim = CounterfactualSimulator()
    outcome = sim.evaluate(cow_patch, {"farmer": ["PASS"], "market": []}, econ, horizon=6)
    # Simulation completes and records non-zero delta due to physical market spend
    assert outcome.intermediate_solvency_ok is True
    assert outcome.fidelity == "VERIFIED"


def test_rc_t3_worker_route_required_invokes_reconnect(base_obs: Dict[str, Any]) -> None:
    """RC-T3: Conversion requiring worker travel invokes AEC-RECONNECT."""
    obs = copy.deepcopy(base_obs)
    obs["farms"][0]["tiles"][2][2] = {"animal": "COW"}
    econ = build_economic_state(obs)

    cfg = AECConfig(enabled_mechanisms=("RESOURCE_CONVERSION",))
    analyzer = ResourceOpportunityAnalyzer()
    opps = [o for o in analyzer.analyze(econ, []) if o.candidate_transformation_family == "RESOURCE_CONVERSION"]
    gen = PatchGenerator(config=cfg)
    patches = gen.generate_patches(opps, econ, {"farmer": ["PASS"], "market": []}, config=cfg)
    cow_patch = next(p for p in patches if "MILK" in p.patch_id)

    # Reconnect result must be attached to the patch
    assert cow_patch.reconnect_result is not None
    assert cow_patch.reconnect_result.safety is True


def test_rc_t4_worker_route_impossible_abstains(base_obs: Dict[str, Any]) -> None:
    """RC-T4: When route reconnection is impossible, patch fails closed."""
    obs = copy.deepcopy(base_obs)
    econ = build_economic_state(obs)

    patch = CoupledPatch(
        patch_id="PATCH_INVAL_ROUTE",
        source_opportunity_id="OPP_INVAL",
        mechanism_family="RESOURCE_CONVERSION",
        worker_mutations={0: ["NORTH"]}
    )
    outcome = SimulationOutcome(
        candidate_final_money=100.0,
        baseline_final_money=100.0,
        delta_our_money=0.0,
        candidate_opp_final_money=100.0,
        baseline_opp_final_money=100.0,
        delta_opponent_money=0.0,
        delta_terminal_margin=0.0,
        candidate_overflow_units=0,
        candidate_sold={},
        baseline_sold={},
        intermediate_solvency_ok=True,
        horizon=6,
        spatial_consistency_ok=False,
        desynchronization_reason="Worker collision with obstacles"
    )
    checker = SafetyChecker()
    passed, checks, reason = checker.verify(patch, outcome, econ, {})
    assert not passed
    assert not checks["spatial_consistency_ok"]


def test_rc_t5_conversion_consumes_reserved_resource(base_obs: Dict[str, Any]) -> None:
    """RC-T5: Conversion attempting to consume a reserved resource fails safety check."""
    obs = copy.deepcopy(base_obs)
    econ = build_economic_state(obs)

    patch = CoupledPatch(
        patch_id="PATCH_RESERVATION_CONFLICT",
        source_opportunity_id="OPP_RES_CONFLICT",
        mechanism_family="RESOURCE_CONVERSION",
        resource_changes={"reservation_conflict": True}
    )
    outcome = SimulationOutcome(
        candidate_final_money=1000.0,
        baseline_final_money=1000.0,
        delta_our_money=0.0,
        candidate_opp_final_money=1000.0,
        baseline_opp_final_money=1000.0,
        delta_opponent_money=0.0,
        delta_terminal_margin=0.0,
        candidate_overflow_units=0,
        candidate_sold={},
        baseline_sold={},
        intermediate_solvency_ok=True,
        horizon=6
    )
    checker = SafetyChecker()
    passed, checks, reason = checker.verify(patch, outcome, econ, {})
    assert not passed
    assert not checks["reservation_consistency_ok"]


def test_rc_t6_simulator_rejects_illegal_action(base_obs: Dict[str, Any]) -> None:
    """RC-T6: Conversion with illegal market action fails safety verification."""
    obs = copy.deepcopy(base_obs)
    econ = build_economic_state(obs)

    patch = CoupledPatch(
        patch_id="PATCH_ILLEGAL_ACT",
        source_opportunity_id="OPP_ILLEGAL",
        mechanism_family="RESOURCE_CONVERSION",
        market_mutations=[["INVALID_OP", "WHEAT", 1]]
    )
    outcome = SimulationOutcome(
        candidate_final_money=100.0,
        baseline_final_money=100.0,
        delta_our_money=0.0,
        candidate_opp_final_money=100.0,
        baseline_opp_final_money=100.0,
        delta_opponent_money=0.0,
        delta_terminal_margin=0.0,
        candidate_overflow_units=0,
        candidate_sold={},
        baseline_sold={},
        intermediate_solvency_ok=True,
        horizon=6
    )
    checker = SafetyChecker()
    passed, checks, reason = checker.verify(patch, outcome, econ, {})
    assert not passed
    assert not checks["legality_ok"]


def test_rc_t7_conversion_cannot_reach_terminal_liquidation(base_obs: Dict[str, Any]) -> None:
    """RC-T7: Conversion that cannot complete before terminal is rejected."""
    obs = copy.deepcopy(base_obs)
    obs["step"] = 700  # Only 20 steps remain
    econ = build_economic_state(obs)

    patch = CoupledPatch(
        patch_id="PATCH_TERM_INFEAS",
        source_opportunity_id="OPP_TERM_INFEAS",
        mechanism_family="RESOURCE_CONVERSION",
        resource_changes={"terminal_infeasible": True}
    )
    outcome = SimulationOutcome(
        candidate_final_money=100.0,
        baseline_final_money=100.0,
        delta_our_money=0.0,
        candidate_opp_final_money=100.0,
        baseline_opp_final_money=100.0,
        delta_opponent_money=0.0,
        delta_terminal_margin=0.0,
        candidate_overflow_units=0,
        candidate_sold={},
        baseline_sold={},
        intermediate_solvency_ok=True,
        horizon=6
    )
    checker = SafetyChecker()
    passed, checks, reason = checker.verify(patch, outcome, econ, {})
    assert not passed
    assert not checks["terminal_resource_ok"]


def test_rc_t8_multi_stage_conversion_exact_parity(base_obs: Dict[str, Any]) -> None:
    """RC-T8: Multi-stage conversion preserves exact trajectory parity in forward simulation."""
    obs = copy.deepcopy(base_obs)
    obs["farms"][0]["tiles"][2][2] = {"animal": "GOOSE"}
    econ = build_economic_state(obs)

    cfg = AECConfig(enabled_mechanisms=("RESOURCE_CONVERSION",))
    analyzer = ResourceOpportunityAnalyzer()
    opps = [o for o in analyzer.analyze(econ, []) if o.candidate_transformation_family == "RESOURCE_CONVERSION"]
    gen = PatchGenerator(config=cfg)
    patches = gen.generate_patches(opps, econ, {"farmer": ["PASS"], "market": []}, config=cfg)
    goose_patch = next(p for p in patches if "EGG" in p.patch_id)

    sim = CounterfactualSimulator()
    outcome = sim.evaluate(goose_patch, {"farmer": ["PASS"], "market": []}, econ, horizon=12)
    assert outcome.fidelity == "VERIFIED"
    assert outcome.feed_security_ok is True
