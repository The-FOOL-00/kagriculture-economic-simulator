import os, sys, importlib.util
base_dir = r"c:\Users\Sundareswaran\Kagriculture"
sys.path.insert(0, os.path.join(base_dir, "external_repos", "kaggriculture-cppsim"))
sys.path.insert(0, os.path.join(base_dir, "candidates", "closed_loop_architecture"))

import kagsim
from dev_004_joint_macro_scheduler import Dev004JointMacroScheduler, BASELINE_PATH

spec = importlib.util.spec_from_file_location("base_check", BASELINE_PATH)
base_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base_mod)

class CounterfactualNoReversalScheduler(Dev004JointMacroScheduler):
    def __init__(self, seat=0, seed=0):
        super().__init__(seat=seat, seed=seed)
        self.committed_plan = None

    def evaluate_checkpoints(self, obs, step):
        super().evaluate_checkpoints(obs, step)
        if self.committed_plan is not None:
            # Enforce commitment
            self.active_plan = self.committed_plan
            self.active_policy = self.policy_registry[self.committed_plan]
        else:
            if self.active_plan != "BASELINE_BACKBONE":
                self.committed_plan = self.active_plan

seeds = [246003, 246005, 246007, 246022, 246028, 246030, 246032, 246035, 246036, 246039, 246042, 246049]

print("Seed | Orig M0 Delta | CF M0 Delta | CF Gain vs Orig")
for s in seeds:
    # Orig match 0 delta
    g0 = kagsim.Game(s)
    c0 = Dev004JointMacroScheduler(seat=0, seed=s)
    b0 = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(b0)
    while not g0.done:
        g0.step(c0.act(g0.observe(0)), b0.agent(g0.observe(1)))
    orig_d = float(g0.reward(0)) - float(g0.reward(1))
    
    # CF match 0 delta
    g1 = kagsim.Game(s)
    c1 = CounterfactualNoReversalScheduler(seat=0, seed=s)
    b1 = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(b1)
    while not g1.done:
        g1.step(c1.act(g1.observe(0)), b1.agent(g1.observe(1)))
    cf_d = float(g1.reward(0)) - float(g1.reward(1))
    
    print(f"{s} | {orig_d:+13.1f} | {cf_d:+11.1f} | {cf_d - orig_d:+15.1f}")
