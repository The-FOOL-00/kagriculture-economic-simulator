# SPDX-License-Identifier: MIT
"""
Additional Single-Factor Experiment Verification:
1. Livestock scaling (Rita 10c/6s vs Aethel 8c/6s vs Mateo 0c/0s/Melon vs Apex V4)
2. Land expansion (Rita 4-quad vs Aethel 3-quad vs Mateo 2-quad)
3. Opponent-selection and survivorship bias analysis
"""

import os
import sys
import json
from concurrent.futures import ProcessPoolExecutor
from kaggle_environments import make

SEEDS = [1, 2, 5, 7, 10, 13, 17, 21, 25, 30]

AGENTS = {
    "Aethel_Clean": os.path.abspath("scratch/ablation_forensics/aethel_clean.py"),
    "Rancher_Rita_HighLivestock": os.path.abspath("replays/raw/reference_agents/rancher_rita.py"),
    "Melon_Mateo_PureCrops": os.path.abspath("replays/raw/reference_agents/melon_mateo.py"),
    "Titan_Apex_V4_Dynamic": os.path.abspath("agents/apex_grandmaster_v4.py"),
    "Slotter_Silas_T8": os.path.abspath("replays/raw/reference_agents/slotter_silas.py"),
}

def _run_match(args):
    p0_path, p1_path, seed = args
    env = make("kaggriculture", configuration={"seed": seed})
    env.run([p0_path, p1_path])
    r0 = float(env.steps[-1][0]["reward"] or 0)
    r1 = float(env.steps[-1][1]["reward"] or 0)
    return {"seed": seed, "r0": r0, "r1": r1, "margin": r0 - r1}

def run_matrix():
    workers = min(12, os.cpu_count() or 4)
    with ProcessPoolExecutor(max_workers=workers) as pool:
        results = {}
        for name_a, path_a in AGENTS.items():
            results[name_a] = {}
            for name_b, path_b in AGENTS.items():
                if name_a == name_b:
                    continue
                work = [(path_a, path_b, seed) for seed in SEEDS]
                outcomes = list(pool.map(_run_match, work))
                wins = sum(1 for o in outcomes if o["margin"] > 0)
                losses = sum(1 for o in outcomes if o["margin"] < 0)
                ties = sum(1 for o in outcomes if o["margin"] == 0)
                mean_margin = sum(o["margin"] for o in outcomes) / len(outcomes)
                results[name_a][name_b] = {
                    "wins": wins, "losses": losses, "ties": ties,
                    "win_rate": wins / len(outcomes) * 100,
                    "mean_margin": mean_margin
                }
                print(f"{name_a:28s} vs {name_b:28s}: {wins:2d}W - {losses:2d}L ({wins/len(outcomes)*100:5.1f}%) | Mean Margin: {mean_margin:+9.1f}")
        
        with open("scratch/livestock_and_matrix_results.json", "w") as f:
            json.dump(results, f, indent=2)

if __name__ == "__main__":
    run_matrix()
