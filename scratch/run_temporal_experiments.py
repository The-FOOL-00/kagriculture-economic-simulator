"""
Large-Scale 100-Seed Matched Experimentation Suite for Temporal Production Waves
Evaluates:
  Arm A: Baseline CL-Economic-V1
  Arm B: Fixed Early Strawberry Control
  Arm C: Fixed Day-8 Sheep Control
  Arm D: Fixed Strawberry + Sheep Control
  Arm E: State-Derived Temporal V1
  Arm F: Integrated Temporal V2
Across 100 Matched Seeds (1000-1099 vs Starter).
Tracks reward distribution, commodity sales, labor efficiency, and saves JSON results.
"""

import sys
import os
import time
import json
import numpy as np
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor, as_completed

PROJECT_ROOT = os.path.abspath(".")
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import kaggle_environments

SEEDS = list(range(1000, 1100))

ARMS = {
    "ARM_A": ("CL-Economic-V1", "candidates.candidate_cl_economic_v1"),
    "ARM_B": ("Fixed-Straw-Control", "candidates.candidate_cl_fixed_straw_control"),
    "ARM_C": ("Fixed-Sheep-Control", "candidates.candidate_cl_fixed_sheep_control"),
    "ARM_D": ("Fixed-Straw-Sheep", "candidates.candidate_cl_fixed_straw_sheep_control"),
    "ARM_E": ("CL-Temporal-V1", "candidates.candidate_cl_temporal_v1"),
    "ARM_F": ("CL-Temporal-V2", "candidates.candidate_cl_temporal_v2"),
}

def _eval_single_match(item):
    arm_key, arm_name, module_name, seed = item
    
    # Import agent function dynamically inside worker process
    mod = __import__(module_name, fromlist=["agent_fn", "agent"])
    if hasattr(mod, "agent_fn"):
        agent = mod.agent_fn
    elif hasattr(mod, "agent"):
        agent = mod.agent
    else:
        raise AttributeError(f"No agent or agent_fn in {module_name}")
        
    cfg = {"episodeSteps": 720, "seed": seed}
    env = kaggle_environments.make("kaggriculture", configuration=cfg)
    
    try:
        env.run([agent, "starter"])
        steps = env.steps
        total_steps = len(steps)
        p = 0
        
        final_reward = float(steps[-1][p].get("reward") or 0.0)
        final_farm = steps[-1][p]["observation"]["farms"][p]
        final_money = float(final_farm["money"])
        
        # Track sales and actions
        units_sold = defaultdict(int)
        moves = 0
        prod = 0
        idle = 0
        
        for s_idx in range(1, total_steps):
            act = steps[s_idx][p].get("action") or {}
            market_orders = act.get("market") or []
            for o in market_orders:
                if o and isinstance(o, list) and o[0] == "SELL":
                    item_name = o[1]
                    qty = int(o[2]) if len(o) > 2 else 1
                    units_sold[item_name] += qty
                    
            farmer_act = act.get("farmer") or ["PASS"]
            hands_acts = act.get("hands") or []
            for w_act in [farmer_act] + hands_acts:
                cmd = w_act[0] if isinstance(w_act, list) and len(w_act) > 0 else (w_act if isinstance(w_act, str) else "PASS")
                if cmd in ("NORTH", "SOUTH", "EAST", "WEST"):
                    moves += 1
                elif cmd == "PASS":
                    idle += 1
                else:
                    prod += 1
                    
        return {
            "arm_key": arm_key,
            "arm_name": arm_name,
            "seed": seed,
            "reward": final_reward,
            "money": final_money,
            "units_sold": dict(units_sold),
            "moves": moves,
            "prod": prod,
            "idle": idle,
            "error": None
        }
    except Exception as e:
        return {
            "arm_key": arm_key,
            "arm_name": arm_name,
            "seed": seed,
            "reward": 0.0,
            "money": 0.0,
            "units_sold": {},
            "moves": 0,
            "prod": 0,
            "idle": 0,
            "error": str(e)
        }

