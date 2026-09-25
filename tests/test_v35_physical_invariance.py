# SPDX-License-Identifier: MIT
"""Kagriculture V35 Test Suite: Physical Choreography & Worker Invariance."""

import os
import sys
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from scripts.v32_common import load_agent
from candidates.v35_a7_opening.main import V35OpeningController


def test_physical_invariance_steps_1_to_24():
    ctrl = V35OpeningController(wash_buy=25, wash_sell=25)
    a7 = load_agent("E9_AST")

    # Mock observation template
    for step in range(1, 25):
        obs = {
            "step": step,
            "player": 0,
            "farms": [
                {
                    "money": 1000.0,
                    "farmer": [step % 10, (step + 2) % 10],
                    "hands": [[1, 1], [2, 2]],
                    "unlocked_quadrants": [1],
                    "tiles": [[None]*10 for _ in range(10)]
                },
                {"money": 1000.0, "farmer": [0, 0], "hands": []}
            ],
            "private": {"shed": {"WHEAT": 10}, "seeds": {"MELON": 2}, "inventories": [{}, {}]},
            "market": {"prices": {"WHEAT": 25.0, "MELON": 250.0}},
        }
        cand_act = ctrl.act(obs)
        base_act = a7.act(obs)

        # Farmer action must be bit-identical
        assert cand_act.get("farmer") == base_act.get("farmer"), f"Physical mismatch at step {step} for farmer"
        # Hands actions must be bit-identical
        assert cand_act.get("hands") == base_act.get("hands"), f"Physical mismatch at step {step} for hands"
