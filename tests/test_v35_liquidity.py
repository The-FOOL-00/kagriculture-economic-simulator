# SPDX-License-Identifier: MIT
"""Kagriculture V35 Test Suite: Liquidity Safety & Cash Floor Verification."""

import os
import sys
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from candidates.v34_a7_tactical.liquidity_guard import LiquidityGuard
from candidates.v35_a7_opening.liquidity_model import solve_opening_liquidity


def test_liquidity_guard_safe():
    guard = LiquidityGuard(min_cash_floor_early=20.0)
    status = guard.evaluate_action_liquidity(
        current_cash=3000.0,
        step=0,
        active_workers=1,
        market_orders=[["BUY_PRODUCT", "WHEAT", 25], ["SELL", "WHEAT", 25]],
        prices={"WHEAT": 25.0},
    )
    assert status.is_safe is True
    assert status.rejection_reason == ""


def test_liquidity_guard_rejects_insolvency():
    guard = LiquidityGuard(min_cash_floor_early=50.0)
    status = guard.evaluate_action_liquidity(
        current_cash=60.0,
        step=0,
        active_workers=1,
        market_orders=[["BUY_PRODUCT", "WHEAT", 10]],  # Costs $250 -> cash drops to -$190
        prices={"WHEAT": 25.0},
    )
    assert status.is_safe is False
    assert "Intra-turn cash" in status.rejection_reason


def test_opening_liquidity_model_comparison():
    traj_30 = solve_opening_liquidity(wash_size=30)
    traj_25 = solve_opening_liquidity(wash_size=25)

    assert traj_25.min_cash_observed > traj_30.min_cash_observed
    assert traj_25.bounced_purchases_risk is False
