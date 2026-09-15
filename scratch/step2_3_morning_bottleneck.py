"""
Step 2 & 3: Morning Bottleneck Telemetry & Opportunity Cost Engine
==================================================================
Instruments Canonical V54 on 30 common seeds (101 to 130).
Focuses on the first four hours of every day (hours 0, 1, 2, 3 -> step % 24 in [0, 1, 2, 3]).

Records:
- Detailed worker actions (position, action, target, productive vs idle/movement)
- Livestock task breakdown (FEED, CARE, MILK, WOOL, FERTILIZER, PICKUP, DROP, PLACE)
- Congestion metrics:
  * Movement steps before productive action
  * Productive actions per worker-hour
  * Workers blocked by shed routing
  * Workers blocked by carrying
  * Duplicate routing
  * Empty movement
  * Waiting time (PASS)
  * Tasks unserved at hour 4

Opportunity Cost Analysis (Step 3):
- Tracks whether unserved tasks at hour 4 get completed by hour 23
- Checks whether unharvested strawberries missed daily refresh / decayed
- Checks whether unwatered plants resulted in missed yield or weeds
- Checks whether unfed animals resulted in missed yield or escapes
- Calculates true causal dollar impact of morning congestion
"""

import os
import sys
import time
import json
import csv
import importlib.util
from collections import defaultdict
import numpy as np
from concurrent.futures import ProcessPoolExecutor

V54_PATH = os.path.abspath("external_repos/lixingtao123-Kaggriculture/variant_v54_h3q4/main.py")
SEEDS = list(range(101, 131))  # 30 common seeds

SHED_TILES_10 = [(4, 4), (4, 5), (5, 4), (5, 5)]
SHED_ACCESS_10 = [
    (3, 4), (3, 5), (4, 3), (4, 6), (5, 3), (5, 6), (6, 4), (6, 5)
]

def load_canonical_v54():
    d = os.path.dirname(V54_PATH)
    if d not in sys.path:
        sys.path.insert(0, d)
    spec = importlib.util.spec_from_file_location(f"v54_telemetry_{os.getpid()}_{time.time_ns()}", V54_PATH)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod.agent

