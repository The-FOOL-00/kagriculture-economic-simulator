"""
Pure Dispatch Ablation Harness & Controlled Pilot Experiment (Steps 6, 7, 8)
============================================================================
Implements:
1. Dispatcher Base with identical task generation from CL-Economic-V1
2. ARM A: Baseline CL-Economic-V1 dispatcher
3. ARM B: Minimal Distance-Aware Dispatcher with:
   priority_adjusted_score = economic_priority - lambda * travel_distance
   with emergency overrides for urgent watering, animal care, at-risk crops, and required logistics.
4. Three lambda parameter settings: LOW, MEDIUM, HIGH.
5. 10-seed pilot (Seeds 1040-1049) across the 4 arms (40 games).
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

# Base Economic Priorities (Documented Scale):
# Units: Economic priority points (calibrated so emergency tasks > 1000, standard ops 100-500)
BASE_PRIORITIES = {
    "URGENT_WATER": 1200.0,   # Emergency: Plant withering risk
    "RIPE_ANIMAL": 1000.0,    # High value: Wool ($200) or Milk ($160) ready
    "CARE_ANIMAL": 950.0,     # High value: Animal productivity / health
    "FEED_ANIMAL": 900.0,     # High value: Prevent hunger penalty
    "FERT": 550.0,            # Fertilizer collection ($100 base revenue)
    "HARVEST_CROPS": 450.0,   # Batch harvest: Strawberry ($240+), Melon ($1250)
    "WATER_CROPS": 320.0,     # Standard daily watering ($30-$60/day value)
    "PLANT_STRAW": 240.0,     # Ongoing Strawberry planting
    "PLANT_MELON": 200.0,     # Melon planting
    "UNBUILT_P": 180.0,       # Pasture construction for livestock
    "PLANT_WHEAT": 120.0,     # Wheat planting
    "WEEDS": 60.0,            # Clearing weeds
}

# Emergency task types that CANNOT be overpowered by distance penalties
EMERGENCY_TYPES = frozenset(["URGENT_WATER", "RIPE_ANIMAL", "CARE_ANIMAL", "FEED_ANIMAL"])


class DistanceAwareDispatcherAgent(ClosedLoopEconomicV1):
    """
    Subclasses CL-Economic-V1.
    Keeps 100% of the economic policy, crop choices, animal acquisitions,
    fertilizer logic, market trading, and scan_field task generation IDENTICAL.
    Only modifies worker assignment in _dispatch_workers using the distance penalty.
    """
    def __init__(self, lambda_val=0.0, policy_name="BASELINE"):
        super().__init__()
        self.lambda_val = float(lambda_val)
        self.policy_name = policy_name

    def _dispatch_workers(self, all_workers, all_invs, tiles, shed, seeds, quads, day, hour, scan_res, step):
        if self.policy_name == "BASELINE":
            # Run exact parent baseline dispatcher
            return super()._dispatch_workers(all_workers, all_invs, tiles, shed, seeds, quads, day, hour, scan_res, step)

        # Distance-Aware Dispatcher (Arm B)
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

        # Step 3: Emergency Animal Handling & JIT Feeding (Emergency Override: Always Protected!)
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

        # Step 4: Distance-Aware Joint Matching
        # Gather all candidate tasks across pools
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

        # Flatten available candidate tasks: (pos, pool_name, base_priority, is_emergency)
        all_cands = []
        seen_cand_pos = set()
        for pool_name, c_list in priority_pools:
            base_p = BASE_PRIORITIES.get(pool_name, 50.0)
            is_emerg = pool_name in EMERGENCY_TYPES
            for c in c_list:
                if c not in claimed_action_tiles and c not in seen_cand_pos:
                    all_cands.append((c, pool_name, base_p, is_emerg))
                    seen_cand_pos.add(c)

        if not all_cands or not still_unassigned:
            # Fallback to Step 5
            pass
        else:
            # Build cost matrix for bipartite matching
            # Cost = - priority_adjusted_score
            # priority_adjusted_score = base_priority - lambda * dist (for non-emergency)
            # For emergency: base_priority is huge (1000+), so emergency tasks always dominate!
            # To format as min-cost matching: cost = (MaxScore - score)
            MAX_SCORE = 2000.0
            cost_matrix = []
            for w in still_unassigned:
                w_pos = all_workers[w]
                row = []
                for c_pos, p_name, base_p, is_emerg in all_cands:
                    d = _dist(w_pos, c_pos)
                    if is_emerg:
                        # Distance is only a minor tie-breaker; emergency priority is preserved
                        score = base_p - 0.1 * d
                    else:
                        score = base_p - self.lambda_val * d
                    cost = MAX_SCORE - score
                    row.append(max(0.0, cost))
                cost_matrix.append(row)

            matching = min_cost_bipartite_matching(cost_matrix)
            assigned_workers = set()
            for w_sub, c_sub in matching:
                w = still_unassigned[w_sub]
                chosen_cand, pool_name, _, _ = all_cands[c_sub]
                claimed_action_tiles.add(chosen_cand)
                assigned_workers.add(w)
                self._worker_targets[w] = (chosen_cand, pool_name, 1)
                actions[w] = [_bfs_step(all_workers[w], chosen_cand, tiles)]

            still_unassigned = [w for w in still_unassigned if w not in assigned_workers]

        # Step 5: Opportunistic Logistics & Fallback (Identical to Baseline)
        for w in still_unassigned:
            pos = all_workers[w]
            inv = all_invs[w]
            produce_load = sum(int(inv.get(it, 0) or 0) for it in PRODUCE_TO_DROP)
            if produce_load > 0 and (hour >= 20 or produce_load >= 5 or _dist(pos, ns) <= 2):
                actions[w] = [_bfs_step(pos, ns, tiles)]
                self._worker_targets[w] = (ns, "DROP", 1)
            else:
                actions[w] = ["PASS"]

        return actions


def run_pilot_match(args):
    arm_name, lambda_val, seed = args
    from scratch.run_protocol_phase1 import run_single_seed_metrics
    agent_factory = lambda: DistanceAwareDispatcherAgent(lambda_val=lambda_val, policy_name=arm_name)
    res = run_single_seed_metrics(seed, agent_cls_factory=agent_factory)
    res["arm"] = arm_name
    res["lambda"] = lambda_val
    return res


def run_controlled_pilot(seeds=list(range(1040, 1050))):
    """
    Runs 10 seeds (1040-1049) across 4 arms:
    ARM A: Baseline
    ARM B (Low): lambda = 3.0
    ARM B (Med): lambda = 8.0
    ARM B (High): lambda = 15.0
    Total = 40 matches
    """
    arms = [
        ("BASELINE", 0.0),
        ("LOW_LAMBDA", 3.0),
        ("MED_LAMBDA", 8.0),
        ("HIGH_LAMBDA", 15.0),
    ]

    tasks = []
    for arm_name, lam in arms:
        for s in seeds:
            tasks.append((arm_name, lam, s))

    print(f"Executing 40 Pilot Simulations across Seeds {seeds[0]}–{seeds[-1]}...")
    t0 = time.time()
    results = defaultdict(list)
    with ProcessPoolExecutor(max_workers=10) as ex:
        futs = [ex.submit(run_pilot_match, t) for t in tasks]
        for f in as_completed(futs):
            res = f.result()
            results[res["arm"]].append(res)

    print(f"Pilot completed in {time.time()-t0:.1f}s.")
    return results

if __name__ == "__main__":
    print("Testing pilot harness single match...")
    t0 = time.time()
    test_res = run_pilot_match(("LOW_LAMBDA", 3.0, 1040))
    print(f"Match completed in {time.time()-t0:.2f}s: Reward=${test_res['reward']:,.2f}, Moves={test_res['movement_turns']}")
