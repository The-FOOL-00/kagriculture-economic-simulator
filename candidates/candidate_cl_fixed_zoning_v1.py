"""
Candidate Closed-Loop Fixed Zoning V1 (CL-Fixed-Zoning-V1) - ARM B CONTROL
==========================================================================
Hypothesis Test: Simultaneous Full-Field Capacity Saturation via Fixed Field Zoning.
Explicitly partitions the 75 unlocked farm tiles into:
- 14 Dedicated Pasture Slots (8 Cows, 6 Sheep)
- 40 Dedicated Strawberry Tiles (Protected from crop competition)
- 16 Dedicated Melon Tiles ($250 high-margin plots)
- 5 Residual Tiles (Dynamic buffer / wheat feed)
- Temporal Multiplexing: Days 0-4 early wheat bootstrap; Day 26 terminal grain surge.

Pure Closed-Loop Standard:
- Zero historical_trace, zero binary_payload/binary_encoding, zero historical lookups.
- Standard library only.
"""

from collections import deque

BOARD = 10
TPD = 24
SHED_ACCESS = frozenset([(4, 4), (5, 4), (4, 5), (5, 5)])

CROPS_DEF = {
    "WHEAT":      {"seed": 10, "first_yield_day": 2, "max_yield_day": 4, "interval": 0, "max_yield": 6, "ongoing": False},
    "CARROT":     {"seed": 20, "first_yield_day": 2, "max_yield_day": 3, "interval": 0, "max_yield": 4, "ongoing": False},
    "TOMATO":     {"seed": 50, "first_yield_day": 8, "max_yield_day": 8, "interval": 1, "max_yield": 4, "ongoing": True},
    "STRAWBERRY": {"seed": 100, "first_yield_day": 10, "max_yield_day": 10, "interval": 2, "max_yield": 4, "ongoing": True},
    "MELON":      {"seed": 80, "first_yield_day": 10, "max_yield_day": 12, "interval": 0, "max_yield": 6, "ongoing": False},
}

# 14 Fixed Pasture Slots (8 Cows, 6 Sheep)
PASTURE_SLOTS = [
    (4, 4), (4, 3), (3, 4), (4, 2),
    (3, 3), (2, 4),
    (5, 4), (6, 4), (5, 3), (6, 3),
    (7, 4), (0, 2), (3, 2), (4, 5),
]

PASTURE_SPECIES = {
    (4, 4): "COW", (4, 3): "COW", (3, 4): "COW", (0, 2): "COW",
    (3, 2): "COW", (3, 3): "COW", (7, 4): "COW", (4, 5): "COW",
    (4, 2): "SHEEP", (2, 4): "SHEEP", (5, 4): "SHEEP",
    (6, 4): "SHEEP", (5, 3): "SHEEP", (6, 3): "SHEEP"
}

# 16 Dedicated Melon Tiles
MELON_ZONE = frozenset([
    (0, 0), (1, 0), (2, 0), (3, 0), (4, 0),
    (0, 1), (1, 1), (5, 1), (6, 1), (7, 1),
    (9, 0), (9, 1), (0, 7), (0, 8), (0, 9), (1, 9)
])

# 40 Dedicated Strawberry Tiles
STRAWBERRY_ZONE = frozenset([
    # NW remaining crop tiles (5)
    (2, 1), (3, 1), (4, 1), (1, 2), (2, 2),
    # NE crop tiles (18)
    (5, 0), (6, 0), (7, 0), (8, 0), (8, 1),
    (5, 2), (6, 2), (7, 2), (8, 2), (9, 2),
    (8, 3), (9, 3), (8, 4), (9, 4),
    (5, 5), (6, 5), (7, 5), (8, 5),
    # SW crop tiles (17)
    (1, 5), (2, 5), (3, 5),
    (0, 6), (1, 6), (2, 6), (3, 6),
    (1, 7), (2, 7), (3, 7), (4, 7),
    (1, 8), (2, 8), (3, 8), (4, 8),
    (2, 9), (3, 9)
])

