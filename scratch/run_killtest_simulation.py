import os
import sys
import importlib.util
import pandas as pd
import json

base_dir = r"c:\Users\Sundareswaran\Kagriculture"
sys.path.insert(0, os.path.join(base_dir, "external_repos", "kaggriculture-cppsim"))
sys.path.insert(0, os.path.join(base_dir, "candidates", "closed_loop_architecture"))
sys.path.insert(0, os.path.join(base_dir, "scratch"))

import kagsim
from dev_004_joint_macro_scheduler import Dev004JointMacroScheduler, BASELINE_PATH, L_MIN, TAU

spec = importlib.util.spec_from_file_location("base_check", BASELINE_PATH)
base_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base_mod)

class HysteresisCommitmentGuardScheduler(Dev004JointMacroScheduler):
    """
    Candidate with HYSTERESIS_COMMITMENT_GUARD.
    Single structural change:
    Once committed to a specialized route (active_plan != 'BASELINE_BACKBONE' after step 72),
    reversion to 'BASELINE_BACKBONE' is disallowed solely because best_delta < TAU.
    Hard Safety Exception:
    Reversion IS permitted IF liquidity falls below the frozen minimum liquidity floor (money < L_MIN).
    """
    def __init__(self, seat=0, seed=0):
        super().__init__(seat=seat, seed=seed)
        self.committed_plan = None
        self.guard_activated = False
        self.safety_override_triggered = False

    def evaluate_checkpoints(self, obs, step):
        super().evaluate_checkpoints(obs, step)
        
        # Check if we have an active specialized commitment
        farms = obs.get("farms", [])
        seat = int(obs.get("player", self.seat) or 0)
        farm = farms[seat] if seat < len(farms) else {}
        money = float(farm.get("money", 0.0) or 0.0)

        if self.committed_plan is not None:
            # We are in a committed specialized route
            if self.active_plan == "BASELINE_BACKBONE":
                # Original planner wanted to revert!
                # Check pre-specified hard safety exception:
                if money < L_MIN:
                    # Hard safety override triggered: allow exit to baseline
                    self.safety_override_triggered = True
                    self.active_plan = "BASELINE_BACKBONE"
                    self.active_policy = self.policy_registry["BASELINE_BACKBONE"]
                else:
                    # Commitment Guard enforces continuation: block reversion!
                    self.guard_activated = True
                    self.active_plan = self.committed_plan
                    self.active_policy = self.policy_registry[self.committed_plan]
        else:
            # First time specializing
            if self.active_plan != "BASELINE_BACKBONE":
                self.committed_plan = self.active_plan


loss_seeds = [246003, 246005, 246007, 246008, 246010, 246016, 246022, 246024, 246028, 246030, 246032, 246035, 246036, 246039, 246042, 246049]
pos_control_seeds = [246012, 246026, 246034, 246048]

def run_paired_crn(candidate_cls, seed):
    # Match 0: Candidate is Seat 0, Baseline is Seat 1
    g0 = kagsim.Game(seed)
    c0 = candidate_cls(seat=0, seed=seed)
    b0 = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(b0)
    while not g0.done:
        g0.step(c0.act(g0.observe(0)), b0.agent(g0.observe(1)))
    rew0_cand = float(g0.reward(0))
    rew0_base = float(g0.reward(1))
    delta0 = rew0_cand - rew0_base

    # Match 1: Baseline is Seat 0, Candidate is Seat 1
    g1 = kagsim.Game(seed)
    b1 = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(b1)
    c1 = candidate_cls(seat=1, seed=seed)
    while not g1.done:
        g1.step(b1.agent(g1.observe(0)), c1.act(g1.observe(1)))
    rew1_base = float(g1.reward(0))
    rew1_cand = float(g1.reward(1))
    delta1 = rew1_cand - rew1_base

    paired_mean_delta = 0.5 * (delta0 + delta1)
    guard_act = getattr(c0, 'guard_activated', False) or getattr(c1, 'guard_activated', False)
    safety_act = getattr(c0, 'safety_override_triggered', False) or getattr(c1, 'safety_override_triggered', False)
    
    return {
        "seed": seed,
        "m0_cand": rew0_cand,
        "m0_base": rew0_base,
        "m0_delta": delta0,
        "m1_cand": rew1_cand,
        "m1_base": rew1_base,
        "m1_delta": delta1,
        "paired_delta": paired_mean_delta,
        "c0_plans": [e['selected_plan'] for e in c0.decision_events],
        "c0_final_plan": c0.active_plan,
        "guard_activated": guard_act,
        "safety_override": safety_act
    }

print("Running 16 Loss Seeds under HYSTERESIS_COMMITMENT_GUARD:")
loss_results = []
for s in loss_seeds:
    res = run_paired_crn(HysteresisCommitmentGuardScheduler, s)
    loss_results.append(res)
    print(f"Seed {s}: paired_delta={res['paired_delta']:+8.1f} | guard_act={res['guard_activated']} | safety={res['safety_override']} | final={res['c0_final_plan']}")

print("\nRunning 4 Positive Control Seeds under HYSTERESIS_COMMITMENT_GUARD:")
control_results = []
for s in pos_control_seeds:
    res = run_paired_crn(HysteresisCommitmentGuardScheduler, s)
    control_results.append(res)
    print(f"Seed {s}: paired_delta={res['paired_delta']:+8.1f} | guard_act={res['guard_activated']} | safety={res['safety_override']} | final={res['c0_final_plan']}")

with open('scratch/killtest_loss_results.json', 'w') as f:
    json.dump(loss_results, f, indent=2)
with open('scratch/killtest_control_results.json', 'w') as f:
    json.dump(control_results, f, indent=2)
