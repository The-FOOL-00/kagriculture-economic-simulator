"""
Prototype Closed-Loop V2 Architecture Test
Validating the high-density zoned closed-loop controller with correct Fibonacci hire costs and full Day 11 expansion.
"""
import kaggle_environments

BOARD_SIZE = 10
TURNS_PER_DAY = 24
SHED_TILES = [(4, 4), (5, 4), (4, 5), (5, 5)]

CROPS = {
    "WHEAT":      {"seed": 10, "first_yield": 2, "max_yield": 6, "ongoing": False},
    "CARROT":     {"seed": 20, "first_yield": 2, "max_yield": 4, "ongoing": False},
    "TOMATO":     {"seed": 50, "first_yield": 8, "max_yield": 4, "ongoing": True},
    "STRAWBERRY": {"seed": 100, "first_yield": 10, "max_yield": 4, "ongoing": True},
    "MELON":      {"seed": 80, "first_yield": 10, "max_yield": 6, "ongoing": False},
}

BASE_PRICES = {
    "WHEAT": 25, "CARROT": 35, "TOMATO": 60, "STRAWBERRY": 120, "MELON": 250,
    "EGG": 50, "MILK": 160, "WOOL": 200, "FERTILIZER": 100
}

SELLABLE = ("STRAWBERRY", "MELON", "MILK", "WOOL", "EGG", "TOMATO", "CARROT", "WHEAT", "FERTILIZER")

# NW Dedicated Layout
PASTURES_NW = [(4, 3), (4, 2), (3, 3), (3, 4)]
ROW0_PATH = [(4, 0), (3, 0), (2, 0), (1, 0), (0, 0)]
ROW1_PATH = [(4, 1), (3, 1), (2, 1), (1, 1), (0, 1)]
ROW2_PATH = [(3, 2), (2, 2), (1, 2), (0, 2)]
ROW34_PATH = [(0, 3), (1, 3), (2, 3), (0, 4), (1, 4), (2, 4)]

# NE Dedicated Layout (10 pastures clustered near shed)
PASTURES_NE = [
    (5, 3), (6, 3), (7, 3), (8, 3),
    (5, 2), (6, 2), (7, 2), (8, 2),
    (6, 4), (7, 4)
]
NE_CROPS = [
    (9, 0), (8, 0), (7, 0), (6, 0), (5, 0),
    (9, 1), (8, 1), (7, 1), (6, 1), (5, 1),
    (9, 2), (9, 3), (8, 4), (9, 4), (5, 4)
]

# SW Dedicated Strawberry Grid (25 tiles: x in 0..4, y in 5..9)
SW_LANES = [
    [(0, 5), (1, 5), (2, 5), (3, 5), (4, 5), (4, 6)],
    [(3, 6), (2, 6), (1, 6), (0, 6), (0, 7), (1, 7)],
    [(2, 7), (3, 7), (4, 7), (4, 8), (3, 8), (2, 8)],
    [(1, 8), (0, 8), (0, 9), (1, 9), (2, 9), (3, 9), (4, 9)]
]

MOVES = {
    "NORTH": (0, -1),
    "SOUTH": (0, 1),
    "EAST":  (1, 0),
    "WEST":  (-1, 0),
}

def manhattan(p1, p2):
    return abs(p1[0] - p2[0]) + abs(p1[1] - p2[1])

def get_unlocked_shed_tiles(tiles):
    valid = []
    for x, y in SHED_TILES:
        if 0 <= x < BOARD_SIZE and 0 <= y < BOARD_SIZE:
            if tiles[y][x] != "LOCKED":
                valid.append((x, y))
    return valid if valid else [(4, 4)]

def is_walkable(x, y, tiles):
    if not (0 <= x < BOARD_SIZE and 0 <= y < BOARD_SIZE):
        return False
    if (x, y) in SHED_TILES:
        return True
    return tiles[y][x] != "LOCKED"

