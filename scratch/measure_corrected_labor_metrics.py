import sys
import os
import json
from collections import defaultdict
import numpy as np
from concurrent.futures import ProcessPoolExecutor
import kaggle_environments

sys.path.insert(0, os.path.abspath('.'))

import candidates.candidate_cl_fert_gated as m1_module
from scratch.counterfactual_policies_w1_w7 import BaseQ50Agent

MOVES = {"NORTH", "SOUTH", "EAST", "WEST"}

def process_one_seed(args):
    ag_name, seed = args
    if ag_name == "M1":
        agent = m1_module.ClosedLoopEconomicV1()
    else:
        agent = BaseQ50Agent(50)

    cfg = {"episodeSteps": 720, "seed": seed}
    env = kaggle_environments.make("kaggriculture", configuration=cfg)
    steps = env.run([agent, "starter"])

    seed_metrics = defaultdict(list)

    for s_idx in range(7 * 24, 19 * 24):
        obs = steps[s_idx][0]["observation"]
        farm = obs.get("farms", [{}, {}])[0]
        tiles = farm.get("tiles", [])
        
        farmer = farm.get("farmer")
        hands = farm.get("hands") or []
        all_workers = [farmer] + hands
        n_workers = len(all_workers)

        p0_act = steps[s_idx][0].get("action") or {}
        f_act = p0_act.get("farmer")
        h_acts = p0_act.get("hands") or []
        all_actions = [f_act] + h_acts

        used_slots = 0
        transit_slots = 0
        productive_slots = 0
        idle_slots = 0

        for act in all_actions:
            op = act[0] if (act and isinstance(act, list) and len(act) > 0) else "PASS"
            if op in MOVES:
                used_slots += 1
                transit_slots += 1
            elif op != "PASS":
                used_slots += 1
                productive_slots += 1
            else:
                idle_slots += 1

        urgent_unwatered = 0
        normal_unwatered = 0
        ripe_straw_capped = 0
        hungry_animals_urgent = 0

        for r in range(len(tiles)):
            for c in range(len(tiles[r])):
                t = tiles[r][c]
                if not isinstance(t, dict): continue
                k = t.get("kind")
                if k == "PLANT":
                    crop = t.get("crop")
                    yu = t.get("yield_units", 0)
                    if crop == "STRAWBERRY" and yu >= 2:
                        ripe_straw_capped += 1
                    if not t.get("watered_today"):
                        if t.get("consecutive_unwatered", 0) >= 1:
                            urgent_unwatered += 1
                        else:
                            normal_unwatered += 1
                elif k == "PASTURE" and t.get("animal"):
                    if not t.get("fed_today") and t.get("consecutive_unfed", 0) >= 1:
                        hungry_animals_urgent += 1

        urgent_demand = urgent_unwatered + hungry_animals_urgent + ripe_straw_capped
        unmet_hours = max(0, (urgent_demand + normal_unwatered) - n_workers)

        seed_metrics["capacity"].append(n_workers)
        seed_metrics["used"].append(used_slots)
        seed_metrics["transit"].append(transit_slots)
        seed_metrics["productive"].append(productive_slots)
        seed_metrics["idle"].append(idle_slots)
        seed_metrics["urgent_demand"].append(urgent_demand)
        seed_metrics["unmet_hours"].append(unmet_hours)

    return ag_name, seed, {k: float(np.mean(v)) for k, v in seed_metrics.items()}

def main():
    seeds = list(range(1250, 1280))
    jobs = [(ag, s) for ag in ["M1", "Q50"] for s in seeds]
    metrics = {"M1": defaultdict(list), "Q50": defaultdict(list)}

    with ProcessPoolExecutor(max_workers=11) as ex:
        for ag_name, s, sm in ex.map(process_one_seed, jobs, chunksize=2):
            for k, val in sm.items():
                metrics[ag_name][k].append(val)

    results = {}
    for ag in ["M1", "Q50"]:
        results[ag] = {k: float(np.mean(v)) for k, v in metrics[ag].items()}

    print(json.dumps(results, indent=2))
    with open("scratch/corrected_labor_metrics.json", "w") as f:
        json.dump(results, f, indent=2)

if __name__ == "__main__":
    main()
