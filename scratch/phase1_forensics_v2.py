import sys, os
sys.path.insert(0, os.path.abspath('.'))
import kaggle_environments
import candidates.slot2_aethel_refined_v2 as v2_mod
from collections import defaultdict, Counter
import json

def run_v2_forensics(seed=42):
    worker_records = []
    daily_worker_routes = defaultdict(lambda: defaultdict(list))
    
    def wrapped_v2(obs, config=None):
        step = int(obs.get("step", 0) or 0)
        day = int(obs.get("day", 0) or 0)
        hour = int(obs.get("hour", 0) or 0)
        
        farm0 = obs["farms"][0]
        farmer_pos = tuple(farm0["farmer"])
        hands_pos = [tuple(h) for h in farm0.get("hands", []) or []]
        all_workers = [farmer_pos] + hands_pos
        
        act = v2_mod.agent(obs)
        f_act = act.get("farmer", ["PASS"])
        h_acts = act.get("hands", []) or []
        all_acts = [f_act] + [h_acts[i] if i < len(h_acts) else ["PASS"] for i in range(len(hands_pos))]
        
        for w_idx, (pos, a) in enumerate(zip(all_workers, all_acts)):
            op = a[0] if isinstance(a, list) and a else str(a)
            if op in ("NORTH", "SOUTH", "EAST", "WEST"):
                act_type = "MOVE"
            elif op in ("PASS", "NONE", ""):
                act_type = "IDLE"
            else:
                act_type = "PROD"
                
            worker_records.append({
                "step": step,
                "day": day,
                "hour": hour,
                "worker": w_idx,
                "pos": pos,
                "action": a,
                "op": op,
                "type": act_type
            })
            daily_worker_routes[day][w_idx].append((hour, pos, a, act_type))
            
        return act

    env = kaggle_environments.make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed})
    env.run([wrapped_v2, "starter"])
    print(f"Simulation completed for Seed {seed}!")
    
    # Analysis of V2 Forensics
    type_counts = Counter(r["type"] for r in worker_records)
    op_counts = Counter(r["op"] for r in worker_records)
    print(f"\n--- V2 Action Breakdown ---")
    print(f"Productive: {type_counts['PROD']}")
    print(f"Movement:   {type_counts['MOVE']}")
    print(f"Idle:       {type_counts['IDLE']}")
    print(f"Total:      {len(worker_records)}")
    
    print("\nTop Operations:")
    for op, cnt in op_counts.most_common(15):
        print(f"  {op:<20}: {cnt}")
        
    # Worker Specialization & Zoning
    worker_zones = defaultdict(lambda: Counter())
    worker_ops = defaultdict(lambda: Counter())
    worker_tasks = defaultdict(list)
    
    for r in worker_records:
        w = r["worker"]
        x, y = r["pos"]
        quad = "NW" if x < 5 and y < 5 else ("NE" if x >= 5 and y < 5 else ("SW" if x < 5 and y >= 5 else "SE"))
        worker_zones[w][quad] += 1
        worker_ops[w][r["op"]] += 1
        
    print(f"\n--- Worker Role & Zone Distribution ---")
    for w in sorted(worker_zones.keys()):
        tot = sum(worker_zones[w].values())
        zone_str = ", ".join(f"{q}: {cnt/tot*100:.1f}%" for q, cnt in worker_zones[w].most_common())
        top_ops = ", ".join(f"{op}: {cnt}" for op, cnt in worker_ops[w].most_common(5))
        prod = sum(cnt for op, cnt in worker_ops[w].items() if op not in ("NORTH", "SOUTH", "EAST", "WEST", "PASS", "NONE", ""))
        mv = sum(cnt for op, cnt in worker_ops[w].items() if op in ("NORTH", "SOUTH", "EAST", "WEST"))
        idl = sum(cnt for op, cnt in worker_ops[w].items() if op in ("PASS", "NONE", ""))
        print(f"Worker {w:2d} (turns {tot:3d} | Prod: {prod:3d} ({prod/tot*100:4.1f}%), Move: {mv:3d} ({mv/tot*100:4.1f}%), Idle: {idl:2d}):")
        print(f"  Zones: {zone_str}")
        print(f"  Top Ops: {top_ops}")
        
    # Analyze Task Sequencing: TSP / serpentine pattern check
    # Check how many times a worker moves to an adjacent tile and does productive work immediately vs walks multiple steps
    move_streaks = defaultdict(list)
    cur_streak = defaultdict(int)
    for r in worker_records:
        w = r["worker"]
        if r["type"] == "MOVE":
            cur_streak[w] += 1
        elif r["type"] == "PROD":
            if cur_streak[w] > 0:
                move_streaks[w].append(cur_streak[w])
                cur_streak[w] = 0
                
    print(f"\n--- Movement Leg Distribution (Steps between productive actions) ---")
    all_streaks = [s for streaks in move_streaks.values() for s in streaks]
    streak_counts = Counter(all_streaks)
    print(f"Mean move steps between productive actions: {sum(all_streaks)/max(1, len(all_streaks)):.2f}")
    for length in sorted(streak_counts.keys())[:8]:
        cnt = streak_counts[length]
        print(f"  Leg length {length}: {cnt} times ({cnt/len(all_streaks)*100:.1f}%)")
        
    # Save results
    with open('scratch/v2_worker_forensics.json', 'w') as f:
        json.dump({
            "type_counts": dict(type_counts),
            "op_counts": dict(op_counts),
            "worker_zones": {w: dict(worker_zones[w]) for w in worker_zones},
            "worker_ops": {w: dict(worker_ops[w]) for w in worker_ops},
            "leg_distribution": dict(streak_counts)
        }, f, indent=2)
    print("\nSaved detailed statistics to scratch/v2_worker_forensics.json")

if __name__ == "__main__":
    run_v2_forensics()
