import sys
import os
import json
from collections import defaultdict
import numpy as np
from concurrent.futures import ProcessPoolExecutor
import kaggle_environments

sys.path.insert(0, os.path.abspath('.'))

from scratch.qualification_counterfactual_suite import BaseQ50Agent
import candidates.candidate_cl_labor_minimal_v1 as candidate_module

def run_fast_instrumented_seed(args):
    pol_name, seed = args
    if pol_name == "Raw_Q50":
        agent = BaseQ50Agent(50)
    elif pol_name == "Frozen_Candidate":
        agent = candidate_module.ClosedLoopLaborMinimalV1(50)
    else:
        raise ValueError(f"Unknown policy {pol_name}")

    cfg = {"episodeSteps": 720, "seed": seed}
    env = kaggle_environments.make("kaggriculture", configuration=cfg)
    steps = env.run([agent, "starter"])
    
    action_counts = defaultdict(int)
    idle_steps = 0
    total_worker_steps = 0
    
    missed_water_events = 0
    strawberry_deaths = 0
    strawberry_cap_loss_events = 0
    strawberry_cap_units_lost = 0
    
    mature_straw_hours = 0
    peripheral_weeds_seen = 0
    watering_conflicts = 0
    animal_conflicts = 0
    
    prev_tiles = None
    
    for step_idx, step_data in enumerate(steps):
        f0_obs = step_data[0]["observation"]["farms"][0]
        step_action = step_data[0].get("action") or {}
        farmer_act = step_action.get("farmer") or []
        hands_act = step_action.get("hands") or []
        workers = f0_obs.get("workers") or []
        
        n_workers = len(workers)
        total_worker_steps += n_workers
        
        # Collect worker action tokens
        worker_act_tokens = []
        if isinstance(farmer_act, list) and len(farmer_act) > 0:
            worker_act_tokens.append(str(farmer_act[0]))
        for h in hands_act:
            if isinstance(h, list) and len(h) > 0:
                worker_act_tokens.append(str(h[0]))
                
        for act in worker_act_tokens:
            action_counts[act] += 1
            
        idle_this_step = n_workers - len(worker_act_tokens)
        idle_steps += max(0, idle_this_step)
        
        # Fast tile checks at midnight or once every 24 steps
        if step_idx % 24 == 0:
            tiles = f0_obs.get("tiles") or []
            unwatered_crops = 0
            for r in range(len(tiles)):
                for c in range(len(tiles[r])):
                    t = tiles[r][c]
                    if not isinstance(t, dict): continue
                    crop = t.get("crop")
                    yu = t.get("yield_units", 0)
                    
                    if crop == "STRAWBERRY" and yu >= 2:
                        mature_straw_hours += 24
                    if crop == "WEED" and (r >= 16 or c >= 16):
                        peripheral_weeds_seen += 1
                    if crop in ["STRAWBERRY", "MELON", "WHEAT"] and not t.get("watered", False):
                        unwatered_crops += 1
                        
            if unwatered_crops > n_workers:
                watering_conflicts += 1
                
            animals = f0_obs.get("animals") or []
            unserviced_animals = sum(1 for a in animals if not a.get("cared", False) or not a.get("fed", False))
            if unserviced_animals > 0 and unwatered_crops > 0 and (unserviced_animals + unwatered_crops) > n_workers:
                animal_conflicts += 1

            if step_idx > 0 and prev_tiles is not None:
                for r in range(len(tiles)):
                    for c in range(len(tiles[r])):
                        pt = prev_tiles[r][c]
                        ct = tiles[r][c]
                        if not isinstance(pt, dict) or not isinstance(ct, dict): continue
                        
                        if pt.get("crop") == "STRAWBERRY" and pt.get("yield_units", 0) >= 2:
                            if not pt.get("watered", False):
                                missed_water_events += 1
                                
                        if pt.get("crop") == "STRAWBERRY" and ct.get("crop") == "WEED":
                            if pt.get("consecutive_unwatered", 0) >= 1 and not pt.get("watered", False):
                                strawberry_deaths += 1
                                
                        if pt.get("crop") == "STRAWBERRY" and pt.get("stage", 0) >= 10:
                            if (pt.get("stage", 0) - 10) % 2 == 0 and pt.get("watered", False):
                                old_yu = pt.get("yield_units", 0)
                                if old_yu + 2 > 4:
                                    strawberry_cap_loss_events += 1
                                    strawberry_cap_units_lost += (old_yu + 2 - 4)
            prev_tiles = tiles

    move_steps = sum(action_counts[k] for k in ["NORTH", "SOUTH", "EAST", "WEST"])
    
    sold_qty = defaultdict(int)
    for st in steps:
        for o in (st[0].get("action") or {}).get("market", []):
            if isinstance(o, list) and len(o) >= 3 and o[0] == "SELL":
                sold_qty[o[1]] += int(o[2])
                
    env_rew = float(steps[-1][0]["reward"])
    
    return {
        "policy": pol_name,
        "seed": seed,
        "reward": env_rew,
        "dig": action_counts["DIG"],
        "move": move_steps,
        "water": action_counts["WATER"],
        "harvest": action_counts["HARVEST"],
        "care": action_counts["CARE"],
        "feed": action_counts["FEED"],
        "plant": sum(action_counts[k] for k in action_counts if k.startswith("PLANT")),
        "idle": idle_steps,
        "total_worker_steps": total_worker_steps,
        "utilization": (total_worker_steps - idle_steps) / max(1, total_worker_steps),
        "missed_water": missed_water_events,
        "strawberry_deaths": strawberry_deaths,
        "cap_loss_events": strawberry_cap_loss_events,
        "cap_units_lost": strawberry_cap_units_lost,
        "mature_straw_hours": mature_straw_hours,
        "peripheral_weeds": peripheral_weeds_seen,
        "water_conflicts": watering_conflicts,
        "animal_conflicts": animal_conflicts,
        "wool": sold_qty["WOOL"],
        "milk": sold_qty["MILK"],
        "strawberry": sold_qty["STRAWBERRY"],
        "wheat": sold_qty["WHEAT"],
        "melon": sold_qty["MELON"],
        "fertilizer": sold_qty["FERTILIZER"],
    }

def main():
    seeds = list(range(941000, 941500))
    print(f"Running Fast Instrumented Analysis on Seeds 941000-941499 (N={len(seeds)})...", flush=True)
    
    jobs = [(p, s) for p in ["Raw_Q50", "Frozen_Candidate"] for s in seeds]
    results = defaultdict(dict)
    
    with ProcessPoolExecutor(max_workers=11) as executor:
        for i, res in enumerate(executor.map(run_fast_instrumented_seed, jobs, chunksize=8)):
            results[res["policy"]][res["seed"]] = res
            if (i + 1) % 100 == 0:
                print(f"Completed {i + 1}/{len(jobs)} runs...", flush=True)

    with open("scratch/instrumented_validation_500seeds.json", "w") as f:
        json.dump(results, f, indent=2)
    print("Saved instrumented results to scratch/instrumented_validation_500seeds.json", flush=True)

if __name__ == "__main__":
    main()
