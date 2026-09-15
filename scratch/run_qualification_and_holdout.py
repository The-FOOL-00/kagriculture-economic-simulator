"""
RIGOROUS 3-DATASET BENCHMARK: V2 VS CANDIDATE POLICIES
======================================================
Evaluates promising candidate policies directly against CLOSED_LOOP_V2 across:
1. Qualification Dataset: Seeds 50050-50099 (N=100 games, balanced seats, CRN)
2. Fresh Holdout Dataset: Seeds 50100-50149 (N=100 games, balanced seats, CRN)
Measures:
- Win Rate
- Paired Margin (mean & median)
- 95% Confidence Interval
- 5th Percentile Lower Tail
- Worst Loss
- Catastrophic Loss Rate (< $60k)
- Shop Stratified Breakdowns
"""
import os
import sys
import json
import math
from typing import Dict, List, Any

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(BASE_DIR, "external_repos", "kaggriculture-cppsim"))
sys.path.insert(0, os.path.join(BASE_DIR, "candidates", "closed_loop_architecture"))
sys.path.insert(0, os.path.join(BASE_DIR, "scratch"))

from run_additive_investigation import evaluate_paired_dataset_parallel as evaluate_paired_dataset

def run_evaluation_suite(candidate_configs: List[Dict[str, Any]]):
    datasets = {
        "Qualification (Seeds 50050-50099)": list(range(50050, 50100)),
        "Fresh Holdout (Seeds 50100-50149)": list(range(50100, 50150))
    }
    
    all_results = {}
    for cfg in candidate_configs:
        name = cfg["name"]
        pol = cfg["policy"]
        k = cfg["k"]
        day = cfg["deploy_day"]
        mode = cfg["land_mode"]
        
        all_results[name] = {}
        print("\n" + "=" * 90)
        print(f"EVALUATING CANDIDATE: {name} (Policy={pol}, k={k}, Day={day}, Land={mode})")
        print("=" * 90)
        
        for d_name, seeds in datasets.items():
            print(f"Running on {d_name} (N={len(seeds)*2} games, CRN, Balanced Seats)...", flush=True)
            res = evaluate_paired_dataset(policy_name=pol, k=k, deploy_day=day, land_mode=mode, seeds=seeds)
            all_results[name][d_name] = res
            
            print(f"  Win Rate:          {res['win_rate']*100:5.1f}%")
            print(f"  Paired Margin:     {res['paired_margin']:+8.1f} ± {res['ci95']:5.1f}")
            print(f"  Median Margin:     {res['median_margin']:+8.1f}")
            print(f"  Worst Loss:        {res['worst_loss']:+8.1f}")
            print(f"  Catastrophic Rate: {res['catastrophic_rate']*100:5.1f}%")
            print(f"  5th Pct Cash:      ${res['p5_cash']:8.1f}")
            print("  Stratified by Shop Family:")
            for fam, fam_data in res["stratified"].items():
                print(f"    {fam:25s}: Margin={fam_data['mean_margin']:+7.1f}, WinRate={fam_data['win_rate']*100:5.1f}% (N={fam_data['n_games']})")

    out_file = os.path.join(BASE_DIR, "scratch", "qualification_and_holdout_results.json")
    with open(out_file, "w") as f:
        json.dump(all_results, f, indent=2)
    print(f"\nSaved qualification & holdout results to {out_file}")

if __name__ == "__main__":
    configs = [
        {"name": "Policy E (Pizza->4, SE Land, Day 12)", "policy": "POLICY_E", "k": 4, "deploy_day": 12, "land_mode": "SE_LAND"},
        {"name": "Policy F (Pizza No Straw->4, SE Land, Day 12)", "policy": "POLICY_F", "k": 4, "deploy_day": 12, "land_mode": "SE_LAND"},
        {"name": "Policy H (Full Info Gated, SE Land, Day 12)", "policy": "POLICY_H", "k": 2, "deploy_day": 12, "land_mode": "SE_LAND"},
        {"name": "Policy E (Pizza->2, Vacant Land, Day 12)", "policy": "POLICY_E", "k": 2, "deploy_day": 12, "land_mode": "VACANT_TILES"},
    ]
    run_evaluation_suite(configs)
