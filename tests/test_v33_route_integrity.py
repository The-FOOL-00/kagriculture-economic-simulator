# SPDX-License-Identifier: MIT
"""V33 Route Integrity Test: Verifies initialization and action validity of all expert routes."""

import json
import os
import sys
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from candidates.v33_meta_strategy.route_bank import RouteBank


def test_route_bank_instantiation():
    bank = RouteBank()
    routes = bank.list_routes()
    expected_routes = ["R0_A7", "R1_V22R1", "R2_DMITRII", "R3_P3090", "R4_V54", "R5_V25P3"]
    assert set(routes) == set(expected_routes), f"Expected routes {expected_routes}, got {routes}"


def test_route_metadata_completeness():
    bank = RouteBank()
    required_keys = [
        "route_id", "name", "source", "archetype", "strategic_phases",
        "phase_boundaries", "compatibility_assumptions", "observed_strengths",
        "observed_weaknesses", "benchmark_mean_cash", "provenance", "status"
    ]
    for rid in bank.list_routes():
        meta = bank.get_metadata(rid)
        for key in required_keys:
            assert key in meta, f"Metadata for {rid} missing key: {key}"


def test_route_action_format():
    """Verifies that every expert route callable returns a legal action structure."""
    bank = RouteBank()
    from kaggle_environments import make
    env = make("kaggriculture")
    dummy_obs = env.reset()[0]["observation"]

    for rid in bank.list_routes():
        agent = bank.load_route(rid)
        action = agent(dummy_obs)
        assert isinstance(action, dict), f"Route {rid} action is not a dict: {type(action)}"
        assert "farmer" in action, f"Route {rid} missing 'farmer' key"
        assert "hands" in action, f"Route {rid} missing 'hands' key"
        assert "market" in action, f"Route {rid} missing 'market' key"
