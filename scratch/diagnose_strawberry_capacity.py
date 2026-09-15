"""
Diagnostic Script: Strawberry Spatial Bottleneck & Irrigation Telemetry
========================================================================
Inspects:
1. Exact strawberry planting tiles and timeline in CL-Economic-V1 vs Frozen V2.
2. Watering reliability (% of bush-days successfully watered).
3. Fertilizer application (% of bushes fertilized).
4. Harvest batching and unharvested/immature strawberry loss.
5. Spatial layout comparison (which quadrants and coordinates are used).
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

def analyze_seed(seed=1000):
    cfg = {"episodeSteps": 720, "seed": seed}
    
    # 1. Run CL-Economic-V1
    env_cl = kaggle_environments.make("kaggriculture", configuration=cfg)
    cl_agent = ClosedLoopEconomicV1()
    env_cl.run([cl_agent, "starter"])
    
    # 2. Run Frozen V2
    env_v2 = kaggle_environments.make("kaggriculture", configuration=cfg)
    env_v2.run([v2_agent, "starter"])
    
    def extract_farm_telemetry(env, agent_name):
        steps = env.steps
        straw_tiles_planted = set()
        straw_history_by_tile = defaultdict(dict) # (x, y) -> {day: (watered, age, yield, fert)}
        actions_by_type = defaultdict(int)
        water_attempts = 0
        water_success = 0
        straw_harvest_events = []
        feed_bought = 0
        fert_collected = 0
        fert_applied = 0
        wheat_planted_tiles = set()
        melon_planted_tiles = set()
        
        # Track daily bush count & watering
        daily_straw_bushes = {}
        daily_straw_watered = {}
        
        for s in range(1, len(steps)):
            step_data = steps[s][0]
            obs = step_data["observation"]
            day = obs.get("day", s // 24)
            hour = obs.get("hour", s % 24)
            farm = obs["farms"][0]
            tiles = farm.get("tiles") or []
            act = step_data.get("action") or {}
            
            # Market actions
            for m in (act.get("market") or []):
                if isinstance(m, list) and len(m) > 2:
                    if m[0] == "BUY_PRODUCT" and m[1] == "WHEAT":
                        feed_bought += int(m[2])
            
            # Worker actions
            all_acts = []
            if act.get("farmer"):
                all_acts.append(act["farmer"])
            for h in (act.get("hands") or []):
                all_acts.append(h)
                
            for a in all_acts:
                if isinstance(a, list) and len(a) > 0:
                    cmd = a[0]
                    if cmd in ("NORTH", "SOUTH", "EAST", "WEST"):
                        actions_by_type["MOVE"] += 1
                    elif cmd == "PASS":
                        actions_by_type["IDLE"] += 1
                    else:
                        actions_by_type["PRODUCTIVE"] += 1
                        if cmd == "WATER":
                            water_attempts += 1
                        elif cmd == "COLLECT_FERTILIZER":
                            fert_collected += 1
                        elif cmd == "FERTILIZE":
                            fert_applied += 1
                        elif cmd == "HARVEST":
                            actions_by_type["HARVEST"] += 1
                        elif cmd == "PLANT":
                            if len(a) > 1:
                                if a[1] == "STRAWBERRY":
                                    actions_by_type["PLANT_STRAW"] += 1
                                elif a[1] == "WHEAT":
                                    actions_by_type["PLANT_WHEAT"] += 1
                                elif a[1] == "MELON":
                                    actions_by_type["PLANT_MELON"] += 1
            
            # Check tiles at end of day (hour 23)
            if hour == 23:
                bushes_today = 0
                watered_today = 0
                for y in range(10):
                    for x in range(10):
                        t = tiles[y][x]
                        if isinstance(t, dict) and t.get("kind") == "PLANT":
                            c = t.get("crop")
                            if c == "STRAWBERRY":
                                bushes_today += 1
                                straw_tiles_planted.add((x, y))
                                is_w = t.get("watered_today", False)
                                if is_w:
                                    watered_today += 1
                                age = day - int(t.get("planted_day", 0))
                                yu = int(t.get("yield_units", 0))
                                is_f = t.get("fertilized_until_day", -1) >= day
                                straw_history_by_tile[(x, y)][day] = {
                                    "watered": is_w, "age": age, "yield": yu, "fertilized": is_f
                                }
                            elif c == "WHEAT":
                                wheat_planted_tiles.add((x, y))
                            elif c == "MELON":
                                melon_planted_tiles.add((x, y))
                daily_straw_bushes[day] = bushes_today
                daily_straw_watered[day] = watered_today
        
        # End of game stats
        final_obs = steps[-1][0]["observation"]
        final_farm = final_obs["farms"][0]
        final_priv = final_obs.get("private") or {}
        shed = dict(final_priv.get("shed") or {})
        reward = float(steps[-1][0].get("reward") or 0.0)
        final_money = float(final_farm.get("money") or 0.0)
        final_tiles = final_farm.get("tiles") or []
        unlocked_quads = final_farm.get("unlocked_quadrants") or []
        
        # Count sales from market orders across game
        sales = defaultdict(int)
        for s in range(1, len(steps)):
            act = steps[s][0].get("action") or {}
            for o in (act.get("market") or []):
                if isinstance(o, list) and len(o) > 2 and o[0] == "SELL":
                    sales[o[1]] += int(o[2])
                    
        # Total bush-days
        total_bush_days = sum(daily_straw_bushes.values())
        total_watered_bush_days = sum(daily_straw_watered.values())
        watering_rate = (total_watered_bush_days / total_bush_days * 100) if total_bush_days > 0 else 0.0
        
        return {
            "agent": agent_name,
            "seed": seed,
            "reward": reward,
            "terminal_money": final_money,
            "unlocked_quads": unlocked_quads,
            "strawberry_tiles_count": len(straw_tiles_planted),
            "strawberry_tiles": sorted(list(straw_tiles_planted)),
            "wheat_tiles_count": len(wheat_planted_tiles),
            "melon_tiles_count": len(melon_planted_tiles),
            "straw_sold": sales.get("STRAWBERRY", 0),
            "wool_sold": sales.get("WOOL", 0),
            "milk_sold": sales.get("MILK", 0),
            "wheat_sold": sales.get("WHEAT", 0),
            "melon_sold": sales.get("MELON", 0),
            "fert_sold": sales.get("FERTILIZER", 0),
            "feed_bought": feed_bought,
            "actions": dict(actions_by_type),
            "total_bush_days": total_bush_days,
            "total_watered_bush_days": total_watered_bush_days,
            "watering_rate_pct": watering_rate,
            "daily_straw_bushes": daily_straw_bushes,
            "daily_straw_watered": daily_straw_watered,
            "shed": shed
        }
    
    cl_res = extract_farm_telemetry(env_cl, "CL-Economic-V1")
    v2_res = extract_farm_telemetry(env_v2, "Frozen-V2")
    return cl_res, v2_res

if __name__ == "__main__":
    print("Running diagnostic comparison on Seed 1000...")
    cl_res, v2_res = analyze_seed(1000)
    
    print("\n" + "="*80)
    print("STRAWBERRY SPATIAL & CAPACITY COMPARISON (SEED 1000)")
    print("="*80)
    print(f"METRIC                        CL-ECONOMIC-V1       FROZEN-V2 (BENCHMARK)")
    print(f"Terminal Reward:              ${cl_res['reward']:,.2f}          ${v2_res['reward']:,.2f}")
    print(f"Terminal Cash:                ${cl_res['terminal_money']:,.2f}           ${v2_res['terminal_money']:,.2f}")
    print(f"Unlocked Quadrants:           {cl_res['unlocked_quads']}         {v2_res['unlocked_quads']}")
    print(f"Strawberry Tiles Used:        {cl_res['strawberry_tiles_count']} tiles             {v2_res['strawberry_tiles_count']} tiles")
    print(f"Strawberry Units Sold:        {cl_res['straw_sold']} units            {v2_res['straw_sold']} units")
    print(f"Wool Units Sold:              {cl_res['wool_sold']} units            {v2_res['wool_sold']} units")
    print(f"Milk Units Sold:              {cl_res['milk_sold']} units            {v2_res['milk_sold']} units")
    print(f"Wheat Units Sold:             {cl_res['wheat_sold']} units            {v2_res['wheat_sold']} units")
    print(f"Fertilizer Units Sold:        {cl_res['fert_sold']} units            {v2_res['fert_sold']} units")
    print(f"Feed Bought (Market):         {cl_res['feed_bought']} units             {v2_res['feed_bought']} units")
    print(f"Watering Success Rate:        {cl_res['watering_rate_pct']:.1f}%                {v2_res['watering_rate_pct']:.1f}%")
    print(f"Total Bush-Days:              {cl_res['total_bush_days']} bush-days       {v2_res['total_bush_days']} bush-days")
    print(f"Total Watered Bush-Days:      {cl_res['total_watered_bush_days']} bush-days       {v2_res['total_watered_bush_days']} bush-days")
    print(f"Action Profile:")
    print(f"  Moves:                      {cl_res['actions'].get('MOVE', 0)}               {v2_res['actions'].get('MOVE', 0)}")
    print(f"  Productive:                 {cl_res['actions'].get('PRODUCTIVE', 0)}               {v2_res['actions'].get('PRODUCTIVE', 0)}")
    print(f"  Idle / Pass:                {cl_res['actions'].get('IDLE', 0)}               {v2_res['actions'].get('IDLE', 0)}")
    print(f"\nStrawberry Tiles (CL): {cl_res['strawberry_tiles']}")
    print(f"Strawberry Tiles (V2): {v2_res['strawberry_tiles']}")
    
    # Save diagnostic results
    os.makedirs("scratch", exist_ok=True)
    with open("scratch/strawberry_diagnostic_seed1000.json", "w") as f:
        json.dump({"cl": cl_res, "v2": v2_res}, f, indent=2)
    print("\nSaved diagnostic output to scratch/strawberry_diagnostic_seed1000.json")
