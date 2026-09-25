# SPDX-License-Identifier: MIT
"""
Train Supervised Option Selector (Experiment P12-06 & P12-08).
Extracts 71-dim economic feature vectors for the 60 search targets and negative A7 states,
trains the SupervisedOptionSelector across multiple random seeds,
and evaluates classification accuracy, precision, and false-positive rate.
"""

import copy
import json
import os
import sys
import time
from typing import Any, Dict, List, Tuple
import numpy as np
import torch

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from kaggle_environments import make
from candidates.v32_rlx2.opponents import load_league_opponent
from candidates.v32_rlx2.state import extract_economic_features, vectorize_features
from candidates.v32_p12_options.supervised import (
    SupervisedOptionSelector,
    MACRO_ACTION_TO_OPTION_IDX,
    OPTION_INDEX_TO_ID
)
from candidates.v32_p12_options.evaluator import _get_shared_obs
from scripts.v32_common import load_agent

def build_dataset_with_features() -> List[Dict[str, Any]]:
    repro_path = os.path.join(REPO_ROOT, "candidates/v32_p12_options/reports/p12_01_reproduction.json")
    with open(repro_path, "r") as f:
        repro_data = json.load(f)

    print(f"Loaded {len(repro_data)} targets from reproduction artifact.")
    dataset = []

    # Cache rollouts by (seed, opponent)
    rollouts = {}
    
    unique_pairs = {(d["seed"], d["opponent"]): [] for d in repro_data}
    for d in repro_data:
        unique_pairs[(d["seed"], d["opponent"])].append(d)

    print(f"Rolling out {len(unique_pairs)} match trajectories to extract 71-dim feature vectors...")
    for (seed, opp_id), targets in unique_pairs.items():
        env = make("kaggriculture", configuration={"seed": seed})
        env.reset()
        a7_agent = load_agent("E9_AST")
        opp_agent = load_league_opponent(opp_id)

        target_steps = {t["step"]: t for t in targets}
        # Also sample negative steps (where A7 is optimal and no option should trigger)
        negative_steps = {step for step in range(24, 336, 24) if step not in target_steps}

        step = 0
        while not env.done:
            p_obs = _get_shared_obs(env, 0)
            opp_obs = _get_shared_obs(env, 1)

            if step in target_steps:
                t = target_steps[step]
                feat = extract_economic_features(p_obs, player=0)
                rec = copy.deepcopy(t)
                rec["state_vector"] = vectorize_features(feat, tier="S2").tolist()
                dataset.append(rec)

            elif step in negative_steps and step % 48 == 0:
                # Add negative target (FOLLOW_A7)
                feat = extract_economic_features(p_obs, player=0)
                rec = {
                    "seed": seed,
                    "step": step,
                    "opponent": opp_id,
                    "seat": 0,
                    "candidate": 0,
                    "candidate_name": "FOLLOW_A7",
                    "terminal_delta": 0.0,
                    "reproduced": True,
                    "state_vector": vectorize_features(feat, tier="S2").tolist()
                }
                dataset.append(rec)

            act0 = a7_agent.act(p_obs)
            act1 = opp_agent(opp_obs)
            env.step([act0, act1])
            step += 1

    print(f"Constructed supervised dataset with {len(dataset)} feature vectors.")
    return dataset

def main():
    print("Starting Supervised Option Selector Training (P12-06 / P12-08)...")
    dataset = build_dataset_with_features()

    seeds = [42, 137, 2026]
    results = {}

    save_dir = os.path.join(REPO_ROOT, "candidates/v32_p12_options/checkpoints")
    os.makedirs(save_dir, exist_ok=True)

    for s in seeds:
        torch.manual_seed(s)
        np.random.seed(s)
        selector = SupervisedOptionSelector(confidence_threshold=0.65)
        ckpt_path = os.path.join(save_dir, f"supervised_selector_seed_{s}.pt")
        
        train_res = selector.train_on_targets(
            dataset=dataset,
            epochs=50,
            batch_size=8,
            lr=1e-3,
            min_value_gap=100.0,
            save_path=ckpt_path
        )
        
        # Evaluate on the dataset
        correct = 0
        total = 0
        option_tp = 0
        option_fp = 0
        option_fn = 0
        
        for item in dataset:
            vec = np.array(item["state_vector"], dtype=np.float32)
            true_cand = item.get("candidate", 0)
            true_cls = MACRO_ACTION_TO_OPTION_IDX.get(true_cand, 0)
            
            pred_cls, conf, reason = selector.select_option(vec)
            
            if pred_cls == true_cls:
                correct += 1
            if pred_cls != 0 and true_cls != 0:
                option_tp += 1
            elif pred_cls != 0 and true_cls == 0:
                option_fp += 1
            elif pred_cls == 0 and true_cls != 0:
                option_fn += 1
                
            total += 1

        acc = correct / max(1, total)
        prec = option_tp / max(1, option_tp + option_fp)
        rec = option_tp / max(1, option_tp + option_fn)
        fp_rate = option_fp / max(1, total)

        results[f"seed_{s}"] = {
            "seed": s,
            "final_loss": train_res["final_loss"],
            "accuracy": float(acc),
            "precision": float(prec),
            "recall": float(rec),
            "false_positive_rate": float(fp_rate),
            "checkpoint": ckpt_path
        }
        print(f"[Seed {s}] Acc={acc*100:.1f}%, Prec={prec*100:.1f}%, Rec={rec*100:.1f}%, FPR={fp_rate*100:.1f}%, Loss={train_res['final_loss']:.4f}")

    out_path = os.path.join(REPO_ROOT, "candidates/v32_p12_options/reports/p12_06_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Saved supervised selector evaluation to {out_path}")

if __name__ == "__main__":
    main()
