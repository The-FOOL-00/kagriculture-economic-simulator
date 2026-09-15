import os, sys, importlib.util
base_dir = r"c:\Users\Sundareswaran\Kagriculture"
sys.path.insert(0, os.path.join(base_dir, "external_repos", "kaggriculture-cppsim"))
sys.path.insert(0, os.path.join(base_dir, "candidates", "closed_loop_architecture"))

import kagsim
from dev_004_joint_macro_scheduler import Dev004JointMacroScheduler, BASELINE_PATH

spec = importlib.util.spec_from_file_location("base_check", BASELINE_PATH)
base_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base_mod)

from run_counterfactual_loss_seeds import CounterfactualNoReversalScheduler

s = 246048
# Trace orig vs CF on 246048
g_orig = kagsim.Game(s)
c_orig = Dev004JointMacroScheduler(seat=0, seed=s)
b_orig = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b_orig)

g_cf = kagsim.Game(s)
c_cf = CounterfactualNoReversalScheduler(seat=0, seed=s)
b_cf = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b_cf)

checkpoints = [72, 144, 150, 195, 216, 288, 300, 500, 719]

step = 0
while not g_orig.done:
    o_orig = g_orig.observe(0)
    o_cf = g_cf.observe(0)
    
    a_orig = c_orig.act(o_orig)
    a_cf = c_cf.act(o_cf)
    
    g_orig.step(a_orig, b_orig.agent(g_orig.observe(1)))
    g_cf.step(a_cf, b_cf.agent(g_cf.observe(1)))
    
    if step in checkpoints:
        f_orig = o_orig['farms'][0]
        f_cf = o_cf['farms'][0]
        print(f"Step {step:3d}: Orig Cash={f_orig['money']:8.1f} (Hands={len(f_orig.get('hands', []))}) | CF Cash={f_cf['money']:8.1f} (Hands={len(f_cf.get('hands', []))})")
        
    step += 1

print(f"Terminal Reward: Orig={g_orig.reward(0)} | CF={g_cf.reward(0)} | Baseline={g_orig.reward(1)}")
