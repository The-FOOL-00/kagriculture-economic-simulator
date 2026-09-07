import sys, os
sys.path.insert(0, os.path.abspath('.'))
import kaggle_environments
import candidates.slot2_aethel_refined_v2 as v2_mod
from collections import defaultdict, Counter

def analyze_v2_patterns():
    worker_traces = defaultdict(list)
    
    def wrapped_v2(obs, config=None):
        farm0 = obs["farms"][0]
        farmer_pos = tuple(farm0["farmer"])
        hands_pos = [tuple(h) for h in farm0.get("hands", []) or []]
        all_workers = [farmer_pos] + hands_pos
        
        act = v2_mod.agent(obs)
        f_act = act.get("farmer", ["PASS"])
        h_acts = act.get("hands", []) or []
        all_acts = [f_act] + [h_acts[i] if i < len(h_acts) else ["PASS"] for i in range(len(hands_pos))]
        
        step = int(obs.get("step", 0) or 0)
        day = step // 24
        hour = step % 24
        
        for w_idx, (pos, a) in enumerate(zip(all_workers, all_acts)):
            op = a[0] if isinstance(a, list) and a else str(a)
            worker_traces[w_idx].append({
                "step": step, "day": day, "hour": hour, "pos": pos, "action": a, "op": op
            })
        return act

    env = kaggle_environments.make("kaggriculture", configuration={"episodeSteps": 720, "seed": 42})
    env.run([wrapped_v2, "starter"])
    
    print("=== Analyzing V2 Worker Daily Routines ===")
    for d in [1, 2, 3, 5, 10]:
        print(f"\n--- Day {d} Worker 0 (Farmer) ---")
        day_steps = [r for r in worker_traces[0] if r["day"] == d]
        route_str = []
        for r in day_steps:
            op = r["op"]
            if op in ("NORTH", "SOUTH", "EAST", "WEST", "PASS"):
                route_str.append(f"{op[:1]}->{r['pos']}")
            else:
                route_str.append(f"[{op}@{r['pos']}]")
        print(" ".join(route_str[:12]))
        print(" ".join(route_str[12:24]))
        
    for d in [2, 5, 10]:
        print(f"\n--- Day {d} Worker 1 (First Hand) ---")
        day_steps = [r for r in worker_traces[1] if r["day"] == d]
        route_str = []
        for r in day_steps:
            op = r["op"]
            if op in ("NORTH", "SOUTH", "EAST", "WEST", "PASS"):
                route_str.append(f"{op[:1]}->{r['pos']}")
            else:
                route_str.append(f"[{op}@{r['pos']}]")
        print(" ".join(route_str[:12]))
        print(" ".join(route_str[12:24]))

if __name__ == "__main__":
    analyze_v2_patterns()
