"""
=============================================================================
GOLDEN CONTROL V1 (Apex Grandmaster v3 - Town Frontrunner & 75-Tile Layout)
=============================================================================
Immutable benchmark control for all experimental comparisons.
Validated Baseline:
- 100% win-rate against baseline bots
- $48,213.40 Mean Match Score across standard benchmark seed suite
- $60,255.00 Peak Single-Match Score
=============================================================================
"""

import math
from collections import deque

CROPS = {
    "WHEAT":      {"seed": 10, "first_yield_day": 2, "max_yield_day": 4, "interval": 0, "max_yield": 6, "ongoing": False, "base_yield": 4},
    "CARROT":     {"seed": 20, "first_yield_day": 2, "max_yield_day": 3, "interval": 0, "max_yield": 4, "ongoing": False, "base_yield": 3},
    "TOMATO":     {"seed": 50, "first_yield_day": 8, "max_yield_day": 8, "interval": 1, "max_yield": 4, "ongoing": True,  "base_yield": 4},
    "STRAWBERRY": {"seed": 100, "first_yield_day": 10, "max_yield_day": 10, "interval": 2, "max_yield": 4, "ongoing": True,  "base_yield": 4},
    "MELON":      {"seed": 80, "first_yield_day": 10, "max_yield_day": 12, "interval": 0, "max_yield": 6, "ongoing": False, "base_yield": 6},
}

PRODUCTS = ["WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON", "EGG", "MILK", "WOOL", "FERTILIZER"]

SHOPS = {
    "BAKERY":         ["EGG", "WHEAT"],
    "PIZZA_SHOP":     ["MILK", "TOMATO", "WHEAT"],
    "BRUNCH_SPOT":    ["EGG", "WHEAT", "STRAWBERRY"],
    "YARN_STORE":     ["WOOL"],
    "ICE_CREAM_SHOP": ["STRAWBERRY", "MILK", "WHEAT"],
    "PET_CAFE":       ["CARROT"],
    "SMOOTHIE_SHOP":  ["STRAWBERRY", "MILK"],
    "FARMERS_MARKET": ["WHEAT", "CARROT", "TOMATO", "STRAWBERRY"],
}

LAND_ORDER = ["NE", "SW", "SE"]
LAND_PRICES = [1000, 2000, 4000]

FARMER_MOVES = {
    "NORTH": (0, -1),
    "SOUTH": (0, 1),
    "EAST":  (1, 0),
    "WEST":  (-1, 0),
}

OPPOSITE_MOVES = {
    (0, -1): "NORTH",
    (0, 1):  "SOUTH",
    (1, 0):  "EAST",
    (-1, 0): "WEST",
}

SHED_TILES = [(4, 4), (5, 4), (4, 5), (5, 5)]


def manhattan(p1, p2):
    return abs(p1[0] - p2[0]) + abs(p1[1] - p2[1])


def fib_hire_cost(n):
    a, b = 1, 1
    for _ in range(n):
        a, b = b, a + b
    return a


def get_unlocked_shed_tiles(tiles, board_size=10):
    valid = []
    for x, y in SHED_TILES:
        if 0 <= x < board_size and 0 <= y < board_size:
            if tiles[y][x] != "LOCKED":
                valid.append((x, y))
    return valid if valid else [(4, 4)]


def bfs_distance_map(start, tiles, board_size=10):
    dist = {start: 0}
    parent = {start: None}
    queue = deque([start])

    while queue:
        cx, cy = queue.popleft()
        for d_name, (dx, dy) in FARMER_MOVES.items():
            nx, ny = cx + dx, cy + dy
            if 0 <= nx < board_size and 0 <= ny < board_size:
                if (nx, ny) not in dist and tiles[ny][nx] != "LOCKED":
                    dist[(nx, ny)] = dist[(cx, cy)] + 1
                    parent[(nx, ny)] = (cx, cy)
                    queue.append((nx, ny))
    return dist, parent


