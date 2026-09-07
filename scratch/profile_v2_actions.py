import sys, os
sys.path.insert(0, os.path.abspath('.'))
import kaggle_environments
import candidates.slot2_aethel_refined_v2 as v2_mod
from collections import Counter

v2_actions = Counter()
v2_prod_actions = Counter()
v2_hires_per_day = {}

def wrapped_v2(obs, config=None):
    step = int(obs.get("step", 0) or 0)
    day = step // 24
    hour = step % 24
    act = v2_mod.agent(obs)
    f_act = act.get("farmer", ["PASS"])
    h_acts = act.get("hands", []) or []
    m_acts = act.get("market", []) or []
    
    hires = sum(1 for m in m_acts if m[0] == "HIRE")
    if hires > 0:
        v2_hires_per_day[day] = v2_hires_per_day.get(day, 0) + hires

    all_acts = [f_act] + h_acts
    for a in all_acts:
        op = a[0] if isinstance(a, list) and a else str(a)
        v2_actions[op] += 1
        if op not in ("NORTH", "SOUTH", "EAST", "WEST", "PASS"):
            v2_prod_actions[op] += 1
    return act

env = kaggle_environments.make("kaggriculture", configuration={"episodeSteps": 720, "seed": 42})
env.run([wrapped_v2, "starter"])

print("V2 Action breakdown:")
for op, cnt in v2_actions.most_common():
    print(f"  {op:<20}: {cnt}")

print("\nV2 Hires per day:")
for d, h in sorted(v2_hires_per_day.items()):
    print(f"  Day {d}: {h} hires")
