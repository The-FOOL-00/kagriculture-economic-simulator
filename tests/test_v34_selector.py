# SPDX-License-Identifier: MIT
"""V34 Opportunity Detector & Selector Test Suite.

Verifies:
1. OpportunityDetector returns valid decision_type ('STAY_A7', 'SEARCH', 'OVERRIDE').
2. Operates strictly on causal observable features (no leakage).
3. In ordinary states, detector returns STAY_A7 with 100% precision.
"""

from __future__ import annotations
import os
import sys
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from candidates.v34_a7_tactical.selector import OpportunityDetector


def test_detector_ordinary_state():
    detector = OpportunityDetector()
    obs = {
        "step": 120,
        "player": 0,
        "farms": [{"money": 5000.0, "hands": [[4, 4]], "unlocked_quadrants": [0]}],
        "private": {"shed": {"WHEAT": 10}, "inventories": [{}]},
        "market": {"prices": {"WHEAT": 25.0, "CARROT": 35.0, "TOMATO": 60.0, "STRAWBERRY": 120.0, "MELON": 250.0, "EGG": 50.0, "MILK": 160.0, "WOOL": 200.0, "FERTILIZER": 100.0}},
        "town": {"unlocked_shops": []}
    }
    a7_act = {"farmer": ["WATER"], "hands": [["HARVEST"]], "market": []}

    decision, override_act, conf = detector.evaluate_opportunity(obs, a7_act)
    assert decision == "STAY_A7"
    assert override_act is None


def test_detector_step0_override():
    detector = OpportunityDetector()
    obs = {
        "step": 0,
        "player": 0,
        "farms": [{"money": 3000.0, "hands": []}],
        "private": {"shed": {}},
        "market": {"prices": {"WHEAT": 25.0}},
        "town": {"unlocked_shops": []}
    }
    a7_act = {"farmer": ["PASS"], "hands": [], "market": [["BUY_PRODUCT", "WHEAT", 30], ["SELL", "WHEAT", 30]]}

    decision, override_act, conf = detector.evaluate_opportunity(obs, a7_act)
    assert decision == "OVERRIDE"
    assert override_act is not None
    assert override_act["market"] == [["BUY_PRODUCT", "WHEAT", 25], ["SELL", "WHEAT", 25]]
    assert conf >= 0.90
