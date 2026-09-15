import os, sys, importlib.util
base_dir = r"c:\Users\Sundareswaran\Kagriculture"
sys.path.insert(0, os.path.join(base_dir, "external_repos", "kaggriculture-cppsim"))
sys.path.insert(0, os.path.join(base_dir, "candidates", "closed_loop_architecture"))

import kagsim
from dev_004_joint_macro_scheduler import Dev004JointMacroScheduler, BASELINE_PATH

spec = importlib.util.spec_from_file_location("base_check", BASELINE_PATH)
base_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base_mod)

for seed in [246003, 246007]:
    g = kagsim.Game(seed)
    cand = Dev004JointMacroScheduler(seat=0, seed=seed)
    base = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(base)
    
    # We step until step 144
    step = 0
    while not g.done and step < 144:
        o0 = g.observe(0)
        o1 = g.observe(1)
        a0 = cand.act(o0)
        a1 = base.agent(o1)
        g.step(a0, a1)
        step += 1
        
    obs0 = g.observe(0)
    obs1 = g.observe(1)
    f0 = obs0['farms'][0]
    f1 = obs1['farms'][1]
    
    print(f"\nSeed {seed} at Step 144:")
    print(f"  Cand seat 0 money: {f0['money']} | Base seat 1 money: {f1['money']} (Diff: {f0['money'] - f1['money']})")
    
    cand_hands = [(h['x'], h['y']) for h in f0.get('hands', [])]
    base_hands = [(h['x'], h['y']) for h in f1.get('hands', [])]
    print(f"  Cand worker positions: {cand_hands}")
    print(f"  Base worker positions: {base_hands}")
    print(f"  Workers matching: {cand_hands == base_hands}")
