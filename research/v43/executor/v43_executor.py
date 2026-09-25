# SPDX-License-Identifier: MIT
"""Kagriculture V43 State-Aware Multi-Step Safe Executor.

Preserves the Golden Property:
- When intervention is NO_INTERVENTION (0), output is 100% bit-for-bit identical to V35.
- Implements V43 compositional intervention primitives:
  * Discrete parametric terminal liquidation (30%, 50%, 70%, 100%)
  * Calibrated spot sales (Milk, Wool)
  * Holding depressed goods
  * Liquidity preservation and expansion deferral
- Fails closed to V35 on any exception, illegal state, or safety violation.
"""

from __future__ import annotations
import copy
import os
import sys
from typing import Any, Dict, List, Optional, Tuple
import numpy as np

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from candidates.v35_a7_opening.main import V35OpeningController

V43_INTERVENTION_NAMES = [
    "NO_INTERVENTION",             # 0: Pure V35 baseline execution (Golden Property)
    "LIQUIDATE_PARTIAL_30",        # 1: Liquidate 30% of marketable shed goods
    "LIQUIDATE_PARTIAL_50",        # 2: Liquidate 50% of marketable shed goods (V42 core)
    "LIQUIDATE_PARTIAL_70",        # 3: Liquidate 70% of marketable shed goods
    "LIQUIDATE_FULL_100",          # 4: Liquidate 100% of marketable shed goods
    "SPOT_SELL_PEAK_MILK",         # 5: Sell Milk when spot price >= $45
    "SPOT_SELL_PEAK_WOOL",         # 6: Sell Wool when spot price >= $50
    "HOLD_DEPRESSED_GOODS",        # 7: Suppress sales of depressed items (< $20)
    "PRESERVE_LIQUIDITY_BUFFER",   # 8: Remove speculative buy orders if cash < $500
    "DEFER_EXPANSION_LOW_CASH",    # 9: Defer land buy if cash < $1,500
]

NUM_V43_INTERVENTIONS = len(V43_INTERVENTION_NAMES)
MARKETABLE_COMMODITIES = ("STRAWBERRY", "MILK", "WOOL", "MELON")


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


class V43SafeExecutor:
    """Multi-step execution controller wrapping V35 with fail-closed safety."""

    def __init__(self, mode: str = "v35"):
        self.mode = mode
        self.v35 = V35OpeningController(wash_buy=25, wash_sell=25)
        self.history: List[int] = []
        self.last_step = -1

    def reset(self):
        self.v35.reset()
        self.history.clear()
        self.last_step = -1

    def get_safety_mask(self, obs: Dict[str, Any], player: int = 0) -> np.ndarray:
        """Computes boolean legality & safety mask for all interventions.
        Action 0 (NO_INTERVENTION) is ALWAYS True.
        """
        mask = np.zeros(NUM_V43_INTERVENTIONS, dtype=bool)
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

        has_marketable = any(shed.get(item, 0) > 0 for item in MARKETABLE_COMMODITIES)
        has_marketable_multi = any(shed.get(item, 0) >= 2 for item in MARKETABLE_COMMODITIES)

        # Terminal liquidation window: steps 690-718
        if (690 <= step <= 696) or (704 <= step <= 718):
            if has_marketable_multi:
                mask[1] = True  # 30%
                mask[2] = True  # 50%
                mask[3] = True  # 70%
            if has_marketable:
                mask[4] = True  # 100%

        # 5: SPOT_SELL_PEAK_MILK
        if shed.get("MILK", 0) >= 3 and _safe_float(prices.get("MILK", 0)) >= 45.0 and step < 680:
            mask[5] = True

        # 6: SPOT_SELL_PEAK_WOOL
        if shed.get("WOOL", 0) >= 3 and _safe_float(prices.get("WOOL", 0)) >= 50.0 and step < 680:
            mask[6] = True

        # 7: HOLD_DEPRESSED_GOODS
        if step < 650 and total_shed_items <= 75:
            has_depressed = any(
                shed.get(item, 0) >= 2 and _safe_float(prices.get(item, 0)) < 20.0
                for item in ("MILK", "WOOL", "STRAWBERRY")
            )
            if has_depressed:
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
        player: int = 0,
        custom_fraction: Optional[float] = None
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

        # Golden Property: NO_INTERVENTION returns base_act directly
        if intervention == 0 or intervention >= NUM_V43_INTERVENTIONS:
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

            # Parametric Liquidation: Actions 1, 2, 3, 4
            if intervention in (1, 2, 3, 4):
                if custom_fraction is not None:
                    frac = custom_fraction
                elif intervention == 1:
                    frac = 0.30
                elif intervention == 2:
                    frac = 0.50
                elif intervention == 3:
                    frac = 0.70
                else:
                    frac = 1.00

                for item in MARKETABLE_COMMODITIES:
                    qty = shed.get(item, 0)
                    if qty > 0 and item not in already_selling and len(mkt) < 10:
                        if frac >= 0.99 or qty == 1:
                            sell_qty = qty
                        else:
                            sell_qty = max(1, int(np.round(qty * frac)))
                        mkt.append(["SELL", item, sell_qty])
                        already_selling.add(item)

            # 5: SPOT_SELL_PEAK_MILK
            elif intervention == 5:
                qty = shed.get("MILK", 0)
                if qty >= 2 and "MILK" not in already_selling and len(mkt) < 10:
                    mkt.append(["SELL", "MILK", qty])

            # 6: SPOT_SELL_PEAK_WOOL
            elif intervention == 6:
                qty = shed.get("WOOL", 0)
                if qty >= 2 and "WOOL" not in already_selling and len(mkt) < 10:
                    mkt.append(["SELL", "WOOL", qty])

            # 7: HOLD_DEPRESSED_GOODS
            elif intervention == 7:
                market_info = _get(obs, "market", {}) or {}
                prices = dict(_get(market_info, "prices", {}) or {})
                depressed = {
                    item for item in ("MILK", "WOOL", "STRAWBERRY")
                    if _safe_float(prices.get(item, 0)) < 20.0
                }
                mkt = [o for o in mkt if not (len(o) > 1 and o[0] == "SELL" and o[1] in depressed)]
                act["market"] = mkt

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
