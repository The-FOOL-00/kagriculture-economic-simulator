import sys
import os
import json
from collections import defaultdict
import numpy as np

sys.path.insert(0, os.path.abspath('.'))

import candidates.candidate_cl_fert_gated as m1_module
from scratch.run_wheat_quota_sweep_50seeds import ParameterizedQuotaAgent
import kaggle_environments

# Approximate theoretical gross marginal values
TASK_NOMINAL_VALUE = {
    "URGENT_WATER": 200.0,       # Avoids death to weed ($120-250 loss)
    "HARVEST_STRAWBERRY": 240.0, # 2 units * $120
    "HARVEST_MILK": 160.0,       # 1 unit milk
    "HARVEST_WOOL": 200.0,       # 1 unit wool
    "FEED": 120.0,               # Prevents skipped production cycle
    "CARE": 120.0,               # Animal happiness / production cycle
    "HARVEST_MELON": 250.0,      # Yield / batch
    "WATER_CROPS": 50.0,         # Normal maintenance
    "HARVEST_WHEAT": 100.0,      # 4 units * $25
    "PLANT_STRAWBERRY": 80.0,    # Future yield NPV
    "PLANT_MELON": 60.0,
    "BUILD_PASTURE": 25.0,       # Future animal slot NPV
    "CLEAR_OBSTACLE": 10.0,      # Land unblocking NPV
    "PLANT_WHEAT": 15.0,
    "MOVE": 0.0,
    "IDLE": 0.0
}

def analyze_opportunity_costs_trajectory(seed):
    cfg = {"episodeSteps": 720, "seed": seed}
    env = kaggle_environments.make("kaggriculture", configuration=cfg)
    steps = env.run([ParameterizedQuotaAgent(50), "starter"])

    opp_cost_events = []
    pasture_while_sb_ripe = 0
    clearing_while_sb_ripe = 0
    sb_while_critical_care = 0

    missed_reward_pasture_clearing = []
    missed_reward_sb_care = []

    for s_idx in range(len(steps)):
        obs = steps[s_idx][0]["observation"]
        day = obs["day"]
        hour = obs["hour"]
        if not (8 <= day <= 14):
            continue

        farm0 = obs["farms"][0]
        tiles = farm0["tiles"]
        workers = [farm0.get("farmer")] + (farm0.get("hands") or [])

        # Check pending tasks on field
        pending_ripe_sb = []
        pending_urgent_water = []
        pending_care = []
        pending_feed = []

        for r in range(len(tiles)):
            for c in range(len(tiles[r])):
                t = tiles[r][c]
                pos = (c, r)
                if isinstance(t, dict):
                    k = t.get("kind")
                    if k == "PLANT":
                        crop = t.get("crop")
                        yu = t.get("yield_units", 0)
                        if crop == "STRAWBERRY" and yu >= 2:
                            pending_ripe_sb.append(pos)
                        if not t.get("watered_today") and t.get("consecutive_unwatered", 0) >= 1:
                            pending_urgent_water.append(pos)
                    elif k == "PASTURE" and t.get("animal"):
                        if not t.get("cared_today"): pending_care.append(pos)
                        if not t.get("fed_today"): pending_feed.append(pos)

        act = steps[s_idx][0].get("action") or {}
        all_acts = [act.get("farmer")] + (act.get("hands") or [])

        for w_idx, a in enumerate(all_acts):
            if not a or not isinstance(a, list):
                continue
            op = a[0]
            w_pos = workers[w_idx] if w_idx < len(workers) else None
            t = tiles[w_pos[1]][w_pos[0]] if (w_pos and w_pos[1] < len(tiles) and w_pos[0] < len(tiles[w_pos[1]])) else None

            # Check case: Worker performs pasture/clearing work while ripe strawberry exists
            if op in ("BUILD_PASTURE", "DIG"):
                if pending_ripe_sb:
                    if op == "BUILD_PASTURE": pasture_while_sb_ripe += 1
                    else: clearing_while_sb_ripe += 1
                    assigned_val = TASK_NOMINAL_VALUE["BUILD_PASTURE"] if op == "BUILD_PASTURE" else TASK_NOMINAL_VALUE["CLEAR_OBSTACLE"]
                    best_alt_val = TASK_NOMINAL_VALUE["HARVEST_STRAWBERRY"]
                    opp_cost = best_alt_val - assigned_val
                    missed_reward_pasture_clearing.append(opp_cost)
                    opp_cost_events.append({
                        "step": s_idx, "day": day, "hour": hour, "worker": w_idx,
                        "assigned": op, "best_alternative": "HARVEST_STRAWBERRY",
                        "opp_cost": opp_cost
                    })

            # Check reverse case: Worker harvests strawberry while critical animal care is pending
            elif op == "HARVEST" and isinstance(t, dict) and t.get("crop") == "STRAWBERRY":
                if pending_care or pending_feed:
                    sb_while_critical_care += 1
                    assigned_val = TASK_NOMINAL_VALUE["HARVEST_STRAWBERRY"]
                    best_alt_val = TASK_NOMINAL_VALUE["CARE"] if pending_care else TASK_NOMINAL_VALUE["FEED"]
                    # If care/feed is late in the day (hour >= 20), missing it causes animal starvation!
                    if hour >= 20:
                        opp_cost = 300.0 - assigned_val # severe animal starvation penalty
                        missed_reward_sb_care.append(opp_cost)
                        opp_cost_events.append({
                            "step": s_idx, "day": day, "hour": hour, "worker": w_idx,
                            "assigned": "HARVEST_STRAWBERRY", "best_alternative": "CRITICAL_ANIMAL_CARE",
                            "opp_cost": opp_cost
                        })

    return {
        "seed": seed,
        "pasture_while_sb_ripe": pasture_while_sb_ripe,
        "clearing_while_sb_ripe": clearing_while_sb_ripe,
        "sb_while_critical_care": sb_while_critical_care,
        "mean_opp_cost_pasture_clearing": float(np.mean(missed_reward_pasture_clearing)) if missed_reward_pasture_clearing else 0.0,
        "total_opp_cost_pasture_clearing": float(np.sum(missed_reward_pasture_clearing)) if missed_reward_pasture_clearing else 0.0,
        "total_opp_cost_sb_care": float(np.sum(missed_reward_sb_care)) if missed_reward_sb_care else 0.0,
        "events_count": len(opp_cost_events)
    }

