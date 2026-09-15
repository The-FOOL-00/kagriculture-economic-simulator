"""
Controlled Strawberry Capacity & Irrigation Variants
====================================================
Subclasses of ClosedLoopEconomicV1 implementing:
- Variant A: Baseline CL-Economic-V1 (Target 40, scattered layout)
- Variant B: Moderate Expansion (Target 24 bushes)
- Variant C: Large Expansion (Target 32 bushes)
- Variant D: Aggressive Expansion (Target 48 bushes)
- Variant E: Contiguous NE Clustered Layout (Target 36 bushes, spatially clustered)
- Variant F: Contiguous NE + Production-Day Irrigation & Proactive Fertilization
"""

import sys
import os
import copy
from collections import deque

PROJECT_ROOT = os.path.abspath(".")
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from candidates.candidate_cl_economic_v1 import (
    ClosedLoopEconomicV1, BOARD, TPD, SHED_ACCESS, WELL_ACCESS,
    CROPS_DEF, PASTURE_SLOTS, PASTURE_SPECIES, MELON_TILES_D0,
    MELON_DESIGNATED_TILES, WHEAT_TILES_D0, SELLABLE, PRODUCE_TO_DROP,
    BASE_PRICES, MOVES, _fib, _dist, _quad, _walkable, _bfs_step,
    _nearest_shed, min_cost_bipartite_matching
)

# Define Contiguous NE Strawberry Cluster (20 tiles in NE)
NE_CONTIGUOUS_STRAWBERRY = frozenset([
    (5, 0), (6, 0), (7, 0), (8, 0), (9, 0),
    (5, 1), (6, 1), (7, 1), (8, 1), (9, 1),
    (5, 2), (6, 2), (7, 2), (8, 2), (9, 2),
    (7, 3), (8, 3), (9, 3), (8, 4), (9, 4)
])

# Combined contiguous zone: 7 NW vacated melon tiles + 20 NE contiguous tiles = 27 primary tiles
# Plus 8 SW tiles = up to 35-40 tiles
NW_VACATED_MELON = frozenset([
    (0, 0), (1, 0), (2, 0), (3, 0), (4, 0),
    (0, 1), (1, 1)
])

