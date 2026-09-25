# SPDX-License-Identifier: MIT
"""Kagriculture V35 Test Suite: Anti-Leakage & Information Invariance."""

import os
import sys
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from candidates.v35_a7_opening.main import V35OpeningController


def test_no_seed_conditioning():
    ctrl1 = V35OpeningController()
    ctrl2 = V35OpeningController()

    obs = {
        "step": 0,
        "player": 0,
        "farms": [{"money": 3000.0, "farmer": [5, 5], "hands": []}],
        "market": {"prices": {"WHEAT": 25.0}},
    }

    # Configuration with different seed IDs
    act1 = ctrl1.act(obs, configuration={"seed": 111111})
    act2 = ctrl2.act(obs, configuration={"seed": 999999})

    assert act1 == act2, "Controller conditioned on configuration.seed!"


def test_forbidden_keys_ignored():
    ctrl = V35OpeningController()
    obs_clean = {
        "step": 0,
        "player": 0,
        "farms": [{"money": 3000.0, "farmer": [5, 5], "hands": []}],
        "market": {"prices": {"WHEAT": 25.0}},
    }
    obs_contaminated = dict(obs_clean)
    obs_contaminated["opponent_id"] = "E8_DMITRII"
    obs_contaminated["future_price"] = 999.0
    obs_contaminated["match_winner"] = 1

    act_clean = ctrl.act(obs_clean)
    act_contam = ctrl.act(obs_contaminated)

    assert act_clean == act_contam, "Controller output shifted in presence of contaminated keys!"


def test_seed_cohort_quarantine():
    # Verify that no V35 code references holdout seeds
    quarantined_ranges = [
        (214200, 214249),
        (340090, 340199),
        (249695, 249734),
    ]
    v35_dir = os.path.join(REPO_ROOT, "candidates", "v35_a7_opening")
    for fname in os.listdir(v35_dir):
        if fname.endswith(".py"):
            fpath = os.path.join(v35_dir, fname)
            with open(fpath, "r", encoding="utf-8") as f:
                code = f.read()
            for r_start, r_end in quarantined_ranges:
                for s in range(r_start, min(r_start + 10, r_end)):
                    assert str(s) not in code, f"Quarantined seed {s} found in {fname}!"