if __name__ == "__main__":
    from concurrent.futures import ProcessPoolExecutor
    seeds = list(range(1250, 1300))
    print(f"Auditing task opportunity costs on {len(seeds)} seeds...")
    with ProcessPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(analyze_opportunity_costs_trajectory, seeds))

    p_sb = np.mean([r["pasture_while_sb_ripe"] for r in results])
    c_sb = np.mean([r["clearing_while_sb_ripe"] for r in results])
    sb_c = np.mean([r["sb_while_critical_care"] for r in results])
    tot_opp_cost = np.mean([r["total_opp_cost_pasture_clearing"] for r in results])
    tot_sb_care_cost = np.mean([r["total_opp_cost_sb_care"] for r in results])

    print("\n" + "="*80)
    print("PHASE 5: OPPORTUNITY COST ANALYSIS (DAYS 8-14, 50 SEEDS)")
    print("="*80)
    print(f"1. Worker builds pasture while ripe strawberry exists: {p_sb:.2f} events / seed")
    print(f"2. Worker clears weeds/obstacles while ripe strawberry exists: {c_sb:.2f} events / seed")
    print(f"   Mean Missed Reward from Discretionary Pasture/Clearing: ${tot_opp_cost:,.2f} / seed")
    print(f"3. Reverse Case: Worker harvests strawberry while critical animal care pending (hour >= 20): {sb_c:.2f} events / seed")
    print(f"   Mean Missed Reward from Starvation Penalty: ${tot_sb_care_cost:,.2f} / seed")

    with open("scratch/opportunity_cost_results.json", "w") as f:
        json.dump({
            "pasture_while_sb_ripe": p_sb,
            "clearing_while_sb_ripe": c_sb,
            "sb_while_critical_care": sb_c,
            "missed_reward_pasture_clearing": tot_opp_cost,
            "missed_reward_sb_care": tot_sb_care_cost
        }, f, indent=2)
