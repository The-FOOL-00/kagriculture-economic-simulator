import os
import sys
import time
import json
import statistics
import platform
import kagsim

# Hardware / Environment details
CPU_MODEL = "13th Gen Intel(R) Core(TM) i7-1355U"
PHYSICAL_CORES = 10
LOGICAL_CORES = 12
PYTHON_VERSION = sys.version
COMPILER_VERSION = "MSVC v18.6.1 (14.51.36231)"
COMPILER_FLAGS = "/O2 /W3 /GL /DNDEBUG /MD /std:c++17"

print("================================================================")
print("BENCHMARKING KAGSIM (CPPSIM) UNDER CONTROLLED EMPIRICAL TESTING")
print("================================================================")
print(f"CPU: {CPU_MODEL} ({PHYSICAL_CORES} cores, {LOGICAL_CORES} threads)")
print(f"Python: {PYTHON_VERSION}")
print(f"Compiler: {COMPILER_VERSION} flags: {COMPILER_FLAGS}")

# 1. Load a realistic action stream from bundled traces
trace_path = r"external_repos\kaggriculture-cppsim\traces\replay_cb.py_11.txt"
sys.path.insert(0, os.path.abspath(r"external_repos\kaggriculture-cppsim\tests"))
from test_golden import parse_trace

from pathlib import Path
seed, acts, finals = parse_trace(Path(trace_path))
stream_a = kagsim.Stream(acts[0])
stream_b = kagsim.Stream(acts[1])
idle_stream = kagsim.Stream([{"farmer": ["PASS"], "hands": [], "market": []}] * 720)

results = {
    "hardware": {
        "cpu_model": CPU_MODEL,
        "physical_cores": PHYSICAL_CORES,
        "logical_cores": LOGICAL_CORES,
        "platform": platform.platform(),
        "python_version": PYTHON_VERSION,
        "compiler_version": COMPILER_VERSION,
        "compiler_flags": COMPILER_FLAGS
    },
    "benchmarks": {}
}

# -------------------------------------------------------------
# BENCHMARK 1: L0 Batch Mode - Single Thread (threads=1)
# -------------------------------------------------------------
print("\n--- BENCHMARK 1: L0 Batch Mode, Single-Thread (threads=1) ---")
N_WARMUP = 200
N_EPISODES = 2000
SEEDS = list(range(1000, 1000 + N_EPISODES))
WARMUP_SEEDS = list(range(500, 500 + N_WARMUP))

# Warmup
warmup_jobs = [(stream_a, idle_stream, s) for s in WARMUP_SEEDS]
_ = kagsim.run_many(warmup_jobs, threads=1)

runs_l0_1t = []
for run_idx in range(3):
    jobs = [(stream_a, idle_stream, s) for s in SEEDS]
    t0 = time.perf_counter()
    res = kagsim.run_many(jobs, threads=1)
    t1 = time.perf_counter()
    wall = t1 - t0
    eps = N_EPISODES / wall
    runs_l0_1t.append({
        "run": run_idx + 1,
        "episodes": N_EPISODES,
        "wall_seconds": wall,
        "episodes_per_second": eps,
        "ms_per_episode": (wall / N_EPISODES) * 1000.0
    })
    print(f"Run {run_idx+1}: {N_EPISODES} episodes in {wall:.4f}s = {eps:.1f} ep/s ({((wall/N_EPISODES)*1000):.3f} ms/ep)")

eps_list = [r["episodes_per_second"] for r in runs_l0_1t]
results["benchmarks"]["L0_single_thread"] = {
    "episodes": N_EPISODES,
    "warmup": N_WARMUP,
    "threads": 1,
    "seed_mode": "varied (2000 distinct seeds)",
    "runs": runs_l0_1t,
    "mean_eps": statistics.mean(eps_list),
    "median_eps": statistics.median(eps_list),
    "min_eps": min(eps_list),
    "max_eps": max(eps_list),
    "includes_process_startup": False,
    "includes_python_overhead": "minimal (run_many GIL released wrapper)"
}

