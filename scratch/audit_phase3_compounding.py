"""
Phase 3: Cash Compounding & State Trajectory Decomposition
Quantifies exact state progression across critical steps:
[120, 150, 200, 240, 255, 264, 265, 266, 288, 336, 360, 500, 650, 719]
Produces:
- FIRST CASH ADVANTAGE
- FIRST PRODUCTION ADVANTAGE
- FIRST REINVESTMENT ADVANTAGE
- FIRST TERMINAL ADVANTAGE
"""

import sys
import os
import json
import numpy as np
from concurrent.futures import ProcessPoolExecutor

PROJECT_ROOT = os.path.abspath(".")
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from kaggle_environments import make
import candidates.slot2_aethel_refined_v2 as v2
from scratch.v2_jit_melon_experiment import agent_H_full_jit_pipeline

STEPS_TO_TRACK = [120, 150, 200, 240, 255, 264, 265, 266, 288, 336, 360, 500, 650, 719]

def count_quadrants(board_size):
    # Standard board is 10x10 (1 quadrant) or expandable (10, 15, 20)
    # In kaggriculture, tiles size indicates board expansion
    if board_size <= 10: return 1
    elif board_size <= 15: return 2 # or 3
    elif board_size <= 20: return 4
    return 1

def run_seed_trajectory(seed):
    trajectory = {}
    for label, fn in [("V2", v2.agent), ("H", agent_H_full_jit_pipeline)]:
        env = make("kaggriculture", configuration={"seed": seed, "episodeSteps": 720})
        env.reset()
        
        step_data = {}
        for step in range(720):
            obs = env.steps[-1][0]["observation"]
            if step in STEPS_TO_TRACK:
                farm = obs["farms"][0]
                priv = obs["private"]
                shed = priv.get("shed", {})
                
                melons_on_field = 0
                strawberries_on_field = 0
                cows_count = 0
                sheep_count = 0
                pastures_count = 0
                
                for row in farm.get("tiles", []):
                    for t in row:
                        if isinstance(t, dict):
                            crop = t.get("crop")
                            kind = t.get("kind")
                            animal = t.get("animal")
                            if crop == "MELON": melons_on_field += 1
                            elif crop == "STRAWBERRY": strawberries_on_field += 1
                            if animal == "COW": cows_count += 1
                            elif animal == "SHEEP": sheep_count += 1
                            if kind == "PASTURE": pastures_count += 1
                
                board_dim = len(farm.get("tiles", []))
                
                step_data[str(step)] = {
                    "cash": float(farm.get("money", 0)),
                    "shed_melon": int(shed.get("MELON", 0)),
                    "field_melon": melons_on_field,
                    "total_melon": int(shed.get("MELON", 0)) + melons_on_field,
                    "shed_strawberry": int(shed.get("STRAWBERRY", 0)),
                    "field_strawberry": strawberries_on_field,
                    "total_strawberry": int(shed.get("STRAWBERRY", 0)) + strawberries_on_field,
                    "shed_milk": int(shed.get("MILK", 0)),
                    "shed_wool": int(shed.get("WOOL", 0)),
                    "shed_fertilizer": int(shed.get("FERTILIZER", 0)),
                    "cows": cows_count,
                    "sheep": sheep_count,
                    "workers": len(farm.get("hands", [])),
                    "pastures": pastures_count,
                    "quadrants": count_quadrants(board_dim)
                }
                
            if env.done:
                break
            action = fn(obs)
            env.step([action, {"farmer": ["PASS"]}])
            
        trajectory[label] = step_data
    return {"seed": seed, "trajectory": trajectory}

def main():
    seeds = [42, 100, 101, 2026, 777, 999, 1050, 1051, 1052, 1053]
    print(f"Running Phase 3 compounding audit on {len(seeds)} seeds...")
    
    with ProcessPoolExecutor(max_workers=5) as executor:
        results = list(executor.map(run_seed_trajectory, seeds))
        
    # Aggregate means across seeds
    summary_by_step = {}
    for st in STEPS_TO_TRACK:
        st_str = str(st)
        v2_cash = [r["trajectory"]["V2"][st_str]["cash"] for r in results]
        h_cash = [r["trajectory"]["H"][st_str]["cash"] for r in results]
        v2_melon = [r["trajectory"]["V2"][st_str]["total_melon"] for r in results]
        h_melon = [r["trajectory"]["H"][st_str]["total_melon"] for r in results]
        v2_cows = [r["trajectory"]["V2"][st_str]["cows"] for r in results]
        h_cows = [r["trajectory"]["H"][st_str]["cows"] for r in results]
        v2_sheep = [r["trajectory"]["V2"][st_str]["sheep"] for r in results]
        h_sheep = [r["trajectory"]["H"][st_str]["sheep"] for r in results]
        v2_workers = [r["trajectory"]["V2"][st_str]["workers"] for r in results]
        h_workers = [r["trajectory"]["H"][st_str]["workers"] for r in results]
        v2_pastures = [r["trajectory"]["V2"][st_str]["pastures"] for r in results]
        h_pastures = [r["trajectory"]["H"][st_str]["pastures"] for r in results]
        v2_fert = [r["trajectory"]["V2"][st_str]["shed_fertilizer"] for r in results]
        h_fert = [r["trajectory"]["H"][st_str]["shed_fertilizer"] for r in results]
        v2_straw = [r["trajectory"]["V2"][st_str]["total_strawberry"] for r in results]
        h_straw = [r["trajectory"]["H"][st_str]["total_strawberry"] for r in results]
        
        summary_by_step[st_str] = {
            "v2_cash_mean": float(np.mean(v2_cash)),
            "h_cash_mean": float(np.mean(h_cash)),
            "cash_delta": float(np.mean(h_cash) - np.mean(v2_cash)),
            "v2_melon_mean": float(np.mean(v2_melon)),
            "h_melon_mean": float(np.mean(h_melon)),
            "melon_delta": float(np.mean(h_melon) - np.mean(v2_melon)),
            "v2_cows_mean": float(np.mean(v2_cows)),
            "h_cows_mean": float(np.mean(h_cows)),
            "v2_sheep_mean": float(np.mean(v2_sheep)),
            "h_sheep_mean": float(np.mean(h_sheep)),
            "v2_workers_mean": float(np.mean(v2_workers)),
            "h_workers_mean": float(np.mean(h_workers)),
            "v2_pastures_mean": float(np.mean(v2_pastures)),
            "h_pastures_mean": float(np.mean(h_pastures)),
            "v2_fert_mean": float(np.mean(v2_fert)),
            "h_fert_mean": float(np.mean(h_fert)),
            "v2_straw_mean": float(np.mean(v2_straw)),
            "h_straw_mean": float(np.mean(h_straw)),
        }
        
    print("\n--- PHASE 3 COMPOUNDING SUMMARY ---")
    print(json.dumps(summary_by_step, indent=2))
    
    with open("scratch/jit_melon_results/phase3_compounding_audit.json", "w") as f:
        json.dump({"summary": summary_by_step, "samples": results[:2]}, f, indent=2)

if __name__ == "__main__":
    main()
