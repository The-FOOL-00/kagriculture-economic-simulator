import json
import os
import sys
import copy
import random
import numpy as np

sys.path.insert(0, os.getcwd())
import kaggle_environments
import kaggle_environments.envs.kaggriculture.kaggriculture as kg_engine

from candidates.candidate_cl_economic_v1 import agent as cl_baseline
from candidates.candidate_cl_fert_gated import agent as cl_gated
from candidates.candidate_cl_pair_m1_m3 import agent as cl_pair

SEEDS = list(range(1000, 1010))

def trace_prng_divergence_details():
    print("================================================================================")
    print("PHASE 4 & 5: EXACT ENGINE PRNG TRACE & DIVERGENCE ANALYSIS")
    print("================================================================================")
    
    # We will trace step-by-step for each seed:
    # 1. When did tile counts first diverge?
    # 2. When did _spawn_weeds call counts diverge?
    # 3. When did the first town-shop draw diverge?
    
    divergence_records = []
    
    for seed in SEEDS:
        env_b = kaggle_environments.make("kaggriculture", configuration={"seed": seed})
        steps_b = env_b.run([cl_baseline, "starter"])
        
        env_g = kaggle_environments.make("kaggriculture", configuration={"seed": seed})
        steps_g = env_g.run([cl_gated, "starter"])
        
        # Compare town shop sequence
        b_shops = steps_b[-1][0]["observation"]["town"]["unlocked_shops"]
        g_shops = steps_g[-1][0]["observation"]["town"]["unlocked_shops"]
        
        # Check first divergence day for town shops
        first_shop_div_day = -1
        first_shop_b = None
        first_shop_g = None
        
        # Check day-by-day shops
        for d in range(1, 30):
            step_idx = d * 24
            if step_idx < len(steps_b):
                sb = steps_b[step_idx][0]["observation"]["town"]["unlocked_shops"]
                sg = steps_g[step_idx][0]["observation"]["town"]["unlocked_shops"]
                if sb != sg and first_shop_div_day == -1:
                    first_shop_div_day = d
                    first_shop_b = sb[-1] if sb else None
                    first_shop_g = sg[-1] if sg else None
                    
        # Check first tile divergence step
        first_tile_div_step = -1
        for s in range(len(steps_b)):
            tb = steps_b[s][0]["observation"]["farms"][0]["tiles"]
            tg = steps_g[s][0]["observation"]["farms"][0]["tiles"]
            if tb != tg and first_tile_div_step == -1:
                first_tile_div_step = s
                
        # Count strawberry shops
        b_straw_shops = sum(1 for s in b_shops if s in ("BRUNCH_SPOT", "ICE_CREAM_SHOP", "SMOOTHIE_SHOP", "FARMERS_MARKET"))
        g_straw_shops = sum(1 for s in g_shops if s in ("BRUNCH_SPOT", "ICE_CREAM_SHOP", "SMOOTHIE_SHOP", "FARMERS_MARKET"))
        
        # Count milk shops
        b_milk_shops = sum(1 for s in b_shops if s in ("PIZZA_SHOP", "ICE_CREAM_SHOP", "SMOOTHIE_SHOP"))
        g_milk_shops = sum(1 for s in g_shops if s in ("PIZZA_SHOP", "ICE_CREAM_SHOP", "SMOOTHIE_SHOP"))
        
        # Count wool shops
        b_wool_shops = sum(1 for s in b_shops if s == "YARN_STORE")
        g_wool_shops = sum(1 for s in g_shops if s == "YARN_STORE")
        
        rew_b = float(steps_b[-1][0]["reward"])
        rew_g = float(steps_g[-1][0]["reward"])
        delta_rew = rew_g - rew_b
        
        rec = {
            "seed": seed,
            "reward_base": rew_b,
            "reward_gated": rew_g,
            "delta_reward": delta_rew,
            "first_tile_div_step": first_tile_div_step,
            "first_shop_div_day": first_shop_div_day,
            "first_shop_b": first_shop_b,
            "first_shop_g": first_shop_g,
            "b_straw_shops": b_straw_shops,
            "g_straw_shops": g_straw_shops,
            "b_milk_shops": b_milk_shops,
            "g_milk_shops": g_milk_shops,
            "b_wool_shops": b_wool_shops,
            "g_wool_shops": g_wool_shops,
            "b_shops": b_shops,
            "g_shops": g_shops
        }
        divergence_records.append(rec)
        
        print(f"Seed {seed}:")
        print(f"  Delta Reward: ${delta_rew:>+9,.1f}")
        print(f"  First Tile Divergence: Step {first_tile_div_step} (Day {first_tile_div_step//24})")
        print(f"  First Shop Divergence: Day {first_shop_div_day} (Base: {first_shop_b} vs Gated: {first_shop_g})")
        print(f"  Strawberry Shops: Base {b_straw_shops} vs Gated {g_straw_shops} (Delta {g_straw_shops - b_straw_shops:>+2})")
        print(f"  Milk Shops:       Base {b_milk_shops} vs Gated {g_milk_shops} (Delta {g_milk_shops - b_milk_shops:>+2})")
        print(f"  Wool Shops:       Base {b_wool_shops} vs Gated {g_wool_shops} (Delta {g_wool_shops - b_wool_shops:>+2})")

    return divergence_records

