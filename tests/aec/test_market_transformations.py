# SPDX-License-Identifier: MIT
"""Test I — Market Transformations Library."""

from aec.market import transform_market_frontload, evaluate_town_cycle_signal
from aec.ir import build_economic_state


def test_frontload_reordering():
    orders = [
        ["HIRE"],
        ["BUY_LAND"],
        ["SELL", "STRAWBERRY", 10],
        ["BUY_PRODUCT", "WHEAT", 5],
        ["SELL", "WOOL", 4]
    ]
    
    reordered, status = transform_market_frontload(orders)
    
    # SELLs must be front-loaded to indices 0 and 1
    assert reordered[0][0] == "SELL"
    assert reordered[1][0] == "SELL"
    assert reordered[2][0] == "BUY_PRODUCT"
    assert reordered[3][0] in ("HIRE", "BUY_LAND")
    assert reordered[4][0] in ("HIRE", "BUY_LAND")


def test_town_cycle_signal_calculation(cash_deficit_obs):
    state = build_economic_state(cash_deficit_obs)
    signal = evaluate_town_cycle_signal(state, "WOOL")
    
    assert signal["item"] == "WOOL"
    assert "steps_to_tick" in signal
    assert "projected_price_at_tick" in signal