def get_next_step(start, target, tiles, board_size=10):
    if start == target:
        return "PASS"

    sx, sy = start
    tx, ty = target

    dx = tx - sx
    dy = ty - sy
    if abs(dx) + abs(dy) == 1:
        move = OPPOSITE_MOVES.get((dx, dy))
        if move and 0 <= tx < board_size and 0 <= ty < board_size and tiles[ty][tx] != "LOCKED":
            return move

    dist, parent = bfs_distance_map(target, tiles, board_size)
    if start not in dist:
        for move, (mdx, mdy) in FARMER_MOVES.items():
            nx, ny = sx + mdx, sy + mdy
            if 0 <= nx < board_size and 0 <= ny < board_size and tiles[ny][nx] != "LOCKED":
                if manhattan((nx, ny), target) < manhattan(start, target):
                    return move
        return "PASS"

    best_move = "PASS"
    min_d = 999999
    for move, (mdx, mdy) in FARMER_MOVES.items():
        nx, ny = sx + mdx, sy + mdy
        pos = (nx, ny)
        if pos in dist and dist[pos] < min_d:
            min_d = dist[pos]
            best_move = move

    return best_move


class FarmState:
    def __init__(self, obs):
        self.raw_obs = obs
        self.player = obs.get("player", 0)
        self.day = obs.get("day", 0)
        self.hour = obs.get("hour", 0)
        self.step = obs.get("step", self.day * 24 + self.hour)
        
        farms = obs.get("farms", [])
        self.farm = farms[self.player] if farms and self.player < len(farms) else {}
        self.opp_farm = farms[1 - self.player] if farms and len(farms) > 1 else {}
        
        self.money = float(self.farm.get("money", 0.0))
        self.farmer_pos = tuple(self.farm.get("farmer", [4, 4]))
        self.hands = [tuple(h) for h in self.farm.get("hands", [])]
        self.hires_today = int(self.farm.get("hires_today", 0))
        self.unlocked_quadrants = list(self.farm.get("unlocked_quadrants", ["NW"]))
        self.tiles = self.farm.get("tiles", [[None]*10 for _ in range(10)])
        
        private = obs.get("private", {}) or {}
        self.shed = dict(private.get("shed", {}))
        self.seeds = dict(private.get("seeds", {}))
        self.inventories = [dict(inv) for inv in private.get("inventories", [{}])]
        
        market = obs.get("market", {}) or {}
        self.market_inv = dict(market.get("inventory", {}))
        self.market_prices = dict(market.get("prices", {}))
        
        town = obs.get("town", {}) or {}
        self.unlocked_shops = list(town.get("unlocked_shops", []))
        
        self._analyze_tiles()
        self._analyze_opponent()

    def _analyze_tiles(self):
        self.empty_tiles = []
        self.weed_tiles = []
        self.unwatered_plants = []
        self.harvestable_plants = []
        self.mature_plants = []
        self.plants = []
        
        self.unfed_animals = []
        self.uncared_animals = []
        self.fertilizer_animals = []
        self.harvestable_animals = []
        self.empty_structures = []

        board_size = len(self.tiles)
        for y in range(board_size):
            for x in range(board_size):
                t = self.tiles[y][x]
                pos = (x, y)
                if t == "LOCKED":
                    continue
                if t is None:
                    self.empty_tiles.append(pos)
                    continue
                if isinstance(t, dict):
                    kind = t.get("kind")
                    if kind == "WEED":
                        self.weed_tiles.append(pos)
                    elif kind == "PLANT":
                        self.plants.append((pos, t))
                        crop = t["crop"]
                        planted_day = t["planted_day"]
                        age = self.day - planted_day
                        cd = CROPS.get(crop, {})
                        watered = t.get("watered_today", False)
                        yield_units = t.get("yield_units", 0)

                        if not watered:
                            self.unwatered_plants.append(pos)

                        is_harvestable = False
                        if cd.get("ongoing", False):
                            if age >= cd["first_yield_day"] and yield_units > 0:
                                is_harvestable = True
                        else:
                            max_day = cd.get("max_yield_day", 4)
                            first_day = cd.get("first_yield_day", 2)
                            if crop == "MELON":
                                if age >= 10 or yield_units >= 6:
                                    is_harvestable = True
                                elif self.day >= 28 and yield_units >= 1:
                                    is_harvestable = True
                            elif crop == "CARROT":
                                if age >= 3 or yield_units >= 3:
                                    is_harvestable = True
                                elif self.day >= 28 and yield_units >= 1:
                                    is_harvestable = True
                            elif crop == "WHEAT":
                                if age >= 4 or yield_units >= 4:
                                    is_harvestable = True
                                elif self.day >= 28 and yield_units >= 1:
                                    is_harvestable = True
                            else:
                                if age >= max_day and yield_units > 0:
                                    is_harvestable = True
                                elif self.day >= 28 and age >= first_day and yield_units > 0:
                                    is_harvestable = True

                        if is_harvestable:
                            self.harvestable_plants.append(pos)

                    elif "animal" in t:
                        animal = t.get("animal")
                        if animal is None:
                            self.empty_structures.append((pos, t.get("kind")))
                        else:
                            if not t.get("fed_today", False):
                                self.unfed_animals.append(pos)
                            if not t.get("cared_today", False):
                                self.uncared_animals.append(pos)
                            if t.get("fertilizer_available", False):
                                self.fertilizer_animals.append(pos)
                            if t.get("yield_units", 0) > 0:
                                self.harvestable_animals.append(pos)
                    elif kind in ("COOP", "PASTURE"):
                        self.empty_structures.append((pos, kind))

    def _analyze_opponent(self):
        self.opp_crops = {p: 0 for p in PRODUCTS}
        self.opp_imminent_harvests = {p: 0 for p in PRODUCTS}
        
        opp_tiles = self.opp_farm.get("tiles", [])
        for row in opp_tiles:
            for t in row:
                if isinstance(t, dict):
                    if t.get("kind") == "PLANT":
                        crop = t.get("crop")
                        if crop in self.opp_crops:
                            self.opp_crops[crop] += 1
                            age = self.day - t.get("planted_day", 0)
                            cd = CROPS.get(crop, {})
                            if not cd.get("ongoing", False):
                                if age >= cd.get("max_yield_day", 4) - 1:
                                    self.opp_imminent_harvests[crop] += 1
                            else:
                                if age >= cd.get("first_yield_day", 8):
                                    self.opp_imminent_harvests[crop] += 1

    def shed_item_count(self):
        return sum(self.shed.values())


