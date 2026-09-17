# SPDX-License-Identifier: MIT
"""Authoritative Market Coupling Parity Suite (§12, §13).

Verifies exact numeric equality between the REAL ENGINE (kagsim) and the
AEC Counterfactual Simulator across all 15 mandatory market coupling cases.
Strictly uses authorized development seeds; zero access to holdout partitions.
"""

from __future__ import annotations

import pytest
from aec.counterfactual.parity_harness import TraceEquivalenceHarness

HARNESS = TraceEquivalenceHarness()
DEV_SEED = 100


def test_case_01_buy_then_sell_same_commodity():
    """CASE 1: BUY then SELL same commodity (intra-basket price escalation)."""
    res = HARNESS.run_turn_parity_comparison(
        seed=DEV_SEED,
        step=5,
        player_action={"market": [["BUY_PRODUCT", "WHEAT", 4], ["SELL", "WHEAT", 2]]},
        opponent_action={"market": []}
    )
    assert res.passed, res.summary()


def test_case_02_sell_then_buy_same_commodity():
    """CASE 2: SELL then BUY same commodity (intra-basket price depression)."""
    res = HARNESS.run_turn_parity_comparison(
        seed=DEV_SEED,
        step=5,
        player_action={"market": [["SELL", "WHEAT", 2], ["BUY_PRODUCT", "WHEAT", 4]]},
        opponent_action={"market": []}
    )
    assert res.passed, res.summary()


def test_case_03_buy_only():
    """CASE 3: BUY only."""
    res = HARNESS.run_turn_parity_comparison(
        seed=DEV_SEED,
        step=5,
        player_action={"market": [["BUY_PRODUCT", "WHEAT", 5]]},
        opponent_action={"market": []}
    )
    assert res.passed, res.summary()


def test_case_04_sell_only():
    """CASE 4: SELL only."""
    res = HARNESS.run_turn_parity_comparison(
        seed=DEV_SEED,
        step=5,
        player_action={"market": [["SELL", "WHEAT", 2]]},
        opponent_action={"market": []}
    )
    assert res.passed, res.summary()


def test_case_05_buy_a_then_sell_b():
    """CASE 5: BUY A then SELL B (cross-asset independence)."""
    res = HARNESS.run_turn_parity_comparison(
        seed=DEV_SEED,
        step=5,
        player_action={"market": [["BUY_PRODUCT", "FERTILIZER", 3], ["SELL", "WHEAT", 2]]},
        opponent_action={"market": []}
    )
    assert res.passed, res.summary()


def test_case_06_buy_a_then_sell_a():
    """CASE 6: BUY A then SELL A (identical volume round-trip)."""
    res = HARNESS.run_turn_parity_comparison(
        seed=DEV_SEED,
        step=5,
        player_action={"market": [["BUY_PRODUCT", "WHEAT", 3], ["SELL", "WHEAT", 3]]},
        opponent_action={"market": []}
    )
    assert res.passed, res.summary()


def test_case_07_multiple_buys_and_sell():
    """CASE 7: Multiple BUYs + SELL in same basket."""
    res = HARNESS.run_turn_parity_comparison(
        seed=DEV_SEED,
        step=5,
        player_action={"market": [
            ["BUY_PRODUCT", "WHEAT", 2],
            ["BUY_PRODUCT", "FERTILIZER", 2],
            ["SELL", "WHEAT", 2]
        ]},
        opponent_action={"market": []}
    )
    assert res.passed, res.summary()


def test_case_08_multiple_sells_and_buy():
    """CASE 8: Multiple SELLs + BUY in same basket."""
    res = HARNESS.run_turn_parity_comparison(
        seed=DEV_SEED,
        step=5,
        player_action={"market": [
            ["SELL", "WHEAT", 1],
            ["SELL", "WHEAT", 1],
            ["BUY_PRODUCT", "WHEAT", 3]
        ]},
        opponent_action={"market": []}
    )
    assert res.passed, res.summary()


def test_case_09_two_player_same_commodity_competition():
    """CASE 9: Two-player concurrent same-commodity trade."""
    res = HARNESS.run_turn_parity_comparison(
        seed=DEV_SEED,
        step=5,
        player_action={"market": [["BUY_PRODUCT", "WHEAT", 4]]},
        opponent_action={"market": [["BUY_PRODUCT", "WHEAT", 4]]}
    )
    assert res.passed, res.summary()


def test_case_10_no_opponent_collision():
    """CASE 10: Player trade with no opponent collision (opponent passes)."""
    res = HARNESS.run_turn_parity_comparison(
        seed=DEV_SEED,
        step=5,
        player_action={"market": [["BUY_PRODUCT", "WHEAT", 2], ["BUY_PRODUCT", "FERTILIZER", 2]]},
        opponent_action={"market": []}
    )
    assert res.passed, res.summary()


def test_case_11_opponent_simultaneous_demand_shock():
    """CASE 11: Opponent simultaneous heavy demand shock."""
    res = HARNESS.run_turn_parity_comparison(
        seed=DEV_SEED,
        step=5,
        player_action={"market": [["BUY_PRODUCT", "WHEAT", 2]]},
        opponent_action={"market": [["BUY_PRODUCT", "WHEAT", 20]]}
    )
    assert res.passed, res.summary()


def test_case_12_cash_limited_basket():
    """CASE 12: Cash-limited basket (order exhausts available funds)."""
    # At step 1, player cash is starting amount ($1000)
    # 50 fertilizer cost > $1000, so partial units execute cleanly
    res = HARNESS.run_turn_parity_comparison(
        seed=DEV_SEED,
        step=1,
        player_action={"market": [["BUY_PRODUCT", "FERTILIZER", 50]]},
        opponent_action={"market": []}
    )
    assert res.passed, res.summary()


def test_case_13_inventory_limited_basket():
    """CASE 13: Inventory-limited basket (attempting to sell more than shed holds)."""
    # At step 1, shed only holds starting wheat (2 units)
    # Ordering SELL 20 should only sell 2 units and halt
    res = HARNESS.run_turn_parity_comparison(
        seed=DEV_SEED,
        step=1,
        player_action={"market": [["SELL", "WHEAT", 20]]},
        opponent_action={"market": []}
    )
    assert res.passed, res.summary()


def test_case_14_capacity_limited_basket():
    """CASE 14: Capacity-limited basket (purchases near shed ceiling)."""
    res = HARNESS.run_turn_parity_comparison(
        seed=DEV_SEED,
        step=5,
        player_action={"market": [["BUY_PRODUCT", "WHEAT", 5]]},
        opponent_action={"market": []}
    )
    assert res.passed, res.summary()


def test_case_15_failed_later_order_after_earlier_mutation():
    """CASE 15: Failed later order after earlier order consumes liquidity."""
    res = HARNESS.run_turn_parity_comparison(
        seed=DEV_SEED,
        step=1,
        player_action={"market": [
            ["BUY_PRODUCT", "FERTILIZER", 10],  # Consumes nearly all cash
            ["BUY_PRODUCT", "WHEAT", 10]         # Insufficient cash; aborts cleanly
        ]},
        opponent_action={"market": []}
    )
    assert res.passed, res.summary()
