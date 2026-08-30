"""
Standalone Competitive Opponent: O12 Top-Meta Emulator
"""
import math

CROPS = {
    "WHEAT":      {"seed": 10, "first_yield_day": 2, "max_yield_day": 4, "interval": 0, "max_yield": 6, "ongoing": False, "base_yield": 4},
    "CARROT":     {"seed": 20, "first_yield_day": 2, "max_yield_day": 3, "interval": 0, "max_yield": 4, "ongoing": False, "base_yield": 3},
    "TOMATO":     {"seed": 50, "first_yield_day": 8, "max_yield_day": 8, "interval": 1, "max_yield": 4, "ongoing": True,  "base_yield": 4},
    "STRAWBERRY": {"seed": 100, "first_yield_day": 10, "max_yield_day": 10, "interval": 2, "max_yield": 4, "ongoing": True,  "base_yield": 4},
    "MELON":      {"seed": 80, "first_yield_day": 10, "max_yield_day": 12, "interval": 0, "max_yield": 6, "ongoing": False, "base_yield": 6},
}

ANIMALS = {
    "GOOSE": {"cost": 300, "structure": "COOP",    "first_yield_day": 4, "interval": 1, "max_held": 4, "product": "EGG"},
    "COW":   {"cost": 600, "structure": "PASTURE", "first_yield_day": 8, "interval": 2, "max_held": 6, "product": "MILK"},
    "SHEEP": {"cost": 500, "structure": "PASTURE", "first_yield_day": 6, "interval": 3, "max_held": 6, "product": "WOOL"},
}

PRODUCTS = ["WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON", "EGG", "MILK", "WOOL", "FERTILIZER"]
PRICE_FLOOR = 1

def fib_hire_cost(n):
    a, b = 1, 1
    for _ in range(n):
        a, b = b, a + b
    return a

def manhattan(p1, p2):
    return abs(p1[0] - p2[0]) + abs(p1[1] - p2[1])

def get_unlocked_shed_tiles(tiles):
    half = len(tiles) // 2
    candidates = [(half - 1, half - 1), (half, half - 1), (half - 1, half), (half, half)]
    return [pos for pos in candidates if tiles[pos[1]][pos[0]] != "LOCKED"]

def get_next_step(start, target, tiles):
    if start == target: return "PASS"
    sx, sy = start
    tx, ty = target
    moves = []
    if tx > sx and tiles[sy][sx + 1] != "LOCKED": moves.append("EAST")
    if tx < sx and tiles[sy][sx - 1] != "LOCKED": moves.append("WEST")
    if ty > sy and tiles[sy + 1][sx] != "LOCKED": moves.append("SOUTH")
    if ty < sy and tiles[sy - 1][sx] != "LOCKED": moves.append("NORTH")
    if not moves:
        for m, (dx, dy) in [("EAST", (1,0)), ("WEST", (-1,0)), ("SOUTH", (0,1)), ("NORTH", (0,-1))]:
            nx, ny = sx + dx, sy + dy
            if 0 <= nx < len(tiles[0]) and 0 <= ny < len(tiles) and tiles[ny][nx] != "LOCKED":
                moves.append(m)
    return moves[0] if moves else "PASS"

