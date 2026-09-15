import json
import os
import sys
import random
import numpy as np

sys.path.insert(0, os.getcwd())
import kaggle_environments

from candidates.candidate_cl_economic_v1 import agent as cl_baseline
from candidates.candidate_cl_fert_gated import agent as cl_gated
from candidates.candidate_cl_pair_m1_m3 import agent as cl_pair

SEEDS_10 = list(range(1000, 1010))

def trace_rng_calls(seed):
    # Simulate the exact RNG state progression as done by kg_env_dump.py
    # Day d: seed_val = (seed * 1_000_003) ^ day
    # rng = random.Random(seed_val)
    # _spawn_weeds called for farm 0, then farm 1
    # then if (day+1) % 3 == 0: rng.choice(sorted(remaining))
    pass

def run_counterfactual_fixed_shops():
    print("================================================================================")
    print("PHASE 5: DETERMINISTIC TOWN-SHOP COUNTERFACTUAL AUDIT (SEEDS 1000-1009)")
    print("================================================================================")
    
    # Step 1: Run Baseline and record the exact town shops unlocked on every day
    baseline_shops_by_seed = {}
    baseline_rewards = {}
    gated_rewards_standard = {}
    pair_rewards_standard = {}
    
    for seed in SEEDS_10:
        env_b = kaggle_environments.make("kaggriculture", configuration={"seed": seed})
        steps_b = env_b.run([cl_baseline, "starter"])
        shops_schedule = {}
        for s in steps_b:
            obs = s[0]["observation"]
            d = obs["day"]
            shops_schedule[d] = list(obs["town"]["unlocked_shops"])
        baseline_shops_by_seed[seed] = shops_schedule
        baseline_rewards[seed] = float(steps_b[-1][0]["reward"])
        
        # Standard Gated
        env_g = kaggle_environments.make("kaggriculture", configuration={"seed": seed})
        steps_g = env_g.run([cl_gated, "starter"])
        gated_rewards_standard[seed] = float(steps_g[-1][0]["reward"])
        
        # Standard Pair
        env_p = kaggle_environments.make("kaggriculture", configuration={"seed": seed})
        steps_p = env_p.run([cl_pair, "starter"])
        pair_rewards_standard[seed] = float(steps_p[-1][0]["reward"])
        
    print("Baseline town-shop schedules captured across 10 seeds.")
    
    # Step 2: Run Gated with forced baseline town-shop schedule
    # We step the environment turn by turn and force obs0.town['unlocked_shops'] = baseline_shops[day]
    gated_rewards_fixed = {}
    pair_rewards_fixed = {}
    
    for seed in SEEDS_10:
        base_schedule = baseline_shops_by_seed[seed]
        
        # Run Gated with Fixed Shops
        env = kaggle_environments.make("kaggriculture", configuration={"seed": seed})
        env.reset()
        
        for step_i in range(720):
            day = env.steps[-1][0]["observation"]["day"]
            # Override town shops in env state before agents act and before town_consume
            forced_list = list(base_schedule.get(day, []))
            for p in range(len(env.steps[-1])):
                env.steps[-1][p]["observation"]["town"]["unlocked_shops"] = list(forced_list)
                
            # Get agent actions
            act0 = cl_gated(env.steps[-1][0]["observation"], env.configuration)
            # starter agent for player 1
            # We can let env handle starter or call default
            # In kaggle_environments step accepts actions
            # But wait, env.step takes [act0, act1]
            pass

    print("Benchmarking fixed-shop deterministic test via custom environment runner...")

if __name__ == "__main__":
    run_counterfactual_fixed_shops()
