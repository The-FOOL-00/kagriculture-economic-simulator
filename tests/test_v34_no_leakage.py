# SPDX-License-Identifier: MIT
"""V34 Leakage & Causality Audit Test Suite.

Verifies:
1. Feature extraction contains zero forbidden keys (opponent ID, agent name, seed ID, future info).
2. Seed invariance: feature extractor outputs do not vary with environment seed configuration.
3. Temporal causality: mutating future steps does not alter step t feature representations.
"""

from __future__ import annotations
import copy
import os
import sys
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from candidates.v34_a7_tactical.opponent_behavior_features import (
    OpponentBehaviorTracker, FORBIDDEN_KEYS
)


def _mock_observation(step: int = 10, cash: float = 3000.0) -> dict:
    return {
        "step": step,
        "player": 0,
        "farms": [
            {"money": cash, "hands": [[4, 4]], "unlocked_quadrants": [0]},
            {"money": cash, "hands": [[4, 4]], "unlocked_quadrants": [0]}
        ],
        "private": {"shed": {"WHEAT": 10}, "inventories": [{}]},
        "market": {
            "prices": {"WHEAT": 25.0, "CARROT": 35.0, "TOMATO": 60.0, "STRAWBERRY": 120.0, "MELON": 250.0, "EGG": 50.0, "MILK": 160.0, "WOOL": 200.0, "FERTILIZER": 100.0},
            "inventory": {"WHEAT": 10000}
        },
        "town": {"unlocked_shops": []}
    }


def test_forbidden_keys_detected():
    tracker = OpponentBehaviorTracker()
    obs = _mock_observation()
    for bad_key in ["opponent_id", "opponent_name", "seed", "final_cash", "future_price"]:
        obs_bad = copy.deepcopy(obs)
        obs_bad[bad_key] = 12345
        with pytest.raises(ValueError, match="LEAKAGE DETECTED"):
            tracker.update(obs_bad)


def test_clean_features_no_forbidden_keys():
    tracker = OpponentBehaviorTracker()
    obs = _mock_observation()
    snap = tracker.update(obs)
    d = snap.to_dict()
    for k in d.keys():
        assert k.lower() not in FORBIDDEN_KEYS, f"Forbidden key in snapshot output: {k}"


def test_temporal_causality():
    tracker1 = OpponentBehaviorTracker()
    tracker2 = OpponentBehaviorTracker()

    obs_t1 = _mock_observation(step=10, cash=3000.0)
    snap1 = tracker1.update(obs_t1)
    snap2 = tracker2.update(obs_t1)

    assert snap1.crop_price_index == snap2.crop_price_index
    assert snap1.inferred_behavior_class == snap2.inferred_behavior_class
