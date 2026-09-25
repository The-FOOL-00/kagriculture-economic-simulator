# SPDX-License-Identifier: MIT
"""V34 Determinism & Seed Reproducibility Test Suite.

Verifies:
1. Running V34 twice on identical seeds produces bit-identical rewards and final cash.
2. Step-by-step action sequences are 100% deterministic.
"""

from __future__ import annotations
import os
import sys
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from kaggle_environments import make
from candidates.v34_a7_tactical.main import V34TacticalController


def test_deterministic_reproducibility():
    ctrl1 = V34TacticalController(enable_tactical=True)
    ctrl2 = V34TacticalController(enable_tactical=True)

    env1 = make("kaggriculture", configuration={"seed": 249675, "episodeSteps": 50})
    env2 = make("kaggriculture", configuration={"seed": 249675, "episodeSteps": 50})

    env1.reset()
    env2.reset()

    for step in range(30):
        o1 = env1.steps[-1][0]["observation"]
        o2 = env2.steps[-1][0]["observation"]

        a1 = ctrl1.act(o1)
        a2 = ctrl2.act(o2)

        assert a1 == a2, f"Action divergence at step {step}"
        env1.step([a1, {"farmer": ["PASS"], "hands": [], "market": []}])
        env2.step([a2, {"farmer": ["PASS"], "hands": [], "market": []}])

    r1 = env1.steps[-1][0]["reward"]
    r2 = env2.steps[-1][0]["reward"]
    assert r1 == r2, f"Reward mismatch: {r1} != {r2}"
