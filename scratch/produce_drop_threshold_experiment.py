"""
Phase 4: Produce-Drop Threshold Curve Experiment (Seeds 1000–1009)
==================================================================
Tests 7 controlled variants modifying ONLY the produce drop trigger:

ARM A: Baseline CL-Economic-V1 (drop if produce >= 5 OR hour >= 20 OR dist <= 2)
ARM B: Drop >= 3 (strictly produce >= 3, no opportunistic dist <= 2, Day 29 terminal flush)
ARM C: Drop >= 5 (strictly produce >= 5, no opportunistic dist <= 2, Day 29 terminal flush)
ARM D: Drop >= 8 (strictly produce >= 8, Day 29 terminal flush)
ARM E: Drop >= 10 (strictly produce >= 10, Day 29 terminal flush)
ARM F: Pocket-Capacity / Terminal Only (drop if produce >= 15 OR Day 29 terminal flush)
ARM G: Hybrid Adaptive (drop if produce >= 8 OR (cash < $400 and produce >= 3 and day <= 10) OR Day >= 28)
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

class ProduceBatchingAgent(ClosedLoopEconomicV1):
    def __init__(self, drop_policy="BASELINE"):
        super().__init__()
        self.drop_policy = drop_policy

    def _should_drop_produce(self, pos, inv, produce_load, hour, day, money, ns):
        if produce_load <= 0:
            return False
            
        if self.drop_policy == "BASELINE":
            # Current CL-Economic-V1 baseline trigger
            return (hour >= 20 or produce_load >= 5 or _dist(pos, ns) <= 2)

        # Terminal liquidation: ALWAYS flush produce to shed on Day 28–29 so market can sell it!
        if day >= 28:
            return True

        if self.drop_policy == "DROP_GE_3":
            return produce_load >= 3

        if self.drop_policy == "DROP_GE_5":
            return produce_load >= 5

        if self.drop_policy == "DROP_GE_8":
            return produce_load >= 8

        if self.drop_policy == "DROP_GE_10":
            return produce_load >= 10

        if self.drop_policy == "CAPACITY_OR_TERMINAL":
            # Engine auto-drops all pockets into shed every midnight at hour 23!
            # So only drop if pocket has >= 15 units or terminal
            return produce_load >= 15

        if self.drop_policy == "HYBRID_ADAPTIVE":
            # 1. High payload: >= 8 units
            if produce_load >= 8:
                return True
            # 2. Early game liquidity need: if cash is low and we need money for animal/seed
            if day <= 10 and money < 400 and produce_load >= 3 and _dist(pos, ns) <= 3:
                return True
            # 3. Otherwise, keep working in the field!
            return False

        return False

    def _dispatch_workers(self, all_workers, all_invs, tiles, shed, seeds, quads, day, hour, scan_res, step):
        actions = [None] * len(all_workers)
        claimed_action_tiles = set()
        ns = _nearest_shed(all_workers[0], tiles)
        target_pasture_slots = scan_res.get("target_pasture_slots", set())

        if hour == 0:
            self._worker_targets.clear()

        # Step 1: Local-First Execution on Current Tile
        for i, (pos, inv) in enumerate(zip(all_workers, all_invs)):
            x, y = pos
            t = tiles[y][x] if 0 <= y < BOARD and 0 <= x < BOARD else None
            produce_load = sum(int(inv.get(it, 0) or 0) for it in PRODUCE_TO_DROP)
            w_inv = int(inv.get("WHEAT", 0) or 0)
            cow_inv = int(inv.get("COW", 0) or 0)
            sheep_inv = int(inv.get("SHEEP", 0) or 0)

            # Check if standing on shed tile and policy permits drop
            if pos in SHED_ACCESS and produce_load > 0 and (cow_inv + sheep_inv) == 0 and (w_inv == 0 or not scan_res["hungry"]):
                if self._should_drop_produce(pos, inv, produce_load, hour, day, self._money if hasattr(self, '_money') else 1000, ns):
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
                    elif task_type == "DROP" and self._should_drop_produce(pos, inv, produce_load, hour, day, self._money if hasattr(self, '_money') else 1000, ns): valid = True

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

        # Step 3: Animal Handling & JIT Feeding (Identical to Baseline)
        has_animals_in_shed = (int(shed.get("COW", 0) or 0) + int(shed.get("SHEEP", 0) or 0)) > 0
        still_unassigned = []
        for w in unassigned_workers:
            pos = all_workers[w]
            inv = all_invs[w]
            cow_inv = int(inv.get("COW", 0) or 0)
            sheep_inv = int(inv.get("SHEEP", 0) or 0)
            w_inv = int(inv.get("WHEAT", 0) or 0)

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

            if scan_res["hungry"]:
                if w_inv > 0:
                    cands = [h for h in scan_res["hungry"] if h not in claimed_action_tiles]
                    if cands:
                        t = min(cands, key=lambda p: _dist(pos, p))
                        claimed_action_tiles.add(t)
                        self._worker_targets[w] = (t, "FEED", 1)
                        actions[w] = [_bfs_step(pos, t, tiles)]
                        continue
                elif int(shed.get("WHEAT", 0) or 0) > 0 and (w in (0, 1, 2, 3) or hour <= 6):
                    if pos in SHED_ACCESS:
                        batch_pickup = min(6, len(scan_res["hungry"]), int(shed.get("WHEAT")))
                        actions[w] = ["PICKUP", "WHEAT", batch_pickup]
                        continue
                    else:
                        claimed_action_tiles.add(ns)
                        self._worker_targets[w] = (ns, "PICKUP", 1)
                        actions[w] = [_bfs_step(pos, ns, tiles)]
                        continue

            still_unassigned.append(w)

        if not still_unassigned:
            return actions

        # Step 4: Joint Multi-Worker Target Allocation (Identical to Baseline)
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

        # Step 5: Opportunistic Logistics Fallback
        for w in still_unassigned:
            if w not in assigned_workers:
                pos = all_workers[w]
                inv = all_invs[w]
                produce_load = sum(int(inv.get(it, 0) or 0) for it in PRODUCE_TO_DROP)
                if self._should_drop_produce(pos, inv, produce_load, hour, day, self._money if hasattr(self, '_money') else 1000, ns):
                    actions[w] = [_bfs_step(pos, ns, tiles)]
                    self._worker_targets[w] = (ns, "DROP", 1)
                else:
                    actions[w] = ["PASS"]

        return actions


def run_produce_experiment_match(args):
    arm_name, seed = args
    from scratch.reconstruct_shed_logistics import instrument_cl_logistics
    agent_factory = lambda: ProduceBatchingAgent(drop_policy=arm_name)
    
    cfg = {"episodeSteps": 720, "seed": seed}
    env = kaggle_environments.make("kaggriculture", configuration=cfg, debug=False)
    agent_inst = agent_factory()
    env.run([agent_inst, "starter"])
    
    steps = env.steps
    total_steps = len(steps)
    
    drop_payloads = []
    harvest_counts = Counter()
    total_harvests = 0
    total_pickups = 0
    total_drops = 0
    total_moves = 0
    total_prods = 0
    total_idles = 0
    shed_max = 0
    
    for s_idx in range(1, total_steps):
        prev_f = steps[s_idx - 1][0]["observation"]["farms"][0]
        act = steps[s_idx][0].get("action") or {}
        all_acts = [act.get("farmer") or ["PASS"]] + (act.get("hands") or [])
        workers = [tuple(prev_f["farmer"])] + [tuple(h) for h in prev_f["hands"]]
        priv = steps[s_idx - 1][0]["observation"].get("private") or {}
        shed = priv.get("shed") or {}
        invs = priv.get("inventories") or []
        
        s_occ = sum(int(v or 0) for v in shed.values())
        if s_occ > shed_max: shed_max = s_occ
        
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
            elif op == "DROP":
                total_drops += 1
                p_inv = invs[w_idx] if w_idx < len(invs) else {}
                load = sum(int(v or 0) for v in p_inv.values())
                drop_payloads.append(load)
            elif op == "PICKUP":
                total_pickups += 1
                
    reward = float(steps[-1][0].get("reward") or 0.0)
    cash = float(steps[-1][0]["observation"]["farms"][0].get("money") or 0.0)
    
    return {
        "arm": arm_name,
        "seed": seed,
        "reward": reward,
        "cash": cash,
        "harvests": total_harvests,
        "pickups": total_pickups,
        "drops": total_drops,
        "mean_payload": float(np.mean(drop_payloads)) if drop_payloads else 0.0,
        "moves": total_moves,
        "prods": total_prods,
        "idles": total_idles,
        "straw": harvest_counts.get("STRAWBERRY", 0),
        "wool": harvest_counts.get("SHEEP", 0),
        "wheat": harvest_counts.get("WHEAT", 0),
        "melon": harvest_counts.get("MELON", 0),
        "milk": harvest_counts.get("COW", 0),
        "shed_max": shed_max
    }


def run_produce_drop_study(seeds=list(range(1000, 1010))):
    arms = [
        "BASELINE",
        "DROP_GE_3",
        "DROP_GE_5",
        "DROP_GE_8",
        "DROP_GE_10",
        "CAPACITY_OR_TERMINAL",
        "HYBRID_ADAPTIVE"
    ]
    
    tasks = []
    for arm in arms:
        for s in seeds:
            tasks.append((arm, s))
            
    print(f"Running Phase 4 Produce-Drop Threshold Curve Study (7 arms x {len(seeds)} seeds = 70 matches)...")
    t0 = time.time()
    results = defaultdict(list)
    with ProcessPoolExecutor(max_workers=10) as ex:
        futs = [ex.submit(run_produce_experiment_match, t) for t in tasks]
        for f in as_completed(futs):
            res = f.result()
            results[res["arm"]].append(res)
            
    print(f"Completed in {time.time()-t0:.1f}s.")
    
    with open("scratch/produce_threshold_results.json", "w") as f:
        json.dump({arm: lst for arm, lst in results.items()}, f, indent=2)
        
    print("\n" + "=" * 115)
    print(f"{'ARM':<22} | {'Reward ($)':<16} | {'Harvests':<9} | {'Drops':<7} | {'Payload':<8} | {'Moves':<7} | {'Straw':<7} | {'Wool':<7} | {'Melon':<7}")
    print("-" * 115)
    
    summary = {}
    for arm in arms:
        lst = results[arm]
        lst.sort(key=lambda x: x["seed"])
        rewards = [r["reward"] for r in lst]
        harvests = [r["harvests"] for r in lst]
        drops = [r["drops"] for r in lst]
        payloads = [r["mean_payload"] for r in lst]
        moves = [r["moves"] for r in lst]
        prods = [r["prods"] for r in lst]
        straws = [r["straw"] for r in lst]
        wools = [r["wool"] for r in lst]
        wheats = [r["wheat"] for r in lst]
        melons = [r["melon"] for r in lst]
        shed_maxes = [r["shed_max"] for r in lst]
        
        m_rew = float(np.mean(rewards))
        m_harv = float(np.mean(harvests))
        m_drop = float(np.mean(drops))
        m_pay = float(np.mean(payloads))
        m_mov = float(np.mean(moves))
        m_str = float(np.mean(straws))
        m_wol = float(np.mean(wools))
        m_mel = float(np.mean(melons))
        
        summary[arm] = {
            "mean_reward": m_rew,
            "std_reward": float(np.std(rewards)),
            "median_reward": float(np.median(rewards)),
            "mean_harvests": m_harv,
            "mean_drops": m_drop,
            "mean_payload": m_pay,
            "mean_moves": m_mov,
            "mean_prods": float(np.mean(prods)),
            "mean_straw": m_str,
            "mean_wool": m_wol,
            "mean_wheat": float(np.mean(wheats)),
            "mean_melon": m_mel,
            "mean_shed_max": float(np.mean(shed_maxes))
        }
        
        print(f"{arm:<22} | ${m_rew:10.2f} ± ${np.std(rewards):5.0f} | {m_harv:9.1f} | {m_drop:7.1f} | {m_pay:7.2f}u | {m_mov:7.1f} | {m_str:7.1f} | {m_wol:7.1f} | {m_mel:7.1f}")
        
    with open("scratch/produce_threshold_summary.json", "w") as f:
        json.dump(summary, f, indent=2)

if __name__ == "__main__":
    run_produce_drop_study()
