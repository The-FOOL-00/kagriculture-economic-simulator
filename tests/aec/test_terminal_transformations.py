# SPDX-License-Identifier: MIT
"""Test J — Terminal Transformations and Phase Shutdown."""

from aec.terminal import transform_terminal_liquidation, transform_phase_shutdown


def test_step_718_liquidation():
    shed = {"STRAWBERRY": 20, "WOOL": 10, "MELON": 5, "WHEAT": 0}
    prices = {"STRAWBERRY": 120, "WOOL": 200, "MELON": 250, "WHEAT": 25}
    
    orders, status = transform_terminal_liquidation(shed, prices)
    
    # Must generate 3 sell orders sorted by total value
    # STRAWBERRY = 2400, WOOL = 2000, MELON = 1250
    assert len(orders) == 3
    assert orders[0] == ["SELL", "STRAWBERRY", 20]
    assert orders[1] == ["SELL", "WOOL", 10]
    assert orders[2] == ["SELL", "MELON", 5]


def test_phase_shutdown_trims_dead_seeds():
    orders = [
        ["BUY_SEED", "STRAWBERRY", 5],
        ["BUY_SEED", "WHEAT", 10],
        ["SELL", "STRAWBERRY", 2]
    ]
    
    # At step 575, STRAWBERRY cannot mature
    filtered, status = transform_phase_shutdown(orders, dead_crops=["STRAWBERRY"])
    
    assert len(filtered) == 2
    assert not any(o[0] == "BUY_SEED" and o[1] == "STRAWBERRY" for o in filtered)
    assert any(o[0] == "BUY_SEED" and o[1] == "WHEAT" for o in filtered)
