# SPDX-License-Identifier: MIT
"""Kagriculture V35 Test Suite: Terminal Liquidation & Step 718 Consistency."""

import os
import sys
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from scripts.v32_common import load_agent
from candidates.v35_a7_opening.main import V35OpeningController


def test_terminal_step_718_identity():
    ctrl = V35OpeningController()
    a7 = load_agent("E9_AST")

    obs = {
        "step": 718,
        "player": 0,
        "farms": [{"money": 100000.0, "farmer": [5, 5], "hands": []}, {"money": 90000.0, "farmer": [0, 0], "hands": []}],
        "private": {"shed": {"MELON": 50, "WHEAT": 100, "STRAWBERRY": 20}, "seeds": {}},
        "market": {"prices": {"MELON": 250.0, "WHEAT": 25.0, "STRAWBERRY": 120.0}},
    }
    cand_act = ctrl.act(obs)
    base_act = a7.act(obs)

    assert cand_act == base_act, "V35 diverged from A7 at terminal step 718!"
    assert len(cand_act.get("market", [])) <= 10
