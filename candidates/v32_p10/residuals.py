# SPDX-License-Identifier: MIT
"""Kagriculture V32 P10 Residual Candidates Library.

Defines candidate minimal, local policy overrides conditioned on observable regimes:
R01: OPPONENT_SELL_PREEMPT
R02: MARKET_QUANTITY_ADJUST
R02_B: OPPONENT_GLUT_TRIM
R03: LIQUIDITY_PROTECTION
R05: LOCAL_LABOR_PATCH
R07: TERMINAL_LOCAL_PATCH

Permanent IDs are assigned and never reused.
"""

from __future__ import annotations
import copy
from typing import Any, Dict, List, Optional, Tuple

try:
    from config import PRODUCTS
    from regime_detector import RegimeFeatures
except ImportError:
    from candidates.v32_p10.config import PRODUCTS
    from candidates.v32_p10.regime_detector import RegimeFeatures


class BaseResidual:
    residual_id: str = "R00"
    name: str = "BASE_RESIDUAL"
    causal_horizon: int = 4  # Steps required to evaluate causal outcome
    
    def can_trigger(self, features: RegimeFeatures, base_action: Dict[str, Any]) -> Tuple[bool, str]:
        """Returns (should_trigger, reason)."""
        return False, "Not implemented"

    def apply(self, base_action: Dict[str, Any], features: RegimeFeatures) -> Dict[str, Any]:
        """Generates the minimal local candidate action."""
        return copy.deepcopy(base_action)


class R01OpponentSellPreempt(BaseResidual):
    """R01: Preempts opponent market sales before price collapse."""
    residual_id = "R01"
    name = "OPPONENT_SELL_PREEMPT"
    causal_horizon = 8

    def can_trigger(self, features: RegimeFeatures, base_action: Dict[str, Any]) -> Tuple[bool, str]:
        if features.step == 0:
            return False, "Step 0 protected"
            
        if not (features.flags.get("OPPONENT_AGGRESSIVE_SELLER") or features.town_consumption_due_steps == 1):
            return False, "No sell pressure"
            
        mkt_orders = base_action.get("market") or []
        existing_sells = {o[1] for o in mkt_orders if o and o[0] == "SELL" and len(o) > 1}
        
        for prod in ("MILK", "WOOL", "MELON", "STRAWBERRY"):
            qty = features.player_shed_inventory.get(prod, 0)
            spot_px = features.spot_prices.get(prod, 0.0)
            if qty >= 4 and prod not in existing_sells and spot_px >= 30.0:
                return True, f"Preempt sell for {prod} (qty={qty}, px={spot_px:.1f})"
                
        return False, "No eligible un-sold inventory"

    def apply(self, base_action: Dict[str, Any], features: RegimeFeatures) -> Dict[str, Any]:
        action = copy.deepcopy(base_action)
        mkt = list(action.get("market") or [])
        existing_sells = {o[1] for o in mkt if o and o[0] == "SELL" and len(o) > 1}
        
        for prod in ("MILK", "WOOL", "MELON", "STRAWBERRY"):
            qty = features.player_shed_inventory.get(prod, 0)
            spot_px = features.spot_prices.get(prod, 0.0)
            if qty >= 4 and prod not in existing_sells and spot_px >= 30.0:
                sell_qty = min(qty, 12)
                if len(mkt) < 10:
                    mkt.append(["SELL", prod, sell_qty])
                break
                
        action["market"] = mkt[:10]
        return action


