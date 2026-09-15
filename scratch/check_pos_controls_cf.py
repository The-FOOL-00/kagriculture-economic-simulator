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

for s in [246012, 246026, 246034, 246048]:
    # Orig match 0
    g0 = kagsim.Game(s)
    c0 = Dev004JointMacroScheduler(seat=0, seed=s)
    b0 = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(b0)
    while not g0.done:
        g0.step(c0.act(g0.observe(0)), b0.agent(g0.observe(1)))
    orig_d = float(g0.reward(0)) - float(g0.reward(1))

    # CF match 0 (no reversal)
    g1 = kagsim.Game(s)
    c1 = CounterfactualNoReversalScheduler(seat=0, seed=s)
    b1 = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(b1)
    while not g1.done:
        g1.step(c1.act(g1.observe(0)), b1.agent(g1.observe(1)))
    cf_d = float(g1.reward(0)) - float(g1.reward(1))

    print(f"Positive Control {s}: Orig Delta = {orig_d:+8.1f} | CF (No Reversal) Delta = {cf_d:+8.1f} | Net = {cf_d - orig_d:+8.1f}")
