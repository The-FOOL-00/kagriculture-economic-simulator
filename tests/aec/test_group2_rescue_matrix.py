# SPDX-License-Identifier: MIT
"""Phase 012 Group 2 Mechanism Rescue Micro-Validation Matrix (§10, §15, §19, §26, §31).

Adversarial synthetic states and activation/control patterns for:
1. TOWN_CYCLE (12 activation + negative-control scenarios)
2. EMERGENCY_RECOVERY (12 failure / false-alarm scenarios)
3. OPPONENT_PREEMPT_SELL (12 pressure / uncertainty scenarios)
4. RESOURCE_CONVERSION (12 conversion / alternative-use scenarios)
"""

from __future__ import annotations

import copy
import math
import pytest
from typing import Any, Dict, List, Tuple

from aec.config import BOARD_SIZE, FINAL_STEP, PRODUCTS, SHED_CAPACITY, TURNS_PER_DAY
from aec.ir.economic_state import build_economic_state
from aec.opportunities.town_cycle import (
    TownCycleSignalDetector,
    compute_required_liquidity,
)
from aec.opportunities.emergency import (
    EmergencyRecoveryDetector,
    EmergencyThreatType,
    IrreversibilityClass,
)
from aec.opportunities.preemption import (
    OpponentPreemptionDetector,
    OpponentPreemptionOpportunity,
    PreemptionFamily,
)
from aec.opportunities.resource import (
    ComparativeValuation,
    ConversionFamily,
    ResourceOpportunityAnalyzer,
    compute_structural_liquidity_requirement,
    evaluate_comparative_margin,
)
from aec.counterfactual.opponent_pressure import OpponentPressureState
from aec.patches.generator import PatchGenerator


@pytest.fixture
def group2_base_obs(normal_opening_obs: Dict[str, Any]) -> Dict[str, Any]:
    """Base observation with 1 Farmer at [4, 4] and 1 Hand at [2, 2]."""
    obs = copy.deepcopy(normal_opening_obs)
    obs["step"] = 50  # 50 % 4 == 2 -> steps_to_town_tick == 2
    obs["day"] = 2
    obs["hour"] = 2
    obs["farms"][0]["farmer"] = [4, 4]
    obs["farms"][0]["hands"] = [[2, 2]]
    obs["farms"][0]["hires_today"] = 1
    obs["farms"][0]["money"] = 1000.0
    obs["farms"][0]["tiles"] = [[None]*10 for _ in range(10)]
    obs["private"]["shed"] = {"MELON": 10, "STRAWBERRY": 10, "WHEAT": 20}
    obs["private"]["inventories"] = [{}, {}]
    obs["town"]["unlocked_shops"] = ["BRUNCH_SPOT", "FARMERS_MARKET"]
    return obs


# =============================================================================
# 1. TOWN_CYCLE / ECONOMIC CYCLE TIMING (12 ADVERSARIAL SCENARIOS - §10, §31)
# =============================================================================

def test_tc_01_abundant_liquidity_allows_delay(group2_base_obs: Dict[str, Any]) -> None:
    """TC-01: Abundant liquidity allows DELAY_SALE when absorption tick is imminent."""
    obs = copy.deepcopy(group2_base_obs)
    obs["farms"][0]["money"] = 2000.0
    econ = build_economic_state(obs)
    detector = TownCycleSignalDetector()
    baseline_action = {"farmer": ["PASS"], "hands": [["PASS"]], "market": [["SELL", "STRAWBERRY", 5]]}

    opps = detector.detect(econ, baseline_action)
    assert len(opps) >= 1
    delay_opp = next((o for o in opps if o.dependency_info.get("timing_action") == "DELAY_SALE"), None)
    assert delay_opp is not None
    assert delay_opp.dependency_info["item"] == "STRAWBERRY"
    assert delay_opp.dependency_info["liquidity_surplus"] > 0


def test_tc_02_tight_liquidity_triggers_partial_sale(group2_base_obs: Dict[str, Any]) -> None:
    """TC-02: Tight liquidity ($50 cash, $100 wages due) triggers PARTIAL_SALE."""
    obs = copy.deepcopy(group2_base_obs)
    obs["farms"][0]["money"] = 50.0  # Deficit of $50 before $100 nightly wages
    obs["step"] = 70                  # Hour 22 (steps_to_night = 1), 70 % 4 == 2 -> steps_to_tick == 2
    econ = build_economic_state(obs)
    detector = TownCycleSignalDetector()
    baseline_action = {"farmer": ["PASS"], "hands": [["PASS"]], "market": [["SELL", "STRAWBERRY", 5]]}

    opps = detector.detect(econ, baseline_action)
    assert len(opps) >= 1
    partial_opp = next((o for o in opps if o.dependency_info.get("timing_action") == "PARTIAL_SALE"), None)
    assert partial_opp is not None
    assert partial_opp.dependency_info["qty_sell"] >= 1
    assert partial_opp.dependency_info["qty_hold"] > 0


def test_tc_03_mandatory_future_purchase_preserves_liquidity(group2_base_obs: Dict[str, Any]) -> None:
    """TC-03: Mandatory seed purchase at day boundary is priced into required liquidity."""
    obs = copy.deepcopy(group2_base_obs)
    obs["step"] = 71  # 1 turn before day boundary (step 72)
    econ = build_economic_state(obs)
    req_liq = compute_required_liquidity(econ, horizon_steps=6)
    # Must include seed allocation ($150) plus any wage obligations
    assert req_liq >= 150.0


