# SPDX-License-Identifier: MIT
"""Kagriculture V34 Tactical Candidate Generator.

Generates localized, legal, physically conservative, A7-compatible alternative actions
at economically sensitive decision points across the 4 core categories:
1. Category A: Step 0 Market Wash Sizing (20/20, 25/25, 35/35, NO_WASH)
2. Category B: Late-Game Planting Cutoff (suppress futile late planting at t >= 680)
3. Category C: Terminal Pre-Liquidation (orderly pre-sale of high-margin crops at t >= 714)
4. Category D: Pre-Wage Reserve Buffer (ensure cash >= $60 before midnight wage deduction)
"""

from __future__ import annotations
import copy
from typing import Any, Dict, List, Optional, Tuple

from candidates.v34_a7_tactical.tactical_types import (
    TacticalCandidate, PromotionStatus
)

CROP_GROWTH_TICKS = {
    "WHEAT": 12,
    "CARROT": 24,
    "TOMATO": 48,
    "STRAWBERRY": 72,
    "MELON": 96,
}


def generate_step0_candidates(obs: Dict[str, Any], default_a7_action: Dict[str, Any]) -> List[TacticalCandidate]:
    """Generates market wash sizing alternatives at Step 0."""
    step = int(obs.get("step", 0) or 0)
    if step != 0:
        return []

    candidates = []
    # Candidate 1: Wash 20
    act_w20 = copy.deepcopy(default_a7_action)
    act_w20["market"] = [["BUY_PRODUCT", "WHEAT", 20], ["SELL", "WHEAT", 20]]
    candidates.append(TacticalCandidate(
        action_id="TACTICAL_STEP0_WASH20",
        parent_a7_action=default_a7_action,
        candidate_action=act_w20,
        category="MARKET_TIMING",
        state_signature="STEP0_WASH_20",
        trigger_features={"step": 0.0, "wheat_wash_size": 20.0},
        action_delta_description="Resize step-0 wheat wash from 30/30 to 20/20",
        physical_impact="NONE",
        market_impact="CONSERVATIVE_CAPITAL_PRESERVATION",
        compatible_horizon=720,
        status=PromotionStatus.EXPERIMENTAL,
    ))

    # Candidate 2: Wash 25
    act_w25 = copy.deepcopy(default_a7_action)
    act_w25["market"] = [["BUY_PRODUCT", "WHEAT", 25], ["SELL", "WHEAT", 25]]
    candidates.append(TacticalCandidate(
        action_id="TACTICAL_STEP0_WASH25",
        parent_a7_action=default_a7_action,
        candidate_action=act_w25,
        category="MARKET_TIMING",
        state_signature="STEP0_WASH_25",
        trigger_features={"step": 0.0, "wheat_wash_size": 25.0},
        action_delta_description="Resize step-0 wheat wash from 30/30 to 25/25",
        physical_impact="NONE",
        market_impact="CONSERVATIVE_CAPITAL_PRESERVATION",
        compatible_horizon=720,
        status=PromotionStatus.EXPERIMENTAL,
    ))

    # Candidate 3: Wash 35
    act_w35 = copy.deepcopy(default_a7_action)
    act_w35["market"] = [["BUY_PRODUCT", "WHEAT", 35], ["SELL", "WHEAT", 35]]
    candidates.append(TacticalCandidate(
        action_id="TACTICAL_STEP0_WASH35",
        parent_a7_action=default_a7_action,
        candidate_action=act_w35,
        category="MARKET_TIMING",
        state_signature="STEP0_WASH_35",
        trigger_features={"step": 0.0, "wheat_wash_size": 35.0},
        action_delta_description="Resize step-0 wheat wash from 30/30 to 35/35",
        physical_impact="NONE",
        market_impact="EXPANSIVE_SPREAD_CAPTURE",
        compatible_horizon=720,
        status=PromotionStatus.EXPERIMENTAL,
    ))

    # Candidate 4: No Wash (PASS on market)
    act_nowash = copy.deepcopy(default_a7_action)
    act_nowash["market"] = []
    candidates.append(TacticalCandidate(
        action_id="TACTICAL_STEP0_NOWASH",
        parent_a7_action=default_a7_action,
        candidate_action=act_nowash,
        category="MARKET_TIMING",
        state_signature="STEP0_NO_WASH",
        trigger_features={"step": 0.0, "wheat_wash_size": 0.0},
        action_delta_description="Eliminate step-0 market wash completely (clean pass)",
        physical_impact="NONE",
        market_impact="ZERO_MARKET_INTERACTION",
        compatible_horizon=720,
        status=PromotionStatus.EXPERIMENTAL,
    ))

    return candidates


