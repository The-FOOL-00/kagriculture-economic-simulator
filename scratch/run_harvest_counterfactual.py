import json
import os
import sys
import numpy as np

sys.path.insert(0, os.getcwd())
import kaggle_environments

from candidates.candidate_cl_economic_v1 import agent as cl_baseline
from candidates.candidate_cl_harvest_priority import agent as cl_harvest_prio

SEEDS = list(range(1000, 1010))

def run_and_measure(agent_fn, seed):
    env = kaggle_environments.make("kaggriculture", configuration={"seed": seed})
    steps = env.run([agent_fn, "starter"])

    straw_harvest = 0
    straw_bushes = {}
    latencies = []
    straw_decay_units = 0
    wool_harvest = 0
    milk_harvest = 0
    wheat_harvest = 0

    for s_idx in range(1, len(steps)):
        prev_obs = steps[s_idx - 1][0]["observation"]
        curr_obs = steps[s_idx][0]["observation"]
        act = steps[s_idx][0].get("action") or {}

        prev_tiles = prev_obs["farms"][0]["tiles"]
        curr_tiles = curr_obs["farms"][0]["tiles"]
        prev_farmer = prev_obs["farms"][0]["farmer"]
        prev_hands = prev_obs["farms"][0]["hands"]
        prev_workers = ([prev_farmer] if prev_farmer else []) + [h for h in prev_hands if h]

        # Track decay
        for y in range(10):
            for x in range(10):
                p = prev_tiles[y][x]
                c = curr_tiles[y][x]
                if isinstance(p, dict) and p.get("crop") == "STRAWBERRY":
                    yu = p.get("yield_units", 0)
                    if yu > 0:
                        pos = (x, y)
                        if pos not in straw_bushes or straw_bushes[pos].get("ripe_since") is None:
                            straw_bushes[pos] = {"ripe_since": s_idx - 1}

                    if isinstance(c, dict) and c.get("kind") == "WEED":
                        if yu > 0:
                            straw_decay_units += yu
                    elif isinstance(c, dict) and c.get("crop") == "STRAWBERRY":
                        all_acts = ([act.get("farmer")] if act.get("farmer") else []) + (act.get("hands", []) or [])
                        harvested = any(w_act and w_act[0] == "HARVEST" and w_pos == [x, y] for w_pos, w_act in zip(prev_workers, all_acts))
                        if not harvested and yu > c.get("yield_units", 0):
                            straw_decay_units += (yu - c["yield_units"])

        # Track harvest
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
                    pos = (wx, wy)
                    if pos in straw_bushes and straw_bushes[pos].get("ripe_since") is not None:
                        latency = (s_idx - 1) - straw_bushes[pos]["ripe_since"]
                        latencies.append(latency)
                        straw_bushes[pos]["ripe_since"] = None
                elif crop == "WHEAT":
                    wheat_harvest += yu
                elif animal == "COW":
                    milk_harvest += yu
                elif animal == "SHEEP":
                    wool_harvest += yu

    reward = steps[-1][0]["observation"]["farms"][0]["money"]
    mean_latency = float(np.mean(latencies)) if latencies else 0.0

    return {
        "reward": reward,
        "straw_harvest": straw_harvest,
        "straw_decay_units": straw_decay_units,
        "mean_latency": mean_latency,
        "wheat_harvest": wheat_harvest,
        "milk_harvest": milk_harvest,
        "wool_harvest": wool_harvest
    }

def main():
    print("="*80)
    print("PHASE 10: HARVEST-LATENCY & DECAY COUNTERFACTUAL (SEEDS 1000-1009)")
    print("="*80)
    print("Comparing Baseline (CL-Economic-V1) vs Immediate Strawberry Harvesting (yu >= 1)...")

    base_res = []
    prio_res = []

    for seed in SEEDS:
        print(f"Running Seed {seed}...")
        b = run_and_measure(cl_baseline, seed)
        p = run_and_measure(cl_harvest_prio, seed)
        base_res.append(b)
        prio_res.append(p)

    metrics = [
        ("Reward ($)", "reward"),
        ("Strawberry Harvest (units)", "straw_harvest"),
        ("Strawberry Decay Loss (units)", "straw_decay_units"),
        ("Harvest Latency (steps)", "mean_latency"),
        ("Wheat Harvest (units)", "wheat_harvest"),
        ("Milk Harvest (units)", "milk_harvest"),
        ("Wool Harvest (units)", "wool_harvest"),
    ]

    print("\n" + "="*80)
    print(f"{'Metric':<30} | {'Baseline CL':<15} | {'Harvest Prio CL':<16} | {'Delta':<12}")
    print("-" * 78)

    for label, key in metrics:
        b_vals = [r[key] for r in base_res]
        p_vals = [r[key] for r in prio_res]
        b_mean = np.mean(b_vals)
        p_mean = np.mean(p_vals)
        delta = p_mean - b_mean
        if "Reward" in label:
            print(f"{label:<30} | ${b_mean:<14,.1f} | ${p_mean:<15,.1f} | {delta:<+12,.1f}")
        else:
            print(f"{label:<30} | {b_mean:<15.2f} | {p_mean:<16.2f} | {delta:<+12.2f}")
    print("="*80)

    print("\nPer-Seed Breakdown (Baseline vs Harvest Prio):")
    print(f"{'Seed':<6} | {'Base Reward':<12} | {'Prio Reward':<12} | {'Delta Rew':<10} | {'Base Straw':<10} | {'Prio Straw':<11} | {'Delta Straw':<10} | {'Base Decay':<10} | {'Prio Decay':<10}")
    print("-" * 105)
    for i, s in enumerate(SEEDS):
        br = base_res[i]["reward"]
        pr = prio_res[i]["reward"]
        bs = base_res[i]["straw_harvest"]
        ps = prio_res[i]["straw_harvest"]
        bd = base_res[i]["straw_decay_units"]
        pd = prio_res[i]["straw_decay_units"]
        print(f"{s:<6} | ${int(br):<11,d} | ${int(pr):<11,d} | ${int(pr-br):<+9,d} | {bs:<10} | {ps:<11} | {ps-bs:<+10} | {bd:<10} | {pd:<10}")
    print("="*105)

    with open("scratch/harvest_counterfactual_results.json", "w") as f:
        json.dump({"base": base_res, "prio": prio_res}, f, indent=2)

if __name__ == "__main__":
    main()