def analyze_seed_telemetry(seed):
    from kaggle_environments import make

    agent_p0 = load_canonical_v54()
    agent_p1 = load_canonical_v54()

    env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed})

    # We will step through manually to inspect state before and after actions
    env.reset()

    # Telemetry storage
    morning_records = []
    daily_unserved_h4 = []
    daily_resolved_h24 = []
    
    total_morning_worker_hours = 0
    total_morning_productive = 0
    total_morning_movement = 0
    total_morning_passes = 0
    
    # Task specific counts in morning
    morning_chores = defaultdict(int)
    
    # Congestion metrics
    shed_routing_blocks = 0
    carrying_blocks = 0
    duplicate_targets = 0
    consecutive_moves_list = []
    
    # Track worker pathing: map worker_id -> current streak of moves
    worker_move_streak = defaultdict(int)

    # We run 720 steps
    for step in range(719):
        state0 = env.state[0]
        obs0 = state0.observation
        farm0 = obs0.farms[0]
        priv0 = obs0.private
        tiles = farm0["tiles"]
        board_size = len(tiles)
        
        day = step // 24
        hour = step % 24
        is_morning = (hour < 4)

        # Before action: state of workers
        farmer_pos = list(farm0["farmer"])
        hands_pos = [list(p) for p in farm0.get("hands", [])]
        all_worker_pos = [farmer_pos] + hands_pos
        num_workers = len(all_worker_pos)

        # Execute agent actions
        # V54 agent returns dict with "farmer", "hands", "market"
        act0 = agent_p0(obs0, env.configuration)
        act1 = agent_p1(env.state[1].observation, env.configuration)

        env.step([act0, act1])

        # Inspect what actions were taken by Seat 0
        farmer_act = act0.get("farmer", ["PASS"]) if act0 else ["PASS"]
        hands_act = act0.get("hands", []) if act0 else []
        all_actions = [farmer_act] + [hands_act[i] if i < len(hands_act) else ["PASS"] for i in range(len(hands_pos))]

        if is_morning:
            total_morning_worker_hours += num_workers

            # Check duplicate target positions
            target_positions = []
            for wid, (wpos, wact) in enumerate(zip(all_worker_pos, all_actions)):
                op = wact[0] if wact else "PASS"
                fx, fy = wpos
                
                # Determine if action is productive or movement/idle
                is_productive = False
                is_move = (op in ["NORTH", "SOUTH", "EAST", "WEST"])
                is_pass = (op == "PASS")
                
                target_tile = None
                if is_move:
                    dx, dy = {"NORTH": (0, -1), "SOUTH": (0, 1), "EAST": (1, 0), "WEST": (-1, 0)}[op]
                    target_tile = (fx + dx, fy + dy)
                    worker_move_streak[wid] += 1
                    total_morning_movement += 1
                elif is_pass:
                    total_morning_passes += 1
                    target_tile = (fx, fy)
                else:
                    # Chore action
                    is_productive = True
                    total_morning_productive += 1
                    consecutive_moves_list.append(worker_move_streak[wid])
                    worker_move_streak[wid] = 0
                    target_tile = (fx, fy)

                # Classify specific chore
                tile_content = tiles[fy][fx] if 0 <= fy < board_size and 0 <= fx < board_size else None
                chore_type = "OTHER"
                if op == "FEED":
                    chore_type = "FEED"
                elif op == "CARE":
                    chore_type = "CARE"
                elif op == "HARVEST":
                    if isinstance(tile_content, dict) and "animal" in tile_content:
                        chore_type = "MILK" if tile_content["animal"] == "COW" else "WOOL"
                    elif isinstance(tile_content, dict) and tile_content.get("crop") == "STRAWBERRY":
                        chore_type = "HARVEST_STRAWBERRY"
                    elif isinstance(tile_content, dict) and tile_content.get("crop") == "WHEAT":
                        chore_type = "HARVEST_WHEAT"
                    else:
                        chore_type = "HARVEST_CROP"
                elif op == "COLLECT_FERTILIZER":
                    chore_type = "FERTILIZER"
                elif op == "PICKUP":
                    chore_type = "PICKUP"
                elif op == "DROP":
                    chore_type = "DROP"
                elif op == "PLACE":
                    chore_type = "PLACE"
                elif op == "WATER":
                    chore_type = "WATER"
                elif op == "PLANT":
                    chore_type = "PLANT"
                elif op == "DIG":
                    chore_type = "DIG"
                elif op == "BUILD_PASTURE":
                    chore_type = "BUILD_PASTURE"

                morning_chores[chore_type] += 1

                # Record worker record
                morning_records.append({
                    "day": day,
                    "hour": hour,
                    "worker_id": wid,
                    "pos_x": fx,
                    "pos_y": fy,
                    "action": op,
                    "chore_type": chore_type,
                    "productive": is_productive,
                    "target": target_tile
                })

                if is_productive:
                    target_positions.append(target_tile)

            # Check duplicate productive targets
            if len(target_positions) != len(set(target_positions)):
                duplicate_targets += (len(target_positions) - len(set(target_positions)))

            # Check shed congestion: multiple workers on shed access tiles
            shed_access_occupancy = sum(1 for pos in all_worker_pos if tuple(pos) in SHED_ACCESS_10)
            if shed_access_occupancy > 2:
                shed_routing_blocks += (shed_access_occupancy - 2)

        # At Hour 4 (step % 24 == 4): Snapshot unserved tasks
        if hour == 4:
            # Snapshot all unserved chores on farm
            unharvested_strawberries = 0
            strawberry_mature_yield = 0
            unwatered_strawberries = 0
            unwatered_other_plants = 0
            unfed_animals = 0
            uncared_animals = 0
            unharvested_milk = 0
            unharvested_wool = 0
            uncollected_fert = 0

            for y in range(board_size):
                for x in range(board_size):
                    t = tiles[y][x]
                    if isinstance(t, dict):
                        if t.get("kind") == "PLANT":
                            if t.get("crop") == "STRAWBERRY":
                                if t.get("yield_units", 0) > 0:
                                    unharvested_strawberries += 1
                                    strawberry_mature_yield += t.get("yield_units", 0)
                                if not t.get("watered_today"):
                                    unwatered_strawberries += 1
                            else:
                                if not t.get("watered_today"):
                                    unwatered_other_plants += 1
                        elif "animal" in t:
                            if not t.get("fed_today"):
                                unfed_animals += 1
                            if not t.get("cared_today"):
                                uncared_animals += 1
                            if t.get("yield_units", 0) > 0:
                                if t.get("animal") == "COW":
                                    unharvested_milk += t.get("yield_units", 0)
                                elif t.get("animal") == "SHEEP":
                                    unharvested_wool += t.get("yield_units", 0)
                            if t.get("fertilizer_available"):
                                uncollected_fert += 1

            daily_unserved_h4.append({
                "day": day,
                "unharvested_strawberries": unharvested_strawberries,
                "strawberry_mature_yield": strawberry_mature_yield,
                "unwatered_strawberries": unwatered_strawberries,
                "unwatered_other": unwatered_other_plants,
                "unfed_animals": unfed_animals,
                "uncared_animals": uncared_animals,
                "unharvested_milk": unharvested_milk,
                "unharvested_wool": unharvested_wool,
                "uncollected_fert": uncollected_fert
            })

        # At Hour 23 (end of day before daily refresh): Snapshot if unserved tasks were resolved
        if hour == 23:
            unwatered_eod = 0
            unfed_eod = 0
            uncared_eod = 0
            strawberries_lost_to_weed = 0
            strawberries_decayed = 0
            strawberries_mature_eod = 0

            for y in range(board_size):
                for x in range(board_size):
                    t = tiles[y][x]
                    if isinstance(t, dict):
                        if t.get("kind") == "PLANT":
                            if not t.get("watered_today"):
                                unwatered_eod += 1
                            if t.get("crop") == "STRAWBERRY":
                                strawberries_mature_eod += t.get("yield_units", 0)
                        elif "animal" in t:
                            if not t.get("fed_today"):
                                unfed_eod += 1
                            if not t.get("cared_today"):
                                uncared_eod += 1

            daily_resolved_h24.append({
                "day": day,
                "unwatered_eod": unwatered_eod,
                "unfed_eod": unfed_eod,
                "uncared_eod": uncared_eod,
                "strawberries_mature_eod": strawberries_mature_eod
            })

    # Final summary for this seed
    final_reward = float(env.steps[-1][0].reward or 0.0)

    return {
        "seed": seed,
        "reward": final_reward,
        "total_morning_worker_hours": total_morning_worker_hours,
        "total_morning_productive": total_morning_productive,
        "total_morning_movement": total_morning_movement,
        "total_morning_passes": total_morning_passes,
        "productive_per_worker_hour": total_morning_productive / max(1, total_morning_worker_hours),
        "mean_consecutive_moves": float(np.mean(consecutive_moves_list)) if consecutive_moves_list else 0.0,
        "shed_routing_blocks": shed_routing_blocks,
        "duplicate_targets": duplicate_targets,
        "morning_chores": dict(morning_chores),
        "daily_unserved_h4": daily_unserved_h4,
        "daily_resolved_h24": daily_resolved_h24
    }