def test_tc_04_multiple_mandatory_purchases_wages_and_feed(group2_base_obs: Dict[str, Any]) -> None:
    """TC-04: Multiple obligations (wages + starving animal feed) compound additively."""
    obs = copy.deepcopy(group2_base_obs)
    obs["step"] = 70  # Hour 22
    obs["farms"][0]["hands"] = [[1, 1], [2, 2]]  # 2 hands -> $200 wages
    obs["private"]["shed"] = {"WHEAT": 0}         # 0 wheat
    obs["farms"][0]["tiles"][0][0] = {
        "kind": "PASTURE", "subtype": "COW", "turns_to_starve": 2
    }
    econ = build_economic_state(obs)
    req_liq = compute_required_liquidity(econ, horizon_steps=4)
    # 2 hands * 100 = 200 wages + 1 cow * wheat price ($25) = 225
    assert req_liq >= 225.0


def test_tc_05_sale_before_purchase_ordering(group2_base_obs: Dict[str, Any]) -> None:
    """TC-05: Patch generator preserves valid order sequence when modifying basket."""
    obs = copy.deepcopy(group2_base_obs)
    econ = build_economic_state(obs)
    detector = TownCycleSignalDetector()
    baseline_action = {
        "farmer": ["PASS"],
        "hands": [["PASS"]],
        "market": [["SELL", "STRAWBERRY", 5], ["BUY_SEED", "CARROT", 2]]
    }
    opps = detector.detect(econ, baseline_action)
    delay_opp = next((o for o in opps if o.dependency_info.get("timing_action") == "DELAY_SALE"), None)
    assert delay_opp is not None

    gen = PatchGenerator(enabled_mechanisms={"TOWN_CYCLE"})
    patches = gen.generate_patches([delay_opp], econ, baseline_action)
    assert len(patches) == 1
    # Delayed strawberry sell should be omitted, leaving BUY_SEED intact
    assert patches[0].market_mutations == [["BUY_SEED", "CARROT", 2]]


def test_tc_06_purchase_before_sale_ordering(group2_base_obs: Dict[str, Any]) -> None:
    """TC-06: Existing BUY orders are preserved when ADVANCE_SALE inserts orders."""
    obs = copy.deepcopy(group2_base_obs)
    obs["step"] = 48  # 48 % 4 == 0 -> steps_to_town_tick == 4 (fresh demand tick)
    econ = build_economic_state(obs)
    detector = TownCycleSignalDetector()
    baseline_action = {
        "farmer": ["PASS"],
        "hands": [["PASS"]],
        "market": [["BUY_SEED", "STRAWBERRY", 1]]
    }
    opps = detector.detect(econ, baseline_action)
    adv_opp = next((o for o in opps if o.dependency_info.get("timing_action") == "ADVANCE_SALE"), None)
    assert adv_opp is not None

    gen = PatchGenerator(enabled_mechanisms={"TOWN_CYCLE"})
    patches = gen.generate_patches([adv_opp], econ, baseline_action)
    assert len(patches) == 1
    mutations = patches[0].market_mutations
    # Advance sale order inserted, previous BUY_SEED retained
    assert any(o[0] == "SELL" and o[1] == adv_opp.dependency_info["item"] for o in mutations)
    assert any(o[0] == "BUY_SEED" and o[1] == "STRAWBERRY" for o in mutations)


def test_tc_07_valuable_delayed_sale_bump(group2_base_obs: Dict[str, Any]) -> None:
    """TC-07: High town absorption produces substantial estimated relevance."""
    obs = copy.deepcopy(group2_base_obs)
    obs["step"] = 51  # 51 % 4 == 3 -> steps_to_town_tick == 1
    econ = build_economic_state(obs)
    detector = TownCycleSignalDetector()
    baseline_action = {"farmer": ["PASS"], "hands": [["PASS"]], "market": [["SELL", "STRAWBERRY", 5]]}

    opps = detector.detect(econ, baseline_action)
    delay_opp = next((o for o in opps if o.dependency_info.get("timing_action") == "DELAY_SALE"), None)
    assert delay_opp is not None
    assert delay_opp.estimated_economic_relevance > 0.0


def test_tc_08_terminal_sale_pressure_abstains(group2_base_obs: Dict[str, Any]) -> None:
    """TC-08: In terminal window (step >= 705), DELAY_SALE is strictly barred."""
    obs = copy.deepcopy(group2_base_obs)
    obs["step"] = 708
    econ = build_economic_state(obs)
    detector = TownCycleSignalDetector()
    baseline_action = {"farmer": ["PASS"], "hands": [["PASS"]], "market": [["SELL", "MELON", 5]]}

    opps = detector.detect(econ, baseline_action)
    assert len(opps) == 0  # Terminal runway constraint triggers complete abstention


def test_tc_09_opponent_supply_pressure_suppresses_delay(group2_base_obs: Dict[str, Any]) -> None:
    """TC-09: Heavy rival supply forecast overrides DELAY_SALE to avoid holding into dump."""
    obs = copy.deepcopy(group2_base_obs)
    # Opponent holds 6 melon ready to dump
    obs["opponent"] = {"supply_forecast": {"MELON": 6}}
    econ = build_economic_state(obs)
    detector = TownCycleSignalDetector()
    baseline_action = {"farmer": ["PASS"], "hands": [["PASS"]], "market": [["SELL", "MELON", 5]]}

    opps = detector.detect(econ, baseline_action)
    melon_delay = [o for o in opps if o.dependency_info.get("timing_action") == "DELAY_SALE" and o.dependency_info.get("item") == "MELON"]
    assert len(melon_delay) == 0


