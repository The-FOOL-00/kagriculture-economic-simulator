import sys
import os
import json
from collections import defaultdict, Counter
import numpy as np
import kaggle_environments

PROJECT_ROOT = os.path.abspath(".")
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from candidates.candidate_cl_economic_v1 import ClosedLoopEconomicV1
import candidates.slot2_aethel_refined_v2 as v2_mod

def analyze_tile_history(agent_fn_or_class, agent_label, seeds=list(range(1000, 1010))):
    print(f"Tracing tile histories for {agent_label} across {len(seeds)} seeds...")
    
    seed_metrics = []
    sample_tile_lifecycles = {} # for seed 1000 detailed transition table

    for seed in seeds:
        cfg = {"episodeSteps": 720, "seed": seed}
        env = kaggle_environments.make("kaggriculture", configuration=cfg, debug=False)
        
        if agent_label == "CL-Economic-V1":
            agent_inst = ClosedLoopEconomicV1()
        else:
            agent_inst = v2_mod.agent

        env.run([agent_inst, "starter"])
        steps = env.steps
        
        # We will track each tile (x, y) over all 720 steps
        # Board is 10x10
        # Tile state at step s: steps[s][0]["observation"]["farms"][0]["tiles"][y][x]
        
        tile_histories = defaultdict(list)
        # Track transitions
        # A tile lifecycle record: list of crop episodes:
        # [ { "crop": ..., "plant_step": ..., "harvest_steps": [...], "harvest_units": ..., "clear_step": ... }, ... ]
        active_crop_episode = {}
        completed_crop_episodes = defaultdict(list)
        
        planting_events = 0
        replanting_succession_events = 0
        harvest_events = 0
        harvest_opcodes_count = Counter()
        harvested_units = Counter()
        crop_counts_planted = Counter()
        tiles_ever_used_for_crops = set()

        # Step-by-step state tracking
        for s in range(len(steps)):
            farm = steps[s][0]["observation"]["farms"][0]
            tiles = farm["tiles"]
            day = s // 24
            hour = s % 24
            
            # Check action at this step
            act = steps[s][0].get("action") or {}
            all_acts = [act.get("farmer") or ["PASS"]] + (act.get("hands") or [])
            workers = [tuple(farm["farmer"])] + [tuple(h) for h in farm["hands"]]
            
            for w_idx, a in enumerate(all_acts):
                if a and a[0] == "HARVEST":
                    pos = workers[w_idx] if w_idx < len(workers) else (0, 0)
                    x, y = pos
                    t = tiles[y][x] if 0 <= y < 10 and 0 <= x < 10 else None
                    if isinstance(t, dict):
                        k = t.get("kind")
                        if k == "PLANT":
                            c = t.get("crop", "UNKNOWN")
                            harvest_opcodes_count[c] += 1
                        elif k == "PASTURE":
                            an = t.get("animal", "UNKNOWN")
                            harvest_opcodes_count[an] += 1
                        else:
                            harvest_opcodes_count["OTHER"] += 1
                    else:
                        harvest_opcodes_count["EMPTY"] += 1

            for y in range(10):
                for x in range(10):
                    t = tiles[y][x]
                    coord = (x, y)
                    prev_ep = active_crop_episode.get(coord)
                    
                    if isinstance(t, dict) and t.get("kind") == "PLANT":
                        tiles_ever_used_for_crops.add(coord)
                        crop = t.get("crop")
                        age = t.get("age", 0)
                        yu = int(t.get("yield_units", 0) or 0)
                        
                        if prev_ep is None:
                            # New planting event!
                            planting_events += 1
                            crop_counts_planted[crop] += 1
                            
                            # Check if this tile had a previous crop episode that was cleared
                            if len(completed_crop_episodes[coord]) > 0:
                                replanting_succession_events += 1
                                
                            active_crop_episode[coord] = {
                                "crop": crop,
                                "plant_step": s,
                                "plant_day": day,
                                "plant_hour": hour,
                                "harvest_steps": [],
                                "harvest_units": 0,
                                "max_yield_seen": yu,
                                "prev_yu": yu
                            }
                        else:
                            # Continuing crop episode
                            # Check if harvest occurred (yield units dropped without tile clearing)
                            prev_yu = prev_ep["prev_yu"]
                            if yu < prev_yu:
                                # Harvest event occurred!
                                units_taken = prev_yu - yu
                                prev_ep["harvest_steps"].append(s)
                                prev_ep["harvest_units"] += units_taken
                                harvest_events += 1
                                harvested_units[crop] += units_taken
                            prev_ep["prev_yu"] = yu
                            if yu > prev_ep["max_yield_seen"]:
                                prev_ep["max_yield_seen"] = yu
                    else:
                        # Tile is NOT a plant (either empty, weed, pasture, etc.)
                        if prev_ep is not None:
                            # Crop episode just ended (cleared / harvested-out)
                            # Final harvest check if it had yield when cleared
                            if prev_ep["prev_yu"] > 0:
                                prev_ep["harvest_steps"].append(s)
                                prev_ep["harvest_units"] += prev_ep["prev_yu"]
                                harvest_events += 1
                                harvested_units[prev_ep["crop"]] += prev_ep["prev_yu"]
                            prev_ep["clear_step"] = s
                            prev_ep["clear_day"] = day
                            completed_crop_episodes[coord].append(prev_ep)
                            del active_crop_episode[coord]

        # End of match: wrap up remaining active episodes
        final_active_tiles = 0
        final_tiles = steps[-1][0]["observation"]["farms"][0]["tiles"]
        for y in range(10):
            for x in range(10):
                t = final_tiles[y][x]
                if isinstance(t, dict) and t.get("kind") == "PLANT":
                    final_active_tiles += 1
                coord = (x, y)
                if coord in active_crop_episode:
                    ep = active_crop_episode[coord]
                    ep["clear_step"] = 720
                    ep["clear_day"] = 30
                    completed_crop_episodes[coord].append(ep)

        # Succession tiles count: physical tiles that hosted >= 2 crop episodes
        succession_tiles_count = sum(1 for coord, eps in completed_crop_episodes.items() if len(eps) >= 2)

        metrics = {
            "seed": seed,
            "unique_crop_tiles_ever": len(tiles_ever_used_for_crops),
            "final_active_crop_tiles": final_active_tiles,
            "total_planting_events": planting_events,
            "crops_planted_counts": dict(crop_counts_planted),
            "replanting_succession_events": replanting_succession_events,
            "succession_physical_tiles": succession_tiles_count,
            "total_harvest_events": harvest_events,
            "harvested_units": dict(harvested_units),
            "harvest_opcodes": dict(harvest_opcodes_count),
            "total_harvest_opcodes": sum(harvest_opcodes_count.values())
        }
        seed_metrics.append(metrics)
        
        if seed == 1000:
            sample_tile_lifecycles = {str(k): v for k, v in completed_crop_episodes.items() if len(v) > 0}

    return {
        "agent": agent_label,
        "seed_metrics": seed_metrics,
        "sample_seed1000_lifecycles": sample_tile_lifecycles
    }

