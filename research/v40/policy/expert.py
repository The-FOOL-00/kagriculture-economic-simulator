# SPDX-License-Identifier: MIT
"""Kagriculture V40 Expert Economic Policy.

Synthesizes the strongest deterministic economic intelligence in the codebase:
1. V35 25/25 Wheat Opening: preserves liquidity floor at Step 10 ($129+ vs $4).
2. A7 Physical Chore Chassis: flawless, tick-exact crop watering and feeding routines.
3. V39 Liquidation Guard: preemptive selling of perishable stock (Strawberries, Milk, Wool)
   at steps 693-694 before opponent dumps crash market spot prices.
4. Counterfactual Headroom Exploitation:
   - Accelerates land expansion on Day 12 (step 288) when liquid capital > $15k.
   - Opportunistic front-running when high-value goods reach market peaks (> $35).
   - Strict liquidity preservation preventing bankruptcy defaults.
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
if os.path.join(REPO_ROOT, "scripts") not in sys.path:
    sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))

from candidates.v35_a7_opening.main import V35OpeningController
from research.v40.policy.actions import get_macro_action_mask, NUM_MACRO_ACTIONS


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


class V40ExpertPolicy:
    """Deterministic Expert Strategic Controller and Macro Label Generator."""

    def __init__(self):
        self.v35_controller = V35OpeningController(wash_buy=25, wash_sell=25)

    def reset(self):
        self.v35_controller.reset()

    def get_base_action(self, obs: Dict[str, Any], cfg: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Returns the base V35 baseline action."""
        try:
            return self.v35_controller.act(obs, cfg)
        except Exception:
            return {"farmer": ["PASS"], "hands": [], "market": []}

    def choose_expert_macro_action(self, obs: Dict[str, Any], player: int = 0) -> int:
        """Selects the optimal economic macro action ID (0..15) based on exact state rules."""
        step = int(_get(obs, "step", 0) or 0)
        farms = list(_get(obs, "farms", []) or [])
        my_farm = farms[player] if farms and player < len(farms) else {}
        cash = _safe_float(_get(my_farm, "money", 0.0))
        unlocked_quads = len(list(_get(my_farm, "unlocked_quadrants", [0]) or [0]))

        private = _get(obs, "private", {}) or {}
        shed = dict(_get(private, "shed", {}) or {})
        market = _get(obs, "market", {}) or {}
        prices = dict(_get(market, "prices", {}) or {})

        mask = get_macro_action_mask(obs, player=player)

        # 1. Terminal Full Liquidation (Steps 693-694, generalized to steps >= 690)
        if step in (692, 693, 694) and mask[13]:
            # If we hold perishable goods in shed, flush immediately!
            if any(shed.get(item, 0) > 0 for item in ("STRAWBERRY", "MILK", "WOOL", "MELON")):
                return 13  # TERMINAL_FULL_LIQUIDATION

        # 2. End-of-game general liquidation (Steps 710..718)
        if step >= 710 and mask[13]:
            if any(shed.get(item, 0) > 0 for item in ("STRAWBERRY", "MILK", "WOOL", "MELON", "CARROT", "TOMATO", "EGG")):
                return 13

        # 3. Emergency Liquidity Preservation
        if cash < 250.0 and step < 680 and mask[14]:
            return 14  # PRESERVE_LIQUIDITY_BUFFER

        # 4. Mid-Game Counterfactual Land Expansion (RLX2-F5 Discovery: Step 288 +$11k alpha)
        if 280 <= step <= 312 and unlocked_quads < 4 and cash >= 12000.0 and mask[1]:
            return 1  # EXPAND_LAND_NOW

        # 5. Market Opportunistic Front-Running (High spot price peak)
        if step < 690 and mask[10]:
            has_peak_goods = any(
                shed.get(item, 0) >= 3 and _safe_float(prices.get(item, 0)) >= 38.0
                for item in ("MILK", "WOOL", "STRAWBERRY", "MELON")
            )
            if has_peak_goods:
                return 10  # MARKET_FRONT_RUN_SELL

        # 6. Aggressive Reinvestment (If massive cash surplus early)
        if step < 400 and cash >= 8000.0 and mask[15]:
            return 15  # AGGRESSIVE_REINVEST

        # Default: Base expert choreography
        return 0  # BASELINE_EXPERT

    def act(self, obs: Dict[str, Any], cfg: Optional[Dict[str, Any]] = None, player: int = 0) -> Dict[str, Any]:
        """Generates full executable action with targeted economic enhancements."""
        step = int(_get(obs, "step", 0) or 0)
        base_act = self.get_base_action(obs, cfg)

        # Apply V39 liquidation guard at steps 693-694
        if step in (693, 694):
            private = _get(obs, "private", {}) or {}
            shed = dict(_get(private, "shed", {}) or {})
            if shed:
                act = copy.deepcopy(base_act)
                mkt = act.setdefault("market", [])
                already_selling = {o[1] for o in mkt if len(o) > 1 and o[0] == "SELL"}
                for item in ("STRAWBERRY", "MILK", "WOOL", "MELON"):
                    qty = shed.get(item, 0)
                    if qty > 0 and item not in already_selling and len(mkt) < 10:
                        mkt.append(["SELL", item, qty])
                return act

        return base_act