def test_tc_10_no_economic_timing_opportunity_abstains(group2_base_obs: Dict[str, Any]) -> None:
    """TC-10: When absorption is zero and tick is distant, detector abstains cleanly."""
    obs = copy.deepcopy(group2_base_obs)
    obs["market"]["expected_absorption"] = {}
    obs["market"]["steps_to_town_tick"] = 10
    econ = build_economic_state(obs)
    detector = TownCycleSignalDetector()
    baseline_action = {"farmer": ["PASS"], "hands": [["PASS"]], "market": [["SELL", "MELON", 5]]}

    opps = detector.detect(econ, baseline_action)
    delay_opps = [o for o in opps if o.dependency_info.get("timing_action") == "DELAY_SALE"]
    assert len(delay_opps) == 0


def test_tc_11_shed_headroom_critical_suppresses_delay(group2_base_obs: Dict[str, Any]) -> None:
    """TC-11: When shed stock > 80, DELAY_SALE is suppressed to prevent shed gridlock."""
    obs = copy.deepcopy(group2_base_obs)
    # Shed holding 85 units total
    obs["private"]["shed"] = {"WHEAT": 50, "MELON": 35}
    econ = build_economic_state(obs)
    detector = TownCycleSignalDetector()
    baseline_action = {"farmer": ["PASS"], "hands": [["PASS"]], "market": [["SELL", "MELON", 5]]}

    opps = detector.detect(econ, baseline_action)
    delay_opps = [o for o in opps if o.dependency_info.get("timing_action") == "DELAY_SALE"]
    assert len(delay_opps) == 0  # Headroom invariant protects shed drop-off capacity


def test_tc_12_advance_sale_bounds_parcel_to_ten(group2_base_obs: Dict[str, Any]) -> None:
    """TC-12: Advance sale bounds parcel to at most 10 units to protect market elasticity."""
    obs = copy.deepcopy(group2_base_obs)
    obs["step"] = 48                              # Fresh demand tick (48 % 4 == 0)
    econ = build_economic_state(obs)
    detector = TownCycleSignalDetector()
    baseline_action = {"farmer": ["PASS"], "hands": [["PASS"]], "market": []}

    opps = detector.detect(econ, baseline_action)
    adv_opp = next((o for o in opps if o.dependency_info.get("timing_action") == "ADVANCE_SALE" and o.dependency_info.get("item") == "STRAWBERRY"), None)
    assert adv_opp is not None
    assert adv_opp.dependency_info["qty"] <= 10

    gen = PatchGenerator(enabled_mechanisms={"TOWN_CYCLE"})
    patches = gen.generate_patches([adv_opp], econ, baseline_action)
    assert len(patches) == 1
    sell_order = next(o for o in patches[0].market_mutations if o[0] == "SELL")
    assert sell_order[2] <= 10


# =============================================================================
# 2. EMERGENCY_RECOVERY / DAMAGE AVOIDANCE (12 ADVERSARIAL SCENARIOS - §15, §31)
# =============================================================================

def test_emr_01_one_turn_before_starvation(group2_base_obs: Dict[str, Any]) -> None:
    """EMR-01: Cow with 1 turn to starve triggers CURRENT_HARD_FAILURE."""
    obs = copy.deepcopy(group2_base_obs)
    obs["farms"][0]["tiles"][0][0] = {
        "kind": "PASTURE", "subtype": "COW", "turns_to_starve": 1
    }
    econ = build_economic_state(obs)
    detector = EmergencyRecoveryDetector()
    opps = detector.detect(econ)
    assert len(opps) == 1
    assert opps[0].threat_type == EmergencyThreatType.LIVESTOCK_STARVATION
    assert opps[0].irreversibility_class == IrreversibilityClass.CURRENT_HARD_FAILURE


def test_emr_02_two_turns_before_starvation(group2_base_obs: Dict[str, Any]) -> None:
    """EMR-02: Cow with 2 turns to starve triggers EMERGING_IRREVERSIBLE_LOSS."""
    obs = copy.deepcopy(group2_base_obs)
    obs["farms"][0]["tiles"][0][0] = {
        "kind": "PASTURE", "subtype": "COW", "turns_to_starve": 2
    }
    econ = build_economic_state(obs)
    detector = EmergencyRecoveryDetector()
    opps = detector.detect(econ)
    assert len(opps) == 1
    assert opps[0].threat_type == EmergencyThreatType.LIVESTOCK_STARVATION
    assert opps[0].irreversibility_class == IrreversibilityClass.EMERGING_IRREVERSIBLE_LOSS


def test_emr_03_four_turns_before_starvation_false_alarm(group2_base_obs: Dict[str, Any]) -> None:
    """EMR-03: Cow with 10 turns to starve is recoverable; detector abstains cleanly."""
    obs = copy.deepcopy(group2_base_obs)
    obs["farms"][0]["tiles"][0][0] = {
        "kind": "PASTURE", "subtype": "COW", "turns_to_starve": 10
    }
    econ = build_economic_state(obs)
    detector = EmergencyRecoveryDetector()
    opps = detector.detect(econ)
    assert len(opps) == 0  # Reversible / recoverable -> no panic


def test_emr_04_worker_already_carrying_feed_false_alarm(group2_base_obs: Dict[str, Any]) -> None:
    """EMR-04: If a worker carries feed, baseline is actively recovering -> abstains."""
    obs = copy.deepcopy(group2_base_obs)
    obs["farms"][0]["tiles"][0][0] = {
        "kind": "PASTURE", "subtype": "COW", "turns_to_starve": 1
    }
    # Hand worker at [2, 2] is already carrying 1 wheat
    obs["private"]["inventories"][1] = {"WHEAT": 1}
    econ = build_economic_state(obs)
    detector = EmergencyRecoveryDetector()
    opps = detector.detect(econ)
    assert len(opps) == 0  # Feed is in transit -> false alarm rejected


