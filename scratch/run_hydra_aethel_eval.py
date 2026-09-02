# SPDX-License-Identifier: MIT
"""
Run multi-seed evaluation between Hydra V1 and Cleo (Aethel), logging exact trajectories and outcomes.
"""

import os
import sys
import json
import copy
import importlib.util
from kaggle_environments import make

def load_agent(filepath):
    spec = importlib.util.spec_from_file_location("agent_mod", filepath)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def eval_head_to_head(seeds=[1, 2, 5, 7, 10, 13, 17, 21, 25, 30]):
    hydra_path = os.path.abspath("agents/hydra_prime.py")
    cleo_path = os.path.abspath("replays/raw/reference_agents/closer_cleo.py")
    
    hydra = load_agent(hydra_path)
    cleo = load_agent(cleo_path)
    
    results = []
    
    for seed in seeds:
        # Match 1: Hydra P0, Cleo P1
        env1 = make("kaggriculture", configuration={"seed": seed})
        env1.run([hydra_path, cleo_path])
        r0_m1 = float(env1.steps[-1][0]["reward"] or 0)
        r1_m1 = float(env1.steps[-1][1]["reward"] or 0)
        status0_m1 = env1.steps[-1][0].get("status", "DONE")
        status1_m1 = env1.steps[-1][1].get("status", "DONE")
        
        # Match 2: Cleo P0, Hydra P1
        env2 = make("kaggriculture", configuration={"seed": seed})
        env2.run([cleo_path, hydra_path])
        r0_m2 = float(env2.steps[-1][0]["reward"] or 0)
        r1_m2 = float(env2.steps[-1][1]["reward"] or 0)
        status0_m2 = env2.steps[-1][0].get("status", "DONE")
        status1_m2 = env2.steps[-1][1].get("status", "DONE")
        
        res_p0 = {
            "seed": seed, "seat": "P0", "hydra_reward": r0_m1, "cleo_reward": r1_m1,
            "margin": r0_m1 - r1_m1, "hydra_status": status0_m1, "cleo_status": status1_m1,
            "is_win": r0_m1 > r1_m1, "is_loss": r0_m1 < r1_m1
        }
        res_p1 = {
            "seed": seed, "seat": "P1", "hydra_reward": r1_m2, "cleo_reward": r0_m2,
            "margin": r1_m2 - r0_m2, "hydra_status": status1_m2, "cleo_status": status0_m2,
            "is_win": r1_m2 > r0_m2, "is_loss": r1_m2 < r0_m2
        }
        results.extend([res_p0, res_p1])
        print(f"Seed {seed:3d} | P0 Hydra: {r0_m1:8.1f} vs Cleo: {r1_m1:8.1f} (Margin: {r0_m1-r1_m1:+8.1f}, Cleo: {status1_m1}) | P1 Hydra: {r1_m2:8.1f} vs Cleo: {r0_m2:8.1f} (Margin: {r1_m2-r0_m2:+8.1f}, Hydra: {status1_m2})")

    total = len(results)
    wins = sum(1 for r in results if r["is_win"])
    losses = sum(1 for r in results if r["is_loss"])
    mean_margin = sum(r["margin"] for r in results) / total
    print(f"\nOVERALL HYDRA VS AETHEL: {wins}W - {losses}L ({wins/total*100:.1f}%) | Mean Margin: {mean_margin:+.1f}")
    
    with open("scratch/hydra_vs_aethel_detailed.json", "w") as f:
        json.dump(results, f, indent=2)

if __name__ == "__main__":
    eval_head_to_head()
