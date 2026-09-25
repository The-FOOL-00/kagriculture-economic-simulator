# SPDX-License-Identifier: MIT
"""Kagriculture V44 Full-Game Economic Strategy Executor.

Expands beyond terminal liquidation into full-game economic alpha families:
- Family A: Land Economics (Advance Land 1/2, Land 3 ROI, Defer Late Land)
- Family B: Labor / Workforce Economics (Early hiring surge, Late hire capping)
- Family C: Livestock & Production Mix (Early cow/sheep acceleration, Payback cutoffs)
- Family D: Town Shop & Scarcity Arbitrage (Peak consumption tick selling)
- Family E: Liquidity Management (Cash reserve shields)
- Family F: Known Liquidation Baseline (V43 40/60/Flush schedule)

Guarantees:
- NO_INTERVENTION (0) is 100.00% bit-for-bit identical to V35 (Golden Property).
- Full legality checks before any action execution.
- Fail-closed fallback to V35 on any error.
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

V44_INTERVENTIONS = [
    # Baseline
    ("NO_INTERVENTION", "BASELINE", "Pure V35 execution (Golden Property)"),
    # Family A: Land Economics
    ("ADVANCE_LAND_1", "LAND", "Purchase Land 1 earlier at step 120-145 if cash >= 1000"),
    ("ADVANCE_LAND_2", "LAND", "Purchase Land 2 earlier at step 220-255 if cash >= 2000"),
    ("PURCHASE_LAND_3", "LAND", "Purchase Land 3 (SE, $4000) at step 300-450 if cash >= 4500"),
    ("DEFER_LAND_3", "LAND", "Suppress Land 3 purchase if step >= 450 (avoid trapped capital)"),
    # Family B: Labor / Workforce Economics
    ("HIRE_EARLY_SURGE", "LABOR", "Hire 2 extra hands at step 24-48 at cheap Fib cost ($1-$2)"),
    ("CAP_LATE_HIRING", "LABOR", "Suppress hiring after step 550 (farm workforce saturated)"),
    # Family C: Livestock & Production Mix
    ("BUY_EXTRA_COW_EARLY", "LIVESTOCK", "Purchase extra Cow ($600) at step 70-120 if cash >= 800"),
    ("BUY_EXTRA_SHEEP_EARLY", "LIVESTOCK", "Purchase extra Sheep ($500) at step 70-120 if cash >= 700"),
    ("INVESTMENT_PAYBACK_CUTOFF", "LIVESTOCK", "Suppress animal purchases after step 520 (cannot amortize)"),
    # Family D: Town Shop & Scarcity Arbitrage
    ("TOWN_SHOP_ARBITRAGE", "MARKET", "Sell high-value shed goods on shop drain tick (step % 4 == 0)"),
    ("TOWN_CENTER_ARBITRAGE", "MARKET", "Sell high-value shed goods on town center drain tick (step % 12 == 0)"),
    # Family E: Liquidity Management
    ("LIQUIDITY_BUFFER_SHIELD", "LIQUIDITY", "Preserve $400 cash buffer in steps 100-400"),
    # Family F: Known Terminal Liquidation
    ("TERMINAL_STAGGERED_FLUSH", "TERMINAL", "V43 3-Point Liquidation: 40% @ 694, 60% @ 705, 100% @ 716"),
]

V44_INTERVENTION_NAMES = [name for name, _, _ in V44_INTERVENTIONS]
NUM_V44_INTERVENTIONS = len(V44_INTERVENTIONS)
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


class V44SafeExecutor:
    """Full-horizon safe economic executor wrapping V35."""

    def __init__(self):
        self.v35 = V35OpeningController(wash_buy=25, wash_sell=25)
        self.history: List[int] = []

    def reset(self):
        self.v35.reset()
        self.history.clear()

    def get_safety_mask(self, obs: Dict[str, Any], player: int = 0) -> np.ndarray:
        """Determines legality and mechanical safety for all V44 interventions."""
        mask = np.zeros(NUM_V44_INTERVENTIONS, dtype=bool)
        mask[0] = True  # Baseline always legal

        step = int(_get(obs, "step", 0) or 0)
        farms = list(_get(obs, "farms", []) or [])
        my_farm = farms[player] if farms and player < len(farms) else {}
        cash = _safe_float(_get(my_farm, "money", 0.0))
        unlocked_quads = len(list(_get(my_farm, "unlocked_quadrants", [0]) or [0]))
        num_hands = len(list(_get(my_farm, "hands", []) or []))

        private = _get(obs, "private", {}) or {}
        shed = dict(_get(private, "shed", {}) or {})
        has_marketable = any(shed.get(item, 0) > 0 for item in MARKETABLE_COMMODITIES)

        # 1: ADVANCE_LAND_1
        if 120 <= step <= 145 and unlocked_quads == 1 and cash >= 1000.0:
            mask[1] = True

        # 2: ADVANCE_LAND_2
        if 220 <= step <= 255 and unlocked_quads == 2 and cash >= 2000.0:
            mask[2] = True

        # 3: PURCHASE_LAND_3
        if 300 <= step <= 450 and unlocked_quads == 3 and cash >= 4500.0:
            mask[3] = True

        # 4: DEFER_LAND_3
        if step >= 450 and unlocked_quads == 3:
            mask[4] = True

        # 5: HIRE_EARLY_SURGE
        if 24 <= step <= 48 and num_hands <= 12 and cash >= 20.0:
            mask[5] = True

        # 6: CAP_LATE_HIRING
        if step >= 550:
            mask[6] = True

        # 7: BUY_EXTRA_COW_EARLY
        if 70 <= step <= 120 and cash >= 800.0:
            mask[7] = True

        # 8: BUY_EXTRA_SHEEP_EARLY
        if 70 <= step <= 120 and cash >= 700.0:
            mask[8] = True

        # 9: INVESTMENT_PAYBACK_CUTOFF
        if step >= 520:
            mask[9] = True

        # 10: TOWN_SHOP_ARBITRAGE (Step % 4 == 0 or 1)
        if (step % 4 == 0 or step % 4 == 1) and has_marketable and step < 680:
            mask[10] = True

        # 11: TOWN_CENTER_ARBITRAGE (Step % 12 == 0 or 1)
        if (step % 12 == 0 or step % 12 == 1) and has_marketable and step < 680:
            mask[11] = True

        # 12: LIQUIDITY_BUFFER_SHIELD
        if 100 <= step <= 400 and cash < 400.0:
            mask[12] = True

        # 13: TERMINAL_STAGGERED_FLUSH
        if (693 <= step <= 696) or (704 <= step <= 707) or (step >= 716):
            if has_marketable:
                mask[13] = True

        return mask

    def execute(
        self,
        intervention: int,
        obs: Dict[str, Any],
        cfg: Optional[Dict[str, Any]] = None,
        player: int = 0
    ) -> Dict[str, Any]:
        """Executes intervention safely on top of V35 base action."""
        step = int(_get(obs, "step", 0) or 0)

        try:
            base_act = self.v35.act(obs, cfg)
        except Exception:
            return {"farmer": ["PASS"], "hands": [], "market": []}

        if intervention == 0 or intervention >= NUM_V44_INTERVENTIONS:
            self.history.append(0)
            return base_act

        mask = self.get_safety_mask(obs, player=player)
        if not mask[intervention]:
            self.history.append(0)
            return base_act

        try:
            act = copy.deepcopy(base_act)
            mkt = act.setdefault("market", [])
            private = _get(obs, "private", {}) or {}
            shed = dict(_get(private, "shed", {}) or {})
            already_selling = {o[1] for o in mkt if len(o) > 1 and o[0] == "SELL"}

            # 1: ADVANCE_LAND_1
            if intervention == 1:
                if not any(len(o) > 0 and o[0] == "BUY_LAND" for o in mkt) and len(mkt) < 10:
                    mkt.insert(0, ["BUY_LAND"])

            # 2: ADVANCE_LAND_2
            elif intervention == 2:
                if not any(len(o) > 0 and o[0] == "BUY_LAND" for o in mkt) and len(mkt) < 10:
                    mkt.insert(0, ["BUY_LAND"])

            # 3: PURCHASE_LAND_3
            elif intervention == 3:
                if not any(len(o) > 0 and o[0] == "BUY_LAND" for o in mkt) and len(mkt) < 10:
                    mkt.insert(0, ["BUY_LAND"])

            # 4: DEFER_LAND_3
            elif intervention == 4:
                mkt = [o for o in mkt if not (len(o) > 0 and o[0] == "BUY_LAND")]

            # 5: HIRE_EARLY_SURGE
            elif intervention == 5:
                if len(mkt) < 8:
                    mkt.append(["HIRE"])
                    mkt.append(["HIRE"])

            # 6: CAP_LATE_HIRING
            elif intervention == 6:
                mkt = [o for o in mkt if not (len(o) > 0 and o[0] == "HIRE")]

            # 7: BUY_EXTRA_COW_EARLY
            elif intervention == 7:
                if len(mkt) < 10:
                    mkt.append(["BUY_ANIMAL", "COW", 1])

            # 8: BUY_EXTRA_SHEEP_EARLY
            elif intervention == 8:
                if len(mkt) < 10:
                    mkt.append(["BUY_ANIMAL", "SHEEP", 1])

            # 9: INVESTMENT_PAYBACK_CUTOFF
            elif intervention == 9:
                mkt = [o for o in mkt if not (len(o) > 0 and o[0] in ("BUY_ANIMAL", "BUY_LAND"))]

            # 10: TOWN_SHOP_ARBITRAGE (Step % 4 == 0 or 1)
            elif intervention == 10:
                for item in ("STRAWBERRY", "MILK", "WOOL"):
                    qty = shed.get(item, 0)
                    if qty >= 2 and item not in already_selling and len(mkt) < 10:
                        sell_qty = max(1, qty // 2)
                        mkt.append(["SELL", item, sell_qty])
                        already_selling.add(item)

            # 11: TOWN_CENTER_ARBITRAGE (Step % 12 == 0 or 1)
            elif intervention == 11:
                for item in MARKETABLE_COMMODITIES:
                    qty = shed.get(item, 0)
                    if qty >= 2 and item not in already_selling and len(mkt) < 10:
                        sell_qty = max(1, qty // 2)
                        mkt.append(["SELL", item, sell_qty])
                        already_selling.add(item)

            # 12: LIQUIDITY_BUFFER_SHIELD
            elif intervention == 12:
                mkt = [o for o in mkt if not (len(o) > 0 and o[0] in ("BUY_LAND", "BUY_ANIMAL", "HIRE"))]

            # 13: TERMINAL_STAGGERED_FLUSH
            elif intervention == 13:
                if step in (693, 694):
                    frac = 0.40
                elif step in (704, 705):
                    frac = 0.60
                else:
                    frac = 1.00

                for item in MARKETABLE_COMMODITIES:
                    qty = shed.get(item, 0)
                    if qty > 0 and item not in already_selling and len(mkt) < 10:
                        sell_qty = qty if frac >= 0.99 or qty == 1 else max(1, int(round(qty * frac)))
                        mkt.append(["SELL", item, sell_qty])
                        already_selling.add(item)

            act["market"] = mkt[:10]
            self.history.append(intervention)
            return act

        except Exception:
            self.history.append(0)
            return base_act
