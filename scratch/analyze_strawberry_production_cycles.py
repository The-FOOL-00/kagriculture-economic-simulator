"""
Strawberry Production Cycles Forensics: CL-Economic-V1 vs Frozen-V2
===================================================================
Tracks every production cycle for every strawberry bush across the 30-day game.
Measures:
1. Number of bushes planted and planting day.
2. For each bush: each production event (days_since_first % 2 == 0):
   - Was it watered on that day?
   - Was it fertilized on that day?
   - Yield added (+2, +1, or 0).
   - Did yield cap at 4 (overflow loss)?
   - Was it harvested in time?
"""

import sys
import os
import json
import copy
from collections import defaultdict

PROJECT_ROOT = os.path.abspath(".")
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import kaggle_environments
from candidates.candidate_cl_economic_v1 import ClosedLoopEconomicV1
from candidates.slot2_aethel_refined_v2 import agent as v2_agent

def trace_cycles(agent_fn, agent_name, seed=1000):
    base_agent = agent_fn
    bushes = {} # (x, y) -> {"planted_day": d, "events": []}
    
    # Store daily states at hour 23
    daily_tile_states = {} # day -> { (x,y): tile_copy }
    
    # Harvest tracking
    harvested_by_tile = defaultdict(int)
    harvest_events = []
    
    # Track inventory drops
    last_invs = None
    
    def tracking_agent(obs, cfg=None):
        nonlocal last_invs
        step = obs['step']
        day = obs.get('day', step // 24)
        hour = obs.get('hour', step % 24)
        
        # Check harvests by tracking inventory deltas and worker positions
        curr_invs = copy.deepcopy(obs['private']['inventories'])
        farms = obs['farms'][0]
        workers = [farms['farmer']] + (farms.get('hands') or [])
        
        if last_invs is not None:
            for i, (ci, li) in enumerate(zip(curr_invs, last_invs)):
                ds = ci.get('STRAWBERRY', 0) - li.get('STRAWBERRY', 0)
                if ds > 0 and i < len(workers):
                    wx, wy = workers[i]
                    harvested_by_tile[(wx, wy)] += ds
                    harvest_events.append((step, day, hour, (wx, wy), ds))
        last_invs = curr_invs
        
        # At end of day (hour 23), record tile states
        if hour == 23:
            tiles = farms.get('tiles') or []
            daily_tile_states[day] = {}
            for y in range(10):
                for x in range(10):
                    t = tiles[y][x]
                    if isinstance(t, dict) and t.get('crop') == 'STRAWBERRY':
                        daily_tile_states[day][(x, y)] = copy.deepcopy(t)
                        if (x, y) not in bushes:
                            bushes[(x, y)] = {
                                "planted_day": t.get("planted_day"),
                                "history": {}
                            }
                        bushes[(x, y)]["history"][day] = {
                            "watered": t.get("watered_today", False),
                            "fertilized": t.get("fertilized_until_day", -1) >= day,
                            "yield_units": t.get("yield_units", 0)
                        }
        
        return base_agent(obs, cfg)

    cfg = {"episodeSteps": 720, "seed": seed}
    env = kaggle_environments.make("kaggriculture", configuration=cfg)
    env.run([tracking_agent, "starter"])
    
    total_harvested = sum(harvested_by_tile.values())
    reward = float(env.steps[-1][0].get("reward") or 0.0)
    
    # Analyze production events for each bush
    # In engine: STRAWBERRY: first_yield_day=10, interval=2, max_yield=4.
    # On day transition current_day -> next_day:
    # days_since_first = next_day - planted_day - 10
    # If days_since_first >= 0 and days_since_first % 2 == 0 and (days_since_first // 2 + 1) <= 4:
    # Production event occurs on the night of current_day!
    # Production relies on current_day's watered_today and fertilized_until_day >= current_day!
    
    production_events_analyzed = []
    total_potential_units = 0
    total_actual_yield_generated = 0
    missed_watering_events = 0
    unfertilized_events = 0
    fertilized_events = 0
    
    for pos, binfo in bushes.items():
        pd = binfo["planted_day"]
        hist = binfo["history"]
        for p_idx in range(4): # up to 4 production cycles
            # The night of current_day = pd + 10 + p_idx * 2 - 1
            prod_day = pd + 10 + p_idx * 2 - 1
            if prod_day in hist:
                day_data = hist[prod_day]
                w = day_data["watered"]
                f = day_data["fertilized"]
                gen = 0
                if w:
                    gen = 2 if f else 1
                    if f: fertilized_events += 1
                    else: unfertilized_events += 1
                else:
                    missed_watering_events += 1
                total_actual_yield_generated += gen
                total_potential_units += 2 # if watered & fertilized
                production_events_analyzed.append({
                    "tile": pos, "planted_day": pd, "cycle": p_idx + 1, "prod_day": prod_day,
                    "watered": w, "fertilized": f, "yield_generated": gen
                })
            elif prod_day <= 29:
                # Died or missing
                missed_watering_events += 1
                total_potential_units += 2
                
    return {
        "agent": agent_name,
        "reward": reward,
        "total_bushes": len(bushes),
        "total_harvested": total_harvested,
        "total_potential_yield": total_potential_units,
        "total_yield_generated": total_actual_yield_generated,
        "fertilized_production_events": fertilized_events,
        "unfertilized_production_events": unfertilized_events,
        "missed_watering_production_events": missed_watering_events,
        "harvest_events_count": len(harvest_events),
        "bushes": bushes
    }

if __name__ == "__main__":
    cl_p = trace_cycles(ClosedLoopEconomicV1(), "CL-Economic-V1", 1000)
    v2_p = trace_cycles(v2_agent, "Frozen-V2", 1000)
    
    print("="*80)
    print("STRAWBERRY PRODUCTION CYCLE ANALYSIS (SEED 1000)")
    print("="*80)
    print(f"METRIC                                CL-ECONOMIC-V1       FROZEN-V2")
    print(f"Terminal Reward:                      ${cl_p['reward']:,.2f}          ${v2_p['reward']:,.2f}")
    print(f"Total Strawberry Bushes Planted:      {cl_p['total_bushes']} bushes           {v2_p['total_bushes']} bushes")
    print(f"Total Strawberry Yield Harvested:     {cl_p['total_harvested']} units            {v2_p['total_harvested']} units")
    print(f"Total Theoretical Max Yield (8/bush): {cl_p['total_potential_yield']} units            {v2_p['total_potential_yield']} units")
    print(f"Total Yield Actually Generated:       {cl_p['total_yield_generated']} units            {v2_p['total_yield_generated']} units")
    print(f"Fertilized Cycles (+2 units):         {cl_p['fertilized_production_events']} cycles           {v2_p['fertilized_production_events']} cycles")
    print(f"Unfertilized Cycles (+1 unit):        {cl_p['unfertilized_production_events']} cycles           {v2_p['unfertilized_production_events']} cycles")
    print(f"Missed/Unwatered Cycles (0 units):    {cl_p['missed_watering_production_events']} cycles           {v2_p['missed_watering_production_events']} cycles")
    print(f"Harvest Actions Taken:                {cl_p['harvest_events_count']} harvests         {v2_p['harvest_events_count']} harvests")
