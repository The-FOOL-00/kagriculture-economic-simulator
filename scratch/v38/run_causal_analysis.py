# SPDX-License-Identifier: MIT
"""Script for Intervention Forensics and Causal Validation (Phase 13 & 14)."""

from __future__ import annotations
import json
import os
import sys
from typing import Any, Dict, List, Optional
import numpy as np

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from candidates.v38_heuristic_ppo.config import SCRATCH_DIR, MACRO_ACTIONS
from candidates.v38_heuristic_ppo.dataset import DATASET_FILE

def run_causal_forensics(dataset_path: str = DATASET_FILE) -> Dict[str, Any]:
    if not os.path.exists(dataset_path):
        print("Dataset not found!")
        return {}
        
    with open(dataset_path, "r") as f:
        data = json.load(f)
        
    records = data["records"]
    forensics = []
    
    # Classify interventions
    successful = 0
    neutral = 0
    harmful = 0
    
    option_stats = {opt: {"count": 0, "pos_alpha": 0, "mean_delta": 0.0, "deltas": []} for opt in range(11)}
    
    for r in records:
        step = r["step"]
        h_cash = r["heuristic_cash"]
        advantages = r.get("advantages", {})
        
        for opt_str, delta in advantages.items():
            opt = int(opt_str)
            if opt == 0:
                continue
            option_stats[opt]["count"] += 1
            option_stats[opt]["deltas"].append(delta)
            if delta > 0:
                option_stats[opt]["pos_alpha"] += 1
                
        best_opt = r["best_option"]
        best_delta = r["best_delta"]
        
        if best_opt == 0:
            classification = "NEUTRAL"
            neutral += 1
        elif best_delta >= 50.0:
            classification = "SUCCESSFUL"
            successful += 1
        elif best_delta < 0:
            classification = "HARMFUL"
            harmful += 1
        else:
            classification = "NEUTRAL"
            neutral += 1
            
        forensics.append({
            "seed": r["seed"],
            "opponent": r["opponent"],
            "step": step,
            "chosen_option": best_opt,
            "option_name": MACRO_ACTIONS.get(best_opt, "UNKNOWN"),
            "heuristic_cash": h_cash,
            "advantage": best_delta,
            "classification": classification
        })
        
    # Aggregate option statistics
    agg_options = {}
    for opt, stat in option_stats.items():
        if stat["count"] > 0:
            agg_options[f"{opt}_{MACRO_ACTIONS.get(opt, 'UNKNOWN')}"] = {
                "evaluations": stat["count"],
                "positive_alpha_rate": stat["pos_alpha"] / stat["count"] * 100.0,
                "mean_delta": float(np.mean(stat["deltas"])),
                "max_delta": float(np.max(stat["deltas"])),
                "min_delta": float(np.min(stat["deltas"]))
            }
            
    summary = {
        "total_decision_points": len(records),
        "successful_interventions": successful,
        "neutral_interventions": neutral,
        "harmful_interventions": harmful,
        "option_causal_performance": agg_options,
        "forensics_sample": forensics[:20]
    }
    
    out_file = os.path.join(SCRATCH_DIR, "intervention_forensics.json")
    with open(out_file, "w") as f:
        json.dump(summary, f, indent=2)
        
    print(f"Forensics written to {out_file}.")
    return summary

if __name__ == "__main__":
    run_causal_forensics()
