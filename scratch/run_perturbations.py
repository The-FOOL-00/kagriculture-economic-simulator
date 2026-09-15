"""
Macroeconomic Perturbation Robustness Experiment
Tests whether candidate policies robustly adapt their investment allocations and timing
under macroeconomic environment shocks (50 matched seeds each):
  Scenario 0: Standard Baseline ($3,000 starting cash)
  Scenario 1: Low Starting Capital ($2,000 starting cash)
  Scenario 2: High Starting Capital ($4,000 starting cash)
  Scenario 3: Price Inversion (Strawberry $80 vs Wool $250)
  Scenario 4: Feed Price Surge (Wheat $50 vs $25)
Compares:
  - Baseline Control (CL-Economic-V1)
  - Fixed Straw+Sheep Control (Arm D)
  - State-Derived Policy (CL-Temporal-V1)
  - Integrated Policy (CL-Temporal-V2)
"""

import sys
import os
import time
import json
import numpy as np
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor, as_completed

PROJECT_ROOT = os.path.abspath(".")
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import kaggle_environments

SEEDS = list(range(2000, 2050)) # 50 matched seeds

CANDIDATES = {
    "Baseline": "candidates.candidate_cl_economic_v1",
    "Fixed-Control": "candidates.candidate_cl_fixed_straw_sheep_control",
    "CL-Temporal-V1": "candidates.candidate_cl_temporal_v1",
    "CL-Temporal-V2": "candidates.candidate_cl_temporal_v2",
}

SCENARIOS = {
    "Standard": {},
    "Low-Money-$2k": {"playerMoney": 2000.0},
    "High-Money-$4k": {"playerMoney": 4000.0},
    "Inverted-Prices": {"marketPrices": {"STRAWBERRY": 80.0, "WOOL": 250.0}},
    "Feed-Surge-$50": {"marketPrices": {"WHEAT": 50.0}},
}

def _eval_perturbation_match(item):
    cand_name, mod_name, scen_name, scen_cfg, seed = item
    
    mod = __import__(mod_name, fromlist=["agent_fn", "agent"])
    agent = getattr(mod, "agent_fn", getattr(mod, "agent", None))
    
    cfg = {"episodeSteps": 720, "seed": seed}
    cfg.update(scen_cfg)
    
    env = kaggle_environments.make("kaggriculture", configuration=cfg)
    try:
        env.run([agent, "starter"])
        r = float(env.steps[-1][0].get("reward") or 0.0)
        return {"cand": cand_name, "scen": scen_name, "seed": seed, "reward": r, "error": None}
    except Exception as e:
        return {"cand": cand_name, "scen": scen_name, "seed": seed, "reward": 0.0, "error": str(e)}

def run_all_perturbations(max_workers=10):
    print("=" * 95)
    print("MACROECONOMIC PERTURBATION ROBUSTNESS EXPERIMENT (50 SEEDS PER SCENARIO)")
    print("=" * 95)
    
    tasks = []
    for c_name, mod_name in CANDIDATES.items():
        for s_name, s_cfg in SCENARIOS.items():
            for s in SEEDS:
                tasks.append((c_name, mod_name, s_name, s_cfg, s))
                
    total = len(tasks)
    print(f"Total perturbation runs: {total} ({len(CANDIDATES)} candidates x {len(SCENARIOS)} scenarios x {len(SEEDS)} seeds)")
    
    results = defaultdict(lambda: defaultdict(list))
    t0 = time.time()
    completed = 0
    
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(_eval_perturbation_match, t) for t in tasks]
        for f in as_completed(futures):
            res = f.result()
            if res["error"] is None:
                results[res["scen"]][res["cand"]].append(res["reward"])
            completed += 1
            if completed % 100 == 0 or completed == total:
                print(f"Perturbation Progress: {completed}/{total} ({completed/total*100:.1f}%) in {time.time()-t0:.1f}s")
                
    # Summary
    summary = {}
    print("\n" + "=" * 105)
    print(f"{'SCENARIO':<18} | {'BASELINE ($)':<18} | {'FIXED-CONTROL ($)':<18} | {'CL-TEMPORAL-V1 ($)':<20} | {'CL-TEMPORAL-V2 ($)':<20}")
    print("-" * 105)
    for s_name in SCENARIOS.keys():
        row = f"{s_name:<18} | "
        summary[s_name] = {}
        for c_name in CANDIDATES.keys():
            arr = results[s_name][c_name]
            m = float(np.mean(arr)) if arr else 0.0
            std = float(np.std(arr)) if arr else 0.0
            summary[s_name][c_name] = {"mean": m, "std": std}
            row += f"${m:10,.1f} +/-${std:5,.0f} | "
        print(row)
    print("=" * 105)
    
    with open("scratch/perturbation_results.json", "w") as f:
        json.dump(summary, f, indent=2)
    print("\nSaved perturbation results to scratch/perturbation_results.json")
    return summary

if __name__ == "__main__":
    run_all_perturbations()
