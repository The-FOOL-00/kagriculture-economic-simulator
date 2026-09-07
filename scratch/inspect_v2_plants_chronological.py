import sys, os
sys.path.insert(0, os.path.abspath('.'))
import kaggle_environments
from candidates.slot2_aethel_refined_v2 import agent as v2_agent

env = kaggle_environments.make("kaggriculture", configuration={"episodeSteps": 720, "seed": 42})
env.run([v2_agent, lambda obs, cfg: {}])

print("V2 Planting Events (Day, Hour, Pos, Crop):")
for s in range(720):
    farm = env.steps[s][0]['observation']['farms'][0]
    farmer = tuple(farm["farmer"])
    hands = [tuple(h) for h in farm.get("hands", []) or []]
    workers = [farmer] + hands
    
    act = env.steps[s][0]['action'] or {}
    f_act = act.get("farmer", ["PASS"])
    h_acts = act.get("hands", []) or []
    all_acts = [f_act] + h_acts
    
    for w_i, (pos, a) in enumerate(zip(workers, all_acts)):
        if isinstance(a, list) and len(a) >= 2 and a[0] == "PLANT":
            crop = a[1]
            day = s // 24
            hr = s % 24
            print(f"  Day {day:2d}, Hr {hr:2d}: Worker {w_i:2d} at {pos} -> PLANT {crop}")
