# SPDX-License-Identifier: MIT
"""Terminal Transformations Library (§17, §27, §37)."""

from __future__ import annotations

import copy
from typing import Any, Dict, List, Optional, Tuple

from aec.config import FINAL_STEP, MAX_MARKET_ORDERS, PRODUCTS, ScientificStatus


def transform_terminal_liquidation(
    shed_inventory: Dict[str, int],
    market_prices: Dict[str, int]
) -> Tuple[List[List[Any]], ScientificStatus]:
    """Generates authoritative step-718 collision-aware liquidation market orders.
    
    Reuses verified ARCH-003 logic:
    - SELL only
    - PRODUCTS only
    - Positively available shed quantities
    - Maximum 10 orders
    - Sorted by total order value (qty * price) descending
    
    Status: REUSED_SAFETY
    """
    candidates = []
    for item in PRODUCTS:
        qty = int(shed_inventory.get(item, 0) or 0)
        if qty > 0:
            price = int(market_prices.get(item, 1) or 1)
            total_val = qty * price
            candidates.append((total_val, item, qty))

    # Sort descending by total coin value
    candidates.sort(key=lambda c: -c[0])

    orders = []
    for _, item, qty in candidates[:MAX_MARKET_ORDERS]:
        orders.append(["SELL", item, qty])

    return orders, ScientificStatus.REUSED_SAFETY


def transform_phase_shutdown(
    market_orders: List[List[Any]],
    dead_crops: List[str]
) -> Tuple[List[List[Any]], ScientificStatus]:
    """Trims dead-investment seed orders that cannot mature before game end.
    
    Status: VERIFIED_SOURCE
    """
    dead_set = set(dead_crops)
    filtered = []
    for o in market_orders:
        if isinstance(o, (list, tuple)) and len(o) >= 2 and o[0] == "BUY_SEED" and o[1] in dead_set:
            continue  # Exclude seed purchase
        filtered.append(list(o))

    return filtered[:MAX_MARKET_ORDERS], ScientificStatus.VERIFIED_SOURCE
