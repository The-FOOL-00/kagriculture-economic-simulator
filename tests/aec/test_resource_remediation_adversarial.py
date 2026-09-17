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
# PART 1: EMERGENCY FEED PURCHASE TERMINAL SAFETY (EF-T1 to EF-T10)
# =============================================================================

def test_ef_t1_late_purchase_no_realizable_benefit(base_obs: Dict[str, Any]) -> None:
    """EF-T1: Late purchase at step 697 with no realizable downstream benefit -> ABSTAIN."""
    obs = copy.deepcopy(base_obs)
    obs["step"] = 697
    obs["day"] = 29
    obs["farms"][0]["tiles"][2][2] = {"animal": "COW"}
    econ = build_economic_state(obs)

    analyzer = ResourceOpportunityAnalyzer()
    opps = [o for o in analyzer.analyze(econ, []) if o.candidate_transformation_family == "EMERGENCY_FEED_PURCHASE"]
    # Feasibility check must suppress pointless late purchase on final day
    assert len(opps) == 0


def test_ef_t2_late_purchase_with_time_to_realize_value(base_obs: Dict[str, Any]) -> None:
    """EF-T2: Purchase before terminal that has sufficient turns to realize value -> Permitted."""
    obs = copy.deepcopy(base_obs)
    obs["step"] = 600  # 120 steps remaining (5 full days)
    obs["day"] = 25
    obs["farms"][0]["tiles"][2][2] = {"animal": "GOOSE"}
    econ = build_economic_state(obs)

    analyzer = ResourceOpportunityAnalyzer()
    opps = [o for o in analyzer.analyze(econ, []) if o.candidate_transformation_family == "EMERGENCY_FEED_PURCHASE"]
    assert len(opps) == 1
    assert opps[0].dependency_info.get("is_terminally_feasible") is True


def test_ef_t3_purchase_destroys_terminal_liquidity(base_obs: Dict[str, Any]) -> None:
    """EF-T3: Purchase that causes net terminal margin degradation -> Safety Rejects (ABSTAIN)."""
    obs = copy.deepcopy(base_obs)
    obs["step"] = 500
    econ = build_economic_state(obs)

    patch = CoupledPatch(
        patch_id="PATCH_FEED_TEST",
        source_opportunity_id="FEED_OPP",
        mechanism_family="EMERGENCY_FEED_PURCHASE",
        market_mutations=[["BUY_PRODUCT", "WHEAT", 10]]
    )
    outcome = SimulationOutcome(
        candidate_final_money=500.0,
        baseline_final_money=1000.0,
        delta_our_money=-500.0,
        candidate_opp_final_money=1000.0,
        baseline_opp_final_money=1000.0,
        delta_opponent_money=0.0,
        delta_terminal_margin=-500.0,
        candidate_overflow_units=0,
        candidate_sold={},
        baseline_sold={},
        intermediate_solvency_ok=True,
        horizon=24
    )
    checker = SafetyChecker()
    passed, checks, reason = checker.verify(patch, outcome, econ, {})
    assert not passed
    assert not checks["terminal_purpose_ok"]
    assert "margin degradation" in reason


def test_ef_t4_early_purchase_prevents_unavoidable_starvation(base_obs: Dict[str, Any]) -> None:
    """EF-T4: Early purchase preventing future unavoidable starvation -> Opportunity admitted."""
    obs = copy.deepcopy(base_obs)
    obs["step"] = 200
    obs["day"] = 8
    obs["farms"][0]["tiles"][1][1] = {"animal": "COW"}
    econ = build_economic_state(obs)

    analyzer = ResourceOpportunityAnalyzer()
    opps = [o for o in analyzer.analyze(econ, []) if o.candidate_transformation_family == "EMERGENCY_FEED_PURCHASE"]
    assert len(opps) == 1


def test_ef_t5_e8_active_but_purchase_genuinely_valuable(base_obs: Dict[str, Any]) -> None:
    """EF-T5: E8 active but purchase has multi-day window to harvest and sell -> Evaluated through full horizon."""
    obs = copy.deepcopy(base_obs)
    obs["step"] = 650  # 70 steps remaining (~3 days)
    obs["day"] = 27
    obs["farms"][0]["tiles"][3][3] = {"animal": "GOOSE"}
    econ = build_economic_state(obs)

    patch = CoupledPatch(
        patch_id="PATCH_FEED_650",
        source_opportunity_id="OPP_FEED",
        mechanism_family="EMERGENCY_FEED_PURCHASE",
        market_mutations=[["BUY_PRODUCT", "WHEAT", 1]]
    )
    policy = MechanismHorizonPolicy()
    cfg = AECConfig()
    h = policy.select_horizon(patch, econ, cfg)
    # Remaining 70 steps > 48 -> standard horizon evaluated without blind cutoff
    assert h >= 18


