import os, sys, importlib.util
base_dir = r"c:\Users\Sundareswaran\Kagriculture"
sys.path.insert(0, os.path.join(base_dir, "external_repos", "kaggriculture-cppsim"))
sys.path.insert(0, os.path.join(base_dir, "candidates", "closed_loop_architecture"))

import kagsim
from dev_004_joint_macro_scheduler import Dev004JointMacroScheduler, BASELINE_PATH

spec = importlib.util.spec_from_file_location("base_check", BASELINE_PATH)
base_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base_mod)

seed = 246007
g = kagsim.Game(seed)
cand = Dev004JointMacroScheduler(seat=0, seed=seed)
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)

step = 0
checkpoints = [144, 168, 192, 216, 240, 264, 288, 360, 480, 600, 719]
while not g.done:
    o0 = g.observe(0)
    o1 = g.observe(1)
    a0 = cand.act(o0)
    a1 = base.agent(o1)
    if step in checkpoints:
        f0 = o0['farms'][0]
        f1 = o1['farms'][1]
        print(f"Step {step:3d} (Day {step//24:2d}): Cand Money={f0['money']:8.1f} | Base Money={f1['money']:8.1f} | Diff={f0['money'] - f1['money']:+8.1f}")
    g.step(a0, a1)
    step += 1

print(f"Terminal Reward: Cand={g.reward(0)} | Base={g.reward(1)} | Final Delta={g.reward(0) - g.reward(1)}")
