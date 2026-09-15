import json
import os
import sys
import numpy as np

sys.path.insert(0, os.getcwd())
import kaggle_environments

from candidates.candidate_cl_economic_v1 import agent as cl_baseline
from candidates.candidate_cl_fert_gated import agent as cl_fert_gated

SEEDS = list(range(1000, 1010))

def run_and_measure(agent_fn, seed):
    env = kaggle_environments.make("kaggriculture", configuration={"seed": seed})
    steps = env.run([agent_fn, "starter"])

    straw_harvest = 0
    straw_fert_actions = 0
    total_fert_actions = 0
    total_water_straw = 0
    movement_steps = 0
    wool_harvest = 0
    milk_harvest = 0
    wheat_harvest = 0
    fert_sold = 0

    # For harvest latency: track for each strawberry bush when yu became > 0 and when harvested
    # bush -> {first_ripe_step: step}
    straw_bushes = {} # (x, y) -> dict
    latencies = []

    for s_idx in range(1, len(steps)):
        prev_obs = steps[s_idx - 1][0]["observation"]
        curr_obs = steps[s_idx][0]["observation"]
        act = steps[s_idx][0].get("action") or {}

        prev_farm = prev_obs["farms"][0]
        curr_farm = curr_obs["farms"][0]
        prev_tiles = prev_farm["tiles"]
        curr_tiles = curr_farm["tiles"]

        prev_farmer = prev_farm["farmer"]
        prev_hands = prev_farm["hands"]
        prev_workers = ([prev_farmer] if prev_farmer else []) + [h for h in prev_hands if h]

        # Check market sells
        for m in act.get("market", []):
            if len(m) >= 3 and m[0] == "SELL" and m[1] == "FERTILIZER":
                fert_sold += int(m[2])

        # Track ripeness for latency
        for y in range(10):
            for x in range(10):
                pt = prev_tiles[y][x]
                if isinstance(pt, dict) and pt.get("crop") == "STRAWBERRY":
                    pos = (x, y)
                    yu = pt.get("yield_units", 0)
                    if yu > 0:
                        if pos not in straw_bushes or straw_bushes[pos].get("ripe_since") is None:
                            straw_bushes[pos] = {"ripe_since": s_idx - 1}

        # Track worker actions
        all_acts = ([act.get("farmer")] if act.get("farmer") else []) + [h for h in act.get("hands", []) if h]
        for w_idx, w_act in enumerate(all_acts):
            if not w_act or len(w_act) == 0:
                continue
            op = w_act[0]
            if op in ("NORTH", "SOUTH", "EAST", "WEST"):
                movement_steps += 1
            if w_idx >= len(prev_workers) or prev_workers[w_idx] is None:
                continue
            wx, wy = prev_workers[w_idx]
            pt = prev_tiles[wy][wx]

            if op == "FERTILIZE":
                total_fert_actions += 1
                if isinstance(pt, dict) and pt.get("crop") == "STRAWBERRY":
                    straw_fert_actions += 1

            elif op == "WATER":
                if isinstance(pt, dict) and pt.get("crop") == "STRAWBERRY":
                    total_water_straw += 1

            elif op == "HARVEST":
                if isinstance(pt, dict):
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
        "straw_fert_actions": straw_fert_actions,
        "total_fert_actions": total_fert_actions,
        "fert_sold": fert_sold,
        "total_water_straw": total_water_straw,
        "mean_latency": mean_latency,
        "movement_steps": movement_steps,
        "wheat_harvest": wheat_harvest,
        "milk_harvest": milk_harvest,
        "wool_harvest": wool_harvest
    }

def main():
    print("="*80)
    print("PHASE 5: CRITICAL FERTILIZER COUNTERFACTUAL (SEEDS 1000-1009)")
    print("="*80)
    print("Comparing Baseline (CL-Economic-V1) vs Mature-Fertilizer-Gating...")

    base_res = []
    gated_res = []

    for seed in SEEDS:
        print(f"Running Seed {seed}...")
        b = run_and_measure(cl_baseline, seed)
        g = run_and_measure(cl_fert_gated, seed)
        base_res.append(b)
        gated_res.append(g)

    metrics = [
        ("Reward ($)", "reward", "${:,.1f}"),
        ("Strawberry Harvest (units)", "straw_harvest", "{:.2f}"),
        ("Strawberry Fert Actions", "straw_fert_actions", "{:.2f}"),
        ("Total Fert Actions", "total_fert_actions", "{:.2f}"),
        ("Fertilizer Sold (orders)", "fert_sold", "{:.2f}"),
        ("Strawberry Water Actions", "total_water_straw", "{:.2f}"),
        ("Harvest Latency (steps)", "mean_latency", "{:.2f}"),
        ("Movement Steps", "movement_steps", "{:.2f}"),
        ("Wheat Harvest (units)", "wheat_harvest", "{:.2f}"),
        ("Milk Harvest (units)", "milk_harvest", "{:.2f}"),
        ("Wool Harvest (units)", "wool_harvest", "{:.2f}"),
    ]

    print("\n" + "="*80)
    print(f"{'Metric':<30} | {'Baseline CL':<15} | {'Gated CL':<15} | {'Delta':<12}")
    print("-" * 78)

    results_table = {}
    for label, key, fmt in metrics:
        b_vals = [r[key] for r in base_res]
        g_vals = [r[key] for r in gated_res]
        b_mean = np.mean(b_vals)
        g_mean = np.mean(g_vals)
        delta = g_mean - b_mean
        results_table[key] = {
            "baseline": b_mean,
            "gated": g_mean,
            "delta": delta
        }
        if "Reward" in label:
            print(f"{label:<30} | ${b_mean:<14,.1f} | ${g_mean:<14,.1f} | {delta:<+12,.1f}")
        else:
            print(f"{label:<30} | {b_mean:<15.2f} | {g_mean:<15.2f} | {delta:<+12.2f}")
    print("="*80)

    # Per seed table for strawberry harvest & reward
    print("\nPer-Seed Breakdown (Baseline vs Gated):")
    print(f"{'Seed':<6} | {'Base Reward':<12} | {'Gated Reward':<12} | {'Delta Rew':<10} | {'Base Straw':<10} | {'Gated Straw':<11} | {'Delta Straw':<10}")
    print("-" * 85)
    for i, s in enumerate(SEEDS):
        br = base_res[i]["reward"]
        gr = gated_res[i]["reward"]
        bs = base_res[i]["straw_harvest"]
        gs = gated_res[i]["straw_harvest"]
        print(f"{s:<6} | ${int(br):<11,d} | ${int(gr):<11,d} | ${int(gr-br):<+9,d} | {bs:<10} | {gs:<11} | {gs-bs:<+10}")
    print("="*85)

    with open("scratch/fert_counterfactual_results.json", "w") as f:
        json.dump({"summary": results_table, "base": base_res, "gated": gated_res}, f, indent=2)

if __name__ == "__main__":
    main()
