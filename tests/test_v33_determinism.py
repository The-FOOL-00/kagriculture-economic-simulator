# SPDX-License-Identifier: MIT
"""V33 Determinism Test: Verifies repeatable, deterministic routing decisions."""

import copy
import os
import sys
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from candidates.v33_meta_strategy.selector import RouteSelector


def test_selector_determinism():
    s1 = RouteSelector()
    s2 = RouteSelector()

    obs = {
        "step": 24,
        "player": 0,
        "market": {"prices": {"WHEAT": 18, "CARROT": 28, "MILK": 170}, "inventory": {"WHEAT": 11500, "MILK": 9500}},
        "farms": [{"hands": []}, {"hands": [1, 2], "claimed": [0, 1]}],
    }

    d1 = s1.evaluate(copy.deepcopy(obs))
    d2 = s2.evaluate(copy.deepcopy(obs))

    assert d1 == d2, f"Determinism failure: {d1} != {d2}"
    assert s1.extract_observable_features(obs) == s2.extract_observable_features(obs)
