"""
Probe V2 vs CL-Economic-V1 Production Timelines
Inspects exact step-by-step history of:
- Strawberry: Buy steps, plant steps, first harvest, total harvest
- Sheep: Buy steps, count, first wool harvest, total wool
- Wheat: Harvest yield sizes, harvest steps, why 1-unit harvests happen
- Fertilizer: Generated, used on which crop, sold
"""

import sys
import os
import json
from collections import defaultdict

PROJECT_ROOT = os.path.abspath(".")
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import kaggle_environments
from candidates.slot2_aethel_refined_v2 import agent as v2_agent
from candidates.candidate_cl_economic_v1 import agent as cl_agent

def trace_production(agent_fn, agent_name, seed=5000):
    cfg = {"episodeSteps": 720, "seed": seed}
    env = kaggle_environments.make("kaggriculture", configuration=cfg)
    env.run([agent_fn, "starter"])
    steps = env.steps
    
    straw_buys = []
    straw_plants = []
    straw_harvests = []
    
    sheep_buys = []
    wool_harvests = []
    
    wheat_harvests = []
    fert_uses = []
    
    for s in range(1, len(steps)):
        day = s // 24
        hr = s % 24
        
        act = steps[s][0].get("action") or {}
        p_farm = steps[s-1][0]["observation"]["farms"][0]
        c_farm = steps[s][0]["observation"]["farms"][0]
        
        # Market orders
        for o in act.get("market", []):
            if not isinstance(o, list) or len(o) < 2: continue
            cmd = o[0]
            item = o[1]
            qty = int(o[2]) if len(o) > 2 else 1
            if cmd == "BUY_SEED" and item == "STRAWBERRY":
                straw_buys.append((s, day, hr, qty))
            elif cmd == "BUY_ANIMAL" and item == "SHEEP":
                sheep_buys.append((s, day, hr, qty))
                
        # Tile transitions
        p_tiles = p_farm.get("tiles") or []
        c_tiles = c_farm.get("tiles") or []
        for r in range(len(p_tiles)):
            for c in range(len(p_tiles[r])):
                pt = p_tiles[r][c] if isinstance(p_tiles[r][c], dict) else {}
                ct = c_tiles[r][c] if isinstance(c_tiles[r][c], dict) else {}
                
                # Planted
                if not pt.get("crop") and ct.get("crop") == "STRAWBERRY":
                    straw_plants.append((s, day, hr, (c, r)))
                    
                # Harvested
                if pt.get("crop") == "STRAWBERRY" and int(pt.get("yield_units", 0) or 0) > 0:
                    c_y = int(ct.get("yield_units", 0) or 0) if ct.get("crop") == "STRAWBERRY" else 0
                    p_y = int(pt.get("yield_units", 0) or 0)
                    if c_y < p_y:
                        straw_harvests.append((s, day, hr, p_y - c_y, pt.get("fertilized", False)))
                        
                if pt.get("crop") == "WHEAT" and int(pt.get("yield_units", 0) or 0) > 0:
                    c_y = int(ct.get("yield_units", 0) or 0) if ct.get("crop") == "WHEAT" else 0
                    p_y = int(pt.get("yield_units", 0) or 0)
                    if c_y < p_y:
                        wheat_harvests.append((s, day, hr, p_y - c_y, int(pt.get("planted_day", 0))))
                        
                if pt.get("kind") == "PASTURE" and pt.get("animal") == "SHEEP" and int(pt.get("yield_units", 0) or 0) > 0:
                    c_y = int(ct.get("yield_units", 0) or 0) if ct.get("kind") == "PASTURE" else 0
                    p_y = int(pt.get("yield_units", 0) or 0)
                    if c_y < p_y:
                        wool_harvests.append((s, day, hr, p_y - c_y))
                        
                # Fertilized
                if pt.get("kind") == "PLANT" and not pt.get("fertilized") and ct.get("fertilized"):
                    fert_uses.append((s, day, hr, pt.get("crop"), (c, r)))
                    
    print(f"=== {agent_name} PRODUCTION TIMELINE (Seed {seed}) ===")
    print(f"Strawberry Seed Purchases (Total: {sum(x[3] for x in straw_buys)} seeds in {len(straw_buys)} orders):")
    for b in straw_buys[:10]:
        print(f"  Step {b[0]:3d} (Day {b[1]:2d}, Hr {b[2]:2d}): bought {b[3]} seeds")
    if len(straw_buys) > 10: print(f"  ... and {len(straw_buys)-10} more orders")
    
    print(f"\nStrawberry Plantings (Total: {len(straw_plants)} plots):")
    if straw_plants:
        first_d = straw_plants[0][1]
        last_d = straw_plants[-1][1]
        print(f"  First planted on Day {first_d} (Step {straw_plants[0][0]}), Last planted on Day {last_d} (Step {straw_plants[-1][0]})")
        d_counts = defaultdict(int)
        for p in straw_plants: d_counts[p[1]] += 1
        for d, count in sorted(d_counts.items()):
            print(f"    Day {d:2d}: planted {count:2d} strawberry plots")
            
    print(f"\nStrawberry Harvests (Total: {sum(h[3] for h in straw_harvests)} units across {len(straw_harvests)} harvests):")
    if straw_harvests:
        print(f"  First harvest on Day {straw_harvests[0][1]} (Step {straw_harvests[0][0]}), Last on Day {straw_harvests[-1][1]}")
        h_sizes = defaultdict(int)
        for h in straw_harvests: h_sizes[h[3]] += 1
        print(f"  Yield sizes distribution: {dict(h_sizes)}")
        
    print(f"\nSheep Purchases (Total: {sum(x[3] for x in sheep_buys)} sheep in {len(sheep_buys)} orders):")
    for b in sheep_buys:
        print(f"  Step {b[0]:3d} (Day {b[1]:2d}, Hr {b[2]:2d}): bought {b[3]} sheep")
    print(f"Wool Harvests (Total: {sum(h[3] for h in wool_harvests)} units across {len(wool_harvests)} shears):")
    if wool_harvests:
        print(f"  First wool shear on Day {wool_harvests[0][1]}, Last on Day {wool_harvests[-1][1]}")

    print(f"\nWheat Harvests (Total: {sum(h[3] for h in wheat_harvests)} units across {len(wheat_harvests)} harvests):")
    w_sizes = defaultdict(int)
    for h in wheat_harvests: w_sizes[h[3]] += 1
    print(f"  Wheat yield sizes distribution: {dict(w_sizes)}")
    if 1 in w_sizes:
        print("  Sample of 1-unit wheat harvests (Step, Day, Hr, PlantedDay):")
        single_w = [h for h in wheat_harvests if h[3] == 1][:5]
        for sw in single_w:
            print(f"    Step {sw[0]:3d} (Day {sw[1]:2d}, Hr {sw[2]:2d}), planted on Day {sw[4]}")

    print(f"\nFertilizer Applications (Total: {len(fert_uses)} applications):")
    f_crops = defaultdict(int)
    for f in fert_uses: f_crops[f[3]] += 1
    print(f"  Fertilizer targets by crop: {dict(f_crops)}")
    print("=" * 80 + "\n")

if __name__ == "__main__":
    trace_production(v2_agent, "FROZEN V2", seed=5000)
    trace_production(cl_agent, "CL-ECONOMIC-V1", seed=5000)
