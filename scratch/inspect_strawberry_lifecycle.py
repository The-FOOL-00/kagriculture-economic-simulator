"""
Lifecycle Inspector: Strawberry Planting, Fertilization, and Harvest Timing
===========================================================================
Deep dive into why Frozen-V2 produces 270 strawberry units vs CL-Economic-V1's 193.
"""

import sys
import os
import json
from collections import defaultdict

PROJECT_ROOT = os.path.abspath(".")
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import kaggle_environments
from candidates.candidate_cl_economic_v1 import ClosedLoopEconomicV1
from candidates.slot2_aethel_refined_v2 import agent as v2_agent

def inspect_lifecycle(seed=1000):
    cfg = {"episodeSteps": 720, "seed": seed}
    
    def run_and_trace(agent):
        env = kaggle_environments.make("kaggriculture", configuration=cfg)
        env.run([agent, "starter"])
        steps = env.steps
        
        # Track every action on strawberry tiles
        tile_events = defaultdict(list) # (x, y) -> list of (step, day, hour, action, details)
        harvests = [] # list of (step, day, hour, tile, yield_units)
        plantings = [] # list of (step, day, hour, tile)
        fertilizations = [] # list of (step, day, hour, tile)
        
        # Track tile state across time
        for s in range(1, len(steps)):
            obs = steps[s][0]["observation"]
            day = obs.get("day", s // 24)
            hour = obs.get("hour", s % 24)
            farm = obs["farms"][0]
            tiles = farm.get("tiles") or []
            act = steps[s][0].get("action") or {}
            
            # Map worker positions
            all_workers = [farm.get("farmer")] + (farm.get("hands") or [])
            all_acts = []
            if act.get("farmer"): all_acts.append(act["farmer"])
            for h in (act.get("hands") or []): all_acts.append(h)
            
            for w_idx, (w_pos, w_act) in enumerate(zip(all_workers, all_acts)):
                if not w_pos or not w_act: continue
                wx, wy = w_pos
                cmd = w_act[0] if isinstance(w_act, list) and len(w_act) > 0 else "PASS"
                
                if cmd == "PLANT" and len(w_act) > 1 and w_act[1] == "STRAWBERRY":
                    plantings.append((s, day, hour, (wx, wy)))
                    tile_events[(wx, wy)].append((s, day, hour, "PLANT"))
                elif cmd == "FERTILIZE":
                    # Check what crop is on this tile
                    t = tiles[wy][wx] if 0 <= wy < 10 and 0 <= wx < 10 else None
                    crop = t.get("crop") if isinstance(t, dict) else None
                    fertilizations.append((s, day, hour, (wx, wy), crop))
                    tile_events[(wx, wy)].append((s, day, hour, f"FERTILIZE_{crop}"))
                elif cmd == "HARVEST":
                    t = tiles[wy][wx] if 0 <= wy < 10 and 0 <= wx < 10 else None
                    crop = t.get("crop") if isinstance(t, dict) else None
                    yu = t.get("yield_units", 0) if isinstance(t, dict) else 0
                    if crop == "STRAWBERRY":
                        harvests.append((s, day, hour, (wx, wy), yu))
                        tile_events[(wx, wy)].append((s, day, hour, f"HARVEST_{yu}"))
                        
        return plantings, fertilizations, harvests, tile_events
    
    cl_p, cl_f, cl_h, cl_events = run_and_trace(ClosedLoopEconomicV1())
    v2_p, v2_f, v2_h, v2_events = run_and_trace(v2_agent)
    
    print("="*80)
    print("LIFECYCLE COMPARISON: CL-ECONOMIC-V1 vs FROZEN-V2 (SEED 1000)")
    print("="*80)
    
    print(f"\n1. PLANTING EVENTS:")
    print(f"CL Total Strawberry Plantings: {len(cl_p)}")
    print(f"V2 Total Strawberry Plantings: {len(v2_p)}")
    
    # Planting day distribution
    cl_plant_days = defaultdict(int)
    for _, d, _, _ in cl_p: cl_plant_days[d] += 1
    v2_plant_days = defaultdict(int)
    for _, d, _, _ in v2_p: v2_plant_days[d] += 1
    
    print(f"CL Planting Days: {dict(sorted(cl_plant_days.items()))}")
    print(f"V2 Planting Days: {dict(sorted(v2_plant_days.items()))}")
    
    print(f"\n2. FERTILIZATION EVENTS:")
    cl_fert_straw = [f for f in cl_f if f[4] == "STRAWBERRY"]
    v2_fert_straw = [f for f in v2_f if f[4] == "STRAWBERRY"]
    print(f"CL Total Fertilizations: {len(cl_f)} (on Strawberry: {len(cl_fert_straw)})")
    print(f"V2 Total Fertilizations: {len(v2_f)} (on Strawberry: {len(v2_fert_straw)})")
    
    # Other crops fertilized
    cl_fert_other = defaultdict(int)
    for f in cl_f: cl_fert_other[f[4]] += 1
    v2_fert_other = defaultdict(int)
    for f in v2_f: v2_fert_other[f[4]] += 1
    print(f"CL Crops Fertilized: {dict(cl_fert_other)}")
    print(f"V2 Crops Fertilized: {dict(v2_fert_other)}")
    
    print(f"\n3. HARVEST EVENTS (STRAWBERRY):")
    cl_h_units = sum(h[4] for h in cl_h)
    v2_h_units = sum(h[4] for h in v2_h)
    print(f"CL Strawberry Harvest Actions: {len(cl_h)} -> Total Yield Harvested: {cl_h_units} units")
    print(f"V2 Strawberry Harvest Actions: {len(v2_h)} -> Total Yield Harvested: {v2_h_units} units")
    
    # Yield distribution per harvest
    cl_h_dist = defaultdict(int)
    for h in cl_h: cl_h_dist[h[4]] += 1
    v2_h_dist = defaultdict(int)
    for h in v2_h: v2_h_dist[h[4]] += 1
    print(f"CL Harvest Yield Distribution (yield -> count): {dict(sorted(cl_h_dist.items()))}")
    print(f"V2 Harvest Yield Distribution (yield -> count): {dict(sorted(v2_h_dist.items()))}")
    
    # Harvests by day
    cl_h_days = defaultdict(int)
    for h in cl_h: cl_h_days[h[1]] += h[4]
    v2_h_days = defaultdict(int)
    for h in v2_h: v2_h_days[h[1]] += h[4]
    print(f"\nCL Harvest Yield by Day: {dict(sorted(cl_h_days.items()))}")
    print(f"V2 Harvest Yield by Day: {dict(sorted(v2_h_days.items()))}")

if __name__ == "__main__":
    inspect_lifecycle(1000)
