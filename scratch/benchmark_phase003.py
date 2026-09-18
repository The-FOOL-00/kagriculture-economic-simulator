# SPDX-License-Identifier: MIT
"""AEC Phase 003: Multi-Worker Coordination Performance Benchmark (§32).

Benchmarks:
- task graph construction
- candidate assignment
- dominance pruning
- space-time route reservation
- multi-worker coordinator end-to-end
Reports mean, median, and p95 latency under representative worker counts (1, 2, 3 workers).
"""

import os
import sys
import time
sys.path.insert(0, os.path.abspath("."))
import numpy as np
from typing import Dict

from aec.coordination.assignment import (
    LaborOpportunityCost,
    WorkerAssignment,
    compute_marginal_labor_cost,
)
from aec.coordination.dominance import MultiWorkerDominancePruner
from aec.coordination.scheduler import MultiWorkerLogisticsCoordinator
from aec.coordination.task_model import (
    TaskActionFamily,
    TaskDependencyGraph,
    TaskPriority,
    WorkerTask,
)
from aec.coordination.worker_model import WorkerState, WorkerType
from aec.replanning.reconnect import SpacetimeReservationTable, deterministic_find_path


def benchmark_task_graph_construction(n_trials: int = 1000):
    latencies = []
    for _ in range(n_trials):
        t0 = time.perf_counter()
        dag = TaskDependencyGraph()
        t1 = WorkerTask(task_id="T1", action_family=TaskActionFamily.PICKUP_RESOURCE, location=(4, 4))
        t2 = WorkerTask(task_id="T2", action_family=TaskActionFamily.FEED_ANIMAL, location=(4, 6), dependent_tasks=["T1"])
        t3 = WorkerTask(task_id="T3", action_family=TaskActionFamily.HARVEST, location=(2, 2))
        dag.add_task(t1)
        dag.add_task(t2)
        dag.add_task(t3)
        ready = dag.get_ready_tasks()
        t_elapsed = (time.perf_counter() - t0) * 1000.0  # ms
        latencies.append(t_elapsed)
    return np.mean(latencies), np.median(latencies), np.percentile(latencies, 95)


def benchmark_dominance_pruning(n_trials: int = 1000):
    task = WorkerTask(task_id="T", action_family=TaskActionFamily.FEED_ANIMAL, location=(4, 5))
    plan_a = [WorkerAssignment(worker_id=0, task=task, start_step=0, completion_step=2)]
    cost_a = LaborOpportunityCost(lost_mandatory_count=1, displaced_value_est=100.0, is_acceptable=False)
    plan_b = [WorkerAssignment(worker_id=1, task=task, start_step=0, completion_step=2)]
    cost_b = LaborOpportunityCost(lost_mandatory_count=0, displaced_value_est=0.0, absorbed_tasks=["T"], is_acceptable=True)
    candidates = [(plan_a, cost_a), (plan_b, cost_b)]

    latencies = []
    for _ in range(n_trials):
        t0 = time.perf_counter()
        _ = MultiWorkerDominancePruner.prune(candidates)
        t_elapsed = (time.perf_counter() - t0) * 1000.0
        latencies.append(t_elapsed)
    return np.mean(latencies), np.median(latencies), np.percentile(latencies, 95)


def benchmark_route_reservation(n_trials: int = 500):
    latencies = []
    for _ in range(n_trials):
        t0 = time.perf_counter()
        table = SpacetimeReservationTable(10)
        table.reserve_vertex(10, (4, 4), 0)
        table.reserve_vertex(11, (4, 5), 0)
        table.reserve_edge(11, (4, 4), (4, 5), 0)
        _ = deterministic_find_path((4, 4), (2, 2), start_step=10, reservations=table, worker_id=1, max_steps=15)
        t_elapsed = (time.perf_counter() - t0) * 1000.0
        latencies.append(t_elapsed)
    return np.mean(latencies), np.median(latencies), np.percentile(latencies, 95)


def benchmark_coordinator_e2e(num_workers: int, n_trials: int = 500):
    coord = MultiWorkerLogisticsCoordinator(board_size=10)
    workers = {
        0: WorkerState(worker_id=0, worker_type=WorkerType.FARMER, position=(0, 0)),
    }
    if num_workers >= 2:
        workers[1] = WorkerState(worker_id=1, worker_type=WorkerType.HAND, position=(4, 4))
    if num_workers >= 3:
        workers[2] = WorkerState(worker_id=2, worker_type=WorkerType.HAND, position=(8, 8))

    baseline_action = {"farmer": ["HARVEST"], "hands": [["PASS"], ["PASS"]][:num_workers - 1]}
    baseline_cont = [{"farmer": ["HARVEST"], "hands": [["PASS"], ["PASS"]][:num_workers - 1]}]

    candidate_tasks = [
        WorkerTask(
            task_id="BENCH_FEED",
            action_family=TaskActionFamily.FEED_ANIMAL,
            location=(4, 5),
            earliest_start=5,
            latest_completion=15,
            priority_class=TaskPriority.LIVESTOCK_SECURITY,
            is_mandatory=True,
        )
    ]

    latencies = []
    for _ in range(n_trials):
        t0 = time.perf_counter()
        _ = coord.plan_coordination(
            candidate_tasks=candidate_tasks,
            workers=workers,
            baseline_action=baseline_action,
            baseline_continuation=baseline_cont,
            current_step=5
        )
        t_elapsed = (time.perf_counter() - t0) * 1000.0
        latencies.append(t_elapsed)
    return np.mean(latencies), np.median(latencies), np.percentile(latencies, 95)


if __name__ == "__main__":
    print("=" * 60)
    print("AEC Phase 003: Multi-Worker Coordination Benchmarks")
    print("=" * 60)

    mean, med, p95 = benchmark_task_graph_construction()
    print(f"Task Graph Construction (1000 trials):  mean={mean:.4f}ms, med={med:.4f}ms, p95={p95:.4f}ms")

    mean, med, p95 = benchmark_dominance_pruning()
    print(f"Dominance Pruning (1000 trials):        mean={mean:.4f}ms, med={med:.4f}ms, p95={p95:.4f}ms")

    mean, med, p95 = benchmark_route_reservation()
    print(f"Route & Spacetime Pathfinding (500):    mean={mean:.4f}ms, med={med:.4f}ms, p95={p95:.4f}ms")

    for nw in [1, 2, 3]:
        mean, med, p95 = benchmark_coordinator_e2e(nw, 500)
        print(f"Coordinator E2E ({nw} Worker(s), 500 trials): mean={mean:.4f}ms, med={med:.4f}ms, p95={p95:.4f}ms")

    print("=" * 60)
