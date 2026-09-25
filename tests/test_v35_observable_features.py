# SPDX-License-Identifier: MIT
"""Kagriculture V35 Test Suite: Observable Feature Extractor."""

import os
import sys
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from candidates.v34_a7_tactical.opponent_behavior_features import (
    OpponentBehaviorTracker, FORBIDDEN_KEYS
)


def test_tracker_feature_extraction():
    tracker = OpponentBehaviorTracker()
    obs = {
        "step": 0,
        "player": 0,
        "farms": [
            {"money": 3000.0, "hands": [], "unlocked_quadrants": [1]},
            {"money": 3000.0, "hands": [], "unlocked_quadrants": [1]},
        ],
        "market": {
            "prices": {"WHEAT": 25.0, "CARROT": 35.0, "TOMATO": 60.0, "MELON": 250.0}
        }
    }
    snap = tracker.update(obs)
    assert snap.step == 0
    assert snap.opp_visible_hands == 0
    assert abs(snap.current_prices["WHEAT"] - 25.0) < 0.01

    vec = snap.to_feature_vector()
    assert len(vec) > 10
    assert not any(val is None for val in vec)


def test_forbidden_keys_exception():
    tracker = OpponentBehaviorTracker()
    for bad_key in ["seed", "opponent_id", "future_price", "final_cash"]:
        obs = {
            "step": 0,
            bad_key: "illegal_value",
            "farms": [{}, {}],
            "market": {}
        }
        with pytest.raises(ValueError, match="LEAKAGE DETECTED"):
            tracker.update(obs)
