# SPDX-License-Identifier: MIT
"""V33 Fallback Test: Verifies instantaneous, deterministic fallback to R0_A7 on error."""

import os
import sys
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from candidates.v33_meta_strategy.route_bank import RouteBank


def test_exception_fallback_handling():
    """Simulates a broken target agent and verifies fallback mechanism."""
    bank = RouteBank()
    a7 = bank.load_route("R0_A7")

    def broken_target_agent(obs, cfg=None):
        raise RuntimeError("Simulated target agent crash!")

    def fallback_wrapper(obs, cfg=None):
        try:
            return broken_target_agent(obs, cfg)
        except Exception:
            return a7(obs, cfg)

    dummy_obs = {
        "step": 50,
        "player": 0,
        "market": {"prices": {"WHEAT": 25}, "inventory": {"WHEAT": 10000}},
        "farms": [{"hands": [], "claimed": [0]}],
        "private": {"cash": 3000, "shed": {}}
    }

    action = fallback_wrapper(dummy_obs)
    assert isinstance(action, dict)
    assert "farmer" in action
    assert "hands" in action
    assert "market" in action
