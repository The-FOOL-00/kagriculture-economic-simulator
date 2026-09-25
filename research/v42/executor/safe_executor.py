# SPDX-License-Identifier: MIT
"""Kagriculture V42 State-Aware Safe Executor.

Preserves the V41 Golden Property:
- When intervention is NO_INTERVENTION (0), output is 100% bit-for-bit identical to V35.
- Implements refined V42 intervention vocabulary:
  * Discrete terminal liquidation (full vs partial 50%)
  * Calibrated peak spot sales (Milk, Wool, Strawberry)
  * Dynamic boundary-gated land expansion
  * Liquidity protection
- Fails closed to V35 on any exception, illegal condition, or safety violation.
"""

from __future__ import annotations
import copy
import os
import sys
from typing import Any, Dict, List, Optional
import numpy as np

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from candidates.v35_a7_opening.main import V35OpeningController

INTERVENTION_NAMES = [
    "NO_INTERVENTION",               # 0: Pure V35 baseline execution (Golden Property)
    "TERMINAL_LIQUIDATE_FULL",       # 1: Steps 690-710 sell 100% of marketable shed goods
    "TERMINAL_LIQUIDATE_PARTIAL",    # 2: Steps 690-710 sell 50% of marketable shed goods (prevents crash)
    "SPOT_SELL_PEAK_MILK",           # 3: Sell Milk when spot price >= $45 (high margin)
    "SPOT_SELL_PEAK_WOOL",           # 4: Sell Wool when spot price >= $50 (high margin)
    "SPOT_SELL_PEAK_STRAWBERRY",     # 5: Sell Strawberry when spot price >= $35 (high margin)
    "HOLD_DEPRESSED_GOODS",          # 6: Suppress sales of depressed items (< $20) if shed < 75%
    "MIDGAME_LAND_EXPAND_GATED",     # 7: Step 280-312 land expansion strictly gated by cash >= $16,000
    "PRESERVE_LIQUIDITY_BUFFER",     # 8: Remove speculative buy orders if cash < $500
    "DEFER_EXPANSION_LOW_CASH",      # 9: Defer land buy if cash < $1,500
]

NUM_INTERVENTIONS = len(INTERVENTION_NAMES)


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


