import json
import os
import sys
import numpy as np

sys.path.insert(0, os.getcwd())
import kaggle_environments

from candidates.candidate_cl_economic_v1 import agent as cl_baseline
from candidates.candidate_cl_fert_gated import agent as cl_m1
from candidates.candidate_cl_harvest_priority import agent as cl_m3
from candidates.candidate_cl_planting_cutoff import agent as cl_m4
from candidates.candidate_cl_pair_m1_m3 import agent as cl_m1_m3
from candidates.candidate_cl_pair_m1_m4 import agent as cl_m1_m4
from candidates.candidate_cl_pair_m3_m4 import agent as cl_m3_m4
from candidates.candidate_cl_trio_m1_m3_m4 import agent as cl_trio

SEEDS = list(range(1000, 1010))

ARMS = [
    ("Baseline (CL-Economic-V1)", cl_baseline),
    ("M1 (Fertilizer Gating)", cl_m1),
    ("M3 (Immediate Harvest)", cl_m3),
    ("M4 (Day 14 Cutoff)", cl_m4),
    ("M1 + M3 (Fert + Harvest)", cl_m1_m3),
    ("M1 + M4 (Fert + Cutoff)", cl_m1_m4),
    ("M3 + M4 (Harvest + Cutoff)", cl_m3_m4),
    ("M1 + M3 + M4 (All 3)", cl_trio),
]

def eval_arm(agent_fn, seed):
    env = kaggle_environments.make("kaggriculture", configuration={"seed": seed})
    steps = env.run([agent_fn, "starter"])

    straw_h = 0
    straw_decay = 0
    straw_fert = 0
    wheat_h = 0
    milk_h = 0
    wool_h = 0

    for s_idx in range(1, len(steps)):
        prev_obs = steps[s_idx - 1][0]["observation"]
        curr_obs = steps[s_idx][0]["observation"]
        act = steps[s_idx][0].get("action") or {}

        prev_tiles = prev_obs["farms"][0]["tiles"]
        curr_tiles = curr_obs["farms"][0]["tiles"]
        prev_farmer = prev_obs["farms"][0]["farmer"]
        prev_hands = prev_obs["farms"][0]["hands"]
        prev_workers = ([prev_farmer] if prev_farmer else []) + [h for h in prev_hands if h]

        # Decay check
        for y in range(10):
            for x in range(10):
                p = prev_tiles[y][x]
                c = curr_tiles[y][x]
                if isinstance(p, dict) and p.get("crop") == "STRAWBERRY":
                    yu = p.get("yield_units", 0)
                    if isinstance(c, dict) and c.get("kind") == "WEED":
                        if yu > 0: straw_decay += yu
                    elif isinstance(c, dict) and c.get("crop") == "STRAWBERRY":
                        all_acts = ([act.get("farmer")] if act.get("farmer") else []) + (act.get("hands", []) or [])
                        harvested = any(w_act and w_act[0] == "HARVEST" and w_pos == [x, y] for w_pos, w_act in zip(prev_workers, all_acts))
                        if not harvested and yu > c.get("yield_units", 0):
                            straw_decay += (yu - c["yield_units"])

        # Actions check
        all_acts = ([act.get("farmer")] if act.get("farmer") else []) + [h for h in act.get("hands", []) if h]
        for w_idx, w_act in enumerate(all_acts):
            if not w_act or len(w_act) == 0: continue
            if w_idx >= len(prev_workers) or prev_workers[w_idx] is None: continue
            wx, wy = prev_workers[w_idx]
            pt = prev_tiles[wy][wx]
            op = w_act[0]

            if op == "FERTILIZE" and isinstance(pt, dict) and pt.get("crop") == "STRAWBERRY":
                straw_fert += 1
            elif op == "HARVEST" and isinstance(pt, dict):
                crop = pt.get("crop")
                animal = pt.get("animal")
                yu = pt.get("yield_units", 0)
                if crop == "STRAWBERRY": straw_h += yu
                elif crop == "WHEAT": wheat_h += yu
                elif animal == "COW": milk_h += yu
                elif animal == "SHEEP": wool_h += yu

    reward = steps[-1][0]["observation"]["farms"][0]["money"]
    return {
        "reward": reward,
        "straw_h": straw_h,
        "straw_decay": straw_decay,
        "straw_fert": straw_fert,
        "wheat_h": wheat_h,
        "milk_h": milk_h,
        "wool_h": wool_h
    }

def main():
    print("="*100)
    print("PHASE 15: COMPLETE STEPWISE ABLATION & PAIRWISE INTERACTION TOURNAMENT (SEEDS 1000-1009)")
    print("="*100)

    summary_table = []

    for name, fn in ARMS:
        print(f"\nEvaluating {name}...")
        res = []
        for s in SEEDS:
            r = eval_arm(fn, s)
            res.append(r)
        
        rew_mean = np.mean([r["reward"] for r in res])
        straw_mean = np.mean([r["straw_h"] for r in res])
        decay_mean = np.mean([r["straw_decay"] for r in res])
        fert_mean = np.mean([r["straw_fert"] for r in res])
        wheat_mean = np.mean([r["wheat_h"] for r in res])
        milk_mean = np.mean([r["milk_h"] for r in res])
        wool_mean = np.mean([r["wool_h"] for r in res])

        summary_table.append({
            "name": name,
            "reward": rew_mean,
            "straw": straw_mean,
            "decay": decay_mean,
            "fert": fert_mean,
            "wheat": wheat_mean,
            "milk": milk_mean,
            "wool": wool_mean
        })

    base_rew = summary_table[0]["reward"]
    base_straw = summary_table[0]["straw"]

    print("\n" + "="*115)
    print(f"{'Arm':<28} | {'Reward ($)':<12} | {'Delta Rew':<10} | {'Straw':<7} | {'Delta S':<8} | {'Decay':<6} | {'Fert':<6} | {'Wheat':<6} | {'Milk':<6} | {'Wool':<6}")
    print("-" * 115)
    for row in summary_table:
        d_rew = row["reward"] - base_rew
        d_straw = row["straw"] - base_straw
        print(f"{row['name']:<28} | ${row['reward']:<11,.1f} | {d_rew:<+10,.1f} | {row['straw']:<7.2f} | {d_straw:<+8.2f} | {row['decay']:<6.2f} | {row['fert']:<6.1f} | {row['wheat']:<6.1f} | {row['milk']:<6.1f} | {row['wool']:<6.1f}")
    print("="*115)

    with open("scratch/pairwise_ablation_results.json", "w") as f:
        json.dump(summary_table, f, indent=2)

if __name__ == "__main__":
    main()
