"""
scratch/run_v2_guarded_counterfactuals.py
=============================================================================
Phase 8, 9, 10, 11: Counterfactuals, Non-Interference, and EV Measurement
=============================================================================
Evaluates:
1. Normal Game Non-Interference: 100 matches comparing Guarded V2 vs Frozen V2.
2. Perturbation Recovery Counterfactuals across matched seeds:
   - Scenario 1: Dropped Day-0 Melon Water Action (Step 22)
   - Scenario 2: Dropped Step-122 Quadrant Unlock Action
   - Scenario 3: Dropped Day-1 Wheat Feed Purchase (Step 24)
   
Measures:
- Score(A) = Normal Baseline
- Score(B) = Perturbed V2 (Unprotected)
- Score(C) = Perturbed Guarded V2 (Protected)
- Prevented Loss = Score(C) - Score(B)
- Net Degradation = Score(A) - Score(C)
=============================================================================
"""

import sys
import os
sys.path.insert(0, os.path.abspath("."))

import json
import time
import numpy as np
from concurrent.futures import ProcessPoolExecutor, as_completed
import kaggle_environments

import candidates.slot2_aethel_refined_v2 as v2
import scratch.v2_guarded_candidate as guarded_v2

def run_normal_match(seed, opp_name="starter"):
    # Run Frozen V2
    env = kaggle_environments.make("kaggriculture", configuration={"seed": seed, "episodeSteps": 720}, debug=False)
    env.reset()
    
    agent_guarded = guarded_v2.GuardedV2Agent()
    
    actions_equal = 0
    total_steps = 719
    interventions = 0
    
    for step in range(total_steps):
        obs0 = env.state[0].observation
        obs1 = env.state[1].observation
        
        act_v2 = v2.agent(obs0)
        act_guarded = agent_guarded(obs0)
        
        if act_v2 == act_guarded:
            actions_equal += 1
        else:
            interventions += 1
            
        env.step([act_v2, "random"])
        
    final_step = env.steps[-1]
    v2_score = float(final_step[0].reward or 0.0)
    
    return {
        "seed": seed,
        "v2_score": v2_score,
        "actions_equal": actions_equal,
        "total_steps": total_steps,
        "interventions": interventions,
        "parity_pct": (actions_equal / total_steps) * 100.0
    }

def run_counterfactual_triad(seed, perturbation_type):
    """
    Runs A (Normal V2), B (Perturbed V2), C (Perturbed Guarded V2)
    on the exact same seed.
    """
    scores = {}
    
    # --- Condition A: Normal V2 ---
    env_a = kaggle_environments.make("kaggriculture", configuration={"seed": seed, "episodeSteps": 720}, debug=False)
    env_a.reset()
    for step in range(719):
        obs0 = env_a.state[0].observation
        act0 = v2.agent(obs0)
        env_a.step([act0, "random"])
    scores["A"] = float(env_a.steps[-1][0].reward or 0.0)
    
    # --- Condition B: Perturbed V2 ---
    env_b = kaggle_environments.make("kaggriculture", configuration={"seed": seed, "episodeSteps": 720}, debug=False)
    env_b.reset()
    for step in range(719):
        obs0 = env_b.state[0].observation
        act0 = v2.agent(obs0)
        
        # Inject perturbation
        if perturbation_type == "drop_melon_water" and step == 22:
            act0["hands"] = [["PASS"] for _ in act0.get("hands", [])]
        elif perturbation_type == "drop_quadrant_unlock" and step == 122:
            act0["farmer"] = ["PASS"]
        elif perturbation_type == "drop_wheat_buy" and step == 24:
            act0["market"] = [o for o in act0.get("market", []) if not (isinstance(o, list) and len(o) >= 2 and o[1] == "WHEAT")]
            
        env_b.step([act0, "random"])
    scores["B"] = float(env_b.steps[-1][0].reward or 0.0)
    
    # --- Condition C: Perturbed Guarded V2 ---
    env_c = kaggle_environments.make("kaggriculture", configuration={"seed": seed, "episodeSteps": 720}, debug=False)
    env_c.reset()
    agent_c = guarded_v2.GuardedV2Agent()
    interventions_c = 0
    for step in range(719):
        obs0 = env_c.state[0].observation
        act0 = agent_c(obs0)
        
        # Inject perturbation before step
        if perturbation_type == "drop_melon_water" and step == 22:
            # Overwrite the base action at step 22, guard should catch at hour 23 (step 23)
            act0["hands"] = [["PASS"] for _ in act0.get("hands", [])]
        elif perturbation_type == "drop_quadrant_unlock" and step == 122:
            act0["farmer"] = ["PASS"]
        elif perturbation_type == "drop_wheat_buy" and step == 24:
            act0["market"] = [o for o in act0.get("market", []) if not (isinstance(o, list) and len(o) >= 2 and o[1] == "WHEAT")]
            
        env_c.step([act0, "random"])
    scores["C"] = float(env_c.steps[-1][0].reward or 0.0)
    
    return {
        "seed": seed,
        "perturbation": perturbation_type,
        "score_A_normal": scores["A"],
        "score_B_perturbed": scores["B"],
        "score_C_guarded": scores["C"],
        "loss_B_vs_A": scores["A"] - scores["B"],
        "recovery_C_vs_B": scores["C"] - scores["B"],
        "net_gap_A_vs_C": scores["A"] - scores["C"],
        "interventions": agent_c.total_interventions
    }