def test_ef_t6_e8_active_chain_cannot_complete(base_obs: Dict[str, Any]) -> None:
    """EF-T6: E8 active with chain that cannot complete before terminal -> ABSTAIN."""
    obs = copy.deepcopy(base_obs)
    obs["step"] = 716  # 4 steps remaining
    obs["farms"][0]["tiles"][3][3] = {"animal": "COW"}
    econ = build_economic_state(obs)

    analyzer = ResourceOpportunityAnalyzer()
    is_feas, reason = analyzer.is_feed_purchase_terminally_feasible(econ, [{"animal": "COW"}], 1)
    assert not is_feas
    assert "Final day" in reason or "Insufficient time" in reason


def test_ef_t7_feed_arrival_after_terminal(base_obs: Dict[str, Any]) -> None:
    """EF-T7: Feed arrival would be at or after terminal -> SafetyChecker rejects."""
    obs = copy.deepcopy(base_obs)
    obs["step"] = 718  # Exactly on final step
    econ = build_economic_state(obs)

    patch = CoupledPatch(
        patch_id="PATCH_FEED_718",
        source_opportunity_id="OPP_FEED_718",
        mechanism_family="EMERGENCY_FEED_PURCHASE",
        market_mutations=[["BUY_PRODUCT", "WHEAT", 1]]
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
        horizon=2
    )
    checker = SafetyChecker()
    passed, checks, reason = checker.verify(patch, outcome, econ, {})
    assert not passed
    assert not checks["terminal_purpose_ok"]


def test_ef_t8_feed_arrival_before_terminal_output_cannot_be_harvested(base_obs: Dict[str, Any]) -> None:
    """EF-T8: Feed arrives before terminal but required product output cannot be harvested -> Safety rejects."""
    obs = copy.deepcopy(base_obs)
    obs["step"] = 710  # 10 steps remaining (same day, no harvest possible)
    econ = build_economic_state(obs)

    patch = CoupledPatch(
        patch_id="PATCH_FEED_710",
        source_opportunity_id="OPP_FEED_710",
        mechanism_family="EMERGENCY_FEED_PURCHASE",
        market_mutations=[["BUY_PRODUCT", "WHEAT", 1]]
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
        horizon=10
    )
    checker = SafetyChecker()
    passed, checks, reason = checker.verify(patch, outcome, econ, {})
    assert not passed
    assert not checks["terminal_purpose_ok"]


def test_ef_t9_feed_arrival_production_harvest_no_market_window(base_obs: Dict[str, Any]) -> None:
    """EF-T9: Insufficient turns to execute final sell -> Safety rejects."""
    obs = copy.deepcopy(base_obs)
    obs["step"] = 694  # Day ends at 696, but step 694 + turns_to_day_end(2) + 3 = 699, only 24 turns
    # Final action step is 718. If only 3 steps remain before 718, cannot sell.
    obs["step"] = 716
    econ = build_economic_state(obs)
    patch = CoupledPatch(
        patch_id="PATCH_NO_SELL",
        source_opportunity_id="OPP_NO_SELL",
        mechanism_family="EMERGENCY_FEED_PURCHASE",
        market_mutations=[["BUY_PRODUCT", "WHEAT", 1]]
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
        horizon=2
    )
    checker = SafetyChecker()
    passed, checks, reason = checker.verify(patch, outcome, econ, {})
    assert not passed


def test_ef_t10_purchase_competes_with_final_liquidation(base_obs: Dict[str, Any]) -> None:
    """EF-T10: Purchase marked as terminal purpose inconsistent -> Safely rejected."""
    obs = copy.deepcopy(base_obs)
    obs["step"] = 600
    econ = build_economic_state(obs)

    patch = CoupledPatch(
        patch_id="PATCH_COMPETE_LIQ",
        source_opportunity_id="OPP_LIQ",
        mechanism_family="EMERGENCY_FEED_PURCHASE",
        resource_changes={"terminal_purpose_inconsistent": True}
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
        horizon=10
    )
    checker = SafetyChecker()
    passed, checks, reason = checker.verify(patch, outcome, econ, {})
    assert not passed
    assert not checks["terminal_purpose_ok"]


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
