import os
import sys
import hashlib
import time
import importlib.util
from kaggle_environments import make

project_root = r"c:\Users\Sundareswaran\Kagriculture"
if project_root not in sys.path:
    sys.path.insert(0, project_root)

print("=" * 80)
print("INDEPENDENT REPOSITORY INFRASTRUCTURE & REPRODUCIBILITY AUDIT")
print("=" * 80)

# 1. Environment Verification
env = make("kaggriculture")
print(f"Kaggle Environment: kaggriculture")
print(f"Configuration: {env.configuration}")
print(f"Episode Steps: {env.configuration.get('episodeSteps')}")
print(f"Turns Per Day: {env.configuration.get('turnsPerDay')}")
print(f"Total Days: {env.configuration.get('episodeSteps') // env.configuration.get('turnsPerDay')}")

# 2. File Hashes
files_to_hash = [
    "agents/slot4_control_frozen_v2.py",
    "agents/golden_v1.py",
    "agents/ablation_batch_14.py",
    "agents/ablation_batch_24.py",
    "agents/ablation_b_emergency_only.py",
    "opponents/o1_titan.py",
    "main.py",
    "compiler.py",
    "config.py",
    "benchmark_harness.py",
    "tournament_engine.py"
]

print("\n--- Canonical File SHA256 Hashes ---")
hashes = {}
for rel_path in files_to_hash:
    abs_path = os.path.join(project_root, rel_path)
    if os.path.exists(abs_path):
        with open(abs_path, "rb") as f:
            h = hashlib.sha256(f.read()).hexdigest()
            hashes[rel_path] = h
            print(f"{rel_path:35s} : {h}")
    else:
        print(f"{rel_path:35s} : NOT FOUND")

# 3. Behavioral Equivalence Test
print("\n--- Behavioral Equivalence Verification ---")
# Check if ablation_batch_14 is byte/behaviorally equivalent to slot4_control_frozen_v2
def run_comparison(a0_path, a1_path, seed=50001):
    env1 = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed}, debug=False)
    env1.run([a0_path, "starter"])
    r1 = env1.steps[-1][0].reward

    env2 = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed}, debug=False)
    env2.run([a1_path, "starter"])
    r2 = env2.steps[-1][0].reward
    return r1, r2

r_control, r_batch14 = run_comparison(
    os.path.join(project_root, "agents/slot4_control_frozen_v2.py"),
    os.path.join(project_root, "agents/ablation_batch_14.py"),
    seed=50001
)
print(f"Control vs Batch-14 on Starter (seed 50001): Control=${r_control:,.2f} | Batch14=${r_batch14:,.2f} | Match: {r_control == r_batch14}")

# 4. Check Self-Play on Control
print("\n--- Control vs Control (Self-Play) Test ---")
env_sp = make("kaggriculture", configuration={"episodeSteps": 720, "seed": 50001}, debug=False)
ctrl_path = os.path.join(project_root, "agents/slot4_control_frozen_v2.py")
env_sp.run([ctrl_path, ctrl_path])
r0 = env_sp.steps[-1][0].reward
r1 = env_sp.steps[-1][1].reward
print(f"Self-play Seed 50001: P0=${r0:,.2f} vs P1=${r1:,.2f} | P0-P1 Diff: ${r0-r1:+,.2f}")

print("\nAudit initialization complete.")
