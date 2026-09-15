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
while not g.done and step < 144:
    o0 = g.observe(0)
    o1 = g.observe(1)
    a0 = cand.act(o0)
    a1 = base.agent(o1)
    g.step(a0, a1)
    step += 1

f0 = g.observe(0)['farms'][0]
f1 = g.observe(1)['farms'][1]

for k in f0.keys():
    if k in ['tiles']:
        # check differing tiles
        diff_tiles = []
        for i, (t0, t1) in enumerate(zip(f0['tiles'], f1['tiles'])):
            if t0 != t1:
                diff_tiles.append((i, t0, t1))
        print(f"Diff tiles count: {len(diff_tiles)}")
        if diff_tiles:
            print(f"First 3 diff tiles: {diff_tiles[:3]}")
    else:
        if f0[k] != f1[k]:
            print(f"Key '{k}' diff: Cand={f0[k]} vs Base={f1[k]}")
