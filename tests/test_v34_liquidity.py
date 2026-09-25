# SPDX-License-Identifier: MIT
"""V34 Liquidity Guard Test Suite.

Verifies:
1. Rejects orders causing intra-turn cash starvation.
2. Enforces required wage buffers within 4 turns of day boundary (step % 24 == 0).
3. Permits safe orders that preserve cash floors and wage runways.
"""

from __future__ import annotations
import os
import sys
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from candidates.v34_a7_tactical.liquidity_guard import LiquidityGuard


def test_intra_turn_cash_starvation_rejected():
    guard = LiquidityGuard(min_cash_floor_early=50.0)
    # Farm has $60. Orders try to BUY $100 before selling $200.
    # Intra-turn cash drops: $60 - $100 = -$40 < $50 floor -> REJECT
    orders = [
        ["BUY_PRODUCT", "WHEAT", 4],  # 4 * 25 = $100
        ["SELL", "WHEAT", 10],       # 10 * 25 = $250
    ]
    status = guard.evaluate_action_liquidity(
        current_cash=60.0,
        step=10,
        active_workers=3,
        market_orders=orders,
        prices={"WHEAT": 25.0},
    )
    assert not status.is_safe
    assert "Intra-turn cash" in status.rejection_reason


def test_precedent_sell_order_accepted():
    guard = LiquidityGuard(min_cash_floor_early=50.0)
    # Reversing order: SELL first then BUY.
    # $60 + $250 = $310 -> $310 - $100 = $210 >= $50 floor -> SAFE
    orders = [
        ["SELL", "WHEAT", 10],       # +$250
        ["BUY_PRODUCT", "WHEAT", 4],  # -$100
    ]
    status = guard.evaluate_action_liquidity(
        current_cash=60.0,
        step=10,
        active_workers=3,
        market_orders=orders,
        prices={"WHEAT": 25.0},
    )
    assert status.is_safe
    assert status.projected_post_action_cash == 210.0


def test_wage_runway_protection():
    guard = LiquidityGuard(min_cash_floor_early=20.0)
    # At step 22 (2 steps before wage at 24), 5 workers need 5 * 10 * 1.15 = $57.50 buffer.
    # Starting cash $65. Buying $20 seed leaves $45 cash. $45 - $57.50 = -$12.50 < $20 floor -> REJECT
    orders = [["BUY_SEED", "WHEAT", 2]]  # -$20
    status = guard.evaluate_action_liquidity(
        current_cash=65.0,
        step=22,
        active_workers=5,
        market_orders=orders,
        prices={"WHEAT": 25.0},
    )
    assert not status.is_safe
    assert "wage buffer" in status.rejection_reason
