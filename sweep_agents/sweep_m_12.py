"""
=============================================================================
KAGGRICULTURE CHAMPION DELIVERABLE 1: HYBRID 6C / 3S / 10M (CORRECTED)
=============================================================================
High-performance standalone hybrid agriculture agent:
- Capital deployment: Day-0 NE Land ($1,000) + SW Land ($2,000) scaling.
- Livestock fleet: 6 Cows (Milk @ $160) + 3 Sheep (Wool @ $200).
- Crop portfolio: 10 Early Melons (Compounding Capital) -> Carrots & Wheat.
- Feed reserve: Strict Wheat safety buffer ensuring zero animal starvation.
- Town synchronization: Post-consumption window liquidation (step % 4 == 0).
- Worker fleet: Dynamic Fibonacci-costed farm hands with spatial bipartite routing.
=============================================================================
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
MARKET_I0 = 10000
PRICE_FLOOR = 1

MARKET_PARAMS = {
    "WHEAT":      {"base":  25, "I0": MARKET_I0, "T": 400, "below_func": "sqrt",   "below_target": 0.80, "above_func": "log",    "above_target": 0.20},
    "CARROT":     {"base":  35, "I0": MARKET_I0, "T": 450, "below_func": "log",    "below_target": 0.20, "above_func": "sqrt",   "above_target": 0.70},
    "TOMATO":     {"base":  60, "I0": MARKET_I0, "T": 200, "below_func": "linear", "below_target": 0.40, "above_func": "sqrt",   "above_target": 0.60},
    "STRAWBERRY": {"base": 120, "I0": MARKET_I0, "T": 100, "below_func": "sqrt",   "below_target": 0.70, "above_func": "linear", "above_target": 0.40},
    "MELON":      {"base": 250, "I0": MARKET_I0, "T": 300, "below_func": "log",    "below_target": 0.20, "above_func": "sq",     "above_target": 0.90},
    "EGG":        {"base":  50, "I0": MARKET_I0, "T": 332, "below_func": "linear", "below_target": 0.40, "above_func": "log",    "above_target": 0.20},
    "MILK":       {"base": 160, "I0": MARKET_I0, "T": 122, "below_func": "sqrt",   "below_target": 0.60, "above_func": "linear", "above_target": 0.40},
    "WOOL":       {"base": 200, "I0": MARKET_I0, "T": 105, "below_func": "log",    "below_target": 0.20, "above_func": "sq",     "above_target": 0.80},
    "FERTILIZER": {"base": 100, "I0": MARKET_I0, "T": 200, "below_func": "linear", "below_target": 0.40, "above_func": "linear", "above_target": 0.40},
}

LAND_PRICES = [1000, 2000, 4000]


def _shape(func, x):
    x = max(0.0, float(x))
    if func == "linear": return x
    if func == "sq":     return x * x
    if func == "sqrt":   return math.sqrt(x)
    if func == "log":    return math.log(1.0 + x)
    if func == "log10":  return math.log10(1.0 + x)
    return x


def compute_market_price(item, inventory):
    p = MARKET_PARAMS[item]
    base = p["base"]
    I0 = p["I0"]
    T = p["T"]
    if inventory < I0:
        f = p["below_func"]
        amp = p["below_target"] * base / _shape(f, T)
        price = base + amp * _shape(f, I0 - inventory)
    else:
        f = p["above_func"]
        amp = p["above_target"] * base / _shape(f, T)
        price = base - amp * _shape(f, inventory - I0)
    return max(PRICE_FLOOR, int(round(price)))


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
    if start == target:
        return "PASS"
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


class Hybrid6C3S10MAgent:
    def __init__(self, target_cows=6, target_sheep=3, target_geese=0, target_melons=12, cycle2_melons=0, sell_batch=14, use_fert=False, care_animals=True, town_sync=True):
        self.target_cows = target_cows
        self.target_sheep = target_sheep
        self.target_geese = target_geese
        self.target_melons = target_melons
        self.cycle2_melons = cycle2_melons
        self.sell_batch_size = sell_batch
        self.use_fert_on_crops = use_fert
        self.care_animals = care_animals
        self.town_sync = town_sync

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
            occupied_pastures = 0
            empty_pastures = []
            coop_count = 0
            occupied_coops = 0
            empty_coops = []
            melon_plants = 0
            unfed_animal_tiles = []

            # Scan Farm Tiles
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
                                occupied_coops += 1
                                goose_count += 1
                                if not t.get("fed_today", False):
                                    chores.append({"type": "FEED", "pos": pos, "weight": 90})
                                    unfed_animal_tiles.append(pos)
                                if self.care_animals and not t.get("cared_today", False):
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
                                occupied_pastures += 1
                                a_type = t.get("animal")
                                if a_type == "COW": cow_count += 1
                                elif a_type == "SHEEP": sheep_count += 1
                                if not t.get("fed_today", False):
                                    chores.append({"type": "FEED", "pos": pos, "weight": 92})
                                    unfed_animal_tiles.append(pos)
                                if self.care_animals and not t.get("cared_today", False):
                                    chores.append({"type": "CARE", "pos": pos, "weight": 76})
                                if t.get("fertilizer_available", False):
                                    chores.append({"type": "COLLECT_FERTILIZER", "pos": pos, "weight": 86})
                                if t.get("yield_units", 0) > 0:
                                    chores.append({"type": "HARVEST", "pos": pos, "weight": 100})
                            else:
                                empty_pastures.append(pos)
                        elif kind == "PLANT":
                            crop = t.get("crop")
                            if crop == "MELON": melon_plants += 1
                            age = day - t.get("planted_day", 0)
                            cd = CROPS.get(crop, {})
                            if not t.get("watered_today", False):
                                chores.append({"type": "WATER", "pos": pos, "weight": 82})
                            if self.use_fert_on_crops and t.get("fertilized_until_day", -1) < day and crop == "MELON":
                                chores.append({"type": "FERTILIZE", "pos": pos, "weight": 78})

                            if cd.get("ongoing", False):
                                if age >= cd["first_yield_day"] and t.get("yield_units", 0) > 0:
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

            # Animals in transit / held
            cows_in_transit = shed.get("COW", 0) + sum(inv.get("COW", 0) for inv in inventories)
            sheep_in_transit = shed.get("SHEEP", 0) + sum(inv.get("SHEEP", 0) for inv in inventories)
            geese_in_transit = shed.get("GOOSE", 0) + sum(inv.get("GOOSE", 0) for inv in inventories)
            total_active_animals = cow_count + sheep_count + goose_count + cows_in_transit + sheep_in_transit + geese_in_transit

            # 1. HIRE FARM HANDS at hour 0
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
            if n_unlocked < 2:
                cost = LAND_PRICES[n_unlocked]
                if n_unlocked == 0 and money >= cost + 250:  # NE Land ($1,000)
                    orders.append(["BUY_LAND"])
                    money -= cost
                elif n_unlocked == 1 and money >= cost + 500 and day <= 14:  # SW Land ($2,000)
                    orders.append(["BUY_LAND"])
                    money -= cost

            spendable = max(0.0, money - 25.0)

            # 3. BUY ANIMALS WITH MANDATORY FEED & LIQUIDITY PROTECTION
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

            # 4. WHEAT FEED BUFFER (Guaranteed procurement BEFORE seed spending)
            if total_active_animals > 0 and day <= 28:
                total_wheat_held = shed.get("WHEAT", 0) + sum(inv.get("WHEAT", 0) for inv in inventories)
                feed_buffer_target = total_active_animals * (3 if day <= 5 else 2)
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
                if day <= 12:
                    if self.target_melons > 0:
                        m_rem_target = max(0, self.target_melons - melon_plants - seeds.get("MELON", 0))
                        m_cnt = min(m_rem_target, needed_seeds, int(spendable // 80))
                    else:
                        m_cnt = 0
                    rem = needed_seeds - m_cnt
                    c_cnt = min(rem, int((spendable - m_cnt * 80) // 20))
                    w_cnt = min(rem - c_cnt, int((spendable - m_cnt * 80 - c_cnt * 20) // 10))
                    if m_cnt > 0: orders.append(["BUY_SEED", "MELON", m_cnt])
                    if c_cnt > 0: orders.append(["BUY_SEED", "CARROT", c_cnt])
                    if w_cnt > 0: orders.append(["BUY_SEED", "WHEAT", w_cnt])
                elif day <= 19:
                    if self.cycle2_melons > 0:
                        m_cnt = min(self.cycle2_melons, needed_seeds, int(spendable // 80))
                    else:
                        m_cnt = 0
                    rem = needed_seeds - m_cnt
                    c_cnt = min(int(rem * 0.7), int((spendable - m_cnt * 80) // 20))
                    w_cnt = min(rem - c_cnt, int((spendable - m_cnt * 80 - c_cnt * 20) // 10))
                    if m_cnt > 0: orders.append(["BUY_SEED", "MELON", m_cnt])
                    if c_cnt > 0: orders.append(["BUY_SEED", "CARROT", c_cnt])
                    if w_cnt > 0: orders.append(["BUY_SEED", "WHEAT", w_cnt])
                elif day <= 26:
                    c_cnt = min(int(needed_seeds * 0.8), int(spendable // 20))
                    w_cnt = min(needed_seeds - c_cnt, int((spendable - c_cnt * 20) // 10))
                    if c_cnt > 0: orders.append(["BUY_SEED", "CARROT", c_cnt])
                    if w_cnt > 0: orders.append(["BUY_SEED", "WHEAT", w_cnt])

            # 6. SELLING / LIQUIDATION
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
                    if self.town_sync and (step % 4 == 0):
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

            # Accurate Pastures to Build based on unplaced animals
            unplaced_pasture_animals = cows_in_transit + sheep_in_transit + cows_ordered + sheep_ordered
            total_pastures_target = self.target_cows + self.target_sheep
            pastures_to_build = max(0, min(total_pastures_target - pasture_count, unplaced_pasture_animals - len(empty_pastures)))

            unplaced_geese = geese_in_transit + geese_ordered
            total_coops_target = self.target_geese
            coops_to_build = max(0, min(total_coops_target - coop_count, unplaced_geese - len(empty_coops)))

            if sum(seeds.values()) > 0 and day <= 26:
                for pos in empty_tiles:
                    chores.append({"type": "PLANT", "pos": pos, "weight": 70})

            # Pass 1: Stand-on instant chore
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
                            if pos in unfed_animal_tiles:
                                unfed_animal_tiles.remove(pos)
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
                        if self.care_animals and not t.get("cared_today", False):
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
                        for sc in ["MELON", "STRAWBERRY", "CARROT", "WHEAT", "TOMATO"]:
                            if avail_seeds.get(sc, 0) > 0:
                                actions[w] = ["PLANT", sc]
                                avail_seeds[sc] -= 1
                                unassigned.remove(w)
                                assigned_pos.add(pos)
                                break

            # Pass 2: Shed Interactions (Stand on shed)
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

            # Pass 3: Targeted Spatial Routing
            rem_chores = [c for c in chores if c["pos"] not in assigned_pos]
            claimed_unfed = set()

            for w in list(unassigned):
                w_p = worker_pos[w]
                inv = inventories[w] if w < len(inventories) else {}

                # 1. Animal delivery to empty structure
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

                # 2. Worker carrying Wheat routes directly to an unfed animal
                if inv.get("WHEAT", 0) > 0 and unfed_animal_tiles:
                    avail_unfed = [p for p in unfed_animal_tiles if p not in claimed_unfed]
                    target = min(avail_unfed or unfed_animal_tiles, key=lambda p: manhattan(w_p, p))
                    claimed_unfed.add(target)
                    actions[w] = [get_next_step(w_p, target, tiles)]
                    unassigned.remove(w)
                    continue

                # 3. Worker without Wheat heads to shed if animals are hungry
                if inv.get("WHEAT", 0) == 0 and unfed_animal_tiles and shed.get("WHEAT", 0) > 0:
                    if len(claimed_unfed) < len(unfed_animal_tiles) and unlocked_sheds:
                        actions[w] = [get_next_step(w_p, unlocked_sheds[0], tiles)]
                        unassigned.remove(w)
                        continue

            # Pass 4: General Chores & Fallback Routing
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

_hybrid_instance = Hybrid6C3S10MAgent()

def agent(obs, configuration=None):
    return _hybrid_instance(obs, configuration)