class OpponentBot:
    def __init__(self):
        self.target_cows = 8
        self.target_sheep = 4
        self.target_geese = 0
        self.primary_crop = "MELON"
        self.primary_crop_count = 10
        self.secondary_crop = "CARROT"
        self.secondary_crop_count = 12
        self.day0_land = True
        self.day10_land = False
        self.sell_batch_size = 14
        self.care_animals = True

    def __call__(self, obs, configuration=None):
        try:
            player = obs.get("player", 0)
            day = obs.get("day", 0)
            hour = obs.get("hour", 0)
            step = obs.get("step", day * 24 + hour)

            farms = obs.get("farms", [])
            farm = farms[player] if farms and player < len(farms) else {}
            money = float(farm.get("money", 0.0))
            farmer_pos = tuple(farm.get("farmer", [4, 4]))
            hands = [tuple(h) for h in farm.get("hands", [])]
            hires_today = int(farm.get("hires_today", 0))
            unlocked_quads = list(farm.get("unlocked_quadrants", ["NW"]))
            tiles = farm.get("tiles", [[None]*10 for _ in range(10)])

            private = obs.get("private", {}) or {}
            shed = dict(private.get("shed", {}))
            seeds = dict(private.get("seeds", {}))
            inventories = [dict(inv) for inv in private.get("inventories", [{}])]

            market = obs.get("market", {}) or {}
            market_prices = dict(market.get("prices", {}))

            orders = []
            chores = []
            empty_tiles = []
            cow_count = 0
            sheep_count = 0
            goose_count = 0
            pasture_count = 0
            empty_pastures = []
            coop_count = 0
            empty_coops = []
            crop_counts = {c: 0 for c in CROPS}
            unfed_animal_tiles = []

            for y in range(len(tiles)):
                for x in range(len(tiles[0])):
                    t = tiles[y][x]
                    pos = (x, y)
                    if t is None:
                        empty_tiles.append(pos)
                    elif isinstance(t, dict):
                        kind = t.get("kind")
                        if kind == "WEED":
                            chores.append({"type": "DIG", "pos": pos, "weight": 95})
                        elif kind == "COOP":
                            coop_count += 1
                            if "animal" in t and t.get("animal"):
                                goose_count += 1
                                if not t.get("fed_today", False):
                                    chores.append({"type": "FEED", "pos": pos, "weight": 90})
                                    unfed_animal_tiles.append(pos)
                                if not t.get("cared_today", False):
                                    chores.append({"type": "CARE", "pos": pos, "weight": 75})
                                if t.get("fertilizer_available", False):
                                    chores.append({"type": "COLLECT_FERTILIZER", "pos": pos, "weight": 85})
                                if t.get("yield_units", 0) > 0:
                                    chores.append({"type": "HARVEST", "pos": pos, "weight": 100})
                            else:
                                empty_coops.append(pos)
                        elif kind == "PASTURE":
                            pasture_count += 1
                            if "animal" in t and t.get("animal"):
                                a_type = t.get("animal")
                                if a_type == "COW": cow_count += 1
                                elif a_type == "SHEEP": sheep_count += 1
                                if not t.get("fed_today", False):
                                    chores.append({"type": "FEED", "pos": pos, "weight": 92})
                                    unfed_animal_tiles.append(pos)
                                if not t.get("cared_today", False):
                                    chores.append({"type": "CARE", "pos": pos, "weight": 76})
                                if t.get("fertilizer_available", False):
                                    chores.append({"type": "COLLECT_FERTILIZER", "pos": pos, "weight": 86})
                                if t.get("yield_units", 0) > 0:
                                    chores.append({"type": "HARVEST", "pos": pos, "weight": 100})
                            else:
                                empty_pastures.append(pos)
                        elif kind == "PLANT":
                            crop = t.get("crop")
                            if crop in crop_counts: crop_counts[crop] += 1
                            age = day - t.get("planted_day", 0)
                            cd = CROPS.get(crop, {})
                            if not t.get("watered_today", False):
                                chores.append({"type": "WATER", "pos": pos, "weight": 82})

                            if cd.get("ongoing", False):
                                if age >= cd.get("first_yield_day", 8) and t.get("yield_units", 0) > 0:
                                    chores.append({"type": "HARVEST", "pos": pos, "weight": 100})
                            else:
                                if crop == "MELON" and (age >= 10 or t.get("yield_units", 0) >= 6 or (day >= 28 and t.get("yield_units", 0) >= 1)):
                                    chores.append({"type": "HARVEST", "pos": pos, "weight": 100})
                                elif crop == "CARROT" and (age >= 3 or t.get("yield_units", 0) >= 3 or (day >= 28 and t.get("yield_units", 0) >= 1)):
                                    chores.append({"type": "HARVEST", "pos": pos, "weight": 100})
                                elif crop == "WHEAT" and (age >= 4 or t.get("yield_units", 0) >= 4 or (day >= 28 and t.get("yield_units", 0) >= 1)):
                                    chores.append({"type": "HARVEST", "pos": pos, "weight": 100})
                                elif age >= cd.get("max_yield_day", 4) and t.get("yield_units", 0) > 0:
                                    chores.append({"type": "HARVEST", "pos": pos, "weight": 100})

            cows_in_transit = shed.get("COW", 0) + sum(inv.get("COW", 0) for inv in inventories)
            sheep_in_transit = shed.get("SHEEP", 0) + sum(inv.get("SHEEP", 0) for inv in inventories)
            geese_in_transit = shed.get("GOOSE", 0) + sum(inv.get("GOOSE", 0) for inv in inventories)
            total_active_animals = cow_count + sheep_count + goose_count + cows_in_transit + sheep_in_transit + geese_in_transit

            # 1. HIRE WORKERS
            total_chores_est = len(chores) + len(empty_tiles)
            if len(unlocked_quads) == 1:
                target_hands = min(3, max(2, (total_chores_est + 6) // 8))
            elif len(unlocked_quads) == 2:
                target_hands = min(5, max(3, (total_chores_est + 8) // 9))
            else:
                target_hands = min(6, max(4, (total_chores_est + 10) // 10))

            if hour == 0 and target_hands > hires_today:
                for _ in range(target_hands - hires_today):
                    cost = fib_hire_cost(hires_today + len([o for o in orders if o[0] == "HIRE"]))
                    if money >= cost + 10:
                        orders.append(["HIRE"])
                        money -= cost

            # 2. LAND EXPANSION
            n_unlocked = len(unlocked_quads) - 1
            if n_unlocked == 0 and self.day0_land and money >= 1200:
                orders.append(["BUY_LAND"])
                money -= 1000
            elif n_unlocked == 1 and self.day10_land and day <= 14 and money >= 2400:
                orders.append(["BUY_LAND"])
                money -= 2000

            spendable = max(0.0, money - 25.0)

            # 3. BUY ANIMALS
            needed_cows = max(0, self.target_cows - cow_count - cows_in_transit)
            needed_sheep = max(0, self.target_sheep - sheep_count - sheep_in_transit)
            needed_geese = max(0, self.target_geese - goose_count - geese_in_transit)

            cows_ordered = 0
            sheep_ordered = 0
            geese_ordered = 0

            if day <= 12:
                if needed_cows > 0 and spendable >= 695 and len(orders) < 10:
                    orders.append(["BUY_ANIMAL", "COW", 1])
                    spendable -= 600
                    money -= 600
                    needed_cows -= 1
                    cows_ordered += 1
                    total_active_animals += 1
                elif needed_sheep > 0 and spendable >= 595 and len(orders) < 10:
                    orders.append(["BUY_ANIMAL", "SHEEP", 1])
                    spendable -= 500
                    money -= 500
                    needed_sheep -= 1
                    sheep_ordered += 1
                    total_active_animals += 1
                elif needed_geese > 0 and spendable >= 395 and len(orders) < 10:
                    orders.append(["BUY_ANIMAL", "GOOSE", 1])
                    spendable -= 300
                    money -= 300
                    needed_geese -= 1
                    geese_ordered += 1
                    total_active_animals += 1

            # 4. WHEAT FEED BUFFER
            if total_active_animals > 0 and day <= 28:
                total_wheat_held = shed.get("WHEAT", 0) + sum(inv.get("WHEAT", 0) for inv in inventories)
                feed_buffer_target = total_active_animals * 3
                if total_wheat_held < feed_buffer_target:
                    deficit = feed_buffer_target - total_wheat_held
                    buy_wheat_qty = min(deficit + total_active_animals, int(spendable // 25))
                    if buy_wheat_qty > 0 and len(orders) < 10:
                        orders.append(["BUY_PRODUCT", "WHEAT", buy_wheat_qty])
                        spendable -= buy_wheat_qty * 25
                        money -= buy_wheat_qty * 25

            # 5. CROP SEED PURCHASES
            total_seeds = sum(seeds.values())
            needed_seeds = max(0, len(empty_tiles) - total_seeds)

            if needed_seeds > 0 and day <= 26 and spendable > 0 and len(orders) < 10:
                p_cost = CROPS[self.primary_crop]["seed"]
                s_cost = CROPS[self.secondary_crop]["seed"]

                p_rem = max(0, self.primary_crop_count - crop_counts.get(self.primary_crop, 0) - seeds.get(self.primary_crop, 0))
                p_cnt = min(p_rem, needed_seeds, int(spendable // p_cost))
                rem = needed_seeds - p_cnt
                s_cnt = min(rem, int((spendable - p_cnt * p_cost) // s_cost))
                w_cnt = min(rem - s_cnt, int((spendable - p_cnt * p_cost - s_cnt * s_cost) // 10))

                if p_cnt > 0: orders.append(["BUY_SEED", self.primary_crop, p_cnt])
                if s_cnt > 0: orders.append(["BUY_SEED", self.secondary_crop, s_cnt])
                if w_cnt > 0: orders.append(["BUY_SEED", "WHEAT", w_cnt])

            # 6. SELLING & MARKET POLICIES
            feed_reserve = total_active_animals * 4 if day < 26 else 0
            sell_priority = ["MELON", "WOOL", "MILK", "FERTILIZER", "EGG", "STRAWBERRY", "TOMATO", "CARROT", "WHEAT"]
            for prod in sell_priority:
                if len(orders) >= 10:
                    break
                qty = shed.get(prod, 0)
                if prod == "WHEAT":
                    qty = max(0, qty - feed_reserve)
                if qty > 0:
                    cur_p = market_prices.get(prod, 1)
                    should_sell = False
                    if day >= 26 or sum(shed.values()) >= 25 or cur_p > 1:
                        should_sell = True
                    if step % 4 == 0:
                        should_sell = True

                    if should_sell:
                        sell_amount = min(qty, self.sell_batch_size) if day < 26 else qty
                        orders.append(["SELL", prod, sell_amount])

            # 7. WORKER ACTIONS & CHORES
            num_workers = 1 + len(hands)
            worker_pos = [farmer_pos] + list(hands)
            actions = [["PASS"] for _ in range(num_workers)]
            unassigned = list(range(num_workers))
            assigned_pos = set()

            unplaced_pasture_animals = cows_in_transit + sheep_in_transit + cows_ordered + sheep_ordered
            total_pastures_target = self.target_cows + self.target_sheep
            pastures_to_build = max(0, min(total_pastures_target - pasture_count, unplaced_pasture_animals - len(empty_pastures)))

            unplaced_geese = geese_in_transit + geese_ordered
            total_coops_target = self.target_geese
            coops_to_build = max(0, min(total_coops_target - coop_count, unplaced_geese - len(empty_coops)))

            if sum(seeds.values()) > 0 and day <= 26:
                for pos in empty_tiles:
                    chores.append({"type": "PLANT", "pos": pos, "weight": 70})

            avail_seeds = dict(seeds)
            for w in list(unassigned):
                pos = worker_pos[w]
                x, y = pos
                t = tiles[y][x]
                inv = inventories[w] if w < len(inventories) else {}

                if isinstance(t, dict):
                    kind = t.get("kind")
                    if kind == "WEED":
                        actions[w] = ["DIG"]
                        unassigned.remove(w)
                        assigned_pos.add(pos)
                        continue
                    elif "animal" in t and t.get("animal"):
                        if not t.get("fed_today", False) and inv.get("WHEAT", 0) > 0:
                            actions[w] = ["FEED"]
                            inv["WHEAT"] -= 1
                            unassigned.remove(w)
                            assigned_pos.add(pos)
                            if pos in unfed_animal_tiles: unfed_animal_tiles.remove(pos)
                            continue
                        if t.get("yield_units", 0) > 0:
                            actions[w] = ["HARVEST"]
                            unassigned.remove(w)
                            assigned_pos.add(pos)
                            continue
                        if t.get("fertilizer_available", False):
                            actions[w] = ["COLLECT_FERTILIZER"]
                            unassigned.remove(w)
                            assigned_pos.add(pos)
                            continue
                        if not t.get("cared_today", False):
                            actions[w] = ["CARE"]
                            unassigned.remove(w)
                            assigned_pos.add(pos)
                            continue
                    elif kind == "PASTURE" and "animal" not in t:
                        if inv.get("COW", 0) > 0:
                            actions[w] = ["PLACE", "COW"]
                            inv["COW"] -= 1
                            unassigned.remove(w)
                            assigned_pos.add(pos)
                            continue
                        elif inv.get("SHEEP", 0) > 0:
                            actions[w] = ["PLACE", "SHEEP"]
                            inv["SHEEP"] -= 1
                            unassigned.remove(w)
                            assigned_pos.add(pos)
                            continue
                    elif kind == "COOP" and "animal" not in t:
                        if inv.get("GOOSE", 0) > 0:
                            actions[w] = ["PLACE", "GOOSE"]
                            inv["GOOSE"] -= 1
                            unassigned.remove(w)
                            assigned_pos.add(pos)
                            continue
                    elif kind == "PLANT":
                        is_h = any(c["pos"] == pos and c["type"] == "HARVEST" for c in chores)
                        if is_h:
                            actions[w] = ["HARVEST"]
                            unassigned.remove(w)
                            assigned_pos.add(pos)
                            continue
                        if not t.get("watered_today", False):
                            actions[w] = ["WATER"]
                            unassigned.remove(w)
                            assigned_pos.add(pos)
                            continue
                elif t is None:
                    if pastures_to_build > 0:
                        actions[w] = ["BUILD_PASTURE"]
                        pastures_to_build -= 1
                        pasture_count += 1
                        empty_pastures.append(pos)
                        unassigned.remove(w)
                        assigned_pos.add(pos)
                        continue
                    elif coops_to_build > 0:
                        actions[w] = ["BUILD_COOP"]
                        coops_to_build -= 1
                        coop_count += 1
                        empty_coops.append(pos)
                        unassigned.remove(w)
                        assigned_pos.add(pos)
                        continue
                    elif day <= 26:
                        for sc in ["MELON", "STRAWBERRY", "TOMATO", "CARROT", "WHEAT"]:
                            if avail_seeds.get(sc, 0) > 0:
                                actions[w] = ["PLANT", sc]
                                avail_seeds[sc] -= 1
                                unassigned.remove(w)
                                assigned_pos.add(pos)
                                break

            unlocked_sheds = get_unlocked_shed_tiles(tiles)
            for w in list(unassigned):
                w_p = worker_pos[w]
                inv = inventories[w] if w < len(inventories) else {}

                if w_p in unlocked_sheds:
                    if shed.get("COW", 0) > 0 and inv.get("COW", 0) == 0 and empty_pastures:
                        actions[w] = ["PICKUP", "COW", 1]
                        shed["COW"] -= 1
                        unassigned.remove(w)
                        continue
                    elif shed.get("SHEEP", 0) > 0 and inv.get("SHEEP", 0) == 0 and empty_pastures:
                        actions[w] = ["PICKUP", "SHEEP", 1]
                        shed["SHEEP"] -= 1
                        unassigned.remove(w)
                        continue
                    elif shed.get("GOOSE", 0) > 0 and inv.get("GOOSE", 0) == 0 and empty_coops:
                        actions[w] = ["PICKUP", "GOOSE", 1]
                        shed["GOOSE"] -= 1
                        unassigned.remove(w)
                        continue
                    elif unfed_animal_tiles and shed.get("WHEAT", 0) > 0 and inv.get("WHEAT", 0) == 0:
                        take_qty = min(4, shed["WHEAT"])
                        actions[w] = ["PICKUP", "WHEAT", take_qty]
                        shed["WHEAT"] -= take_qty
                        unassigned.remove(w)
                        continue

            rem_chores = [c for c in chores if c["pos"] not in assigned_pos]
            claimed_unfed = set()

            for w in list(unassigned):
                w_p = worker_pos[w]
                inv = inventories[w] if w < len(inventories) else {}

                if inv.get("COW", 0) > 0 or inv.get("SHEEP", 0) > 0:
                    if empty_pastures:
                        target = min(empty_pastures, key=lambda p: manhattan(w_p, p))
                        actions[w] = [get_next_step(w_p, target, tiles)]
                        unassigned.remove(w)
                        continue
                if inv.get("GOOSE", 0) > 0:
                    if empty_coops:
                        target = min(empty_coops, key=lambda p: manhattan(w_p, p))
                        actions[w] = [get_next_step(w_p, target, tiles)]
                        unassigned.remove(w)
                        continue

                if inv.get("WHEAT", 0) > 0 and unfed_animal_tiles:
                    avail_unfed = [p for p in unfed_animal_tiles if p not in claimed_unfed]
                    target = min(avail_unfed or unfed_animal_tiles, key=lambda p: manhattan(w_p, p))
                    claimed_unfed.add(target)
                    actions[w] = [get_next_step(w_p, target, tiles)]
                    unassigned.remove(w)
                    continue

                if inv.get("WHEAT", 0) == 0 and unfed_animal_tiles and shed.get("WHEAT", 0) > 0:
                    if len(claimed_unfed) < len(unfed_animal_tiles) and unlocked_sheds:
                        actions[w] = [get_next_step(w_p, unlocked_sheds[0], tiles)]
                        unassigned.remove(w)
                        continue

            for w in unassigned:
                w_p = worker_pos[w]
                if rem_chores:
                    best_c = None
                    best_score = -999999.0
                    for c in rem_chores:
                        dist = manhattan(w_p, c["pos"])
                        score = c["weight"] - dist * 2.0
                        if score > best_score:
                            best_score = score
                            best_c = c
                    if best_c:
                        actions[w] = [get_next_step(w_p, best_c["pos"], tiles)]
                        assigned_pos.add(best_c["pos"])
                        rem_chores.remove(best_c)
                        continue

                if w_p not in unlocked_sheds and unlocked_sheds:
                    actions[w] = [get_next_step(w_p, unlocked_sheds[0], tiles)]
                else:
                    actions[w] = ["PASS"]

            return {
                "farmer": actions[0],
                "hands": actions[1:] if len(actions) > 1 else [],
                "market": orders[:10]
            }
        except Exception:
            return {"farmer": ["PASS"], "hands": [], "market": []}

_opp_instance = OpponentBot()
def agent(obs, configuration=None):
    return _opp_instance(obs, configuration)