# -------------------------------------------------------------
# BENCHMARK 2: L0 Batch Mode - Multi-Thread (threads=0 => all logical cores)
# -------------------------------------------------------------
print("\n--- BENCHMARK 2: L0 Batch Mode, Multi-Thread (threads=0, all cores) ---")
N_WARMUP_MT = 1000
N_EPISODES_MT = 10000
SEEDS_MT = list(range(2000, 2000 + N_EPISODES_MT))
_ = kagsim.run_many([(stream_a, idle_stream, s) for s in range(N_WARMUP_MT)], threads=0)

runs_l0_mt = []
for run_idx in range(3):
    jobs = [(stream_a, idle_stream, s) for s in SEEDS_MT]
    t0 = time.perf_counter()
    res = kagsim.run_many(jobs, threads=0)
    t1 = time.perf_counter()
    wall = t1 - t0
    eps = N_EPISODES_MT / wall
    eps_per_core = eps / LOGICAL_CORES
    runs_l0_mt.append({
        "run": run_idx + 1,
        "episodes": N_EPISODES_MT,
        "wall_seconds": wall,
        "episodes_per_second_total": eps,
        "episodes_per_second_per_core": eps_per_core,
        "ms_per_episode_total": (wall / N_EPISODES_MT) * 1000.0
    })
    print(f"Run {run_idx+1}: {N_EPISODES_MT} episodes in {wall:.4f}s = {eps:.1f} ep/s total ({eps_per_core:.1f} ep/s/core)")

eps_mt_list = [r["episodes_per_second_total"] for r in runs_l0_mt]
results["benchmarks"]["L0_multi_thread"] = {
    "episodes": N_EPISODES_MT,
    "warmup": N_WARMUP_MT,
    "threads": 0,
    "seed_mode": "varied (10000 distinct seeds)",
    "runs": runs_l0_mt,
    "mean_eps_total": statistics.mean(eps_mt_list),
    "median_eps_total": statistics.median(eps_mt_list),
    "min_eps_total": min(eps_mt_list),
    "max_eps_total": max(eps_mt_list),
    "mean_eps_per_core": statistics.mean(eps_mt_list) / LOGICAL_CORES,
    "includes_process_startup": False,
    "includes_python_overhead": "minimal (GIL released C++ thread pool)"
}

# -------------------------------------------------------------
# BENCHMARK 3: L1 Step Mode (Game.step in Python)
# -------------------------------------------------------------
print("\n--- BENCHMARK 3: L1 Step Mode (Game.step Python overhead) ---")
N_EPISODES_L1 = 50
runs_l1 = []
raw_pass_act = {"farmer": ["PASS"], "hands": [], "market": []}

for run_idx in range(3):
    t0 = time.perf_counter()
    for s_idx in range(N_EPISODES_L1):
        g = kagsim.Game(42 + s_idx)
        for _ in range(720):
            g.step(raw_pass_act, raw_pass_act)
    t1 = time.perf_counter()
    wall = t1 - t0
    eps = N_EPISODES_L1 / wall
    runs_l1.append({
        "run": run_idx + 1,
        "episodes": N_EPISODES_L1,
        "wall_seconds": wall,
        "episodes_per_second": eps,
        "ms_per_episode": (wall / N_EPISODES_L1) * 1000.0
    })
    print(f"Run {run_idx+1}: {N_EPISODES_L1} episodes in {wall:.4f}s = {eps:.1f} ep/s ({((wall/N_EPISODES_L1)*1000):.3f} ms/ep)")

eps_l1_list = [r["episodes_per_second"] for r in runs_l1]
results["benchmarks"]["L1_step_mode"] = {
    "episodes": N_EPISODES_L1,
    "threads": 1,
    "runs": runs_l1,
    "mean_eps": statistics.mean(eps_l1_list),
    "median_eps": statistics.median(eps_l1_list),
    "min_eps": min(eps_l1_list),
    "max_eps": max(eps_l1_list),
    "includes_process_startup": False,
    "includes_python_overhead": "Full Python loop crossing per step"
}

# Save raw benchmark results
with open(r"forensic_verification\benchmark_raw\cppsim_benchmark.json", "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2)

print("\nBenchmark completed and saved to forensic_verification/benchmark_raw/cppsim_benchmark.json")
