# SPDX-License-Identifier: MIT
"""V34 Observable Features Test Suite.

Verifies:
1. Feature extraction produces fixed-length, finite, float vectors.
2. Inferred behavior classification handles edge cases (e.g. extreme price swings) gracefully.
3. Tracker state updates and maintains windowed history correctly.
"""

from __future__ import annotations
import numpy as np
import os
import sys
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from candidates.v34_a7_tactical.opponent_behavior_features import (
    OpponentBehaviorTracker, OpponentBehaviorSnapshot, BASE_PRICES
)


def test_feature_vector_validity():
    tracker = OpponentBehaviorTracker()
    obs = {
        "step": 48,
        "player": 0,
        "farms": [
            {"money": 4500.0, "hands": [[4, 4], [4, 5]], "unlocked_quadrants": [0]},
            {"money": 2100.0, "hands": [[4, 4]], "unlocked_quadrants": [0, 1]}
        ],
        "private": {"shed": {"WHEAT": 20}, "inventories": [{}, {}]},
        "market": {
            "prices": BASE_PRICES,
            "inventory": {"WHEAT": 10000}
        },
        "town": {"unlocked_shops": []}
    }

    snap = tracker.update(obs)
    vec = snap.to_feature_vector()

    assert isinstance(vec, np.ndarray)
    assert np.all(np.isfinite(vec))
    assert len(vec) == 17  # 8 core features + 9 commodity price ratios
    assert snap.inferred_behavior_class == "BALANCED_REGIME"


def test_saturation_detection():
    tracker = OpponentBehaviorTracker()
    # Simulate a sudden wheat/crop collapse over 5 turns
    for t in range(5):
        wheat_p = 25.0 - t * 4.0  # Drops 25 -> 21 -> 17 -> 13 -> 9
        obs = {
            "step": t,
            "player": 0,
            "farms": [{"money": 3000.0}, {"money": 3000.0}],
            "private": {"shed": {}},
            "market": {"prices": {**BASE_PRICES, "WHEAT": wheat_p, "CARROT": 20.0}},
            "town": {"unlocked_shops": []}
        }
        snap = tracker.update(obs)

    # By turn 4, crop sell pressure should be recognized
    assert snap.crop_sell_pressure > 0.0
    assert snap.inferred_behavior_class in ("HIGH_CROP_SATURATION", "BALANCED_REGIME")