def test_emr_05_wage_deficit_at_hour_23_triggers(group2_base_obs: Dict[str, Any]) -> None:
    """EMR-05: Hour 23 wage deficit with no pending sales triggers CURRENT_HARD_FAILURE."""
    obs = copy.deepcopy(group2_base_obs)
    obs["step"] = 71  # Day 2, Hour 23
    obs["farms"][0]["money"] = 20.0  # $20 cash vs $100 wages
    obs["private"]["shed"] = {"WHEAT": 10, "MELON": 5}
    econ = build_economic_state(obs)
    detector = EmergencyRecoveryDetector()
    opps = detector.detect(econ, baseline_action={"farmer": ["PASS"], "hands": [["PASS"]], "market": []})
    assert len(opps) == 1
    assert opps[0].threat_type == EmergencyThreatType.CRITICAL_CASH_INSOLVENCY
    assert opps[0].irreversibility_class == IrreversibilityClass.CURRENT_HARD_FAILURE
    assert opps[0].dependency_info["deficit"] == 80.0


def test_emr_06_wage_deficit_with_pending_sales_false_alarm(group2_base_obs: Dict[str, Any]) -> None:
    """EMR-06: Hour 22 cash is $20, but baseline sells 2 strawberry ($240) -> abstains."""
    obs = copy.deepcopy(group2_base_obs)
    obs["step"] = 70  # Day 2, Hour 22
    obs["farms"][0]["money"] = 20.0
    econ = build_economic_state(obs)
    detector = EmergencyRecoveryDetector()
    baseline_action = {
        "farmer": ["PASS"],
        "hands": [["PASS"]],
        "market": [["SELL", "STRAWBERRY", 2]]  # 2 * 120 = 240 covers 100 wages
    }
    opps = detector.detect(econ, baseline_action)
    assert len(opps) == 0  # Recoverable via baseline orders -> false alarm rejected


def test_emr_07_wage_deficit_at_hour_10_false_alarm(group2_base_obs: Dict[str, Any]) -> None:
    """EMR-07: Cash is $20 at Hour 10 (13 turns to night); normal farming will recover -> abstains."""
    obs = copy.deepcopy(group2_base_obs)
    obs["step"] = 58  # Hour 10 (steps_to_night = 13)
    obs["farms"][0]["money"] = 20.0
    econ = build_economic_state(obs)
    detector = EmergencyRecoveryDetector()
    opps = detector.detect(econ, baseline_action={"farmer": ["PASS"], "hands": [["PASS"]], "market": []})
    assert len(opps) == 0  # Reversible daylight fluctuation -> no panic


def test_emr_08_minimal_liquidation_sells_lowest_margin(group2_base_obs: Dict[str, Any]) -> None:
    """EMR-08: Wage rescue liquidates WHEAT before MELON to preserve high-margin stock."""
    obs = copy.deepcopy(group2_base_obs)
    obs["step"] = 71  # Hour 23
    obs["farms"][0]["money"] = 50.0  # $50 deficit
    obs["private"]["shed"] = {"MELON": 5, "WHEAT": 10}
    econ = build_economic_state(obs)
    detector = EmergencyRecoveryDetector()
    opps = detector.detect(econ, baseline_action={"farmer": ["PASS"], "hands": [["PASS"]], "market": []})
    assert len(opps) == 1
    assert opps[0].dependency_info["chosen_item"] == "WHEAT"  # Lowest margin prioritized


def test_emr_09_minimal_liquidation_bounds_quantity_to_deficit(group2_base_obs: Dict[str, Any]) -> None:
    """EMR-09: Deficit is $50, wheat is $25; sells exactly 2 wheat, preserving remaining 18."""
    obs = copy.deepcopy(group2_base_obs)
    obs["step"] = 71
    obs["farms"][0]["money"] = 50.0  # $50 deficit
    obs["private"]["shed"] = {"WHEAT": 20}
    econ = build_economic_state(obs)
    detector = EmergencyRecoveryDetector()
    opps = detector.detect(econ, baseline_action={"farmer": ["PASS"], "hands": [["PASS"]], "market": []})
    assert len(opps) == 1
    opp = opps[0]
    assert opp.dependency_info["qty_to_sell"] == 2

    gen = PatchGenerator(enabled_mechanisms={"EMERGENCY_RECOVERY"})
    patches = gen.generate_patches([opp], econ, baseline_action={"farmer": ["PASS"], "hands": [["PASS"]], "market": []})
    assert len(patches) == 1
    # Check that market order is exactly SELL WHEAT 2, NOT 20
    assert patches[0].market_mutations == [["SELL", "WHEAT", 2]]


def test_emr_10_terminal_failure_to_liquidate_triggers(group2_base_obs: Dict[str, Any]) -> None:
    """EMR-10: Step 717 with shed stock and no sell orders triggers terminal rescue."""
    obs = copy.deepcopy(group2_base_obs)
    obs["step"] = 717
    obs["private"]["shed"] = {"MELON": 3, "STRAWBERRY": 2}
    econ = build_economic_state(obs)
    detector = EmergencyRecoveryDetector()
    opps = detector.detect(econ, baseline_action={"farmer": ["PASS"], "hands": [["PASS"]], "market": []})
    assert len(opps) == 1
    assert opps[0].threat_type == EmergencyThreatType.TERMINAL_FAILURE_TO_LIQUIDATE


