"""
Modular Economic Arms Generator for Closed-Loop Ablation Study
Subclasses ClosedLoopCoordinatedV1 directly to ensure 100% execution fidelity
while modifying exactly ONE economic policy per Arm.
"""

import sys
import os

PROJECT_ROOT = os.path.abspath(".")
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from candidates.candidate_cl_coordinated_v1 import (
    ClosedLoopCoordinatedV1, _fib, _dist, _quad, _bfs_step,
    BOARD, TPD, SHED_ACCESS, WELL_ACCESS, CROPS_DEF,
    PASTURE_SLOTS, PASTURE_SPECIES, MELON_TILES_D0,
    MELON_DESIGNATED_TILES, WHEAT_TILES_D0, SELLABLE,
    PRODUCE_TO_DROP, BASE_PRICES, min_cost_bipartite_matching
)

# ---------------------------------------------------------------------------
# Arm A: Baseline CL-Coordinated-V1 (Control)
# ---------------------------------------------------------------------------
class ArmABaseline(ClosedLoopCoordinatedV1):
    pass


# ---------------------------------------------------------------------------
# Arm B: Worker Hiring Cap (Max Hands = 11)
# ---------------------------------------------------------------------------
class ArmBWorkerCap(ClosedLoopCoordinatedV1):
    def _macro_market(self, step, day, hour, money, quads, tiles, shed, seeds, hired, invs, obs):
        orders = super()._macro_market(step, day, hour, money, quads, tiles, shed, seeds, hired, invs, obs)
        # Re-filter hiring orders to cap at 11 hands
        filtered_orders = []
        cur_h = hired
        for order in orders:
            if order and order[0] == "HIRE":
                if cur_h < 11:
                    filtered_orders.append(order)
                    cur_h += 1
            else:
                filtered_orders.append(order)
        return filtered_orders[:10]


# ---------------------------------------------------------------------------
# Arm C: Fertilizer Rationalization (Never fertilize Wheat)
# ---------------------------------------------------------------------------
class ArmCFertilizerRational(ClosedLoopCoordinatedV1):
    def _dispatch_workers(self, all_workers, all_invs, tiles, shed, seeds, quads, day, hour, scan_res, step):
        # We intercept local-first execution: prohibit fertilizing wheat
        actions = [None] * len(all_workers)
        claimed_action_tiles = set()
        ns = (4, 4)
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
                    
                    # STRICT GUARD: DO NOT FERTILIZE WHEAT!
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

        # Remainder follows standard ClosedLoopCoordinatedV1 dispatch
        return self._finish_dispatch(actions, claimed_action_tiles, all_workers, all_invs, tiles, shed, seeds, quads, day, hour, scan_res, step)

    def _finish_dispatch(self, actions, claimed_action_tiles, all_workers, all_invs, tiles, shed, seeds, quads, day, hour, scan_res, step):
        # Calls the parent dispatch logic for steps 2-5
        # Reconstruct unassigned_workers
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

        # Step 3: Priority Handling for Animal Handling & JIT Feeding
        ns = (4, 4)
        target_pasture_slots = scan_res.get("target_pasture_slots", set())
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

        # Step 4: Joint Multi-Worker Target Allocation with Cluster Lock & Spatial Affinity
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

        # Step 5: En-Route Opportunistic Logistics & Fallback
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


# ---------------------------------------------------------------------------
# Arm D: Crop Harvest Batching (Strawberry yield_units >= 2)
# ---------------------------------------------------------------------------
class ArmDStrawberryBatch(ClosedLoopCoordinatedV1):
    def _scan_field(self, tiles, quads, seeds, shed, invs, day):
        scan_res = super()._scan_field(tiles, quads, seeds, shed, invs, day)
        
        # Override ripe_crops: require strawberry yield >= 2 (or day >= 27)
        new_ripe = []
        for y in range(BOARD):
            for x in range(BOARD):
                t = tiles[y][x] if tiles else None
                if not isinstance(t, dict) or t.get("kind") != "PLANT":
                    continue
                crop = t.get("crop")
                c_def = CROPS_DEF.get(crop, {})
                first_yd = c_def.get("first_yield_day", 2)
                age = day - int(t.get("planted_day", 0) or 0)
                yu = int(t.get("yield_units", 0) or 0)

                if yu > 0 and age >= first_yd:
                    if crop == "MELON":
                        if yu >= 5 or day >= 27:
                            new_ripe.append((x, y))
                    elif crop == "WHEAT":
                        if yu >= 4 or day >= 27:
                            new_ripe.append((x, y))
                    elif crop == "STRAWBERRY":
                        # BATCH HARVEST: require at least 2 strawberries!
                        if yu >= 2 or day >= 27:
                            new_ripe.append((x, y))
                    else:
                        new_ripe.append((x, y))
                        
        scan_res["ripe_crops"] = new_ripe
        return scan_res