def generate_late_cutoff_candidates(obs: Dict[str, Any], default_a7_action: Dict[str, Any]) -> List[TacticalCandidate]:
    """Generates planting cutoff alternatives at step >= 680."""
    step = int(obs.get("step", 0) or 0)
    if step < 672:
        return []

    remaining_steps = 718 - step
    units = [default_a7_action.get("farmer", ["PASS"])] + list(default_a7_action.get("hands", []) or [])

    # Check if any unit is attempting to PLANT a slow crop that cannot mature
    has_futile_plant = False
    cleaned_farmer = list(default_a7_action.get("farmer", ["PASS"]))
    cleaned_hands = [list(h) for h in (default_a7_action.get("hands", []) or [])]

    all_cleaned = [cleaned_farmer] + cleaned_hands
    for i, u in enumerate(units):
        if u and u[0] == "PLANT" and len(u) >= 2:
            crop = u[1]
            growth_req = CROP_GROWTH_TICKS.get(crop, 24)
            if growth_req > remaining_steps:
                has_futile_plant = True
                # Convert futile plant to PASS
                all_cleaned[i] = ["PASS"]

    if not has_futile_plant:
        return []

    act_cutoff = copy.deepcopy(default_a7_action)
    act_cutoff["farmer"] = all_cleaned[0]
    act_cutoff["hands"] = all_cleaned[1:]

    # Also remove corresponding BUY_SEED orders if present
    mkt = []
    for order in (act_cutoff.get("market") or []):
        if order and order[0] == "BUY_SEED" and len(order) >= 2:
            crop = order[1]
            if CROP_GROWTH_TICKS.get(crop, 24) > remaining_steps:
                continue
        mkt.append(order)
    act_cutoff["market"] = mkt

    return [TacticalCandidate(
        action_id="TACTICAL_LATE_PLANTING_CUTOFF",
        parent_a7_action=default_a7_action,
        candidate_action=act_cutoff,
        category="TERMINAL_TIMING",
        state_signature=f"STEP_{step}_LATE_CUTOFF",
        trigger_features={"step": float(step), "remaining_steps": float(remaining_steps)},
        action_delta_description=f"Suppress futile planting of crops requiring > {remaining_steps} ticks to mature",
        physical_impact="CONSERVATIVE_IDLE",
        market_impact="SEED_EXPENSE_SAVING",
        compatible_horizon=remaining_steps,
        status=PromotionStatus.EXPERIMENTAL,
    )]


def generate_pre_liquidation_candidates(obs: Dict[str, Any], default_a7_action: Dict[str, Any]) -> List[TacticalCandidate]:
    """Generates pre-liquidation alternatives at step in [714..717]."""
    step = int(obs.get("step", 0) or 0)
    if not (714 <= step <= 717):
        return []

    shed = obs.get("private", {}).get("shed", {}) or {}
    prices = obs.get("market", {}).get("prices", {}) or {}

    # Check for high-margin items held in shed
    sells_to_add = []
    for item in ["MELON", "STRAWBERRY", "MILK", "WOOL"]:
        qty = int(shed.get(item, 0) or 0)
        p = float(prices.get(item, 0.0) or 0.0)
        if qty >= 5 and p >= 100.0:
            sells_to_add.append(["SELL", item, min(qty, 20)])

    if not sells_to_add:
        return []

    act_preliq = copy.deepcopy(default_a7_action)
    current_market = act_preliq.get("market", []) or []
    # Prepend our high-margin sells up to limit 10
    new_market = (sells_to_add + current_market)[:10]
    act_preliq["market"] = new_market

    return [TacticalCandidate(
        action_id=f"TACTICAL_PRE_LIQUIDATION_S{step}",
        parent_a7_action=default_a7_action,
        candidate_action=act_preliq,
        category="TERMINAL_TIMING",
        state_signature=f"STEP_{step}_PRE_LIQUIDATION",
        trigger_features={"step": float(step), "pre_sell_items_count": float(len(sells_to_add))},
        action_delta_description=f"Pre-sell {len(sells_to_add)} high-margin items before final step 718 dump",
        physical_impact="NONE",
        market_impact="PRICE_SLIPPAGE_MITIGATION",
        compatible_horizon=719 - step,
        status=PromotionStatus.EXPERIMENTAL,
    )]