if __name__ == "__main__":
    cl_res = analyze_tile_history(ClosedLoopEconomicV1, "CL-Economic-V1")
    v2_res = analyze_tile_history(v2_mod.agent, "Frozen-V2")
    
    with open("scratch/audit_tile_lifecycle_results.json", "w") as f:
        json.dump({"CL": cl_res, "V2": v2_res}, f, indent=2)
        
    print("\n" + "="*80)
    print("TILE LIFECYCLE & CONSISTENCY AUDIT COMPARISON (Seeds 1000-1009)")
    print("="*80)
    
    for label, res in [("CL-Economic-V1", cl_res), ("Frozen-V2", v2_res)]:
        sm = res["seed_metrics"]
        u_tiles = [x["unique_crop_tiles_ever"] for x in sm]
        final_t = [x["final_active_crop_tiles"] for x in sm]
        plants = [x["total_planting_events"] for x in sm]
        succ_ev = [x["replanting_succession_events"] for x in sm]
        succ_tiles = [x["succession_physical_tiles"] for x in sm]
        harv_ev = [x["total_harvest_events"] for x in sm]
        harv_ops = [x["total_harvest_opcodes"] for x in sm]
        
        # Crops planted breakdown
        wheat_p = [x["crops_planted_counts"].get("WHEAT", 0) for x in sm]
        melon_p = [x["crops_planted_counts"].get("MELON", 0) for x in sm]
        straw_p = [x["crops_planted_counts"].get("STRAWBERRY", 0) for x in sm]
        
        # Units harvested breakdown
        wheat_u = [x["harvested_units"].get("WHEAT", 0) for x in sm]
        melon_u = [x["harvested_units"].get("MELON", 0) for x in sm]
        straw_u = [x["harvested_units"].get("STRAWBERRY", 0) for x in sm]
        
        print(f"\n--- {label} ---")
        print(f"Unique physical tiles ever used for crops: {np.mean(u_tiles):.1f} (min {min(u_tiles)}, max {max(u_tiles)})")
        print(f"Final active crop tiles:                   {np.mean(final_t):.1f}")
        print(f"Total PLANTING events:                     {np.mean(plants):.1f} (Wheat: {np.mean(wheat_p):.1f}, Melon: {np.mean(melon_p):.1f}, Straw: {np.mean(straw_p):.1f})")
        print(f"Succession events (replant on same tile):  {np.mean(succ_ev):.1f}")
        print(f"Physical tiles with succession (>=2 crops):{np.mean(succ_tiles):.1f}")
        print(f"Total crop HARVEST events (tile-derived):  {np.mean(harv_ev):.1f}")
        print(f"Total HARVEST opcodes (all targets):       {np.mean(harv_ops):.1f}")
        print(f"Harvested crop units:                      Wheat: {np.mean(wheat_u):.1f}, Melon: {np.mean(melon_u):.1f}, Straw: {np.mean(straw_u):.1f}")
