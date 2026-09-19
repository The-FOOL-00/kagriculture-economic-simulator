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
