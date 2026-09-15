"""
Exact Strawberry Production Loss Accounting: Reconstructing every cycle
Tracks for every cycle of every bush:
- Was it watered on cycle night?
- Was it fertilized on cycle night?
- What was yield_units immediately before cycle?
- How many units were added vs theoretical +2?
- How many units were clipped by min(4, ...)?
- How many units were left unharvested at step 719?
"""
import sys
import os
import copy
from collections import defaultdict
import numpy as np

PROJECT_ROOT = os.path.abspath(".")
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import kaggle_environments
from candidates.candidate_cl_economic_v1 import ClosedLoopEconomicV1
import candidates.slot2_aethel_refined_v2 as v2_mod

TPD = 24

def audit_seed_strawberry_accounting(seed, agent_name):
    if agent_name == "CL":
        agent_fn = ClosedLoopEconomicV1()
    else:
        agent_fn = v2_mod.agent

    cfg = {"episodeSteps": 720, "seed": seed}
    env = kaggle_environments.make("kaggriculture", configuration=cfg, debug=False)
    env.run([agent_fn, "starter"])
    steps = env.steps

    # Track all bushes
    bushes = {} # (x, y) -> {"planted_day": d, "planted_step": s}
    
    # Loss categories
    unwatered_cycle_loss = 0     # lost 1 unit because not watered (so no fert bonus)
    unfertilized_cycle_loss = 0   # lost 1 unit because watered but not fertilized
    cap_overflow_loss = 0         # lost units because min(4, yu + bonus) capped
    decay_loss = 0                # lost units because step >= max_lifespan_step
    harvested_total = 0

    # Track step-by-step
    for s_idx in range(1, len(steps)):
        prev_obs = steps[s_idx - 1][0]["observation"]
        curr_obs = steps[s_idx][0]["observation"]
        act = steps[s_idx][0].get("action") or {}

        step = prev_obs.get("step", s_idx - 1)
        day = prev_obs.get("day", step // TPD)
        hour = prev_obs.get("hour", step % TPD)

        prev_f = prev_obs["farms"][0]
        curr_f = curr_obs["farms"][0]
        prev_tiles = prev_f["tiles"]
        curr_tiles = curr_f["tiles"]

        # Track harvests
        farmer_act = act.get("farmer") or ["PASS"]
        hands_act = act.get("hands") or []
        all_acts = [farmer_act] + hands_act
        prev_farmer = tuple(prev_f["farmer"])
        prev_hands = [tuple(h) for h in (prev_f.get("hands") or [])]
        prev_workers = [prev_farmer] + prev_hands

        for w_idx, a in enumerate(all_acts):
            if a and a[0] == "HARVEST":
                fx, fy = prev_workers[w_idx] if w_idx < len(prev_workers) else (4, 4)
                t = prev_tiles[fy][fx]
                if isinstance(t, dict) and t.get("crop") == "STRAWBERRY":
                    harvested_total += t.get("yield_units", 0)

        # Track new plantings
        for w_idx, a in enumerate(all_acts):
            if a and a[0] == "PLANT" and len(a) > 1 and a[1] == "STRAWBERRY":
                fx, fy = prev_workers[w_idx] if w_idx < len(prev_workers) else (4, 4)
                bushes[(fx, fy)] = {"planted_day": day, "planted_step": step}

        # Check day transition (hour 23 -> hour 0 of next day)
        if hour == 23:
            next_day = day + 1
            for (bx, by), binfo in list(bushes.items()):
                prev_t = prev_tiles[by][bx]
                curr_t = curr_tiles[by][bx]
                if not (isinstance(prev_t, dict) and prev_t.get("crop") == "STRAWBERRY"):
                    continue
                
                # Check if this night was a production cycle for this bush
                pday = binfo["planted_day"]
                days_since_first = next_day - pday - 10
                if days_since_first >= 0 and days_since_first % 2 == 0:
                    prod_count = days_since_first // 2 + 1
                    if prod_count <= 4:
                        # Production cycle occurred!
                        was_watered = prev_t.get("watered_today", False)
                        is_fert = was_watered and (prev_t.get("fertilized_until_day", -1) >= day)
                        prev_yu = prev_t.get("yield_units", 0)
                        
                        expected_bonus = 2 if is_fert else 1
                        ideal_bonus = 2

                        if not was_watered:
                            unwatered_cycle_loss += 1
                        elif not is_fert:
                            unfertilized_cycle_loss += 1

                        # Cap overflow:
                        if prev_yu + expected_bonus > 4:
                            cap_overflow_loss += (prev_yu + expected_bonus - 4)

        # Check decay during the day (from decay_plants: if mls >= 0 and step >= mls and (step-mls)%2 == 0)
        # We can observe this if yield_units decreased between steps without a HARVEST action
        # Let's verify by checking curr_t vs prev_t on non-harvest steps
        for (bx, by), binfo in list(bushes.items()):
            prev_t = prev_tiles[by][bx]
            curr_t = curr_tiles[by][bx]
            if isinstance(prev_t, dict) and isinstance(curr_t, dict) and prev_t.get("crop") == "STRAWBERRY":
                harvest_here = False
                for w_idx, a in enumerate(all_acts):
                    if a and a[0] == "HARVEST":
                        fx, fy = prev_workers[w_idx] if w_idx < len(prev_workers) else (4, 4)
                        if (fx, fy) == (bx, by):
                            harvest_here = True
                if not harvest_here and hour != 23: # not night refresh
                    if curr_t.get("yield_units", 0) < prev_t.get("yield_units", 0):
                        decay_loss += (prev_t.get("yield_units", 0) - curr_t.get("yield_units", 0))

    # At final step (step 719), check unharvested units left on bushes
    final_tiles = steps[-1][0]["observation"]["farms"][0]["tiles"]
    unharvested_final = 0
    for y in range(10):
        for x in range(10):
            t = final_tiles[y][x]
            if isinstance(t, dict) and t.get("crop") == "STRAWBERRY":
                unharvested_final += t.get("yield_units", 0)

    return {
        "seed": seed,
        "agent": agent_name,
        "harvested": harvested_total,
        "unwatered_cycle_loss": unwatered_cycle_loss,
        "unfertilized_cycle_loss": unfertilized_cycle_loss,
        "cap_overflow_loss": cap_overflow_loss,
        "decay_loss": decay_loss,
        "unharvested_final": unharvested_final
    }

if __name__ == "__main__":
    print("Running exact loss accounting across Seeds 1000-1009...")
    seeds = list(range(1000, 1010))
    cl_results = [audit_seed_strawberry_accounting(s, "CL") for s in seeds]
    v2_results = [audit_seed_strawberry_accounting(s, "V2") for s in seeds]

    print(f"\n{'Metric':<32} | {'CL Mean':<12} {'V2 Mean':<12} {'Delta (V2 - CL)':<15}")
    print("-" * 75)
    for m in [
        "harvested",
        "unwatered_cycle_loss",
        "unfertilized_cycle_loss",
        "cap_overflow_loss",
        "decay_loss",
        "unharvested_final"
    ]:
        cl_val = np.mean([r[m] for r in cl_results])
        v2_val = np.mean([r[m] for r in v2_results])
        print(f"{m:<32} | {cl_val:<12.2f} {v2_val:<12.2f} {v2_val - cl_val:<+15.2f}")
