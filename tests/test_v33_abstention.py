# SPDX-License-Identifier: MIT
"""V33 Abstention Test: Verifies that selector defaults to R0_A7 abstention under uncertainty."""

import os
import sys
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from candidates.v33_meta_strategy.selector import RouteSelector


def test_default_abstention_on_normal_markets():
    selector = RouteSelector(decision_steps=(24, 48, 72))
    # Equilibrium baseline market
    obs = {
        "step": 24,
        "player": 0,
        "market": {"prices": {"WHEAT": 25, "CARROT": 35, "MILK": 160}, "inventory": {"WHEAT": 10000, "MILK": 10000}},
        "farms": [{"hands": []}, {"hands": [1, 2], "claimed": [0]}],
    }
    decision = selector.evaluate(obs)
    assert decision == "STAY_R0"
    assert selector.switches_made == 0


def test_abstention_on_missing_or_corrupt_data():
    selector = RouteSelector(decision_steps=(24, 48, 72))
    corrupt_obs = {"step": 24}
    decision = selector.evaluate(corrupt_obs)
    assert decision == "STAY_R0"
    assert selector.switches_made == 0
