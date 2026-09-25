# SPDX-License-Identifier: MIT
"""V33 Route Transition Test: Verifies transition boundary gating and safety invariants."""

import json
import os
import sys
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from candidates.v33_meta_strategy.selector import RouteSelector


def test_transition_specs_file():
    spec_path = os.path.join(REPO_ROOT, "transition_specs.json")
    assert os.path.exists(spec_path), f"Missing {spec_path}"
    with open(spec_path, "r", encoding="utf-8") as f:
        spec = json.load(f)
    assert spec["source_default"] == "R0_A7"
    assert "R2_DMITRII" in spec["allowed_switch_targets"]
    assert spec["safety_protocols"]["max_switches_per_episode"] == 1


def test_one_switch_first_invariant():
    selector = RouteSelector(decision_steps=(24, 48, 72), min_gain_threshold=1000.0)

    # Simulated hostile market triggering switch
    obs_step24 = {
        "step": 24,
        "player": 0,
        "market": {"prices": {"WHEAT": 15}, "inventory": {"WHEAT": 12000}},
        "farms": [{"hands": []}, {"hands": [1, 2], "claimed": [0, 1]}],
    }

    d1 = selector.evaluate(obs_step24)
    assert d1 == "SWITCH_R2_DMITRII"
    assert selector.switches_made == 1

    # At step 48, selector must NOT switch again (must stay on current route)
    obs_step48 = dict(obs_step24, step=48)
    d2 = selector.evaluate(obs_step48)
    assert d2 == "STAY_R0"
    assert selector.switches_made == 1


def test_disallowed_boundary_steps():
    """Verifies that selector never initiates switches at illegal steps (e.g. t=10, 100, 288)."""
    selector = RouteSelector(decision_steps=(24, 48, 72), min_gain_threshold=1000.0)
    for bad_step in [0, 12, 35, 100, 288, 500]:
        obs = {
            "step": bad_step,
            "player": 0,
            "market": {"prices": {"WHEAT": 10}, "inventory": {"WHEAT": 15000}},
            "farms": [{"hands": []}, {"hands": [1, 2], "claimed": [0, 1]}],
        }
        dec = selector.evaluate(obs)
        assert dec == "STAY_R0", f"Unexpected switch at illegal step {bad_step}"
