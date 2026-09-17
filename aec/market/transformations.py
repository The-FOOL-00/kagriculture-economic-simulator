# SPDX-License-Identifier: MIT
"""Market Transformations Library (§14, §18, §19, §37)."""

from __future__ import annotations

import copy
from typing import Any, Dict, List, Optional, Tuple

from aec.config import PRODUCTS, ScientificStatus
from aec.ir.economic_state import EconomicState


def transform_market_frontload(
    orders: List[List[Any]]
) -> Tuple[List[List[Any]], ScientificStatus]:
    """Front-loads market orders into Group A (SELL), Group B (BUY_PRODUCT), Group C (Capital).
    
    Status: VERIFIED_SOURCE (reused from Teammate V3 frontload_core.py)
    """
    A, B, C = [], [], []
    for j, o in enumerate(orders):
        if not isinstance(o, (list, tuple)) or not o:
            continue
        op = o[0]
        if op == "SELL":
            # Check if part of buy-then-sell wash
            wash = any(p[0] == "BUY_PRODUCT" and len(p) > 1 and len(o) > 1 and p[1] == o[1] for p in orders[:j])
            (B if wash else A).append(list(o))
        elif op == "BUY_PRODUCT":
            B.append(list(o))
        else:
            C.append(list(o))
    return (A + B + C)[:10], ScientificStatus.VERIFIED_SOURCE


def evaluate_town_cycle_signal(
    econ_state: EconomicState,
    item: str
) -> Dict[str, Any]:
    """Calculates town-cycle signal: price, expected rebound, and absorption countdown.
    
    Status: PLAUSIBLE_UNPROVEN
    """
    step = econ_state.step
    steps_to_tick = econ_state.market.steps_to_town_tick
    cur_price = econ_state.market.get_price(item)
    absorption = econ_state.market.expected_absorption.get(item, 0)
    
    # Expected post-tick price bump if shop absorbs inventory
    projected_bump = 0
    if absorption > 0:
        projected_bump = min(15, absorption * 3)

    return {
        "item": item,
        "step": step,
        "steps_to_tick": steps_to_tick,
        "cur_price": cur_price,
        "projected_price_at_tick": cur_price + projected_bump,
        "absorption": absorption,
        "status": ScientificStatus.PLAUSIBLE_UNPROVEN.value,
    }
