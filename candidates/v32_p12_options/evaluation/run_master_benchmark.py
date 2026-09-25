# SPDX-License-Identifier: MIT
"""
V32 P12 Master Benchmark & Fresh Seed Generalization (P12-05 & P12-10).
Evaluates policies across fresh DEV seeds (249677-249681), all 6 league opponents,
and both player seats (0 and 1).
Policies evaluated:
  - Baseline: A7 Incumbent
  - Candidate A: A7 + Search-Gated Options
  - Candidate B: A7 + Supervised Selector (Production Candidate)
  - Candidate C: A7 + PPO Selector
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

from candidates.v32_p12_options.evaluator import run_paired_leg, aggregate_benchmark_results
from candidates.v32_p12_options.selector import OptionControllerConfig
from candidates.v32_rlx2.opponents import LEAGUE_OPPONENTS
from scripts.v32_common import check_seed_allowed

FRESH_DEV_SEEDS = [249677, 249678, 249679, 249680, 249681]

def run_benchmark_leg(job: Dict[str, Any]) -> Dict[str, Any]:
    cfg = OptionControllerConfig(
        max_options_per_episode=1,
        min_separation_ticks=48,
        option_horizon=4,
        require_full_sync=True,
        mode=job["mode"],
        supervised_model_path=job.get("supervised_model_path"),
        ppo_model_path=job.get("ppo_model_path")
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

    # Verify seed governance
    for s in FRESH_DEV_SEEDS:
        check_seed_allowed(s)

    print(f"Verified seed governance for {len(FRESH_DEV_SEEDS)} fresh DEV seeds: {FRESH_DEV_SEEDS}", flush=True)

    t0 = time.time()
    sup_ckpt = os.path.join(REPO_ROOT, "candidates/v32_p12_options/checkpoints/supervised_selector_seed_42.pt")
    ppo_ckpt = os.path.join(REPO_ROOT, "candidates/v32_p12_options/checkpoints/ppo_option_selector.pt")

    policies = [
        {"policy_name": "P12_Search_Gated", "mode": "oracle_search", "supervised_model_path": None, "ppo_model_path": None},
        {"policy_name": "P12_Supervised_Selector", "mode": "supervised", "supervised_model_path": sup_ckpt, "ppo_model_path": None},
        {"policy_name": "P12_PPO_Selector", "mode": "ppo", "supervised_model_path": None, "ppo_model_path": ppo_ckpt},
    ]

    jobs = []
    for pol in policies:
        for seed in FRESH_DEV_SEEDS:
            for opp in LEAGUE_OPPONENTS:
                for seat in [0, 1]:
                    jobs.append({
                        "policy_name": pol["policy_name"],
                        "mode": pol["mode"],
                        "supervised_model_path": pol["supervised_model_path"],
                        "ppo_model_path": pol["ppo_model_path"],
                        "seed": seed,
                        "opponent": opp,
                        "seat": seat
                    })

    print(f"Launching Master Benchmark across {len(jobs)} match legs with 10 workers...", flush=True)

    results = []
    with ProcessPoolExecutor(max_workers=10) as pool:
        futures = {pool.submit(run_benchmark_leg, j): j for j in jobs}
        completed = 0
        for fut in as_completed(futures):
            completed += 1
            res = fut.result()
            results.append(res)
            print(f"[{completed:3d}/{len(jobs)}] {res['policy_name']:<24} | S={res['seed']} St={res['seat']} vs {res['opponent']:<10} | Opts={res['options_activated']} | Delta={res['paired_delta']:+8.1f}", flush=True)

    # Aggregate summaries by policy and by opponent
    policy_summaries = {}
    opp_breakdown = {}

    for pol in policies:
        pname = pol["policy_name"]
        subset = [r for r in results if r["policy_name"] == pname]
        policy_summaries[pname] = aggregate_benchmark_results(subset)
        
        opp_breakdown[pname] = {}
        for opp in LEAGUE_OPPONENTS:
            opp_sub = [r for r in subset if r["opponent"] == opp]
            opp_breakdown[pname][opp] = aggregate_benchmark_results(opp_sub)

    out_dir = os.path.join(REPO_ROOT, "candidates/v32_p12_options/reports")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "p12_master_benchmark_results.json")
    with open(out_path, "w") as f:
        json.dump({
            "raw": results,
            "policy_summaries": policy_summaries,
            "opp_breakdown": opp_breakdown
        }, f, indent=2)

    elapsed = time.time() - t0
    print(f"\nMaster Benchmark complete in {elapsed:.2f}s!", flush=True)
    print(f"Saved results to {out_path}", flush=True)

    # Master Benchmark Table (Section 63 format)
    print("\n" + "=" * 120)
    print("MASTER BENCHMARK (Section 63 Table)")
    print("=" * 120)
    print(f"{'Policy':<24} | {'Mean ($)':<10} | {'Median ($)':<10} | {'P25 ($)':<10} | {'P75 ($)':<10} | {'Min ($)':<10} | {'W':<3} | {'L':<3} | {'T':<3} | {'Paired Δ':<10} | {'Activations':<11}")
    print("-" * 120)
    
    # Baseline A7 entry
    a7_sub = [r for r in results if r["policy_name"] == "P12_Search_Gated"]
    a7_scores = [r["a7_cash"] for r in a7_sub]
    print(f"{'A7 Incumbent':<24} | ${np.mean(a7_scores):>8,.1f} | ${np.median(a7_scores):>8,.1f} | ${np.percentile(a7_scores, 25):>8,.1f} | ${np.percentile(a7_scores, 75):>8,.1f} | ${np.min(a7_scores):>8,.1f} | {'—':<3} | {'—':<3} | {'—':<3} | {'+$0.0':>10} | {'0 / 60':>11}")

    for pname, s in policy_summaries.items():
        print(f"{pname:<24} | ${s['cand_mean']:>8,.1f} | ${s['cand_median']:>8,.1f} | ${s['cand_p25']:>8,.1f} | ${s['cand_p75']:>8,.1f} | ${s['cand_min']:>8,.1f} | {s['wins']:<3} | {s['losses']:<3} | {s['ties']:<3} | {s['paired_delta_mean']:>+10,.1f} | {s['total_activations']:>5} / {s['legs']}")
    print("=" * 120)

if __name__ == "__main__":
    main()
