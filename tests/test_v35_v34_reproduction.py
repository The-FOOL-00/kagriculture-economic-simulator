# SPDX-License-Identifier: MIT
"""Kagriculture V35 Test Suite: V34 25/25 Reproduction Verification."""

import json
import os
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
REPRO_PATH = os.path.join(REPO_ROOT, "v34_reproduction.json")


def test_reproduction_file_exists():
    assert os.path.exists(REPRO_PATH), f"Reproduction output file missing at {REPRO_PATH}"


def test_reproduction_win_rates():
    with open(REPRO_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data.get("verified") is True, "Reproduction verified flag is not True"
    summary = data["summary"]

    a7_wins = summary["A7_BASELINE"]["wins"]
    v34_wins = summary["V34_WASH25"]["wins"]

    assert a7_wins == 53.0, f"Expected A7 baseline 53.0 wins, got {a7_wins}"
    assert v34_wins == 57.0, f"Expected V34 57.0 wins, got {v34_wins}"
    assert v34_wins > a7_wins, "V34 wins did not exceed A7 baseline"


def test_reproduction_deltas():
    with open(REPRO_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    v34 = data["summary"]["V34_WASH25"]
    assert v34["mean_paired_delta"] > 0.0, "V34 mean paired delta is non-positive"
    assert v34["worst_paired_delta"] >= 0.0, f"V34 worst paired delta is negative: {v34['worst_paired_delta']}"
    assert v34["interventions_per_match"] == 1.0, "Interventions per match was not exactly 1.0"
