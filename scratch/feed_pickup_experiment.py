"""
Phase 5: Feed Pickup Batching Experiment (Seeds 1000–1009)
=========================================================
Tests controlled variants modifying ONLY the livestock feed pickup logic:

ARM A: Baseline CL-Economic-V1 (batch_pickup = min(6, len(hungry), shed_wheat), workers 0-3)
ARM B: Moderate Batching (batch_pickup = min(6, shed_wheat), always takes full 6 units)
ARM C: Large Batching (batch_pickup = min(14, shed_wheat), takes up to 14 units)
ARM D: Dedicated Feeder (Only Worker 1 fetches feed, takes up to 14 units; other workers stay in fields)
ARM E: Coordinated Shared Feeder (Only 1 worker dispatched to shed at a time, bulk batch = min(12, shed_wheat))
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

class FeedBatchingAgent(ClosedLoopEconomicV1):
    def __init__(self, feed_policy="BASELINE"):
        super().__init__()
        self.feed_policy = feed_policy

    def _dispatch_workers(self, all_workers, all_invs, tiles, shed, seeds, quads, day, hour, scan_res, step):
        actions = [None] * len(all_workers)
        claimed_action_tiles = set()
        ns = _nearest_shed(all_workers[0], tiles)
        target_pasture_slots = scan_res.get("target_pasture_slots", set())

        if hour == 0:
            self._worker_targets.clear()

        # Step 1: Local-First Execution on Current Tile (Identical to Baseline)
        for i, (pos, inv) in enumerate(zip(all_workers, all_invs)):
            x, y = pos
            t = tiles[y][x] if 0 <= y < BOARD and 0 <= x < BOARD else None
            produce_load = sum(int(inv.get(it, 0) or 0) for it in PRODUCE_TO_DROP)
            w_inv = int(inv.get("WHEAT", 0) or 0)
            cow_inv = int(inv.get("COW", 0) or 0)
            sheep_inv = int(inv.get("SHEEP", 0) or 0)

            if pos in SHED_ACCESS and produce_load > 0 and (cow_inv + sheep_inv) == 0 and (w_inv == 0 or not scan_res["hungry"]):
                actions[i] = ["DROP"]
                claimed_action_tiles.add(pos)
                self._worker_targets.pop(i, None)
                continue

            if isinstance(t, dict):
                k = t.get("kind")
                if k == "PLANT":
                    crop = t.get("crop")
                    fert_inv = int(inv.get("FERTILIZER", 0) or 0)
                    if pos in scan_res["ripe_crops"] and pos not in claimed_action_tiles:
                        actions[i] = ["HARVEST"]; claimed_action_tiles.add(pos); self._worker_targets.pop(i, None); continue
                    if crop != "WHEAT" and fert_inv > 0 and t.get("fertilized_until_day", -1) < day and pos not in claimed_action_tiles:
                        actions[i] = ["FERTILIZE"]; claimed_action_tiles.add(pos); self._worker_targets.pop(i, None); continue
                    if not t.get("watered_today") and pos not in claimed_action_tiles:
                        actions[i] = ["WATER"]; claimed_action_tiles.add(pos); self._worker_targets.pop(i, None); continue
                elif k == "PASTURE":
                    if t.get("animal"):
                        if not t.get("fed_today") and w_inv > 0 and pos not in claimed_action_tiles:
                            actions[i] = ["FEED"]; claimed_action_tiles.add(pos); self._worker_targets.pop(i, None); continue
                        if not t.get("cared_today") and pos not in claimed_action_tiles:
                            actions[i] = ["CARE"]; claimed_action_tiles.add(pos); self._worker_targets.pop(i, None); continue
                        if int(t.get("yield_units", 0) or 0) > 0 and pos not in claimed_action_tiles:
                            actions[i] = ["HARVEST"]; claimed_action_tiles.add(pos); self._worker_targets.pop(i, None); continue
                        if t.get("fertilizer_available") and pos not in claimed_action_tiles:
                            actions[i] = ["COLLECT_FERTILIZER"]; claimed_action_tiles.add(pos); self._worker_targets.pop(i, None); continue
                    else:
                        desired_sp = PASTURE_SPECIES.get(pos, "COW")
                        if desired_sp == "SHEEP" and sheep_inv > 0 and pos not in claimed_action_tiles:
                            actions[i] = ["PLACE", "SHEEP"]; claimed_action_tiles.add(pos); self._worker_targets.pop(i, None); continue
                        elif desired_sp == "COW" and cow_inv > 0 and pos not in claimed_action_tiles:
                            actions[i] = ["PLACE", "COW"]; claimed_action_tiles.add(pos); self._worker_targets.pop(i, None); continue
                        elif cow_inv > 0 and pos not in claimed_action_tiles:
                            actions[i] = ["PLACE", "COW"]; claimed_action_tiles.add(pos); self._worker_targets.pop(i, None); continue
                        elif sheep_inv > 0 and pos not in claimed_action_tiles:
                            actions[i] = ["PLACE", "SHEEP"]; claimed_action_tiles.add(pos); self._worker_targets.pop(i, None); continue
                elif k == "WEED" and pos not in claimed_action_tiles:
                    actions[i] = ["DIG"]; claimed_action_tiles.add(pos); self._worker_targets.pop(i, None); continue
            elif t is None:
                if pos in scan_res["unbuilt_p"] and pos not in claimed_action_tiles:
                    actions[i] = ["BUILD_PASTURE"]; claimed_action_tiles.add(pos); self._worker_targets.pop(i, None); continue
                if pos in scan_res["plant_s"] and int(seeds.get("STRAWBERRY", 0) or 0) > 0 and pos not in claimed_action_tiles:
                    seeds["STRAWBERRY"] = max(0, int(seeds.get("STRAWBERRY")) - 1)
                    actions[i] = ["PLANT", "STRAWBERRY"]; claimed_action_tiles.add(pos); self._worker_targets.pop(i, None); continue
                if pos in scan_res["plant_m"] and int(seeds.get("MELON", 0) or 0) > 0 and pos not in claimed_action_tiles:
                    seeds["MELON"] = max(0, int(seeds.get("MELON")) - 1)
                    actions[i] = ["PLANT", "MELON"]; claimed_action_tiles.add(pos); self._worker_targets.pop(i, None); continue
                if pos in scan_res["plant_w"] and int(seeds.get("WHEAT", 0) or 0) > 0 and pos not in claimed_action_tiles:
                    seeds["WHEAT"] = max(0, int(seeds.get("WHEAT")) - 1)
                    actions[i] = ["PLANT", "WHEAT"]; claimed_action_tiles.add(pos); self._worker_targets.pop(i, None); continue

        # Step 2: Validate active commitments
        unassigned_workers = []
        for i, (pos, inv) in enumerate(zip(all_workers, all_invs)):
            if actions[i] is not None:
                continue
            produce_load = sum(int(inv.get(it, 0) or 0) for it in PRODUCE_TO_DROP)
            w_inv = int(inv.get("WHEAT", 0) or 0)
            valid = False

            if i in self._worker_targets:
                active_t, task_type, sc = self._worker_targets[i]
                if sc < 15 and active_t not in claimed_action_tiles:
                    ax, ay = active_t
                    at = tiles[ay][ax] if 0 <= ay < BOARD and 0 <= ax < BOARD else None
                    if task_type == "WATER" and isinstance(at, dict) and not at.get("watered_today"): valid = True
                    elif task_type == "HARVEST" and isinstance(at, dict) and int(at.get("yield_units", 0) or 0) > 0: valid = True
                    elif task_type == "FEED" and w_inv > 0 and isinstance(at, dict) and not at.get("fed_today"): valid = True
                    elif task_type == "DROP" and produce_load > 0: valid = True

                    if valid:
                        self._worker_targets[i] = (active_t, task_type, sc + 1)
                        claimed_action_tiles.add(active_t)
                        actions[i] = [_bfs_step(pos, active_t, tiles)]
                    else:
                        self._worker_targets.pop(i, None)
                else:
                    self._worker_targets.pop(i, None)
            if not valid:
                unassigned_workers.append(i)

        if not unassigned_workers:
            return actions

        # Step 3: Priority Handling for Animal Handling & FEED BATCHING
        has_animals_in_shed = (int(shed.get("COW", 0) or 0) + int(shed.get("SHEEP", 0) or 0)) > 0
        still_unassigned = []
        
        # Calculate feed batch parameters
        wheat_in_shed = int(shed.get("WHEAT", 0) or 0)
        total_wheat_in_hands = sum(int(inv.get("WHEAT", 0) or 0) for inv in all_invs)
        feed_needed = len(scan_res["hungry"])
        deficit = max(0, feed_needed - total_wheat_in_hands)
        
        # Check if another worker is already en route to shed for feed
        someone_heading_to_shed_for_feed = any(
            self._worker_targets.get(w, (None, None))[1] == "PICKUP" and
            int(all_invs[w].get("WHEAT", 0) or 0) == 0
            for w in range(len(all_workers))
        )

        for w in unassigned_workers:
            pos = all_workers[w]
            inv = all_invs[w]
            cow_inv = int(inv.get("COW", 0) or 0)
            sheep_inv = int(inv.get("SHEEP", 0) or 0)
            w_inv = int(inv.get("WHEAT", 0) or 0)

            # Animal Placement
            if (cow_inv + sheep_inv) > 0:
                car_sp = "COW" if cow_inv > 0 else "SHEEP"
                matching_slots = [p for p in target_pasture_slots if PASTURE_SPECIES.get(p) == car_sp and p not in claimed_action_tiles]
                cands = [p for p in matching_slots if p in scan_res["empty_p"]] or [p for p in matching_slots if p in scan_res["unbuilt_p"]] or [p for p in scan_res["empty_p"] if p not in claimed_action_tiles]
                if cands:
                    t = min(cands, key=lambda p: _dist(pos, p))
                    claimed_action_tiles.add(t)
                    self._worker_targets[w] = (t, "PLACE", 1)
                    actions[w] = [_bfs_step(pos, t, tiles)]
                    continue
            elif has_animals_in_shed and (cow_inv + sheep_inv) == 0 and (w in (0, 1) or hour <= 3):
                if pos in SHED_ACCESS:
                    if int(shed.get("COW", 0) or 0) > 0: actions[w] = ["PICKUP", "COW", 1]; continue
                    elif int(shed.get("SHEEP", 0) or 0) > 0: actions[w] = ["PICKUP", "SHEEP", 1]; continue
                else:
                    claimed_action_tiles.add(ns)
                    self._worker_targets[w] = (ns, "PICKUP", 1)
                    actions[w] = [_bfs_step(pos, ns, tiles)]
                    continue

            # FEEDING & FEED PICKUP LOGIC
            if scan_res["hungry"]:
                if w_inv > 0:
                    cands = [h for h in scan_res["hungry"] if h not in claimed_action_tiles]
                    if cands:
                        t = min(cands, key=lambda p: _dist(pos, p))
                        claimed_action_tiles.add(t)
                        self._worker_targets[w] = (t, "FEED", 1)
                        actions[w] = [_bfs_step(pos, t, tiles)]
                        continue
                elif wheat_in_shed > 0:
                    should_fetch = False
                    batch_pickup = 1

                    if self.feed_policy == "BASELINE":
                        should_fetch = (w in (0, 1, 2, 3) or hour <= 6)
                        batch_pickup = min(6, len(scan_res["hungry"]), wheat_in_shed)

                    elif self.feed_policy == "MODERATE_BATCH":
                        should_fetch = (w in (0, 1) or hour <= 6) and (deficit > 0 or someone_heading_to_shed_for_feed is False)
                        batch_pickup = min(6, wheat_in_shed)

                    elif self.feed_policy == "LARGE_BATCH":
                        should_fetch = (w in (0, 1) or hour <= 6) and (deficit > 0 or someone_heading_to_shed_for_feed is False)
                        batch_pickup = min(14, wheat_in_shed)

                    elif self.feed_policy == "DEDICATED_FEEDER":
                        # Only worker 1 fetches feed; other workers stay in fields!
                        should_fetch = (w == 1) or (hour >= 18 and deficit > 0 and w == 0)
                        batch_pickup = min(14, wheat_in_shed)

                    elif self.feed_policy == "COORDINATED_SHARED":
                        # Only fetch if there is an actual net deficit and nobody else is currently fetching
                        if deficit > 0 and not someone_heading_to_shed_for_feed:
                            should_fetch = (w in (0, 1, 2) or hour <= 6)
                            batch_pickup = min(12, max(6, deficit), wheat_in_shed)

                    if should_fetch:
                        if pos in SHED_ACCESS:
                            actions[w] = ["PICKUP", "WHEAT", batch_pickup]
                            continue
                        else:
                            claimed_action_tiles.add(ns)
                            self._worker_targets[w] = (ns, "PICKUP", 1)
                            actions[w] = [_bfs_step(pos, ns, tiles)]
                            someone_heading_to_shed_for_feed = True
                            continue

            still_unassigned.append(w)

        if not still_unassigned:
            return actions

        # Step 4: Priority Pools Matching (Identical to Baseline)
        priority_pools = [
            ("URGENT_WATER", scan_res["urgent_unwatered"]),
            ("RIPE_ANIMAL", scan_res["ripe_a"]),
            ("FERT", scan_res["fert"]),
            ("HARVEST_CROPS", scan_res["ripe_crops"]),
            ("WATER_CROPS", scan_res["unwatered"]),
            ("PLANT_STRAW", scan_res["plant_s"] if int(seeds.get("STRAWBERRY", 0) or 0) > 0 else []),
            ("PLANT_MELON", scan_res["plant_m"] if int(seeds.get("MELON", 0) or 0) > 0 else []),
            ("PLANT_WHEAT", scan_res["plant_w"] if int(seeds.get("WHEAT", 0) or 0) > 0 else []),
            ("UNBUILT_P", scan_res["unbuilt_p"]),
            ("WEEDS", scan_res["weeds"]),
        ]

        assigned_workers = set()
        for pool_name, pool_cands in priority_pools:
            avail_cands = [c for c in pool_cands if c not in claimed_action_tiles]
            avail_workers = [w for w in still_unassigned if w not in assigned_workers]
            if not avail_cands or not avail_workers:
                continue

            cost_matrix = []
            for w in avail_workers:
                w_pos = all_workers[w]
                pref_q = self._worker_preferred_quad(w)
                row = []
                for c in avail_cands:
                    d = _dist(w_pos, c)
                    c_q = _quad(c[0], c[1])
                    zone_pen = 0.0 if c_q == pref_q else 2.0
                    cx, cy = c
                    cb = 0.0
                    for ox, oy in avail_cands:
                        if (ox, oy) == c: continue
                        cd = abs(cx - ox) + abs(cy - oy)
                        if cd == 1: cb += 2.5
                        elif cd == 2: cb += 1.0
                    local_bonus = 3.0 if d <= 2 else 0.0
                    cost = d + zone_pen - 0.4 * cb - local_bonus
                    row.append(cost)
                cost_matrix.append(row)

            matching = min_cost_bipartite_matching(cost_matrix)
            for w_idx_sub, c_idx_sub in matching:
                w = avail_workers[w_idx_sub]
                chosen_cand = avail_cands[c_idx_sub]
                claimed_action_tiles.add(chosen_cand)
                assigned_workers.add(w)
                self._worker_targets[w] = (chosen_cand, pool_name, 1)
                actions[w] = [_bfs_step(all_workers[w], chosen_cand, tiles)]

        # Step 5: Opportunistic Logistics (Identical to Baseline)
        for w in still_unassigned:
            if w not in assigned_workers:
                pos = all_workers[w]
                inv = all_invs[w]
                produce_load = sum(int(inv.get(it, 0) or 0) for it in PRODUCE_TO_DROP)
                if produce_load > 0 and (hour >= 20 or produce_load >= 5 or _dist(pos, ns) <= 2):
                    actions[w] = [_bfs_step(pos, ns, tiles)]
                    self._worker_targets[w] = (ns, "DROP", 1)
                else:
                    actions[w] = ["PASS"]

        return actions


def run_feed_match(args):
    arm_name, seed = args
    from scratch.produce_drop_threshold_experiment import run_produce_experiment_match
    # Custom runner
    cfg = {"episodeSteps": 720, "seed": seed}
    env = kaggle_environments.make("kaggriculture", configuration=cfg, debug=False)
    agent_inst = FeedBatchingAgent(feed_policy=arm_name)
    env.run([agent_inst, "starter"])
    
    steps = env.steps
    total_steps = len(steps)
    
    harvest_counts = Counter()
    total_harvests = 0
    total_pickups = 0
    total_drops = 0
    total_moves = 0
    total_prods = 0
    total_idles = 0
    wheat_pickups = 0
    wheat_picked_up_units = 0
    
    care_daily = []
    
    for s_idx in range(1, total_steps):
        prev_f = steps[s_idx - 1][0]["observation"]["farms"][0]
        curr_f = steps[s_idx][0]["observation"]["farms"][0]
        act = steps[s_idx][0].get("action") or {}
        all_acts = [act.get("farmer") or ["PASS"]] + (act.get("hands") or [])
        workers = [tuple(prev_f["farmer"])] + [tuple(h) for h in prev_f["hands"]]
        
        for w_idx, a in enumerate(all_acts):
            if not a: total_idles += 1; continue
            op = a[0]
            if op in ("NORTH", "SOUTH", "EAST", "WEST"): total_moves += 1
            elif op in ("WATER", "HARVEST", "FEED", "CARE", "PLANT", "BUILD_PASTURE", "FERTILIZE", "COLLECT_FERTILIZER", "DIG", "DROP", "PICKUP", "PLACE"): total_prods += 1
            else: total_idles += 1
            
            if op == "HARVEST":
                total_harvests += 1
                pos = workers[w_idx] if w_idx < len(workers) else (0, 0)
                t = prev_f["tiles"][pos[1]][pos[0]] if 0 <= pos[1] < 10 and 0 <= pos[0] < 10 else None
                if isinstance(t, dict):
                    k = t.get("kind")
                    yu = int(t.get("yield_units", 0) or 0)
                    if k == "PLANT": harvest_counts[t.get("crop")] += yu
                    elif k == "PASTURE": harvest_counts[t.get("animal")] += yu
            elif op == "PICKUP":
                total_pickups += 1
                if len(a) > 1 and a[1] == "WHEAT":
                    wheat_pickups += 1
                    wheat_picked_up_units += int(a[2]) if len(a) > 2 else 1
            elif op == "DROP":
                total_drops += 1
                
        if (s_idx % 24) == 23:
            animals = [t for row in curr_f["tiles"] for t in row if isinstance(t, dict) and t.get("kind") == "PASTURE" and t.get("animal")]
            if animals:
                cared = sum(1 for t in animals if t.get("cared_today") and t.get("fed_today"))
                care_daily.append(cared / len(animals))
                
    reward = float(steps[-1][0].get("reward") or 0.0)
    return {
        "arm": arm_name,
        "seed": seed,
        "reward": reward,
        "harvests": total_harvests,
        "pickups": total_pickups,
        "wheat_pickups": wheat_pickups,
        "wheat_picked_up_units": wheat_picked_up_units,
        "mean_wheat_batch": wheat_picked_up_units / max(1, wheat_pickups),
        "drops": total_drops,
        "moves": total_moves,
        "prods": total_prods,
        "idles": total_idles,
        "straw": harvest_counts.get("STRAWBERRY", 0),
        "wool": harvest_counts.get("SHEEP", 0),
        "wheat": harvest_counts.get("WHEAT", 0),
        "milk": harvest_counts.get("COW", 0),
        "care_fed_pct": float(np.mean(care_daily)) * 100 if care_daily else 100.0
    }


def run_feed_study(seeds=list(range(1000, 1010))):
    arms = [
        "BASELINE",
        "MODERATE_BATCH",
        "LARGE_BATCH",
        "DEDICATED_FEEDER",
        "COORDINATED_SHARED"
    ]
    
    tasks = []
    for arm in arms:
        for s in seeds:
            tasks.append((arm, s))
            
    print(f"Running Phase 5 Feed Pickup Batching Study across {len(seeds)} Seeds (50 matches total)...")
    t0 = time.time()
    results = defaultdict(list)
    with ProcessPoolExecutor(max_workers=10) as ex:
        futs = [ex.submit(run_feed_match, t) for t in tasks]
        for f in as_completed(futs):
            res = f.result()
            results[res["arm"]].append(res)
            
    print(f"Completed in {time.time()-t0:.1f}s.")
    
    with open("scratch/feed_batching_results.json", "w") as f:
        json.dump({arm: lst for arm, lst in results.items()}, f, indent=2)
        
    print("\n" + "=" * 115)
    print(f"{'ARM':<20} | {'Reward ($)':<16} | {'Harvests':<9} | {'Pickups':<8} | {'WheatPick':<9} | {'Batch':<6} | {'Moves':<7} | {'Wool':<7} | {'CareFed%':<8}")
    print("-" * 115)
    
    summary = {}
    for arm in arms:
        lst = results[arm]
        lst.sort(key=lambda x: x["seed"])
        rewards = [r["reward"] for r in lst]
        harvests = [r["harvests"] for r in lst]
        pickups = [r["pickups"] for r in lst]
        w_picks = [r["wheat_pickups"] for r in lst]
        batches = [r["mean_wheat_batch"] for r in lst]
        moves = [r["moves"] for r in lst]
        straws = [r["straw"] for r in lst]
        wools = [r["wool"] for r in lst]
        milks = [r["milk"] for r in lst]
        cares = [r["care_fed_pct"] for r in lst]
        
        m_rew = float(np.mean(rewards))
        m_harv = float(np.mean(harvests))
        m_pick = float(np.mean(pickups))
        m_wpick = float(np.mean(w_picks))
        m_bat = float(np.mean(batches))
        m_mov = float(np.mean(moves))
        m_wol = float(np.mean(wools))
        m_car = float(np.mean(cares))
        
        summary[arm] = {
            "mean_reward": m_rew,
            "std_reward": float(np.std(rewards)),
            "median_reward": float(np.median(rewards)),
            "mean_harvests": m_harv,
            "mean_pickups": m_pick,
            "mean_wheat_pickups": m_wpick,
            "mean_wheat_batch": m_bat,
            "mean_moves": m_mov,
            "mean_straw": float(np.mean(straws)),
            "mean_wool": m_wol,
            "mean_milk": float(np.mean(milks)),
            "mean_care_fed_pct": m_car
        }
        
        print(f"{arm:<20} | ${m_rew:10.2f} ± ${np.std(rewards):5.0f} | {m_harv:9.1f} | {m_pick:8.1f} | {m_wpick:9.1f} | {m_bat:5.1f}u | {m_mov:7.1f} | {m_wol:7.1f} | {m_car:6.1f}%")
        
    with open("scratch/feed_batching_summary.json", "w") as f:
        json.dump(summary, f, indent=2)

if __name__ == "__main__":
    run_feed_study()
