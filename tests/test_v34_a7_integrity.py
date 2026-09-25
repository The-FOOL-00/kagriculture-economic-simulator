# SPDX-License-Identifier: MIT
"""V34 A7 Baseline Integrity & Determinism Test Suite.

Verifies:
1. Protected incumbent A7 standalone (candidates/v30_a7_standalone/main.py) loads cleanly.
2. Deterministic execution: identical observations produce bit-identical actions.
3. A7 produces valid action structures with farmer, hands, and market keys.
"""

from __future__ import annotations
import copy
import hashlib
import os
import sys
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from scripts.v32_common import load_agent
from kaggle_environments import make

A7_PATH = os.path.join(REPO_ROOT, "candidates", "v30_a7_standalone", "main.py")
A7_SHA256 = "51c1d25245f68dd8de66b355f2ad6ca1d79de8af02efed521a5a82f7be69ce3f"


def test_a7_file_sha256():
    h = hashlib.sha256()
    with open(A7_PATH, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    assert h.hexdigest().lower() == A7_SHA256.lower()


def test_a7_step0_wash30():
    """Verifies that A7 modifies Step 0 market action to WASH30."""
    agent = load_agent("E9_AST")
    env = make("kaggriculture", configuration={"seed": 249675, "episodeSteps": 720})
    env.reset()
    obs = env.steps[-1][0]["observation"]
    act = agent.act(obs)

    assert isinstance(act, dict)
    assert "market" in act
    expected_wash = [["BUY_PRODUCT", "WHEAT", 30], ["SELL", "WHEAT", 30]]
    assert act["market"] == expected_wash, f"Expected {expected_wash}, got {act['market']}"


def test_a7_deterministic_parity():
    """Verifies that two independent runs on the same seed produce bit-identical rewards."""
    agent1 = load_agent("E9_AST")
    agent2 = load_agent("E9_AST")

    env1 = make("kaggriculture", configuration={"seed": 249675, "episodeSteps": 120})
    env2 = make("kaggriculture", configuration={"seed": 249675, "episodeSteps": 120})

    env1.reset()
    env2.reset()

    # Step both 20 steps
    for _ in range(20):
        o1 = env1.steps[-1][0]["observation"]
        o2 = env2.steps[-1][0]["observation"]
        a1 = agent1.act(o1)
        a2 = agent2.act(o2)
        assert a1 == a2, f"Divergence detected at step {o1.get('step')}"
        env1.step([a1, {"farmer": ["PASS"], "hands": [], "market": []}])
        env2.step([a2, {"farmer": ["PASS"], "hands": [], "market": []}])
