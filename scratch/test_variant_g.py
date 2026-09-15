"""
Variant G: Contiguous NE Strawberry + Active Care with Protected Wool
=====================================================================
Refines Variant F by:
1. Protecting Sheep Care & Shearing: ensures animal care and shearing are not delayed by fertilizer trips.
2. Production-Day Strawberry Irrigation: maintains priority watering for strawberry bushes on production nights.
3. Proactive Strawberry Fertilization: dispatches idle or nearby workers with fertilizer to strawberry bushes.
"""

import sys
import os
import copy
from collections import defaultdict
import numpy as np
from concurrent.futures import ProcessPoolExecutor

PROJECT_ROOT = os.path.abspath(".")
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import kaggle_environments
from scratch.strawberry_variants import VariantE_ContiguousNE
from candidates.candidate_cl_economic_v1 import (
    BOARD, TPD, SHED_ACCESS, WELL_ACCESS, CROPS_DEF,
    PASTURE_SLOTS, PASTURE_SPECIES, PRODUCE_TO_DROP,
    _dist, _quad, _nearest_shed, _bfs_step, min_cost_bipartite_matching
)

class VariantG_ProtectedWool(VariantE_ContiguousNE):
    def _scan_field(self, tiles, quads, seeds, shed, invs, day):
        scan = super()._scan_field(tiles, quads, seeds, shed, invs, day)
        prod_straw_unwatered = []
        unfert_straw = []
        other_unwatered = []
        
        for pos in scan.get("unwatered", []):
            x, y = pos
            t = tiles[y][x] if tiles else None
            if isinstance(t, dict) and t.get("kind") == "PLANT" and t.get("crop") == "STRAWBERRY":
                pd = int(t.get("planted_day", 0))
                dsf = (day + 1) - pd - 10
                if dsf >= 0 and dsf % 2 == 0 and (dsf // 2 + 1) <= 4:
                    prod_straw_unwatered.append(pos)
                else:
                    other_unwatered.append(pos)
            else:
                other_unwatered.append(pos)
                
        for y in range(BOARD):
            for x in range(BOARD):
                pos = (x, y)
                t = tiles[y][x] if tiles else None
                if isinstance(t, dict) and t.get("kind") == "PLANT" and t.get("crop") == "STRAWBERRY":
                    if t.get("fertilized_until_day", -1) < day:
                        pd = int(t.get("planted_day", 0))
                        dsf = (day + 1) - pd - 10
                        if dsf >= -1 and (dsf // 2 + 1) <= 4:
                            unfert_straw.append(pos)
                            
        scan["prod_straw_unwatered"] = prod_straw_unwatered
        scan["unfert_straw"] = unfert_straw
        scan["other_unwatered"] = other_unwatered
        return scan

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
                    if crop == "STRAWBERRY" and fert_inv > 0 and t.get("fertilized_until_day", -1) < day and pos not in claimed_action_tiles:
                        actions[i] = ["FERTILIZE"]; claimed_action_tiles.add(pos); self._worker_targets.pop(i, None); continue
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

        # Step 2: Active commitments
        unassigned_workers = []
        for i, (pos, inv) in enumerate(zip(all_workers, all_invs)):
            if actions[i] is not None: continue
            produce_load = sum(int(inv.get(it, 0) or 0) for it in PRODUCE_TO_DROP)
            w_inv = int(inv.get("WHEAT", 0) or 0)
            valid = False
            if i in self._worker_targets:
                active_t, task_type, sc = self._worker_targets[i]
                if sc < 15 and active_t not in claimed_action_tiles:
                    ax, ay = active_t
                    at = tiles[ay][ax] if 0 <= ay < BOARD and 0 <= ax < BOARD else None
                    if task_type in ("WATER", "PROD_WATER") and isinstance(at, dict) and not at.get("watered_today"): valid = True
                    elif task_type == "FERT_STRAW" and isinstance(at, dict) and at.get("fertilized_until_day", -1) < day: valid = True
                    elif task_type == "HARVEST" and isinstance(at, dict) and int(at.get("yield_units", 0) or 0) > 0: valid = True
                    elif task_type == "FEED" and w_inv > 0 and isinstance(at, dict) and not at.get("fed_today"): valid = True
                    elif task_type == "CARE" and isinstance(at, dict) and not at.get("cared_today"): valid = True
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

        # Step 3: Livestock Feeding & Placement
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

        # Step 4: Protected Animal Care & Shearing FIRST (Preserves $200 Wool)
        # Priority pools ensure RIPE_ANIMAL and CARE_ANIMAL come BEFORE fertilizer excursions!
        priority_pools = [
            ("URGENT_WATER", scan_res["urgent_unwatered"]),
            ("RIPE_ANIMAL", scan_res["ripe_a"]),
            ("CARE_ANIMAL", scan_res["care_a"]),
            ("PROD_STRAW_WATER", scan_res.get("prod_straw_unwatered", [])),
            ("FERT", scan_res["fert"]),
            ("HARVEST_CROPS", scan_res["ripe_crops"]),
            ("WATER_CROPS", scan_res.get("other_unwatered", [])),
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
                    prod_bonus = 4.0 if pool_name == "PROD_STRAW_WATER" else 0.0
                    animal_bonus = 3.0 if pool_name in ("RIPE_ANIMAL", "CARE_ANIMAL") else 0.0
                    cost = d + zone_pen - 0.4 * cb - local_bonus - prod_bonus - animal_bonus
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

        still_unassigned = [w for w in still_unassigned if w not in assigned_workers]
        
        # Step 5: Opportunistic Proactive Fertilizer Trip for Remaining Free Workers
        workers_with_fert = [w for w in still_unassigned if int(all_invs[w].get("FERTILIZER", 0) or 0) > 0]
        unfert_cands = [c for c in scan_res.get("unfert_straw", []) if c not in claimed_action_tiles]
        for w in workers_with_fert:
            if unfert_cands:
                t = min(unfert_cands, key=lambda p: _dist(all_workers[w], p))
                unfert_cands.remove(t)
                claimed_action_tiles.add(t)
                assigned_workers.add(w)
                self._worker_targets[w] = (t, "FERT_STRAW", 1)
                actions[w] = [_bfs_step(all_workers[w], t, tiles)]

        # Step 6: En-Route Logistics & Fallback
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

def eval_single(seed):
    agent = VariantG_ProtectedWool()
    cfg = {"episodeSteps": 720, "seed": seed}
    env = kaggle_environments.make("kaggriculture", configuration=cfg)
    env.run([agent, "starter"])
    steps = env.steps
    reward = float(steps[-1][0].get("reward") or 0.0)
    sales = defaultdict(int)
    for s in range(1, len(steps)):
        act = steps[s][0].get("action") or {}
        for o in (act.get("market") or []):
            if isinstance(o, list) and len(o) > 2 and o[0] == "SELL":
                sales[o[1]] += int(o[2])
    return {
        "seed": seed, "reward": reward,
        "straw_sold": sales.get("STRAWBERRY", 0),
        "wool_sold": sales.get("WOOL", 0),
        "milk_sold": sales.get("MILK", 0),
        "wheat_sold": sales.get("WHEAT", 0),
        "fert_sold": sales.get("FERTILIZER", 0),
    }

if __name__ == "__main__":
    seeds = range(1000, 1050)
    print(f"Running Variant G (Protected Wool) on {len(seeds)} seeds...")
    with ProcessPoolExecutor(max_workers=10) as ex:
        res = list(ex.map(eval_single, seeds))
    
    rewards = [r["reward"] for r in res]
    straw = [r["straw_sold"] for r in res]
    wool = [r["wool_sold"] for r in res]
    milk = [r["milk_sold"] for r in res]
    
    mean_r = np.mean(rewards)
    med_r = np.median(rewards)
    std_r = np.std(rewards)
    ci95 = 1.96 * std_r / np.sqrt(len(rewards))
    
    print("\n" + "="*80)
    print("VARIANT G (PROTECTED WOOL) RESULTS (50 SEEDS: 1000-1049)")
    print("="*80)
    print(f"Mean Reward:       ${mean_r:,.2f}  ±${ci95:,.2f}")
    print(f"Median Reward:     ${med_r:,.2f}")
    print(f"Mean Straw Sold:   {np.mean(straw):.1f} units")
    print(f"Mean Wool Sold:    {np.mean(wool):.1f} units")
    print(f"Mean Milk Sold:    {np.mean(milk):.1f} units")
    print("="*80)
