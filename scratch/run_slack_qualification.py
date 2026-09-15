"""
SLACK-CAPACITY REAL-OPTION: QUALIFICATION + HOLDOUT EVALUATION
==============================================================
Evaluates the top candidate policies from Discovery (Seeds 50000-50049) on:
  - Qualification: Seeds 50050-50099 (N=100 games, balanced seats, CRN)
  - Fresh Holdout: Seeds 50100-50149 (N=100 games, balanced seats, CRN)

Candidates evaluated:
  - POLICY_F: k=4 tomatoes on SE_LAND if (Pizza_shop AND NOT Straw_shop)
  - POLICY_G: k=4 if pizza + shed_free>40, k=2 if shed_free>20, else 0
  - POLICY_E: k=4 tomatoes on SE_LAND if Pizza_shop present (any combo)
  - POLICY_H: k=2 if pizza and <2 straw shops and shed_free>=35 (hardest gating)
  - vk_vacant k=1: 1 tomato on Vacant tiles if Pizza (pizza-conditioned, cheap)
"""
import os, sys, json, math
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor
from typing import Dict, List, Any

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(BASE_DIR, "external_repos", "kaggriculture-cppsim"))
sys.path.insert(0, os.path.join(BASE_DIR, "candidates", "closed_loop_architecture"))
sys.path.insert(0, os.path.join(BASE_DIR, "scratch"))

from run_additive_investigation import (
    evaluate_paired_dataset_parallel,
    precompute_shop_families,
)

DATASETS = {
    "Qualification (50050-50099)": list(range(50050, 50100)),
    "Fresh Holdout (50100-50149)": list(range(50100, 50150)),
}

CANDIDATES = [
    {"name": "POLICY_F (Pizza no-Straw -> k=4, SE_LAND, Day12)", "policy": "POLICY_F", "k": 4, "deploy_day": 12, "land_mode": "SE_LAND"},
    {"name": "POLICY_G (Pizza+ShedFree gated, SE_LAND, Day12)",   "policy": "POLICY_G", "k": 4, "deploy_day": 12, "land_mode": "SE_LAND"},
    {"name": "POLICY_E (Any Pizza -> k=4, SE_LAND, Day12)",       "policy": "POLICY_E", "k": 4, "deploy_day": 12, "land_mode": "SE_LAND"},
    {"name": "POLICY_H (Full-gated k=2, SE_LAND, Day12)",         "policy": "POLICY_H", "k": 2, "deploy_day": 12, "land_mode": "SE_LAND"},
    {"name": "vk_vacant k=1 (Pizza -> k=1, VACANT, Day12)",       "policy": "SWEEP_K_1", "k": 1, "deploy_day": 12, "land_mode": "VACANT_TILES"},
]

def print_result(r: Dict[str, Any]):
    print(f"  WinRate:          {r['win_rate']*100:5.1f}%")
    print(f"  PairedMargin:     {r['paired_margin']:+8.1f} ± {r['ci95']:5.1f}  (95% CI)")
    print(f"  MedianMargin:     {r['median_margin']:+8.1f}")
    print(f"  WorstLoss:        {r['worst_loss']:+8.1f}")
    print(f"  CatastrophicRate: {r['catastrophic_rate']*100:5.1f}%  (<$60k)")
    print(f"  P5 Cash:          ${r['p5_cash']:8.1f}")
    print(f"  Stratified:")
    for fam, fd in r.get("stratified", {}).items():
        print(f"    {fam:30s}: margin={fd['mean_margin']:+7.1f}  wr={fd['win_rate']*100:5.1f}%  N={fd['n_games']}")

def main():
    all_results = {}

    for ds_name, seeds in DATASETS.items():
        print(f"\n{'='*100}")
        print(f"DATASET: {ds_name}")
        print(f"{'='*100}\n")

        families = precompute_shop_families(seeds)
        ds_results = {}

        with ProcessPoolExecutor(max_workers=6) as executor:
            for cfg in CANDIDATES:
                name = cfg["name"]
                print(f"\n--- {name} ---")
                r = evaluate_paired_dataset_parallel(
                    policy_name=cfg["policy"],
                    k=cfg["k"],
                    deploy_day=cfg["deploy_day"],
                    land_mode=cfg["land_mode"],
                    seeds=seeds,
                    families=families,
                    executor=executor,
                )
                ds_results[name] = r
                print_result(r)

        all_results[ds_name] = ds_results

    out = os.path.join(BASE_DIR, "scratch", "qualification_and_holdout_results.json")
    with open(out, "w") as f:
        json.dump(all_results, f, indent=2)
    print(f"\n\nSaved results to {out}")

    # Print summary table
    print("\n\n" + "="*110)
    print("QUALIFICATION + HOLDOUT SUMMARY TABLE")
    print("="*110)
    print(f"{'Candidate':<45} {'Dataset':<30} {'Margin':>10} {'CI95':>8} {'WinRate':>9} {'WorstLoss':>11}")
    print("-"*110)
    for ds_name, ds_results in all_results.items():
        for cname, r in ds_results.items():
            short = cname[:44]
            short_ds = ds_name[:29]
            print(f"{short:<45} {short_ds:<30} {r['paired_margin']:>+10.1f} {r['ci95']:>8.1f} {r['win_rate']*100:>8.1f}% {r['worst_loss']:>+11.1f}")

if __name__ == "__main__":
    main()
