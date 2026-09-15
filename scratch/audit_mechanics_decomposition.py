import sys
import os
import json
from collections import defaultdict, Counter
import numpy as np
from concurrent.futures import ProcessPoolExecutor, as_completed
import kaggle_environments

PROJECT_ROOT = os.path.abspath(".")
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from candidates.candidate_cl_economic_v1 import ClosedLoopEconomicV1
import candidates.slot2_aethel_refined_v2 as v2_mod
from scratch.produce_drop_threshold_experiment import ProduceBatchingAgent

def analyze_match_forensics(args):
    agent_type, policy_name, seed = args
    cfg = {"episodeSteps": 720, "seed": seed}
    env = kaggle_environments.make("kaggriculture", configuration=cfg, debug=False)
    
    if agent_type == "CL":
        agent_inst = ClosedLoopEconomicV1()
    elif agent_type == "V2":
        agent_inst = v2_mod.agent
    elif agent_type == "PRODUCE":
        agent_inst = ProduceBatchingAgent(drop_policy=policy_name)
    else:
        raise ValueError(f"Unknown {agent_type}")
        
    env.run([agent_inst, "starter"])
    steps = env.steps
    total_steps = len(steps)
    
    # 1. Morning Cash Ledger (Day d, hour 0)
    morning_cash = {}
    morning_shed_produce = {}
    morning_pocket_produce = {}
    
    # 2. Sheep & Wool Life History
    sheep_purchases = [] # (step, count)
    sheep_placements = [] # step
    pastures_built = [] # (step, coord)
    sheep_feed_events = 0
    sheep_shear_events = 0 # HARVEST on sheep
    sheep_days_fed = defaultdict(int)
    sheep_days_unfed = defaultdict(int)
    final_sheep_count = 0
    
    # 3. Melon Wave Forensics
    melon_plantings = [] # (step, day, coord)
    melon_harvests = [] # (step, day, coord, yield_units)
    melon_cleared = [] # (step, day, coord)
    
    # 4. Field Occupancy & Worker Placement
    worker_steps_in_field = 0 # worker outside shed/well
    worker_steps_near_crops = 0 # worker dist <= 1 from crop
    delayed_harvest_opportunities = 0 # mature crop (yu == max_yield) standing unharvested
    
    for s in range(total_steps):
        day = s // 24
        hour = s % 24
        farm = steps[s][0]["observation"]["farms"][0]
        priv = steps[s][0]["observation"].get("private") or {}
        shed = priv.get("shed") or {}
        invs = priv.get("inventories") or []
        tiles = farm.get("tiles") or []
        workers = [tuple(farm["farmer"])] + [tuple(h) for h in farm["hands"]]
        
        # Morning observation (hour 0)
        if hour == 0:
            morning_cash[day] = float(farm.get("money") or 0.0)
            morning_shed_produce[day] = sum(int(shed.get(it, 0) or 0) for it in ("STRAWBERRY", "MELON", "WOOL", "MILK"))
            pock_p = sum(sum(int(inv.get(it, 0) or 0) for it in ("STRAWBERRY", "MELON", "WOOL", "MILK")) for inv in invs)
            morning_pocket_produce[day] = pock_p

        # Check actions taken at step s
        act = steps[s][0].get("action") or {}
        all_acts = [act.get("farmer") or ["PASS"]] + (act.get("hands") or [])
        m_orders = act.get("market") or []
        
        for mo in m_orders:
            if isinstance(mo, list) and len(mo) >= 2 and mo[0] == "BUY_ANIMAL" and mo[1] == "SHEEP":
                cnt = int(mo[2]) if len(mo) > 2 else 1
                sheep_purchases.append((s, day, hour, cnt))
                
        for w_idx, a in enumerate(all_acts):
            if not a: continue
            op = a[0]
            pos = workers[w_idx] if w_idx < len(workers) else (0, 0)
            if op == "PLACE" and len(a) > 1 and a[1] == "SHEEP":
                sheep_placements.append((s, day, hour, pos))
            elif op == "BUILD_PASTURE":
                pastures_built.append((s, day, hour, pos))
            elif op == "FEED":
                # Check target tile
                t = tiles[pos[1]][pos[0]] if 0 <= pos[1] < 10 and 0 <= pos[0] < 10 else None
                if isinstance(t, dict) and t.get("animal") == "SHEEP":
                    sheep_feed_events += 1
            elif op == "HARVEST":
                t = tiles[pos[1]][pos[0]] if 0 <= pos[1] < 10 and 0 <= pos[0] < 10 else None
                if isinstance(t, dict):
                    if t.get("kind") == "PASTURE" and t.get("animal") == "SHEEP":
                        sheep_shear_events += 1
                    elif t.get("kind") == "PLANT" and t.get("crop") == "MELON":
                        melon_harvests.append((s, day, hour, pos, int(t.get("yield_units", 0) or 0)))
            elif op == "PLANT" and len(a) > 1 and a[1] == "MELON":
                melon_plantings.append((s, day, hour, pos))
                
        # Worker spatial positions
        for w in workers:
            x, y = w
            if (x, y) not in ((4,4), (5,4), (4,5), (5,5), (4,6), (5,6)):
                worker_steps_in_field += 1
            # near crop
            near = False
            for dx, dy in ((0,0), (1,0), (-1,0), (0,1), (0,-1)):
                nx, ny = x + dx, y + dy
                if 0 <= nx < 10 and 0 <= ny < 10:
                    t = tiles[ny][nx]
                    if isinstance(t, dict) and t.get("kind") == "PLANT":
                        near = True
                        break
            if near:
                worker_steps_near_crops += 1
                
        # Check standing mature unharvested crops
        for r in tiles:
            for t in r:
                if isinstance(t, dict) and t.get("kind") == "PLANT":
                    c = t.get("crop")
                    yu = int(t.get("yield_units", 0) or 0)
                    if c == "WHEAT" and yu >= 6:
                        delayed_harvest_opportunities += 1
                    elif c == "MELON" and yu >= 6:
                        delayed_harvest_opportunities += 1
                    elif c == "STRAWBERRY" and yu >= 4:
                        delayed_harvest_opportunities += 1

    # End of match counts
    final_tiles = steps[-1][0]["observation"]["farms"][0]["tiles"]
    final_sheep = sum(1 for r in final_tiles for t in r if isinstance(t, dict) and t.get("animal") == "SHEEP")
    final_cows = sum(1 for r in final_tiles for t in r if isinstance(t, dict) and t.get("animal") == "COW")
    
    # Classify melon plantings into Wave 1 (Days 0-4) and Wave 2 (Day 5+)
    wave1_melons = [m for m in melon_plantings if m[1] <= 4]
    wave2_melons = [m for m in melon_plantings if m[1] > 4]

    return {
        "agent_type": agent_type,
        "policy_name": policy_name,
        "seed": seed,
        "morning_cash": morning_cash,
        "morning_shed_produce": morning_shed_produce,
        "morning_pocket_produce": morning_pocket_produce,
        "sheep_purchases": sheep_purchases,
        "sheep_placements": sheep_placements,
        "pastures_built_count": len(pastures_built),
        "sheep_feed_events": sheep_feed_events,
        "sheep_shear_events": sheep_shear_events,
        "final_sheep_count": final_sheep,
        "final_cows_count": final_cows,
        "total_melon_plantings": len(melon_plantings),
        "wave1_melon_plantings": len(wave1_melons),
        "wave2_melon_plantings": len(wave2_melons),
        "wave1_melon_details": wave1_melons,
        "wave2_melon_details": wave2_melons,
        "melon_harvests_count": len(melon_harvests),
        "worker_steps_in_field": worker_steps_in_field,
        "worker_steps_near_crops": worker_steps_near_crops,
        "delayed_harvest_opportunities": delayed_harvest_opportunities
    }

