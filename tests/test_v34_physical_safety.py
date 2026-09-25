# SPDX-License-Identifier: MIT
"""V34 Physical Synchronization & Choreography Safety Test Suite.

Verifies:
1. Tactical candidates do not disturb A7's physical worker positions or pathing.
2. Market-only interventions have 0 physical divergence steps.
3. Planting cutoff interventions convert actions to PASS without displacing workers.
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
from candidates.v34_a7_tactical.candidate_generator import (
    generate_step0_candidates, generate_late_cutoff_candidates
)


def test_step0_market_physical_invariance():
    """Verifies that altering Step 0 market wash does not displace workers."""
    env = make("kaggriculture", configuration={"seed": 249675, "episodeSteps": 20})
    env.reset()
    a7 = load_agent("E9_AST")
    obs = env.steps[-1][0]["observation"]
    base_act = a7.act(obs)

    cands = generate_step0_candidates(obs, base_act)
    assert len(cands) >= 3

    for c in cands:
        # Physical action of farmer and hands must be identical to parent A7
        assert c.candidate_action["farmer"] == base_act["farmer"]
        assert c.candidate_action["hands"] == base_act["hands"]
        assert c.physical_impact in ("NONE", "CONSERVATIVE")


def test_late_cutoff_physical_safety():
    """Verifies that late planting cutoff converts futile PLANT actions to PASS without moves."""
    mock_obs = {
        "step": 690,
        "player": 0,
        "farms": [{"money": 50000.0, "hands": [[4, 4], [4, 5]]}],
        "private": {"shed": {}},
        "market": {"prices": {"MELON": 250.0}},
        "town": {"unlocked_shops": []}
    }
    # A7 attempts to plant Melon (needs 96 ticks, but only 28 ticks remain)
    a7_act = {
        "farmer": ["PLANT", "MELON"],
        "hands": [["PASS"]],
        "market": [["BUY_SEED", "MELON", 1]],
    }
    cands = generate_late_cutoff_candidates(mock_obs, a7_act)
    assert len(cands) == 1
    cand = cands[0]
    # The futile PLANT should be converted to PASS, keeping farmer stationary at (4,4)
    assert cand.candidate_action["farmer"] == ["PASS"]
    # No movement direction allowed
    assert cand.candidate_action["farmer"][0] not in ("NORTH", "SOUTH", "EAST", "WEST")
