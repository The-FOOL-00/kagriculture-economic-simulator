"""
Phase 2: Independent Reproduction of the +18 Melon Claim across 100 Seeds
Measures melon planting, watering, maturity, harvesting, sales, and revenue for V2 vs Candidate H.
"""

import sys
import os
import json
import numpy as np
from concurrent.futures import ProcessPoolExecutor

PROJECT_ROOT = os.path.abspath(".")
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from kaggle_environments import make
import candidates.slot2_aethel_refined_v2 as v2
from scratch.v2_jit_melon_experiment import agent_H_full_jit_pipeline

def run_single_seed_melons(seed):
    records = {}
    for label, fn in [("V2", v2.agent), ("H", agent_H_full_jit_pipeline)]:
        env = make("kaggriculture", configuration={"seed": seed, "episodeSteps": 720})
        env.reset()
        
        planted_count = 0
        watered_events = 0
        peak_yield = 0
        harvest_events = []
        sale_events = []
        total_revenue = 0.0
        mature_harvested = 0
        
        # Track up to Step 300 (melons are harvested/sold between step 240 and 280)
        for step in range(300):
            obs = env.steps[-1][0]["observation"]
            money_before = obs["farms"][0]["money"]
            shed_before_melon = obs["private"]["shed"].get("MELON", 0)
            
            # Count planted crops on farm
            melon_tiles = 0
            curr_yield_sum = 0
            for row in obs["farms"][0]["tiles"]:
                for t in row:
                    if isinstance(t, dict) and t.get("crop") == "MELON":
                        melon_tiles += 1
                        curr_yield_sum += t.get("yield", 0)
            
            if melon_tiles > planted_count:
                planted_count = melon_tiles
            if curr_yield_sum > peak_yield:
                peak_yield = curr_yield_sum
                
            action = fn(obs)
            
            # Count watering actions in action
            all_unit_actions = [action.get("farmer", [])] + action.get("hands", [])
            for ua in all_unit_actions:
                if isinstance(ua, list) and len(ua) >= 1 and ua[0] == "WATER":
                    watered_events += 1
                    
            env.step([action, {"farmer": ["PASS"]}])
            
            obs_after = env.steps[-1][0]["observation"]
            money_after = obs_after["farms"][0]["money"]
            shed_after_melon = obs_after["private"]["shed"].get("MELON", 0)
            
            # Did harvest occur? (shed melon increased)
            harvested = shed_after_melon - shed_before_melon
            if harvested > 0:
                harvest_events.append({"step": step, "amount": harvested})
                mature_harvested += harvested
                
            # Did melon sale occur?
            market_orders = action.get("market", [])
            for mo in market_orders:
                if isinstance(mo, list) and len(mo) >= 3 and mo[0] == "SELL" and mo[1] == "MELON":
                    qty = mo[2]
                    delta_m = money_after - money_before
                    # Note: other market transactions might co-occur, but melon sale is usually the main one
                    sale_events.append({"step": step, "qty": qty, "delta_money": delta_m})
                    total_revenue += delta_m

        records[label] = {
            "planted": planted_count,
            "peak_yield": peak_yield,
            "mature_harvested": mature_harvested,
            "harvest_events": harvest_events,
            "sale_events": sale_events,
            "revenue": total_revenue,
            "watered_events": watered_events
        }
        
    delta_mature = records["H"]["mature_harvested"] - records["V2"]["mature_harvested"]
    delta_rev = records["H"]["revenue"] - records["V2"]["revenue"]
    
    return {
        "seed": seed,
        "V2": records["V2"],
        "H": records["H"],
        "delta_mature": delta_mature,
        "delta_revenue": delta_rev
    }

def main():
    seeds = list(range(1000, 1100))
    print(f"Running Phase 2 melon audit across {len(seeds)} seeds...")
    
    with ProcessPoolExecutor(max_workers=6) as executor:
        results = list(executor.map(run_single_seed_melons, seeds))
        
    delta_mature_list = [r["delta_mature"] for r in results]
    delta_rev_list = [r["delta_revenue"] for r in results]
    v2_mature_list = [r["V2"]["mature_harvested"] for r in results]
    h_mature_list = [r["H"]["mature_harvested"] for r in results]
    v2_rev_list = [r["V2"]["revenue"] for r in results]
    h_rev_list = [r["H"]["revenue"] for r in results]
    
    stats = {
        "n_seeds": len(seeds),
        "v2_mature_mean": float(np.mean(v2_mature_list)),
        "h_mature_mean": float(np.mean(h_mature_list)),
        "delta_mature_mean": float(np.mean(delta_mature_list)),
        "delta_mature_median": float(np.median(delta_mature_list)),
        "delta_mature_p5": float(np.percentile(delta_mature_list, 5)),
        "delta_mature_p95": float(np.percentile(delta_mature_list, 95)),
        "delta_mature_min": float(np.min(delta_mature_list)),
        "delta_mature_max": float(np.max(delta_mature_list)),
        "v2_revenue_mean": float(np.mean(v2_rev_list)),
        "h_revenue_mean": float(np.mean(h_rev_list)),
        "delta_revenue_mean": float(np.mean(delta_rev_list)),
        "delta_revenue_median": float(np.median(delta_rev_list)),
        "delta_revenue_p5": float(np.percentile(delta_rev_list, 5)),
        "delta_revenue_p95": float(np.percentile(delta_rev_list, 95)),
        "v2_planted": results[0]["V2"]["planted"],
        "h_planted": results[0]["H"]["planted"],
        "v2_harvest_step": results[0]["V2"]["harvest_events"][0]["step"] if results[0]["V2"]["harvest_events"] else None,
        "h_harvest_step": results[0]["H"]["harvest_events"][0]["step"] if results[0]["H"]["harvest_events"] else None,
        "v2_sale_step": results[0]["V2"]["sale_events"][0]["step"] if results[0]["V2"]["sale_events"] else None,
        "h_sale_step": results[0]["H"]["sale_events"][0]["step"] if results[0]["H"]["sale_events"] else None,
    }
    
    print("\n--- PHASE 2 RESULTS SUMMARY ---")
    print(json.dumps(stats, indent=2))
    
    with open("scratch/jit_melon_results/phase2_melon_audit.json", "w") as f:
        json.dump({"stats": stats, "details": results}, f, indent=2)

if __name__ == "__main__":
    main()
