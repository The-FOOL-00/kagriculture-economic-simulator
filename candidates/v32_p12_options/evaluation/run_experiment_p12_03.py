# SPDX-License-Identifier: MIT
"""
V32 P12 Experiment P12-03: OPTION-SPACING & FREQUENCY ABLATION
Compares:
  - F0: pure A7 (0 options)
  - F1: max 1 option
  - F2: max 2 options
  - F3: max 3 options
along with spacing intervals {24, 48, 72} ticks.
Measures terminal cash, paired delta vs A7, and desynchronization rate.
"""

import copy
import json
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import Any, Dict, List
import numpy as np

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from candidates.v32_p12_options.selector import OptionControllerConfig
from candidates.v32_p12_options.evaluator import run_paired_leg, aggregate_benchmark_results

EVAL_SEEDS = [249635, 249636, 249637, 249675, 249676]
OPPONENTS = ["E2_A7", "E8_DMITRII"]
SEATS = [0, 1]

def run_single_job(job: Dict[str, Any]) -> Dict[str, Any]:
    cfg = OptionControllerConfig(
        max_options_per_episode=job["max_options"],
        min_separation_ticks=job["min_spacing"],
        option_horizon=4,
        require_full_sync=True,
        mode="oracle_search"
    )
    res = run_paired_leg(
        seed=job["seed"],
        opponent_id=job["opponent"],
        seat=job["seat"],
        controller_config=cfg
    )
    res["config_name"] = job["config_name"]
    res["max_options"] = job["max_options"]
    res["min_spacing"] = job["min_spacing"]
    return res

def main():
    print("Launching Experiment P12-03 (Option Frequency & Spacing Ablation)...")
    t0 = time.time()
    
    # 1. Frequency configs
    freq_configs = [
        {"config_name": "F0_A7", "max_options": 0, "min_spacing": 48},
        {"config_name": "F1_Max1", "max_options": 1, "min_spacing": 48},
        {"config_name": "F2_Max2", "max_options": 2, "min_spacing": 48},
        {"config_name": "F3_Max3", "max_options": 3, "min_spacing": 24},
    ]
    
    # 2. Spacing configs (with max_options=2)
    spacing_configs = [
        {"config_name": "Spacing_24", "max_options": 2, "min_spacing": 24},
        {"config_name": "Spacing_48", "max_options": 2, "min_spacing": 48},
        {"config_name": "Spacing_72", "max_options": 2, "min_spacing": 72},
    ]
    
    # Deduplicate jobs:
    # F2_Max2 with min_spacing=48 is identical to Spacing_48
    all_configs = [
        {"config_name": "F0_A7", "max_options": 0, "min_spacing": 48},
        {"config_name": "F1_Max1", "max_options": 1, "min_spacing": 48},
        {"config_name": "F2_Spacing_48", "max_options": 2, "min_spacing": 48},
        {"config_name": "F2_Spacing_24", "max_options": 2, "min_spacing": 24},
        {"config_name": "F2_Spacing_72", "max_options": 2, "min_spacing": 72},
        {"config_name": "F3_Max3", "max_options": 3, "min_spacing": 24},
    ]
    
    jobs = []
    for cfg in all_configs:
        for seed in EVAL_SEEDS:
            for opp in OPPONENTS:
                for seat in [0]:  # focus on seat 0 for frequency/spacing ablation
                    jobs.append({
                        "config_name": cfg["config_name"],
                        "max_options": cfg["max_options"],
                        "min_spacing": cfg["min_spacing"],
                        "seed": seed,
                        "opponent": opp,
                        "seat": seat
                    })

    print(f"Total jobs to execute: {len(jobs)}", flush=True)
    results = []
    
    with ProcessPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(run_single_job, job): job for job in jobs}
        completed = 0
        for fut in as_completed(futures):
            completed += 1
            res = fut.result()
            results.append(res)
            print(f"[{completed:2d}/{len(jobs)}] {res['config_name']:<14} | Seed {res['seed']} vs {res['opponent']} | Opts={res['options_activated']} | Delta={res['paired_delta']:+8.1f}", flush=True)

    # Aggregate by config
    summary_by_config = {}
    for cfg in all_configs:
        cname = cfg["config_name"]
        subset = [r for r in results if r["config_name"] == cname]
        summary_by_config[cname] = aggregate_benchmark_results(subset)
        
    out_dir = os.path.join(REPO_ROOT, "candidates/v32_p12_options/reports")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "p12_03_results.json")
    with open(out_path, "w") as f:
        json.dump({"raw_results": results, "summary": summary_by_config}, f, indent=2)
        
    print(f"\nP12-03 complete in {time.time()-t0:.2f}s!")
    print(f"Saved results to {out_path}")

    # Print summary table
    print("\n================== P12-03 SUMMARY ==================")
    print(f"{'Config':<16} | {'Mean Cash':<12} | {'Mean Delta':<12} | {'Min Delta':<12} | {'Activations':<12}")
    print("-" * 72)
    for cname, s in summary_by_config.items():
        print(f"{cname:<16} | ${s['cand_mean']:>10,.2f} | {s['paired_delta_mean']:>+10,.2f} | {s['paired_delta_min']:>+10,.2f} | {s['total_activations']:>10}")

if __name__ == "__main__":
    main()
