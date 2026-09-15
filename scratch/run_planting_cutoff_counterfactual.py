import json
import os
import sys
import numpy as np

sys.path.insert(0, os.getcwd())
import kaggle_environments

from candidates.candidate_cl_economic_v1 import agent as cl_baseline
from candidates.candidate_cl_planting_cutoff import agent as cl_cutoff

SEEDS = list(range(1000, 1010))

def run_and_measure(agent_fn, seed):
    env = kaggle_environments.make("kaggriculture", configuration={"seed": seed})
    steps = env.run([agent_fn, "starter"])

    straw_harvest = 0
    straw_bushes = 0
    wool_harvest = 0
    milk_harvest = 0
    wheat_harvest = 0

    # Count unique strawberry bushes
    planted_coords = set()
    for s_idx in range(1, len(steps)):
        prev_obs = steps[s_idx - 1][0]["observation"]
        curr_obs = steps[s_idx][0]["observation"]
        act = steps[s_idx][0].get("action") or {}

        prev_tiles = prev_obs["farms"][0]["tiles"]
        curr_tiles = curr_obs["farms"][0]["tiles"]
        prev_farmer = prev_obs["farms"][0]["farmer"]
        prev_hands = prev_obs["farms"][0]["hands"]
        prev_workers = ([prev_farmer] if prev_farmer else []) + [h for h in prev_hands if h]

        for y in range(10):
            for x in range(10):
                pt = prev_tiles[y][x]
                ct = curr_tiles[y][x]
                if (not isinstance(pt, dict) or pt.get("crop") != "STRAWBERRY") and (isinstance(ct, dict) and ct.get("crop") == "STRAWBERRY"):
                    planted_coords.add((x, y, s_idx))

        all_acts = ([act.get("farmer")] if act.get("farmer") else []) + [h for h in act.get("hands", []) if h]
        for w_idx, w_act in enumerate(all_acts):
            if not w_act or len(w_act) == 0:
                continue
            if w_idx >= len(prev_workers) or prev_workers[w_idx] is None:
                continue
            wx, wy = prev_workers[w_idx]
            pt = prev_tiles[wy][wx]
            op = w_act[0]

            if op == "HARVEST" and isinstance(pt, dict):
                crop = pt.get("crop")
                animal = pt.get("animal")
                yu = pt.get("yield_units", 0)
                if crop == "STRAWBERRY":
                    straw_harvest += yu
                elif crop == "WHEAT":
                    wheat_harvest += yu
                elif animal == "COW":
                    milk_harvest += yu
                elif animal == "SHEEP":
                    wool_harvest += yu

    reward = steps[-1][0]["observation"]["farms"][0]["money"]

    return {
        "reward": reward,
        "straw_harvest": straw_harvest,
        "straw_bushes": len(planted_coords),
        "wheat_harvest": wheat_harvest,
        "milk_harvest": milk_harvest,
        "wool_harvest": wool_harvest
    }

def main():
    print("="*80)
    print("PHASE 12: LATE-PLANTING CUTOFF COUNTERFACTUAL (SEEDS 1000-1009)")
    print("="*80)
    print("Comparing Baseline (CL-Economic-V1, cutoff=20) vs Planting Cutoff (cutoff=14)...")

    base_res = []
    cut_res = []

    for seed in SEEDS:
        print(f"Running Seed {seed}...")
        b = run_and_measure(cl_baseline, seed)
        c = run_and_measure(cl_cutoff, seed)
        base_res.append(b)
        cut_res.append(c)

    metrics = [
        ("Reward ($)", "reward"),
        ("Strawberry Harvest (units)", "straw_harvest"),
        ("Strawberry Bushes Planted", "straw_bushes"),
        ("Wheat Harvest (units)", "wheat_harvest"),
        ("Milk Harvest (units)", "milk_harvest"),
        ("Wool Harvest (units)", "wool_harvest"),
    ]

    print("\n" + "="*80)
    print(f"{'Metric':<30} | {'Baseline CL':<15} | {'Cutoff-14 CL':<15} | {'Delta':<12}")
    print("-" * 78)

    for label, key in metrics:
        b_vals = [r[key] for r in base_res]
        c_vals = [r[key] for r in cut_res]
        b_mean = np.mean(b_vals)
        c_mean = np.mean(c_vals)
        delta = c_mean - b_mean
        if "Reward" in label:
            print(f"{label:<30} | ${b_mean:<14,.1f} | ${c_mean:<14,.1f} | {delta:<+12,.1f}")
        else:
            print(f"{label:<30} | {b_mean:<15.2f} | {c_mean:<15.2f} | {delta:<+12.2f}")
    print("="*80)

    print("\nPer-Seed Breakdown (Baseline vs Cutoff-14):")
    print(f"{'Seed':<6} | {'Base Reward':<12} | {'Cut Reward':<12} | {'Delta Rew':<10} | {'Base Straw':<10} | {'Cut Straw':<11} | {'Delta Straw':<10}")
    print("-" * 88)
    for i, s in enumerate(SEEDS):
        br = base_res[i]["reward"]
        cr = cut_res[i]["reward"]
        bs = base_res[i]["straw_harvest"]
        cs = cut_res[i]["straw_harvest"]
        print(f"{s:<6} | ${int(br):<11,d} | ${int(cr):<11,d} | ${int(cr-br):<+9,d} | {bs:<10} | {cs:<11} | {cs-bs:<+10}")
    print("="*88)

    with open("scratch/planting_cutoff_results.json", "w") as f:
        json.dump({"base": base_res, "cutoff": cut_res}, f, indent=2)

if __name__ == "__main__":
    main()
