# SPDX-License-Identifier: MIT
"""V33 Market Overlay: Price-Impact-Aware Sell Slot Reordering.

Applies price impact and demand urgency sorting to existing SELL orders generated
by the underlying expert route. Does NOT alter worker movement, planting, or capex.
Self-contained implementation of official Kaggriculture 1.32.7 market equations.
"""

from __future__ import annotations
import copy
import math
from typing import Any, Callable, Dict, List, Optional

PRICE_FLOOR = 1
MARKET_PARAMS = {
    "WHEAT": (25, 10000, 400, "sqrt", 0.8, "log", 0.2),
    "CARROT": (35, 10000, 450, "hinge", 1.0, "sqrt", 0.7),
    "TOMATO": (60, 10000, 200, "hinge", 0.4, "sqrt", 0.6),
    "STRAWBERRY": (120, 10000, 100, "sqrt", 0.7, "linear", 1.6),
    "MELON": (250, 10000, 300, "log", 0.2, "sq", 3.6),
    "EGG": (50, 10000, 332, "hinge", 0.4, "log", 0.2),
    "MILK": (160, 10000, 122, "sqrt", 0.6, "linear", 1.6),
    "WOOL": (200, 10000, 105, "log", 0.2, "sq", 3.2),
    "FERTILIZER": (100, 10000, 200, "linear", 0.4, "linear", 0.4),
}


def _get(value: Any, key: str, default: Any = None) -> Any:
    if isinstance(value, dict):
        return value.get(key, default)
    return getattr(value, key, default)


def _shape(name: str, value: float, scale: Optional[float] = None) -> float:
    val = max(0.0, float(value))
    if name == "linear":
        return val
    if name == "sq":
        return val * val
    if name == "sqrt":
        return math.sqrt(val)
    if name == "log":
        return math.log1p(val)
    if name == "log10":
        return math.log10(1.0 + val)
    if name == "hinge":
        if scale is None or scale <= 0:
            return val
        norm = val / scale
        return norm + 8.0 * max(0.0, norm - 1.0) ** 2
    raise ValueError(f"unknown market shape {name!r}")


def market_price(item: str, inventory: int) -> int:
    """Computes exact Kaggriculture 1.32.7 default price for an inventory level."""
    base, equilibrium, scale, below_func, below_target, above_func, above_target = MARKET_PARAMS[item]
    if inventory < equilibrium:
        amp = below_target * base / _shape(below_func, scale, scale)
        p = base + amp * _shape(below_func, equilibrium - inventory, scale)
    else:
        amp = above_target * base / _shape(above_func, scale, scale)
        p = base - amp * _shape(above_func, inventory - equilibrium, scale)
    return max(PRICE_FLOOR, int(round(p)))


def is_sell(order: Any) -> bool:
    return (
        isinstance(order, (list, tuple))
        and len(order) >= 3
        and order[0] == "SELL"
        and order[1] in MARKET_PARAMS
    )


def impact_score(obs: Dict[str, Any], order: Any) -> float:
    """Computes revenue delta impact: quantity * (current_quote - later_quote)."""
    if not is_sell(order):
        return float("-inf")
    item = str(order[1])
    try:
        qty = max(0, int(order[2]))
    except (TypeError, ValueError):
        return 0.0
    mkt = _get(obs, "market", {}) or {}
    inv = _get(mkt, "inventory", {}) or {}
    prices = _get(mkt, "prices", {}) or {}
    current_inv = int(_get(inv, item, 10000) or 10000)
    current_quote = float(_get(prices, item, market_price(item, current_inv)) or 0)
    later_quote = float(market_price(item, current_inv + qty))
    return float(qty) * max(0.0, current_quote - later_quote)


def reorder_sell_orders(obs: Dict[str, Any], action: Dict[str, Any], demand_alpha: float = 0.25) -> Dict[str, Any]:
    """Sorts only existing SELL orders in action['market']; preserves all BUY/HIRE orders."""
    act = copy.deepcopy(action) if isinstance(action, dict) else {}
    market = list(act.get("market") or [])
    if len(market) < 2:
        return act

    sells = []
    for idx, order in enumerate(market):
        if not is_sell(order):
            continue
        base_score = impact_score(obs, order)
        item = str(order[1])
        qty = max(0, int(order[2])) if len(order) > 2 else 0

        # Town demand urgency
        mkt_obs = _get(obs, "market", {}) or {}
        inv = _get(mkt_obs, "inventory", {}) or {}
        current_inv = int(_get(inv, item, 10000) or 10000)
        excess = max(0, current_inv + qty - 10000)
        urgency = min(1.0, excess / 500.0) if excess > 0 else 0.0
        final_score = base_score * (1.0 + demand_alpha * urgency)

        sells.append((final_score, -idx, copy.deepcopy(order)))

    if len(sells) < 2:
        return act

    # Sort descending by impact score
    sells.sort(reverse=True)
    ranked_iter = iter(row[2] for row in sells)
    act["market"] = [next(ranked_iter) if is_sell(o) else o for o in market]
    return act


def wrap_market_overlay(base_agent: Callable, demand_alpha: float = 0.25) -> Callable:
    """Wraps an agent callable with the price-impact market timing overlay."""
    def wrapped(obs: Dict[str, Any], configuration: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        raw_action = base_agent(obs, configuration)
        return reorder_sell_orders(obs, raw_action, demand_alpha=demand_alpha)
    return wrapped
