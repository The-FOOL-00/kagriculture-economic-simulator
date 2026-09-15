import sys
import os
import json
from collections import defaultdict
import numpy as np
from concurrent.futures import ProcessPoolExecutor
import kaggle_environments

sys.path.insert(0, os.path.abspath('.'))

import candidates.candidate_cl_fert_gated as m1_module
from scratch.run_wheat_quota_sweep_50seeds import ParameterizedQuotaAgent

def analyze_seed_telemetry(seed):
    cfg = {"episodeSteps": 720, "seed": seed}
    
    # Run M1
    env_m1 = kaggle_environments.make("kaggriculture", configuration=cfg)
    steps_m1 = env_m1.run([m1_module.ClosedLoopEconomicV1(), "starter"])
    rew_m1 = float(steps_m1[-1][0]["reward"])

    # Run Q50
    env_q50 = kaggle_environments.make("kaggriculture", configuration=cfg)
    steps_q50 = env_q50.run([ParameterizedQuotaAgent(50), "starter"])
    rew_q50 = float(steps_q50[-1][0]["reward"])

    def extract_metrics(steps):
        strawberry_plants = {} # pos -> {planted_day, first_yield_day, harvests, rots, lost_units}
        hourly_demand = []
        hourly_capacity = []
        task_counts_d9_14 = defaultdict(int)

        for s_idx in range(len(steps)):
            obs = steps[s_idx][0]["observation"]
            day = obs["day"]
            hour = obs["hour"]
            farm0 = obs["farms"][0]
            tiles = farm0["tiles"]
            workers = [farm0.get("farmer")] + (farm0.get("hands") or [])
            num_workers = len(workers)

            if 7 <= day <= 18:
                # compute demand
                demand = 0
                for r in range(len(tiles)):
                    for c in range(len(tiles[r])):
                        t = tiles[r][c]
                        if isinstance(t, dict):
                            k = t.get("kind")
                            if k == "PLANT":
                                if t.get("yield_units", 0) >= (2 if t.get("crop") == "STRAWBERRY" else 4): demand += 1
                                if not t.get("watered_today"): demand += 1
                            elif k == "PASTURE" and t.get("animal"):
                                if not t.get("fed_today"): demand += 1
                                if not t.get("cared_today"): demand += 1
                                if t.get("yield_units", 0) > 0: demand += 1
                            elif k == "WEED":
                                demand += 1
                hourly_demand.append(demand)
                hourly_capacity.append(num_workers)

            # Track actions in Days 9-14
            if 9 <= day <= 14:
                act = steps[s_idx][0].get("action") or {}
                all_acts = [act.get("farmer")] + (act.get("hands") or [])
                for w_idx, a in enumerate(all_acts):
                    if a and isinstance(a, list):
                        op = a[0]
                        w_pos = workers[w_idx] if w_idx < len(workers) else None
                        t = tiles[w_pos[1]][w_pos[0]] if (w_pos and w_pos[1] < len(tiles) and w_pos[0] < len(tiles[w_pos[1]])) else None
                        if op == "HARVEST" and isinstance(t, dict):
                            task_counts_d9_14[f"HARVEST_{t.get('crop') or t.get('animal')}"] += 1
                        elif op == "BUILD_PASTURE":
                            task_counts_d9_14["BUILD_PASTURE"] += 1
                        elif op == "DIG":
                            task_counts_d9_14["DIG_WEED"] += 1
                        elif op == "FEED":
                            task_counts_d9_14["FEED"] += 1
                        elif op == "CARE":
                            task_counts_d9_14["CARE"] += 1
                        elif op == "WATER":
                            task_counts_d9_14["WATER"] += 1
                        elif op == "PLACE":
                            task_counts_d9_14["PLACE_ANIMAL"] += 1
                        elif op in ("NORTH", "SOUTH", "EAST", "WEST"):
                            task_counts_d9_14["MOVE"] += 1
                        else:
                            task_counts_d9_14[op] += 1

            # Track strawberry lifecycles
            for r in range(len(tiles)):
                for c in range(len(tiles[r])):
                    t = tiles[r][c]
                    pos = (c, r)
                    if isinstance(t, dict) and t.get("crop") == "STRAWBERRY":
                        if pos not in strawberry_plants:
                            strawberry_plants[pos] = {
                                "planted_day": t["planted_day"],
                                "first_yield_day": None,
                                "rot_day": None,
                                "harvests": 0,
                                "total_yield_harvested": 0
                            }
                        if t.get("yield_units", 0) > 0 and strawberry_plants[pos]["first_yield_day"] is None:
                            strawberry_plants[pos]["first_yield_day"] = day
                    elif pos in strawberry_plants and strawberry_plants[pos]["rot_day"] is None:
                        if isinstance(t, dict) and t.get("kind") == "WEED":
                            strawberry_plants[pos]["rot_day"] = day

            # Count harvest events
            act = steps[s_idx][0].get("action") or {}
            all_acts = [act.get("farmer")] + (act.get("hands") or [])
            for w_idx, a in enumerate(all_acts):
                if a and isinstance(a, list) and a[0] == "HARVEST":
                    w_pos = workers[w_idx] if w_idx < len(workers) else None
                    if w_pos and tuple(w_pos) in strawberry_plants:
                        t = tiles[w_pos[1]][w_pos[0]] if (w_pos[1] < len(tiles) and w_pos[0] < len(tiles[w_pos[1]])) else None
                        if isinstance(t, dict) and t.get("crop") == "STRAWBERRY":
                            strawberry_plants[tuple(w_pos)]["harvests"] += 1
                            strawberry_plants[tuple(w_pos)]["total_yield_harvested"] += int(t.get("yield_units", 0) or 0)

        # Summary of strawberry
        total_sb = len(strawberry_plants)
        rotted_sb = sum(1 for p in strawberry_plants.values() if p["rot_day"] is not None)
        harvested_sb = sum(p["harvests"] for p in strawberry_plants.values())
        first_yield_days = [p["first_yield_day"] for p in strawberry_plants.values() if p["first_yield_day"] is not None]

        # Sold quantities
        sold_qty = defaultdict(int)
        for st in steps:
            for o in (st[0].get("action") or {}).get("market", []):
                if isinstance(o, list) and len(o) >= 3 and o[0] == "SELL":
                    sold_qty[o[1]] += int(o[2])

        return {
            "mean_demand": float(np.mean(hourly_demand)) if hourly_demand else 0,
            "mean_capacity": float(np.mean(hourly_capacity)) if hourly_capacity else 0,
            "total_strawberry_plants": total_sb,
            "rotted_strawberry_plants": rotted_sb,
            "total_strawberry_harvests": harvested_sb,
            "mean_first_yield_day": float(np.mean(first_yield_days)) if first_yield_days else 0,
            "sold_qty": dict(sold_qty),
            "task_counts_d9_14": dict(task_counts_d9_14)
        }

    m1_diag = extract_metrics(steps_m1)
    q50_diag = extract_metrics(steps_q50)

    return {
        "seed": seed,
        "rew_m1": rew_m1,
        "rew_q50": rew_q50,
        "m1": m1_diag,
        "q50": q50_diag
    }

