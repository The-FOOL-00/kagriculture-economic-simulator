# SPDX-License-Identifier: MIT
"""V32 P4 Economic Counterfactual:
Compares the economic trajectory of:
  A) P3 Baseline (reversed wash [SELL30, BUY30])
  B) P3 Baseline with Step-0 Market Action Replaced by Expert Wash ([BUY30, SELL30])
  C) P4 Arm 1 (naturally predicts [BUY30, SELL30])
"""

import json
import os
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, REPO_ROOT)
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))

import numpy as np
import torch
from kaggle_environments import make
from v32_common import check_seed_allowed, load_agent
from v32.p2.essentials import essentialize
from v32.p2.features import Normalizer
from v32.p3.models import P3Policy
from v32.p3.rollout import Predictor

def run_counterfactual():
    norm = Normalizer.from_json(json.load(open(os.path.join(REPO_ROOT, "results", "v32_p2_norm.json"))))
    
    # Load P3 baseline model
    p3_model = P3Policy(157, 12)
    p3_d = np.load(os.path.join(REPO_ROOT, "results", "v32_p3_bc.npz"), allow_pickle=True)
    p3_model.load_state_dict({k: torch.tensor(v) for k, v in p3_d.items() if k != "meta"})
    p3_model.eval()
    
    # Load P4 Arm 1 model
    p4_model = P3Policy(157, 12)
    p4_d = np.load(os.path.join(REPO_ROOT, "results", "v32_p4_arm1_balanced.npz"), allow_pickle=True)
    p4_model.load_state_dict({k: torch.tensor(v) for k, v in p4_d.items() if k != "meta"})
    p4_model.eval()
    
    seeds = [249675, 249676, 249677]
    opp_name = "E2_A7"
    opp_ag = load_agent(opp_name)
    
    results = []
    
    for s in seeds:
        # Condition A: P3 Baseline
        pred_p3 = Predictor(p3_model, norm)
        pred_p3.reset()
        env_a = make("kaggriculture", configuration={"seed": s})
        env_a.run([
            lambda obs, cfg=None: pred_p3.step(essentialize(obs, 0), deterministic=True)["action"],
            lambda obs, cfg=None: opp_ag.act(obs, cfg)
        ])
        cash_a = float(env_a.steps[-1][0]["reward"])
        step0_m_a = env_a.steps[1][0]["action"].get("market", []) # action applied in step 0
        
        # Condition B: P3 Baseline with Step 0 Market Spliced to Correct Wash
        pred_p3_cf = Predictor(p3_model, norm)
        pred_p3_cf.reset()
        env_b = make("kaggriculture", configuration={"seed": s})
        step_b = [0]
        def learner_b(obs, cfg=None):
            pr = pred_p3_cf.step(essentialize(obs, 0), deterministic=True)
            act = pr["action"]
            if step_b[0] == 0:
                act["market"] = [["BUY_PRODUCT", "WHEAT", 30], ["SELL", "WHEAT", 30]]
            step_b[0] += 1
            return act
        env_b.run([learner_b, lambda obs, cfg=None: opp_ag.act(obs, cfg)])
        cash_b = float(env_b.steps[-1][0]["reward"])
        
        # Condition C: P4 Arm 1 (End-to-End Autonomous)
        pred_p4 = Predictor(p4_model, norm)
        pred_p4.reset()
        env_c = make("kaggriculture", configuration={"seed": s})
        env_c.run([
            lambda obs, cfg=None: pred_p4.step(essentialize(obs, 0), deterministic=True)["action"],
            lambda obs, cfg=None: opp_ag.act(obs, cfg)
        ])
        cash_c = float(env_c.steps[-1][0]["reward"])
        
        rec = {
            "seed": s,
            "p3_baseline_cash": cash_a,
            "p3_spliced_wash_cash": cash_b,
            "p4_arm1_cash": cash_c
        }
        results.append(rec)
        print(f"Seed {s}: P3 Baseline=${cash_a:.1f} | P3 + Spliced Wash=${cash_b:.1f} | P4 Arm 1=${cash_c:.1f}", flush=True)
        
    out_pth = os.path.join(REPO_ROOT, "results", "v32_p4_counterfactual.json")
    with open(out_pth, "w") as f:
        json.dump(results, f, indent=1)
    print(f"Wrote counterfactual results to {out_pth}")

if __name__ == "__main__":
    run_counterfactual()
