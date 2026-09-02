import os
import sys
import time
from kaggle_environments import make

v2_path = "candidates/slot2_aethel_refined_v2.py"
kawatta_path = "opponents/replay_kawatta_taido.py"

print("Testing V2 vs Replay KawattaTaido...")

# Run match with seed 42
cfg = {"episodeSteps": 720, "seed": 42}
env = make("kaggriculture", configuration=cfg, debug=False)

t0 = time.time()
# Kawatta as P0, V2 as P1 (matching the live match!)
env.run([kawatta_path, v2_path])
dur = time.time() - t0

r0 = float(env.steps[-1][0].reward or 0)
r1 = float(env.steps[-1][1].reward or 0)

print(f"Outcome in {dur:.2f}s:")
print(f"KawattaTaido (P0): ${r0:,.0f}")
print(f"V2 (P1):           ${r1:,.0f}")
print(f"Margin (V2 - Kawatta): ${r1 - r0:+,.0f}")

# Also test swapped
print("\nTesting swapped positions (V2 as P0, Kawatta as P1)...")
env2 = make("kaggriculture", configuration=cfg, debug=False)
env2.run([v2_path, kawatta_path])
r0_s = float(env2.steps[-1][0].reward or 0)
r1_s = float(env2.steps[-1][1].reward or 0)
print(f"V2 (P0):           ${r0_s:,.0f}")
print(f"KawattaTaido (P1): ${r1_s:,.0f}")
print(f"Margin (V2 - Kawatta): ${r0_s - r1_s:+,.0f}")
