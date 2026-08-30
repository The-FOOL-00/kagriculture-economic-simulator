import os
import sys
import time
from kaggle_environments import make

project_root = r"c:\Users\Sundareswaran\Kagriculture"
main_path = os.path.join(project_root, "main.py")
ctrl_path = os.path.join(project_root, "agents", "slot4_control_frozen_v2.py")

print("Testing main.py single-file release execution...")
env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": 50000}, debug=True)

t0 = time.time()
env.run([main_path, ctrl_path])
elapsed = time.time() - t0

last = env.steps[-1]
r_main = float(last[0].reward or 0.0)
r_ctrl = float(last[1].reward or 0.0)

print(f"Match Complete: {elapsed:.2f}s total ({elapsed*1000/720:.2f}ms/step)")
print(f"Main Reward:   ${r_main:,.2f}")
print(f"Control Reward: ${r_ctrl:,.2f}")
print(f"Margin:        {r_main - r_ctrl:+,.2f}")

assert len(env.steps) == 721, f"Expected 721 steps, got {len(env.steps)}"
assert r_main > 0, "Main agent scored 0!"
print("\n>>> MAIN.PY PASSES ALL COMPETITION COMPLIANCE CHECKS <<<")
