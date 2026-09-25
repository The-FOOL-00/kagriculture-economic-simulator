# SPDX-License-Identifier: MIT
"""Kagriculture V40 Strategic Macro Action Space & Deterministic Executor.

Defines 16 economically expressive strategic macro decisions:
- Expansion Timing (accelerate land vs defer land)
- Labor Strategy (hire worker vs freeze hiring to reduce wages)
- Production Mix (Melon focus vs Carrot fast-cash vs Cow dairy vs Sheep wool)
- Market & Liquidity Strategy (front-run sell, accumulate hold, terminal liquidate, preserve buffer)

Provides:
1. Legal Action Masking: boolean legality mask based on observation and capital
2. Deterministic Action Execution: translates macro strategic intent into valid
   Kaggle action dictionaries on top of the base plan without breaking chore validity.
"""

from __future__ import annotations
import copy
from typing import Any, Dict, List, Optional, Tuple
import numpy as np

# Action Definitions
ACTION_NAMES = [
    "BASELINE_EXPERT",             # 0: Execute base planned choreography
    "EXPAND_LAND_NOW",             # 1: Unlock next quadrant immediately
    "DEFER_EXPANSION",             # 2: Cancel planned land buy to protect cash
    "HIRE_WORKER_NOW",             # 3: Hire an extra worker for harvest capacity
    "FREEZE_HIRING",               # 4: Suppress planned worker hiring
    "LIVESTOCK_COW",               # 5: Buy Cow and establish dairy production
    "LIVESTOCK_SHEEP",             # 6: Buy Sheep and establish wool production
    "CROP_FOCUS_MELON",            # 7: Buy Melon seed and prioritize planting
    "CROP_FOCUS_CARROT",           # 8: Buy Carrot seed for rapid 3-day cash cycle
    "HARVEST_AND_CARE_PRIORITY",   # 9: Prioritize collecting milk/wool and harvesting
    "MARKET_FRONT_RUN_SELL",       # 10: Sell high-value stock before opponent dumps
    "MARKET_ACCUMULATE_HOLD",      # 11: Suppress sales when prices are temporarily depressed
    "EARLY_SHED_LIQUIDATION",      # 12: Preemptive mid-to-late game shed clearing
    "TERMINAL_FULL_LIQUIDATION",   # 13: Endgame flush of all marketable products
    "PRESERVE_LIQUIDITY_BUFFER",   # 14: Emergency capital reservation (prevent insolvency)
    "AGGRESSIVE_REINVEST",         # 15: Deploy excess idle cash into productive assets
]

NUM_MACRO_ACTIONS = len(ACTION_NAMES)

# Economics constants
LAND_PRICES = (1000.0, 2000.0, 4000.0)
SEED_PRICES = {"WHEAT": 10.0, "CARROT": 20.0, "TOMATO": 50.0, "STRAWBERRY": 100.0, "MELON": 80.0}
ANIMAL_COSTS = {"COW": 400.0, "SHEEP": 500.0, "GOOSE": 300.0}
MIN_LIQUIDITY_BUFFER = 200.0


def _get(obj: Any, key: str, default: Any = None) -> Any:
    if isinstance(obj, dict):
        return obj.get(key, default)
    getter = getattr(obj, "get", None)
    if callable(getter):
        return getter(key, default)
    return getattr(obj, key, default)


def _safe_float(val: Any, default: float = 0.0) -> float:
    try:
        f = float(val)
        return default if np.isnan(f) or np.isinf(f) else f
    except (TypeError, ValueError):
        return default


