# SPDX-License-Identifier: MIT
"""Market Transformations Library (§14, §18, §19, §37)."""

from __future__ import annotations

import copy
from typing import Any, Dict, List, Optional, Tuple

from aec.config import PRODUCTS, ScientificStatus
from aec.ir.economic_state import EconomicState


def transform_dependency_aware_market_timing(
    orders: List[List[Any]],
    econ_state: Optional[Any] = None
) -> Tuple[List[List[Any]], ScientificStatus]:
    """Reorders market orders using causal DAG dependency closure.
    
    Invariants:
    1. Same-asset market coupling: if commodity X has both BUY_PRODUCT and SELL,
       their relative order is strictly preserved (never inverting BUY -> SELL).
    2. Uncoupled SELL orders (providing liquidity without endogenous price risk)
       are placed ahead of capital expenditures (HIRE, BUY_LAND, BUY_SEED).
    3. Preserves total order count and items.
    
    Status: EXPERIMENTAL (Candidate for EXP-AEC-003)
    """
    if not orders or len(orders) < 2:
        return list(orders), ScientificStatus.EXPERIMENTAL

    # 1. Identify commodities with multiple orders (same-asset coupling)
    asset_ops: Dict[str, List[str]] = {}
    for o in orders:
        if isinstance(o, (list, tuple)) and len(o) > 1:
            op = o[0]
            item = o[1]
            if op in ("BUY_PRODUCT", "SELL"):
                asset_ops.setdefault(item, []).append(op)

    coupled_items = {
        item for item, ops in asset_ops.items()
        if "BUY_PRODUCT" in ops and "SELL" in ops
    }

    # 2. Partition orders respecting causal coupling
    # Group A: Uncoupled SELL orders (safe for pre-impact liquidity)
    # Group B: Coupled orders and BUY_PRODUCT orders (preserving existing relative order)
    # Group C: Capital expenditure / other orders (HIRE, BUY_LAND, BUY_SEED, etc.)
    A: List[List[Any]] = []
    B: List[List[Any]] = []
    C: List[List[Any]] = []

    for o in orders:
        if not isinstance(o, (list, tuple)) or not o:
            continue
        op = o[0]
        item = o[1] if len(o) > 1 else None

        if op == "SELL":
            if item in coupled_items:
                # Coupled with BUY_PRODUCT of same asset: cannot frontload ahead of BUY
                B.append(list(o))
            else:
                # Uncoupled SELL: safe to promote for liquidity
                A.append(list(o))
        elif op == "BUY_PRODUCT":
            B.append(list(o))
        else:
            C.append(list(o))

    candidate = (A + B + C)[:10]
    return candidate, ScientificStatus.EXPERIMENTAL


def transform_market_frontload(
    orders: List[List[Any]]
) -> Tuple[List[List[Any]], ScientificStatus]:
    """[RETIRED / FALSIFIED IN EXP-AEC-002] Legacy unconditional front-loading.
    
    Status: FALSIFIED
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
    return (A + B + C)[:10], ScientificStatus.FALSIFIED


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