def bfs_step(start, target, tiles):
    if start == target:
        return "PASS"
    sx, sy = start
    tx, ty = target

    dx, dy = tx - sx, ty - sy
    if abs(dx) + abs(dy) == 1:
        for m_name, (mx, my) in MOVES.items():
            if mx == dx and my == dy:
                if is_walkable(tx, ty, tiles):
                    return m_name

    queue = [start]
    visited = {start: None}
    head = 0
    while head < len(queue):
        cx, cy = queue[head]
        head += 1
        if (cx, cy) == target:
            break
        for m_name, (mx, my) in MOVES.items():
            nx, ny = cx + mx, cy + my
            if is_walkable(nx, ny, tiles):
                if (nx, ny) not in visited:
                    visited[(nx, ny)] = ((cx, cy), m_name)
                    queue.append((nx, ny))

    if target not in visited or visited[target] is None:
        best_m = "PASS"
        best_dist = 999
        for m_name, (mx, my) in MOVES.items():
            nx, ny = sx + mx, sy + my
            if is_walkable(nx, ny, tiles):
                d = manhattan((nx, ny), target)
                if d < best_dist:
                    best_dist = d
                    best_m = m_name
        return best_m

    curr = target
    first_move = "PASS"
    while visited[curr] is not None:
        prev, move = visited[curr]
        if prev == start:
            first_move = move
            break
        curr = prev
    return first_move


def _fib(n):
    a, b = 1, 1
    for _ in range(n):
        a, b = b, a + b
    return a


