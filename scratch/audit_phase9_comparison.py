"""
Phase 9: Deterministic Baseline Comparison
Compares on fixed development seeds:
A = Frozen V2
B = Replay-Derived H (Upper Bound)
C = New Closed-Loop JIT Opening + V2
"""

import sys
import os
sys.path.insert(0, os.path.abspath("."))
import json
import numpy as np
from kaggle_environments import make
import candidates.slot2_aethel_refined_v2 as v2
from scratch.v2_jit_melon_experiment import agent_H_full_jit_pipeline
import scratch.v2_jit_opening_closed_loop as cand_c

def robust(fn):
    def wrapped(obs, cfg=None):
        if obs.get("step") is None:
            obs["step"] = int(obs.get("day", 0) * 24 + obs.get("hour", 0))
        return fn(obs, cfg)
    return wrapped

SEEDS = [42, 100, 101, 2026, 777, 999]

def run_phase9():
    print("--- PHASE 9: DETERMINISTIC BASELINE COMPARISON (A vs B vs C) ---")
    results = []
    
    for s in SEEDS:
        cfg = {"seed": s, "episodeSteps": 720}
        
        # 1. Candidate A: Frozen V2 vs V2
        env_a = make("kaggriculture", configuration=cfg)
        env_a.run([robust(v2.agent), robust(v2.agent)])
        r_a = float(env_a.steps[-1][0]["reward"] or 0)
        
        # 2. Candidate B: Replay-Derived H vs V2
        env_b = make("kaggriculture", configuration=cfg)
        env_b.run([robust(agent_H_full_jit_pipeline), robust(v2.agent)])
        r_b = float(env_b.steps[-1][0]["reward"] or 0)
        
        # 3. Candidate C: New Closed-Loop JIT + V2 vs V2
        env_c = make("kaggriculture", configuration=cfg)
        env_c.run([robust(cand_c.agent), robust(v2.agent)])
        r_c = float(env_c.steps[-1][0]["reward"] or 0)
        
        r_v2_opp_c = float(env_c.steps[-1][1]["reward"] or 0)
        margin_c = r_c - r_v2_opp_c
        margin_b = r_b - float(env_b.steps[-1][1]["reward"] or 0)
        
        row = {
            "seed": s,
            "reward_A_v2": r_a,
            "reward_B_h": r_b,
            "reward_C_closed_loop": r_c,
            "margin_B_vs_v2": margin_b,
            "margin_C_vs_v2": margin_c
        }
        results.append(row)
        print(f"Seed {s:5d}: A (V2)={r_a:8.1f} | B (H Replay)={r_b:8.1f} (margin {margin_b:+8.1f}) | C (Closed-Loop)={r_c:8.1f} (margin {margin_c:+8.1f})")
        
    means = {
        "mean_A": float(np.mean([r["reward_A_v2"] for r in results])),
        "mean_B": float(np.mean([r["reward_B_h"] for r in results])),
        "mean_C": float(np.mean([r["reward_C_closed_loop"] for r in results])),
        "mean_margin_B": float(np.mean([r["margin_B_vs_v2"] for r in results])),
        "mean_margin_C": float(np.mean([r["margin_C_vs_v2"] for r in results]))
    }
    
    print("\nSummary Means across representative seeds:")
    print(json.dumps(means, indent=2))
    
    with open("scratch/jit_melon_results/phase9_deterministic_comparison.json", "w") as f:
        json.dump({"records": results, "summary": means}, f, indent=2)

if __name__ == "__main__":
    run_phase9()
