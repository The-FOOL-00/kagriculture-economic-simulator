import os
import sys
import importlib.util
import pandas as pd
import json

base_dir = r"c:\Users\Sundareswaran\Kagriculture"
sys.path.insert(0, os.path.join(base_dir, "external_repos", "kaggriculture-cppsim"))
sys.path.insert(0, os.path.join(base_dir, "candidates", "closed_loop_architecture"))

import kagsim
from dev_004_joint_macro_scheduler import Dev004JointMacroScheduler, BASELINE_PATH

spec = importlib.util.spec_from_file_location("base_check", BASELINE_PATH)
base_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base_mod)

bb_nonzero_seeds = [246003, 246005, 246007, 246022, 246026, 246028, 246030, 246032, 246034, 246035, 246036, 246039, 246042, 246049]

# Let's check what animals or assets were bought by candidate between step 72 and step 144 (or step 216)
for seed in [246003, 246007, 246026, 246035]:
    g = kagsim.Game(seed)
    cand = Dev004JointMacroScheduler(seat=0, seed=seed)
    base = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(base)
    
    cand_purchases = []
    base_purchases = []
    
    step = 0
    while not g.done and step <= 250:
        o0 = g.observe(0)
        o1 = g.observe(1)
        a0 = cand.act(o0)
        a1 = base.agent(o1)
        
        # Check market actions in a0 and a1
        for m in a0.get('market', []):
            if m[0] == 'BUY_ANIMAL':
                cand_purchases.append((step, m))
        for m in a1.get('market', []):
            if m[0] == 'BUY_ANIMAL':
                base_purchases.append((step, m))
                
        g.step(a0, a1)
        step += 1
        
    print(f"\nSeed {seed}:")
    print(f"  Candidate animal purchases: {cand_purchases}")
    print(f"  Baseline animal purchases: {base_purchases}")