if __name__ == "__main__":
    seeds = list(range(1000, 1010))
    tasks = []
    for s in seeds:
        tasks.append(("CL", "BASELINE", s))
        tasks.append(("V2", "FROZEN_V2", s))
        tasks.append(("PRODUCE", "DROP_GE_8", s))
        tasks.append(("PRODUCE", "CAPACITY_OR_TERMINAL", s))
        
    print(f"Running Mechanics Forensics Suite ({len(tasks)} runs across 10 workers)...")
    results = defaultdict(list)
    with ProcessPoolExecutor(max_workers=10) as ex:
        futs = [ex.submit(analyze_match_forensics, t) for t in tasks]
        for f in as_completed(futs):
            res = f.result()
            key = f"{res['agent_type']}:{res['policy_name']}"
            results[key].append(res)
            
    with open("scratch/audit_mechanics_results.json", "w") as f:
        json.dump({k: v for k, v in results.items()}, f, indent=2)
        
    print("Mechanics Forensics Complete. Summary:")
    for key, lst in sorted(results.items()):
        lst.sort(key=lambda x: x["seed"])
        field_steps = np.mean([x["worker_steps_in_field"] for x in lst])
        near_crops = np.mean([x["worker_steps_near_crops"] for x in lst])
        delayed_harv = np.mean([x["delayed_harvest_opportunities"] for x in lst])
        sheeps = np.mean([x["final_sheep_count"] for x in lst])
        shears = np.mean([x["sheep_shear_events"] for x in lst])
        w1_m = np.mean([x["wave1_melon_plantings"] for x in lst])
        w2_m = np.mean([x["wave2_melon_plantings"] for x in lst])
        
        # Check cash on critical days 5, 8, 10
        d5_cash = np.mean([x["morning_cash"].get("5", 0) for x in lst])
        d8_cash = np.mean([x["morning_cash"].get("8", 0) for x in lst])
        d10_cash = np.mean([x["morning_cash"].get("10", 0) for x in lst])
        
        print(f"\n--- {key} ---")
        print(f"Morning Cash: Day 5: ${d5_cash:.1f} | Day 8: ${d8_cash:.1f} | Day 10: ${d10_cash:.1f}")
        print(f"Sheep / Wool: Final Sheep: {sheeps:.1f} | Shears: {shears:.1f}")
        print(f"Melons:       Wave 1: {w1_m:.1f} | Wave 2: {w2_m:.1f}")
        print(f"Logistics:    Field Steps: {field_steps:.1f} | Near Crops: {near_crops:.1f} | Delayed Harv Opps: {delayed_harv:.1f}")
