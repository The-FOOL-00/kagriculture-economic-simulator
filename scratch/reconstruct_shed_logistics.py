"""
Phase 1 & Phase 2: Shed Logistics Forensics & Event Reconstruction
==================================================================
Instruments CL-Economic-V1 across Seeds 1000–1009 to:
1. Capture every shed visit, DROP action, and PICKUP action.
2. Measure payload distributions, shed inventory over time, and trigger causes.
3. Classify each shed trip into Categories A–G.
"""

import sys
import os
import copy
import json
import time
from collections import defaultdict, Counter
import numpy as np

PROJECT_ROOT = os.path.abspath(".")
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import kaggle_environments
from candidates.candidate_cl_economic_v1 import agent as cl_agent, SHED_ACCESS

def _dist(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])

def instrument_cl_logistics(seed=1000):
    cfg = {"episodeSteps": 720, "seed": seed}
    env = kaggle_environments.make("kaggriculture", configuration=cfg, debug=False)
    env.run([cl_agent, "starter"])
    
    steps = env.steps
    total_steps = len(steps)
    
    drop_events = []
    pickup_events = []
    shed_trips = []
    
    harvest_counts = Counter()
    total_harvests = 0
    total_pickups = 0
    total_drops = 0
    total_moves = 0
    total_prods = 0
    total_idles = 0
    
    shed_occupancy_over_time = []
    
    # Track worker previous locations and shed transit
    worker_last_pos = {}
    worker_started_shed_trip = {}
    
    trip_classifications = Counter()
    
    for s_idx in range(1, total_steps):
        step = s_idx - 1
        day = step // 24
        hour = step % 24
        
        prev_f = steps[s_idx - 1][0]["observation"]["farms"][0]
        curr_f = steps[s_idx][0]["observation"]["farms"][0]
        
        prev_priv = steps[s_idx - 1][0]["observation"].get("private") or {}
        prev_shed = prev_priv.get("shed") or {}
        prev_invs = prev_priv.get("inventories") or []
        
        curr_priv = steps[s_idx][0]["observation"].get("private") or {}
        curr_shed = curr_priv.get("shed") or {}
        curr_invs = curr_priv.get("inventories") or []
        
        shed_occ = sum(int(v or 0) for v in prev_shed.values())
        shed_occupancy_over_time.append(shed_occ)
        
        act = steps[s_idx][0].get("action") or {}
        farmer_act = act.get("farmer") or ["PASS"]
        hands_act = act.get("hands") or []
        all_acts = [farmer_act] + hands_act
        
        workers = [tuple(prev_f["farmer"])] + [tuple(h) for h in prev_f["hands"]]
        
        for w_idx, a in enumerate(all_acts):
            if not a:
                total_idles += 1
                continue
            op = a[0]
            pos = workers[w_idx] if w_idx < len(workers) else (0, 0)
            
            if op in ("NORTH", "SOUTH", "EAST", "WEST"):
                total_moves += 1
            elif op in ("WATER", "HARVEST", "FEED", "CARE", "PLANT", "BUILD_PASTURE", "FERTILIZE", "COLLECT_FERTILIZER", "DIG", "DROP", "PICKUP", "PLACE"):
                total_prods += 1
            else:
                total_idles += 1
                
            if op == "HARVEST":
                total_harvests += 1
                t = prev_f["tiles"][pos[1]][pos[0]] if 0 <= pos[1] < 10 and 0 <= pos[0] < 10 else None
                if isinstance(t, dict):
                    k = t.get("kind")
                    yu = int(t.get("yield_units", 0) or 0)
                    if k == "PLANT": harvest_counts[t.get("crop")] += yu
                    elif k == "PASTURE": harvest_counts[t.get("animal")] += yu
                    
            elif op == "DROP":
                total_drops += 1
                p_inv = prev_invs[w_idx] if w_idx < len(prev_invs) else {}
                c_inv = curr_invs[w_idx] if w_idx < len(curr_invs) else {}
                drop_payload = sum(int(v or 0) for v in p_inv.values())
                
                # Classify trip
                # Check why worker was at shed
                if drop_payload >= 5:
                    cat = "A. produce drop (significant load >= 5)"
                elif drop_payload > 0 and hour >= 20:
                    cat = "F. unnecessary evening produce drop (engine auto-drops at h23)"
                elif drop_payload > 0 and _dist(pos, (4, 4)) <= 2:
                    cat = "F. unnecessary opportunistic produce drop (low payload < 5)"
                elif drop_payload == 0:
                    cat = "F. empty drop action"
                else:
                    cat = "G. unclear"
                    
                trip_classifications[cat] += 1
                drop_events.append({
                    "step": step, "day": day, "hour": hour, "worker": w_idx,
                    "pos": pos, "payload": drop_payload, "items": dict(p_inv),
                    "category": cat
                })
                
            elif op == "PICKUP":
                total_pickups += 1
                item = a[1] if len(a) > 1 else "UNKNOWN"
                qty = int(a[2]) if len(a) > 2 else 1
                
                if item in ("COW", "SHEEP"):
                    cat = "E. emergency animal placement logistics"
                elif item == "WHEAT":
                    if qty >= 6:
                        cat = "B. feed pickup (bulk batch >= 6)"
                    else:
                        cat = "F. unnecessary fragmented feed pickup (small batch < 6)"
                elif item == "FERTILIZER":
                    cat = "C. fertilizer pickup"
                else:
                    cat = "G. unclear"
                    
                trip_classifications[cat] += 1
                pickup_events.append({
                    "step": step, "day": day, "hour": hour, "worker": w_idx,
                    "pos": pos, "item": item, "qty": qty, "category": cat
                })

    final_reward = float(steps[-1][0].get("reward") or 0.0)
    final_cash = float(steps[-1][0]["observation"]["farms"][0].get("money") or 0.0)
    
    payloads = [e["payload"] for e in drop_events]
    feed_quantities = [e["qty"] for e in pickup_events if e["item"] == "WHEAT"]
    
    return {
        "seed": seed,
        "reward": final_reward,
        "terminal_cash": final_cash,
        "total_moves": total_moves,
        "total_prods": total_prods,
        "total_idles": total_idles,
        "total_harvests": total_harvests,
        "total_pickups": total_pickups,
        "total_drops": total_drops,
        "mean_drop_payload": float(np.mean(payloads)) if payloads else 0.0,
        "median_drop_payload": float(np.median(payloads)) if payloads else 0.0,
        "max_drop_payload": int(np.max(payloads)) if payloads else 0,
        "total_produce_dropped": sum(payloads),
        "total_feed_picked_up": sum(feed_quantities),
        "mean_feed_pickup_qty": float(np.mean(feed_quantities)) if feed_quantities else 0.0,
        "mean_shed_occupancy": float(np.mean(shed_occupancy_over_time)),
        "max_shed_occupancy": int(np.max(shed_occupancy_over_time)),
        "trip_classifications": dict(trip_classifications),
        "harvest_yields": dict(harvest_counts)
    }

