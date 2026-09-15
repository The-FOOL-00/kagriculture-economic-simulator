import os, sys, importlib.util
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

step = 0
while not g.done:
    o0 = g.observe(0)
    o1 = g.observe(1)
    a0 = cand.act(o0)
    a1 = base_mod.agent(o1)
    g.step(a0, a1)
    step += 1

print("Seed 246002 decision events:")
for ev in cand.decision_events:
    print(ev)
