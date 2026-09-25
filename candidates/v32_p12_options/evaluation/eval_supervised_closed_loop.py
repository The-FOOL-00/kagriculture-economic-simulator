# SPDX-License-Identifier: MIT
"""
Experiment P12-06 & P12-08: Closed-Loop Evaluation of Supervised Option Selector.
Compares:
  - Baseline: A7
  - Candidate A: A7 + Search Gated Options (mode="oracle_search")
  - Candidate B: A7 + Supervised Option Selector (mode="supervised", Seed 42 checkpoint)
Measures terminal cash, paired delta, win rate, and option activations.
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

def run_job(job: Dict[str, Any]) -> Dict[str, Any]:
    cfg = OptionControllerConfig(
        max_options_per_episode=1,
        min_separation_ticks=48,
        option_horizon=4,
        require_full_sync=True,
        mode=job["mode"],
        supervised_model_path=job.get("supervised_model_path")
    )
    res = run_paired_leg(
        seed=job["seed"],
        opponent_id=job["opponent"],
        seat=job["seat"],
        controller_config=cfg
    )
    res["policy_name"] = job["policy_name"]
    return res

def main():
    try:
        sys.stdout.reconfigure(line_buffering=True)
    except Exception:
        pass

    print("Launching Closed-Loop Supervised Selector Evaluation (P12-06)...", flush=True)
    t0 = time.time()

    ckpt_path = os.path.join(REPO_ROOT, "candidates/v32_p12_options/checkpoints/supervised_selector_seed_42.pt")
    
    policies = [
        {"policy_name": "A7_Search_Gated", "mode": "oracle_search", "supervised_model_path": None},
        {"policy_name": "A7_Supervised_Selector", "mode": "supervised", "supervised_model_path": ckpt_path},
    ]

    jobs = []
    for pol in policies:
        for seed in EVAL_SEEDS:
            for opp in OPPONENTS:
                for seat in [0, 1]:  # both seats!
                    jobs.append({
                        "policy_name": pol["policy_name"],
                        "mode": pol["mode"],
                        "supervised_model_path": pol["supervised_model_path"],
                        "seed": seed,
                        "opponent": opp,
                        "seat": seat
                    })

    print(f"Total legs to execute: {len(jobs)} across {len(policies)} policies", flush=True)
    results = []

    with ProcessPoolExecutor(max_workers=10) as pool:
        futures = {pool.submit(run_job, j): j for j in jobs}
        completed = 0
        for fut in as_completed(futures):
            completed += 1
            res = fut.result()
            results.append(res)
            print(f"[{completed:2d}/{len(jobs)}] {res['policy_name']:<22} | Seed {res['seed']} Seat {res['seat']} vs {res['opponent']} | Opts={res['options_activated']} | Delta={res['paired_delta']:+8.1f}", flush=True)

    summary = {}
    for pol in policies:
        pname = pol["policy_name"]
        subset = [r for r in results if r["policy_name"] == pname]
        summary[pname] = aggregate_benchmark_results(subset)

    out_path = os.path.join(REPO_ROOT, "candidates/v32_p12_options/reports/p12_06_closed_loop.json")
    with open(out_path, "w") as f:
        json.dump({"raw": results, "summary": summary}, f, indent=2)

    elapsed = time.time() - t0
    print(f"\nP12-06 closed loop evaluation complete in {elapsed:.2f}s!", flush=True)
    print(f"Saved to {out_path}", flush=True)

    print("\n================== P12-06 CLOSED LOOP SUMMARY ==================")
    print(f"{'Policy':<24} | {'Mean Cash':<12} | {'Median Cash':<12} | {'Paired Delta':<14} | {'Worst Delta':<12} | {'Win Rate':<10}")
    print("-" * 94)
    for pname, s in summary.items():
        print(f"{pname:<24} | ${s['cand_mean']:>10,.2f} | ${s['cand_median']:>10,.2f} | {s['paired_delta_mean']:>+12,.2f} | {s['paired_delta_min']:>+10,.2f} | {s['win_rate']*100:>8.1f}%")

if __name__ == "__main__":
    main()
