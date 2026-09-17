# SPDX-License-Identifier: MIT
"""Performance benchmarks and latency characterization for AEC-RESOURCE (§28)."""

from __future__ import annotations

import copy
import statistics
import time
import pytest

from aec.counterfactual.simulator import CounterfactualSimulator
from aec.ir.economic_state import build_economic_state
from aec.patches.patch import CoupledPatch
from aec.resource.conversions import ConversionDiscoveryEngine
from aec.resource.dag import ResourceEdge, ResourceNode, TemporalResourceDAG
from aec.resource.feed_security import FeedSecurityEngine


def test_benchmark_resource_subsystems(normal_opening_obs) -> None:
    """Benchmark per-component latency for graph construction, closure, feed security, and conversions (§28)."""
    obs = copy.deepcopy(normal_opening_obs)
    obs["farms"][0]["tiles"][1][1] = {"kind": "PASTURE", "animal": "COW", "fed_today": False}
    obs["farms"][0]["tiles"][2][2] = {"kind": "COOP", "animal": "GOOSE", "fed_today": False}
    obs["private"]["shed"]["WHEAT"] = 10
    econ_state = build_economic_state(obs)

    n_iterations = 200

    # 1. Benchmark Temporal DAG construction
    dag_times = []
    for _ in range(n_iterations):
        t0 = time.perf_counter()
        dag = TemporalResourceDAG()
        for i in range(10):
            dag.add_node(ResourceNode(node_id=f"N_{i}", commodity="WHEAT", quantity=i, turn=i))
        for i in range(9):
            dag.add_edge(ResourceEdge(
                edge_id=f"E_{i}", source_node_ids=[f"N_{i}"], dest_node_ids=[f"N_{i+1}"],
                action_type="BUY_PRODUCT", start_turn=i, completion_turn=i+1, quantity_delta={"WHEAT": 1}
            ))
        dag_times.append((time.perf_counter() - t0) * 1000.0)

    # 2. Benchmark Dependency Closure
    closure_times = []
    for _ in range(n_iterations):
        t0 = time.perf_counter()
        _ = dag.compute_dependency_closure({"N_0"})
        closure_times.append((time.perf_counter() - t0) * 1000.0)

    # 3. Benchmark Feed Security Engine
    feed_engine = FeedSecurityEngine()
    future_trajectory = [{"farmer": ["PASS"], "hands": [], "market": []} for _ in range(24)]
    feed_times = []
    for _ in range(n_iterations):
        t0 = time.perf_counter()
        _ = feed_engine.evaluate_feed_trajectory(econ_state, future_trajectory, horizon=24)
        feed_times.append((time.perf_counter() - t0) * 1000.0)

    # 4. Benchmark Conversion Path Discovery
    conv_engine = ConversionDiscoveryEngine()
    conv_times = []
    for _ in range(n_iterations):
        t0 = time.perf_counter()
        _ = conv_engine.discover_conversion_paths(econ_state, max_horizon=48)
        conv_times.append((time.perf_counter() - t0) * 1000.0)

    # Compute statistics (ms)
    def stats(series):
        s = sorted(series)
        mean_v = statistics.mean(s)
        med_v = statistics.median(s)
        p95_v = s[int(len(s) * 0.95)]
        return mean_v, med_v, p95_v

    mean_dag, med_dag, p95_dag = stats(dag_times)
    mean_cls, med_cls, p95_cls = stats(closure_times)
    mean_feed, med_feed, p95_feed = stats(feed_times)
    mean_conv, med_conv, p95_conv = stats(conv_times)

    print("\n--- AEC-RESOURCE LATENCY BENCHMARKS (ms) ---")
    print(f"DAG Construction:    mean={mean_dag:.4f}ms, med={med_dag:.4f}ms, p95={p95_dag:.4f}ms")
    print(f"Dependency Closure:  mean={mean_cls:.4f}ms, med={med_cls:.4f}ms, p95={p95_cls:.4f}ms")
    print(f"Feed Security Engine:mean={mean_feed:.4f}ms, med={med_feed:.4f}ms, p95={p95_feed:.4f}ms")
    print(f"Conversion Discovery:mean={mean_conv:.4f}ms, med={med_conv:.4f}ms, p95={p95_conv:.4f}ms")

    # Verify tractability requirement (< 5ms per component, total << 100ms)
    assert mean_dag < 1.0, f"DAG construction too slow: {mean_dag}ms"
    assert mean_cls < 0.5, f"Closure computation too slow: {mean_cls}ms"
    assert mean_feed < 1.0, f"Feed security analysis too slow: {mean_feed}ms"
    assert mean_conv < 1.0, f"Conversion discovery too slow: {mean_conv}ms"
