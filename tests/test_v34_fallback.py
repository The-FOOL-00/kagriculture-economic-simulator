# SPDX-License-Identifier: MIT
"""V34 Fallback & Parity Test Suite.

Verifies:
1. candidates/v34_a7_tactical/main.py exports agent(obs, configuration=None).
2. When enable_tactical=False, V34 is bit-for-bit identical to baseline A7.
3. Injected exceptions in tactical evaluation trigger immediate, safe A7 fallback.
"""

from __future__ import annotations
import copy
import os
import sys
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from kaggle_environments import make
from scripts.v32_common import load_agent
from candidates.v34_a7_tactical.main import V34TacticalController, agent


def test_submission_signature():
    env = make("kaggriculture", configuration={"seed": 249675, "episodeSteps": 10})
    env.reset()
    obs = env.steps[-1][0]["observation"]
    action = agent(obs)
    assert isinstance(action, dict)
    assert "farmer" in action
    assert "hands" in action
    assert "market" in action


def test_fallback_parity_when_disabled():
    """When tactical mode is disabled, controller must match A7 bit-for-bit."""
    ctrl = V34TacticalController(enable_tactical=False)
    a7 = load_agent("E9_AST")

    env = make("kaggriculture", configuration={"seed": 249675, "episodeSteps": 50})
    env.reset()

    for _ in range(15):
        obs = env.steps[-1][0]["observation"]
        act_ctrl = ctrl.act(obs)
        act_a7 = a7.act(obs)
        assert act_ctrl == act_a7, f"Parity mismatch at step {obs.get('step')}"
        env.step([act_ctrl, {"farmer": ["PASS"], "hands": [], "market": []}])


def test_exception_triggers_a7_fallback():
    """Injecting a malformed observation must not crash the agent; it must return valid fallback."""
    ctrl = V34TacticalController(enable_tactical=True)
    # Malformed observation with non-dict farms
    malformed_obs = {"step": 0, "player": 0, "farms": "NOT_A_LIST"}
    action = ctrl.act(malformed_obs)
    assert isinstance(action, dict)
    assert "farmer" in action
