import os, sys, importlib.util
base_dir = r"c:\Users\Sundareswaran\Kagriculture"
sys.path.insert(0, os.path.join(base_dir, "external_repos", "kaggriculture-cppsim"))
sys.path.insert(0, os.path.join(base_dir, "candidates", "closed_loop_architecture"))

import kagsim
from dev_004_joint_macro_scheduler import Dev004JointMacroScheduler, BASELINE_PATH

spec = importlib.util.spec_from_file_location("base_check", BASELINE_PATH)
base_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base_mod)

# Class that disables reversal: once specialized, stays specialized!
class NoReversalCandidate(Dev004JointMacroScheduler):
    def evaluate_checkpoints(self, obs, step):
        super().evaluate_checkpoints(obs, step)
        # If we were specialized, do not revert to BASELINE_BACKBONE!
        # Unless safety override
        # Here: pure counterfactual test: keep initial specialization
        if hasattr(self, '_committed_plan') and self._committed_plan is not None:
            self.active_plan = self._committed_plan
            self.active_policy = self.policy_registry[self.active_plan]
        else:
            if self.active_plan != "BASELINE_BACKBONE":
                self._committed_plan = self.active_plan

for seed in [246003, 246005, 246007, 246022, 246028, 246030, 246032, 246035, 246036, 246039, 246042, 246049]:
    g = kagsim.Game(seed)
    cand_cf = NoReversalCandidate(seat=0, seed=seed)
    base = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(base)
    
    while not g.done:
        o0 = g.observe(0)
        o1 = g.observe(1)
        a0 = cand_cf.act(o0)
        a1 = base.agent(o1)
        g.step(a0, a1)
        
    cf_delta = float(g.reward(0)) - float(g.reward(1))
    print(f"Seed {seed}: Original Match 0 delta vs Counterfactual (No Reversal) delta: {cf_delta:+.1f}")
