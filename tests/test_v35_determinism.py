# SPDX-License-Identifier: MIT
"""Kagriculture V35 Test Suite: Determinism & Replay Consistency."""

import copy
import os
import sys
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from candidates.v35_a7_opening.main import agent, V35OpeningController


def test_agent_call_determinism():
    obs = {
        "step": 0,
        "player": 0,
        "farms": [{"money": 3000.0, "farmer": [5, 5], "hands": []}],
        "market": {"prices": {"WHEAT": 25.0}},
    }

    first_act = agent(copy.deepcopy(obs))
    for _ in range(10):
        next_act = agent(copy.deepcopy(obs))
        assert first_act == next_act, "Non-deterministic output detected!"


def test_controller_reset_determinism():
    ctrl = V35OpeningController()
    obs0 = {"step": 0, "player": 0, "farms": [{"money": 3000.0}], "market": {"prices": {"WHEAT": 25.0}}}
    obs1 = {"step": 1, "player": 0, "farms": [{"money": 1054.0}], "market": {"prices": {"WHEAT": 25.0}}}

    act0_run1 = ctrl.act(obs0)
    act1_run1 = ctrl.act(obs1)

    ctrl.reset()
    act0_run2 = ctrl.act(obs0)
    act1_run2 = ctrl.act(obs1)

    assert act0_run1 == act0_run2
    assert act1_run1 == act1_run2
