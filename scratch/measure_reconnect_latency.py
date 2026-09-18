# SPDX-License-Identifier: MIT
"""Benchmark AEC-RECONNECT latency across pathfinding, target search, splicing, and simulation."""

import time
from aec.replanning.reconnect import (
    ReconnectRequest,
    reconnect_worker_trajectory,
    deterministic_find_path,
    ReconnectionEngine
)
from aec.ir.economic_state import build_economic_state

def benchmark():
    engine = ReconnectionEngine(board_size=10)
    
    # 1. Pathfinding latency (1000 runs)
    t0 = time.perf_counter()
    for _ in range(1000):
        deterministic_find_path((1, 1), (8, 8), start_step=0, max_steps=20)
    t_path = (time.perf_counter() - t0) / 1000.0 * 1000.0 # ms

    # 2. Target identification (1000 runs)
    baseline_continuation = [
        {"farmer": ["EAST"]}, {"farmer": ["SOUTH"]}, {"farmer": ["HARVEST"]},
        {"farmer": ["DROP"]}, {"farmer": ["EAST"]}, {"farmer": ["PLANT"]}
    ]
    t0 = time.perf_counter()
    for _ in range(1000):
        engine.identify_reconnection_targets(baseline_continuation, start_pos=(4, 4), worker_id=0)
    t_targets = (time.perf_counter() - t0) / 1000.0 * 1000.0 # ms

    # 3. Full Local Route Splice (1000 runs)
    class MockWorker:
        def __init__(self):
            self.position = (4, 4)
            self.worker_id = 0
    class MockWorkers:
        def get_worker(self, wid):
            return MockWorker()
    class MockEcon:
        def __init__(self):
            self.step = 100
            self.workers = MockWorkers()

    req = ReconnectRequest(
        worker=0,
        divergence_point=100,
        patched_action=["SOUTH"],
        baseline_continuation=baseline_continuation,
        econ_state=MockEcon(),
        causal_closure={"LOCAL_WEED"}
    )
    t0 = time.perf_counter()
    for _ in range(1000):
        reconnect_worker_trajectory(req)
    t_reconnect = (time.perf_counter() - t0) / 1000.0 * 1000.0 # ms

    print(f"Pathfinding: {t_path:.4f} ms")
    print(f"Target Identification: {t_targets:.4f} ms")
    print(f"Full Reconnection & Splicing: {t_reconnect:.4f} ms")

if __name__ == "__main__":
    benchmark()