def test_emr_11_terminal_failure_when_baseline_already_selling_abstains(group2_base_obs: Dict[str, Any]) -> None:
    """EMR-11: Step 717 where baseline already has a sell order abstains cleanly."""
    obs = copy.deepcopy(group2_base_obs)
    obs["step"] = 717
    obs["private"]["shed"] = {"MELON": 3}
    econ = build_economic_state(obs)
    detector = EmergencyRecoveryDetector()
    baseline_action = {"farmer": ["PASS"], "hands": [["PASS"]], "market": [["SELL", "MELON", 3]]}
    opps = detector.detect(econ, baseline_action)
    assert len(opps) == 0  # Already liquidating -> no duplicate intervention


def test_emr_12_irreversibility_classification_integrity() -> None:
    """EMR-12: IrreversibilityClass enum values match governance specification."""
    classes = [c.value for c in IrreversibilityClass]
    assert "REVERSIBLE_DEGRADATION" in classes
    assert "RECOVERABLE_DEGRADATION" in classes
    assert "EMERGING_IRREVERSIBLE_LOSS" in classes
    assert "CURRENT_HARD_FAILURE" in classes


# =============================================================================
# 3. OPPONENT_PREEMPT_SELL / ROBUST UNCERTAINTY (12 ADVERSARIAL SCENARIOS - §19, §31)
# =============================================================================

def test_opp_01_high_sale_pressure_triggers_defensive_preemption(group2_base_obs: Dict[str, Any]) -> None:
    """OPP-01: Rival sale pressure 0.6 on melon with high price triggers defensive preemption."""
    obs = copy.deepcopy(group2_base_obs)
    econ = build_economic_state(obs)
    pressure = OpponentPressureState(sale_pressure={"MELON": 0.60})
    detector = OpponentPreemptionDetector()
    opps = detector.detect(econ, pressure)
    assert len(opps) >= 1
    melon_opp = next((o for o in opps if o.target_product == "MELON"), None)
    assert melon_opp is not None
    assert melon_opp.preemption_family == PreemptionFamily.DEFENSIVE_INVENTORY
    assert melon_opp.observed_pressure == 0.60


def test_opp_02_bounded_uncertainty_worst_case_evaluation(group2_base_obs: Dict[str, Any]) -> None:
    """OPP-02: Preemption records positive worst-case delta under uncertainty."""
    obs = copy.deepcopy(group2_base_obs)
    econ = build_economic_state(obs)
    pressure = OpponentPressureState(sale_pressure={"MELON": 0.55})
    detector = OpponentPreemptionDetector()
    opps = detector.detect(econ, pressure)
    melon_opp = next((o for o in opps if o.target_product == "MELON"), None)
    assert melon_opp is not None
    assert melon_opp.worst_case_delta > 0.0


def test_opp_03_rival_dump_scenario(group2_base_obs: Dict[str, Any]) -> None:
    """OPP-03: Under rival dump scenario, preemption avoids projected price decay."""
    obs = copy.deepcopy(group2_base_obs)
    econ = build_economic_state(obs)
    pressure = OpponentPressureState(sale_pressure={"STRAWBERRY": 0.50})
    detector = OpponentPreemptionDetector()
    opps = detector.detect(econ, pressure)
    berry_opp = next((o for o in opps if o.target_product == "STRAWBERRY"), None)
    assert berry_opp is not None
    assert berry_opp.projected_rival_depression_impact > 0.0


def test_opp_04_rival_hold_scenario_self_value_dominance(group2_base_obs: Dict[str, Any]) -> None:
    """OPP-04: Selling at high price ($250 melon) guarantees non-negative utility if rival holds."""
    obs = copy.deepcopy(group2_base_obs)
    obs["market"]["prices"]["MELON"] = 260  # Above base price
    econ = build_economic_state(obs)
    pressure = OpponentPressureState(sale_pressure={"MELON": 0.50})
    detector = OpponentPreemptionDetector()
    opps = detector.detect(econ, pressure)
    melon_opp = next((o for o in opps if o.target_product == "MELON"), None)
    assert melon_opp is not None
    assert melon_opp.expected_our_revenue >= 10 * 250


def test_opp_05_depressed_market_prevents_preemptive_dump(group2_base_obs: Dict[str, Any]) -> None:
    """OPP-05: If current price is severely depressed ($150 for melon vs base $250), abstains."""
    obs = copy.deepcopy(group2_base_obs)
    obs["market"]["prices"]["MELON"] = 150  # 60% of base price
    econ = build_economic_state(obs)
    pressure = OpponentPressureState(sale_pressure={"MELON": 0.80})
    detector = OpponentPreemptionDetector()
    opps = detector.detect(econ, pressure)
    # Fire sale into already-collapsed market is rejected by self-value dominance
    melon_opps = [o for o in opps if o.target_product == "MELON"]
    assert len(melon_opps) == 0


def test_opp_06_unverified_rumors_abstains(group2_base_obs: Dict[str, Any]) -> None:
    """OPP-06: Low pressure (0.1) without observable rival stock produces 0 opportunities."""
    obs = copy.deepcopy(group2_base_obs)
    econ = build_economic_state(obs)
    pressure = OpponentPressureState(sale_pressure={"MELON": 0.10, "STRAWBERRY": 0.10})
    detector = OpponentPreemptionDetector()
    opps = detector.detect(econ, pressure)
    assert len(opps) == 0


