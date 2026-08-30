"""
=============================================================================
KAGGRICULTURE PRIMARY CHALLENGER: HYBRID 8C4S 15M FEED-INSULATED
=============================================================================
Key Interventions:
1. Homegrown Wheat Feed Buffer (Default 4 Dedicated Tiles):
   - Plants 4 dedicated Wheat plots on Day 0 to generate 16-24 feed units by Day 3-4.
   - Eliminates reliance on store-bought feed during the critical Days 2-8 window.
2. Dynamic Animal Acquisition Gating:
   - Evaluates real-time market Wheat spot price before buying discretionary livestock.
   - If Wheat Spot Price > wheat_price_threshold (default $35) and feed reserve is inadequate,
     discretionary Cow/Sheep expansion is gated until feed stability is restored.
3. Capital Reserve & Melon Compounding Protection:
   - Day-0 capital allocation prioritizes NE Land ($1,000), 15 Melons ($1,200), and 4 Wheat ($40),
     ensuring zero cannibalization of the early compounding engine.
4. Comprehensive Feed Ledger & Telemetry Tracking:
   - Tracks daily feed coverage %, homegrown yields, market purchases, and feed consumption.
5. Complete 4-Pass Spatial Worker Scheduler with Shed Pickup/Placement.
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

def fib_hire_cost(n):
    a, b = 1, 1
    for _ in range(n): a, b = b, a + b
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

class HybridFeedInsulatedAgent:
    def __init__(self, target_cows=8, target_sheep=4, target_melons=15, 
                 homegrown_wheat_tiles=4, wheat_price_threshold=35.0, sell_batch=14, care_animals=True):
        self.target_cows = target_cows
        self.target_sheep = target_sheep
        self.target_geese = 0
        self.target_melons = target_melons
        self.homegrown_wheat_tiles = homegrown_wheat_tiles
        self.wheat_price_threshold = wheat_price_threshold
        self.sell_batch_size = sell_batch
        self.care_animals = care_animals

        # Feed Ledger Telemetry
        self.ledger = []
        self.total_homegrown_wheat_harvested = 0
        self.total_purchased_wheat = 0
        self.total_feed_consumed = 0

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
            wheat_spot_price = float(market_prices.get("WHEAT", 25.0))

            orders = []
            chores = []
            empty_tiles = []
            cow_count = 0
            sheep_count = 0
            pasture_count = 0
            occupied_pastures = 0
            empty_pastures = []
            melon_plants = 0
            wheat_plants = 0
            carrot_plants = 0
            unfed_animal_tiles = []

            # 1. Scan Farm Tiles
            for y in range(len(tiles)):
                for x in range(len(tiles[0])):
                    t = tiles[y][x]
                    pos = (x, y)
                    if t is None:
                        empty_tiles.append(pos)
                    elif isinstance(t, dict):
                        kind = t.get("kind")
                        if kind == "WEED":
                            chores.append({"type": "DIG", "pos": pos, "weight": 98})
                        elif kind == "PASTURE":
                            pasture_count += 1
                            if "animal" in t and t.get("animal"):
                                occupied_pastures += 1
                                a_type = t.get("animal")
                                if a_type == "COW": cow_count += 1
                                elif a_type == "SHEEP": sheep_count += 1
                                if not t.get("fed_today", False):
                                    chores.append({"type": "FEED", "pos": pos, "weight": 95})
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
                            elif crop == "WHEAT": wheat_plants += 1
                            elif crop == "CARROT": carrot_plants += 1
                            age = day - t.get("planted_day", 0)
                            cd = CROPS.get(crop, {})
                            if not t.get("watered_today", False):
                                chores.append({"type": "WATER", "pos": pos, "weight": 84})
                            if crop == "MELON":
                                if age >= 10 or t.get("yield_units", 0) >= 6 or (day >= 28 and t.get("yield_units", 0) >= 1):
                                    chores.append({"type": "HARVEST", "pos": pos, "weight": 100})
                            elif crop == "WHEAT":
                                if age >= 3 or t.get("yield_units", 0) >= 4 or (day >= 28 and t.get("yield_units", 0) >= 1):
                                    chores.append({"type": "HARVEST", "pos": pos, "weight": 98})
                            elif crop == "CARROT":
                                if age >= 3 or t.get("yield_units", 0) >= 3 or (day >= 28 and t.get("yield_units", 0) >= 1):
                                    chores.append({"type": "HARVEST", "pos": pos, "weight": 100})
                            elif age >= cd.get("max_yield_day", 4) and t.get("yield_units", 0) > 0:
                                chores.append({"type": "HARVEST", "pos": pos, "weight": 100})

            cows_in_transit = shed.get("COW", 0) + sum(inv.get("COW", 0) for inv in inventories)
            sheep_in_transit = shed.get("SHEEP", 0) + sum(inv.get("SHEEP", 0) for inv in inventories)
            total_active_animals = cow_count + sheep_count + cows_in_transit + sheep_in_transit

            # 2. Labor Hiring at Hour 0
            total_workload = len(chores) + len(empty_tiles)
            if len(unlocked_quads) == 1:
                target_hands = min(3, max(2, (total_workload + 6) // 8))
            elif len(unlocked_quads) == 2:
                target_hands = min(5, max(3, (total_workload + 8) // 9))
            else:
                target_hands = min(6, max(4, (total_workload + 10) // 10))

            if hour == 0 and target_hands > hires_today:
                for _ in range(target_hands - hires_today):
                    cost = fib_hire_cost(hires_today + len([o for o in orders if o[0] == "HIRE"]))
                    if money >= cost + 10:
                        orders.append(["HIRE"])
                        money -= cost

            # 3. Land Purchase
            n_unlocked = len(unlocked_quads) - 1
            if n_unlocked == 0 and money >= 1200:
                orders.append(["BUY_LAND"])
                money -= 1000
            elif n_unlocked == 1 and money >= 2800 and day <= 14:
                orders.append(["BUY_LAND"])
                money -= 2000

            spendable = max(0.0, money - 25.0)

            # 4. Day-0 Protected Seed Procurement (Melon + Dedicated Homegrown Wheat)
            if day <= 1:
                # Dedicated Homegrown Wheat Seeds
                wheat_seeds_needed = max(0, self.homegrown_wheat_tiles - (wheat_plants + seeds.get("WHEAT", 0)))
                if wheat_seeds_needed > 0 and spendable >= 10 and len(orders) < 10:
                    can_buy_w = min(wheat_seeds_needed, int(spendable // 10), 10)
                    if can_buy_w > 0:
                        orders.append(["BUY_SEED", "WHEAT", can_buy_w])
                        spendable -= can_buy_w * 10
                        money -= can_buy_w * 10

                # Early Melon Seeds (Protected Compounding)
                melon_seeds_needed = max(0, self.target_melons - (melon_plants + seeds.get("MELON", 0)))
                if melon_seeds_needed > 0 and spendable >= 80 and len(orders) < 10:
                    can_buy_m = min(melon_seeds_needed, int(spendable // 80), 10)
                    if can_buy_m > 0:
                        orders.append(["BUY_SEED", "MELON", can_buy_m])
                        spendable -= can_buy_m * 80
                        money -= can_buy_m * 80

            # 5. Dynamic Animal Purchases (Feed-Insulated & Capital Gated)
            needed_cows = max(0, self.target_cows - cow_count - cows_in_transit)
            needed_sheep = max(0, self.target_sheep - sheep_count - sheep_in_transit)
            cows_ordered = 0
            sheep_ordered = 0

            # Feed Insulation Gating:
            # If we produce our own wheat, or if shed wheat covers the herd, we are feed-insulated.
            # Only gate expansion if:
            # 1. Market wheat is expensive (> threshold)
            # 2. Shed has < 2 days of feed for the expanded herd
            # 3. AND we do NOT have dedicated homegrown wheat plots growing
            feed_gated = False
            if self.wheat_price_threshold is not None and wheat_spot_price > self.wheat_price_threshold:
                min_feed = (total_active_animals + 1) * 2
                has_homegrown = (wheat_plants >= 2 or seeds.get("WHEAT", 0) >= 2)
                if shed.get("WHEAT", 0) < min_feed and not has_homegrown:
                    feed_gated = True

            # Allow livestock expansion through Day 14 (when melon cash is reinvested)
            if day <= 14 and not feed_gated:
                # Buy Cows first up to target_cows
                if needed_cows > 0 and spendable >= 695 and len(orders) < 10:
                    orders.append(["BUY_ANIMAL", "COW", 1])
                    spendable -= 600
                    money -= 600
                    cows_ordered += 1
                # Buy Sheep up to target_sheep
                if needed_sheep > 0 and spendable >= 595 and len(orders) < 10:
                    orders.append(["BUY_ANIMAL", "SHEEP", 1])
                    spendable -= 500
                    money -= 500
                    sheep_ordered += 1

            total_active_animals += cows_ordered + sheep_ordered

            # 6. Feed Reserve Maintenance
            feed_reserve_target = total_active_animals * (4 if day < 26 else 0)
            wheat_in_shed = shed.get("WHEAT", 0)

            imminent_homegrown = wheat_plants * 4 if (day <= 4 and wheat_plants > 0) else 0
            net_feed_target = max(total_active_animals * 2, feed_reserve_target - imminent_homegrown)

            if wheat_in_shed < net_feed_target and spendable >= 25 and len(orders) < 10:
                deficit = net_feed_target - wheat_in_shed
                max_affordable = int(spendable // max(1, wheat_spot_price))
                to_buy = min(deficit, max_affordable, 15)
                if to_buy > 0:
                    orders.append(["BUY_PRODUCT", "WHEAT", to_buy])
                    spendable -= to_buy * wheat_spot_price
                    money -= to_buy * wheat_spot_price
                    self.total_purchased_wheat += to_buy

            # 7. Secondary Seed Procurement (Carrots & Wheat Rotation)
            if day >= 2 and day <= 24 and (wheat_plants + seeds.get("WHEAT", 0)) < self.homegrown_wheat_tiles and spendable >= 20 and len(orders) < 10:
                w_needed = self.homegrown_wheat_tiles - (wheat_plants + seeds.get("WHEAT", 0))
                can_buy_w = min(w_needed, int(spendable // 10), 6)
                if can_buy_w > 0:
                    orders.append(["BUY_SEED", "WHEAT", can_buy_w])
                    spendable -= can_buy_w * 10
                    money -= can_buy_w * 10

            if day <= 2 and (melon_plants + seeds.get("MELON", 0)) < self.target_melons and spendable >= 80 and len(orders) < 10:
                m_needed = self.target_melons - (melon_plants + seeds.get("MELON", 0))
                can_buy_m = min(m_needed, int(spendable // 80), 8)
                if can_buy_m > 0:
                    orders.append(["BUY_SEED", "MELON", can_buy_m])
                    spendable -= can_buy_m * 80
                    money -= can_buy_m * 80

            if day >= 3 and day <= 26 and (seeds.get("CARROT", 0)) < 8 and spendable >= 40 and len(orders) < 10:
                c_needed = 8 - seeds.get("CARROT", 0)
                can_buy_c = min(c_needed, int(spendable // 20), 6)
                if can_buy_c > 0:
                    orders.append(["BUY_SEED", "CARROT", can_buy_c])
                    spendable -= can_buy_c * 20
                    money -= can_buy_c * 20

            # 8. Modulo-4 Town Liquidation
            if step % 4 == 0 or step >= 680:
                for prod in ["MELON", "WOOL", "MILK", "CARROT", "FERTILIZER"]:
                    qty = shed.get(prod, 0)
                    if qty > 0 and len(orders) < 10:
                        batch = min(qty, self.sell_batch_size if step < 680 else 30)
                        orders.append(["SELL", prod, batch])

                if shed.get("WHEAT", 0) > feed_reserve_target + 8 and day < 26 and len(orders) < 10:
                    surplus = shed["WHEAT"] - (feed_reserve_target + 8)
                    orders.append(["SELL", "WHEAT", min(surplus, 10)])

            # 9. Full 4-Pass Spatial Worker Dispatch
            unplaced_pasture_animals = cows_in_transit + sheep_in_transit + cows_ordered + sheep_ordered
            pastures_to_build = max(0, min(self.target_cows + self.target_sheep - pasture_count, unplaced_pasture_animals - len(empty_pastures)))

            worker_pos = [farmer_pos] + hands
            unassigned = list(range(len(worker_pos)))
            actions = [["PASS"] for _ in range(len(worker_pos))]
            assigned_pos = set()

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
                    elif kind == "PLANT":
                        is_h = any(c["pos"] == pos and c["type"] == "HARVEST" for c in chores)
                        if is_h:
                            actions[w] = ["HARVEST"]
                            if t.get("crop") == "WHEAT":
                                self.total_homegrown_wheat_harvested += t.get("yield_units", 4)
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
                    elif day <= 26:
                        # Prioritize Dedicated Homegrown Wheat planting first, then Melons, then Carrots
                        for sc in ["WHEAT", "MELON", "CARROT"]:
                            if sc == "WHEAT" and wheat_plants >= self.homegrown_wheat_tiles:
                                continue
                            if avail_seeds.get(sc, 0) > 0:
                                actions[w] = ["PLANT", sc]
                                avail_seeds[sc] -= 1
                                if sc == "WHEAT": wheat_plants += 1
                                elif sc == "MELON": melon_plants += 1
                                elif sc == "CARROT": carrot_plants += 1
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

            # Record telemetry at end of each day (hour 23)
            if hour == 23:
                self.ledger.append({
                    "day": day,
                    "active_animals": total_active_animals,
                    "wheat_in_shed": shed.get("WHEAT", 0),
                    "wheat_spot_price": wheat_spot_price,
                    "money": money,
                    "cows": cow_count,
                    "sheep": sheep_count,
                    "wheat_plants": wheat_plants,
                    "melon_plants": melon_plants
                })

            return {
                "farmer": actions[0],
                "hands": actions[1:] if len(actions) > 1 else [],
                "market": orders[:10]
            }
        except Exception:
            return {"farmer": ["PASS"], "hands": [], "market": []}

_challenger_instance = HybridFeedInsulatedAgent()
def agent(obs, configuration=None):
    return _challenger_instance(obs, configuration)
