import sys
import os
import json
import random
import numpy as np
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor

PROJECT_ROOT = os.path.abspath(".")
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import kaggle_environments
import kaggle_environments.envs.kaggriculture.kaggriculture as kg_engine

from candidates.candidate_cl_economic_v1 import agent as cl_baseline
from candidates.candidate_cl_fert_gated import agent as cl_gated

SEEDS_50 = list(range(1000, 1050))

def trace_single_seed_causal_chain(seed):
    # Run Baseline
    env_b = kaggle_environments.make("kaggriculture", configuration={"seed": seed})
    steps_b = env_b.run([cl_baseline, "starter"])
    
    # Run Gated M1
    env_g = kaggle_environments.make("kaggriculture", configuration={"seed": seed})
    steps_g = env_g.run([cl_gated, "starter"])
    
    n_steps = len(steps_b)
    
    first_action_div = -1
    first_tile_div = -1
    first_empty_count_div = -1
    first_weeds_div = -1
    first_shop_div_day = -1
    first_mkt_inv_div = -1
    first_mkt_pr_div = -1
    first_rew_div = -1
    
    # Track empty tiles at hour 23 of each day
    empty_tiles_b = {}
    empty_tiles_g = {}
    
    # Weeds spawned on each day
    weeds_spawned_b = {}
    weeds_spawned_g = {}
    
    for s in range(n_steps):
        obs_b = steps_b[s][0]["observation"]
        obs_g = steps_g[s][0]["observation"]
        
        act_b = steps_b[s][0].get("action")
        act_g = steps_g[s][0].get("action")
        
        day = obs_b["day"]
        hour = obs_b["hour"]
        
        # 1. Action divergence
        if act_b != act_g and first_action_div == -1:
            first_action_div = s
            
        # 2. Tile state divergence
        tb = obs_b["farms"][0]["tiles"]
        tg = obs_g["farms"][0]["tiles"]
        if tb != tg and first_tile_div == -1:
            first_tile_div = s
            
        # Count empty tiles at hour 23 (before _end_of_day)
        if hour == 23:
            eb = sum(row.count(None) for row in tb)
            eg = sum(row.count(None) for row in tg)
            empty_tiles_b[day] = eb
            empty_tiles_g[day] = eg
            if eb != eg and first_empty_count_div == -1:
                first_empty_count_div = s
                
        # 3. Market inventory divergence
        mb = obs_b.get("market") or {}
        mg = obs_g.get("market") or {}
        ib = mb.get("inventory") or {}
        ig = mg.get("inventory") or {}
        if ib != ig and first_mkt_inv_div == -1:
            first_mkt_inv_div = s
            
        # 4. Market price divergence
        pb = mb.get("prices") or {}
        pg = mg.get("prices") or {}
        if pb != pg and first_mkt_pr_div == -1:
            first_mkt_pr_div = s
            
        # 5. Reward / Money divergence
        money_b = obs_b["farms"][0]["money"]
        money_g = obs_g["farms"][0]["money"]
        if money_b != money_g and first_rew_div == -1:
            first_rew_div = s

    # Compare shop sequences day-by-day
    for d in range(1, 30):
        s_idx = min(d * 24, n_steps - 1)
        sb = steps_b[s_idx][0]["observation"]["town"]["unlocked_shops"]
        sg = steps_g[s_idx][0]["observation"]["town"]["unlocked_shops"]
        if sb != sg and first_shop_div_day == -1:
            first_shop_div_day = d
            
    final_shops_b = steps_b[-1][0]["observation"]["town"]["unlocked_shops"]
    final_shops_g = steps_g[-1][0]["observation"]["town"]["unlocked_shops"]
    
    straw_shops_b = sum(1 for x in final_shops_b if x in ("BRUNCH_SPOT", "ICE_CREAM_SHOP", "SMOOTHIE_SHOP", "FARMERS_MARKET"))
    straw_shops_g = sum(1 for x in final_shops_g if x in ("BRUNCH_SPOT", "ICE_CREAM_SHOP", "SMOOTHIE_SHOP", "FARMERS_MARKET"))
    
    milk_shops_b = sum(1 for x in final_shops_b if x in ("PIZZA_SHOP", "ICE_CREAM_SHOP", "SMOOTHIE_SHOP"))
    milk_shops_g = sum(1 for x in final_shops_g if x in ("PIZZA_SHOP", "ICE_CREAM_SHOP", "SMOOTHIE_SHOP"))
    
    rew_b = float(steps_b[-1][0]["reward"])
    rew_g = float(steps_g[-1][0]["reward"])
    
    return {
        "seed": seed,
        "first_action_div": first_action_div,
        "first_tile_div": first_tile_div,
        "first_empty_count_div": first_empty_count_div,
        "first_shop_div_day": first_shop_div_day,
        "first_mkt_inv_div": first_mkt_inv_div,
        "first_mkt_pr_div": first_mkt_pr_div,
        "first_rew_div": first_rew_div,
        "empty_d8_b": empty_tiles_b.get(8, 0),
        "empty_d8_g": empty_tiles_g.get(8, 0),
        "delta_empty_d8": empty_tiles_g.get(8, 0) - empty_tiles_b.get(8, 0),
        "straw_shops_b": straw_shops_b,
        "straw_shops_g": straw_shops_g,
        "delta_straw_shops": straw_shops_g - straw_shops_b,
        "milk_shops_b": milk_shops_b,
        "milk_shops_g": milk_shops_g,
        "delta_milk_shops": milk_shops_g - milk_shops_b,
        "rew_b": rew_b,
        "rew_g": rew_g,
        "delta_reward": rew_g - rew_b
    }