def test_opp_07_purchase_preemption_acquires_scarce_seeds(group2_base_obs: Dict[str, Any]) -> None:
    """OPP-07: Rival buy pressure 0.7 on melon seed triggers purchase preemption."""
    obs = copy.deepcopy(group2_base_obs)
    obs["farms"][0]["money"] = 600.0
    econ = build_economic_state(obs)
    pressure = OpponentPressureState(buy_pressure={"MELON": 0.70})
    detector = OpponentPreemptionDetector()
    opps = detector.detect(econ, pressure)
    buy_opp = next((o for o in opps if o.preemption_family == PreemptionFamily.PURCHASE_PREEMPTION), None)
    assert buy_opp is not None
    assert buy_opp.target_product == "MELON"
    assert buy_opp.quantity == 2


def test_opp_08_purchase_preemption_abstains_if_poor(group2_base_obs: Dict[str, Any]) -> None:
    """OPP-08: If cash is low ($50), purchase preemption is suppressed to protect solvency."""
    obs = copy.deepcopy(group2_base_obs)
    obs["farms"][0]["money"] = 50.0  # Cannot afford melon seeds
    econ = build_economic_state(obs)
    pressure = OpponentPressureState(buy_pressure={"MELON": 0.80})
    detector = OpponentPreemptionDetector()
    opps = detector.detect(econ, pressure)
    buy_opps = [o for o in opps if o.preemption_family == PreemptionFamily.PURCHASE_PREEMPTION]
    assert len(buy_opps) == 0


def test_opp_09_defensive_sell_bounds_parcel_to_ten(group2_base_obs: Dict[str, Any]) -> None:
    """OPP-09: Shed has 30 strawberry; preemption bounds parcel to max 10 to protect elasticity."""
    obs = copy.deepcopy(group2_base_obs)
    obs["private"]["shed"]["STRAWBERRY"] = 30
    econ = build_economic_state(obs)
    pressure = OpponentPressureState(sale_pressure={"STRAWBERRY": 0.60})
    detector = OpponentPreemptionDetector()
    opps = detector.detect(econ, pressure)
    berry_opp = next((o for o in opps if o.target_product == "STRAWBERRY"), None)
    assert berry_opp is not None
    assert berry_opp.quantity == 10  # Capped at 10


def test_opp_10_patch_preserves_existing_baseline_orders(group2_base_obs: Dict[str, Any]) -> None:
    """OPP-10: Patch generator inserts preemption order without overwriting existing BUY orders."""
    obs = copy.deepcopy(group2_base_obs)
    econ = build_economic_state(obs)
    pressure = OpponentPressureState(sale_pressure={"MELON": 0.60})
    detector = OpponentPreemptionDetector()
    opps = detector.detect(econ, pressure)
    melon_opp = next((o for o in opps if o.target_product == "MELON"), None)
    assert melon_opp is not None

    baseline_action = {
        "farmer": ["PASS"],
        "hands": [["PASS"]],
        "market": [["BUY_SEED", "CARROT", 2]]
    }
    gen = PatchGenerator(enabled_mechanisms={"OPPONENT_PREEMPT_SELL"})
    patches = gen.generate_patches([melon_opp], econ, baseline_action)
    assert len(patches) == 1
    mutations = patches[0].market_mutations
    assert any(o[0] == "SELL" and o[1] == "MELON" for o in mutations)
    assert any(o[0] == "BUY_SEED" and o[1] == "CARROT" for o in mutations)


def test_opp_11_zero_shed_inventory_abstains(group2_base_obs: Dict[str, Any]) -> None:
    """OPP-11: If shed has 0 units of the threatened commodity, defensive sell abstains."""
    obs = copy.deepcopy(group2_base_obs)
    obs["private"]["shed"]["MELON"] = 0  # No melon in shed
    econ = build_economic_state(obs)
    pressure = OpponentPressureState(sale_pressure={"MELON": 0.90})
    detector = OpponentPreemptionDetector()
    opps = detector.detect(econ, pressure)
    melon_opps = [o for o in opps if o.target_product == "MELON" and o.preemption_family == PreemptionFamily.DEFENSIVE_INVENTORY]
    assert len(melon_opps) == 0


def test_opp_12_preemption_family_enum_integrity() -> None:
    """OPP-12: PreemptionFamily enum contains all 4 expected families."""
    fams = [f.value for f in PreemptionFamily]
    assert "DEFENSIVE_INVENTORY" in fams
    assert "PURCHASE_PREEMPTION" in fams
    assert "CAPACITY_PREEMPTION" in fams
    assert "TIMING_PREEMPTION" in fams


# =============================================================================
# 4. RESOURCE CONVERSION (12 conversion / alternative-use scenarios §20-§26)
# =============================================================================

def test_rc_01_low_margin_conversion_rejected_after_labor_cost(group2_base_obs: Dict[str, Any]) -> None:
    """RC-01: Gross output positive, but net margin <= 0 after labor opportunity cost -> PRUNED."""
    obs = copy.deepcopy(group2_base_obs)
    econ = build_economic_state(obs)
    # Gross = 30, keep source = 20, cash cost = 5, labor steps = 4 (cost 12) -> net = 30 - 20 - 5 - 12 = -7
    comp = evaluate_comparative_margin(
        source_commodity="WHEAT",
        target_commodity="CARROT",
        source_qty=1,
        target_qty=1,
        upfront_cash_cost=5.0,
        duration_steps=48,
        econ_state=econ,
        family=ConversionFamily.PRODUCT_CONVERSION,
        worker_labor_steps=4,
    )
    assert not comp.is_economically_superior
    assert "Negative incremental net margin" in comp.rejection_reason


