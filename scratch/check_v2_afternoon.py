import sys, os
sys.path.insert(0, os.path.abspath('.'))
import kaggle_environments
import candidates.slot2_aethel_refined_v2 as v2_mod
from collections import Counter, defaultdict

def check_v2_afternoon():
    hour_actions = defaultdict(Counter)
    
    def wrapped_v2(obs, config=None):
        hour = int(obs.get("hour", 0) or 0)
        farm = obs["farms"][0]
        farmer = tuple(farm["farmer"])
        hands = [tuple(h) for h in farm.get("hands", []) or []]
        
        act = v2_mod.agent(obs)
        f_act = act.get("farmer", ["PASS"])
        h_acts = act.get("hands", []) or []
        all_acts = [f_act] + [h_acts[i] if i < len(h_acts) else ["PASS"] for i in range(len(hands))]
        
        for a in all_acts:
            op = a[0] if isinstance(a, list) and a else str(a)
            hour_actions[hour][op] += 1
        return act

    env = kaggle_environments.make("kaggriculture", configuration={"episodeSteps": 720, "seed": 42})
    env.run([wrapped_v2, "starter"])
    
    print("=== V2 Action Distribution by Hour of Day ===")
    for h in range(24):
        tot = sum(hour_actions[h].values())
        passes = hour_actions[h]["PASS"]
        moves = sum(hour_actions[h][m] for m in ("NORTH", "SOUTH", "EAST", "WEST"))
        prods = tot - passes - moves
        top_prods = ", ".join(f"{op}:{cnt}" for op, cnt in hour_actions[h].most_common(5) if op not in ("NORTH", "SOUTH", "EAST", "WEST", "PASS"))
        print(f"Hour {h:02d}: Total={tot:3d} | Prod={prods:3d} ({prods/tot*100:4.1f}%) | Move={moves:3d} | Pass={passes:3d} | Ops: {top_prods}")

if __name__ == "__main__":
    check_v2_afternoon()
