"""
Step 1 Raw Telemetry Extraction for Seeds 1000-1009
Agents:
- CL-Economic-V1 (candidates/candidate_cl_economic_v1.py)
- Frozen V2 (candidates/slot2_aethel_refined_v2.py)
"""
import sys
import os
import json
import copy
from collections import defaultdict

PROJECT_ROOT = os.path.abspath(".")
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import kaggle_environments
from candidates.candidate_cl_economic_v1 import ClosedLoopEconomicV1
import candidates.slot2_aethel_refined_v2 as v2_mod

TPD = 24

def dist(p1, p2):
    return abs(p1[0] - p2[0]) + abs(p1[1] - p2[1])

def run_agent_telemetry(seed, agent_type="CL"):
    if agent_type == "CL":
        agent_inst = ClosedLoopEconomicV1()
        agent_fn = agent_inst
    else:
        # V2 uses function closure or agent
        agent_fn = v2_mod.agent

    # We will wrap the agent to capture pre-step state if needed, or inspect env.steps
    # Using env.steps gives the post-action and pre-action transitions perfectly.
    cfg = {"episodeSteps": 720, "seed": seed}
    env = kaggle_environments.make("kaggriculture", configuration=cfg, debug=False)
    
    # Run episode
    env.run([agent_fn, "starter"])
    steps = env.steps
    total_steps = len(steps)

    # Telemetry storage
    plant_events = []
    harvest_events = []
    water_events = []
    daily_tile_snapshots = {} # day -> { (x,y): tile_copy }
    
    # Tile history tracker: (x, y) -> list of occupants
    # each occupant: { "crop": crop, "planted_step": s, "planted_day": d, "harvest_events": [], "water_events": [], "end_step": None, "end_reason": None }
    tile_history = defaultdict(list)
    tile_last_seen = {} # (x, y) -> crop

    for s_idx in range(1, total_steps):
        prev_obs_0 = steps[s_idx - 1][0]["observation"]
        curr_obs_0 = steps[s_idx][0]["observation"]
        act_0 = steps[s_idx][0].get("action") or {}
        
        prev_farm = prev_obs_0["farms"][0]
        curr_farm = curr_obs_0["farms"][0]
        prev_priv = prev_obs_0["private"]
        curr_priv = curr_obs_0["private"]

        step = prev_obs_0.get("step", s_idx - 1)
        day = prev_obs_0.get("day", step // TPD)
        hour = prev_obs_0.get("hour", step % TPD)
        cash_before = float(prev_farm.get("money", 0))
        quads = list(prev_farm.get("unlocked_quadrants", []))

        prev_farmer = tuple(prev_farm["farmer"])
        prev_hands = [tuple(h) for h in (prev_farm.get("hands") or [])]
        prev_workers = [prev_farmer] + prev_hands

        curr_farmer = tuple(curr_farm["farmer"])
        curr_hands = [tuple(h) for h in (curr_farm.get("hands") or [])]
        curr_workers = [curr_farmer] + curr_hands

        farmer_act = act_0.get("farmer") or ["PASS"]
        hands_act = act_0.get("hands") or []
        all_acts = [farmer_act] + hands_act

        prev_tiles = prev_farm["tiles"]
        curr_tiles = curr_farm["tiles"]

        # Track worker actions
        for w_idx, a in enumerate(all_acts):
            if not a:
                continue
            op = a[0]
            w_pos = prev_workers[w_idx] if w_idx < len(prev_workers) else (4, 4)

            if op == "PLANT":
                crop = a[1] if len(a) > 1 else "UNKNOWN"
                fx, fy = w_pos
                prev_tile_state = prev_tiles[fy][fx]
                
                # Check succession: was there a crop previously on this tile?
                prev_occ = tile_last_seen.get((fx, fy))
                is_succession = (prev_occ is not None)
                prev_crop = prev_occ["crop"] if is_succession else None

                event = {
                    "seed": seed,
                    "agent": agent_type,
                    "step": step,
                    "day": day,
                    "hour": hour,
                    "worker_idx": w_idx,
                    "coordinate": [fx, fy],
                    "crop": crop,
                    "previous_tile_state": copy.deepcopy(prev_tile_state),
                    "is_succession": is_succession,
                    "previous_crop": prev_crop,
                    "cash_before": cash_before,
                    "num_workers": len(prev_workers),
                    "unlocked_quads": copy.deepcopy(quads)
                }
                plant_events.append(event)
                
                new_occ = {
                    "crop": crop,
                    "planted_step": step,
                    "planted_day": day,
                    "coord": (fx, fy),
                    "water_events": [],
                    "harvest_events": [],
                    "fertilized_events": []
                }
                tile_history[(fx, fy)].append(new_occ)
                tile_last_seen[(fx, fy)] = new_occ

            elif op == "WATER":
                fx, fy = w_pos
                target_tile = prev_tiles[fy][fx]
                crop_on_tile = target_tile.get("crop") if (isinstance(target_tile, dict) and target_tile.get("kind") == "PLANT") else None
                
                # Distance traveled: worker was at prev_workers[w_idx] when executing WATER on (fx, fy), so dist is 0
                # But worker may have moved to get here; we track movement in separate travel analysis
                wevent = {
                    "seed": seed,
                    "agent": agent_type,
                    "step": step,
                    "day": day,
                    "hour": hour,
                    "worker_idx": w_idx,
                    "coordinate": [fx, fy],
                    "crop": crop_on_tile,
                    "was_watered_today": target_tile.get("watered_today", False) if isinstance(target_tile, dict) else False,
                    "yield_units": target_tile.get("yield_units", 0) if isinstance(target_tile, dict) else 0
                }
                water_events.append(wevent)
                if (fx, fy) in tile_last_seen and tile_last_seen[(fx, fy)]["crop"] == crop_on_tile:
                    tile_last_seen[(fx, fy)]["water_events"].append((step, day, hour))

            elif op == "HARVEST":
                fx, fy = w_pos
                target_tile = prev_tiles[fy][fx]
                crop_on_tile = None
                yield_units = 0
                if isinstance(target_tile, dict):
                    crop_on_tile = target_tile.get("crop") or target_tile.get("animal")
                    yield_units = target_tile.get("yield_units", 0)
                
                hevent = {
                    "seed": seed,
                    "agent": agent_type,
                    "step": step,
                    "day": day,
                    "hour": hour,
                    "worker_idx": w_idx,
                    "coordinate": [fx, fy],
                    "crop": crop_on_tile,
                    "yield_units": yield_units
                }
                harvest_events.append(hevent)
                if (fx, fy) in tile_last_seen and tile_last_seen[(fx, fy)]["crop"] == crop_on_tile:
                    tile_last_seen[(fx, fy)]["harvest_events"].append((step, day, hour, yield_units))

        # Snapshot at hour 23
        if hour == 23:
            daily_tile_snapshots[day] = {}
            for y in range(10):
                for x in range(10):
                    t = curr_tiles[y][x]
                    if isinstance(t, dict):
                        daily_tile_snapshots[day][f"{x},{y}"] = copy.deepcopy(t)

    # Final summary statistics
    final_reward = float(steps[-1][0].get("reward") or 0.0)
    
    # Compute total harvested by crop from inventory drops / deltas or harvest events
    crop_harvest_totals = defaultdict(int)
    for h in harvest_events:
        if h["crop"]:
            crop_harvest_totals[h["crop"]] += h["yield_units"]

    return {
        "seed": seed,
        "agent": agent_type,
        "reward": final_reward,
        "plant_events": plant_events,
        "harvest_events": harvest_events,
        "water_events": water_events,
        "daily_tile_snapshots": daily_tile_snapshots,
        "crop_harvest_totals": dict(crop_harvest_totals),
        "steps_count": total_steps
    }

if __name__ == "__main__":
    print("Testing single run Seed 1000...")
    res_cl = run_agent_telemetry(1000, "CL")
    print(f"CL Seed 1000: Reward={res_cl['reward']:.2f}, Plants={len(res_cl['plant_events'])}, Harvests={len(res_cl['harvest_events'])}, Waterings={len(res_cl['water_events'])}")
    print(f"CL Harvest Totals: {res_cl['crop_harvest_totals']}")
    
    res_v2 = run_agent_telemetry(1000, "V2")
    print(f"V2 Seed 1000: Reward={res_v2['reward']:.2f}, Plants={len(res_v2['plant_events'])}, Harvests={len(res_v2['harvest_events'])}, Waterings={len(res_v2['water_events'])}")
    print(f"V2 Harvest Totals: {res_v2['crop_harvest_totals']}")