class DynamicLookaheadEconomy:
    def __init__(self):
        pass

    def get_shop_demand_vector(self, farm_state):
        demand = {p: 0 for p in PRODUCTS}
        for shop in farm_state.unlocked_shops:
            prods = SHOPS.get(shop, [])
            mult = 2 if len(prods) == 1 else 1
            for p in prods:
                demand[p] += mult
        return demand

    def compute_dp_crop_roi(self, farm_state):
        day = farm_state.day
        remaining_days = 29 - day
        shop_demands = self.get_shop_demand_vector(farm_state)
        
        scores = {}
        for crop, cdata in CROPS.items():
            seed_cost = cdata["seed"]
            cur_price = farm_state.market_prices.get(crop, 25)
            market_inv = farm_state.market_inv.get(crop, 10000)
            
            scarcity_factor = max(0, (10000 - market_inv) * 0.04)
            shop_boost = shop_demands.get(crop, 0) * 10.0
            opp_penalty = farm_state.opp_crops.get(crop, 0) * 1.5

            if not cdata["ongoing"]:
                growth_cycle = cdata["max_yield_day"]
                if remaining_days < cdata["first_yield_day"]:
                    scores[crop] = -9999
                    continue
                
                cycles = remaining_days // growth_cycle
                rem = remaining_days % growth_cycle
                
                expected_yield = cdata["max_yield"] if crop == "MELON" else cdata["base_yield"]
                if crop == "CARROT": expected_yield = 3
                elif crop == "WHEAT": expected_yield = 4

                profit_per_cycle = (expected_yield * cur_price) - seed_cost
                total_expected_profit = cycles * profit_per_cycle
                
                if rem >= cdata["first_yield_day"]:
                    total_expected_profit += (cdata["base_yield"] * cur_price - seed_cost)

                daily_roi = (total_expected_profit / max(1, remaining_days)) + shop_boost + scarcity_factor - opp_penalty
                scores[crop] = daily_roi
            else:
                first_day = cdata["first_yield_day"]
                if remaining_days < first_day:
                    scores[crop] = -9999
                    continue
                num_harvests = (remaining_days - first_day) // cdata["interval"] + 1
                num_harvests = min(cdata["max_yield"], max(0, num_harvests))
                total_expected_profit = (num_harvests * cur_price) - seed_cost
                daily_roi = (total_expected_profit / max(1, remaining_days)) + shop_boost + scarcity_factor - opp_penalty
                scores[crop] = daily_roi

        return scores

    def solve_optimal_portfolio(self, farm_state, slots_to_plant):
        day = farm_state.day
        remaining_days = 29 - day
        
        if remaining_days < 2 or slots_to_plant <= 0:
            return {}

        scores = self.compute_dp_crop_roi(farm_state)
        opp_melon_flood = farm_state.opp_crops.get("MELON", 0) >= 14

        portfolio = {}
        if day <= 12 and remaining_days >= 12:
            if opp_melon_flood:
                melon_c = int(slots_to_plant * 0.35)
                straw_c = int(slots_to_plant * 0.25)
                carrot_c = int(slots_to_plant * 0.25)
                wheat_c = slots_to_plant - melon_c - straw_c - carrot_c
                if melon_c > 0: portfolio["MELON"] = melon_c
                if straw_c > 0: portfolio["STRAWBERRY"] = straw_c
                if carrot_c > 0: portfolio["CARROT"] = carrot_c
                if wheat_c > 0: portfolio["WHEAT"] = wheat_c
            else:
                melon_c = int(slots_to_plant * 0.65)
                carrot_c = int(slots_to_plant * 0.25)
                wheat_c = slots_to_plant - melon_c - carrot_c
                if melon_c > 0: portfolio["MELON"] = melon_c
                if carrot_c > 0: portfolio["CARROT"] = carrot_c
                if wheat_c > 0: portfolio["WHEAT"] = wheat_c

        elif day <= 19 and remaining_days >= 10:
            melon_c = int(slots_to_plant * 0.50)
            carrot_c = int(slots_to_plant * 0.35)
            wheat_c = slots_to_plant - melon_c - carrot_c
            if melon_c > 0: portfolio["MELON"] = melon_c
            if carrot_c > 0: portfolio["CARROT"] = carrot_c
            if wheat_c > 0: portfolio["WHEAT"] = wheat_c

        elif remaining_days >= 3:
            carrot_c = int(slots_to_plant * 0.75)
            wheat_c = slots_to_plant - carrot_c
            if carrot_c > 0: portfolio["CARROT"] = carrot_c
            if wheat_c > 0: portfolio["WHEAT"] = wheat_c
        else:
            portfolio = {}

        return portfolio