def run_all_counterfactuals(num_seeds=30, max_workers=6):
    print("=" * 80)
    print(f"RUNNING COUNTERFACTUAL & NON-INTERFERENCE EVALUATION ({num_seeds} seeds/test)")
    print("=" * 80)
    
    # 1. Non-interference test
    print("\n--- 1. Testing Normal Game Action Parity & Non-Interference ---")
    parity_tasks = [2000 + i for i in range(num_seeds)]
    parity_results = []
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(run_normal_match, s) for s in parity_tasks]
        for f in as_completed(futures):
            parity_results.append(f.result())
            
    total_steps_eval = sum(r["total_steps"] for r in parity_results)
    total_equal_eval = sum(r["actions_equal"] for r in parity_results)
    total_interv = sum(r["interventions"] for r in parity_results)
    overall_parity = (total_equal_eval / total_steps_eval) * 100.0
    
    print(f"Total Steps Evaluated: {total_steps_eval:,}")
    print(f"Total Action Matches:  {total_equal_eval:,} ({overall_parity:.4f}%)")
    print(f"False Interventions:  {total_interv}")
    
    # 2. Perturbation Scenarios
    perturbations = ["drop_melon_water", "drop_quadrant_unlock", "drop_wheat_buy"]
    cf_results = {}
    
    for p_type in perturbations:
        print(f"\n--- 2. Evaluating Perturbation: {p_type} ---")
        tasks = [(3000 + i, p_type) for i in range(num_seeds)]
        results_p = []
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(run_counterfactual_triad, s, p) for s, p in tasks]
            for f in as_completed(futures):
                results_p.append(f.result())
                
        avg_A = np.mean([r["score_A_normal"] for r in results_p])
        avg_B = np.mean([r["score_B_perturbed"] for r in results_p])
        avg_C = np.mean([r["score_C_guarded"] for r in results_p])
        avg_loss = np.mean([r["loss_B_vs_A"] for r in results_p])
        avg_recovery = np.mean([r["recovery_C_vs_B"] for r in results_p])
        recovery_pct = (avg_recovery / avg_loss * 100.0) if avg_loss > 0 else 0.0
        
        print(f"Normal V2 Score (A):          ${avg_A:,.2f}")
        print(f"Perturbed V2 Score (B):       ${avg_B:,.2f} (Loss: -${avg_loss:,.2f})")
        print(f"Guarded V2 Score (C):         ${avg_C:,.2f} (Recovered: +${avg_recovery:,.2f}, {recovery_pct:.1f}%)")
        
        cf_results[p_type] = {
            "avg_score_A": float(avg_A),
            "avg_score_B": float(avg_B),
            "avg_score_C": float(avg_C),
            "avg_loss": float(avg_loss),
            "avg_recovery": float(avg_recovery),
            "recovery_pct": float(recovery_pct),
            "details": results_p
        }
        
    summary = {
        "non_interference": {
            "total_steps": total_steps_eval,
            "actions_equal": total_equal_eval,
            "interventions": total_interv,
            "parity_pct": overall_parity
        },
        "perturbations": cf_results
    }
    
    out_file = "scratch/counterfactual_safety_results.json"
    with open(out_file, "w") as fp:
        json.dump(summary, fp, indent=2)
    print(f"\nSaved counterfactual results to {out_file}")
    
    return summary

if __name__ == "__main__":
    run_all_counterfactuals(num_seeds=30, max_workers=6)
