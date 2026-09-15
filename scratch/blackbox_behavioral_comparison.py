"""
Black-Box Behavioral Comparison: CL-Economic-V1 vs Frozen V2
============================================================
Analyzes:
1. Complete opcode action distribution
2. Pickup / Drop logistics breakdown (what items are being picked up and dropped, and where?)
3. Harvest frequency and yield batching
4. Physical tile layout and crop counts
"""
import sys
import os
from collections import defaultdict, Counter
import json
import kaggle_environments

PROJECT_ROOT = os.path.abspath(".")
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from candidates.slot2_aethel_refined_v2 import agent as v2
from candidates.candidate_cl_economic_v1 import agent as cl

def profile_agent(agent_fn, seed=1000):
    env = kaggle_environments.make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed})
    env.run([agent_fn, "starter"])
    
    op_counts = Counter()
    pickup_items = Counter()
    pickup_batches = defaultdict(list)
    drop_counts = 0
    harvest_crops = Counter()
    
    # Track inventory loads at drop
    drop_loads = []
    
    for s_idx in range(1, len(env.steps)):
        act = env.steps[s_idx][0].get("action", {})
        all_acts = [act.get("farmer", [])] + act.get("hands", [])
        prev_f = env.steps[s_idx - 1][0]["observation"]["farms"][0]
        workers = [prev_f["farmer"]] + prev_f["hands"]
        priv = env.steps[s_idx - 1][0]["observation"].get("private", {})
        invs = priv.get("inventories", [])
        
        for w_idx, a in enumerate(all_acts):
            if not a:
                op_counts["PASS"] += 1
                continue
            op = a[0]
            op_counts[op] += 1
            
            if op == "PICKUP":
                item = a[1] if len(a) > 1 else "UNKNOWN"
                qty = int(a[2]) if len(a) > 2 else 1
                pickup_items[item] += qty
                pickup_batches[item].append(qty)
            elif op == "DROP":
                drop_counts += 1
                if w_idx < len(invs):
                    inv = invs[w_idx]
                    load = sum(inv.values())
                    drop_loads.append(load)
            elif op == "HARVEST":
                if w_idx < len(workers):
                    pos = workers[w_idx]
                    t = prev_f["tiles"][pos[1]][pos[0]]
                    if isinstance(t, dict):
                        k = t.get("kind")
                        if k == "PLANT": harvest_crops[t.get("crop")] += int(t.get("yield_units", 0) or 0)
                        elif k == "PASTURE": harvest_crops[t.get("animal")] += int(t.get("yield_units", 0) or 0)
                        
    return {
        "op_counts": dict(op_counts),
        "pickup_items": dict(pickup_items),
        "mean_pickup_batch": {k: float(sum(v)/len(v)) for k, v in pickup_batches.items()},
        "drop_counts": drop_counts,
        "mean_drop_load": float(sum(drop_loads)/len(drop_loads)) if drop_loads else 0.0,
        "harvest_yields": dict(harvest_crops)
    }

if __name__ == "__main__":
    print("Profiling Frozen V2...")
    v2_prof = profile_agent(v2, 1000)
    print("Profiling CL-Economic-V1...")
    cl_prof = profile_agent(cl, 1000)
    
    print("\n" + "=" * 75)
    print(f"{'Opcode':<20} | {'CL-Economic-V1':<18} | {'Frozen V2':<18} | {'Delta':<12}")
    print("-" * 75)
    all_ops = set(cl_prof["op_counts"].keys()) | set(v2_prof["op_counts"].keys())
    for op in sorted(all_ops, key=lambda x: cl_prof["op_counts"].get(x, 0), reverse=True):
        c_val = cl_prof["op_counts"].get(op, 0)
        v_val = v2_prof["op_counts"].get(op, 0)
        print(f"{op:<20} | {c_val:18d} | {v_val:18d} | {v_val - c_val:+12d}")
        
    print("\n--- LOGISTICS COMPARISON ---")
    print(f"CL Pickups: {cl_prof['pickup_items']} (Batch means: {cl_prof['mean_pickup_batch']})")
    print(f"V2 Pickups: {v2_prof['pickup_items']} (Batch means: {v2_prof['mean_pickup_batch']})")
    print(f"CL Drops: {cl_prof['drop_counts']} drops, Mean Load: {cl_prof['mean_drop_load']:.1f} units")
    print(f"V2 Drops: {v2_prof['drop_counts']} drops, Mean Load: {v2_prof['mean_drop_load']:.1f} units")
    print(f"CL Harvest Yield: {cl_prof['harvest_yields']}")
    print(f"V2 Harvest Yield: {v2_prof['harvest_yields']}")
