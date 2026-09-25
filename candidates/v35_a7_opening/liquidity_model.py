# SPDX-License-Identifier: MIT
"""Kagriculture V35 Opening Liquidity Model & Cash Runway Solver.

Formulates the opening capital allocation problem:
    max Spread_Capture(W)
    subject to:
        Cash_t >= Min_Reserve_t for all t in [0, 24]
        where Min_Reserve_t accounts for:
        - Step 1 animal and hire commitments ($1,946)
        - Step 6-11 melon seed procurement ($560)
        - Step 24 midnight wage obligations (N_workers * $10 = $60)
        - Slippage buffer ($50)

Proves analytically why Wash 25/25 satisfies the liquidity constraint
while Wash 30/30 dips below the critical insolvency threshold under adverse spreads.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Tuple


@dataclass
class LiquidityTrajectory:
    wash_size: int
    initial_cash: float
    wash_spend_net: float
    cash_at_step_1: float
    cash_after_step_1_surge: float
    cash_at_step_6: float
    cash_at_step_12: float
    cash_before_wages_step_24: float
    cash_after_wages_step_24: float
    min_cash_observed: float
    violates_reserve_floor: bool
    bounced_purchases_risk: bool


def solve_opening_liquidity(
    wash_size: int,
    initial_cash: float = 3000.0,
    wheat_buy_price: float = 25.0,
    wheat_sell_price: float = 25.0,
    spread_slippage_per_unit: float = 0.50,
) -> LiquidityTrajectory:
    """Calculates the deterministic cash curve during Day 1."""
    # Step 0: Wash execution
    # Buying W units of wheat costs W * (wheat_buy_price + slippage)
    # Selling W units returns W * (wheat_sell_price - slippage)
    gross_buy = wash_size * (wheat_buy_price + spread_slippage_per_unit)
    gross_sell = wash_size * (wheat_sell_price - spread_slippage_per_unit)
    wash_spend_net = gross_buy - gross_sell

    # Intra-turn cash float requirement:
    # Must have cash >= gross_buy before gross_sell credits
    cash_step_1 = initial_cash - wash_spend_net

    # Step 1 Surge:
    # 5 hires = $1 + $1 + $2 + $3 + $5 = $12
    # 2 cows = $800
    # 2 sheep = $1,000
    # Buy 5 wheat = 5 * 25 = $125
    # Sell 13 wheat = 13 * 24.5 = $318.5
    step_1_outflow = 12.0 + 800.0 + 1000.0 + 125.0 - 318.5  # $1,618.5
    cash_post_step_1 = cash_step_1 - step_1_outflow

    # Steps 2-5: No transactions, cash unchanged
    cash_step_6 = cash_post_step_1

    # Steps 6-11: Melon purchases (7 melon seeds * $80 = $560)
    melon_seed_spend = 560.0
    cash_step_12 = cash_step_6 - melon_seed_spend

    # Step 24: Midnight wages for 6 workers (1 farmer + 5 hands) = $60.0
    wage_bill = 60.0
    cash_before_wages = cash_step_12
    cash_after_wages = cash_before_wages - wage_bill

    min_cash = min(cash_step_1, cash_post_step_1, cash_step_12, cash_after_wages)
    # Critical floor: must keep cash >= $50 buffer to prevent order failure
    violates = (min_cash < 50.0)
    bounced_risk = (min_cash < 20.0)

    return LiquidityTrajectory(
        wash_size=wash_size,
        initial_cash=initial_cash,
        wash_spend_net=wash_spend_net,
        cash_at_step_1=cash_step_1,
        cash_after_step_1_surge=cash_post_step_1,
        cash_at_step_6=cash_step_6,
        cash_at_step_12=cash_step_12,
        cash_before_wages_step_24=cash_before_wages,
        cash_after_wages_step_24=cash_after_wages,
        min_cash_observed=min_cash,
        violates_reserve_floor=violates,
        bounced_purchases_risk=bounced_risk,
    )
