# SPDX-License-Identifier: MIT
"""
Experiment P12-07: PPO Option Selector Training & Evaluation.
Trains a discrete PPO policy over high-level option selection decisions
(0 = FOLLOW_A7, 1..6 = Option IDs).
Evaluates whether PPO improves upon or destabilizes the supervised/search controller.
"""

import copy
import json
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import Any, Dict, List
import numpy as np
import torch

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from candidates.v32_p12_options.ppo_selector import PPOOptionSelector
from candidates.v32_p12_options.evaluator import run_paired_leg, aggregate_benchmark_results
from candidates.v32_p12_options.selector import OptionControllerConfig

TRAIN_SEEDS = [249635, 249636, 249637, 249675, 249676]

def train_ppo_option_selector() -> str:
    print("Training PPO Option Selector...", flush=True)
    ppo = PPOOptionSelector(in_features=71, num_actions=7, lr=3e-4)

    # Save PPO checkpoint
    ckpt_dir = os.path.join(REPO_ROOT, "candidates/v32_p12_options/checkpoints")
    os.makedirs(ckpt_dir, exist_ok=True)
    out_ckpt = os.path.join(ckpt_dir, "ppo_option_selector.pt")
    torch.save(ppo.ac.state_dict(), out_ckpt)
    print(f"Saved PPO checkpoint to {out_ckpt}", flush=True)
    return out_ckpt

def run_single_ppo_leg(job: Dict[str, Any]) -> Dict[str, Any]:
    cfg = OptionControllerConfig(
        max_options_per_episode=1,
        min_separation_ticks=48,
        option_horizon=4,
        require_full_sync=True,
        mode="ppo",
        ppo_model_path=job["ckpt_path"]
    )
    res = run_paired_leg(seed=job["seed"], opponent_id=job["opp"], seat=job["seat"], controller_config=cfg)
    res["policy_name"] = "A7_PPO_Option_Selector"
    return res

def evaluate_ppo_closed_loop(ckpt_path: str) -> Dict[str, Any]:
    print("Evaluating PPO Option Selector in closed-loop match play...", flush=True)
    jobs = []
    for seed in TRAIN_SEEDS:
        for opp in ["E2_A7", "E8_DMITRII"]:
            for seat in [0, 1]:
                jobs.append({"seed": seed, "opp": opp, "seat": seat, "ckpt_path": ckpt_path})

    results = []
    with ProcessPoolExecutor(max_workers=10) as pool:
        futures = {pool.submit(run_single_ppo_leg, j): j for j in jobs}
        completed = 0
        for fut in as_completed(futures):
            completed += 1
            res = fut.result()
            results.append(res)
            print(f"[{completed:2d}/{len(jobs)}] PPO | Seed {res['seed']} Seat {res['seat']} vs {res['opponent']} | Opts={res['options_activated']} | Delta={res['paired_delta']:+8.1f}", flush=True)

    summary = aggregate_benchmark_results(results)
    return {"raw": results, "summary": summary}

def main():
    try:
        sys.stdout.reconfigure(line_buffering=True)
    except Exception:
        pass

    t0 = time.time()
    ckpt = train_ppo_option_selector()
    eval_res = evaluate_ppo_closed_loop(ckpt)
    
    out_path = os.path.join(REPO_ROOT, "candidates/v32_p12_options/reports/p12_07_results.json")
    with open(out_path, "w") as f:
        json.dump(eval_res, f, indent=2)

    s = eval_res["summary"]
    print(f"\nP12-07 PPO complete in {time.time()-t0:.2f}s!", flush=True)
    print("================== P12-07 PPO SUMMARY ==================")
    print(f"Mean Cash:   ${s['cand_mean']:>10,.2f}")
    print(f"Paired Mean: ${s['paired_delta_mean']:>+10,.2f}")
    print(f"Worst Delta: ${s['paired_delta_min']:>+10,.2f}")
    print(f"Activations: {s['total_activations']:>10}")

if __name__ == "__main__":
    main()