def get_macro_action_mask(obs: Dict[str, Any], player: int = 0) -> np.ndarray:
    """Computes boolean legality mask for all 16 macro actions."""
    mask = np.zeros(NUM_MACRO_ACTIONS, dtype=bool)

    # Action 0: BASELINE_EXPERT is always legal
    mask[0] = True

    step = int(_get(obs, "step", 0) or 0)
    farms = list(_get(obs, "farms", []) or [])
    my_farm = farms[player] if farms and player < len(farms) else {}
    cash = _safe_float(_get(my_farm, "money", 0.0))

    unlocked_quads = len(list(_get(my_farm, "unlocked_quadrants", [0]) or [0]))
    hands = list(_get(my_farm, "hands", []) or [])
    worker_count = 1 + len(hands)

    private = _get(obs, "private", {}) or {}
    shed = dict(_get(private, "shed", {}) or {})
    market = _get(obs, "market", {}) or {}
    prices = dict(_get(market, "prices", {}) or {})

    # 1: EXPAND_LAND_NOW
    if unlocked_quads < 4 and step < 500:
        cost = LAND_PRICES[unlocked_quads - 1]
        if cash >= (cost + MIN_LIQUIDITY_BUFFER):
            mask[1] = True

    # 2: DEFER_EXPANSION (legal if land purchase is affordable or mid-game)
    if unlocked_quads < 4 and 100 <= step < 550:
        mask[2] = True

    # 3: HIRE_WORKER_NOW
    if worker_count < 14 and step < 504 and (step % 24 == 0):
        # Approximate hire cost: daily Fibonacci
        hire_cost = 10.0 + (worker_count * 5.0)
        if cash >= (hire_cost + MIN_LIQUIDITY_BUFFER):
            mask[3] = True

    # 4: FREEZE_HIRING (legal if we have at least 4 workers and before late-game)
    if worker_count >= 4 and step < 550:
        mask[4] = True

    # 5: LIVESTOCK_COW (cost $400, requires pasture structure or cash)
    if step < 432 and cash >= (ANIMAL_COSTS["COW"] + MIN_LIQUIDITY_BUFFER):
        mask[5] = True

    # 6: LIVESTOCK_SHEEP (cost $500)
    if step < 432 and cash >= (ANIMAL_COSTS["SHEEP"] + MIN_LIQUIDITY_BUFFER):
        mask[6] = True

    # 7: CROP_FOCUS_MELON (cost $80, melon takes 10 days = 240 steps to grow)
    if step < 450 and cash >= (SEED_PRICES["MELON"] + MIN_LIQUIDITY_BUFFER):
        mask[7] = True

    # 8: CROP_FOCUS_CARROT (cost $20, takes 3 days = 72 steps to grow)
    if step < 600 and cash >= (SEED_PRICES["CARROT"] + MIN_LIQUIDITY_BUFFER):
        mask[8] = True

    # 9: HARVEST_AND_CARE_PRIORITY
    if step < 710 and any(shed.get(item, 0) > 0 for item in ("WHEAT", "MILK", "WOOL", "EGG")):
        mask[9] = True

    # 10: MARKET_FRONT_RUN_SELL
    high_value_items = ("MILK", "WOOL", "STRAWBERRY", "MELON")
    has_high_val_goods = any(shed.get(item, 0) >= 2 and _safe_float(prices.get(item, 0)) >= 25.0 for item in high_value_items)
    if has_high_val_goods and step < 712:
        mask[10] = True

    # 11: MARKET_ACCUMULATE_HOLD
    has_depressed_goods = any(shed.get(item, 0) >= 2 and _safe_float(prices.get(item, 0)) < 18.0 for item in ("MILK", "WOOL", "STRAWBERRY"))
    if has_depressed_goods and step < 650:
        mask[11] = True

    # 12: EARLY_SHED_LIQUIDATION (Day 20..27, Steps 480..648)
    total_shed = sum(shed.get(item, 0) for item in high_value_items)
    if 480 <= step < 672 and total_shed >= 4:
        mask[12] = True

    # 13: TERMINAL_FULL_LIQUIDATION (Days 28..29, Steps 672..718)
    total_sellable = sum(shed.get(item, 0) for item in ("MILK", "WOOL", "STRAWBERRY", "MELON", "CARROT", "TOMATO", "EGG"))
    if step >= 672 and total_sellable > 0:
        mask[13] = True

    # 14: PRESERVE_LIQUIDITY_BUFFER (available if cash is tight)
    if cash < 1000.0 and step < 680:
        mask[14] = True

    # 15: AGGRESSIVE_REINVEST (available if cash surplus > $5,000)
    if cash >= 5000.0 and step < 500:
        mask[15] = True

    return mask


