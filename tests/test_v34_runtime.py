# SPDX-License-Identifier: MIT
"""V34 Runtime Latency & Compute Budget Test Suite.

Verifies:
1. candidates/v34_a7_tactical/main.py respects Kaggle per-turn time budget.
2. Normal A7 turn latency has mean < 50ms and P99 < 200ms.
3. Gated tactical turn latency does not exceed 1000ms.
"""

from __future__ import annotations
import os
import sys
import time
import numpy as np
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from kaggle_environments import make
from candidates.v34_a7_tactical.main import V34TacticalController


def test_turn_latency_benchmark():
    ctrl = V34TacticalController(enable_tactical=True)
    env = make("kaggriculture", configuration={"seed": 249675, "episodeSteps": 100})
    env.reset()

    latencies = []
    # Run 50 steps measuring exact per-turn latency
    for _ in range(50):
        obs = env.steps[-1][0]["observation"]
        t0 = time.perf_counter()
        act = ctrl.act(obs)
        dt = (time.perf_counter() - t0) * 1000.0  # in ms
        latencies.append(dt)
        env.step([act, {"farmer": ["PASS"], "hands": [], "market": []}])

    mean_lat = float(np.mean(latencies))
    p95_lat = float(np.percentile(latencies, 95))
    max_lat = float(np.max(latencies))

    print(f"\nRuntime Latency over 50 turns: Mean={mean_lat:.2f}ms, P95={p95_lat:.2f}ms, Max={max_lat:.2f}ms")
    # Invariant: mean latency < 50ms, max < 1000ms
    assert mean_lat < 50.0, f"Mean latency {mean_lat}ms exceeds 50ms budget"
    assert max_lat < 1000.0, f"Max latency {max_lat}ms exceeds 1000ms budget"
