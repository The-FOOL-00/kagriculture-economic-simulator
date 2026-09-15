import sys
import os
import json
from collections import defaultdict
import numpy as np
import kaggle_environments

sys.path.insert(0, os.path.abspath('.'))

import candidates.candidate_cl_fert_gated as m1_module
from scratch.run_wheat_quota_sweep_50seeds import ParameterizedQuotaAgent

MOVES = {"NORTH", "SOUTH", "EAST", "WEST"}

def track_simulation_telemetry(agent_class, seed, quota=50, start_day=7, end_day=18):
    if agent_class == "M1":
        agent = m1_module.ClosedLoopEconomicV1()
    elif agent_class == "Q50":
        agent = ParameterizedQuotaAgent(quota)
    else:
        agent = agent_class()

    cfg = {"episodeSteps": 720, "seed": seed}
    env = kaggle_environments.make("kaggriculture", configuration=cfg)
    steps = env.run([agent, "starter"])

    telemetry_by_hour = {}
    strawberry_tiles_lifecycle = {}

    start_step = start_day * 24
    end_step = (end_day + 1) * 24

    # Pre-scan for all strawberry plantings across entire game
    for s_idx in range(len(steps)):
        obs = steps[s_idx][0]["observation"]
        farms = obs.get("farms", [{}, {}])
        farm0 = farms[0] if len(farms) > 0 else {}
        tiles = farm0.get("tiles", [])

        for r in range(len(tiles)):
            for c in range(len(tiles[r])):
                t = tiles[r][c]
                pos = (c, r)
                if isinstance(t, dict) and t.get("crop") == "STRAWBERRY":
                    p_day = t.get("planted_day", 0)
                    if pos not in strawberry_tiles_lifecycle:
                        strawberry_tiles_lifecycle[pos] = {
                            "pos": pos,
                            "planted_day": p_day,
                            "planted_step": s_idx,
                            "expected_maturation_day": p_day + 10,
                            "first_yield_step": None,
                            "harvest_steps": [],
                            "yield_units_history": [],
                            "rotted": False,
                            "rot_step": None,
                            "unwatered_count": 0,
                            "max_unharvested_wait_hours": 0,
                            "hours_delayed": 0
                        }
                    rec = strawberry_tiles_lifecycle[pos]
                    yu = t.get("yield_units", 0)
                    rec["yield_units_history"].append((s_idx, yu))
                    if yu > 0 and rec["first_yield_step"] is None:
                        rec["first_yield_step"] = s_idx

                # Check if previously tracked strawberry died / rotted to WEED
                elif pos in strawberry_tiles_lifecycle:
                    rec = strawberry_tiles_lifecycle[pos]
                    if not rec["rotted"] and rec.get("planted_step", 0) <= s_idx:
                        if isinstance(t, dict) and t.get("kind") == "WEED":
                            rec["rotted"] = True
                            rec["rot_step"] = s_idx

        # Check action for strawberry harvest
        p0_act = steps[s_idx][0].get("action") or {}
        f_act = p0_act.get("farmer")
        farmer_pos = farm0.get("farmer")
        all_workers = [farmer_pos] + (farm0.get("hands") or [])
        all_actions = [f_act] + (p0_act.get("hands") or [])

        for w_idx, (w_pos, act) in enumerate(zip(all_workers, all_actions)):
            if act and isinstance(act, list) and act[0] == "HARVEST":
                if w_pos and tuple(w_pos) in strawberry_tiles_lifecycle:
                    st_tile = tiles[w_pos[1]][w_pos[0]] if w_pos[1] < len(tiles) and w_pos[0] < len(tiles[w_pos[1]]) else None
                    if isinstance(st_tile, dict) and st_tile.get("crop") == "STRAWBERRY":
                        strawberry_tiles_lifecycle[tuple(w_pos)]["harvest_steps"].append(s_idx)

    # Detailed hour-by-hour telemetry from start_step to end_step
    hourly_labor_demand = []
    hourly_labor_capacity = []
    hourly_records = []

    for s_idx in range(start_step, min(end_step, len(steps))):
        obs = steps[s_idx][0]["observation"]
        day = obs.get("day", 0)
        hour = obs.get("hour", 0)
        farms = obs.get("farms", [{}, {}])
        farm0 = farms[0] if len(farms) > 0 else {}
        tiles = farm0.get("tiles", [])
        private = obs.get("private", {})
        shed = private.get("shed", {})
        seeds = farm0.get("seeds", {})
        invs = private.get("inventories", [])

        farmer_pos = farm0.get("farmer")
        hands_pos = farm0.get("hands") or []
        all_workers = [farmer_pos] + hands_pos
        num_workers = len(all_workers)

        p0_act = steps[s_idx][0].get("action") or {}
        f_act = p0_act.get("farmer")
        h_acts = p0_act.get("hands") or []
        all_actions = [f_act] + h_acts

        # Compute LABOR_CAPACITY[t]
        capacity = num_workers

        # Compute tasks available on field (LABOR_DEMAND[t])
        demand_breakdown = {
            "ripe_strawberry": 0,
            "ripe_wheat": 0,
            "ripe_melon": 0,
            "ripe_animal": 0,
            "unwatered_crops": 0,
            "urgent_unwatered": 0,
            "hungry_animals": 0,
            "care_animals": 0,
            "unbuilt_pasture": 0,
            "weeds_to_clear": 0,
            "plant_strawberry": 0,
            "plant_melon": 0,
            "plant_wheat": 0,
            "animals_in_shed_to_place": int(shed.get("COW", 0) or 0) + int(shed.get("SHEEP", 0) or 0),
            "fertilizer_collect": 0,
        }

        for r in range(len(tiles)):
            for c in range(len(tiles[r])):
                t = tiles[r][c]
                if not isinstance(t, dict):
                    continue
                k = t.get("kind")
                if k == "PLANT":
                    crop = t.get("crop")
                    yu = t.get("yield_units", 0)
                    if yu >= (2 if crop == "STRAWBERRY" else (4 if crop == "WHEAT" else 5)):
                        if crop == "STRAWBERRY": demand_breakdown["ripe_strawberry"] += 1
                        elif crop == "WHEAT": demand_breakdown["ripe_wheat"] += 1
                        elif crop == "MELON": demand_breakdown["ripe_melon"] += 1
                    if not t.get("watered_today"):
                        if t.get("consecutive_unwatered", 0) >= 1:
                            demand_breakdown["urgent_unwatered"] += 1
                        else:
                            demand_breakdown["unwatered_crops"] += 1
                elif k == "PASTURE":
                    if t.get("animal"):
                        if not t.get("fed_today"): demand_breakdown["hungry_animals"] += 1
                        if not t.get("cared_today"): demand_breakdown["care_animals"] += 1
                        if t.get("yield_units", 0) > 0: demand_breakdown["ripe_animal"] += 1
                        if t.get("fertilizer_available"): demand_breakdown["fertilizer_collect"] += 1
                elif k == "WEED":
                    demand_breakdown["weeds_to_clear"] += 1

        total_demand = sum(demand_breakdown.values())
        hourly_labor_demand.append(total_demand)
        hourly_labor_capacity.append(capacity)

        # Worker action breakdown
        worker_records = []
        action_type_counts = defaultdict(int)

        for w_i, (w_pos, act) in enumerate(zip(all_workers, all_actions)):
            op = act[0] if (act and isinstance(act, list)) else "PASS"
            is_move = op in MOVES
            is_idle = (op == "PASS")

            task_type = "IDLE"
            if is_move:
                task_type = "MOVE"
            elif op == "HARVEST":
                if w_pos:
                    t = tiles[w_pos[1]][w_pos[0]] if w_pos[1] < len(tiles) and w_pos[0] < len(tiles[w_pos[1]]) else None
                    if isinstance(t, dict):
                        if t.get("crop") == "STRAWBERRY": task_type = "HARVEST_STRAWBERRY"
                        elif t.get("crop") == "WHEAT": task_type = "HARVEST_WHEAT"
                        elif t.get("crop") == "MELON": task_type = "HARVEST_MELON"
                        elif t.get("animal") == "COW": task_type = "HARVEST_MILK"
                        elif t.get("animal") == "SHEEP": task_type = "HARVEST_WOOL"
                        else: task_type = "HARVEST_OTHER"
            elif op == "PLANT":
                crop = act[1] if len(act) > 1 else "UNKNOWN"
                task_type = f"PLANT_{crop}"
            elif op == "WATER":
                task_type = "WATER"
            elif op == "DIG":
                task_type = "CLEAR_OBSTACLE"
            elif op == "BUILD_PASTURE":
                task_type = "BUILD_PASTURE"
            elif op == "FEED":
                task_type = "FEED"
            elif op == "CARE":
                task_type = "CARE"
            elif op == "PICKUP":
                task_type = "PICKUP"
            elif op == "DROP":
                task_type = "DROP"
            elif op == "PLACE":
                task_type = "PLACE"
            elif op == "FERTILIZE":
                task_type = "FERTILIZE"
            elif op == "COLLECT_FERTILIZER":
                task_type = "COLLECT_FERTILIZER"

            action_type_counts[task_type] += 1
            worker_records.append({
                "worker_id": w_i,
                "pos": w_pos,
                "action": act,
                "op": op,
                "task_type": task_type,
                "is_move": is_move,
                "is_idle": is_idle
            })

        hourly_records.append({
            "step": s_idx,
            "day": day,
            "hour": hour,
            "workers_count": num_workers,
            "capacity": capacity,
            "demand": total_demand,
            "demand_breakdown": demand_breakdown,
            "action_counts": dict(action_type_counts),
            "workers": worker_records
        })

    final_reward = float(steps[-1][0]["reward"])

    return {
        "seed": seed,
        "agent": agent_class if isinstance(agent_class, str) else "Custom",
        "final_reward": final_reward,
        "strawberry_lifecycle": {f"{k[0]},{k[1]}": v for k, v in strawberry_tiles_lifecycle.items()},
        "hourly_telemetry": hourly_records,
        "mean_demand": float(np.mean(hourly_labor_demand)),
        "mean_capacity": float(np.mean(hourly_labor_capacity)),
        "peak_demand": int(np.max(hourly_labor_demand)),
        "min_demand": int(np.min(hourly_labor_demand))
    }

if __name__ == "__main__":
    print("Testing telemetry tracking on seed 1250...")
    res = track_simulation_telemetry("Q50", 1250)
    print(f"Seed 1250 Q50 Reward: {res['final_reward']}")
    print(f"Mean Labor Demand: {res['mean_demand']:.2f}, Mean Capacity: {res['mean_capacity']:.2f}, Peak Demand: {res['peak_demand']}")
    print(f"Tracked {len(res['strawberry_lifecycle'])} strawberry bushes.")
    for pos, lif in list(res['strawberry_lifecycle'].items())[:3]:
        print(f"  Tile {pos}: planted day {lif['planted_day']}, harvests: {len(lif['harvest_steps'])}, rotted: {lif['rotted']}")