def test_rc_02_keep_source_dominates_when_target_value_low(group2_base_obs: Dict[str, Any]) -> None:
    """RC-02: Keeping source resource has higher value than converting -> PRUNED."""
    obs = copy.deepcopy(group2_base_obs)
    obs["market"]["prices"]["WHEAT"] = 50  # High wheat price
    obs["market"]["prices"]["MILK"] = 60   # Low milk price
    econ = build_economic_state(obs)
    comp = evaluate_comparative_margin(
        source_commodity="WHEAT",
        target_commodity="MILK",
        source_qty=1,
        target_qty=1,
        upfront_cash_cost=10.0,
        duration_steps=48,
        econ_state=econ,
        family=ConversionFamily.FEED_CONVERSION,
        worker_labor_steps=2,
    )
    # convert net = 60 - 50 - 10 - 6 = -6
    assert not comp.is_economically_superior
    assert "Negative incremental net margin" in comp.rejection_reason


def test_rc_03_dominated_by_direct_target_purchase(group2_base_obs: Dict[str, Any]) -> None:
    """RC-03: Direct target market purchase is cheaper than converting -> PRUNED."""
    obs = copy.deepcopy(group2_base_obs)
    obs["market"]["prices"]["CARROT"] = 35  # Market price gives positive gross
    obs["market"]["prices"]["WHEAT"] = 20
    econ = build_economic_state(obs)
    # Target qty 2 gives gross 70. Convert costs: cash 10 + keep wheat 20 + labor 6 = 36 (net +34)
    # But direct purchase from alternative market is only 25 -> buying directly dominates converting
    comp = evaluate_comparative_margin(
        source_commodity="WHEAT",
        target_commodity="CARROT",
        source_qty=1,
        target_qty=2,
        upfront_cash_cost=10.0,
        duration_steps=48,
        econ_state=econ,
        family=ConversionFamily.PRODUCT_CONVERSION,
        worker_labor_steps=2,
        market_buy_price=15.0,
    )
    assert not comp.is_economically_superior
    assert "Dominated by direct target purchase" in comp.rejection_reason


def test_rc_04_feed_conversion_unlocks_milk_with_valid_runway_and_margin(group2_base_obs: Dict[str, Any]) -> None:
    """RC-04: High milk price, cow on farm, valid runway -> DETECTED & PATCHED."""
    obs = copy.deepcopy(group2_base_obs)
    obs["step"] = 100
    obs["farms"][0]["tiles"][2][2] = {"animal": "COW"}
    obs["farms"][0]["money"] = 1000.0
    obs["private"]["shed"]["WHEAT"] = 5
    obs["market"]["prices"]["MILK"] = 180
    obs["market"]["prices"]["WHEAT"] = 25
    econ = build_economic_state(obs)

    analyzer = ResourceOpportunityAnalyzer()
    opps = analyzer.analyze(econ, [])
    conv_opps = [o for o in opps if o.candidate_transformation_family == "RESOURCE_CONVERSION" and o.dependency_info.get("target") == "MILK"]
    assert len(conv_opps) > 0
    opp = conv_opps[0]
    assert opp.dependency_info["comparative_valuation"]["is_economically_superior"]
    assert opp.dependency_info["comparative_valuation"]["convert_net_value"] > 50.0

    gen = PatchGenerator(enabled_mechanisms={"RESOURCE_CONVERSION"})
    patches = gen.generate_patches([opp], econ, {"farmer": ["PASS"], "market": []})
    assert len(patches) == 1
    assert "MILK" in patches[0].patch_id


def test_rc_05_feed_conversion_rejected_when_runway_insufficient(group2_base_obs: Dict[str, Any]) -> None:
    """RC-05: Cow on pasture, but remaining horizon is too short to collect yield -> PRUNED."""
    obs = copy.deepcopy(group2_base_obs)
    obs["step"] = 680  # Remaining horizon = 40 steps (< 48 cow incubation + 4 buffer = 52)
    obs["farms"][0]["tiles"][2][2] = {"animal": "COW"}
    econ = build_economic_state(obs)

    comp = evaluate_comparative_margin(
        source_commodity="WHEAT",
        target_commodity="MILK",
        source_qty=1,
        target_qty=1,
        upfront_cash_cost=25.0,
        duration_steps=48,
        econ_state=econ,
        family=ConversionFamily.FEED_CONVERSION,
        pickup_buffer_steps=4,
        worker_labor_steps=2,
    )
    assert not comp.is_economically_superior
    assert "Insufficient terminal runway" in comp.rejection_reason


def test_rc_06_seed_conversion_rejected_when_planting_runway_insufficient(group2_base_obs: Dict[str, Any]) -> None:
    """RC-06: Carrot seed takes 48 steps to grow, but only 35 steps remain -> PRUNED."""
    obs = copy.deepcopy(group2_base_obs)
    obs["step"] = 685  # Remaining horizon = 35 steps
    econ = build_economic_state(obs)

    comp = evaluate_comparative_margin(
        source_commodity="CASH",
        target_commodity="CARROT",
        source_qty=0,
        target_qty=4,
        upfront_cash_cost=20.0,
        duration_steps=48,
        econ_state=econ,
        family=ConversionFamily.SEED_CONVERSION,
        pickup_buffer_steps=4,
        worker_labor_steps=2,
    )
    assert not comp.is_economically_superior
    assert "Insufficient terminal runway" in comp.rejection_reason