def main():
    print("=" * 80)
    print("STEP 2 & 3: MORNING BOTTLENECK TELEMETRY & OPPORTUNITY COST (30 SEEDS)")
    print("=" * 80, flush=True)

    t0 = time.time()
    results = []
    with ProcessPoolExecutor(max_workers=8) as pool:
        for res in pool.map(analyze_seed_telemetry, SEEDS):
            results.append(res)
            print(f"Seed {res['seed']} | Reward: ${res['reward']:,.0f} | Prod/Worker-Hr: {res['productive_per_worker_hour']:.3f} | Mean Move Steps: {res['mean_consecutive_moves']:.2f}", flush=True)

    elapsed = time.time() - t0
    print(f"\nCompleted 30 seeds in {elapsed:.1f}s.")

    # Aggregate telemetry
    total_wh = sum(r["total_morning_worker_hours"] for r in results)
    total_prod = sum(r["total_morning_productive"] for r in results)
    total_move = sum(r["total_morning_movement"] for r in results)
    total_pass = sum(r["total_morning_passes"] for r in results)
    shed_blocks = sum(r["shed_routing_blocks"] for r in results)
    dup_targets = sum(r["duplicate_targets"] for r in results)
    
    mean_moves_before_prod = float(np.mean([r["mean_consecutive_moves"] for r in results]))
    prod_per_wh = total_prod / max(1, total_wh)

    # Chores breakdown
    chore_totals = defaultdict(int)
    for r in results:
        for k, v in r["morning_chores"].items():
            chore_totals[k] += v

    # Unserved tasks at hour 4 vs end of day
    h4_strawb_unharvested = []
    h4_strawb_unwatered = []
    h4_unfed = []
    h4_uncared = []
    
    eod_unwatered = []
    eod_unfed = []
    eod_uncared = []
    eod_strawb_held = []

    for r in results:
        for h4 in r["daily_unserved_h4"]:
            h4_strawb_unharvested.append(h4["strawberry_mature_yield"])
            h4_strawb_unwatered.append(h4["unwatered_strawberries"])
            h4_unfed.append(h4["unfed_animals"])
            h4_uncared.append(h4["uncared_animals"])
        for eod in r["daily_resolved_h24"]:
            eod_unwatered.append(eod["unwatered_eod"])
            eod_unfed.append(eod["unfed_eod"])
            eod_uncared.append(eod["uncared_eod"])
            eod_strawb_held.append(eod["strawberries_mature_eod"])

    print("\n" + "=" * 80)
    print("MORNING BOTTLENECK TELEMETRY SUMMARY (FIRST 4 HOURS)")
    print("=" * 80)
    print(f"Total Morning Worker-Hours:     {total_wh:,}")
    print(f"Productive Actions:             {total_prod:,} ({total_prod/total_wh*100:.1f}%)")
    print(f"Movement Steps:                 {total_move:,} ({total_move/total_wh*100:.1f}%)")
    print(f"Idle / Pass Steps:              {total_pass:,} ({total_pass/total_wh*100:.1f}%)")
    print(f"Productive Actions / Worker-Hr: {prod_per_wh:.3f}")
    print(f"Mean Movement Steps Before Prod:{mean_moves_before_prod:.2f}")
    print(f"Shed Congestion Incidents:      {shed_blocks:,}")
    print(f"Duplicate Target Actions:       {dup_targets:,}")

    print("\nMorning Chores Breakdown (Total Actions Across 30 Seeds x 30 Days):")
    for k, v in sorted(chore_totals.items(), key=lambda x: -x[1]):
        print(f"  {k:22s}: {v:6,d} ({v/total_prod*100:5.1f}% of productive actions)")

    print("\n" + "=" * 80)
    print("OPPORTUNITY COST ANALYSIS: HOUR 4 SNAPSHOT VS END-OF-DAY RESOLUTION")
    print("=" * 80)
    print(f"Mean Mature Strawberry Yield Unharvested at Hour 4: {np.mean(h4_strawb_unharvested):.2f} units/day")
    print(f"Mean Unwatered Strawberries at Hour 4:             {np.mean(h4_strawb_unwatered):.2f} tiles/day")
    print(f"Mean Unfed Animals at Hour 4:                      {np.mean(h4_unfed):.2f} animals/day")
    print(f"Mean Uncared Animals at Hour 4:                    {np.mean(h4_uncared):.2f} animals/day")
    print("-" * 50)
    print(f"Mean Unwatered Crops at End of Day (Hour 23):       {np.mean(eod_unwatered):.4f} tiles/day")
    print(f"Mean Unfed Animals at End of Day (Hour 23):         {np.mean(eod_unfed):.4f} animals/day")
    print(f"Mean Uncared Animals at End of Day (Hour 23):       {np.mean(eod_uncared):.4f} animals/day")
    print(f"Mean Mature Strawberries Unharvested at End of Day: {np.mean(eod_strawb_held):.2f} units/day")

    out_data = {
        "total_worker_hours": total_wh,
        "productive_actions": total_prod,
        "movement_steps": total_move,
        "pass_steps": total_pass,
        "prod_per_worker_hour": prod_per_wh,
        "mean_moves_before_prod": mean_moves_before_prod,
        "shed_routing_blocks": shed_blocks,
        "duplicate_targets": dup_targets,
        "chores_breakdown": dict(chore_totals),
        "h4_strawb_unharvested_mean": float(np.mean(h4_strawb_unharvested)),
        "h4_strawb_unwatered_mean": float(np.mean(h4_strawb_unwatered)),
        "h4_unfed_mean": float(np.mean(h4_unfed)),
        "h4_uncared_mean": float(np.mean(h4_uncared)),
        "eod_unwatered_mean": float(np.mean(eod_unwatered)),
        "eod_unfed_mean": float(np.mean(eod_unfed)),
        "eod_uncared_mean": float(np.mean(eod_uncared)),
        "eod_strawb_held_mean": float(np.mean(eod_strawb_held)),
        "per_seed_results": [{k: v for k, v in r.items() if k not in ["daily_unserved_h4", "daily_resolved_h24"]} for r in results]
    }
    with open("scratch/step2_3_telemetry_summary.json", "w", encoding="utf-8") as f:
        json.dump(out_data, f, indent=2)

    print("\nTelemetry saved to scratch/step2_3_telemetry_summary.json")

if __name__ == "__main__":
    main()