class StateAwareExecutor:
    """V42 Execution controller wrapping V35 with fail-closed safety."""

    def __init__(self, mode: str = "v35"):
        self.mode = mode  # "v35" or "v39"
        self.v35 = V35OpeningController(wash_buy=25, wash_sell=25)
        self.history: List[int] = []
        self.last_step = -1

    def reset(self):
        self.v35.reset()
        self.history.clear()
        self.last_step = -1

    def get_safety_mask(self, obs: Dict[str, Any], player: int = 0) -> np.ndarray:
        """Computes boolean legality & safety mask for all interventions.
        NO_INTERVENTION (0) is ALWAYS True.
        """
        mask = np.zeros(NUM_INTERVENTIONS, dtype=bool)
        mask[0] = True  # Baseline is always legal

        step = int(_get(obs, "step", 0) or 0)
        farms = list(_get(obs, "farms", []) or [])
        my_farm = farms[player] if farms and player < len(farms) else {}
        cash = _safe_float(_get(my_farm, "money", 0.0))
        unlocked_quads = len(list(_get(my_farm, "unlocked_quadrants", [0]) or [0]))

        private = _get(obs, "private", {}) or {}
        shed = dict(_get(private, "shed", {}) or {})
        total_shed_items = sum(shed.values())

        market = _get(obs, "market", {}) or {}
        prices = dict(_get(market, "prices", {}) or {})

        marketable_items = ("STRAWBERRY", "MILK", "WOOL", "MELON")
        has_marketable = any(shed.get(item, 0) > 0 for item in marketable_items)

        # 1: TERMINAL_LIQUIDATE_FULL
        if step in (692, 693, 694) or (step >= 710 and step <= 718):
            if has_marketable:
                mask[1] = True

        # 2: TERMINAL_LIQUIDATE_PARTIAL (sell 50% if quantity >= 2)
        if step in (690, 691, 692, 693, 694) or (step >= 705 and step <= 715):
            if any(shed.get(item, 0) >= 2 for item in marketable_items):
                mask[2] = True

        # 3: SPOT_SELL_PEAK_MILK
        if shed.get("MILK", 0) >= 3 and _safe_float(prices.get("MILK", 0)) >= 45.0 and step < 680:
            mask[3] = True

        # 4: SPOT_SELL_PEAK_WOOL
        if shed.get("WOOL", 0) >= 3 and _safe_float(prices.get("WOOL", 0)) >= 50.0 and step < 680:
            mask[4] = True

        # 5: SPOT_SELL_PEAK_STRAWBERRY
        if shed.get("STRAWBERRY", 0) >= 4 and _safe_float(prices.get("STRAWBERRY", 0)) >= 35.0 and step < 680:
            mask[5] = True

        # 6: HOLD_DEPRESSED_GOODS
        if step < 650 and total_shed_items <= 75:
            has_depressed = any(
                shed.get(item, 0) >= 2 and _safe_float(prices.get(item, 0)) < 20.0
                for item in ("MILK", "WOOL", "STRAWBERRY")
            )
            if has_depressed:
                mask[6] = True

        # 7: MIDGAME_LAND_EXPAND_GATED (only with massive capital surplus >= $16,000)
        if 280 <= step <= 312 and unlocked_quads < 4 and cash >= 16000.0:
            mask[7] = True

        # 8: PRESERVE_LIQUIDITY_BUFFER
        if cash < 500.0 and step < 680:
            mask[8] = True

        # 9: DEFER_EXPANSION_LOW_CASH
        if unlocked_quads < 4 and cash < 1500.0 and 100 <= step < 500:
            mask[9] = True

        return mask

    def execute(
        self,
        intervention: int,
        obs: Dict[str, Any],
        cfg: Optional[Dict[str, Any]] = None,
        player: int = 0
    ) -> Dict[str, Any]:
        """Executes intervention on top of V35 base action.
        Guarantees: intervention == 0 => bit-identical to V35.act(obs, cfg).
        """
        step = int(_get(obs, "step", 0) or 0)
        self.last_step = step

        # Baseline action from V35
        try:
            base_act = self.v35.act(obs, cfg)
        except Exception:
            return {"farmer": ["PASS"], "hands": [], "market": []}

        # In V39 mode, apply V39 liquidation rule by default if intervention is 0
        if self.mode == "v39" and step in (693, 694) and intervention == 0:
            intervention = 1

        # Golden Property: NO_INTERVENTION returns base_act directly
        if intervention == 0 or intervention >= NUM_INTERVENTIONS:
            self.history.append(0)
            return base_act

        # Safety verification
        mask = self.get_safety_mask(obs, player=player)
        if not mask[intervention]:
            self.history.append(0)
            return base_act

        # Apply verified intervention
        try:
            act = copy.deepcopy(base_act)
            mkt = act.setdefault("market", [])
            private = _get(obs, "private", {}) or {}
            shed = dict(_get(private, "shed", {}) or {})
            already_selling = {o[1] for o in mkt if len(o) > 1 and o[0] == "SELL"}

            # 1: TERMINAL_LIQUIDATE_FULL (100% of marketable goods)
            if intervention == 1:
                for item in ("STRAWBERRY", "MILK", "WOOL", "MELON", "CARROT", "TOMATO"):
                    qty = shed.get(item, 0)
                    if qty > 0 and item not in already_selling and len(mkt) < 10:
                        mkt.append(["SELL", item, qty])
                        already_selling.add(item)

            # 2: TERMINAL_LIQUIDATE_PARTIAL (50% of marketable goods)
            elif intervention == 2:
                for item in ("STRAWBERRY", "MILK", "WOOL", "MELON"):
                    qty = shed.get(item, 0)
                    if qty >= 2 and item not in already_selling and len(mkt) < 10:
                        sell_qty = max(1, qty // 2)
                        mkt.append(["SELL", item, sell_qty])
                        already_selling.add(item)

            # 3: SPOT_SELL_PEAK_MILK
            elif intervention == 3:
                qty = shed.get("MILK", 0)
                if qty >= 2 and "MILK" not in already_selling and len(mkt) < 10:
                    mkt.append(["SELL", "MILK", qty])

            # 4: SPOT_SELL_PEAK_WOOL
            elif intervention == 4:
                qty = shed.get("WOOL", 0)
                if qty >= 2 and "WOOL" not in already_selling and len(mkt) < 10:
                    mkt.append(["SELL", "WOOL", qty])

            # 5: SPOT_SELL_PEAK_STRAWBERRY
            elif intervention == 5:
                qty = shed.get("STRAWBERRY", 0)
                if qty >= 2 and "STRAWBERRY" not in already_selling and len(mkt) < 10:
                    mkt.append(["SELL", "STRAWBERRY", qty])

            # 6: HOLD_DEPRESSED_GOODS
            elif intervention == 6:
                market_info = _get(obs, "market", {}) or {}
                prices = dict(_get(market_info, "prices", {}) or {})
                depressed = {
                    item for item in ("MILK", "WOOL", "STRAWBERRY")
                    if _safe_float(prices.get(item, 0)) < 20.0
                }
                mkt = [o for o in mkt if not (len(o) > 1 and o[0] == "SELL" and o[1] in depressed)]
                act["market"] = mkt

            # 7: MIDGAME_LAND_EXPAND_GATED
            elif intervention == 7:
                if not any(len(o) > 0 and o[0] == "BUY_LAND" for o in mkt) and len(mkt) < 10:
                    mkt.append(["BUY_LAND"])

            # 8: PRESERVE_LIQUIDITY_BUFFER
            elif intervention == 8:
                mkt = [o for o in mkt if len(o) > 0 and o[0] not in ("BUY_LAND", "BUY_ANIMAL")]
                act["market"] = mkt

            # 9: DEFER_EXPANSION_LOW_CASH
            elif intervention == 9:
                mkt = [o for o in mkt if len(o) > 0 and o[0] != "BUY_LAND"]
                act["market"] = mkt

            act["market"] = mkt[:10]
            self.history.append(intervention)
            return act

        except Exception:
            self.history.append(0)
            return base_act
