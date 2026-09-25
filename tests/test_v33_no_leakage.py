# SPDX-License-Identifier: MIT
"""V33 No Leakage Test: Verifies complete absence of future leakage and hidden identifiers."""

import os
import sys
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from candidates.v33_meta_strategy.selector import RouteSelector


def test_no_hidden_identifier_dependence():
    """Verifies that selector features do not ingest seed, opponent_id, or player rank."""
    selector = RouteSelector()
    forbidden_keys = ["seed", "opponent_id", "opponent", "rank", "leaderboard", "final_cash", "future"]

    obs = {
        "step": 24,
        "player": 0,
        "seed": 999999,
        "opponent_id": "CHEATING_OPPONENT",
        "market": {"prices": {"WHEAT": 25}, "inventory": {"WHEAT": 10000}},
        "farms": [{"hands": []}, {"hands": []}],
    }

    features = selector.extract_observable_features(obs)
    for feat_name in features.keys():
        for f_key in forbidden_keys:
            assert f_key not in feat_name.lower(), f"Forbidden key '{f_key}' found in feature '{feat_name}'"


def test_leakage_audit_script():
    """Runs the formal replay_leakage_audit tool."""
    from candidates.v33_meta_strategy.replay_leakage_audit import run_leakage_audit
    status = run_leakage_audit()
    assert status == 0, "Formal leakage audit returned non-zero error code!"