def run_decoupled_shop_counterfactual():
    print("\n" + "=" * 80)
    print("RUNNING DETERMINISTIC COUNTERFACTUAL: DECOUPLED TOWN-SHOP PRNG STREAM")
    print("=" * 80)
    
    # Save original _end_of_day
    orig_end_of_day = kg_engine._end_of_day
    
    def decoupled_end_of_day(state, env, day):
        obs0 = state[0].observation
        cfg = env.configuration
        board_size = int(kg_engine.get(cfg, "boardSize", 10))
        turns_per_day = max(1, int(kg_engine.get(cfg, "turnsPerDay", 24)))
        weed_chance = float(kg_engine.get(cfg, "weedSpawnChance", 0.005))
        shed_cap = int(kg_engine.get(cfg, "shedCapacity", 100))
        shop_interval = max(1, int(kg_engine.get(cfg, "townShopUnlockInterval", 3)))

        seed = env.info.get("seed", 0)
        # Standard RNG for weeds
        rng = random.Random((seed * 1_000_003) ^ day)

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
            remaining = [s for s in kg_engine.SHOPS if s not in town["unlocked_shops"]]
            if remaining:
                # DEDICATED INDEPENDENT PRNG STREAM FOR TOWN SHOPS:
                # Keyed strictly off (seed, next_day), completely independent of empty tiles!
                town_rng = random.Random((seed * 777_777) ^ next_day)
                choice = town_rng.choice(sorted(remaining))
                town["unlocked_shops"].append(choice)

    # Monkeypatch engine
    kg_engine._end_of_day = decoupled_end_of_day
    
    counterfactual_results = []
    
    try:
        for seed in SEEDS:
            env_b = kaggle_environments.make("kaggriculture", configuration={"seed": seed})
            steps_b = env_b.run([cl_baseline, "starter"])
            rew_b = float(steps_b[-1][0]["reward"])
            shops_b = steps_b[-1][0]["observation"]["town"]["unlocked_shops"]
            
            env_g = kaggle_environments.make("kaggriculture", configuration={"seed": seed})
            steps_g = env_g.run([cl_gated, "starter"])
            rew_g = float(steps_g[-1][0]["reward"])
            shops_g = steps_g[-1][0]["observation"]["town"]["unlocked_shops"]
            
            delta_rew = rew_g - rew_b
            shops_identical = (shops_b == shops_g)
            
            print(f"Seed {seed} (RNG-Decoupled): Base=${rew_b:>9,.1f} | Gated=${rew_g:>9,.1f} | Delta=${delta_rew:>+9,.1f} | Shops Identical: {shops_identical}")
            
            counterfactual_results.append({
                "seed": seed,
                "rew_base": rew_b,
                "rew_gated": rew_g,
                "delta_rew": delta_rew,
                "shops_identical": shops_identical
            })
    finally:
        # Restore original
        kg_engine._end_of_day = orig_end_of_day
        
    mean_orig_delta = -5476.20
    mean_decoupled_delta = np.mean([r["delta_rew"] for r in counterfactual_results])
    
    print("\n" + "=" * 80)
    print("DETERMINISTIC COUNTERFACTUAL RESULTS (10-SEED MEANS):")
    print(f"  Original Delta Reward (Coupled RNG):   ${mean_orig_delta:>+9,.2f}")
    print(f"  RNG-Controlled Delta Reward (Decoupled): ${mean_decoupled_delta:>+9,.2f}")
    print(f"  Difference (RNG-Induced Artifact):      ${mean_decoupled_delta - mean_orig_delta:>+9,.2f}")
    print("=" * 80)

if __name__ == "__main__":
    trace_prng_divergence_details()
    run_decoupled_shop_counterfactual()