# Residual Tiles (for early wheat feed and terminal wheat surge)
RESIDUAL_ZONE = frozenset([
    (0, 3), (1, 3), (2, 3), (0, 4), (1, 4)
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
    if x < 5 and y < 5: return "NW"
    if x >= 5 and y < 5: return "NE"
    if x < 5 and y >= 5: return "SW"
    return "SE"

def _walkable(x, y, tiles, target=None):
    if not (0 <= x < BOARD and 0 <= y < BOARD):
        return False
    t = tiles[y][x]
    if t == "LOCKED":
        return (x, y) in SHED_ACCESS or (target is not None and (x, y) == target)
    return True

def _bfs_step(start, goal, tiles):
    if start == goal:
        return "PASS"
    sx, sy = start
    gx, gy = goal

    if _dist(start, goal) == 1:
        for m, (dx, dy) in MOVES.items():
            nx, ny = sx + dx, sy + dy
            if (nx, ny) == goal and (0 <= nx < BOARD and 0 <= ny < BOARD):
                return m

    q = deque([start])
    vis = {start: None}

    while q:
        cx, cy = q.popleft()
        if (cx, cy) == goal:
            break
        for m, (dx, dy) in MOVES.items():
            nx, ny = cx + dx, cy + dy
            if 0 <= nx < BOARD and 0 <= ny < BOARD and (nx, ny) not in vis:
                if _walkable(nx, ny, tiles, goal):
                    vis[(nx, ny)] = ((cx, cy), m)
                    q.append((nx, ny))

    if goal not in vis or vis[goal] is None:
        best_m, bd = "PASS", 999
        for m, (dx, dy) in MOVES.items():
            nx, ny = sx + dx, sy + dy
            if 0 <= nx < BOARD and 0 <= ny < BOARD and _walkable(nx, ny, tiles, goal):
                d = _dist((nx, ny), goal)
                if d < bd:
                    bd, best_m = d, m
        return best_m

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

def min_cost_bipartite_matching(cost_matrix):
    n = len(cost_matrix)
    if n == 0: return []
    m = len(cost_matrix[0])
    if m == 0: return []
    
    transposed = False
    if n > m:
        cost_matrix = [[cost_matrix[r][c] for r in range(n)] for c in range(m)]
        n, m = m, n
        transposed = True

    u = [0.0] * (n + 1)
    v = [0.0] * (m + 1)
    p = [0] * (m + 1)
    way = [0] * (m + 1)

    for i in range(1, n + 1):
        p[0] = i
        j0 = 0
        minv = [float('inf')] * (m + 1)
        used = [False] * (m + 1)
        while True:
            used[j0] = True
            i0 = p[j0]
            delta = float('inf')
            j1 = 0
            for j in range(1, m + 1):
                if not used[j]:
                    cur = cost_matrix[i0 - 1][j - 1] - u[i0] - v[j]
                    if cur < minv[j]:
                        minv[j] = cur
                        way[j] = j0
                    if minv[j] < delta:
                        delta = minv[j]
                        j1 = j
            for j in range(m + 1):
                if used[j]:
                    u[p[j]] += delta
                    v[j] -= delta
                else:
                    minv[j] -= delta
            j0 = j1
            if p[j0] == 0:
                break
        while True:
            j1 = way[j0]
            p[j0] = p[j1]
            j0 = j1
            if j0 == 0:
                break

    matching = []
    for j in range(1, m + 1):
        if p[j] != 0:
            if transposed:
                matching.append((j - 1, p[j] - 1))
            else:
                matching.append((p[j] - 1, j - 1))
    return matching


class ClosedLoopFixedZoningV1:
    def __init__(self):
        self._step = -1
        self._worker_targets = {}

    def __call__(self, obs, config=None):
        raw_step = obs.get("step")
        step = int(raw_step) if raw_step is not None else 0
        day = int(obs.get("day", 0) or 0) if obs.get("day") is not None else step // TPD
        hour = int(obs.get("hour", 0) or 0) if obs.get("hour") is not None else step % TPD

        if step == 0 or step <= self._step:
            self._step = -1
            self._worker_targets.clear()
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

        orders = self._macro_market(step, day, hour, money, quads, tiles, shed, seeds, hired, all_invs, obs)
        scan_res = self._scan_field(tiles, quads, seeds, shed, all_invs, day)
        actions = self._dispatch_workers(all_workers, all_invs, tiles, shed, seeds, quads, day, hour, scan_res, step)

        return {
            "farmer": actions[0],
            "hands": actions[1:],
            "market": orders[:10]
        }

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

        straw_f = sum(1 for r in tiles for t in r if isinstance(t, dict) and t.get("crop") == "STRAWBERRY")
        straw_s = int(seeds.get("STRAWBERRY", 0) or 0)
        straw_tot = straw_f + straw_s

        prices = (obs.get("market") or {}).get("prices") or {}

        # 1. SALES
        sells = []
        for item in ("MELON", "WOOL", "MILK", "STRAWBERRY", "FERTILIZER", "EGG", "WHEAT"):
            qty = int(shed.get(item, 0) or 0)
            if item == "WHEAT":
                feed_res = max(12, int(n_animals * 1.5))
                qty = max(0, qty - feed_res)
            elif item == "FERTILIZER":
                fert_reserve = min(8, straw_f) if 9 <= day <= 23 else 0
                qty = max(0, qty - fert_reserve)

            if qty > 0:
                p_val = float(prices.get(item, BASE_PRICES.get(item, 100)) or 100)
                min_p = BASE_PRICES.get(item, 100) * 0.40 if day < 27 else 1.0
                if p_val >= min_p:
                    sells.append((qty * p_val, item, qty))

        sells.sort(reverse=True)
        for _, item, qty in sells[:5]:
            orders.append(["SELL", item, qty])

        # 2. FEED BUFFER
        total_wheat = int(shed.get("WHEAT", 0) or 0) + sum(int(inv.get("WHEAT", 0) or 0) for inv in invs)
        target_feed_buffer = max(12, int(n_animals * 1.5))
        if n_animals > 0 and total_wheat < target_feed_buffer and money >= 80 and len(orders) < 8:
            need_feed = target_feed_buffer - total_wheat
            can_feed = min(need_feed, min(14, int((money - 50) // 30)))
            if can_feed > 0:
                orders.append(["BUY_PRODUCT", "WHEAT", can_feed])
                money -= can_feed * 30

        # 3. LAND EXPANSION
        if len(quads) == 1 and money >= 1050 and day >= 7 and len(orders) < 8:
            orders.append(["BUY_LAND"])
            money -= 1000
        elif len(quads) == 2 and money >= 2100 and day >= 10 and len(orders) < 8:
            orders.append(["BUY_LAND"])
            money -= 2000

        # 4. FIXED LIVESTOCK TARGETS (8 Cows, 6 Sheep)
        shed_anim_count = int(shed.get("COW", 0) or 0) + int(shed.get("SHEEP", 0) or 0) + cows_inv + sheep_inv
        if shed_anim_count == 0 and hour == 0 and len(orders) < 8:
            target_sheep = 6
            target_cows = 8
            sheep_needed = max(0, target_sheep - sheep_tot)
            cows_needed = max(0, target_cows - cows_tot)

            # Day 8 Inversion: Prioritize sheep from Day 7 onward
            if day >= 7 and sheep_needed > 0 and money >= 750:
                can_buy_s = min(sheep_needed, min(4, int((money - 250) // 500)))
                if can_buy_s > 0:
                    orders.append(["BUY_ANIMAL", "SHEEP", can_buy_s])
                    money -= can_buy_s * 500
                    sheep_tot += can_buy_s
                    n_animals += can_buy_s

            if cows_needed > 0 and money >= 650 and len(orders) < 8:
                can_buy_c = min(cows_needed, min(2, int((money - 250) // 400)))
                if can_buy_c > 0:
                    orders.append(["BUY_ANIMAL", "COW", can_buy_c])
                    money -= can_buy_c * 400
                    cows_tot += can_buy_c
                    n_animals += can_buy_c

            if day < 7 and sheep_needed > 0 and money >= 750 and len(orders) < 8:
                can_buy_s = min(sheep_needed, min(2, int((money - 250) // 500)))
                if can_buy_s > 0:
                    orders.append(["BUY_ANIMAL", "SHEEP", can_buy_s])
                    money -= can_buy_s * 500
                    sheep_tot += can_buy_s
                    n_animals += can_buy_s

        # 5. FIXED 40 STRAWBERRY SEED TARGET (Days 4-13)
        if hour == 0 and 4 <= day <= 13 and len(orders) < 8:
            target_straw = 40 if day >= 7 else (8 if day < 6 else 16)
            needed_straw = max(0, target_straw - straw_tot)
            if needed_straw > 0 and money >= 250:
                can_buy = min(needed_straw, min(8, int((money - 150) // 100)))
                if can_buy > 0:
                    orders.append(["BUY_SEED", "STRAWBERRY", can_buy])
                    money -= can_buy * 100
                    straw_tot += can_buy

        # 6. FIXED 16 MELON SEED TARGET (Days 0-18)
        if hour == 0 and 4 <= day <= 18 and len(orders) < 8:
            melons_f = sum(1 for r in tiles for t in r if isinstance(t, dict) and t.get("crop") == "MELON")
            melons_s = int(seeds.get("MELON", 0) or 0)
            target_melons = 7 if day < 7 else (12 if day < 11 else 16)
            needed_m = max(0, target_melons - (melons_f + melons_s))
            if needed_m > 0 and money >= 250:
                can_buy_m = min(needed_m, min(5, int((money - 150) // 80)))
                if can_buy_m > 0:
                    orders.append(["BUY_SEED", "MELON", can_buy_m])
                    money -= can_buy_m * 80

        # 7. FIXED WHEAT TARGET: D0-3 early bootstrap + D26 terminal grain surge (26 seeds)
        if hour == 0 and len(orders) < 8:
            wheat_s = int(seeds.get("WHEAT", 0) or 0)
            if day <= 3 and wheat_s < 10 and money >= 200:
                can_buy_w = min(10 - wheat_s, min(10, int((money - 150) // 10)))
                if can_buy_w > 0:
                    orders.append(["BUY_SEED", "WHEAT", can_buy_w])
                    money -= can_buy_w * 10
            elif day == 26 and wheat_s < 26 and money >= 400:
                can_buy_w = min(26 - wheat_s, min(26, int((money - 200) // 10)))
                if can_buy_w > 0:
                    orders.append(["BUY_SEED", "WHEAT", can_buy_w])
                    money -= can_buy_w * 10

        # 8. LABOR SIZING (11 hands)
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
        unbuilt_p = []
        empty_p = []
        hungry = []
        ripe_a = []
        fert = []
        care_a = []
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

                # 1. Pasture Zone Protection
                if pos in all_pasture_slots_set:
                    if t is None:
                        if pos in target_pasture_slots:
                            unbuilt_p.append(pos)
                        continue
                    elif isinstance(t, dict):
                        k = t.get("kind")
                        if k == "PASTURE":
                            if t.get("animal"):
                                if not t.get("fed_today"):
                                    hungry.append(pos)
                                if not t.get("cared_today"):
                                    care_a.append(pos)
                                if int(t.get("yield_units", 0) or 0) > 0:
                                    ripe_a.append(pos)
                                if t.get("fertilizer_available"):
                                    fert.append(pos)
                            else:
                                empty_p.append(pos)
                            continue
                        elif k == "WEED":
                            weeds.append(pos)
                            continue

                # 2. Empty Tile Scanning with Strict Fixed Zoning
                if t is None:
                    if day < 3:
                        # Day 0-2 initial setup: melon in melon zone, wheat in residual/strawberry zones
                        if pos in MELON_ZONE and int(seeds.get("MELON", 0) or 0) > 0:
                            plant_m.append(pos)
                        elif (pos in RESIDUAL_ZONE or pos in STRAWBERRY_ZONE) and int(seeds.get("WHEAT", 0) or 0) > 0:
                            plant_w.append(pos)
                    else:
                        # Fixed Zoning: Each zone only accepts its designated crop!
                        if pos in MELON_ZONE:
                            if int(seeds.get("MELON", 0) or 0) > 0 and day <= 18:
                                plant_m.append(pos)
                            elif day >= 26 and int(seeds.get("WHEAT", 0) or 0) > 0:
                                plant_w.append(pos) # Re-seed vacated melon plots with terminal wheat!
                        elif pos in STRAWBERRY_ZONE:
                            if int(seeds.get("STRAWBERRY", 0) or 0) > 0 and day <= 14:
                                plant_s.append(pos)
                            elif day >= 26 and int(seeds.get("WHEAT", 0) or 0) > 0:
                                plant_w.append(pos) # Re-seed vacant plots with terminal wheat!
                        elif pos in RESIDUAL_ZONE:
                            if (day <= 4 or day >= 26) and int(seeds.get("WHEAT", 0) or 0) > 0:
                                plant_w.append(pos)
                    continue

                # 3. Existing Plant Scanning
                if isinstance(t, dict):
                    k = t.get("kind")
                    if k == "PLANT":
                        crop = t.get("crop")
                        c_def = CROPS_DEF.get(crop, {})
                        first_yd = c_def.get("first_yield_day", 2)
                        age = day - int(t.get("planted_day", 0) or 0)
                        yu = int(t.get("yield_units", 0) or 0)

                        if yu > 0 and age >= first_yd:
                            if crop == "MELON":
                                if yu >= 5 or day >= 27:
                                    ripe_crops.append(pos)
                            elif crop == "WHEAT":
                                if yu >= 4 or day >= 27:
                                    ripe_crops.append(pos)
                            elif crop == "STRAWBERRY":
                                if yu >= 2 or day >= 27:
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
            "unbuilt_p": unbuilt_p, "empty_p": empty_p, "hungry": hungry, "care_a": care_a, "ripe_a": ripe_a,
            "fert": fert, "urgent_unwatered": urgent_unwatered, "unwatered": unwatered,
            "ripe_crops": ripe_crops, "plant_m": plant_m, "plant_s": plant_s, "plant_w": plant_w,
            "weeds": weeds, "target_pasture_slots": target_pasture_slots
        }

    def _worker_preferred_quad(self, w_idx):
        if w_idx in (0, 1, 2): return "NW"
        if w_idx in (3, 4, 5): return "NE"
        if w_idx in (6, 7, 8): return "SW"
        return "SE"

    def _dispatch_workers(self, all_workers, all_invs, tiles, shed, seeds, quads, day, hour, scan_res, step):
        actions = [None] * len(all_workers)
        claimed_action_tiles = set()
        ns = _nearest_shed(all_workers[0], tiles)
        target_pasture_slots = scan_res.get("target_pasture_slots", set())

        if hour == 0:
            self._worker_targets.clear()

        # Step 1: Local-First Action Execution
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
                    if 9 <= day <= 23 and crop in ("STRAWBERRY", "MELON") and fert_inv > 0 and t.get("fertilized_until_day", -1) < day and pos not in claimed_action_tiles:
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
                        elif sheep_inv > 0 and pos not in claimed_action_tiles:
                            actions[i] = ["PLACE", "SHEEP"]; claimed_action_tiles.add(pos); self._worker_targets.pop(i, None); continue
                        elif cow_inv > 0 and pos not in claimed_action_tiles:
                            actions[i] = ["PLACE", "COW"]; claimed_action_tiles.add(pos); self._worker_targets.pop(i, None); continue
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

        # Step 2: Validate active worker commitments
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

        # Step 3: Priority Handling for Animals & Feeding
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
                    if int(shed.get("SHEEP", 0) or 0) > 0: actions[w] = ["PICKUP", "SHEEP", 1]; continue
                    elif int(shed.get("COW", 0) or 0) > 0: actions[w] = ["PICKUP", "COW", 1]; continue
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

        # Step 4: Spatial Bipartite Assignment
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

        # Step 5: Fallback & Produce Drops
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

    def _terminal_action(self, tiles, all_workers, all_invs, shed, obs):
        actions = []
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


_FIXED_ZONING_AGENT = ClosedLoopFixedZoningV1()

def agent(obs, config=None):
    return _FIXED_ZONING_AGENT(obs, config)
