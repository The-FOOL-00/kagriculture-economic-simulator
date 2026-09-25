# SPDX-License-Identifier: MIT
"""Script for Adversarial & Stress Testing (Phase 17)."""

from __future__ import annotations
import json
import os
import sys
import time
from typing import Any, Dict, List, Optional
import numpy as np

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from candidates.v38_heuristic_ppo.config import SCRATCH_DIR, SAFE_DEV_SEEDS
from candidates.v38_heuristic_ppo.evaluate import evaluate_single_match

def run_adversarial_suite() -> Dict[str, Any]:
    print("Running Adversarial Stress Suite...")
    
    # 1. Hostile Dumper Stressor (SYN_AGG)
    # 2. Frontier LB Competitor (E8_DMITRII)
    # 3. Mirror Competitor (E2_A7)
    stress_opps = ["SYN_AGG", "E8_DMITRII", "E2_A7"]
    stress_seeds = SAFE_DEV_SEEDS[:4]
    
    policies = ["V35", "V38_HEURISTIC", "V38_PPO"]
    results = []
    
    for pol in policies:
        for opp in stress_opps:
            for s in stress_seeds:
                for seat in (0, 1):
                    res = evaluate_single_match(
                        policy_name=pol,
                        opponent_id=opp,
                        seed=s,
                        seat=seat,
                        bc_path=os.path.join(SCRATCH_DIR, "bc_policy.pt"),
                        ppo_path=os.path.join(SCRATCH_DIR, "ppo_policy.pt")
                    )
                    results.append(res)
                    
    # Compile stress metrics
    summary = {}
    for pol in policies:
        p_recs = [r for r in results if r["policy"] == pol]
        pts = sum(r["win"] for r in p_recs)
        n = len(p_recs)
        cash_list = [r["cand_cash"] for r in p_recs]
        
        # Breakdown by stress opp
        opp_breakdown = {}
        for opp in stress_opps:
            o_recs = [r for r in p_recs if r["opponent"] == opp]
            opp_breakdown[opp] = {
                "matches": len(o_recs),
                "win_rate": sum(r["win"] for r in o_recs) / max(1, len(o_recs)) * 100.0,
                "mean_cash": float(np.mean([r["cand_cash"] for r in o_recs])),
                "min_cash": float(np.min([r["cand_cash"] for r in o_recs]))
            }
            
        summary[pol] = {
            "total_matches": n,
            "overall_win_rate": pts / max(1, n) * 100.0,
            "mean_cash": float(np.mean(cash_list)),
            "min_cash": float(np.min(cash_list)),
            "opp_breakdown": opp_breakdown
        }
        
    out_file = os.path.join(SCRATCH_DIR, "adversarial_results.json")
    with open(out_file, "w") as f:
        json.dump(summary, f, indent=2)
        
    print(f"Adversarial Suite complete! Saved to {out_file}")
    return summary

if __name__ == "__main__":
    run_adversarial_suite()