class StrategicMacroExecutor:
    """Executes macro intent on top of the base action dictionary."""

    def __init__(self):
        pass

    def execute(
        self,
        macro_action: int,
        base_action: Dict[str, Any],
        obs: Dict[str, Any],
        player: int = 0
    ) -> Dict[str, Any]:
        """Applies macro action residual modification to base_action."""
        if macro_action == 0 or macro_action >= NUM_MACRO_ACTIONS:
            return copy.deepcopy(base_action)

        act = copy.deepcopy(base_action)
        mkt = act.setdefault("market", [])
        step = int(_get(obs, "step", 0) or 0)
        private = _get(obs, "private", {}) or {}
        shed = dict(_get(private, "shed", {}) or {})
        market = _get(obs, "market", {}) or {}
        prices = dict(_get(market, "prices", {}) or {})

        # Action 1: EXPAND_LAND_NOW
        if macro_action == 1:
            if not any(len(o) > 0 and o[0] == "BUY_LAND" for o in mkt) and len(mkt) < 10:
                mkt.append(["BUY_LAND"])

        # Action 2: DEFER_EXPANSION
        elif macro_action == 2:
            mkt = [o for o in mkt if len(o) > 0 and o[0] != "BUY_LAND"]
            act["market"] = mkt

        # Action 3: HIRE_WORKER_NOW
        elif macro_action == 3:
            if not any(len(o) > 0 and o[0] == "HIRE" for o in mkt) and len(mkt) < 10:
                mkt.append(["HIRE"])

        # Action 4: FREEZE_HIRING
        elif macro_action == 4:
            mkt = [o for o in mkt if len(o) > 0 and o[0] != "HIRE"]
            act["market"] = mkt

        # Action 5: LIVESTOCK_COW
        elif macro_action == 5:
            if not any(len(o) > 1 and o[0] == "BUY_ANIMAL" and o[1] == "COW" for o in mkt) and len(mkt) < 10:
                mkt.append(["BUY_ANIMAL", "COW", 1])

        # Action 6: LIVESTOCK_SHEEP
        elif macro_action == 6:
            if not any(len(o) > 1 and o[0] == "BUY_ANIMAL" and o[1] == "SHEEP" for o in mkt) and len(mkt) < 10:
                mkt.append(["BUY_ANIMAL", "SHEEP", 1])

        # Action 7: CROP_FOCUS_MELON
        elif macro_action == 7:
            if not any(len(o) > 1 and o[0] == "BUY_SEED" and o[1] == "MELON" for o in mkt) and len(mkt) < 10:
                mkt.append(["BUY_SEED", "MELON", 4])

        # Action 8: CROP_FOCUS_CARROT
        elif macro_action == 8:
            if not any(len(o) > 1 and o[0] == "BUY_SEED" and o[1] == "CARROT" for o in mkt) and len(mkt) < 10:
                mkt.append(["BUY_SEED", "CARROT", 6])

        # Action 10: MARKET_FRONT_RUN_SELL
        elif macro_action == 10:
            for item in ("MILK", "WOOL", "STRAWBERRY", "MELON"):
                qty = shed.get(item, 0)
                if qty > 0 and len(mkt) < 10:
                    already_selling = any(len(o) > 1 and o[0] == "SELL" and o[1] == item for o in mkt)
                    if not already_selling:
                        mkt.append(["SELL", item, qty])

        # Action 11: MARKET_ACCUMULATE_HOLD
        elif macro_action == 11:
            # Suppress selling of depressed items
            depressed = [item for item in ("MILK", "WOOL", "STRAWBERRY") if _safe_float(prices.get(item, 0)) < 18.0]
            mkt = [o for o in mkt if not (len(o) > 1 and o[0] == "SELL" and o[1] in depressed)]
            act["market"] = mkt

        # Action 12: EARLY_SHED_LIQUIDATION
        elif macro_action == 12:
            for item in ("MILK", "WOOL", "STRAWBERRY", "MELON"):
                qty = shed.get(item, 0)
                if qty >= 2 and len(mkt) < 10:
                    already_selling = any(len(o) > 1 and o[0] == "SELL" and o[1] == item for o in mkt)
                    if not already_selling:
                        mkt.append(["SELL", item, qty])

        # Action 13: TERMINAL_FULL_LIQUIDATION
        elif macro_action == 13:
            for item in ("MILK", "WOOL", "STRAWBERRY", "MELON", "CARROT", "TOMATO", "EGG", "WHEAT"):
                qty = shed.get(item, 0)
                if qty > 0 and len(mkt) < 10:
                    already_selling = any(len(o) > 1 and o[0] == "SELL" and o[1] == item for o in mkt)
                    if not already_selling:
                        mkt.append(["SELL", item, qty])

        # Action 14: PRESERVE_LIQUIDITY_BUFFER
        elif macro_action == 14:
            # Remove speculative purchases (land, animals, seeds)
            mkt = [o for o in mkt if len(o) > 0 and o[0] not in ("BUY_LAND", "BUY_ANIMAL")]
            act["market"] = mkt

        # Action 15: AGGRESSIVE_REINVEST
        elif macro_action == 15:
            # Add melon seed and cow buy if affordable
            if len(mkt) < 9:
                mkt.append(["BUY_SEED", "MELON", 4])
            if len(mkt) < 10:
                mkt.append(["BUY_ANIMAL", "COW", 1])

        # Ensure order cap is respected (max 10 orders per turn)
        act["market"] = mkt[:10]
        return act
