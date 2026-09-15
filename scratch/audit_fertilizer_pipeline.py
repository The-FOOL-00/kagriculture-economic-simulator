"""
Fertilizer Pipeline Audit: CL vs V2 across Seeds 1000-1009
Measures:
- Fertilizer collected from animals
- Fertilizer sold on market
- Fertilizer applied to strawberries
- Fertilizer applied to other crops (wheat, melons, etc.)
- Waste / unused fertilizer
"""
import sys
import os
import json
from collections import defaultdict
import numpy as np

PROJECT_ROOT = os.path.abspath(".")
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import kaggle_environments
from candidates.candidate_cl_economic_v1 import ClosedLoopEconomicV1
import candidates.slot2_aethel_refined_v2 as v2_mod

TPD = 24

def audit_fert_seed(seed, agent_name):
    if agent_name == "CL":
        agent_fn = ClosedLoopEconomicV1()
    else:
        agent_fn = v2_mod.agent

    cfg = {"episodeSteps": 720, "seed": seed}
    env = kaggle_environments.make("kaggriculture", configuration=cfg, debug=False)
    env.run([agent_fn, "starter"])
    steps = env.steps

    collected = 0
    applied_straw = 0
    applied_melon = 0
    applied_wheat = 0
    applied_other = 0
    sold_market = 0

    for s_idx in range(1, len(steps)):
        prev_obs = steps[s_idx - 1][0]["observation"]
        act = steps[s_idx][0].get("action") or {}

        prev_f = prev_obs["farms"][0]
        prev_tiles = prev_f["tiles"]
        farmer_act = act.get("farmer") or ["PASS"]
        hands_act = act.get("hands") or []
        all_acts = [farmer_act] + hands_act

        prev_farmer = tuple(prev_f["farmer"])
        prev_hands = [tuple(h) for h in (prev_f.get("hands") or [])]
        prev_workers = [prev_farmer] + prev_hands

        # Market
        for o in act.get("market") or []:
            if isinstance(o, list) and len(o) > 2 and o[0] == "SELL" and o[1] == "FERTILIZER":
                sold_market += int(o[2])

        # Workers
        for w_idx, a in enumerate(all_acts):
            if not a:
                continue
            op = a[0]
            fx, fy = prev_workers[w_idx] if w_idx < len(prev_workers) else (4, 4)
            t = prev_tiles[fy][fx]

            if op == "COLLECT_FERTILIZER":
                collected += 1
            elif op == "FERTILIZE":
                if isinstance(t, dict) and t.get("kind") == "PLANT":
                    crop = t.get("crop")
                    if crop == "STRAWBERRY":
                        applied_straw += 1
                    elif crop == "MELON":
                        applied_melon += 1
                    elif crop == "WHEAT":
                        applied_wheat += 1
                    else:
                        applied_other += 1

    final_shed_fert = steps[-1][0]["observation"]["private"]["shed"].get("FERTILIZER", 0)

    return {
        "collected": collected,
        "sold_market": sold_market,
        "applied_straw": applied_straw,
        "applied_melon": applied_melon,
        "applied_wheat": applied_wheat,
        "applied_other": applied_other,
        "final_shed_fert": final_shed_fert
    }

if __name__ == "__main__":
    print("Auditing fertilizer pipeline across Seeds 1000-1009...")
    seeds = list(range(1000, 1010))
    cl_res = [audit_fert_seed(s, "CL") for s in seeds]
    v2_res = [audit_fert_seed(s, "V2") for s in seeds]

    print(f"\n{'Fertilizer Metric':<30} | {'CL Mean':<12} {'V2 Mean':<12} {'Delta (V2 - CL)':<15}")
    print("-" * 75)
    for m in [
        "collected",
        "applied_straw",
        "applied_melon",
        "applied_wheat",
        "applied_other",
        "sold_market",
        "final_shed_fert"
    ]:
        cl_v = np.mean([r[m] for r in cl_res])
        v2_v = np.mean([r[m] for r in v2_res])
        print(f"{m:<30} | {cl_v:<12.2f} {v2_v:<12.2f} {v2_v - cl_v:<+15.2f}")
