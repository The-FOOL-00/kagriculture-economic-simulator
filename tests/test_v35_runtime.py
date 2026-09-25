# SPDX-License-Identifier: MIT
"""Kagriculture V35 Test Suite: Latency & Runtime Budget Compliance."""

import os
import sys
import time
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from candidates.v35_a7_opening.main import V35OpeningController


def test_step0_latency_budget():
    ctrl = V35OpeningController()
    obs = {
        "step": 0,
        "player": 0,
        "farms": [{"money": 3000.0, "farmer": [5, 5], "hands": []}],
        "market": {"prices": {"WHEAT": 25.0}},
    }
    # Warmup
    _ = ctrl.act(obs)

    times = []
    for _ in range(50):
        t0 = time.perf_counter()
        _ = ctrl.act(obs)
        dt = (time.perf_counter() - t0) * 1000.0  # ms
        times.append(dt)

    mean_ms = sum(times) / len(times)
    assert mean_ms < 5.0, f"Step 0 latency too high: {mean_ms:.3f}ms (threshold 5.0ms)"


def test_subsequent_steps_latency_budget():
    ctrl = V35OpeningController()
    obs = {
        "step": 1,
        "player": 0,
        "farms": [{"money": 1054.0, "farmer": [5, 4], "hands": []}],
        "private": {"shed": {"WHEAT": 17}, "seeds": {}},
        "market": {"prices": {"WHEAT": 25.0}},
    }
    times = []
    for _ in range(50):
        t0 = time.perf_counter()
        _ = ctrl.act(obs)
        dt = (time.perf_counter() - t0) * 1000.0  # ms
        times.append(dt)

    mean_ms = sum(times) / len(times)
    assert mean_ms < 2.0, f"Subsequent step latency too high: {mean_ms:.3f}ms (threshold 2.0ms)"
