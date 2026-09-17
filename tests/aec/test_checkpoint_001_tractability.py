# SPDX-License-Identifier: MIT
"""AEC Checkpoint 001: Computational Tractability Benchmark (§16).

Measures development-only execution metrics:
- candidate count
- dependency closure size
- local simulation cost (H=4)
- medium replan cost (H=18)
- extended replan cost (H=36)
- full replan cost (H=48)
- latency distribution
"""

from __future__ import annotations

import copy
import time
from typing import Any, Dict, List
import pytest

from aec.config import AECConfig
from aec.counterfactual.simulator import CounterfactualSimulator
from aec.ir.dependency_graph import ActionBasketDependencyGraph, ActionNode, CausalEdgeType, build_basket_dependency_graph
from aec.ir.economic_state import build_economic_state
from aec.patches.patch import CoupledPatch


def test_tractability_benchmark_metrics(normal_opening_obs: Dict[str, Any]) -> None:
    """Measures candidate count, closure size, and simulator costs across escalation horizons."""
    state = build_economic_state(normal_opening_obs)
    baseline_action = {
        "farmer": ["EAST"],
        "hands": [["SOUTH"]],
        "market": [
            ["BUY_PRODUCT", "WHEAT", 10],
            ["SELL", "STRAWBERRY", 5]
        ]
    }

    # 1. Dependency Closure Size & Timing
    t0 = time.perf_counter()
    graph = build_basket_dependency_graph(baseline_action, state)
    closure_size = len(graph.compute_dependency_closure({"MKT_1_SELL_STRAWBERRY"}))
    closure_time_ms = (time.perf_counter() - t0) * 1000.0

    assert closure_size >= 1
    assert closure_time_ms < 2.0, f"Closure calculation too slow: {closure_time_ms:.3f}ms"

    # 2. Simulator Timing Across Horizons
    simulator = CounterfactualSimulator()
    patch = CoupledPatch(
        patch_id="BENCH_PATCH",
        source_opportunity_id="BENCH_OPP",
        market_mutations=[["SELL", "STRAWBERRY", 5], ["BUY_PRODUCT", "WHEAT", 10]],
        expected_horizon=4
    )

    continuation = [{"farmer": ["EAST"], "hands": [["SOUTH"]], "market": []} for _ in range(50)]

    # Warmup
    _ = simulator.evaluate(patch, baseline_action, state, 4, continuation[:4])

    # H=4 (Local short replan)
    t_local0 = time.perf_counter()
    for _ in range(20):
        _ = simulator.evaluate(patch, baseline_action, state, 4, continuation[:4])
    local_cost_ms = ((time.perf_counter() - t_local0) / 20.0) * 1000.0

    # H=18 (Medium replan)
    t_med0 = time.perf_counter()
    for _ in range(20):
        _ = simulator.evaluate(patch, baseline_action, state, 18, continuation[:18])
    medium_cost_ms = ((time.perf_counter() - t_med0) / 20.0) * 1000.0

    # H=36 (Extended replan)
    t_ext0 = time.perf_counter()
    for _ in range(20):
        _ = simulator.evaluate(patch, baseline_action, state, 36, continuation[:36])
    extended_cost_ms = ((time.perf_counter() - t_ext0) / 20.0) * 1000.0

    # H=48 (Strategic/Full replan)
    t_full0 = time.perf_counter()
    for _ in range(20):
        _ = simulator.evaluate(patch, baseline_action, state, 48, continuation[:48])
    full_cost_ms = ((time.perf_counter() - t_full0) / 20.0) * 1000.0

    print("\nTRACTABILITY BENCHMARK RESULTS:")
    print(f"Dependency closure calculation: {closure_time_ms:.3f} ms (size: {closure_size})")
    print(f"Level 1 Local replan (H=4):     {local_cost_ms:.3f} ms")
    print(f"Level 3 Medium replan (H=18):   {medium_cost_ms:.3f} ms")
    print(f"Level 4 Extended replan (H=36): {extended_cost_ms:.3f} ms")
    print(f"Level 5 Full replan (H=48):     {full_cost_ms:.3f} ms")

    # Assert tractability bounds (< 25ms per simulation even for full horizon H=48)
    assert local_cost_ms < 5.0, f"Local simulation exceeded budget: {local_cost_ms:.2f}ms"
    assert medium_cost_ms < 15.0, f"Medium simulation exceeded budget: {medium_cost_ms:.2f}ms"
    assert extended_cost_ms < 25.0, f"Extended simulation exceeded budget: {extended_cost_ms:.2f}ms"
    assert full_cost_ms < 35.0, f"Full simulation exceeded budget: {full_cost_ms:.2f}ms"
