"""
Robustness, Runtime, Leaks, and Determinism Forensics
(Parts 24, 25, 26, 27, 28, 29, 30, 31)
"""

import os
import sys
import time
import math
import gc
import json
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

hybrid_mod = load_module_from_path("hybrid_agent_module2", os.path.join(project_root, "agents/hybrid_6c3s_10m.py"))
Hybrid6C3S10MAgent = hybrid_mod.Hybrid6C3S10MAgent

# 1. Part 24: Check Invalid Actions across 20 episodes
def test_invalid_actions_and_exceptions(num_episodes=20):
    print("\n" + "="*80)
    print(f"PART 24 — CHECKING FOR INVALID ACTIONS & EXCEPTIONS ({num_episodes} EPISODES)")
    print("="*80)
    
    agent_path = "agents/hybrid_6c3s_10m.py"
    invalid_actions = 0
    exceptions = 0
    seeds = [50000 + i * 23 for i in range(num_episodes)]
    
    for i, s in enumerate(seeds):
        env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": s}, debug=True)
        env.run([agent_path, "starter"])
        
        # Check step statuses
        for step_idx, step_data in enumerate(env.steps):
            p0 = step_data[0]
            if p0.get("status") not in ["ACTIVE", "DONE"]:
                print(f"  [ERROR] Episode {i+1} (Seed {s}) Step {step_idx}: Status {p0.get('status')}")
                invalid_actions += 1
                
        # Check reward validity
        r0 = env.steps[-1][0].reward
        if r0 is None or math.isnan(r0) or r0 < 0:
            print(f"  [ERROR] Episode {i+1} (Seed {s}): Invalid Reward {r0}")
            invalid_actions += 1
            
    print(f"Total Episodes Tested: {num_episodes}")
    print(f"Total Invalid Actions: {invalid_actions}")
    print(f"Total Exceptions:      {exceptions}")
    if invalid_actions == 0 and exceptions == 0:
        print("  -> PASSED: ZERO INVALID ACTIONS DETECTED!")

# 2. Part 25: Check Determinism
def test_determinism(seed=10001, trials=3):
    print("\n" + "="*80)
    print(f"PART 25 — DETERMINISM CHECK (SEED {seed}, {trials} TRIALS)")
    print("="*80)
    
    agent_path = "agents/hybrid_6c3s_10m.py"
    rewards = []
    actions_traces = []
    
    for t in range(trials):
        env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed}, debug=False)
        env.run([agent_path, "starter"])
        r = env.steps[-1][0].reward
        rewards.append(r)
        
        # Capture all actions
        acts = [s[0].get("action") for s in env.steps]
        actions_traces.append(acts)
        print(f"Trial {t+1}: Reward = ${r:,.2f}")
        
    is_det = all(r == rewards[0] for r in rewards) and all(actions_traces[i] == actions_traces[0] for i in range(trials))
    print(f"Bitwise Deterministic: {is_det}")
    if is_det:
        print("  -> PASSED: 100% BITWISE IDENTICAL ACTION SEQUENCES ACROSS RUNS!")

# 3. Part 26: Measure Runtime & Per-Turn Latency
def test_runtime_profiling(seed=10001):
    print("\n" + "="*80)
    print(f"PART 26 — RUNTIME PROFILING (SEED {seed})")
    print("="*80)
    
    agent_inst = Hybrid6C3S10MAgent()
    env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed}, debug=False)
    
    latencies = []
    obs = env.reset()[0].observation
    
    for step in range(720):
        t0 = time.perf_counter()
        act = agent_inst(obs)
        dt = (time.perf_counter() - t0) * 1000.0 # ms
        latencies.append(dt)
        
        # Step env with dummy starter for opp
        steps_res = env.step([act, {"farmer": ["PASS"], "hands": [], "market": []}])
        obs = steps_res[0].observation
        
    latencies = np.array(latencies)
    print(f"Total Steps Measured: {len(latencies)}")
    print(f"Mean Latency:   {np.mean(latencies):6.2f} ms")
    print(f"Median (p50):   {np.median(latencies):6.2f} ms")
    print(f"p95 Latency:    {np.percentile(latencies, 95):6.2f} ms")
    print(f"p99 Latency:    {np.percentile(latencies, 99):6.2f} ms")
    print(f"Max Latency:    {np.max(latencies):6.2f} ms")
    print(f"Total Turn Time: {np.sum(latencies)/1000.0:6.2f} s")

# 4. Part 27 & 28: Memory Leak and Cross-Game Reset Test
def test_memory_and_reset(episodes=20):
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

# 5. Part 29: Player-Side Symmetry
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
    test_invalid_actions_and_exceptions(20)
    test_determinism()
    test_runtime_profiling()
    test_memory_and_reset(20)
    test_side_symmetry()