# ---------------------------------------------------------------------------
# Arm E: Livestock Acquisition (Cow Priority & Day >= 5)
# ---------------------------------------------------------------------------
class ArmELivestockPriority(ClosedLoopCoordinatedV1):
    def _macro_market(self, step, day, hour, money, quads, tiles, shed, seeds, hired, invs, obs):
        orders = []

        if step == 0:
            if money >= 2780:
                return [
                    ["BUY_ANIMAL", "COW", 3],
                    ["BUY_ANIMAL", "SHEEP", 1],
                    ["BUY_SEED", "MELON", 7],
                    ["BUY_SEED", "WHEAT", 10],
                    ["BUY_PRODUCT", "WHEAT", 17],
                    ["HIRE"], ["HIRE"]
                ]
            else:
                cur_m = money
                ret = []
                if cur_m >= 400: ret.append(["BUY_ANIMAL", "COW", 1]); cur_m -= 400
                if cur_m >= 100: ret.append(["BUY_SEED", "WHEAT", min(10, int(cur_m // 10))])
                if cur_m >= 1: ret.append(["HIRE"])
                return ret

        cows_f = sum(1 for r in tiles for t in r if isinstance(t, dict) and t.get("animal") == "COW")
        sheep_f = sum(1 for r in tiles for t in r if isinstance(t, dict) and t.get("animal") == "SHEEP")
        cows_inv = sum(int(inv.get("COW", 0) or 0) for inv in invs)
        sheep_inv = sum(int(inv.get("SHEEP", 0) or 0) for inv in invs)
        cows_tot = cows_f + int(shed.get("COW", 0) or 0) + cows_inv
        sheep_tot = sheep_f + int(shed.get("SHEEP", 0) or 0) + sheep_inv
        n_animals = cows_tot + sheep_tot

        prices = (obs.get("market") or {}).get("prices") or {}
        sells = []
        for item in ("MELON", "WOOL", "MILK", "STRAWBERRY", "FERTILIZER", "EGG", "WHEAT"):
            qty = int(shed.get(item, 0) or 0)
            if item == "WHEAT":
                feed_res = max(15, n_animals * 2)
                qty = max(0, qty - feed_res)
            if qty > 0:
                p_val = float(prices.get(item, BASE_PRICES.get(item, 100)) or 100)
                sells.append((qty * p_val, item, qty))
        sells.sort(reverse=True)
        for _, item, qty in sells[:5]:
            orders.append(["SELL", item, qty])

        total_wheat = int(shed.get("WHEAT", 0) or 0) + sum(int(inv.get("WHEAT", 0) or 0) for inv in invs)
        target_feed_buffer = max(15, n_animals * 2)
        if n_animals > 0 and total_wheat < target_feed_buffer and money >= 80 and len(orders) < 8:
            need_feed = target_feed_buffer - total_wheat
            can_feed = min(need_feed, min(10, int((money - 50) // 30)))
            if can_feed > 0:
                orders.append(["BUY_PRODUCT", "WHEAT", can_feed])
                money -= can_feed * 30

        if len(quads) == 1 and money >= 1050 and day >= 7 and len(orders) < 8:
            orders.append(["BUY_LAND"])
            money -= 1000
        elif len(quads) == 2 and money >= 2100 and day >= 10 and len(orders) < 8:
            orders.append(["BUY_LAND"])
            money -= 2000

        shed_anim_count = int(shed.get("COW", 0) or 0) + int(shed.get("SHEEP", 0) or 0) + cows_inv + sheep_inv
        # COW PRIORITY: Unlock at Day 5, buy COW before SHEEP!
        if shed_anim_count == 0 and hour == 0 and n_animals < 14:
            if ("NE" in quads or (len(quads) == 1 and day >= 5)) and 5 <= day <= 22 and len(orders) < 8:
                target_cows = 8
                target_sheep = 6
                cows_needed = max(0, target_cows - cows_tot)
                sheep_needed = max(0, target_sheep - sheep_tot)
                
                # BUY COW FIRST!
                if cows_needed > 0 and money >= 650 and len(orders) < 8:
                    can_buy_c = min(cows_needed, min(2, int((money - 250) // 400)))
                    if can_buy_c > 0:
                        orders.append(["BUY_ANIMAL", "COW", can_buy_c])
                        money -= can_buy_c * 400
                        cows_tot += can_buy_c
                if sheep_needed > 0 and money >= 750 and len(orders) < 8:
                    can_buy_s = min(sheep_needed, min(3, int((money - 250) // 500)))
                    if can_buy_s > 0:
                        orders.append(["BUY_ANIMAL", "SHEEP", can_buy_s])
                        money -= can_buy_s * 500
                        sheep_tot += can_buy_s

        if hour == 0 and 4 <= day <= 22 and len(orders) < 8:
            melons_f = sum(1 for r in tiles for t in r if isinstance(t, dict) and t.get("crop") == "MELON")
            melons_s = int(seeds.get("MELON", 0) or 0)
            target_melons = 7 if day < 7 else (11 if day < 12 else 16)
            needed_m = max(0, target_melons - (melons_f + melons_s))
            if needed_m > 0 and money >= 250:
                can_buy_m = min(needed_m, min(6, int((money - 150) // 80)))
                if can_buy_m > 0:
                    orders.append(["BUY_SEED", "MELON", can_buy_m])
                    money -= can_buy_m * 80

        if hour == 0 and 4 <= day <= 20 and len(orders) < 8:
            straw_f = sum(1 for r in tiles for t in r if isinstance(t, dict) and t.get("crop") == "STRAWBERRY")
            straw_s = int(seeds.get("STRAWBERRY", 0) or 0)
            target_straw = 4 if day < 7 else (18 if day < 10 else 40)
            needed = max(0, target_straw - straw_f - straw_s)
            if needed > 0 and money >= 250:
                can_buy = min(needed, min(8, int((money - 150) // 100)))
                if can_buy > 0:
                    orders.append(["BUY_SEED", "STRAWBERRY", can_buy])
                    money -= can_buy * 100

        if hour == 0 and 2 <= day <= 24 and len(orders) < 8:
            wheat_s = int(seeds.get("WHEAT", 0) or 0)
            if wheat_s < 10 and money >= 200:
                can_buy_w = min(10 - wheat_s, min(10, int((money - 150) // 10)))
                if can_buy_w > 0:
                    orders.append(["BUY_SEED", "WHEAT", can_buy_w])
                    money -= can_buy_w * 10

        if day == 0: target_hands = 5
        elif day < 4: target_hands = 4
        elif day < 7: target_hands = 6
        elif day < 10: target_hands = 9
        elif day < 20: target_hands = 12
        else: target_hands = 13

        cur_h = hired
        budget = money
        while cur_h < target_hands and len(orders) < 10:
            cost = _fib(cur_h)
            if budget >= cost:
                orders.append(["HIRE"])
                budget -= cost
                cur_h += 1
            else:
                break

        return orders[:10]


# ---------------------------------------------------------------------------
# Arm F: JIT Feed Buffering
# ---------------------------------------------------------------------------
class ArmFFeedBuffering(ClosedLoopCoordinatedV1):
    def _macro_market(self, step, day, hour, money, quads, tiles, shed, seeds, hired, invs, obs):
        orders = []

        if step == 0:
            if money >= 2780:
                return [
                    ["BUY_ANIMAL", "COW", 3],
                    ["BUY_ANIMAL", "SHEEP", 1],
                    ["BUY_SEED", "MELON", 7],
                    ["BUY_SEED", "WHEAT", 10],
                    ["BUY_PRODUCT", "WHEAT", 17],
                    ["HIRE"], ["HIRE"]
                ]
            else:
                cur_m = money
                ret = []
                if cur_m >= 400: ret.append(["BUY_ANIMAL", "COW", 1]); cur_m -= 400
                if cur_m >= 100: ret.append(["BUY_SEED", "WHEAT", min(10, int(cur_m // 10))])
                if cur_m >= 1: ret.append(["HIRE"])
                return ret

        cows_f = sum(1 for r in tiles for t in r if isinstance(t, dict) and t.get("animal") == "COW")
        sheep_f = sum(1 for r in tiles for t in r if isinstance(t, dict) and t.get("animal") == "SHEEP")
        cows_inv = sum(int(inv.get("COW", 0) or 0) for inv in invs)
        sheep_inv = sum(int(inv.get("SHEEP", 0) or 0) for inv in invs)
        cows_tot = cows_f + int(shed.get("COW", 0) or 0) + cows_inv
        sheep_tot = sheep_f + int(shed.get("SHEEP", 0) or 0) + sheep_inv
        n_animals = cows_tot + sheep_tot

        prices = (obs.get("market") or {}).get("prices") or {}
        sells = []
        for item in ("MELON", "WOOL", "MILK", "STRAWBERRY", "FERTILIZER", "EGG", "WHEAT"):
            qty = int(shed.get(item, 0) or 0)
            if item == "WHEAT":
                # JIT FEED BUFFER: 1.2x animals instead of 2.0x
                feed_res = max(8, int(n_animals * 1.2))
                qty = max(0, qty - feed_res)
            if qty > 0:
                p_val = float(prices.get(item, BASE_PRICES.get(item, 100)) or 100)
                sells.append((qty * p_val, item, qty))
        sells.sort(reverse=True)
        for _, item, qty in sells[:5]:
            orders.append(["SELL", item, qty])

        total_wheat = int(shed.get("WHEAT", 0) or 0) + sum(int(inv.get("WHEAT", 0) or 0) for inv in invs)
        target_feed_buffer = max(8, int(n_animals * 1.2))
        if n_animals > 0 and total_wheat < target_feed_buffer and money >= 80 and len(orders) < 8:
            need_feed = target_feed_buffer - total_wheat
            can_feed = min(need_feed, min(10, int((money - 50) // 30)))
            if can_feed > 0:
                orders.append(["BUY_PRODUCT", "WHEAT", can_feed])
                money -= can_feed * 30

        if len(quads) == 1 and money >= 1050 and day >= 7 and len(orders) < 8:
            orders.append(["BUY_LAND"])
            money -= 1000
        elif len(quads) == 2 and money >= 2100 and day >= 10 and len(orders) < 8:
            orders.append(["BUY_LAND"])
            money -= 2000

        shed_anim_count = int(shed.get("COW", 0) or 0) + int(shed.get("SHEEP", 0) or 0) + cows_inv + sheep_inv
        if shed_anim_count == 0 and hour == 0 and n_animals < 14:
            if ("NE" in quads or (len(quads) == 1 and day >= 7)) and 7 <= day <= 22 and len(orders) < 8:
                target_cows = 8
                target_sheep = 6
                cows_needed = max(0, target_cows - cows_tot)
                sheep_needed = max(0, target_sheep - sheep_tot)
                if sheep_needed > 0 and money >= 750:
                    can_buy_s = min(sheep_needed, min(3, int((money - 250) // 500)))
                    if can_buy_s > 0:
                        orders.append(["BUY_ANIMAL", "SHEEP", can_buy_s])
                        money -= can_buy_s * 500
                        sheep_tot += can_buy_s
                if cows_needed > 0 and money >= 650 and len(orders) < 8:
                    can_buy_c = min(cows_needed, min(2, int((money - 250) // 400)))
                    if can_buy_c > 0:
                        orders.append(["BUY_ANIMAL", "COW", can_buy_c])
                        money -= can_buy_c * 400
                        cows_tot += can_buy_c

        if hour == 0 and 4 <= day <= 22 and len(orders) < 8:
            melons_f = sum(1 for r in tiles for t in r if isinstance(t, dict) and t.get("crop") == "MELON")
            melons_s = int(seeds.get("MELON", 0) or 0)
            target_melons = 7 if day < 7 else (11 if day < 12 else 16)
            needed_m = max(0, target_melons - (melons_f + melons_s))
            if needed_m > 0 and money >= 250:
                can_buy_m = min(needed_m, min(6, int((money - 150) // 80)))
                if can_buy_m > 0:
                    orders.append(["BUY_SEED", "MELON", can_buy_m])
                    money -= can_buy_m * 80

        if hour == 0 and 4 <= day <= 20 and len(orders) < 8:
            straw_f = sum(1 for r in tiles for t in r if isinstance(t, dict) and t.get("crop") == "STRAWBERRY")
            straw_s = int(seeds.get("STRAWBERRY", 0) or 0)
            target_straw = 4 if day < 7 else (18 if day < 10 else 40)
            needed = max(0, target_straw - straw_f - straw_s)
            if needed > 0 and money >= 250:
                can_buy = min(needed, min(8, int((money - 150) // 100)))
                if can_buy > 0:
                    orders.append(["BUY_SEED", "STRAWBERRY", can_buy])
                    money -= can_buy * 100

        if hour == 0 and 2 <= day <= 24 and len(orders) < 8:
            wheat_s = int(seeds.get("WHEAT", 0) or 0)
            if wheat_s < 10 and money >= 200:
                can_buy_w = min(10 - wheat_s, min(10, int((money - 150) // 10)))
                if can_buy_w > 0:
                    orders.append(["BUY_SEED", "WHEAT", can_buy_w])
                    money -= can_buy_w * 10

        if day == 0: target_hands = 5
        elif day < 4: target_hands = 4
        elif day < 7: target_hands = 6
        elif day < 10: target_hands = 9
        elif day < 20: target_hands = 12
        else: target_hands = 13

        cur_h = hired
        budget = money
        while cur_h < target_hands and len(orders) < 10:
            cost = _fib(cur_h)
            if budget >= cost:
                orders.append(["HIRE"])
                budget -= cost
                cur_h += 1
            else:
                break

        return orders[:10]


# ---------------------------------------------------------------------------
# Arm G: Terminal Pocket Flush (Step >= 700)
# ---------------------------------------------------------------------------
class ArmGTerminalFlush(ClosedLoopCoordinatedV1):
    def _terminal_action(self, tiles, all_workers, all_invs, shed, obs):
        actions = []
        claimed = set()
        ns = (4, 4)
        sells = []
        prices = (obs.get("market") or {}).get("prices") or {}
        
        # Liquidate everything in shed
        for item in SELLABLE:
            qty = int(shed.get(item, 0) or 0)
            if qty > 0:
                p_val = float(prices.get(item, BASE_PRICES.get(item, 100)) or 100)
                sells.append((qty * p_val, item, qty))
        sells.sort(reverse=True)
        m_orders = [["SELL", item, qty] for _, item, qty in sells[:10]]

        for i, (pos, inv) in enumerate(zip(all_workers, all_invs)):
            x, y = pos
            produce_load = sum(int(inv.get(it, 0) or 0) for it in PRODUCE_TO_DROP) + int(inv.get("WHEAT", 0) or 0)

            # FLUSH ALL POCKETS
            if pos in SHED_ACCESS and produce_load > 0:
                actions.append(["DROP"])
                continue

            if produce_load > 0:
                actions.append([_bfs_step(pos, ns, tiles)])
            else:
                actions.append(["PASS"])

        return {
            "farmer": actions[0],
            "hands": actions[1:],
            "market": m_orders
        }


# ---------------------------------------------------------------------------
# Arm I: Best Synthesized Economic Architecture
# Combines:
# 1. Cap 11 Hands (saves late capital, reduces congestion)
# 2. No Wheat Fertilization (saves $100 fertilizer for Strawberry or sale)
# 3. Strawberry Yield >= 2 (batches harvests, eliminates 1-berry trips)
# 4. Cow Priority & Day >= 5 (accelerates milk and fertilizer daily cash flow)
# 5. Terminal Pocket Flush (liquidates pocket produce)
# ---------------------------------------------------------------------------
class ArmISynthesized(ArmCFertilizerRational):
    def _macro_market(self, step, day, hour, money, quads, tiles, shed, seeds, hired, invs, obs):
        orders = []

        if step == 0:
            if money >= 2780:
                return [
                    ["BUY_ANIMAL", "COW", 3],
                    ["BUY_ANIMAL", "SHEEP", 1],
                    ["BUY_SEED", "MELON", 7],
                    ["BUY_SEED", "WHEAT", 10],
                    ["BUY_PRODUCT", "WHEAT", 17],
                    ["HIRE"], ["HIRE"]
                ]
            else:
                cur_m = money
                ret = []
                if cur_m >= 400: ret.append(["BUY_ANIMAL", "COW", 1]); cur_m -= 400
                if cur_m >= 100: ret.append(["BUY_SEED", "WHEAT", min(10, int(cur_m // 10))])
                if cur_m >= 1: ret.append(["HIRE"])
                return ret

        cows_f = sum(1 for r in tiles for t in r if isinstance(t, dict) and t.get("animal") == "COW")
        sheep_f = sum(1 for r in tiles for t in r if isinstance(t, dict) and t.get("animal") == "SHEEP")
        cows_inv = sum(int(inv.get("COW", 0) or 0) for inv in invs)
        sheep_inv = sum(int(inv.get("SHEEP", 0) or 0) for inv in invs)
        cows_tot = cows_f + int(shed.get("COW", 0) or 0) + cows_inv
        sheep_tot = sheep_f + int(shed.get("SHEEP", 0) or 0) + sheep_inv
        n_animals = cows_tot + sheep_tot

        prices = (obs.get("market") or {}).get("prices") or {}
        sells = []
        for item in ("MELON", "WOOL", "MILK", "STRAWBERRY", "FERTILIZER", "EGG", "WHEAT"):
            qty = int(shed.get(item, 0) or 0)
            if item == "WHEAT":
                feed_res = max(12, int(n_animals * 1.5))
                qty = max(0, qty - feed_res)
            if qty > 0:
                p_val = float(prices.get(item, BASE_PRICES.get(item, 100)) or 100)
                sells.append((qty * p_val, item, qty))
        sells.sort(reverse=True)
        for _, item, qty in sells[:5]:
            orders.append(["SELL", item, qty])

        total_wheat = int(shed.get("WHEAT", 0) or 0) + sum(int(inv.get("WHEAT", 0) or 0) for inv in invs)
        target_feed_buffer = max(12, int(n_animals * 1.5))
        if n_animals > 0 and total_wheat < target_feed_buffer and money >= 80 and len(orders) < 8:
            need_feed = target_feed_buffer - total_wheat
            can_feed = min(need_feed, min(10, int((money - 50) // 30)))
            if can_feed > 0:
                orders.append(["BUY_PRODUCT", "WHEAT", can_feed])
                money -= can_feed * 30

        if len(quads) == 1 and money >= 1050 and day >= 7 and len(orders) < 8:
            orders.append(["BUY_LAND"])
            money -= 1000
        elif len(quads) == 2 and money >= 2100 and day >= 10 and len(orders) < 8:
            orders.append(["BUY_LAND"])
            money -= 2000

        shed_anim_count = int(shed.get("COW", 0) or 0) + int(shed.get("SHEEP", 0) or 0) + cows_inv + sheep_inv
        # Cow Priority & Day 5
        if shed_anim_count == 0 and hour == 0 and n_animals < 14:
            if ("NE" in quads or (len(quads) == 1 and day >= 5)) and 5 <= day <= 22 and len(orders) < 8:
                target_cows = 8
                target_sheep = 6
                cows_needed = max(0, target_cows - cows_tot)
                sheep_needed = max(0, target_sheep - sheep_tot)
                
                # COW FIRST
                if cows_needed > 0 and money >= 650 and len(orders) < 8:
                    can_buy_c = min(cows_needed, min(2, int((money - 250) // 400)))
                    if can_buy_c > 0:
                        orders.append(["BUY_ANIMAL", "COW", can_buy_c])
                        money -= can_buy_c * 400
                        cows_tot += can_buy_c
                if sheep_needed > 0 and money >= 750 and len(orders) < 8:
                    can_buy_s = min(sheep_needed, min(3, int((money - 250) // 500)))
                    if can_buy_s > 0:
                        orders.append(["BUY_ANIMAL", "SHEEP", can_buy_s])
                        money -= can_buy_s * 500
                        sheep_tot += can_buy_s

        if hour == 0 and 4 <= day <= 22 and len(orders) < 8:
            melons_f = sum(1 for r in tiles for t in r if isinstance(t, dict) and t.get("crop") == "MELON")
            melons_s = int(seeds.get("MELON", 0) or 0)
            target_melons = 7 if day < 7 else (11 if day < 12 else 16)
            needed_m = max(0, target_melons - (melons_f + melons_s))
            if needed_m > 0 and money >= 250:
                can_buy_m = min(needed_m, min(6, int((money - 150) // 80)))
                if can_buy_m > 0:
                    orders.append(["BUY_SEED", "MELON", can_buy_m])
                    money -= can_buy_m * 80

        if hour == 0 and 4 <= day <= 20 and len(orders) < 8:
            straw_f = sum(1 for r in tiles for t in r if isinstance(t, dict) and t.get("crop") == "STRAWBERRY")
            straw_s = int(seeds.get("STRAWBERRY", 0) or 0)
            target_straw = 8 if day < 7 else (24 if day < 10 else 40)
            needed = max(0, target_straw - straw_f - straw_s)
            if needed > 0 and money >= 250:
                can_buy = min(needed, min(8, int((money - 150) // 100)))
                if can_buy > 0:
                    orders.append(["BUY_SEED", "STRAWBERRY", can_buy])
                    money -= can_buy * 100

        if hour == 0 and 2 <= day <= 24 and len(orders) < 8:
            wheat_s = int(seeds.get("WHEAT", 0) or 0)
            if wheat_s < 10 and money >= 200:
                can_buy_w = min(10 - wheat_s, min(10, int((money - 150) // 10)))
                if can_buy_w > 0:
                    orders.append(["BUY_SEED", "WHEAT", can_buy_w])
                    money -= can_buy_w * 10

        # CAP HANDS AT 11
        if day == 0: target_hands = 5
        elif day < 4: target_hands = 4
        elif day < 7: target_hands = 6
        elif day < 10: target_hands = 9
        else: target_hands = 11

        cur_h = hired
        budget = money
        while cur_h < target_hands and len(orders) < 10:
            cost = _fib(cur_h)
            if budget >= cost:
                orders.append(["HIRE"])
                budget -= cost
                cur_h += 1
            else:
                break

        return orders[:10]

    def _scan_field(self, tiles, quads, seeds, shed, invs, day):
        scan_res = super()._scan_field(tiles, quads, seeds, shed, invs, day)
        # Strawberry batching >= 2
        new_ripe = []
        for y in range(BOARD):
            for x in range(BOARD):
                t = tiles[y][x] if tiles else None
                if not isinstance(t, dict) or t.get("kind") != "PLANT":
                    continue
                crop = t.get("crop")
                c_def = CROPS_DEF.get(crop, {})
                first_yd = c_def.get("first_yield_day", 2)
                age = day - int(t.get("planted_day", 0) or 0)
                yu = int(t.get("yield_units", 0) or 0)

                if yu > 0 and age >= first_yd:
                    if crop == "MELON":
                        if yu >= 5 or day >= 27:
                            new_ripe.append((x, y))
                    elif crop == "WHEAT":
                        if yu >= 4 or day >= 27:
                            new_ripe.append((x, y))
                    elif crop == "STRAWBERRY":
                        if yu >= 2 or day >= 27:
                            new_ripe.append((x, y))
                    else:
                        new_ripe.append((x, y))
        scan_res["ripe_crops"] = new_ripe
        return scan_res

    def _terminal_action(self, tiles, all_workers, all_invs, shed, obs):
        actions = []
        ns = (4, 4)
        sells = []
        prices = (obs.get("market") or {}).get("prices") or {}
        
        for item in SELLABLE:
            qty = int(shed.get(item, 0) or 0)
            if qty > 0:
                p_val = float(prices.get(item, BASE_PRICES.get(item, 100)) or 100)
                sells.append((qty * p_val, item, qty))
        sells.sort(reverse=True)
        m_orders = [["SELL", item, qty] for _, item, qty in sells[:10]]

        for i, (pos, inv) in enumerate(zip(all_workers, all_invs)):
            produce_load = sum(int(inv.get(it, 0) or 0) for it in PRODUCE_TO_DROP) + int(inv.get("WHEAT", 0) or 0)
            if pos in SHED_ACCESS and produce_load > 0:
                actions.append(["DROP"])
            elif produce_load > 0:
                actions.append([_bfs_step(pos, ns, tiles)])
            else:
                actions.append(["PASS"])

        return {
            "farmer": actions[0],
            "hands": actions[1:],
            "market": m_orders
        }


# Factories
def make_arm_a(): return ArmABaseline()
def make_arm_b(): return ArmBWorkerCap()
def make_arm_c(): return ArmCFertilizerRational()
def make_arm_d(): return ArmDStrawberryBatch()
def make_arm_e(): return ArmELivestockPriority()
def make_arm_f(): return ArmFFeedBuffering()
def make_arm_g(): return ArmGTerminalFlush()
def make_arm_i(): return ArmISynthesized()
