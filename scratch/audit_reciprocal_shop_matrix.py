import sys
import os
import json
import random
import numpy as np
from concurrent.futures import ProcessPoolExecutor

PROJECT_ROOT = os.path.abspath(".")
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import kaggle_environments
import kaggle_environments.envs.kaggriculture.kaggriculture as kg_engine

from candidates.candidate_cl_economic_v1 import agent as cl_baseline
from candidates.candidate_cl_fert_gated import agent as cl_gated

SEEDS_RECIPROCAL = list(range(1000, 1020)) # 20 seeds for high statistical power

def run_match_with_forced_shops(agent_fn, seed, forced_shops=None):
    # If forced_shops is None, run standard natural engine
    if forced_shops is None:
        env = kaggle_environments.make("kaggriculture", configuration={"seed": seed})
        steps = env.run([agent_fn, "starter"])
        rew = float(steps[-1][0]["reward"])
        shops = list(steps[-1][0]["observation"]["town"]["unlocked_shops"])
        return rew, shops

    # Otherwise monkeypatch _end_of_day for this run
    orig_end_of_day = kg_engine._end_of_day
    
    # Pre-map day -> shop to unlock
    # Town shops unlock on days 2, 5, 8, 11, 14, 17, 20, 23, 26, 29 (day % 3 == 2, next_day % 3 == 0)
    # forced_shops is a list of up to 10 shops
    shop_schedule = {}
    shop_idx = 0
    for d in range(30):
        if (d + 1) % 3 == 0 and shop_idx < len(forced_shops):
            shop_schedule[d] = forced_shops[shop_idx]
            shop_idx += 1
            
    def custom_end_of_day(state, env, day):
        obs0 = state[0].observation
        cfg = env.configuration
        board_size = int(kg_engine.get(cfg, "boardSize", 10))
        turns_per_day = max(1, int(kg_engine.get(cfg, "turnsPerDay", 24)))
        weed_chance = float(kg_engine.get(cfg, "weedSpawnChance", 0.005))
        shed_cap = int(kg_engine.get(cfg, "shedCapacity", 100))
        shop_interval = max(1, int(kg_engine.get(cfg, "townShopUnlockInterval", 3)))

        seed_val = env.info.get("seed", 0)
        rng = random.Random((seed_val * 1_000_003) ^ day)

        for player_id, farm in enumerate(obs0.farms):
            private = state[player_id].observation.private
            kg_engine._daily_refresh_plants(farm, day, turns_per_day)
            kg_engine._daily_refresh_animals(farm, day)
            kg_engine._spawn_weeds(farm, board_size, weed_chance, rng)
            kg_engine._drop_inventories_to_shed(private, shed_cap)
            farm["farmer"] = list(kg_engine._default_spawn(board_size))
            farm["hands"] = []
            farm["hires_today"] = 0
            private["inventories"] = [{}]

        next_day = day + 1
        town = obs0.town
        if next_day > 0 and next_day % shop_interval == 0:
            if day in shop_schedule and len(town["unlocked_shops"]) < kg_engine.MAX_SHOP_INSTANCES:
                town["unlocked_shops"].append(shop_schedule[day])

    kg_engine._end_of_day = custom_end_of_day
    try:
        env = kaggle_environments.make("kaggriculture", configuration={"seed": seed})
        steps = env.run([agent_fn, "starter"])
        rew = float(steps[-1][0]["reward"])
        shops = list(steps[-1][0]["observation"]["town"]["unlocked_shops"])
        return rew, shops
    finally:
        kg_engine._end_of_day = orig_end_of_day

def evaluate_seed_reciprocal(seed):
    # 1. Natural Baseline (Arm A)
    rew_a, shops_a = run_match_with_forced_shops(cl_baseline, seed, None)
    
    # 2. Natural M1 (Arm B)
    rew_b, shops_b = run_match_with_forced_shops(cl_gated, seed, None)
    
    # 3. Baseline under Baseline shops (Arm C) -> should match A closely or exactly
    rew_c, _ = run_match_with_forced_shops(cl_baseline, seed, shops_a)
    
    # 4. M1 under Baseline shops (Arm D)
    rew_d, _ = run_match_with_forced_shops(cl_gated, seed, shops_a)
    
    # 5. Baseline under M1 shops (Arm E)
    rew_e, _ = run_match_with_forced_shops(cl_baseline, seed, shops_b)
    
    # 6. M1 under M1 shops (Arm F)
    rew_f, _ = run_match_with_forced_shops(cl_gated, seed, shops_b)
    
    return {
        "seed": seed,
        "A": rew_a,
        "B": rew_b,
        "C": rew_c,
        "D": rew_d,
        "E": rew_e,
        "F": rew_f,
        "diff_shops": (shops_a != shops_b),
        "B_minus_A": rew_b - rew_a,
        "D_minus_C": rew_d - rew_c, # Strategy effect holding shops to Baseline stream
        "F_minus_E": rew_f - rew_e, # Strategy effect holding shops to M1 stream
        "shops_a": shops_a,
        "shops_b": shops_b
    }

def main():
    print("Running Reciprocal Shop Counterfactual Matrix across Seeds 1000-1019...")
    with ProcessPoolExecutor(max_workers=8) as executor:
        results = list(executor.map(evaluate_seed_reciprocal, SEEDS_RECIPROCAL))
        
    with open("scratch/reciprocal_shop_matrix_results.json", "w") as f:
        json.dump(results, f, indent=2)
        
    print("=" * 80)
    print("RECIPROCAL SHOP-STREAM COUNTERFACTUAL RESULTS (N=20)")
    print("=" * 80)
    
    b_minus_a = [r["B_minus_A"] for r in results]
    d_minus_c = [r["D_minus_C"] for r in results]
    f_minus_e = [r["F_minus_E"] for r in results]
    
    print(f"{'Seed':<6} | {'Natural (B-A)':<14} | {'Base Shops (D-C)':<16} | {'M1 Shops (F-E)':<16} | {'Shops Differ?'}")
    print("-" * 75)
    for r in results:
        print(f"{r['seed']:<6} | ${r['B_minus_A']:>+12,.1f} | ${r['D_minus_C']:>+14,.1f} | ${r['F_minus_E']:>+14,.1f} | {r['diff_shops']}")
        
    print("-" * 75)
    print(f"{'MEAN':<6} | ${np.mean(b_minus_a):>+12,.1f} | ${np.mean(d_minus_c):>+14,.1f} | ${np.mean(f_minus_e):>+14,.1f} | {sum(r['diff_shops'] for r in results)}/{len(results)}")
    print(f"{'WIN%':<6} | {np.sum(np.array(b_minus_a)>0)/len(results)*100:>11.1f}% | {np.sum(np.array(d_minus_c)>0)/len(results)*100:>13.1f}% | {np.sum(np.array(f_minus_e)>0)/len(results)*100:>13.1f}% |")

if __name__ == "__main__":
    main()