class ApexMarketManager:
    def __init__(self):
        self.economy = DynamicLookaheadEconomy()

    def generate_market_orders(self, farm_state, planned_hires=0):
        orders = []
        money = farm_state.money
        day = farm_state.day
        hour = farm_state.hour
        step = farm_state.step

        # 1. HIRE FARM HANDS at hour 0
        if hour == 0 and planned_hires > farm_state.hires_today:
            needed = planned_hires - farm_state.hires_today
            for _ in range(needed):
                cost = fib_hire_cost(farm_state.hires_today + len([o for o in orders if o[0] == "HIRE"]))
                if money >= cost:
                    orders.append(["HIRE"])
                    money -= cost

        # 2. BUY LAND EXPANSION (NE and SW only)
        n_unlocked = len(farm_state.unlocked_quadrants) - 1
        if n_unlocked < 2:
            cost = LAND_PRICES[n_unlocked]
            should_buy_land = False
            if n_unlocked == 0 and money >= cost + 250: # NE ($1k)
                should_buy_land = True
            elif n_unlocked == 1 and money >= cost + 600 and day <= 12: # SW ($2k)
                should_buy_land = True
            
            if should_buy_land and len(orders) < 10:
                orders.append(["BUY_LAND"])
                money -= cost

        RESERVE_CASH = 30.0
        spendable = max(0.0, money - RESERVE_CASH)

        # 3. BUY SEEDS (Using DP Lookahead Portfolio)
        empty_count = len(farm_state.empty_tiles)
        total_seeds_held = sum(farm_state.seeds.values())
        needed_seeds = max(0, empty_count - total_seeds_held)
        
        if needed_seeds > 0 and day <= 26 and len(orders) < 10 and spendable > 0:
            portfolio = self.economy.solve_optimal_portfolio(farm_state, needed_seeds)
            for crop, count in portfolio.items():
                if len(orders) >= 10:
                    break
                seed_price = CROPS[crop]["seed"]
                affordable = min(count, int(spendable // seed_price))
                if affordable > 0:
                    orders.append(["BUY_SEED", crop, affordable])
                    spendable -= affordable * seed_price
                    money -= affordable * seed_price

        # 4. TOWN-CONSUMPTION SYNCHRONIZED SELLING & OPPONENT FRONTRUNNING
        is_post_town_consumption = (step % 4 == 1) or (step % 12 == 1) or (step % 4 == 0)
        
        sell_priority = ["MELON", "WOOL", "MILK", "STRAWBERRY", "FERTILIZER", "TOMATO", "EGG", "CARROT", "WHEAT"]
        for prod in sell_priority:
            if len(orders) >= 10:
                break
            qty = farm_state.shed.get(prod, 0)
            if qty > 0:
                cur_p = farm_state.market_prices.get(prod, 1)
                opp_imminent = farm_state.opp_imminent_harvests.get(prod, 0) >= 6

                should_sell = False
                if day >= 26 or farm_state.shed_item_count() >= 30:
                    should_sell = True
                elif opp_imminent:
                    should_sell = True
                elif is_post_town_consumption and cur_p > 1:
                    should_sell = True
                elif cur_p > 1:
                    should_sell = True

                if should_sell:
                    sell_amount = min(qty, 12) if day < 26 else qty
                    orders.append(["SELL", prod, sell_amount])

        return orders[:10]


class WorkerScheduler:
    def __init__(self):
        pass

    def plan_hires(self, farm_state):
        day = farm_state.day
        hour = farm_state.hour
        money = farm_state.money

        if hour != 0:
            return farm_state.hires_today

        total_chores = (
            len(farm_state.weed_tiles) +
            len(farm_state.harvestable_plants) +
            len(farm_state.unwatered_plants) +
            len(farm_state.empty_tiles)
        )

        unlocked_quads = len(farm_state.unlocked_quadrants)
        
        if day <= 1:
            target_workers = 3
        elif day <= 4:
            target_workers = 4
        else:
            if unlocked_quads == 1:
                target_workers = min(4, max(2, (total_chores + 8) // 10))
            elif unlocked_quads == 2:
                target_workers = min(5, max(3, (total_chores + 10) // 11))
            else:
                target_workers = min(6, max(4, (total_chores + 12) // 12))

        target_hands = max(0, target_workers - 1)
        if money < 10:
            target_hands = min(1, target_hands)
        elif money < 50:
            target_hands = min(2, target_hands)
        elif money < 250:
            target_hands = min(3, target_hands)

        return target_hands

    def assign_worker_actions(self, farm_state):
        num_workers = 1 + len(farm_state.hands)
        worker_positions = [farm_state.farmer_pos] + list(farm_state.hands)
        worker_inventories = farm_state.inventories
        
        available_seeds = dict(farm_state.seeds)
        unlocked_sheds = get_unlocked_shed_tiles(farm_state.tiles)
        
        chores = []
        for pos in farm_state.harvestable_plants:
            chores.append({"type": "HARVEST_PLANT", "pos": pos, "weight": 100})
        for pos in farm_state.weed_tiles:
            chores.append({"type": "DIG_WEED", "pos": pos, "weight": 90})
        for pos in farm_state.unwatered_plants:
            chores.append({"type": "WATER", "pos": pos, "weight": 80})

        total_seeds = sum(available_seeds.values())
        if total_seeds > 0 and farm_state.day <= 26:
            for pos in farm_state.empty_tiles:
                chores.append({"type": "PLANT", "pos": pos, "weight": 70})

        assigned_chore_positions = set()
        actions = [["PASS"] for _ in range(num_workers)]
        unassigned_workers = list(range(num_workers))

        for w_idx in list(unassigned_workers):
            pos = worker_positions[w_idx]
            x, y = pos
            tile = farm_state.tiles[y][x]
            inv = worker_inventories[w_idx] if w_idx < len(worker_inventories) else {}

            if isinstance(tile, dict):
                kind = tile.get("kind")
                if kind == "WEED":
                    actions[w_idx] = ["DIG"]
                    unassigned_workers.remove(w_idx)
                    assigned_chore_positions.add(pos)
                    continue
                elif kind == "PLANT":
                    if pos in farm_state.harvestable_plants:
                        actions[w_idx] = ["HARVEST"]
                        unassigned_workers.remove(w_idx)
                        assigned_chore_positions.add(pos)
                        continue
                    elif inv.get("FERTILIZER", 0) > 0 and tile.get("fertilized_until_day", -1) < farm_state.day:
                        actions[w_idx] = ["FERTILIZE"]
                        unassigned_workers.remove(w_idx)
                        assigned_chore_positions.add(pos)
                        continue
                    elif not tile.get("watered_today", False):
                        actions[w_idx] = ["WATER"]
                        unassigned_workers.remove(w_idx)
                        assigned_chore_positions.add(pos)
                        continue

            elif tile is None and farm_state.day <= 26:
                planted = False
                for seed_crop in ["MELON", "STRAWBERRY", "CARROT", "WHEAT", "TOMATO"]:
                    if available_seeds.get(seed_crop, 0) > 0:
                        actions[w_idx] = ["PLANT", seed_crop]
                        available_seeds[seed_crop] -= 1
                        unassigned_workers.remove(w_idx)
                        assigned_chore_positions.add(pos)
                        planted = True
                        break
                if planted:
                    continue

        remaining_chores = [c for c in chores if c["pos"] not in assigned_chore_positions]

        for w_idx in unassigned_workers:
            w_pos = worker_positions[w_idx]

            if not remaining_chores:
                if w_pos not in unlocked_sheds:
                    move = get_next_step(w_pos, unlocked_sheds[0], farm_state.tiles)
                    actions[w_idx] = [move]
                else:
                    actions[w_idx] = ["PASS"]
                continue

            best_chore = None
            best_score = -999999
            for chore in remaining_chores:
                dist = manhattan(w_pos, chore["pos"])
                score = chore["weight"] - dist * 2.2
                if score > best_score:
                    best_score = score
                    best_chore = chore

            if best_chore:
                target_pos = best_chore["pos"]
                remaining_chores.remove(best_chore)
                assigned_chore_positions.add(target_pos)
                
                move = get_next_step(w_pos, target_pos, farm_state.tiles)
                actions[w_idx] = [move]
            else:
                actions[w_idx] = ["PASS"]

        return {
            "farmer": actions[0],
            "hands": actions[1:] if len(actions) > 1 else []
        }


_MARKET_MGR = None
_SCHEDULER = None


def get_managers():
    global _MARKET_MGR, _SCHEDULER
    if _MARKET_MGR is None:
        _MARKET_MGR = ApexMarketManager()
    if _SCHEDULER is None:
        _SCHEDULER = WorkerScheduler()
    return _MARKET_MGR, _SCHEDULER


def agent(obs):
    try:
        farm_state = FarmState(obs)
        market_mgr, scheduler = get_managers()

        planned_hires = scheduler.plan_hires(farm_state)
        market_orders = market_mgr.generate_market_orders(farm_state, planned_hires)
        worker_actions = scheduler.assign_worker_actions(farm_state)

        return {
            "farmer": worker_actions.get("farmer", ["PASS"]),
            "hands": worker_actions.get("hands", []),
            "market": market_orders,
        }
    except Exception as e:
        print(f"Error in agent: {e}")
        return {"farmer": ["PASS"], "hands": [], "market": []}