class PrototypeAgent:
    def __init__(self):
        self.reset()

    def reset(self):
        self.last_step = -1
        self.q2_bought = False
        self.q3_bought = False

    def __call__(self, obs, config=None):
        day = int(obs.get("day", 0) or 0)
        hour = int(obs.get("hour", 0) or 0)
        step = obs.get("step")
        if step is None:
            step = day * TURNS_PER_DAY + hour
        else:
            step = int(step)

        if step == 0 or step <= self.last_step:
            self.reset()
        self.last_step = step

        player = int(obs.get("player", 0) or 0)
        farms = obs.get("farms", [{}, {}]) or [{}, {}]
        farm = farms[player] if len(farms) > player else {}
        private = obs.get("private", {}) or {}
        shed = dict(private.get("shed", {}) or {})
        seeds = dict(private.get("seeds", {}) or {})
        inventories = list(private.get("inventories", []) or [])

        tiles = farm.get("tiles", []) or []
        farmer_pos = tuple(farm.get("farmer", [4, 4]))
        hands_pos = [tuple(p) for p in farm.get("hands", []) or []]
        all_workers = [farmer_pos] + hands_pos
        money = float(farm.get("money", 0) or 0)
        quads = farm.get("unlocked_quadrants", ["NW"]) or ["NW"]

        # Step 712+ Terminal Engine
        if step >= 712:
            return self._terminal_action(obs, farm, private, tiles, all_workers, shed)

        market_orders = []

        # =====================================================================
        # MARKET & CAPITAL CONTROLLER
        # =====================================================================
        if step == 0:
            market_orders = [
                ["BUY_ANIMAL", "COW", 3],
                ["BUY_ANIMAL", "SHEEP", 1],
                ["BUY_SEED", "MELON", 12],
                ["BUY_SEED", "WHEAT", 8],
                ["BUY_PRODUCT", "WHEAT", 4],
                ["HIRE"],
                ["HIRE"],
                ["HIRE"],
                ["HIRE"]
            ]
        elif hour == 0:
            # 1. Morning Liquidation: SELL FIRST to fund buys
            for item in ["MELON", "STRAWBERRY", "WOOL", "MILK", "FERTILIZER"]:
                qty = int(shed.get(item, 0) or 0)
                if qty > 0 and len(market_orders) < 10:
                    market_orders.append(["SELL", item, qty])

            # 2. Land Unlocks
            if len(quads) == 1 and money >= 1200 and day >= 7 and not self.q2_bought:
                market_orders.append(["BUY_LAND"])
                self.q2_bought = True
            if len(quads) == 2 and money >= 2200 and day >= 10 and not self.q3_bought:
                market_orders.append(["BUY_LAND"])
                self.q3_bought = True

            # 3. Seed Purchases
            if "SW" in quads and money >= 1000 and day >= 10:
                straw_held = int(seeds.get("STRAWBERRY", 0) or 0)
                if straw_held < 25 and len(market_orders) < 10:
                    buy_straw = min(25 - straw_held, int(money // 100))
                    if buy_straw > 0:
                        market_orders.append(["BUY_SEED", "STRAWBERRY", buy_straw])

            if day in (11, 21) and money >= 1000:
                melon_held = int(seeds.get("MELON", 0) or 0)
                if melon_held < 12 and len(market_orders) < 10:
                    buy_m = min(12 - melon_held, int(money // 80))
                    if buy_m > 0:
                        market_orders.append(["BUY_SEED", "MELON", buy_m])

            # 4. Livestock & Feed Maintenance
            cows_alive = sum(1 for row in tiles for t in row if isinstance(t, dict) and t.get("animal") == "COW")
            sheep_alive = sum(1 for row in tiles for t in row if isinstance(t, dict) and t.get("animal") == "SHEEP")
            total_animals = cows_alive + sheep_alive
            wheat_held = int(shed.get("WHEAT", 0) or 0)
            needed_feed = max(4, total_animals)
            if wheat_held < needed_feed and money >= 60 and len(market_orders) < 10:
                buy_feed = min(needed_feed - wheat_held, int(money // 30))
                if buy_feed > 0:
                    market_orders.append(["BUY_PRODUCT", "WHEAT", buy_feed])

            if "NE" in quads and money >= 1500:
                active_p = PASTURES_NW + PASTURES_NE
                empty_built_p = [p for p in active_p if isinstance(tiles[p[1]][p[0]], dict) and tiles[p[1]][p[0]].get("kind") == "PASTURE" and not tiles[p[1]][p[0]].get("animal")]
                animals_in_shed = int(shed.get("COW", 0) or 0) + int(shed.get("SHEEP", 0) or 0)
                slots = max(0, len(empty_built_p) - animals_in_shed)
                if slots > 0:
                    if cows_alive < 10 and len(market_orders) < 10:
                        bc = min(slots, min(3, int(money // 400)))
                        if bc > 0:
                            market_orders.append(["BUY_ANIMAL", "COW", bc])
                            slots -= bc
                    if sheep_alive < 4 and slots > 0 and len(market_orders) < 10:
                        bs = min(slots, min(2, int(money // 500)))
                        if bs > 0:
                            market_orders.append(["BUY_ANIMAL", "SHEEP", bs])

            # 5. Labor Hiring (cost is Fibonacci: 1, 1, 2, 3, 5, 8...)
            hires_today = int(farm.get("hires_today", 0) or 0)
            if day < 7:
                target_hands = 4
            elif day < 10:
                target_hands = 6
            elif "SW" in quads and money >= 3000:
                target_hands = 12
            elif money >= 1000:
                target_hands = 8
            else:
                target_hands = 4

            curr_hires = hires_today
            rem_money = money
            while curr_hires < target_hands and len(market_orders) < 10:
                cost = _fib(curr_hires)
                if rem_money >= cost:
                    market_orders.append(["HIRE"])
                    rem_money -= cost
                    curr_hires += 1
                else:
                    break

        # =====================================================================
        # WORKER CONTROLLERS
        # =====================================================================
        f_inv = inventories[0] if len(inventories) > 0 else {}
        farmer_act = self._livestock_act(farmer_pos, f_inv, PASTURES_NW, tiles, shed)

        hands_act = [["PASS"] for _ in hands_pos]
        nw_crop_paths = [ROW0_PATH, ROW1_PATH, ROW2_PATH, ROW34_PATH]

        for h_idx, h_pos in enumerate(hands_pos):
            w_idx = h_idx + 1
            h_inv = inventories[w_idx] if w_idx < len(inventories) else {}

            if h_idx < 4:
                path = nw_crop_paths[h_idx]
                hands_act[h_idx] = self._crop_act(h_pos, h_inv, path, tiles, shed, seeds, day, hour)
            elif h_idx == 4 and "NE" in quads:
                hands_act[h_idx] = self._livestock_act(h_pos, h_inv, PASTURES_NE, tiles, shed)
            elif h_idx == 5 and "NE" in quads:
                hands_act[h_idx] = self._crop_act(h_pos, h_inv, NE_CROPS, tiles, shed, seeds, day, hour)
            elif "SW" in quads:
                lane_idx = (h_idx - 6) % len(SW_LANES) if h_idx >= 6 else (h_idx % len(SW_LANES))
                lane = SW_LANES[lane_idx]
                hands_act[h_idx] = self._crop_act(h_pos, h_inv, lane, tiles, shed, seeds, day, hour)
            else:
                path = nw_crop_paths[h_idx % 4]
                hands_act[h_idx] = self._crop_act(h_pos, h_inv, path, tiles, shed, seeds, day, hour)

        return {
            "farmer": farmer_act,
            "hands": hands_act,
            "market": market_orders[:10]
        }

    def _livestock_act(self, w_pos, w_inv, pastures, tiles, shed):
        wx, wy = w_pos
        w_tile = tiles[wy][wx] if 0 <= wy < BOARD_SIZE and 0 <= wx < BOARD_SIZE else None
        w_load = sum(w_inv.values())

        unbuilt_p = [p for p in pastures if tiles[p[1]][p[0]] is None]
        empty_p = [p for p in pastures if isinstance(tiles[p[1]][p[0]], dict) and tiles[p[1]][p[0]].get("kind") == "PASTURE" and not tiles[p[1]][p[0]].get("animal")]
        hungry_p = [p for p in pastures if isinstance(tiles[p[1]][p[0]], dict) and tiles[p[1]][p[0]].get("animal") and not tiles[p[1]][p[0]].get("fed_today")]
        fert_p = [p for p in pastures if isinstance(tiles[p[1]][p[0]], dict) and tiles[p[1]][p[0]].get("fertilizer_available")]
        yield_p = [p for p in pastures if isinstance(tiles[p[1]][p[0]], dict) and int(tiles[p[1]][p[0]].get("yield_units", 0) or 0) > 0]

        # 1. On current tile
        if w_tile is None and w_pos in pastures:
            return ["BUILD_PASTURE"]
        elif isinstance(w_tile, dict) and w_tile.get("kind") == "PASTURE":
            if not w_tile.get("animal"):
                if w_inv.get("COW", 0) > 0:
                    return ["PLACE", "COW"]
                elif w_inv.get("SHEEP", 0) > 0:
                    return ["PLACE", "SHEEP"]
            else:
                if not w_tile.get("fed_today") and w_inv.get("WHEAT", 0) > 0:
                    return ["FEED"]
                elif w_tile.get("fertilizer_available"):
                    return ["COLLECT_FERTILIZER"]
                elif int(w_tile.get("yield_units", 0) or 0) > 0:
                    return ["HARVEST"]

        # 2. At shed: multi-item pickup and dropping
        if w_pos in SHED_TILES:
            sellables = any(k in SELLABLE and k != "WHEAT" for k, v in w_inv.items() if v > 0)
            if sellables:
                return ["DROP"]

            needed_animals = len(empty_p) - (w_inv.get("COW", 0) + w_inv.get("SHEEP", 0))
            if needed_animals > 0:
                cows_avail = int(shed.get("COW", 0) or 0)
                sheep_avail = int(shed.get("SHEEP", 0) or 0)
                if cows_avail > 0:
                    take = min(cows_avail, needed_animals)
                    return ["PICKUP", "COW", take]
                elif sheep_avail > 0:
                    take = min(sheep_avail, needed_animals)
                    return ["PICKUP", "SHEEP", take]

            needed_feed = len(hungry_p) - w_inv.get("WHEAT", 0)
            feed_avail = int(shed.get("WHEAT", 0) or 0)
            if needed_feed > 0 and feed_avail > 0:
                take_feed = min(feed_avail, needed_feed)
                return ["PICKUP", "WHEAT", take_feed]

        # 3. Routing
        target = None
        if hungry_p and w_inv.get("WHEAT", 0) > 0:
            target = min(hungry_p, key=lambda p: manhattan(w_pos, p))
        elif (w_inv.get("COW", 0) > 0 or w_inv.get("SHEEP", 0) > 0) and empty_p:
            target = min(empty_p, key=lambda p: manhattan(w_pos, p))
        elif (hungry_p and w_inv.get("WHEAT", 0) == 0 and shed.get("WHEAT", 0) > 0) or \
             (empty_p and (w_inv.get("COW", 0) + w_inv.get("SHEEP", 0)) == 0 and (shed.get("COW", 0) > 0 or shed.get("SHEEP", 0) > 0)):
            target = min(get_unlocked_shed_tiles(tiles), key=lambda s: manhattan(w_pos, s))
        elif yield_p:
            target = min(yield_p, key=lambda p: manhattan(w_pos, p))
        elif fert_p:
            target = min(fert_p, key=lambda p: manhattan(w_pos, p))
        elif unbuilt_p:
            target = min(unbuilt_p, key=lambda p: manhattan(w_pos, p))
        elif w_load > 0:
            target = min(get_unlocked_shed_tiles(tiles), key=lambda s: manhattan(w_pos, s))

        if target and target != w_pos:
            return [bfs_step(w_pos, target, tiles)]
        return ["PASS"]

    def _crop_act(self, w_pos, w_inv, path, tiles, shed, seeds, day, hour):
        wx, wy = w_pos
        w_tile = tiles[wy][wx] if 0 <= wy < BOARD_SIZE and 0 <= wx < BOARD_SIZE else None
        w_load = sum(w_inv.values())

        if w_pos in SHED_TILES and w_load > 0:
            return ["DROP"]

        if isinstance(w_tile, dict) and w_tile.get("kind") == "PLANT":
            crop = w_tile.get("crop")
            age = day - int(w_tile.get("planted_day", 0) or 0)
            fy = CROPS.get(crop, {}).get("first_yield", 2)
            units = int(w_tile.get("yield_units", 0) or 0)
            if units >= 6 or (age >= fy and units > 0):
                return ["HARVEST"]
            elif not w_tile.get("watered_today"):
                return ["WATER"]
        elif w_tile is None and w_pos in path:
            if path in SW_LANES:
                if seeds.get("STRAWBERRY", 0) > 0:
                    seeds["STRAWBERRY"] -= 1
                    return ["PLANT", "STRAWBERRY"]
            elif (wy in (0, 1) or (wy == 2 and wx in (0, 1))) and seeds.get("MELON", 0) > 0:
                seeds["MELON"] -= 1
                return ["PLANT", "MELON"]
            elif seeds.get("WHEAT", 0) > 0:
                seeds["WHEAT"] -= 1
                return ["PLANT", "WHEAT"]

        if w_load >= 6 or (hour >= 21 and w_load > 0):
            nearest_shed = min(get_unlocked_shed_tiles(tiles), key=lambda s: manhattan(w_pos, s))
            return [bfs_step(w_pos, nearest_shed, tiles)]

        target = None
        for tp in path:
            tx, ty = tp
            if not (0 <= tx < BOARD_SIZE and 0 <= ty < BOARD_SIZE):
                continue
            tt = tiles[ty][tx]
            if isinstance(tt, dict) and tt.get("kind") == "PLANT" and not tt.get("watered_today"):
                target = tp
                break

        if not target:
            for tp in path:
                tx, ty = tp
                if not (0 <= tx < BOARD_SIZE and 0 <= ty < BOARD_SIZE):
                    continue
                tt = tiles[ty][tx]
                if isinstance(tt, dict) and tt.get("kind") == "PLANT":
                    crop = tt.get("crop")
                    age = day - int(tt.get("planted_day", 0) or 0)
                    fy = CROPS.get(crop, {}).get("first_yield", 2)
                    if int(tt.get("yield_units", 0) or 0) > 0 and age >= fy:
                        target = tp
                        break

        if not target:
            for tp in path:
                tx, ty = tp
                if not (0 <= tx < BOARD_SIZE and 0 <= ty < BOARD_SIZE):
                    continue
                tt = tiles[ty][tx]
                if tt is None:
                    if path in SW_LANES and seeds.get("STRAWBERRY", 0) > 0:
                        target = tp
                        break
                    elif (ty in (0, 1) or (ty == 2 and tx in (0, 1))) and seeds.get("MELON", 0) > 0:
                        target = tp
                        break
                    elif seeds.get("WHEAT", 0) > 0:
                        target = tp
                        break

        if target and target != w_pos:
            return [bfs_step(w_pos, target, tiles)]
        elif w_load > 0:
            nearest_shed = min(get_unlocked_shed_tiles(tiles), key=lambda s: manhattan(w_pos, s))
            return [bfs_step(w_pos, nearest_shed, tiles)]

        return ["PASS"]

    def _terminal_action(self, obs, farm, private, tiles, all_workers, shed):
        size = len(tiles)
        sheds = set(get_unlocked_shed_tiles(tiles))
        inventories = list(private.get("inventories", []) or [])
        inventories.extend({} for _ in range(len(all_workers) - len(inventories)))

        available_ripe = {
            (x, y)
            for y, row in enumerate(tiles)
            for x, tile in enumerate(row)
            if isinstance(tile, dict) and int(tile.get("yield_units", 0) or 0) > 0
        }

        actions = []
        pending_drop = {}

        for pos, inv in zip(all_workers, inventories):
            inv = inv or {}
            load = sum(max(0, int(v or 0)) for v in inv.values())
            x, y = pos
            tile = tiles[y][x] if 0 <= y < size and 0 <= x < size else None

            if load > 0 and pos in sheds:
                act = ["DROP"]
                for item, count in inv.items():
                    if item in SELLABLE:
                        pending_drop[item] = pending_drop.get(item, 0) + max(0, int(count or 0))
            elif isinstance(tile, dict) and int(tile.get("yield_units", 0) or 0) > 0:
                act = ["HARVEST"]
                available_ripe.discard(pos)
            elif load > 0:
                nearest_shed = min(sheds, key=lambda s: manhattan(pos, s))
                act = [bfs_step(pos, nearest_shed, tiles)]
            elif available_ripe:
                target = min(available_ripe, key=lambda t: (manhattan(pos, t), t[1], t[0]))
                available_ripe.discard(target)
                act = [bfs_step(pos, target, tiles)]
            elif isinstance(tile, dict) and tile.get("fertilizer_available", False):
                act = ["COLLECT_FERTILIZER"]
            else:
                act = ["PASS"]
            actions.append(act)

        merged_shed = dict(shed)
        for item, count in pending_drop.items():
            merged_shed[item] = int(merged_shed.get(item, 0) or 0) + count

        sells = []
        for item in SELLABLE:
            qty = int(merged_shed.get(item, 0) or 0)
            if qty > 0:
                p = BASE_PRICES.get(item, 100)
                sells.append((qty * p, item, qty))

        sells.sort(reverse=True)
        market = [["SELL", item, qty] for _, item, qty in sells[:10]]

        return {
            "farmer": actions[0],
            "hands": actions[1:],
            "market": market[:10]
        }

prototype_agent = PrototypeAgent()