def run_phase1_phase2_study(seeds=list(range(1000, 1010))):
    print(f"Running Phase 1 & 2 Shed Logistics Forensics on Seeds {seeds[0]}–{seeds[-1]}...")
    t0 = time.time()
    results = [instrument_cl_logistics(s) for s in seeds]
    print(f"Completed in {time.time()-t0:.1f}s.")
    
    with open("scratch/shed_logistics_raw.json", "w") as f:
        json.dump(results, f, indent=2)
        
    print("\n" + "=" * 80)
    print("PHASE 1 REPRODUCTION: CL-ECONOMIC-V1 SHED LOGISTICS (SEEDS 1000–1009)")
    print("=" * 80)
    
    rewards = [r["reward"] for r in results]
    harvests = [r["total_harvests"] for r in results]
    pickups = [r["total_pickups"] for r in results]
    drops = [r["total_drops"] for r in results]
    mean_payloads = [r["mean_drop_payload"] for r in results]
    max_payloads = [r["max_drop_payload"] for r in results]
    moves = [r["total_moves"] for r in results]
    prods = [r["total_prods"] for r in results]
    straws = [r["harvest_yields"].get("STRAWBERRY", 0) for r in results]
    wools = [r["harvest_yields"].get("SHEEP", 0) for r in results]
    wheats = [r["harvest_yields"].get("WHEAT", 0) for r in results]
    melons = [r["harvest_yields"].get("MELON", 0) for r in results]
    milks = [r["harvest_yields"].get("COW", 0) for r in results]
    feed_qties = [r["total_feed_picked_up"] for r in results]
    shed_maxes = [r["max_shed_occupancy"] for r in results]
    
    print(f"Mean Reward:             ${np.mean(rewards):10.2f} ± ${np.std(rewards):.2f}")
    print(f"HARVEST Actions:          {np.mean(harvests):8.1f} turns")
    print(f"PICKUP Actions:           {np.mean(pickups):8.1f} turns")
    print(f"DROP Actions:             {np.mean(drops):8.1f} turns")
    print(f"Mean Drop Payload:        {np.mean(mean_payloads):8.2f} units (Max: {np.mean(max_payloads):.1f})")
    print(f"Feed Picked Up:           {np.mean(feed_qties):8.1f} units")
    print(f"Movement Turns:           {np.mean(moves):8.1f} turns")
    print(f"Productive Turns:         {np.mean(prods):8.1f} turns")
    print(f"Strawberries Harvested:   {np.mean(straws):8.1f} units")
    print(f"Wool Harvested:           {np.mean(wools):8.1f} units")
    print(f"Wheat Harvested:          {np.mean(wheats):8.1f} units")
    print(f"Melon Harvested:          {np.mean(melons):8.1f} units")
    print(f"Milk Harvested:           {np.mean(milks):8.1f} units")
    print(f"Max Shed Occupancy:       {np.mean(shed_maxes):8.1f} / 100 units")
    
    print("\n" + "=" * 80)
    print("PHASE 2 SHED TRIP CAUSAL CLASSIFICATION (MEAN PER RUN)")
    print("=" * 80)
    all_cats = Counter()
    for r in results:
        for k, v in r["trip_classifications"].items():
            all_cats[k] += v / len(seeds)
            
    for cat, count in all_cats.most_common():
        print(f"  {cat:<65}: {count:6.1f} actions ({count/(np.mean(drops)+np.mean(pickups))*100:.1f}%)")

if __name__ == "__main__":
    run_phase1_phase2_study()
