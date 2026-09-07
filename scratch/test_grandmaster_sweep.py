import sys, os
sys.path.insert(0, os.path.abspath('.'))
import copy
import json
import kaggle_environments
import numpy as np

from candidates.candidate_cl_aethel_prime import CLAethelPrime, CROPS_DEF, _fib, _dist, _nearest_shed, SHED_ACCESS, PRODUCE_TO_DROP, PASTURE_SPECIES, BOARD, TPD, _quad

SEEDS = [42, 100, 2024]

class GrandmasterCandidate(CLAethelPrime):
    """
    Candidate CL-Aethel Grandmaster (Architecture H):
    100% Closed-Loop, Zero Replay, Pure Observation-Driven.
    Combines Prime's Closed-Loop Spatial Scheduler with:
    1. Scaled Workload-Driven Hiring (D0: 5, D1-3: 4, D4-6: 6, D7-9: 8, D10+: 12-14)
    2. Guarded Maturation Harvesting (Never harvest melons/ongoing crops prematurely!)
    3. Dedicated Mid-Game Melon Pipeline (10-12 melons in unlocked quads on D10-14)
    4. Morning Water-First Sweep (All plants watered by hour 14 daily, 100% yield guarantee)
    5. Value-Maximizing Market Queue (Gross-impact sorting to capture peak shop prices)
    """
    def _macro_market(self, step, day, hour, money, quads, tiles, shed, seeds, hired, invs, obs):
        orders = []

        # Day 0 Synchronized Opening: 3 Cows, 1 Sheep, 7 Melons, 10 Wheat, 17 Feed, 2 Hires
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

        # Count animals
        cows_f = sum(1 for r in tiles for t in r if isinstance(t, dict) and t.get("animal") == "COW")
        sheep_f = sum(1 for r in tiles for t in r if isinstance(t, dict) and t.get("animal") == "SHEEP")
        cows_tot = cows_f + int(shed.get("COW", 0) or 0)
        sheep_tot = sheep_f + int(shed.get("SHEEP", 0) or 0)
        n_animals = cows_tot + sheep_tot

        # Market Sells: High-Value Liquidation with Peak Impact Sorting
        prices = (obs.get("market") or {}).get("prices") or {}
        sells = []
        for item in ("MELON", "WOOL", "MILK", "STRAWBERRY", "FERTILIZER", "EGG", "WHEAT"):
            qty = int(shed.get(item, 0) or 0)
            if item == "WHEAT":
                feed_res = max(15, n_animals * 2)
                qty = max(0, qty - feed_res)
            if qty > 0:
                p_val = float(prices.get(item, 100) or 100)
                sells.append((qty * p_val, item, qty))
        sells.sort(reverse=True)
        for _, item, qty in sells:
            if len(orders) < 8:
                orders.append(["SELL", item, qty])

        # Dynamic Feed Replenishment
        total_wheat = int(shed.get("WHEAT", 0) or 0) + sum(int(inv.get("WHEAT", 0) or 0) for inv in invs)
        target_feed_buffer = max(15, n_animals * 2)
        if n_animals > 0 and total_wheat < target_feed_buffer and money >= 80 and len(orders) < 9:
            need_feed = target_feed_buffer - total_wheat
            can_feed = min(need_feed, min(10, int((money - 50) // 30)))
            if can_feed > 0:
                orders.append(["BUY_PRODUCT", "WHEAT", can_feed])
                money -= can_feed * 30

        # Dynamic Land Expansions: Day 7 NE, Day 10 SW
        if len(quads) == 1 and money >= 1050 and day >= 7 and len(orders) < 9:
            orders.append(["BUY_LAND"])
            money -= 1000
        elif len(quads) == 2 and money >= 2100 and day >= 10 and len(orders) < 9:
            orders.append(["BUY_LAND"])
            money -= 2000

        # Animal Scaling: 8 Cows and 6 Sheep
        shed_anim_count = int(shed.get("COW", 0) or 0) + int(shed.get("SHEEP", 0) or 0)
        if shed_anim_count == 0 and hour == 0:
            if ("NE" in quads or (len(quads) == 1 and day >= 7)) and 7 <= day <= 22 and len(orders) < 9:
                target_cows = 8
                target_sheep = 6
                cows_needed = max(0, target_cows - cows_tot)
                sheep_needed = max(0, target_sheep - sheep_tot)
                if sheep_needed > 0 and money >= 750:
                    can_buy_s = min(sheep_needed, min(3, int((money - 250) // 500)))
                    if can_buy_s > 0:
                        orders.append(["BUY_ANIMAL", "SHEEP", can_buy_s])
                        money -= can_buy_s * 500
                if cows_needed > 0 and money >= 650 and len(orders) < 9:
                    can_buy_c = min(cows_needed, min(2, int((money - 250) // 400)))
                    if can_buy_c > 0:
                        orders.append(["BUY_ANIMAL", "COW", can_buy_c])
                        money -= can_buy_c * 400

        # Mid-game Melon Succession (Days 10-15): 14 melons in SW/NE
        if hour == 0 and 10 <= day <= 15 and len(orders) < 9:
            melons_f = sum(1 for r in tiles for t in r if isinstance(t, dict) and t.get("crop") == "MELON")
            melons_s = int(seeds.get("MELON", 0) or 0)
            target_melons = 14
            needed_m = max(0, target_melons - (melons_f + melons_s))
            if needed_m > 0 and money >= 300:
                can_buy_m = min(needed_m, min(8, int((money - 150) // 80)))
                if can_buy_m > 0:
                    orders.append(["BUY_SEED", "MELON", can_buy_m])
                    money -= can_buy_m * 80

        # Strawberry Procurement (Days 4-16)
        if hour == 0 and 4 <= day <= 16 and len(orders) < 9:
            straw_f = sum(1 for r in tiles for t in r if isinstance(t, dict) and t.get("crop") == "STRAWBERRY")
            straw_s = int(seeds.get("STRAWBERRY", 0) or 0)
            target_straw = 4 if day < 7 else (18 if day < 10 else 40)
            needed = max(0, target_straw - straw_f - straw_s)
            if needed > 0 and money >= 250:
                can_buy = min(needed, min(8, int((money - 150) // 100)))
                if can_buy > 0:
                    orders.append(["BUY_SEED", "STRAWBERRY", can_buy])
                    money -= can_buy * 100

        # Scaled Daily Hiring
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

    def _scan_field(self, tiles, quads, seeds, shed, invs, day):
        res = super()._scan_field(tiles, quads, seeds, shed, invs, day)
        # Strict maturation guard: Melon requires yield_units >= 6 (or day >= 27)
        guarded_ripe = []
        for pos in res["ripe_crops"]:
            t = tiles[pos[1]][pos[0]]
            if isinstance(t, dict) and t.get("kind") == "PLANT":
                crop = t.get("crop")
                yu = int(t.get("yield_units", 0) or 0)
                if crop == "MELON":
                    if yu >= 6 or day >= 27:
                        guarded_ripe.append(pos)
                elif crop == "WHEAT":
                    if yu >= 5 or day >= 27:
                        guarded_ripe.append(pos)
                else:
                    guarded_ripe.append(pos)
            else:
                guarded_ripe.append(pos)
        res["ripe_crops"] = guarded_ripe
        return res

    def _dispatch_workers(self, all_workers, all_invs, tiles, shed, seeds, quads, day, hour, scan_res):
        actions = [None] * len(all_workers)
        claimed_tiles = set()
        ns = _nearest_shed(all_workers[0], tiles)
        target_pasture_slots = scan_res.get("target_pasture_slots", set())

        # ── Step 1: Local-First Execution ─────────────────────────────────────
        for i, (pos, inv) in enumerate(zip(all_workers, all_invs)):
            x, y = pos
            t = tiles[y][x] if 0 <= y < BOARD and 0 <= x < BOARD else None
            produce_load = sum(int(inv.get(it, 0) or 0) for it in PRODUCE_TO_DROP)
            w_inv = int(inv.get("WHEAT", 0) or 0)
            cow_inv = int(inv.get("COW", 0) or 0)
            sheep_inv = int(inv.get("SHEEP", 0) or 0)

            if pos in SHED_ACCESS and produce_load > 0 and (cow_inv + sheep_inv) == 0 and (w_inv == 0 or not scan_res["hungry"]):
                actions[i] = ["DROP"]
                claimed_tiles.add(pos)
                continue

            if isinstance(t, dict):
                k = t.get("kind")
                if k == "PLANT":
                    crop = t.get("crop")
                    c_def = CROPS_DEF.get(crop, {})
                    age = day - int(t.get("planted_day", 0) or 0)
                    yu = int(t.get("yield_units", 0) or 0)
                    
                    # Water first if not watered today!
                    if not t.get("watered_today") and pos not in claimed_tiles:
                        actions[i] = ["WATER"]
                        claimed_tiles.add(pos)
                        continue

                    # Harvest mature crop
                    if pos in scan_res["ripe_crops"] and pos not in claimed_tiles:
                        actions[i] = ["HARVEST"]
                        claimed_tiles.add(pos)
                        continue

                elif k == "PASTURE":
                    if t.get("animal"):
                        if not t.get("fed_today") and w_inv > 0 and pos not in claimed_tiles:
                            actions[i] = ["FEED"]
                            claimed_tiles.add(pos)
                            continue
                        if not t.get("cared_today") and pos not in claimed_tiles:
                            actions[i] = ["CARE"]
                            claimed_tiles.add(pos)
                            continue
                        if int(t.get("yield_units", 0) or 0) > 0 and pos not in claimed_tiles:
                            actions[i] = ["HARVEST"]
                            claimed_tiles.add(pos)
                            continue
                        if t.get("fertilizer_available") and pos not in claimed_tiles:
                            actions[i] = ["COLLECT_FERTILIZER"]
                            claimed_tiles.add(pos)
                            continue
                    else:
                        desired_sp = PASTURE_SPECIES.get(pos, "COW")
                        if desired_sp == "SHEEP" and sheep_inv > 0 and pos not in claimed_tiles:
                            actions[i] = ["PLACE", "SHEEP"]
                            claimed_tiles.add(pos)
                            continue
                        elif desired_sp == "COW" and cow_inv > 0 and pos not in claimed_tiles:
                            actions[i] = ["PLACE", "COW"]
                            claimed_tiles.add(pos)
                            continue
                        elif cow_inv > 0 and pos not in claimed_tiles:
                            actions[i] = ["PLACE", "COW"]
                            claimed_tiles.add(pos)
                            continue
                        elif sheep_inv > 0 and pos not in claimed_tiles:
                            actions[i] = ["PLACE", "SHEEP"]
                            claimed_tiles.add(pos)
                            continue
                elif k == "WEED" and pos not in claimed_tiles:
                    actions[i] = ["DIG"]
                    claimed_tiles.add(pos)
                    continue
            elif t is None:
                if pos in scan_res["unbuilt_p"] and pos not in claimed_tiles:
                    actions[i] = ["BUILD_PASTURE"]
                    claimed_tiles.add(pos)
                    continue
                if pos in scan_res["plant_s"] and int(seeds.get("STRAWBERRY", 0) or 0) > 0 and pos not in claimed_tiles:
                    seeds["STRAWBERRY"] = max(0, int(seeds.get("STRAWBERRY")) - 1)
                    actions[i] = ["PLANT", "STRAWBERRY"]
                    claimed_tiles.add(pos)
                    continue
                if pos in scan_res["plant_m"] and int(seeds.get("MELON", 0) or 0) > 0 and pos not in claimed_tiles:
                    seeds["MELON"] = max(0, int(seeds.get("MELON")) - 1)
                    actions[i] = ["PLANT", "MELON"]
                    claimed_tiles.add(pos)
                    continue
                if pos in scan_res["plant_w"] and int(seeds.get("WHEAT", 0) or 0) > 0 and pos not in claimed_tiles:
                    seeds["WHEAT"] = max(0, int(seeds.get("WHEAT")) - 1)
                    actions[i] = ["PLANT", "WHEAT"]
                    claimed_tiles.add(pos)
                    continue

        # ── Step 2: Routing with Water-First Discipline ───────────────────────
        for i, (pos, inv) in enumerate(zip(all_workers, all_invs)):
            if actions[i] is not None:
                continue

            produce_load = sum(int(inv.get(it, 0) or 0) for it in PRODUCE_TO_DROP)
            w_inv = int(inv.get("WHEAT", 0) or 0)
            cow_inv = int(inv.get("COW", 0) or 0)
            sheep_inv = int(inv.get("SHEEP", 0) or 0)
            target = None

            if tiles[pos[1]][pos[0]] == "LOCKED" and pos not in SHED_ACCESS:
                target = (4, 4)
            elif (cow_inv + sheep_inv) > 0:
                car_sp = "COW" if cow_inv > 0 else "SHEEP"
                matching_slots = [p for p in target_pasture_slots if PASTURE_SPECIES.get(p) == car_sp and p not in claimed_tiles]
                cands = [p for p in matching_slots if p in scan_res["empty_p"]] or [p for p in matching_slots if p in scan_res["unbuilt_p"]] or [p for p in scan_res["empty_p"] if p not in claimed_tiles] or [p for p in scan_res["unbuilt_p"] if p not in claimed_tiles]
                if cands:
                    target = min(cands, key=lambda p: _dist(pos, p))
            elif w_inv > 0 and scan_res["hungry"]:
                cands = [h for h in scan_res["hungry"] if h not in claimed_tiles]
                if cands:
                    target = min(cands, key=lambda p: _dist(pos, p))
            elif produce_load > 0 and (hour >= 21 or produce_load >= 6):
                target = ns

            # High-priority chores
            if target is None:
                # 1. Urgent unwatered plants
                if scan_res.get("urgent_unwatered"):
                    cands = [u for u in scan_res["urgent_unwatered"] if u not in claimed_tiles]
                    if cands: target = min(cands, key=lambda p: _dist(pos, p))

                # 2. General unwatered plants (MORNING WATER SWEEP: hours 0-14)
                if target is None and hour <= 14 and scan_res.get("unwatered"):
                    cands = [u for u in scan_res["unwatered"] if u not in claimed_tiles]
                    if cands: target = min(cands, key=lambda p: _dist(pos, p))

                # 3. Dedicated Herdmaster handling for workers 0 and 1
                if target is None and (i in (0, 1) or not scan_res.get("unwatered")):
                    has_animals_in_shed = (int(shed.get("COW", 0) or 0) + int(shed.get("SHEEP", 0) or 0)) > 0
                    if has_animals_in_shed and (cow_inv + sheep_inv) == 0:
                        if pos in SHED_ACCESS:
                            if int(shed.get("COW", 0) or 0) > 0: actions[i] = ["PICKUP", "COW", 1]; continue
                            elif int(shed.get("SHEEP", 0) or 0) > 0: actions[i] = ["PICKUP", "SHEEP", 1]; continue
                        else:
                            target = ns
                    elif scan_res["hungry"] and w_inv == 0 and int(shed.get("WHEAT", 0) or 0) > 0:
                        if pos in SHED_ACCESS:
                            actions[i] = ["PICKUP", "WHEAT", min(6, len(scan_res["hungry"]), int(shed.get("WHEAT")))]
                            continue
                        else:
                            target = ns
                    elif scan_res["ripe_a"]:
                        cands = [r for r in scan_res["ripe_a"] if r not in claimed_tiles]
                        if cands: target = min(cands, key=lambda p: _dist(pos, p))
                    elif scan_res["fert"]:
                        cands = [f for f in scan_res["fert"] if f not in claimed_tiles]
                        if cands: target = min(cands, key=lambda p: _dist(pos, p))

                # 4. Harvest mature crops
                if target is None and scan_res.get("ripe_crops"):
                    cands = [r for r in scan_res["ripe_crops"] if r not in claimed_tiles]
                    if cands: target = min(cands, key=lambda p: _dist(pos, p))

                # 5. Afternoon unwatered sweep
                if target is None and scan_res.get("unwatered"):
                    cands = [u for u in scan_res["unwatered"] if u not in claimed_tiles]
                    if cands: target = min(cands, key=lambda p: _dist(pos, p))

                # 6. Planting & Pasture building
                if target is None and scan_res.get("unbuilt_p"):
                    cands = [u for u in scan_res["unbuilt_p"] if u not in claimed_tiles]
                    if cands: target = min(cands, key=lambda p: _dist(pos, p))

                if target is None and scan_res.get("plant_s") and int(seeds.get("STRAWBERRY", 0) or 0) > 0:
                    cands = [p for p in scan_res["plant_s"] if p not in claimed_tiles]
                    if cands: target = min(cands, key=lambda p: _dist(pos, p))

                if target is None and scan_res.get("plant_m") and int(seeds.get("MELON", 0) or 0) > 0:
                    cands = [p for p in scan_res["plant_m"] if p not in claimed_tiles]
                    if cands: target = min(cands, key=lambda p: _dist(pos, p))

                if target is None and scan_res.get("plant_w") and int(seeds.get("WHEAT", 0) or 0) > 0:
                    cands = [p for p in scan_res["plant_w"] if p not in claimed_tiles]
                    if cands: target = min(cands, key=lambda p: _dist(pos, p))

                if target is None and scan_res.get("weeds"):
                    cands = [w for w in scan_res["weeds"] if w not in claimed_tiles]
                    if cands: target = min(cands, key=lambda p: _dist(pos, p))

            if target is not None:
                claimed_tiles.add(target)
                mv = self._bfs(pos, target, tiles) if hasattr(self, '_bfs') else "PASS"
                actions[i] = [mv] if mv != "PASS" else ["PASS"]
            else:
                actions[i] = ["PASS"]

        return actions

def test():
    print("Testing CL-Aethel Grandmaster across seeds 42, 100, 2024...")
    gm = GrandmasterCandidate()
    def agent(obs, cfg=None): return gm(obs, cfg)
    
    scores = []
    for s in SEEDS:
        env = kaggle_environments.make("kaggriculture", configuration={"episodeSteps": 720, "seed": s})
        starter = kaggle_environments.environments['kaggriculture']['agents']['starter']
        env.run([agent, starter])
        sc = env.steps[-1][0]['reward']
        scores.append(sc)
        print(f"  Seed {s}: Final Bank = ${sc:,.1f}")
    print(f"Mean: ${np.mean(scores):,.1f} +/- {np.std(scores):,.1f}")

if __name__ == '__main__':
    test()
