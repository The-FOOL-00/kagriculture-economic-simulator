"""
Phase 4 & Phase 8: Controlled Selective Irrigation Ablation Study
================================================================
Compares 5 Controlled Watering Policies on matched Seeds 1000–1009 (50 matches total):

ARM A: Baseline CL-Economic-V1 (waters all plants every day)
ARM B: Skip-Mature (skips non-ongoing crops at max_yield when consecutive_unwatered == 0)
ARM C: Late-Cycle Selective (skips Day 29 watering and non-yielding late crops)
ARM D: Strawberry-Sync (skips mature strawberries on off-production days when safe)
ARM E: State-Derived Integrated (combines all state-derived value filters)
"""

import sys
import os
import copy
import json
import time
from collections import defaultdict, Counter
import numpy as np
from concurrent.futures import ProcessPoolExecutor, as_completed

PROJECT_ROOT = os.path.abspath(".")
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import kaggle_environments
from candidates.candidate_cl_economic_v1 import (
    ClosedLoopEconomicV1, BOARD, TPD, SHED_ACCESS, WELL_ACCESS,
    CROPS_DEF, PASTURE_SLOTS, PASTURE_SPECIES, MELON_TILES_D0,
    MELON_DESIGNATED_TILES, WHEAT_TILES_D0, SELLABLE, PRODUCE_TO_DROP,
    BASE_PRICES, MOVES, _dist, _quad, _nearest_shed, _bfs_step,
    min_cost_bipartite_matching
)

class SelectiveWateringAgent(ClosedLoopEconomicV1):
    def __init__(self, watering_policy="BASELINE"):
        super().__init__()
        self.watering_policy = watering_policy

    def _scan_field(self, tiles, quads, seeds, shed, invs, day):
        # Run parent scan_field first
        scan_res = super()._scan_field(tiles, quads, seeds, shed, invs, day)
        
        if self.watering_policy == "BASELINE":
            return scan_res

        # Filter unwatered crops based on observable state
        filtered_unwatered = []
        # urgent_unwatered (consecutive_unwatered >= 1) is ALWAYS protected in all policies!
        urgent_unwatered = scan_res["urgent_unwatered"]

        for pos in scan_res["unwatered"]:
            x, y = pos
            t = tiles[y][x]
            if not (isinstance(t, dict) and t.get("kind") == "PLANT"):
                continue
                
            crop = t.get("crop")
            c_def = CROPS_DEF.get(crop, {})
            age = day - int(t.get("planted_day", 0) or 0)
            yu = int(t.get("yield_units", 0) or 0)
            max_y = c_def.get("max_yield", 4)
            max_yd = c_def.get("max_yield_day", 4)
            ongoing = c_def.get("ongoing", False)
            p_day = int(t.get("planted_day", 0) or 0)
            
            should_water = True
            
            if self.watering_policy == "SKIP_MATURE":
                # ARM B: Skip non-ongoing crops that have already achieved max_yield
                if not ongoing and yu >= max_y:
                    should_water = False
                    
            elif self.watering_policy == "LATE_CYCLE":
                # ARM C: Skip watering on Day 29 (cannot yield before game end at step 720)
                if day >= 29:
                    should_water = False
                elif not ongoing and day >= 27 and age >= max_yd:
                    should_water = False

            elif self.watering_policy == "STRAWBERRY_SYNC":
                # ARM D: Skip mature strawberries on off-production days
                if ongoing and crop == "STRAWBERRY" and age >= 10:
                    is_prod_day = ((day - p_day - 10) % 2 == 0)
                    if not is_prod_day:
                        should_water = False

            elif self.watering_policy == "STATE_DERIVED":
                # ARM E: Integrated state-derived value filter
                # 1. Day 29: Zero terminal value for any new water action
                if day >= 29:
                    should_water = False
                # 2. Non-ongoing at max yield: Zero incremental yield
                elif not ongoing and yu >= max_y:
                    should_water = False
                # 3. Non-ongoing past max yield day: Zero incremental yield
                elif not ongoing and age >= max_yd:
                    should_water = False
                # 4. Mature strawberries on off-production days: Zero yield today, safe to defer
                elif ongoing and crop == "STRAWBERRY" and age >= 10:
                    is_prod_day = ((day - p_day - 10) % 2 == 0)
                    if not is_prod_day:
                        should_water = False

            if should_water:
                filtered_unwatered.append(pos)

        scan_res["unwatered"] = filtered_unwatered
        return scan_res


