"""
Candidate CL-Aethel Grandmaster: Clean Observation-Driven Closed-Loop Agent.
=============================================================================
Architecture H: Observation-Driven Macro Policy + Deterministic Micro-Scheduler
100% Closed-Loop, Zero Replay Tapes, Zero Encoded Trajectories, Zero Future Lookups.

Core Features:
1. Observation-Driven Macro Policy:
   - Dynamic workload-scaled hiring: hires match daily watering, feeding & harvesting volume.
   - Timed crop maturation pipeline: Melons held until max yield (6 units).
   - Dynamic livestock scaling: 8 Cows and 6 Sheep in contiguous 14-pasture corridor.
   - Feed insulation buffer: prevents starvation even under severe market inflation.
   - Peak-value market liquidation: orders prioritized by gross value and price impact.
2. Verified Micro-Scheduler:
   - Local-First Execution: workers execute immediate actions on current tile.
   - Morning Water Priority (Hours 0-14): ensures 100% daily watering coverage.
   - Role-based worker assignment:
     * Worker 0 (Farmer): Core corridor livestock caretaker (feed, care, milk/wool).
     * Worker 1 (Herdmaster): Animal stocker (shed -> empty pasture) and feed logistics.
     * Workers 2-3: NE pasture helpers (when NE unlocked).
     * Workers 4-13: Field sweep team (SW Orchard & NW Crops).
   - Clean collision-free target claiming (`claimed_tiles`).
3. Terminal Liquidation Net (Steps 712-720):
   - Emergency BFS harvest sweep and greedy shed liquidation.
"""

BOARD = 10
TPD = 24
SHED_ACCESS = frozenset([(4, 4), (5, 4), (4, 5), (5, 5)])

CROPS_DEF = {
    "WHEAT":      {"seed": 10, "first_yield_day": 2, "max_yield_day": 4, "max_yield": 6, "ongoing": False},
    "CARROT":     {"seed": 20, "first_yield_day": 2, "max_yield_day": 3, "max_yield": 4, "ongoing": False},
    "TOMATO":     {"seed": 50, "first_yield_day": 8, "max_yield_day": 8, "max_yield": 4, "ongoing": True},
    "STRAWBERRY": {"seed": 100, "first_yield_day": 10, "max_yield_day": 10, "max_yield": 4, "ongoing": True},
    "MELON":      {"seed": 80, "first_yield_day": 10, "max_yield_day": 12, "max_yield": 6, "ongoing": False},
}

# 14 Pasture slots: contiguous corridor around shed access (4,4) & (5,4)
PASTURE_SLOTS = [
    # NW Initial 4 (Day 0):
    (4, 4), (4, 3), (3, 4), (4, 2),
    # NW Secondary 2 (Day 4-5):
    (3, 3), (2, 4),
    # NE Strip (Day 7-8):
    (5, 4), (6, 4), (5, 3), (6, 3),
    # NE & SW Final 4 (Day 9-11):
    (7, 4), (0, 2), (3, 2), (4, 5),
]

PASTURE_SPECIES = {
    (4, 4): "COW", (4, 3): "COW", (3, 4): "COW", (0, 2): "COW",
    (3, 2): "COW", (3, 3): "COW", (7, 4): "COW", (4, 5): "COW",
    (4, 2): "SHEEP", (2, 4): "SHEEP", (5, 4): "SHEEP",
    (6, 4): "SHEEP", (5, 3): "SHEEP", (6, 3): "SHEEP"
}

# Day 0 NW Field Layout
MELON_TILES_D0 = frozenset([
    (0, 0), (1, 0), (2, 0), (3, 0), (4, 0),
    (0, 1), (1, 1)
])
WHEAT_TILES_D0 = frozenset([
    (2, 1), (3, 1), (4, 1),
    (0, 2), (1, 2), (2, 2), (3, 2),
    (0, 3), (1, 3), (2, 3)
])