class R02MarketQuantityAdjust(BaseResidual):
    """R02: Adjusts sell order quantity or trims sales during temporary price gluts."""
    residual_id = "R02"
    name = "MARKET_QUANTITY_ADJUST"
    causal_horizon = 8

    def can_trigger(self, features: RegimeFeatures, base_action: Dict[str, Any]) -> Tuple[bool, str]:
        if features.step >= 710 or features.step == 0:
            return False, "Outside mid-game window"
            
        mkt = base_action.get("market") or []
        for o in mkt:
            if o and o[0] == "SELL" and len(o) >= 3:
                prod = o[1]
                qty = int(o[2])
                px = features.spot_prices.get(prod, 0.0)
                inv = features.market_inventory.get(prod, 0)
                if inv >= 40 and px < 15.0 and qty > 8 and features.player_cash > 500:
                    return True, f"Trim depressed sale of {prod} (px={px:.1f}, inv={inv})"
        return False, "No depressed sales"

    def apply(self, base_action: Dict[str, Any], features: RegimeFeatures) -> Dict[str, Any]:
        action = copy.deepcopy(base_action)
        mkt = []
        for o in action.get("market") or []:
            if o and o[0] == "SELL" and len(o) >= 3:
                prod = o[1]
                qty = int(o[2])
                px = features.spot_prices.get(prod, 0.0)
                inv = features.market_inventory.get(prod, 0)
                if inv >= 40 and px < 15.0 and qty > 8 and features.player_cash > 500:
                    mkt.append(["SELL", prod, max(4, qty // 2)])
                else:
                    mkt.append(o)
            else:
                mkt.append(o)
        action["market"] = mkt[:10]
        return action


class R02BOpponentGlutTrim(BaseResidual):
    """R02_B: Refined Opponent-Specific Glut Trim.
    
    Only trims or defers a sale if the GLUT was proven caused by OPPONENT selling
    (features.opp_recent_sales >= 8), protecting against self-induced inventory hold.
    """
    residual_id = "R02_B"
    name = "OPPONENT_GLUT_TRIM"
    causal_horizon = 8

    def can_trigger(self, features: RegimeFeatures, base_action: Dict[str, Any]) -> Tuple[bool, str]:
        if features.step >= 680 or features.step <= 10:
            return False, "Outside mid-game window"
            
        mkt = base_action.get("market") or []
        for o in mkt:
            if o and o[0] == "SELL" and len(o) >= 3:
                prod = o[1]
                qty = int(o[2])
                opp_sold = features.opp_recent_sales.get(prod, 0)
                px = features.spot_prices.get(prod, 0.0)
                inv = features.market_inventory.get(prod, 0)
                
                # Strict condition: Opponent must have actively dumped this exact product
                if opp_sold >= 8 and inv >= 30 and px < 25.0 and qty >= 8 and features.player_cash > 400:
                    return True, f"Opponent dumped {opp_sold} {prod} (mkt_inv={inv}, px={px:.1f})"
        return False, "No opponent-induced dump"

    def apply(self, base_action: Dict[str, Any], features: RegimeFeatures) -> Dict[str, Any]:
        action = copy.deepcopy(base_action)
        mkt = []
        for o in action.get("market") or []:
            if o and o[0] == "SELL" and len(o) >= 3:
                prod = o[1]
                qty = int(o[2])
                opp_sold = features.opp_recent_sales.get(prod, 0)
                inv = features.market_inventory.get(prod, 0)
                if opp_sold >= 8 and inv >= 30 and features.player_cash > 400:
                    # Defer half the lot to post-consumption clearing
                    mkt.append(["SELL", prod, max(4, qty // 2)])
                else:
                    mkt.append(o)
            else:
                mkt.append(o)
        action["market"] = mkt[:10]
        return action


class R03LiquidityProtection(BaseResidual):
    """R03: Suppresses non-critical purchases when liquid cash is dangerously low."""
    residual_id = "R03"
    name = "LIQUIDITY_PROTECTION"
    causal_horizon = 12

    def can_trigger(self, features: RegimeFeatures, base_action: Dict[str, Any]) -> Tuple[bool, str]:
        if features.step == 0:
            return False, "Step 0 protected"
            
        if features.player_cash < 120.0:
            mkt = base_action.get("market") or []
            for o in mkt:
                if o and o[0] in ("BUY_SEED", "BUY_ANIMAL", "BUY_LAND"):
                    return True, f"Low cash (${features.player_cash:.1f}) with purchase {o[0]}"
        return False, "Cash adequate"

    def apply(self, base_action: Dict[str, Any], features: RegimeFeatures) -> Dict[str, Any]:
        action = copy.deepcopy(base_action)
        mkt = []
        for o in action.get("market") or []:
            if o and o[0] in ("BUY_ANIMAL", "BUY_LAND"):
                continue
            mkt.append(o)
        action["market"] = mkt
        return action


class R05LocalLaborPatch(BaseResidual):
    """R05: Defers an individual hand hire when cash runway is tight and no chores exist."""
    residual_id = "R05"
    name = "LOCAL_LABOR_PATCH"
    causal_horizon = 24

    def can_trigger(self, features: RegimeFeatures, base_action: Dict[str, Any]) -> Tuple[bool, str]:
        if features.step <= 10 or features.step >= 650:
            return False, "Bootstrap and endgame labor protected"
            
        mkt = base_action.get("market") or []
        has_hire = any(o[0] == "HIRE" for o in mkt if o)
        if has_hire and features.player_cash < 100.0 and features.player_worker_count >= 6:
            return True, f"Tight cash (${features.player_cash:.1f}) with {features.player_worker_count} active workers"
        return False, "Labor conditions normal"

    def apply(self, base_action: Dict[str, Any], features: RegimeFeatures) -> Dict[str, Any]:
        action = copy.deepcopy(base_action)
        mkt = [o for o in action.get("market") or [] if o and o[0] != "HIRE"]
        action["market"] = mkt
        return action


class R07TerminalLocalPatch(BaseResidual):
    """R07: Liquidates residual shed goods in the final steps (716-718)."""
    residual_id = "R07"
    name = "TERMINAL_LOCAL_PATCH"
    causal_horizon = 4

    def can_trigger(self, features: RegimeFeatures, base_action: Dict[str, Any]) -> Tuple[bool, str]:
        if features.step < 716:
            return False, "Not terminal step"
            
        mkt = base_action.get("market") or []
        existing_sells = {o[1] for o in mkt if o and o[0] == "SELL" and len(o) > 1}
        for prod, qty in features.player_shed_inventory.items():
            if qty > 0 and prod not in existing_sells:
                return True, f"Terminal un-liquidated item: {prod} (qty={qty})"
        return False, "All shed items already being sold"

    def apply(self, base_action: Dict[str, Any], features: RegimeFeatures) -> Dict[str, Any]:
        action = copy.deepcopy(base_action)
        mkt = list(action.get("market") or [])
        existing_sells = {o[1] for o in mkt if o and o[0] == "SELL" and len(o) > 1}
        for prod, qty in features.player_shed_inventory.items():
            if qty > 0 and prod not in existing_sells and len(mkt) < 10:
                mkt.append(["SELL", prod, qty])
        action["market"] = mkt[:10]
        return action


RESIDUAL_REGISTRY = {
    "R01": R01OpponentSellPreempt,
    "R02": R02MarketQuantityAdjust,
    "R02_B": R02BOpponentGlutTrim,
    "R03": R03LiquidityProtection,
    "R05": R05LocalLaborPatch,
    "R07": R07TerminalLocalPatch,
}
