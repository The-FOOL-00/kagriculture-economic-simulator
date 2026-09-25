# SPDX-License-Identifier: MIT
"""V33 Market Overlay Test: Verifies sell-order reordering safety and invariance of non-market actions."""

import os
import sys
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from candidates.v33_meta_strategy.market_overlay import reorder_sell_orders


def test_market_overlay_preserves_farmer_and_hands():
    obs = {
        "step": 100,
        "market": {"prices": {"WHEAT": 25, "MILK": 160}, "inventory": {"WHEAT": 10000, "MILK": 10000}}
    }
    action = {
        "farmer": ["MOVE", "NORTH"],
        "hands": [["HARVEST", 12], ["WATER", 14]],
        "market": [["BUY_ITEM", "SEED", 10], ["SELL", "WHEAT", 20], ["SELL", "MILK", 10]]
    }

    modified = reorder_sell_orders(obs, action)
    assert modified["farmer"] == ["MOVE", "NORTH"]
    assert modified["hands"] == [["HARVEST", 12], ["WATER", 14]]
    # BUY order must remain intact
    assert any(o[0] == "BUY_ITEM" for o in modified["market"])


def test_market_overlay_on_empty_market():
    obs = {"step": 0, "market": {}}
    action = {"farmer": ["PASS"], "hands": [], "market": []}
    modified = reorder_sell_orders(obs, action)
    assert modified["market"] == []
