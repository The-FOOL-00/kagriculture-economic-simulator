# SPDX-License-Identifier: MIT
"""V32 P4 Trajectory Inspector: inspects the rollout of Arm 1."""

import json
import os
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, REPO_ROOT)
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))

import torch
import numpy as np
from kaggle_environments import make
from v32_common import check_seed_allowed, load_agent
from v32.p2.essentials import essentialize
from v32.p2.features import Normalizer
from v32.p3.models import P3Policy
from v32.p3.rollout import Predictor

def inspect_trajectory():
    norm = Normalizer.from_json(json.load(open(os.path.join(REPO_ROOT, "results", "v32_p2_norm.json"))))
    model = P3Policy(157, 12)
    d = np.load(os.path.join(REPO_ROOT, "results/v32_p4_arm1_balanced.npz"), allow_pickle=True)
    model.load_state_dict({k: torch.tensor(v) for k, v in d.items() if k != "meta"})
    model.eval()
    
    pred = Predictor(model, norm)
    pred.reset()
    opp_ag = load_agent("E2_A7")
    
    seed = 249675
    env = make("kaggriculture", configuration={"seed": seed})
    
    actions_taken = []
    
    def learner_act(obs, cfg=None):
        step_idx = len(actions_taken)
        pr = pred.step(essentialize(obs, 0), deterministic=True)
        actions_taken.append((step_idx, pr["action"]))
        return pr["action"]
        
    def opp_act(obs, cfg=None):
        return opp_ag.act(obs, cfg)
        
    env.run([learner_act, opp_act])
    
    print(f"Total steps: {len(actions_taken)}")
    print(f"Final reward: {env.steps[-1][0]['reward']}")
    
    # Inspect first 10 steps
    print("\n--- First 10 steps actions and farm state ---")
    for s_idx in range(10):
        obs = env.steps[s_idx][0]["observation"]
        farm = obs["farms"][0]
        act = actions_taken[s_idx][1]
        inv = obs.get("inventory", [{}])[0]
        print(f"Step {s_idx}: money={farm['money']:.1f}, hands={len(farm['hands'])}, inv={inv}, act={act}")
        
    # Inspect steps where big money changes happened
    print("\n--- Significant transitions ---")
    for s_idx in range(1, len(actions_taken)):
        f_prev = env.steps[s_idx-1][0]["observation"]["farms"][0]
        f_curr = env.steps[s_idx][0]["observation"]["farms"][0]
        dm = f_curr["money"] - f_prev["money"]
        if abs(dm) > 500:
            act = actions_taken[s_idx][1]
            print(f"Step {s_idx}: money {f_prev['money']:.1f} -> {f_curr['money']:.1f} (delta={dm:+.1f}), hands={len(f_curr['hands'])}, act={act}")

if __name__ == "__main__":
    inspect_trajectory()