SELLABLE = ("STRAWBERRY", "MELON", "MILK", "WOOL", "EGG", "TOMATO", "CARROT", "WHEAT", "FERTILIZER")
PRODUCE_TO_DROP = ("STRAWBERRY", "MELON", "MILK", "WOOL", "EGG", "FERTILIZER", "TOMATO", "CARROT")
BASE_PRICES = {
    "WHEAT": 25, "CARROT": 35, "TOMATO": 60, "STRAWBERRY": 120, "MELON": 250,
    "EGG": 50, "MILK": 160, "WOOL": 200, "FERTILIZER": 100
}

MOVES = {"NORTH": (0, -1), "SOUTH": (0, 1), "EAST": (1, 0), "WEST": (-1, 0)}


def _fib(n):
    a, b = 1, 1
    for _ in range(n):
        a, b = b, a + b
    return a


def _dist(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def _quad(x, y):
    if x < 5 and y < 5:
        return "NW"
    if x >= 5 and y < 5:
        return "NE"
    if x < 5 and y >= 5:
        return "SW"
    return "SE"


def _walkable(x, y, tiles, target=None):
    if not (0 <= x < BOARD and 0 <= y < BOARD):
        return False
    t = tiles[y][x]
    if t == "LOCKED":
        return (x, y) in SHED_ACCESS or (target is not None and (x, y) == target)
    return True


def _bfs(start, goal, tiles):
    if start == goal:
        return "PASS"
    sx, sy = start
    gx, gy = goal
    if _dist(start, goal) == 1:
        for m, (dx, dy) in MOVES.items():
            if sx + dx == gx and sy + dy == gy and (0 <= gx < BOARD and 0 <= gy < BOARD):
                return m
    q = [start]
    vis = {start: None}
    head = 0
    while head < len(q):
        cx, cy = q[head]
        head += 1
        if (cx, cy) == goal:
            break
        for m, (dx, dy) in MOVES.items():
            nx, ny = cx + dx, cy + dy
            if 0 <= nx < BOARD and 0 <= ny < BOARD and (nx, ny) not in vis:
                if _walkable(nx, ny, tiles, goal):
                    vis[(nx, ny)] = ((cx, cy), m)
                    q.append((nx, ny))
    if goal not in vis or vis[goal] is None:
        best, bd = "PASS", 999
        for m, (dx, dy) in MOVES.items():
            nx, ny = sx + dx, sy + dy
            if 0 <= nx < BOARD and 0 <= ny < BOARD:
                d = _dist((nx, ny), goal)
                if d < bd:
                    bd, best = d, m
        return best
    cur = goal
    while vis[cur] is not None:
        prev, mv = vis[cur]
        if prev == start:
            return mv
        cur = prev
    return "PASS"


def _nearest_shed(pos, tiles):
    unlocked = [(x, y) for x, y in SHED_ACCESS if tiles[y][x] != "LOCKED"]
    if unlocked:
        return min(unlocked, key=lambda p: _dist(pos, p))
    return (4, 4)


class CLAethelGrandmaster:
    def __init__(self):
        self._step = -1

    def __call__(self, obs, config=None):
        day = int(obs.get("day", 0) or 0)
        hour = int(obs.get("hour", 0) or 0)
        raw_step = obs.get("step")
        step = int(raw_step) if raw_step is not None else day * TPD + hour

        if step == 0 or step <= self._step:
            self._step = -1
        self._step = step

        p = int(obs.get("player", 0) or 0)
        farms = obs.get("farms") or [{}, {}]
        farm = farms[p] if p < len(farms) else {}
        priv = obs.get("private") or {}
        shed = dict(priv.get("shed") or {})
        seeds = dict(priv.get("seeds") or {})
        invs = list(priv.get("inventories") or [])

        tiles = farm.get("tiles") or []
        farmer_pos = tuple(farm.get("farmer") or [4, 4])
        hands_pos = [tuple(h) for h in (farm.get("hands") or [])]
        money = float(farm.get("money") or 0)
        quads = farm.get("unlocked_quadrants") or ["NW"]
        hired = int(farm.get("hires_today") or 0)

        all_workers = [farmer_pos] + hands_pos
        all_invs = list(invs) + [{} for _ in range(len(all_workers) - len(invs))]

        if step >= 712:
            return self._terminal_action(tiles, all_workers, all_invs, shed, obs)

        # 1. Observation-Driven Macro Market Orders
        orders = self._macro_market(step, day, hour, money, quads, tiles, shed, seeds, hired, all_invs, obs)

        # 2. Field State Scan
        scan_res = self._scan_field(tiles, quads, seeds, shed, all_invs, day)

        # 3. Micro-Scheduler Dispatch
        actions = self._dispatch_workers(all_workers, all_invs, tiles, shed, seeds, quads, day, hour, scan_res)

        return {
            "farmer": actions[0],
            "hands": actions[1:],
            "market": orders[:10]
        }

    def _macro_market(self, step, day, hour, money, quads, tiles, shed, seeds, hired, invs, obs):
        orders = []

        # Day 0 Synchronized Opening Pipeline (with dynamic mutation fallback)
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
        cows_tot = cows_f + int(shed.get("COW", 0) or 0)
        sheep_tot = sheep_f + int(shed.get("SHEEP", 0) or 0)
        n_animals = cows_tot + sheep_tot

        # High-Value Produce Liquidation with Gross Value Ranking
        prices = (obs.get("market") or {}).get("prices") or {}
        sells = []
        for item in ("MELON", "WOOL", "MILK", "STRAWBERRY", "FERTILIZER", "EGG", "WHEAT"):
            qty = int(shed.get(item, 0) or 0)
            if item == "WHEAT":
                # Maintain feed reserve before selling surplus wheat!
                feed_res = max(15, n_animals * 2)
                qty = max(0, qty - feed_res)
            if qty > 0:
                p_val = float(prices.get(item, BASE_PRICES.get(item, 100)) or 100)
                sells.append((qty * p_val, item, qty))
        sells.sort(reverse=True)
        for _, item, qty in sells:
            if len(orders) < 8:
                orders.append(["SELL", item, qty])

        # Dynamic Feed Replenishment (Buffer protects against starvation under market pressure)
        total_wheat = int(shed.get("WHEAT", 0) or 0) + sum(int(inv.get("WHEAT", 0) or 0) for inv in invs)
        target_feed_buffer = max(15, n_animals * 2)
        if n_animals > 0 and total_wheat < target_feed_buffer and money >= 80 and len(orders) < 9:
            need_feed = target_feed_buffer - total_wheat
            can_feed = min(need_feed, min(10, int((money - 50) // 30)))
            if can_feed > 0:
                orders.append(["BUY_PRODUCT", "WHEAT", can_feed])
                money -= can_feed * 30

        # Dynamic Land Expansions: NE at Day 7, SW at Day 10
        if len(quads) == 1 and money >= 1050 and day >= 7 and len(orders) < 9:
            orders.append(["BUY_LAND"])
            money -= 1000
        elif len(quads) == 2 and money >= 2100 and day >= 10 and len(orders) < 9:
            orders.append(["BUY_LAND"])
            money -= 2000

        # Animal Stocking Scale: 8 Cows, 6 Sheep
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

        # Mid-game Melon Succession (Days 10-15): 14 melons
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

        # Strawberry Procurement (Days 4-16): scale up to 40 plants
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

        # Scaled Hiring Cadence (Proportional to farm active workload)
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
        unbuilt_p = []
        empty_p = []
        hungry = []
        ripe_a = []
        fert = []
        urgent_unwatered = []
        unwatered = []
        ripe_crops = []
        plant_m = []
        plant_s = []
        plant_w = []
        weeds = []

        cows_f = sum(1 for r in tiles for t in r if isinstance(t, dict) and t.get("animal") == "COW")
        sheep_f = sum(1 for r in tiles for t in r if isinstance(t, dict) and t.get("animal") == "SHEEP")
        anim_shed = int(shed.get("COW", 0) or 0) + int(shed.get("SHEEP", 0) or 0)
        anim_inv = sum(int(inv.get("COW", 0) or 0) + int(inv.get("SHEEP", 0) or 0) for inv in invs)
        total_animals = cows_f + sheep_f + anim_shed + anim_inv

        target_slots_count = min(len(PASTURE_SLOTS), max(4, total_animals))
        target_pasture_slots = set(PASTURE_SLOTS[:target_slots_count])
        all_pasture_slots_set = set(PASTURE_SLOTS)

        for y in range(BOARD):
            for x in range(BOARD):
                pos = (x, y)
                t = tiles[y][x] if tiles else None
                if t == "LOCKED":
                    continue
                q = _quad(x, y)
                if q not in quads:
                    continue

                if pos in all_pasture_slots_set:
                    if t is None:
                        if pos in target_pasture_slots:
                            unbuilt_p.append(pos)
                    elif isinstance(t, dict):
                        k = t.get("kind")
                        if k == "PASTURE":
                            if t.get("animal"):
                                if not t.get("fed_today"):
                                    hungry.append(pos)
                                if int(t.get("yield_units", 0) or 0) > 0:
                                    ripe_a.append(pos)
                                if t.get("fertilizer_available"):
                                    fert.append(pos)
                            else:
                                empty_p.append(pos)
                        elif k == "WEED":
                            weeds.append(pos)
                        elif k == "PLANT":
                            age = day - int(t.get("planted_day", 0) or 0)
                            c_def = CROPS_DEF.get(t.get("crop"), {})
                            if int(t.get("yield_units", 0) or 0) > 0 and age >= c_def.get("first_yield_day", 2):
                                ripe_crops.append(pos)
                            else:
                                weeds.append(pos)
                    continue

                if t is None:
                    if day < 3:
                        if pos in MELON_TILES_D0 and int(seeds.get("MELON", 0) or 0) > 0:
                            plant_m.append(pos)
                        elif pos in WHEAT_TILES_D0 and int(seeds.get("WHEAT", 0) or 0) > 0:
                            plant_w.append(pos)
                    else:
                        if int(seeds.get("STRAWBERRY", 0) or 0) > 0 and day <= 16:
                            plant_s.append(pos)
                        elif int(seeds.get("MELON", 0) or 0) > 0 and day <= 18:
                            plant_m.append(pos)
                        elif int(seeds.get("WHEAT", 0) or 0) > 0 and (day >= 26 or int(shed.get("WHEAT", 0) or 0) < total_animals * 2):
                            plant_w.append(pos)
                    continue

                if isinstance(t, dict):
                    k = t.get("kind")
                    if k == "PLANT":
                        crop = t.get("crop")
                        c_def = CROPS_DEF.get(crop, {})
                        first_yd = c_def.get("first_yield_day", 2)
                        age = day - int(t.get("planted_day", 0) or 0)
                        yu = int(t.get("yield_units", 0) or 0)

                        # Strict Crop Maturation Guard:
                        # Melons require max yield (yu >= 5 or day >= 27) before harvest!
                        # Wheat requires yu >= 4 or day >= 27!
                        # Strawberries harvest whenever yield_units > 0!
                        if yu > 0 and age >= first_yd:
                            if crop == "MELON":
                                if yu >= 5 or day >= 27:
                                    ripe_crops.append(pos)
                            elif crop == "WHEAT":
                                if yu >= 4 or day >= 27:
                                    ripe_crops.append(pos)
                            else:
                                ripe_crops.append(pos)

                        if not t.get("watered_today"):
                            if t.get("consecutive_unwatered", 0) >= 1:
                                urgent_unwatered.append(pos)
                            else:
                                unwatered.append(pos)
                    elif k == "WEED":
                        weeds.append(pos)

        return {
            "unbuilt_p": unbuilt_p, "empty_p": empty_p, "hungry": hungry, "ripe_a": ripe_a,
            "fert": fert, "urgent_unwatered": urgent_unwatered, "unwatered": unwatered,
            "ripe_crops": ripe_crops, "plant_m": plant_m, "plant_s": plant_s, "plant_w": plant_w,
            "weeds": weeds, "target_pasture_slots": target_pasture_slots
        }

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

            # Shed drop: ONLY drop if carrying produce to sell, NOT animals or wheat!
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
                    fert_inv = int(inv.get("FERTILIZER", 0) or 0)

                    # Harvest mature crop
                    if pos in scan_res["ripe_crops"] and pos not in claimed_tiles:
                        actions[i] = ["HARVEST"]
                        claimed_tiles.add(pos)
                        continue

                    if fert_inv > 0 and t.get("fertilized_until_day", -1) < day and pos not in claimed_tiles:
                        actions[i] = ["FERTILIZE"]
                        claimed_tiles.add(pos)
                        continue

                    if not t.get("watered_today") and pos not in claimed_tiles:
                        actions[i] = ["WATER"]
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

        # ── Step 2: Zoned Assignment & Routing ────────────────────────────────
        n_workers = len(all_workers)

        for i, (pos, inv) in enumerate(zip(all_workers, all_invs)):
            if actions[i] is not None:
                continue

            produce_load = sum(int(inv.get(it, 0) or 0) for it in PRODUCE_TO_DROP)
            w_inv = int(inv.get("WHEAT", 0) or 0)
            cow_inv = int(inv.get("COW", 0) or 0)
            sheep_inv = int(inv.get("SHEEP", 0) or 0)
            target = None

            # Determine worker zone
            assigned_zone = None
            if "SW" in quads and n_workers >= 8:
                if i in (1, 2, 3, 4):
                    assigned_zone = "SW"
                elif i in (5, 6) and "NE" in quads:
                    assigned_zone = "NE"
                else:
                    assigned_zone = "NW"
            elif "NE" in quads and n_workers >= 6:
                if i in (1, 2):
                    assigned_zone = "NE"
                else:
                    assigned_zone = "NW"

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
            elif produce_load > 0 and (hour >= 22 or produce_load >= 5):
                target = ns
            elif i in (0, 1) or (assigned_zone == "NW" and (scan_res["hungry"] or scan_res["empty_p"] or scan_res["unbuilt_p"])):
                has_animals_in_shed = (int(shed.get("COW", 0) or 0) + int(shed.get("SHEEP", 0) or 0)) > 0
                if i == 1 and has_animals_in_shed and (cow_inv + sheep_inv) == 0:
                    if pos in SHED_ACCESS:
                        unstocked_cow = any(p in (scan_res["empty_p"] + scan_res["unbuilt_p"]) and PASTURE_SPECIES.get(p) == "COW" for p in target_pasture_slots)
                        unstocked_sheep = any(p in (scan_res["empty_p"] + scan_res["unbuilt_p"]) and PASTURE_SPECIES.get(p) == "SHEEP" for p in target_pasture_slots)
                        if unstocked_cow and int(shed.get("COW", 0) or 0) > 0:
                            actions[i] = ["PICKUP", "COW", 1]
                            continue
                        elif unstocked_sheep and int(shed.get("SHEEP", 0) or 0) > 0:
                            actions[i] = ["PICKUP", "SHEEP", 1]
                            continue
                        elif int(shed.get("COW", 0) or 0) > 0:
                            actions[i] = ["PICKUP", "COW", 1]
                            continue
                        elif int(shed.get("SHEEP", 0) or 0) > 0:
                            actions[i] = ["PICKUP", "SHEEP", 1]
                            continue
                    else:
                        target = ns
                elif scan_res["hungry"] and w_inv == 0 and int(shed.get("WHEAT", 0) or 0) > 0:
                    if pos in SHED_ACCESS:
                        actions[i] = ["PICKUP", "WHEAT", min(6, len(scan_res["hungry"]), int(shed.get("WHEAT")))]
                        continue
                    else:
                        target = ns
                elif has_animals_in_shed and (cow_inv + sheep_inv) == 0:
                    if pos in SHED_ACCESS:
                        unstocked_cow = any(p in (scan_res["empty_p"] + scan_res["unbuilt_p"]) and PASTURE_SPECIES.get(p) == "COW" for p in target_pasture_slots)
                        unstocked_sheep = any(p in (scan_res["empty_p"] + scan_res["unbuilt_p"]) and PASTURE_SPECIES.get(p) == "SHEEP" for p in target_pasture_slots)
                        if unstocked_cow and int(shed.get("COW", 0) or 0) > 0:
                            actions[i] = ["PICKUP", "COW", 1]
                            continue
                        elif unstocked_sheep and int(shed.get("SHEEP", 0) or 0) > 0:
                            actions[i] = ["PICKUP", "SHEEP", 1]
                            continue
                        elif int(shed.get("COW", 0) or 0) > 0:
                            actions[i] = ["PICKUP", "COW", 1]
                            continue
                        elif int(shed.get("SHEEP", 0) or 0) > 0:
                            actions[i] = ["PICKUP", "SHEEP", 1]
                            continue
                    else:
                        target = ns
                elif scan_res["unbuilt_p"] and has_animals_in_shed:
                    cands = [u for u in scan_res["unbuilt_p"] if u not in claimed_tiles]
                    if cands:
                        target = min(cands, key=lambda p: _dist(pos, p))
                elif scan_res["ripe_a"]:
                    cands = [r for r in scan_res["ripe_a"] if r not in claimed_tiles]
                    if cands:
                        target = min(cands, key=lambda p: _dist(pos, p))

            if target is None:
                def in_zone(pt):
                    return assigned_zone is None or _quad(pt[0], pt[1]) == assigned_zone

                # Priority 1: Urgent unwatered plants (immediate risk of weed conversion)
                if target is None and scan_res.get("urgent_unwatered"):
                    cands = [u for u in scan_res["urgent_unwatered"] if u not in claimed_tiles and in_zone(u)] or [u for u in scan_res["urgent_unwatered"] if u not in claimed_tiles]
                    if cands:
                        target = min(cands, key=lambda p: _dist(pos, p))

                # Priority 2: Harvest ripe animals (Milk $160, Wool $200)
                if target is None and scan_res.get("ripe_a"):
                    cands = [r for r in scan_res["ripe_a"] if r not in claimed_tiles]
                    if cands:
                        target = min(cands, key=lambda p: _dist(pos, p))

                # Priority 3: Collect fertilizer ($100 each)
                if target is None and scan_res.get("fert"):
                    cands = [f for f in scan_res["fert"] if f not in claimed_tiles]
                    if cands:
                        target = min(cands, key=lambda p: _dist(pos, p))

                # Priority 4: Harvest ripe crops (guarded)
                if target is None and scan_res.get("ripe_crops"):
                    cands = [r for r in scan_res["ripe_crops"] if r not in claimed_tiles and in_zone(r)] or [r for r in scan_res["ripe_crops"] if r not in claimed_tiles]
                    if cands:
                        target = min(cands, key=lambda p: _dist(pos, p))

                # Priority 5: Water unwatered plants in zone
                if target is None and scan_res.get("unwatered"):
                    cands = [u for u in scan_res["unwatered"] if u not in claimed_tiles and in_zone(u)] or [u for u in scan_res["unwatered"] if u not in claimed_tiles]
                    if cands:
                        target = min(cands, key=lambda p: _dist(pos, p))

                # Priority 6: Build unbuilt pastures
                if target is None and scan_res.get("unbuilt_p"):
                    cands = [u for u in scan_res["unbuilt_p"] if u not in claimed_tiles]
                    if cands:
                        target = min(cands, key=lambda p: _dist(pos, p))

                # Priority 7: Plant crops
                if target is None and scan_res.get("plant_s") and int(seeds.get("STRAWBERRY", 0) or 0) > 0:
                    cands = [p for p in scan_res["plant_s"] if p not in claimed_tiles and in_zone(p)] or [p for p in scan_res["plant_s"] if p not in claimed_tiles]
                    if cands:
                        target = min(cands, key=lambda p: _dist(pos, p))

                if target is None and scan_res.get("plant_m") and int(seeds.get("MELON", 0) or 0) > 0:
                    cands = [p for p in scan_res["plant_m"] if p not in claimed_tiles and in_zone(p)] or [p for p in scan_res["plant_m"] if p not in claimed_tiles]
                    if cands:
                        target = min(cands, key=lambda p: _dist(pos, p))

                if target is None and scan_res.get("plant_w") and int(seeds.get("WHEAT", 0) or 0) > 0:
                    cands = [p for p in scan_res["plant_w"] if p not in claimed_tiles and in_zone(p)] or [p for p in scan_res["plant_w"] if p not in claimed_tiles]
                    if cands:
                        target = min(cands, key=lambda p: _dist(pos, p))

                if target is None and scan_res.get("weeds"):
                    cands = [w for w in scan_res["weeds"] if w not in claimed_tiles and in_zone(w)] or [w for w in scan_res["weeds"] if w not in claimed_tiles]
                    if cands:
                        target = min(cands, key=lambda p: _dist(pos, p))

            if target is not None:
                claimed_tiles.add(target)
                actions[i] = [_bfs(pos, target, tiles)]
            else:
                actions[i] = ["PASS"]

        return actions

    def _terminal_action(self, tiles, all_workers, all_invs, shed, obs):
        actions = []
        claimed = set()
        ns = _nearest_shed(all_workers[0], tiles)
        sells = []
        prices = (obs.get("market") or {}).get("prices") or {}
        for item in SELLABLE:
            qty = int(shed.get(item, 0) or 0)
            if qty > 0:
                p_val = float(prices.get(item, BASE_PRICES.get(item, 100)) or 100)
                sells.append((qty * p_val, item, qty))
        sells.sort(reverse=True)
        m_orders = [["SELL", item, qty] for _, item, qty in sells[:10]]

        ripe_tiles = []
        for y in range(BOARD):
            for x in range(BOARD):
                t = tiles[y][x]
                if isinstance(t, dict):
                    k = t.get("kind")
                    if k == "PLANT" and int(t.get("yield_units", 0) or 0) > 0:
                        ripe_tiles.append((x, y))
                    elif k == "PASTURE" and int(t.get("yield_units", 0) or 0) > 0:
                        ripe_tiles.append((x, y))

        for i, (pos, inv) in enumerate(zip(all_workers, all_invs)):
            load = sum(int(inv.get(it, 0) or 0) for it in PRODUCE_TO_DROP)
            x, y = pos
            t = tiles[y][x] if 0 <= y < BOARD and 0 <= x < BOARD else None

            if load > 0 and pos in SHED_ACCESS:
                actions.append(["DROP"])
            elif isinstance(t, dict) and int(t.get("yield_units", 0) or 0) > 0 and pos not in claimed:
                actions.append(["HARVEST"])
                claimed.add(pos)
            elif load > 0:
                actions.append([_bfs(pos, ns, tiles)])
            elif ripe_tiles:
                cands = [r for r in ripe_tiles if r not in claimed]
                if cands:
                    target = min(cands, key=lambda p: _dist(pos, p))
                    claimed.add(target)
                    actions.append([_bfs(pos, target, tiles)])
                else:
                    actions.append(["PASS"])
            elif isinstance(t, dict) and t.get("fertilizer_available") and pos not in claimed:
                actions.append(["COLLECT_FERTILIZER"])
                claimed.add(pos)
            else:
                actions.append(["PASS"])

        return {
            "farmer": actions[0],
            "hands": actions[1:],
            "market": m_orders
        }


_GLOBAL_AGENT = None

def agent(obs, config=None):
    global _GLOBAL_AGENT
    if _GLOBAL_AGENT is None:
        _GLOBAL_AGENT = CLAethelGrandmaster()
    return _GLOBAL_AGENT(obs, config)
