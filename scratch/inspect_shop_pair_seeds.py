"""
scratch/inspect_shop_pair_seeds.py
Find seeds from the 500-seed census with specific non-Yarn shop pairs.
Test candidate routes against Plan 0 baseline on the exact same seeds.
"""
import json
import os
import sys

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, BASE_DIR)
sys.path.insert(0, os.path.join(BASE_DIR, "external_repos", "kaggriculture-cppsim"))
sys.path.insert(0, os.path.join(BASE_DIR, "candidates"))
sys.path.insert(0, os.path.join(BASE_DIR, "extracted_agents", "dmitrii_lb2800"))

import kagsim
import compiled_v54_plus_residual
from router_parent import SHOP_PLANS

def main():
    with open(os.path.join(BASE_DIR, "results", "phase3_shop_census_500seeds.json")) as f:
        data = json.load(f)
        
    print("Pairs and counts:")
    for pair_str, count in sorted(data["pair_counts"].items(), key=lambda x: -x[1])[:20]:
        print(f"  {pair_str:35}: {count:3d} seeds | mean cash: ${data['pair_dmitrii_mean'].get(pair_str, 0):10,.2f}")

if __name__ == "__main__":
    main()
