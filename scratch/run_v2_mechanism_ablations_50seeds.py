import json
import os
import sys
import numpy as np
from concurrent.futures import ProcessPoolExecutor

PROJECT_ROOT = os.path.abspath(".")
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import kaggle_environments

from candidates.candidate_cl_fert_gated import agent as m1_baseline
from candidates.candidate_cl_m1_sheep_timing import agent as m1_sheep
from candidates.candidate_cl_m1_pocket_batching import agent as m1_batch
from candidates.candidate_cl_m1_wheat_expansion import agent as m1_wheat

SEEDS_50 = list(range(1000, 1050))

def run_single_ablation_match(args):
    arm_name, seed = args
    if arm_name == "M1_Baseline": agent_fn = m1_baseline
    elif arm_name == "M1_SheepTiming": agent_fn = m1_sheep
    elif arm_name == "M1_PocketBatching": agent_fn = m1_batch
    elif arm_name == "M1_WheatExpansion": agent_fn = m1_wheat
    else: raise ValueError(f"Unknown arm {arm_name}")
    
    env = kaggle_environments.make("kaggriculture", configuration={"seed": seed})
    steps = env.run([agent_fn, "starter"])
    
    rev_by_item = {
        "STRAWBERRY": 0.0, "MELON": 0.0, "MILK": 0.0, "WOOL": 0.0,
        "WHEAT": 0.0, "FERTILIZER": 0.0, "EGG": 0.0
    }
    qty_sold = {k: 0 for k in rev_by_item}
    
    moves = 0
    passes = 0
    
    for s_idx in range(1, len(steps)):
        prev_obs = steps[s_idx-1][0]["observation"]
        act = steps[s_idx][0].get("action") or {}
        prev_prices = (prev_obs.get("market") or {}).get("prices") or {}
        
        all_wacts = [act.get("farmer", [])] + act.get("hands", [])
        for wact in all_wacts:
            if not wact: continue
            c = wact[0]
            if c in ("NORTH", "SOUTH", "EAST", "WEST"): moves += 1
            elif c == "PASS": passes += 1
            
        for order in act.get("market") or []:
            if not order: continue
            cmd = order[0]
            item = order[1] if len(order) > 1 else None
            qty = int(order[2]) if len(order) > 2 else 1
            p = float(prev_prices.get(item, 0.0))
            if cmd == "SELL" and item in rev_by_item:
                rev_by_item[item] += qty * p
                qty_sold[item] += qty
                
    terminal_reward = float(steps[-1][0]["reward"])
    
    return {
        "arm": arm_name,
        "seed": seed,
        "reward": terminal_reward,
        "rev_by_item": rev_by_item,
        "qty_sold": qty_sold,
        "moves": moves,
        "passes": passes
    }

def main():
    print("Launching Single-Mechanism Ablation Suite (Seeds 1000-1049, N=50 seeds x 4 arms = 200 matches)...")
    tasks = []
    arms = ["M1_Baseline", "M1_SheepTiming", "M1_PocketBatching", "M1_WheatExpansion"]
    for a in arms:
        for s in SEEDS_50:
            tasks.append((a, s))
            
    results = {a: {} for a in arms}
    with ProcessPoolExecutor(max_workers=8) as executor:
        for res in executor.map(run_single_ablation_match, tasks):
            results[res["arm"]][str(res["seed"])] = res
            
    out_path = "scratch/v2_mechanism_ablations_50seeds_raw.json"
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Ablation suite complete. Results saved to {out_path}.")

if __name__ == "__main__":
    main()
