"""
Runtime Profiling, Memory Leaks, Cross-Game Reset, and Side Symmetry
(Parts 26, 27, 28, 29)
"""

import os
import sys
import time
import tracemalloc
import importlib.util
import numpy as np
from kaggle_environments import make

project_root = r"c:\Users\Sundareswaran\Kagriculture"
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def load_module_from_path(module_name, file_path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = mod
    spec.loader.exec_module(mod)
    return mod

hybrid_mod = load_module_from_path("hybrid_mod3", os.path.join(project_root, "agents/hybrid_6c3s_10m.py"))
Hybrid6C3S10MAgent = hybrid_mod.Hybrid6C3S10MAgent

# 1. Part 26: Measure Runtime & Per-Turn Latency
def test_runtime_profiling(seed=10001):
    print("\n" + "="*80)
    print(f"PART 26 — RUNTIME PROFILING (SEED {seed})")
    print("="*80)
    
    agent_inst = Hybrid6C3S10MAgent()
    env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed}, debug=False)
    
    latencies = []
    
    # We will measure per-call execution time by hooking the agent
    def timed_agent(obs, config=None):
        t0 = time.perf_counter()
        act = agent_inst(obs, config)
        dt = (time.perf_counter() - t0) * 1000.0 # ms
        latencies.append(dt)
        return act
        
    env.run([timed_agent, "starter"])
    
    lat = np.array(latencies)
    print(f"Total Steps Measured: {len(lat)}")
    print(f"Mean Latency:   {np.mean(lat):6.2f} ms")
    print(f"Median (p50):   {np.median(lat):6.2f} ms")
    print(f"p95 Latency:    {np.percentile(lat, 95):6.2f} ms")
    print(f"p99 Latency:    {np.percentile(lat, 99):6.2f} ms")
    print(f"Max Latency:    {np.max(lat):6.2f} ms")
    print(f"Total Turn Time: {np.sum(lat)/1000.0:6.2f} s")

# 2. Part 27 & 28: Memory Leak and Cross-Game Reset Test
def test_memory_and_reset(episodes=15):
    print("\n" + "="*80)
    print(f"PART 27 & 28 — MEMORY LEAK & CROSS-GAME RESET TEST ({episodes} EPISODES)")
    print("="*80)
    
    shared_agent = Hybrid6C3S10MAgent()
    
    tracemalloc.start()
    snapshot_start = tracemalloc.take_snapshot()
    
    cashes = []
    for ep in range(episodes):
        env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": 10001 + ep}, debug=False)
        env.run([shared_agent, "starter"])
        cashes.append(env.steps[-1][0].reward)
        
    snapshot_end = tracemalloc.take_snapshot()
    top_stats = snapshot_end.compare_to(snapshot_start, 'lineno')
    
    print("Memory Allocation Growth (Top 3):")
    for stat in top_stats[:3]:
        print(" ", stat)
        
    # Check if cross-game rerun gives same result on seed 10001
    env_clean = make("kaggriculture", configuration={"episodeSteps": 720, "seed": 10001}, debug=False)
    env_clean.run([Hybrid6C3S10MAgent(), "starter"])
    clean_reward = env_clean.steps[-1][0].reward
    
    env_reused = make("kaggriculture", configuration={"episodeSteps": 720, "seed": 10001}, debug=False)
    env_reused.run([shared_agent, "starter"])
    reused_reward = env_reused.steps[-1][0].reward
    
    print(f"\nFresh Agent on Seed 10001:  ${clean_reward:,.2f}")
    print(f"Reused Agent on Seed 10001: ${reused_reward:,.2f}")
    if clean_reward == reused_reward:
        print("  -> PASSED: Cross-game state is fully stateless (Zero cross-game state pollution)!")
    else:
        print("  -> FAILED: State leaked across games!")

# 3. Part 29: Player-Side Symmetry
def test_side_symmetry(seeds=[10001, 10002, 10003, 10004, 10005]):
    print("\n" + "="*80)
    print("PART 29 — PLAYER-SIDE SYMMETRY TEST (P0 vs P1)")
    print("="*80)
    
    agent_path = "agents/hybrid_6c3s_10m.py"
    opp_path = "agents/golden_v1.py"
    
    p0_cashes = []
    p1_cashes = []
    
    for s in seeds:
        env0 = make("kaggriculture", configuration={"episodeSteps": 720, "seed": s}, debug=False)
        env0.run([agent_path, opp_path])
        p0_cashes.append(env0.steps[-1][0].reward)
        
        env1 = make("kaggriculture", configuration={"episodeSteps": 720, "seed": s}, debug=False)
        env1.run([opp_path, agent_path])
        p1_cashes.append(env1.steps[-1][1].reward)
        
    print(f"Agent as Player 0 Mean: ${np.mean(p0_cashes):10,.2f}")
    print(f"Agent as Player 1 Mean: ${np.mean(p1_cashes):10,.2f}")
    print(f"Side Difference (P0 - P1): ${np.mean(p0_cashes) - np.mean(p1_cashes):+10,.2f}")

if __name__ == "__main__":
    test_runtime_profiling()
    test_memory_and_reset(15)
    test_side_symmetry()
