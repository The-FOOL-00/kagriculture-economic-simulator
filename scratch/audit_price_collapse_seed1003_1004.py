import json
import os
import sys

sys.path.insert(0, os.getcwd())
import kaggle_environments

from candidates.candidate_cl_fert_gated import agent as cl_gated
from candidates.candidate_cl_economic_v1 import agent as cl_baseline

def trace_collapse(seed):
    print(f"\n================ STEP-BY-STEP TRACE OF PRICE COLLAPSE FOR SEED {seed} ================")
    
    # Run Baseline
    env_b = kaggle_environments.make("kaggriculture", configuration={"seed": seed})
    steps_b = env_b.run([cl_baseline, "starter"])
    
    # Run Gated
    env_g = kaggle_environments.make("kaggriculture", configuration={"seed": seed})
    steps_g = env_g.run([cl_gated, "starter"])
    
    for label, steps in [("BASELINE", steps_b), ("GATED", steps_g)]:
        print(f"\n--- {label} (Seed {seed}) ---")
        town_shops_final = steps[-1][0]["observation"]["town"]["unlocked_shops"]
        print(f"Unlocked Town Shops: {town_shops_final}")
        
        # Check strawberry consuming shops
        # SHOPS: BRUNCH_SPOT, ICE_CREAM_SHOP, SMOOTHIE_SHOP, FARMERS_MARKET
        straw_shops = [s for s in town_shops_final if s in ("BRUNCH_SPOT", "ICE_CREAM_SHOP", "SMOOTHIE_SHOP", "FARMERS_MARKET")]
        print(f"Strawberry-consuming shops ({len(straw_shops)}): {straw_shops}")
        
        # Find step where strawberry price hit minimum
        min_p = 999
        min_step = -1
        first_1_step = -1
        
        for s_idx in range(len(steps)):
            obs = steps[s_idx][0]["observation"]
            sp = obs["market"]["prices"]["STRAWBERRY"]
            si = obs["market"]["inventory"]["STRAWBERRY"]
            fi = obs["market"]["inventory"]["FERTILIZER"]
            fp = obs["market"]["prices"]["FERTILIZER"]
            
            if sp < min_p:
                min_p = sp
                min_step = s_idx
            if sp == 1 and first_1_step == -1:
                first_1_step = s_idx
                # Print details of the collapse step!
                prev_obs = steps[s_idx-1][0]["observation"]
                prev_sp = prev_obs["market"]["prices"]["STRAWBERRY"]
                prev_si = prev_obs["market"]["inventory"]["STRAWBERRY"]
                act = steps[s_idx-1][0].get("action") or {}
                m_orders = act.get("market") or []
                print(f"  [COLLAPSE DETECTED] Step {s_idx} (Day {obs['day']}, Hour {obs['hour']}):")
                print(f"    Previous Strawberry Price: ${prev_sp}, Inventory: {prev_si}")
                print(f"    Current Strawberry Price:  ${sp}, Inventory: {si}")
                print(f"    Fertilizer Price: ${fp}, Inventory: {fi}")
                print(f"    Executed Market Orders in Prev Step: {m_orders}")
                
        print(f"  Minimum Strawberry Price: ${min_p} reached at Step {min_step} (First hit $1 at Step {first_1_step})")
        print(f"  Terminal Market Inventory STRAWBERRY: {steps[-1][0]['observation']['market']['inventory']['STRAWBERRY']}")
        print(f"  Terminal Market Inventory FERTILIZER: {steps[-1][0]['observation']['market']['inventory']['FERTILIZER']}")

if __name__ == "__main__":
    trace_collapse(1003)
    trace_collapse(1004)