def test_rc_07_seed_conversion_unlocks_productive_yield_with_valid_runway(group2_base_obs: Dict[str, Any]) -> None:
    """RC-07: Carrot seed planted with remaining horizon = 200 -> positive margin."""
    obs = copy.deepcopy(group2_base_obs)
    obs["step"] = 100
    obs["farms"][0]["money"] = 500.0
    econ = build_economic_state(obs)

    comp = evaluate_comparative_margin(
        source_commodity="CASH",
        target_commodity="CARROT",
        source_qty=0,
        target_qty=4,
        upfront_cash_cost=20.0,
        duration_steps=48,
        econ_state=econ,
        family=ConversionFamily.SEED_CONVERSION,
        pickup_buffer_steps=4,
        worker_labor_steps=2,
    )
    assert comp.is_economically_superior
    # 4 carrots * 35 = 140. Upfront = 20, labor = 6. Net = 140 - 20 - 6 = 114
    assert comp.convert_net_value > 100.0


def test_rc_08_liquidity_risk_conversion_breaches_structural_feed_reserve(group2_base_obs: Dict[str, Any]) -> None:
    """RC-08: Conversion cash cost depletes cash below required structural herd feed reserve -> PRUNED."""
    obs = copy.deepcopy(group2_base_obs)
    obs["farms"][0]["tiles"][1][1] = {"animal": "COW"}
    obs["farms"][0]["tiles"][1][2] = {"animal": "COW"}
    obs["farms"][0]["money"] = 60.0  # Cash is 60, 2 cows need 50 feed reserve
    obs["market"]["prices"]["WHEAT"] = 25
    econ = build_economic_state(obs)

    # Conversion upfront cost is 25 -> post-cash is 35, which is < 50 required liquidity
    comp = evaluate_comparative_margin(
        source_commodity="WHEAT",
        target_commodity="WOOL",
        source_qty=1,
        target_qty=1,
        upfront_cash_cost=25.0,
        duration_steps=72,
        econ_state=econ,
        family=ConversionFamily.FEED_CONVERSION,
        worker_labor_steps=2,
    )
    assert not comp.is_economically_superior
    assert "Capital depletion" in comp.rejection_reason


def test_rc_09_high_worker_opportunity_cost_exceeds_gain(group2_base_obs: Dict[str, Any]) -> None:
    """RC-09: Heavy worker diversion (30 steps = 90 cost) exceeds gross gain (50) -> PRUNED."""
    obs = copy.deepcopy(group2_base_obs)
    econ = build_economic_state(obs)

    comp = evaluate_comparative_margin(
        source_commodity="WHEAT",
        target_commodity="CARROT",
        source_qty=1,
        target_qty=2,
        upfront_cash_cost=10.0,
        duration_steps=48,
        econ_state=econ,
        family=ConversionFamily.PRODUCT_CONVERSION,
        worker_labor_steps=30,  # 30 * 3 = 90 coins labor diversion
    )
    assert not comp.is_economically_superior
    assert "Negative incremental net margin" in comp.rejection_reason


def test_rc_10_terminal_conversion_beaten_by_direct_shed_liquidation(group2_base_obs: Dict[str, Any]) -> None:
    """RC-10: Near terminal, raw inventory liquidation beats conversion after labor cost -> PRUNED."""
    obs = copy.deepcopy(group2_base_obs)
    obs["step"] = 700
    obs["market"]["prices"]["WOOL"] = 200
    obs["market"]["prices"]["CLOTH"] = 205  # Slight markup
    econ = build_economic_state(obs)

    # Raw wool in shed liquidates for 200 without labor. Cloth is 205, but conversion labor is 4 steps (12 coins).
    # Net = 205 - 200 - 12 = -7 -> direct liquidation dominates!
    comp = evaluate_comparative_margin(
        source_commodity="WOOL",
        target_commodity="CLOTH",
        source_qty=1,
        target_qty=1,
        upfront_cash_cost=0.0,
        duration_steps=8,
        econ_state=econ,
        family=ConversionFamily.TERMINAL_CONVERSION,
        worker_labor_steps=4,
    )
    assert not comp.is_economically_superior
    assert "Negative incremental net margin" in comp.rejection_reason


def test_rc_11_terminal_conversion_superior_to_raw_liquidation(group2_base_obs: Dict[str, Any]) -> None:
    """RC-11: Near terminal, conversion value materially exceeds raw liquidation even after labor -> SUPERIOR."""
    obs = copy.deepcopy(group2_base_obs)
    obs["step"] = 690
    obs["market"]["prices"]["WHEAT"] = 25
    obs["market"]["prices"]["EGG"] = 60
    econ = build_economic_state(obs)

    # 1 wheat (25) -> 1 egg (60), labor 2 steps (6). Net = 60 - 25 - 6 = +29
    comp = evaluate_comparative_margin(
        source_commodity="WHEAT",
        target_commodity="EGG",
        source_qty=1,
        target_qty=1,
        upfront_cash_cost=0.0,
        duration_steps=24,
        econ_state=econ,
        family=ConversionFamily.TERMINAL_CONVERSION,
        worker_labor_steps=2,
    )
    assert comp.is_economically_superior
    assert comp.convert_net_value > 20.0


def test_rc_12_shed_capacity_overflow_prunes_conversion(group2_base_obs: Dict[str, Any]) -> None:
    """RC-12: Conversion producing net positive items when shed is full -> PRUNED."""
    obs = copy.deepcopy(group2_base_obs)
    # Fill shed to capacity 100
    obs["private"]["shed"]["WHEAT"] = 100
    econ = build_economic_state(obs)

    # Conversion from 0 input to 4 target carrots
    comp = evaluate_comparative_margin(
        source_commodity="CASH",
        target_commodity="CARROT",
        source_qty=0,
        target_qty=4,
        upfront_cash_cost=20.0,
        duration_steps=48,
        econ_state=econ,
        family=ConversionFamily.SEED_CONVERSION,
        worker_labor_steps=2,
    )
    assert not comp.is_economically_superior
    assert "Shed capacity overflow" in comp.rejection_reason



