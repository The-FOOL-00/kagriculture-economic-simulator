import os
import sys
import importlib.util

base_dir = r"c:\Users\Sundareswaran\Kagriculture"
sys.path.insert(0, os.path.join(base_dir, "external_repos", "kaggriculture-cppsim"))
sys.path.insert(0, os.path.join(base_dir, "candidates", "closed_loop_architecture"))

import kagsim
from dev_004_joint_macro_scheduler import Dev004JointMacroScheduler, BASELINE_PATH

spec = importlib.util.spec_from_file_location("base_check", BASELINE_PATH)
base_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base_mod)

seed = 246002
g = kagsim.Game(seed)
cand = Dev004JointMacroScheduler(seat=0, seed=seed)
base = base_mod

diff_steps = []
step = 0
while not g.done:
    o0 = g.observe(0)
    o1 = g.observe(1)
    a0 = cand.act(o0)
    a1 = base.agent(o1)
    # also see what baseline would do in seat 0
    a0_base = base.agent(o0)
    if a0 != a0_base:
        diff_steps.append((step, a0, a0_base))
    g.step(a0, a1)
    step += 1

print(f"Seed {seed}: total steps={step}, different actions between cand(seat 0) and base(seat 0): {len(diff_steps)}")
if diff_steps:
    print(f"First 5 diff steps: {diff_steps[:5]}")
else:
    print("Bit-for-bit identical actions across all 720 steps!")
