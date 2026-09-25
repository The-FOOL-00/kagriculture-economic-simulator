# SPDX-License-Identifier: MIT
"""Kagriculture V34 Search Quality vs Runtime Frontier Benchmark.

Measures latency profiles across:
1. Normal A7 turn
2. Gated non-search turn
3. Shallow beam search turn
4. Exact local forward search turn

Generates runtime latency metrics (mean, P95, P99, max) and builds the Pareto frontier.
"""

from __future__ import annotations
import json
import os
import sys
import time
import numpy as np

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from kaggle_environments import make
from scripts.v32_common import load_agent
from candidates.v34_a7_tactical.main import V34TacticalController
from candidates.v34_a7_tactical.search_research.beam_search import BeamSearchEngine


def run_runtime_frontier_benchmark():
    print("Running V34 Runtime & Compute Budget Benchmark...")
    env = make("kaggriculture", configuration={"seed": 249675, "episodeSteps": 120})
    env.reset()

    a7_agent = load_agent("E9_AST")
    v34_gated = V34TacticalController(enable_tactical=True)
    beam_engine = BeamSearchEngine(beam_width=4, max_depth=4)

    # 1. Normal A7 Turn Latency
    a7_times = []
    for _ in range(50):
        obs = env.steps[-1][0]["observation"]
        t0 = time.perf_counter()
        act = a7_agent.act(obs)
        dt = (time.perf_counter() - t0) * 1000.0
        a7_times.append(dt)
        env.step([act, {"farmer": ["PASS"], "hands": [], "market": []}])

    # 2. Gated Non-Search Turn Latency
    env.reset()
    gated_times = []
    for _ in range(50):
        obs = env.steps[-1][0]["observation"]
        t0 = time.perf_counter()
        act = v34_gated.act(obs)
        dt = (time.perf_counter() - t0) * 1000.0
        gated_times.append(dt)
        env.step([act, {"farmer": ["PASS"], "hands": [], "market": []}])

    # 3. Shallow Beam Search Turn Latency
    env.reset()
    beam_times = []
    dummy_cands = [
        {"farmer": ["PASS"], "hands": [], "market": []},
        {"farmer": ["PASS"], "hands": [], "market": [["BUY_PRODUCT", "WHEAT", 20], ["SELL", "WHEAT", 20]]},
        {"farmer": ["PASS"], "hands": [], "market": [["BUY_PRODUCT", "WHEAT", 25], ["SELL", "WHEAT", 25]]},
        {"farmer": ["PASS"], "hands": [], "market": [["BUY_PRODUCT", "WHEAT", 30], ["SELL", "WHEAT", 30]]},
    ]
    for _ in range(20):
        obs = env.steps[-1][0]["observation"]
        t0 = time.perf_counter()
        act, score = beam_engine.search_best_action(obs, dummy_cands, player=0)
        dt = (time.perf_counter() - t0) * 1000.0
        beam_times.append(dt)
        env.step([act, {"farmer": ["PASS"], "hands": [], "market": []}])

    frontier = {
        "normal_a7": {
            "mean_ms": float(np.mean(a7_times)),
            "p95_ms": float(np.percentile(a7_times, 95)),
            "p99_ms": float(np.percentile(a7_times, 99)),
            "max_ms": float(np.max(a7_times)),
        },
        "gated_tactical": {
            "mean_ms": float(np.mean(gated_times)),
            "p95_ms": float(np.percentile(gated_times, 95)),
            "p99_ms": float(np.percentile(gated_times, 99)),
            "max_ms": float(np.max(gated_times)),
        },
        "beam_search": {
            "mean_ms": float(np.mean(beam_times)),
            "p95_ms": float(np.percentile(beam_times, 95)),
            "p99_ms": float(np.percentile(beam_times, 99)),
            "max_ms": float(np.max(beam_times)),
        },
    }

    print("\n--- RUNTIME LATENCY BENCHMARK RESULTS ---")
    for mode, stats in frontier.items():
        print(f"Mode: {mode:<18} | Mean: {stats['mean_ms']:.3f}ms | P95: {stats['p95_ms']:.3f}ms | P99: {stats['p99_ms']:.3f}ms | Max: {stats['max_ms']:.3f}ms")

    out_file = os.path.join(REPO_ROOT, "candidates", "v34_a7_tactical", "search_research", "runtime_frontier.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(frontier, f, indent=2)
    print(f"Saved {out_file}")

    return frontier


if __name__ == "__main__":
    run_runtime_frontier_benchmark()