# ---------------------------------------------------------------------------
# Variant B: Moderate Capacity (Target 24)
# ---------------------------------------------------------------------------
class VariantB_Moderate24(ClosedLoopEconomicV1):
    def _macro_market(self, step, day, hour, money, quads, tiles, shed, seeds, hired, invs, obs):
        orders = super()._macro_market(step, day, hour, money, quads, tiles, shed, seeds, hired, invs, obs)
        # Cap strawberry buying at target 24
        if hour == 0 and 4 <= day <= 20:
            straw_f = sum(1 for r in tiles for t in r if isinstance(t, dict) and t.get("crop") == "STRAWBERRY")
            straw_s = int(seeds.get("STRAWBERRY", 0) or 0)
            target_straw = 8 if day < 7 else 24
            needed = max(0, target_straw - straw_f - straw_s)
            # Filter out and replace strawberry order if present
            new_orders = []
            for o in orders:
                if len(o) > 1 and o[0] == "BUY_SEED" and o[1] == "STRAWBERRY":
                    if needed > 0 and money >= 250:
                        can_buy = min(needed, min(8, int((money - 150) // 100)))
                        if can_buy > 0:
                            new_orders.append(["BUY_SEED", "STRAWBERRY", can_buy])
                else:
                    new_orders.append(o)
            orders = new_orders
        return orders

# ---------------------------------------------------------------------------
# Variant C: Large Capacity (Target 32)
# ---------------------------------------------------------------------------
class VariantC_Large32(ClosedLoopEconomicV1):
    def _macro_market(self, step, day, hour, money, quads, tiles, shed, seeds, hired, invs, obs):
        orders = super()._macro_market(step, day, hour, money, quads, tiles, shed, seeds, hired, invs, obs)
        if hour == 0 and 4 <= day <= 20:
            straw_f = sum(1 for r in tiles for t in r if isinstance(t, dict) and t.get("crop") == "STRAWBERRY")
            straw_s = int(seeds.get("STRAWBERRY", 0) or 0)
            target_straw = 8 if day < 7 else (24 if day < 10 else 32)
            needed = max(0, target_straw - straw_f - straw_s)
            new_orders = []
            for o in orders:
                if len(o) > 1 and o[0] == "BUY_SEED" and o[1] == "STRAWBERRY":
                    if needed > 0 and money >= 250:
                        can_buy = min(needed, min(8, int((money - 150) // 100)))
                        if can_buy > 0:
                            new_orders.append(["BUY_SEED", "STRAWBERRY", can_buy])
                else:
                    new_orders.append(o)
            orders = new_orders
        return orders

# ---------------------------------------------------------------------------
# Variant D: Aggressive Capacity (Target 48)
# ---------------------------------------------------------------------------
class VariantD_Aggressive48(ClosedLoopEconomicV1):
    def _macro_market(self, step, day, hour, money, quads, tiles, shed, seeds, hired, invs, obs):
        orders = super()._macro_market(step, day, hour, money, quads, tiles, shed, seeds, hired, invs, obs)
        if hour == 0 and 4 <= day <= 20:
            straw_f = sum(1 for r in tiles for t in r if isinstance(t, dict) and t.get("crop") == "STRAWBERRY")
            straw_s = int(seeds.get("STRAWBERRY", 0) or 0)
            target_straw = 8 if day < 7 else (24 if day < 10 else 48)
            needed = max(0, target_straw - straw_f - straw_s)
            new_orders = []
            for o in orders:
                if len(o) > 1 and o[0] == "BUY_SEED" and o[1] == "STRAWBERRY":
                    if needed > 0 and money >= 250:
                        can_buy = min(needed, min(8, int((money - 150) // 100)))
                        if can_buy > 0:
                            new_orders.append(["BUY_SEED", "STRAWBERRY", can_buy])
                else:
                    new_orders.append(o)
            orders = new_orders
        return orders

# ---------------------------------------------------------------------------
# Variant E: Contiguous NE Clustered Layout (Target 36)
# ---------------------------------------------------------------------------
class VariantE_ContiguousNE(ClosedLoopEconomicV1):
    def _macro_market(self, step, day, hour, money, quads, tiles, shed, seeds, hired, invs, obs):
        orders = super()._macro_market(step, day, hour, money, quads, tiles, shed, seeds, hired, invs, obs)
        if hour == 0 and 4 <= day <= 20:
            straw_f = sum(1 for r in tiles for t in r if isinstance(t, dict) and t.get("crop") == "STRAWBERRY")
            straw_s = int(seeds.get("STRAWBERRY", 0) or 0)
            target_straw = 8 if day < 7 else (24 if day < 10 else 36)
            needed = max(0, target_straw - straw_f - straw_s)
            new_orders = []
            for o in orders:
                if len(o) > 1 and o[0] == "BUY_SEED" and o[1] == "STRAWBERRY":
                    if needed > 0 and money >= 250:
                        can_buy = min(needed, min(8, int((money - 150) // 100)))
                        if can_buy > 0:
                            new_orders.append(["BUY_SEED", "STRAWBERRY", can_buy])
                else:
                    new_orders.append(o)
            orders = new_orders
        return orders

    def _scan_field(self, tiles, quads, seeds, shed, invs, day):
        scan = super()._scan_field(tiles, quads, seeds, shed, invs, day)
        # Prioritize Contiguous NE tiles for strawberry planting
        plant_s = scan.get("plant_s", [])
        if plant_s:
            # Sort plant_s so NE contiguous tiles and NW vacated melon tiles come first
            def straw_tile_priority(pos):
                if pos in NE_CONTIGUOUS_STRAWBERRY: return 0
                if pos in NW_VACATED_MELON: return 1
                return 2 + _dist(pos, (7, 2))
            plant_s.sort(key=straw_tile_priority)
            scan["plant_s"] = plant_s
        return scan

# ---------------------------------------------------------------------------
# Variant F: Contiguous NE + Production-Day Irrigation & Proactive Fertilization
# ---------------------------------------------------------------------------
class VariantF_ActiveCare(VariantE_ContiguousNE):
    def _scan_field(self, tiles, quads, seeds, shed, invs, day):
        scan = super()._scan_field(tiles, quads, seeds, shed, invs, day)
        
        # Identify strawberry bushes with production night TONIGHT
        # In engine: STRAWBERRY: first_yield_day=10, interval=2, max_yield=4.
        # Production event triggers if: days_since_first = (day + 1) - planted_day - 10 >= 0
        # and days_since_first % 2 == 0 and (days_since_first // 2 + 1) <= 4.
        # This requires watering TODAY (day)!
        
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
                
        # Also identify strawberry bushes that are NOT fertilized yet
        for y in range(BOARD):
            for x in range(BOARD):
                pos = (x, y)
                t = tiles[y][x] if tiles else None
                if isinstance(t, dict) and t.get("kind") == "PLANT" and t.get("crop") == "STRAWBERRY":
                    if t.get("fertilized_until_day", -1) < day:
                        pd = int(t.get("planted_day", 0))
                        dsf = (day + 1) - pd - 10
                        # Needs fertilizer before or on production day
                        if dsf >= -1 and (dsf // 2 + 1) <= 4:
                            unfert_straw.append(pos)
                            
        scan["prod_straw_unwatered"] = prod_straw_unwatered
        scan["unfert_straw"] = unfert_straw
        scan["other_unwatered"] = other_unwatered
        return scan

    def _dispatch_workers(self, all_workers, all_invs, tiles, shed, seeds, quads, day, hour, scan_res, step):
        # Dispatch with Production-Day Priority
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
                    
                    # PROACTIVE FERTILIZE: Prioritize Strawberry fertilization
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

        # Step 4: Proactive Fertilizer Carrier Dispatch
        # If a worker carries fertilizer and there are unfertilized strawberry bushes, route worker directly to them!
        workers_with_fert = [w for w in still_unassigned if int(all_invs[w].get("FERTILIZER", 0) or 0) > 0]
        unfert_cands = [c for c in scan_res.get("unfert_straw", []) if c not in claimed_action_tiles]
        assigned_fert_workers = set()
        for w in workers_with_fert:
            if unfert_cands:
                t = min(unfert_cands, key=lambda p: _dist(all_workers[w], p))
                unfert_cands.remove(t)
                claimed_action_tiles.add(t)
                assigned_fert_workers.add(w)
                self._worker_targets[w] = (t, "FERT_STRAW", 1)
                actions[w] = [_bfs_step(all_workers[w], t, tiles)]

        still_unassigned = [w for w in still_unassigned if w not in assigned_fert_workers]
        if not still_unassigned:
            return actions

        # Step 5: Prioritized Priority Pools (URGENT -> PROD_STRAW_WATER -> RIPE_ANIMAL -> HARVEST -> OTHER_WATER)
        priority_pools = [
            ("URGENT_WATER", scan_res["urgent_unwatered"]),
            ("PROD_STRAW_WATER", scan_res.get("prod_straw_unwatered", [])),
            ("RIPE_ANIMAL", scan_res["ripe_a"]),
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
                    # Prioritize production-day strawberry watering
                    prod_bonus = 4.0 if pool_name == "PROD_STRAW_WATER" else 0.0
                    cost = d + zone_pen - 0.4 * cb - local_bonus - prod_bonus
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

        # Step 6: En-Route Opportunistic Logistics & Fallback
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