def main():
    seeds = list(range(1250, 1280)) # 30 seeds
    print(f"Running Phase 1-3 Diagnostic on {len(seeds)} seeds with 10 workers...")
    with ProcessPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(analyze_seed_telemetry, seeds))

    m1_rews = [r["rew_m1"] for r in results]
    q50_rews = [r["rew_q50"] for r in results]
    deltas = [r["rew_q50"] - r["rew_m1"] for r in results]

    print("\n" + "="*80)
    print("PHASE 1-3 DIAGNOSTIC SUMMARY (30 SEEDS)")
    print("="*80)
    print(f"Mean Reward: M1 = ${np.mean(m1_rews):,.2f} | Q50 = ${np.mean(q50_rews):,.2f} | Delta = +${np.mean(deltas):,.2f}")
    print(f"Win Rate Q50 vs M1: {sum(1 for d in deltas if d > 0)/len(deltas)*100:.1f}%")

    m1_demand = np.mean([r["m1"]["mean_demand"] for r in results])
    q50_demand = np.mean([r["q50"]["mean_demand"] for r in results])
    m1_cap = np.mean([r["m1"]["mean_capacity"] for r in results])
    q50_cap = np.mean([r["q50"]["mean_capacity"] for r in results])

    print(f"\nLabor Demand vs Capacity (Days 7-18):")
    print(f"  M1:  Mean Demand = {m1_demand:.1f} actions/h | Capacity = {m1_cap:.1f} workers (Ratio = {m1_demand/m1_cap:.2f}x)")
    print(f"  Q50: Mean Demand = {q50_demand:.1f} actions/h | Capacity = {q50_cap:.1f} workers (Ratio = {q50_demand/q50_cap:.2f}x)")

    # Strawberry metrics
    m1_sb_sold = np.mean([r["m1"]["sold_qty"].get("STRAWBERRY", 0) for r in results])
    q50_sb_sold = np.mean([r["q50"]["sold_qty"].get("STRAWBERRY", 0) for r in results])
    m1_sb_rot = np.mean([r["m1"]["rotted_strawberry_plants"] for r in results])
    q50_sb_rot = np.mean([r["q50"]["rotted_strawberry_plants"] for r in results])
    m1_sb_harv = np.mean([r["m1"]["total_strawberry_harvests"] for r in results])
    q50_sb_harv = np.mean([r["q50"]["total_strawberry_harvests"] for r in results])
    m1_first_yd = np.mean([r["m1"]["mean_first_yield_day"] for r in results])
    q50_first_yd = np.mean([r["q50"]["mean_first_yield_day"] for r in results])

    print(f"\nStrawberry Production & Loss Metrics:")
    print(f"  Mean Sold: M1 = {m1_sb_sold:.2f} u | Q50 = {q50_sb_sold:.2f} u (Delta = {q50_sb_sold - m1_sb_sold:+.2f} u)")
    print(f"  Mean Bush Rots: M1 = {m1_sb_rot:.2f} | Q50 = {q50_sb_rot:.2f} rots/seed")
    print(f"  Mean Bush Harvest Actions: M1 = {m1_sb_harv:.2f} | Q50 = {q50_sb_harv:.2f}")
    print(f"  Mean First Yield Day: M1 = Day {m1_first_yd:.1f} | Q50 = Day {q50_first_yd:.1f}")

    # Days 9-14 Task Allocation
    tasks = set()
    for r in results:
        tasks.update(r["m1"]["task_counts_d9_14"].keys())
        tasks.update(r["q50"]["task_counts_d9_14"].keys())

    print(f"\nDays 9-14 Task Action Distribution (Mean actions / seed):")
    print(f"{'Task':<25} | {'M1 Actions':<14} | {'Q50 Actions':<14} | {'Delta (Q50 - M1)':<16}")
    print("-" * 75)
    for t in sorted(tasks):
        m1_c = np.mean([r["m1"]["task_counts_d9_14"].get(t, 0) for r in results])
        q50_c = np.mean([r["q50"]["task_counts_d9_14"].get(t, 0) for r in results])
        if m1_c > 1 or q50_c > 1:
            print(f"{t:<25} | {m1_c:>12.1f}   | {q50_c:>12.1f}   | {q50_c - m1_c:>+14.1f}")

    with open("scratch/phase1_to_3_diagnostic_results.json", "w") as f:
        json.dump(results, f)
    print("\nSaved detailed diagnostic to scratch/phase1_to_3_diagnostic_results.json")

if __name__ == "__main__":
    main()
