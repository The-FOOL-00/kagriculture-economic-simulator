"""
=============================================================================
CANDIDATE SLOT 5: APEX SYNTHESIS V2 (VALIDATED CHAMPION)
=============================================================================
- 8 Cows + 4 Sheep Staged Fleet with Rapid Early Melon Opening (15 Melons)
- Lean Just-in-Time Feed Buffer (2-day buffer = 24 wheat vs wasteful 48 wheat)
- Cycle-2 Strategic Melon Reinvestment (6-8 midgame melons on Days 10-12)
- Batch 24 Liquidation Peak with Pre-Town-Consumption Timing
- Emergency Liquidity Override for Close-Game / Feed Critical Protection
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

class ApexSynthesisV2Agent:
    def __init__(
        self,
        target_cows=12,
        target_sheep=4,
        target_geese=0,
        target_melons=15,
        cycle2_melons=8,
        sell_batch=24,
        feed_buffer_days=2,
        emergency_liquidity=True,
        care_animals=True
    ):
        self.target_cows = target_cows
        self.target_sheep = target_sheep
        self.target_geese = target_geese
        self.target_melons = target_melons
        self.cycle2_melons = cycle2_melons
        self.sell_batch_size = sell_batch
        self.feed_buffer_days = feed_buffer_days
        self.emergency_liquidity = emergency_liquidity
        self.care_animals = care_animals

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
                            if crop == "MELON":
                                if age >= 10 or t.get("yield_units", 0) >= 6 or (day >= 28 and t.get("yield_units", 0) >= 1):
                                    chores.append({"type": "HARVEST", "pos": pos, "weight": 100})
                            elif crop == "CARROT":
                                if age >= 3 or t.get("yield_units", 0) >= 3 or (day >= 28 and t.get("yield_units", 0) >= 1):
                                    chores.append({"type": "HARVEST", "pos": pos, "weight": 100})
                            elif crop == "WHEAT":
                                if age >= 4 or t.get("yield_units", 0) >= 4 or (day >= 28 and t.get("yield_units", 0) >= 1):
                                    chores.append({"type": "HARVEST", "pos": pos, "weight": 100})
                            elif age >= cd.get("max_yield_day", 4) and t.get("yield_units", 0) > 0:
                                chores.append({"type": "HARVEST", "pos": pos, "weight": 100})

            cows_in_transit = shed.get("COW", 0) + sum(inv.get("COW", 0) for inv in inventories)
            sheep_in_transit = shed.get("SHEEP", 0) + sum(inv.get("SHEEP", 0) for inv in inventories)
            geese_in_transit = shed.get("GOOSE", 0) + sum(inv.get("GOOSE", 0) for inv in inventories)
            total_active_animals = cow_count + sheep_count + goose_count + cows_in_transit + sheep_in_transit + geese_in_transit

            # 2. Labor Hiring
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

            # 3. Land Purchase
            n_unlocked = len(unlocked_quads) - 1
            if n_unlocked < 2:
                cost = LAND_PRICES[n_unlocked]
                if n_unlocked == 0 and money >= cost + 250:
                    orders.append(["BUY_LAND"])
                    money -= cost
                elif n_unlocked == 1 and money >= cost + 500 and day <= 14:
                    orders.append(["BUY_LAND"])
                    money -= cost

            spendable = max(0.0, money - 25.0)

            # 4. Animal Procurement
            needed_cows = max(0, self.target_cows - cow_count - cows_in_transit)
            needed_sheep = max(0, self.target_sheep - sheep_count - sheep_in_transit)
            cows_ordered = 0
            sheep_ordered = 0

            if day <= 12:
                if needed_cows > 0 and spendable >= 695 and len(orders) < 10:
                    orders.append(["BUY_ANIMAL", "COW", 1])
                    spendable -= 600
                    money -= 600
                    cows_ordered += 1
                if needed_sheep > 0 and spendable >= 595 and len(orders) < 10:
                    orders.append(["BUY_ANIMAL", "SHEEP", 1])
                    spendable -= 500
                    money -= 500
                    sheep_ordered += 1

            total_active_animals += cows_ordered + sheep_ordered

            # 5. Lean Just-in-Time Feed Reserve
            feed_reserve_target = total_active_animals * (self.feed_buffer_days if day < 26 else 0)
            wheat_in_shed = shed.get("WHEAT", 0)
            if wheat_in_shed < feed_reserve_target and spendable >= 25 and len(orders) < 10:
                wheat_price = market_prices.get("WHEAT", 25)
                deficit = feed_reserve_target - wheat_in_shed
                max_affordable = int(spendable // max(1, wheat_price))
                to_buy = min(deficit, max_affordable, 15)
                if to_buy > 0:
                    orders.append(["BUY_PRODUCT", "WHEAT", to_buy])
                    spendable -= to_buy * wheat_price
                    money -= to_buy * wheat_price

            # 6. Emergency Liquidity Override
            if self.emergency_liquidity:
                feed_critical = (wheat_in_shed < total_active_animals * 1) if total_active_animals > 0 else False
                labor_critical = (hour == 0 and money < 20)
                if (feed_critical or labor_critical) and len(orders) < 10:
                    for prod in ["MELON", "WOOL", "MILK", "CARROT", "FERTILIZER"]:
                        qty = shed.get(prod, 0)
                        if qty > 0 and len(orders) < 10:
                            orders.append(["SELL", prod, min(qty, 10)])
                            break

            # 7. Seed Purchasing
            if day <= 2 and (melon_plants + seeds.get("MELON", 0)) < self.target_melons and spendable >= 80 and len(orders) < 10:
                needed = self.target_melons - (melon_plants + seeds.get("MELON", 0))
                can_buy = min(needed, int(spendable // 80), 8)
                if can_buy > 0:
                    orders.append(["BUY_SEED", "MELON", can_buy])
                    spendable -= can_buy * 80
                    money -= can_buy * 80

            # Wave 2: Cycle-2 Midgame Melons on Days 10-13
            if 10 <= day <= 13 and (melon_plants + seeds.get("MELON", 0)) < (self.target_melons + self.cycle2_melons) and spendable >= 200 and len(orders) < 10:
                needed = (self.target_melons + self.cycle2_melons) - (melon_plants + seeds.get("MELON", 0))
                can_buy = min(needed, int(spendable // 80), 6)
                if can_buy > 0:
                    orders.append(["BUY_SEED", "MELON", can_buy])
                    spendable -= can_buy * 80
                    money -= can_buy * 80

            # Rapid Secondary Carrots
            if day >= 3 and day <= 26 and (seeds.get("CARROT", 0)) < 8 and spendable >= 40 and len(orders) < 10:
                needed = 8 - seeds.get("CARROT", 0)
                can_buy = min(needed, int(spendable // 20), 6)
                if can_buy > 0:
                    orders.append(["BUY_SEED", "CARROT", can_buy])
                    spendable -= can_buy * 20
                    money -= can_buy * 20

            # 8. Liquidation Market Execution (Batch 24 Peak)
            if step % 4 == 0 or step >= 680:
                for prod in ["MELON", "WOOL", "MILK", "CARROT", "FERTILIZER"]:
                    qty = shed.get(prod, 0)
                    if qty > 0 and len(orders) < 10:
                        batch = min(qty, self.sell_batch_size if step < 680 else 30)
                        orders.append(["SELL", prod, batch])

            # 9. 4-Pass Worker Dispatch
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
                        for sc in ["MELON", "CARROT", "WHEAT"]:
                            if avail_seeds.get(sc, 0) > 0:
                                actions[w] = ["PLANT", sc]
                                avail_seeds[sc] -= 1
                                unassigned.remove(w)
                                assigned_pos.add(pos)
                                break

            # Pass 2: Shed Interactions
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

                if inv.get("COW", 0) > 0 or inv.get("SHEEP", 0) > 0:
                    if empty_pastures:
                        target = min(empty_pastures, key=lambda p: manhattan(w_p, p))
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

            # Pass 4: Fallback & Chores
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

_agent_instance = ApexSynthesisV2Agent()
def agent(obs, configuration=None):
    return _agent_instance(obs, configuration)
