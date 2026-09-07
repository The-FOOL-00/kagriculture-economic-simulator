import sys, os
sys.path.insert(0, os.path.abspath('.'))
import kaggle_environments
import candidates.slot2_aethel_refined_v2 as v2_mod
from collections import defaultdict, Counter

def check_v2_animal_workers():
    worker_ops = defaultdict(Counter)
    def wrapped_v2(obs, config=None):
        farm = obs["farms"][0]
        farmer = tuple(farm["farmer"])
        hands = [tuple(h) for h in farm.get("hands", []) or []]
        act = v2_mod.agent(obs)
        f_act = act.get("farmer", ["PASS"])
        h_acts = act.get("hands", []) or []
        all_acts = [f_act] + [h_acts[i] if i < len(h_acts) else ["PASS"] for i in range(len(hands))]
        for w_i, a in enumerate(all_acts):
            op = a[0] if isinstance(a, list) and a else str(a)
            worker_ops[w_i][op] += 1
        return act
    env = kaggle_environments.make("kaggriculture", configuration={"episodeSteps": 720, "seed": 42})
    env.run([wrapped_v2, "starter"])
    
    print("=== V2 Livestock Chores by Worker ===")
    for w_i in sorted(worker_ops.keys()):
        feeds = worker_ops[w_i]["FEED"]
        cares = worker_ops[w_i]["CARE"]
        ferts = worker_ops[w_i]["COLLECT_FERTILIZER"]
        waters = worker_ops[w_i]["WATER"]
        tot = sum(worker_ops[w_i].values())
        print(f"Worker {w_i:2d} (tot {tot:3d}): FEED={feeds:3d} | CARE={cares:3d} | FERT={ferts:3d} | WATER={waters:3d}")

if __name__ == "__main__":
    check_v2_animal_workers()