def main():
    print("Tracing 50-Seed Causal Chain (Seeds 1000-1049)...")
    with ProcessPoolExecutor(max_workers=8) as executor:
        results = list(executor.map(trace_single_seed_causal_chain, SEEDS_50))
        
    with open("scratch/causal_chain_50seeds_results.json", "w") as f:
        json.dump(results, f, indent=2)
        
    print("Completed. Running summary statistics...")
    
    # Compute summary
    action_divs = [r["first_action_div"] for r in results]
    tile_divs = [r["first_tile_div"] for r in results]
    empty_divs = [r["first_empty_count_div"] for r in results]
    shop_divs = [r["first_shop_div_day"] for r in results if r["first_shop_div_day"] != -1]
    shop_div_count = len(shop_divs)
    
    delta_empty_d8 = [r["delta_empty_d8"] for r in results]
    delta_straw_shops = [r["delta_straw_shops"] for r in results]
    delta_milk_shops = [r["delta_milk_shops"] for r in results]
    delta_rews = [r["delta_reward"] for r in results]
    
    print("\n" + "=" * 80)
    print("50-SEED CAUSAL CHAIN TIMELINE")
    print("=" * 80)
    print(f"Total Seeds Evaluated:           {len(results)}")
    print(f"First Action Divergence:         Mean Step {np.mean(action_divs):.1f} (Min {np.min(action_divs)}, Max {np.max(action_divs)})")
    print(f"First Tile State Divergence:     Mean Step {np.mean(tile_divs):.1f} (Min {np.min(tile_divs)}, Max {np.max(tile_divs)})")
    print(f"First Empty Count Divergence:    Mean Step {np.mean(empty_divs):.1f} (Day {np.mean(empty_divs)/24:.1f})")
    print(f"Seeds with Divergent Town Shops: {shop_div_count} / {len(results)} ({shop_div_count/len(results)*100:.1f}%)")
    if shop_divs:
        print(f"First Town Shop Divergence Day:  Mean Day {np.mean(shop_divs):.1f} (Min Day {np.min(shop_divs)}, Max Day {np.max(shop_divs)})")
        
    print("\n" + "=" * 80)
    print("CORRELATION ANALYSIS ACROSS 50 SEEDS")
    print("=" * 80)
    
    # Correlation matrix
    corr_empty_straw = np.corrcoef(delta_empty_d8, delta_straw_shops)[0, 1]
    corr_empty_milk = np.corrcoef(delta_empty_d8, delta_milk_shops)[0, 1]
    corr_empty_rew = np.corrcoef(delta_empty_d8, delta_rews)[0, 1]
    corr_straw_rew = np.corrcoef(delta_straw_shops, delta_rews)[0, 1]
    corr_milk_rew = np.corrcoef(delta_milk_shops, delta_rews)[0, 1]
    
    print(f"Corr(Empty Tiles Diff Day 8, Delta Strawberry Shops): {corr_empty_straw:>+7.3f}")
    print(f"Corr(Empty Tiles Diff Day 8, Delta Milk Shops):       {corr_empty_milk:>+7.3f}")
    print(f"Corr(Empty Tiles Diff Day 8, Delta Reward):           {corr_empty_rew:>+7.3f}")
    print(f"Corr(Delta Strawberry Shops, Delta Reward):           {corr_straw_rew:>+7.3f}")
    print(f"Corr(Delta Milk Shops, Delta Reward):                 {corr_milk_rew:>+7.3f}")

if __name__ == "__main__":
    main()
