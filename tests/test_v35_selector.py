# SPDX-License-Identifier: MIT
"""Kagriculture V35 Test Suite: Opportunity Detector & Selector Logic."""

import os
import sys
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from candidates.v34_a7_tactical.selector import OpportunityDetector


def test_selector_step0_override():
    detector = OpportunityDetector()
    obs = {
        "step": 0,
        "player": 0,
        "farms": [{"money": 3000.0, "hands": []}],
        "market": {"prices": {"WHEAT": 25.0}},
    }
    a7_action = {"farmer": ["PASS"], "hands": [], "market": [["BUY_PRODUCT", "WHEAT", 30], ["SELL", "WHEAT", 30]]}

    decision, override_act, conf = detector.evaluate_opportunity(obs, a7_action)

    assert decision == "OVERRIDE"
    assert override_act is not None
    assert override_act["market"] == [["BUY_PRODUCT", "WHEAT", 25], ["SELL", "WHEAT", 25]]
    assert conf >= 0.90


def test_selector_midgame_stay_a7():
    detector = OpportunityDetector()
    obs = {
        "step": 100,
        "player": 0,
        "farms": [{"money": 5000.0, "hands": []}],
        "market": {"prices": {"WHEAT": 25.0}},
    }
    a7_action = {"farmer": ["PASS"], "hands": [], "market": []}

    decision, override_act, conf = detector.evaluate_opportunity(obs, a7_action)
    assert decision == "STAY_A7"
    assert override_act is None
