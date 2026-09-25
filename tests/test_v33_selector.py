# SPDX-License-Identifier: MIT
"""V33 Selector Test: Verifies classification logic and threshold behavior."""

import os
import sys
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from candidates.v33_meta_strategy.selector import RouteSelector


def test_selector_feature_extraction():
    selector = RouteSelector()
    obs = {
        "step": 24,
        "player": 0,
        "market": {"prices": {"WHEAT": 22, "CARROT": 30, "MILK": 170}, "inventory": {"WHEAT": 10500, "MILK": 9800}},
        "farms": [{"hands": [1, 2, 3, 4], "claimed": [0]}, {"hands": [1, 2], "claimed": [0, 1]}],
    }
    feats = selector.extract_observable_features(obs)
    assert feats["step"] == 24.0
    assert feats["wheat_price"] == 22.0
    assert feats["opp_visible_hands"] == 2.0
    assert feats["opp_claimed_quads"] == 2.0
    assert feats["crop_basket_index"] > 0.0


def test_selector_confidence_threshold_gating():
    # If gain is below threshold, must STAY on R0
    selector = RouteSelector(decision_steps=(24,), min_gain_threshold=5000.0)
    obs = {
        "step": 24,
        "player": 0,
        "market": {"prices": {"WHEAT": 18}, "inventory": {"WHEAT": 11000}},
        "farms": [{"hands": []}, {"hands": [1, 2], "claimed": [0]}],
    }
    decision = selector.evaluate(obs)
    assert decision == "STAY_R0"
