"""
Phase 3: Activation Audit for Causal Architecture Decomposition.
Runs 100 matched seeds for each treatment T1..T8.
Measures:
- activation rate
- first activation step
- median activation step
- number of trajectories affected / divergence from V2
"""

import sys
import os
import json
import time
import numpy as np
from concurrent.futures import ProcessPoolExecutor, as_completed
import kaggle_environments

project_root = r"c:\Users\Sundareswaran\Kagriculture"
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import candidates.slot2_aethel_refined_v2 as v2
import scratch.arch_base as arch

SEEDS = [1000 + i * 17 for i in range(100)]

TREATMENTS = {
    "T1_DAY0_SPATIAL": {"T1": True, "T2": False, "T3": False, "T4": False, "T5": False, "T6": False, "T7": False, "T8": True},
    "T2_FAST_Q2": {"T1": False, "T2": True, "T3": False, "T4": False, "T5": False, "T6": False, "T7": False, "T8": True},
    "T3_MILK_HOLD_FAST_Q3": {"T1": False, "T2": False, "T3": True, "T4": False, "T5": False, "T6": False, "T7": False, "T8": True},
    "T4_PASTURE_16": {"T1": False, "T2": False, "T3": False, "T4": True, "T5": False, "T6": False, "T7": False, "T8": True},
    "T5_HERD_13C_3S": {"T1": False, "T2": False, "T3": False, "T4": False, "T5": True, "T6": False, "T7": False, "T8": True},
    "T6_CASH_CROPS": {"T1": False, "T2": False, "T3": False, "T4": False, "T5": False, "T6": True, "T7": False, "T8": True},
    "T7_FEED_BUFFER": {"T1": False, "T2": False, "T3": False, "T4": False, "T5": False, "T6": False, "T7": True, "T8": True},
    "T8_NO_MARKET_CTRL": {"T1": False, "T2": False, "T3": False, "T4": False, "T5": False, "T6": False, "T7": False, "T8": False},
}


def run_single_audit(args):
    t_name, flags, seed = args
    env = kaggle_environments.make("kaggriculture", configuration={"seed": seed, "episodeSteps": 720})
    
    agent_inst = arch.ArchBaseAgent(flags)
    agent_fn = lambda obs, cfg=None: agent_inst(obs, cfg)
    
    # Run against V2 opponent
    env.run([agent_fn, v2.agent])
    
    # Find which treatments activated
    # Also check if actions differed from pure V2 trace
    activated_steps = []
    for k, v in agent_inst.activation_events.items():
        if flags.get(k, False) or (k == "T8" and not flags.get("T8", True)):
            activated_steps.extend(v)
            
    is_active = len(activated_steps) > 0
    first_step = min(activated_steps) if is_active else None
    median_step = int(np.median(activated_steps)) if is_active else None
    
    score_treat = float(env.steps[-1][0]["reward"])
    score_opp = float(env.steps[-1][1]["reward"])
    
    return {
        "treatment": t_name,
        "seed": seed,
        "is_active": is_active,
        "first_step": first_step,
        "median_step": median_step,
        "num_activation_events": len(activated_steps),
        "score_treat": score_treat,
        "score_opp": score_opp,
        "margin": score_treat - score_opp
    }


def main():
    print("=" * 80)
    print("PHASE 3: ACTIVATION AUDIT (100 SEEDS PER TREATMENT)")
    print("=" * 80)
    
    tasks = []
    for t_name, flags in TREATMENTS.items():
        for s in SEEDS:
            tasks.append((t_name, flags, s))
            
    print(f"Submitting {len(tasks)} simulation tasks across CPU cores...", flush=True)
    t0 = time.time()
    
    results = []
    with ProcessPoolExecutor(max_workers=min(8, os.cpu_count() or 4)) as pool:
        futures = [pool.submit(run_single_audit, task) for task in tasks]
        completed = 0
        for f in as_completed(futures):
            res = f.result()
            results.append(res)
            completed += 1
            if completed % 100 == 0 or completed == len(tasks):
                print(f"Completed {completed}/{len(tasks)} ({completed/len(tasks)*100:.1f}%) in {time.time()-t0:.1f}s", flush=True)
                
    # Aggregate by treatment
    summary = {}
    for t_name in TREATMENTS.keys():
        t_res = [r for r in results if r["treatment"] == t_name]
        active_cnt = sum(1 for r in t_res if r["is_active"])
        act_rate = active_cnt / len(t_res) * 100.0
        first_steps = [r["first_step"] for r in t_res if r["first_step"] is not None]
        median_steps = [r["median_step"] for r in t_res if r["median_step"] is not None]
        
        summary[t_name] = {
            "total_runs": len(t_res),
            "active_runs": active_cnt,
            "activation_rate_pct": act_rate,
            "mean_first_step": float(np.mean(first_steps)) if first_steps else None,
            "median_first_step": int(np.median(first_steps)) if first_steps else None,
            "overall_median_step": int(np.median(median_steps)) if median_steps else None,
            "mean_margin": float(np.mean([r["margin"] for r in t_res])),
            "mean_score": float(np.mean([r["score_treat"] for r in t_res]))
        }
        
    print("\n" + "=" * 80)
    print("ACTIVATION AUDIT RESULTS SUMMARY")
    print("=" * 80)
    print(f"{'Treatment':<25} | {'Act Rate':<10} | {'1st Step (Med)':<15} | {'Median Step':<12} | {'Trajectories':<12}")
    print("-" * 80)
    for t_name, s in summary.items():
        first_str = f"{s['median_first_step']}" if s['median_first_step'] is not None else "N/A"
        med_str = f"{s['overall_median_step']}" if s['overall_median_step'] is not None else "N/A"
        print(f"{t_name:<25} | {s['activation_rate_pct']:>8.1f}% | {first_str:>15} | {med_str:>12} | {s['active_runs']:>4}/{s['total_runs']}")
        
    with open("scratch/activation_audit_results.json", "w", encoding="utf-8") as f:
        json.dump({"summary": summary, "raw": results}, f, indent=2)
        
    print("\nSaved audit results to scratch/activation_audit_results.json")


if __name__ == "__main__":
    main()