def run_ablation_match(args):
    arm_name, seed = args
    from scratch.run_protocol_phase1 import run_single_seed_metrics
    agent_factory = lambda: SelectiveWateringAgent(watering_policy=arm_name)
    res = run_single_seed_metrics(seed, agent_cls_factory=agent_factory)
    res["arm"] = arm_name
    return res


def run_watering_pilot(seeds=list(range(1000, 1010))):
    arms = [
        "BASELINE",
        "SKIP_MATURE",
        "LATE_CYCLE",
        "STRAWBERRY_SYNC",
        "STATE_DERIVED"
    ]
    
    tasks = []
    for arm in arms:
        for s in seeds:
            tasks.append((arm, s))
            
    print(f"Running Phase 8 Controlled Watering Pilot across {len(seeds)} Seeds (50 matches total)...")
    t0 = time.time()
    results = defaultdict(list)
    with ProcessPoolExecutor(max_workers=10) as ex:
        futs = [ex.submit(run_ablation_match, t) for t in tasks]
        for f in as_completed(futs):
            res = f.result()
            results[res["arm"]].append(res)
            
    print(f"Completed in {time.time()-t0:.1f}s.")
    
    with open("scratch/watering_pilot_results.json", "w") as f:
        save_dict = {arm: [r for r in lst] for arm, lst in results.items()}
        json.dump(save_dict, f, indent=2)
        
    print("\n" + "=" * 105)
    print(f"{'ARM':<18} | {'Reward ($)':<16} | {'Moves':<8} | {'Prod':<8} | {'Idle':<8} | {'Straw':<7} | {'Wool':<7} | {'Milk':<7} | {'Water%':<7} | {'Care%':<7}")
    print("-" * 105)
    
    summary = {}
    for arm in arms:
        lst = results[arm]
        lst.sort(key=lambda x: x["seed"])
        rewards = [r["reward"] for r in lst]
        moves = [r["movement_turns"] for r in lst]
        prods = [r["productive_turns"] for r in lst]
        idles = [r["idle_turns"] for r in lst]
        straws = [r["strawberry_harvested"] for r in lst]
        wools = [r["wool_harvested"] for r in lst]
        wheats = [r["wheat_harvested"] for r in lst]
        milks = [r["milk_harvested"] for r in lst]
        waters = [r["watering_completion"] * 100 for r in lst]
        cares = [r["animal_care_completion"] * 100 for r in lst]
        
        m_rew = float(np.mean(rewards))
        m_mov = float(np.mean(moves))
        m_prd = float(np.mean(prods))
        m_str = float(np.mean(straws))
        m_wol = float(np.mean(wools))
        
        summary[arm] = {
            "mean_reward": m_rew,
            "std_reward": float(np.std(rewards)),
            "median_reward": float(np.median(rewards)),
            "mean_moves": m_mov,
            "mean_prods": m_prd,
            "mean_idles": float(np.mean(idles)),
            "mean_straw": m_str,
            "mean_wool": m_wol,
            "mean_wheat": float(np.mean(wheats)),
            "mean_milk": float(np.mean(milks)),
            "mean_water_pct": float(np.mean(waters)),
            "mean_care_pct": float(np.mean(cares)),
        }
        
        print(f"{arm:<18} | ${m_rew:10.2f} ± ${np.std(rewards):5.0f} | {m_mov:8.1f} | {m_prd:8.1f} | {float(np.mean(idles)):8.1f} | {m_str:7.1f} | {m_wol:7.1f} | {float(np.mean(milks)):7.1f} | {float(np.mean(waters)):6.1f}% | {float(np.mean(cares)):6.1f}%")
        
    with open("scratch/watering_pilot_summary.json", "w") as f:
        json.dump(summary, f, indent=2)

if __name__ == "__main__":
    run_watering_pilot()
