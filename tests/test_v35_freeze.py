# SPDX-License-Identifier: MIT
"""Kagriculture V35 Test Suite: Candidate Freeze & Packaging Verification."""

import os
import sys
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from candidates.v35_a7_opening.main import agent


def test_agent_callable_interface():
    assert callable(agent), "V35 entry point 'agent' is not callable"


def test_agent_fail_closed_on_empty_obs():
    # Empty observation should safely return pass action without throwing uncaught exceptions
    act = agent({})
    assert isinstance(act, dict)
    assert "farmer" in act
    assert "hands" in act
    assert "market" in act


def test_agent_fail_closed_on_corrupted_obs():
    corrupted_obs = {
        "step": "corrupted_step",
        "player": "none",
        "farms": "invalid",
        "market": None,
    }
    act = agent(corrupted_obs)
    assert isinstance(act, dict)
    assert "farmer" in act
    assert "hands" in act
    assert "market" in act


def test_candidate_file_exists():
    cand_path = os.path.join(REPO_ROOT, "candidates", "v35_a7_opening", "main.py")
    assert os.path.exists(cand_path), f"Candidate main.py missing at {cand_path}"
    assert os.path.getsize(cand_path) > 500, "Candidate main.py is unexpectedly small"
