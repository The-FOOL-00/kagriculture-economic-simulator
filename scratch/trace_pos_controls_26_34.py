import os, sys, importlib.util
base_dir = r"c:\Users\Sundareswaran\Kagriculture"
sys.path.insert(0, os.path.join(base_dir, "external_repos", "kaggriculture-cppsim"))
sys.path.insert(0, os.path.join(base_dir, "candidates", "closed_loop_architecture"))

import kagsim
from dev_004_joint_macro_scheduler import Dev004JointMacroScheduler, BASELINE_PATH

spec = importlib.util.spec_from_file_location("base_check", BASELINE_PATH)
base_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base_mod)

for seed in [246026, 246034]:
    g = kagsim.Game(seed)
    cand = Dev004JointMacroScheduler(seat=0, seed=seed)
    base = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(base)
    
    step = 0
    while not g.done:
        o0 = g.observe(0)
        o1 = g.observe(1)
        a0 = cand.act(o0)
        a1 = base.agent(o1)
        if step in [72, 144, 216, 288, 500, 719]:
            f0 = o0['farms'][0]
            f1 = o1['farms'][1]
            print(f"Seed {seed} Step {step:3d}: Cand Money={f0['money']:8.1f} | Base Money={f1['money']:8.1f} | Diff={f0['money'] - f1['money']:+8.1f}")
        g.step(a0, a1)
        step += 1
    print(f"Seed {seed} Terminal: Cand={g.reward(0)} | Base={g.reward(1)} | Delta={g.reward(0) - g.reward(1)}\n")
