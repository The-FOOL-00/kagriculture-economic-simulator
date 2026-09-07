import sys, os
sys.path.insert(0, os.path.abspath('.'))
import kaggle_environments
from candidates.candidate_cl_aethel_grandmaster import agent as gm_agent
from collections import defaultdict, Counter
import json

def run_gm_forensics(seed=42):
    worker_records = []
    daily_worker_routes = defaultdict(lambda: defaultdict(list))
    
    def wrapped_gm(obs, config=None):
        step = int(obs.get("step", 0) or 0)
        day = int(obs.get("day", 0) or 0)
        hour = int(obs.get("hour", 0) or 0)
        
        farm0 = obs["farms"][0]
        farmer_pos = tuple(farm0["farmer"])
        hands_pos = [tuple(h) for h in farm0.get("hands", []) or []]
        all_workers = [farmer_pos] + hands_pos
        
        act = gm_agent(obs)
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
    env.run([wrapped_gm, "starter"])
    print(f"Simulation completed for Seed {seed}!")
    
    type_counts = Counter(r["type"] for r in worker_records)
    op_counts = Counter(r["op"] for r in worker_records)
    print(f"\n--- Grandmaster Action Breakdown ---")
    print(f"Productive: {type_counts['PROD']}")
    print(f"Movement:   {type_counts['MOVE']}")
    print(f"Idle:       {type_counts['IDLE']}")
    print(f"Total:      {len(worker_records)}")
    
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
                
    all_streaks = [s for streaks in move_streaks.values() for s in streaks]
    streak_counts = Counter(all_streaks)
    print(f"\n--- Movement Leg Distribution (Steps between productive actions) ---")
    print(f"Mean move steps between productive actions: {sum(all_streaks)/max(1, len(all_streaks)):.2f}")
    for length in sorted(streak_counts.keys())[:8]:
        cnt = streak_counts[length]
        print(f"  Leg length {length}: {cnt} times ({cnt/len(all_streaks)*100:.1f}%)")
        
    with open('scratch/gm_worker_forensics.json', 'w') as f:
        json.dump({
            "type_counts": dict(type_counts),
            "op_counts": dict(op_counts),
            "leg_distribution": dict(streak_counts)
        }, f, indent=2)
    print("\nSaved detailed statistics to scratch/gm_worker_forensics.json")

if __name__ == "__main__":
    run_gm_forensics()
