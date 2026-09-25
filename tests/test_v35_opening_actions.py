# SPDX-License-Identifier: MIT
"""Kagriculture V35 Test Suite: Opening Actions & Action Validity."""

import os
import sys
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from scripts.v32_common import load_agent
from candidates.v35_a7_opening.main import V35OpeningController


def test_opening_step0_wash():
    ctrl = V35OpeningController(wash_buy=25, wash_sell=25)
    obs = {
        "step": 0,
        "player": 0,
        "farms": [{"money": 3000.0, "farmer": [5, 5], "hands": []}, {"money": 3000.0, "farmer": [5, 5], "hands": []}],
        "private": {"shed": {}, "seeds": {}},
        "market": {"prices": {"WHEAT": 25.0}},
    }
    act = ctrl.act(obs)
    assert "market" in act
    assert act["market"] == [["BUY_PRODUCT", "WHEAT", 25], ["SELL", "WHEAT", 25]]
    assert ctrl.interventions_count == 1


def test_post_opening_a7_identity():
    ctrl = V35OpeningController(wash_buy=25, wash_sell=25)
    a7 = load_agent("E9_AST")

    obs = {
        "step": 1,
        "player": 0,
        "farms": [{"money": 1054.0, "farmer": [5, 4], "hands": []}, {"money": 1054.0, "farmer": [5, 4], "hands": []}],
        "private": {"shed": {"WHEAT": 17}, "seeds": {}},
        "market": {"prices": {"WHEAT": 25.0}},
    }
    cand_act = ctrl.act(obs)
    base_act = a7.act(obs)

    assert cand_act == base_act, "Controller diverged from A7 at step > 0!"
    assert ctrl.interventions_count == 0  # No interventions at step 1


def test_action_structure_legality():
    ctrl = V35OpeningController()
    obs = {"step": 0, "player": 0, "farms": [{"money": 3000.0}], "market": {}}
    act = ctrl.act(obs)

    assert isinstance(act, dict)
    assert "farmer" in act and isinstance(act["farmer"], list)
    assert "hands" in act and isinstance(act["hands"], list)
    assert "market" in act and isinstance(act["market"], list)
    assert len(act["market"]) <= 10
