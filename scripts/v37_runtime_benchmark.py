# SPDX-License-Identifier: MIT
"""V37: Runtime benchmark for staged V35 agent."""

import json
import os
import statistics
import sys
import time
import tracemalloc

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
STAGING_DIR = os.path.join(REPO_ROOT, "submission_final_v35")
sys.path.insert(0, STAGING_DIR)

def benchmark():
    tracemalloc.start()
    t_start = time.perf_counter()
    import main
    t_import = (time.perf_counter() - t_start) * 1000.0  # ms
    mem_current, mem_peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    # Step 0 observation
    obs0 = {
        "step": 0,
        "player": 0,
        "farms": [{"cash": 1000, "hands": []}, {"cash": 1000, "hands": []}],
        "market": {"prices": {"WHEAT": {"price": 10}}}
    }

    # Subsequent observation
    obs_sub = {
        "step": 10,
        "player": 0,
        "farms": [{"cash": 1200, "hands": []}, {"cash": 1100, "hands": []}],
        "market": {"prices": {"WHEAT": {"price": 10}}}
    }

    # Warmup
    for _ in range(50):
        main.agent(obs0)
        main.agent(obs_sub)

    # Benchmark Step 0 (500 reps)
    latencies_step0 = []
    for _ in range(500):
        t0 = time.perf_counter()
        main.agent(obs0)
        t1 = time.perf_counter()
        latencies_step0.append((t1 - t0) * 1000.0)

    # Benchmark Subsequent steps (2000 reps)
    latencies_sub = []
    for _ in range(2000):
        t0 = time.perf_counter()
        main.agent(obs_sub)
        t1 = time.perf_counter()
        latencies_sub.append((t1 - t0) * 1000.0)

    def stats(data):
        s = sorted(data)
        n = len(s)
        return {
            "reps": n,
            "mean_ms": round(statistics.mean(s), 5),
            "median_ms": round(statistics.median(s), 5),
            "p95_ms": round(s[int(0.95 * n)], 5),
            "p99_ms": round(s[int(0.99 * n)], 5),
            "max_ms": round(max(s), 5),
            "min_ms": round(min(s), 5)
        }

    res = {
        "import_time_ms": round(t_import, 3),
        "peak_memory_kb": round(mem_peak / 1024.0, 2),
        "step_0": stats(latencies_step0),
        "subsequent_steps": stats(latencies_sub),
        "competition_limit_ms": 1000.0,
        "step0_budget_pct": round((statistics.mean(latencies_step0) / 1000.0) * 100, 4),
        "sub_budget_pct": round((statistics.mean(latencies_sub) / 1000.0) * 100, 4)
    }

    print("RUNTIME_BENCHMARK_RESULTS:", json.dumps(res, indent=2))

if __name__ == "__main__":
    benchmark()
