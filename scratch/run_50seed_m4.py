import json
import os
import sys
import numpy as np

sys.path.insert(0, os.getcwd())
import kaggle_environments

from candidates.candidate_cl_economic_v1 import agent as cl_baseline
from candidates.candidate_cl_planting_cutoff import agent as cl_cutoff

SEEDS_50 = list(range(1000, 1050))

def run_seed(agent_fn, seed):
    env = kaggle_environments.make("kaggriculture", configuration={"seed": seed})
    steps = env.run([agent_fn, "starter"])
    reward = steps[-1][0]["observation"]["farms"][0]["money"]
    straw_h = 0
    for s_idx in range(1, len(steps)):
        prev_tiles = steps[s_idx - 1][0]["observation"]["farms"][0]["tiles"]
        act = steps[s_idx][0].get("action") or {}
        prev_farmer = steps[s_idx - 1][0]["observation"]["farms"][0]["farmer"]
        prev_hands = steps[s_idx - 1][0]["observation"]["farms"][0]["hands"]
        prev_workers = ([prev_farmer] if prev_farmer else []) + [h for h in prev_hands if h]
        all_acts = ([act.get("farmer")] if act.get("farmer") else []) + [h for h in act.get("hands", []) if h]
        for w_idx, w_act in enumerate(all_acts):
            if w_act and w_act[0] == "HARVEST" and w_idx < len(prev_workers) and prev_workers[w_idx]:
                wx, wy = prev_workers[w_idx]
                pt = prev_tiles[wy][wx]
                if isinstance(pt, dict) and pt.get("crop") == "STRAWBERRY":
                    straw_h += pt.get("yield_units", 0)
    return reward, straw_h

def main():
    print("="*80)
    print("PHASE 17: 50-SEED ESCALATION OF DAY-14 CUTOFF (SEEDS 1000-1049)")
    print("="*80)

    base_rewards = []
    cut_rewards = []
    base_straws = []
    cut_straws = []

    for idx, seed in enumerate(SEEDS_50):
        br, bs = run_seed(cl_baseline, seed)
        cr, cs = run_seed(cl_cutoff, seed)
        base_rewards.append(br)
        cut_rewards.append(cr)
        base_straws.append(bs)
        cut_straws.append(cs)
        if (idx + 1) % 10 == 0:
            print(f"Progress: {idx+1}/50 seeds completed... Current Delta Rew: {np.mean(cut_rewards) - np.mean(base_rewards):+,.1f}")

    d_rew = np.array(cut_rewards) - np.array(base_rewards)
    d_straw = np.array(cut_straws) - np.array(base_straws)

    print("\n" + "="*80)
    print("50-SEED MATCHED COMPARISON RESULTS")
    print("="*80)
    print(f"Baseline Reward Mean: ${np.mean(base_rewards):<12,.1f} | Std: ${np.std(base_rewards):<10,.1f}")
    print(f"Cutoff-14 Reward Mean: ${np.mean(cut_rewards):<12,.1f} | Std: ${np.std(cut_rewards):<10,.1f}")
    print(f"Reward Delta (Cut - Base): {np.mean(d_rew):+,.1f} (Median: {np.median(d_rew):+,.1f})")
    
    # Bootstrap CI
    rng = np.random.default_rng(42)
    boot_rew = [np.mean(rng.choice(d_rew, size=len(d_rew), replace=True)) for _ in range(10000)]
    ci_rew = np.percentile(boot_rew, [2.5, 97.5])
    print(f"Reward Delta 95% CI: [{ci_rew[0]:+,.1f}, {ci_rew[1]:+,.1f}]")

    print(f"\nBaseline Straw Mean: {np.mean(base_straws):.2f}")
    print(f"Cutoff-14 Straw Mean: {np.mean(cut_straws):.2f}")
    print(f"Straw Delta: {np.mean(d_straw):+.2f}")
    boot_straw = [np.mean(rng.choice(d_straw, size=len(d_straw), replace=True)) for _ in range(10000)]
    ci_straw = np.percentile(boot_straw, [2.5, 97.5])
    print(f"Straw Delta 95% CI: [{ci_straw[0]:+.2f}, {ci_straw[1]:+.2f}]")
    print("="*80)

    with open("scratch/50seed_cutoff_results.json", "w") as f:
        json.dump({
            "base_rewards": base_rewards,
            "cut_rewards": cut_rewards,
            "base_straws": base_straws,
            "cut_straws": cut_straws,
            "delta_rewards": d_rew.tolist(),
            "delta_straws": d_straw.tolist()
        }, f, indent=2)

if __name__ == "__main__":
    main()