def run_all_screening(seeds=SEEDS, max_workers=10):
    print("=" * 95)
    print("100-SEED MATCHED SCREENING TOURNAMENT ACROSS TEMPORAL ARMS A - F")
    print(f"Total Seeds: {len(seeds)} (Seeds {seeds[0]}-{seeds[-1]}) | Parallel Workers: {max_workers}")
    print("=" * 95)
    
    tasks = []
    for arm_key, (arm_name, mod_name) in ARMS.items():
        for s in seeds:
            tasks.append((arm_key, arm_name, mod_name, s))
            
    total_matches = len(tasks)
    print(f"Total matches to run: {total_matches} ({len(ARMS)} arms x {len(seeds)} seeds)")
    
    results_by_arm = defaultdict(list)
    t0 = time.time()
    completed = 0
    
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(_eval_single_match, t) for t in tasks]
        for f in as_completed(futures):
            res = f.result()
            results_by_arm[res["arm_key"]].append(res)
            completed += 1
            if completed % 50 == 0 or completed == total_matches:
                elapsed = time.time() - t0
                pct = completed / total_matches * 100
                rate = completed / elapsed
                print(f"Progress: {completed}/{total_matches} matches ({pct:.1f}%) | Elapsed: {elapsed:.1f}s | Rate: {rate:.2f} m/s")
                
    elapsed_total = time.time() - t0
    print(f"\nTournament completed in {elapsed_total:.1f}s.")
    
    # Process and summarize statistics
    summary = {}
    print("\n" + "=" * 110)
    print(f"{'ARM':<6} | {'NAME':<24} | {'MEAN REWARD':<15} | {'STD DEV':<12} | {'MEDIAN':<12} | {'STRAW':<8} | {'WOOL':<8} | {'MILK':<8} | {'WHEAT':<8}")
    print("-" * 110)
    
    for arm_key in sorted(ARMS.keys()):
        arm_name = ARMS[arm_key][0]
        data = results_by_arm[arm_key]
        rewards = [d["reward"] for d in data if d["error"] is None]
        mean_r = float(np.mean(rewards))
        std_r = float(np.std(rewards))
        med_r = float(np.median(rewards))
        
        straw_u = float(np.mean([d["units_sold"].get("STRAWBERRY", 0) for d in data]))
        wool_u = float(np.mean([d["units_sold"].get("WOOL", 0) for d in data]))
        milk_u = float(np.mean([d["units_sold"].get("MILK", 0) for d in data]))
        wheat_u = float(np.mean([d["units_sold"].get("WHEAT", 0) for d in data]))
        melon_u = float(np.mean([d["units_sold"].get("MELON", 0) for d in data]))
        fert_u = float(np.mean([d["units_sold"].get("FERTILIZER", 0) for d in data]))
        moves = float(np.mean([d["moves"] for d in data]))
        prod = float(np.mean([d["prod"] for d in data]))
        
        summary[arm_key] = {
            "name": arm_name,
            "mean_reward": mean_r,
            "std_reward": std_r,
            "median_reward": med_r,
            "min_reward": float(np.min(rewards)),
            "max_reward": float(np.max(rewards)),
            "straw_units": straw_u,
            "wool_units": wool_u,
            "milk_units": milk_u,
            "wheat_units": wheat_u,
            "melon_units": melon_u,
            "fert_units": fert_u,
            "moves": moves,
            "productive": prod,
            "raw_rewards": rewards
        }
        
        print(f"{arm_key:<6} | {arm_name:<24} | ${mean_r:13,.2f} | +/-${std_r:9,.2f} | ${med_r:10,.2f} | {straw_u:6.1f} | {wool_u:6.1f} | {milk_u:6.1f} | {wheat_u:6.1f}")
        
    print("=" * 110)
    
    with open("scratch/temporal_screening_100seeds_results.json", "w") as f:
        json.dump(summary, f, indent=2)
    print("\nSaved full summary to scratch/temporal_screening_100seeds_results.json")
    return summary

if __name__ == "__main__":
    run_all_screening()
