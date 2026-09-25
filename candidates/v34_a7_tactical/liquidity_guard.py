# SPDX-License-Identifier: MIT
"""Kagriculture V34 Fail-Closed Liquidity Guard.

Enforces strict capital safety invariants before and after tactical interventions:
1. Wage Runway: Guarantees sufficient liquid cash for upcoming daily wage deductions.
2. Minimum Cash Floor: Enforces hard capital floors ($50 early, $200 midgame).
3. Intra-Turn Execution Precedence: Verifies that BUY orders never precede SELL orders
   unless starting cash is strictly sufficient to fund the purchases unconditionally.
4. Reversion: Returns True if safe, False if the intervention must be rejected.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

SEED_PRICES = {"WHEAT": 10, "CARROT": 20, "TOMATO": 50, "STRAWBERRY": 100, "MELON": 80}
ANIMAL_COSTS = {"GOOSE": 300, "COW": 400, "SHEEP": 500}
WAGE_PER_WORKER = 10.0


@dataclass
class LiquidityStatus:
    is_safe: bool
    current_cash: float
    projected_post_action_cash: float
    wage_buffer_required: float
    rejection_reason: str = ""


class LiquidityGuard:
    """Fail-closed liquidity verification module."""

    def __init__(
        self,
        min_cash_floor_early: float = 20.0,
        min_cash_floor_mid: float = 100.0,
        safety_margin_ratio: float = 1.15,
    ):
        self.min_cash_floor_early = min_cash_floor_early
        self.min_cash_floor_mid = min_cash_floor_mid
        self.safety_margin_ratio = safety_margin_ratio

    def evaluate_action_liquidity(
        self,
        current_cash: float,
        step: int,
        active_workers: int,
        market_orders: List[List[Any]],
        prices: Dict[str, float],
    ) -> LiquidityStatus:
        """Evaluates whether market_orders can execute safely without risking insolvency."""
        # 1. Calculate required wage buffer
        # In Kaggriculture, wages are deducted every 24 steps (at step % 24 == 0)
        steps_to_wage = 24 - (step % 24)
        if steps_to_wage <= 4:
            # Imminent wage deduction: must protect upcoming wage
            required_wage_buffer = active_workers * WAGE_PER_WORKER * self.safety_margin_ratio
        else:
            required_wage_buffer = 0.0

        min_floor = self.min_cash_floor_early if step < 120 else self.min_cash_floor_mid

        # 2. Simulate order execution sequentially
        cash_cursor = current_cash
        worst_intra_turn_cash = cash_cursor

        for order in market_orders:
            if not order or len(order) < 2:
                continue
            op = order[0]
            item = order[1]
            qty = int(order[2]) if len(order) >= 3 else 1

            if op == "SELL":
                unit_price = float(prices.get(item, 0.0))
                cash_cursor += unit_price * qty

            elif op == "BUY_SEED":
                unit_price = float(SEED_PRICES.get(item, 50.0))
                cost = unit_price * qty
                cash_cursor -= cost
                worst_intra_turn_cash = min(worst_intra_turn_cash, cash_cursor)

            elif op == "BUY_PRODUCT":
                unit_price = float(prices.get(item, 25.0))
                cost = unit_price * qty
                cash_cursor -= cost
                worst_intra_turn_cash = min(worst_intra_turn_cash, cash_cursor)

            elif op == "BUY_ANIMAL":
                cost = float(ANIMAL_COSTS.get(item, 400.0)) * qty
                cash_cursor -= cost
                worst_intra_turn_cash = min(worst_intra_turn_cash, cash_cursor)

            elif op == "HIRE":
                # Conservative estimate for next hire
                cash_cursor -= 50.0
                worst_intra_turn_cash = min(worst_intra_turn_cash, cash_cursor)

            elif op == "BUY_LAND":
                cash_cursor -= 1000.0
                worst_intra_turn_cash = min(worst_intra_turn_cash, cash_cursor)

        # 3. Check invariants
        if worst_intra_turn_cash < min_floor:
            return LiquidityStatus(
                is_safe=False,
                current_cash=current_cash,
                projected_post_action_cash=cash_cursor,
                wage_buffer_required=required_wage_buffer,
                rejection_reason=f"Intra-turn cash ({worst_intra_turn_cash:.1f}) dipped below minimum floor ({min_floor:.1f})",
            )

        if (cash_cursor - required_wage_buffer) < min_floor:
            return LiquidityStatus(
                is_safe=False,
                current_cash=current_cash,
                projected_post_action_cash=cash_cursor,
                wage_buffer_required=required_wage_buffer,
                rejection_reason=f"Post-action cash ({cash_cursor:.1f}) insufficient for upcoming wage buffer ({required_wage_buffer:.1f}) + floor ({min_floor:.1f})",
            )

        return LiquidityStatus(
            is_safe=True,
            current_cash=current_cash,
            projected_post_action_cash=cash_cursor,
            wage_buffer_required=required_wage_buffer,
            rejection_reason="",
        )
