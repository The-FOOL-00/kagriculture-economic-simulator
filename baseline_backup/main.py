"""
=============================================================================
Kaggriculture Apex Titan Grandmaster (Production Deployment Agent)
=============================================================================
Autonomous Modular Architecture:
- World Model & Farm Grid Representation
- Dynamic Price & Slippage Market Model
- Town Demand & Scarcity Consumption Forecaster
- Net Present Value (NPV) & Crop ROI Evaluator
- Opponent Farm Radar & Anti-Glut Frontrunner
- Deadline-Aware Spatial Labor Scheduler
- Rolling-Horizon Macro Portfolio Planner
=============================================================================
"""

import math
import copy
from collections import deque


# ======================================================================
# SECTION: config.py
# ======================================================================
"""
Game configuration and market economics formulas for Kaggriculture.
"""


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

TOWN_CENTER_PRODUCTS = [p for p in PRODUCTS if p != "FERTILIZER"]
TOWN_CENTER_DEMAND_SCHEDULE = [(20, 4), (10, 2), (0, 1)]

LAND_ORDER = ["NE", "SW", "SE"]
LAND_PRICES = [1000, 2000, 4000]

FARMER_MOVES = {
    "NORTH": (0, -1),
    "SOUTH": (0, 1),
    "EAST":  (1, 0),
    "WEST":  (-1, 0),
}


def _shape(func, x):
    x = max(0.0, float(x))
    if func == "linear": return x
    if func == "sq":     return x * x
    if func == "sqrt":   return math.sqrt(x)
    if func == "log":    return math.log(1.0 + x)
    if func == "log10":  return math.log10(1.0 + x)
    return x


def compute_market_price(item, inventory, params=None):
    p = (params or MARKET_PARAMS)[item]
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
    """Cumulative or per-hire cost fib(0)=1, fib(1)=1, fib(2)=2, fib(3)=3, fib(4)=5..."""
    a, b = 1, 1
    for _ in range(n):
        a, b = b, a + b
    return a

# ======================================================================
# SECTION: pathfinding.py
# ======================================================================
"""
Fast pathfinding, grid navigation, and movement utilities for Kaggriculture.
"""


OPPOSITE_MOVES = {
    (0, -1): "NORTH",
    (0, 1):  "SOUTH",
    (1, 0):  "EAST",
    (-1, 0): "WEST",
}

SHED_TILES = [(4, 4), (5, 4), (4, 5), (5, 5)]


def manhattan(p1, p2):
    return abs(p1[0] - p2[0]) + abs(p1[1] - p2[1])


def get_unlocked_shed_tiles(tiles, board_size=10):
    """Return shed access tiles that are currently unlocked."""
    valid = []
    for x, y in SHED_TILES:
        if 0 <= x < board_size and 0 <= y < board_size:
            if tiles[y][x] != "LOCKED":
                valid.append((x, y))
    return valid if valid else [(4, 4)]


def bfs_distance_map(start, tiles, board_size=10):
    """
    Compute shortest distances and predecessors from start to all reachable tiles.
    """
    sx, sy = start
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
    """
    Find the single next directional move ("NORTH", "SOUTH", "EAST", "WEST", or "PASS")
    to reach target from start via unlocked tiles.
    """
    if start == target:
        return "PASS"

    sx, sy = start
    tx, ty = target

    # Quick direct check if neighbor
    dx = tx - sx
    dy = ty - sy
    if abs(dx) + abs(dy) == 1:
        move = OPPOSITE_MOVES.get((dx, dy))
        if move and 0 <= tx < board_size and 0 <= ty < board_size and tiles[ty][tx] != "LOCKED":
            return move

    # BFS from target back to start
    dist, parent = bfs_distance_map(target, tiles, board_size)
    if start not in dist:
        # Fallback greedy manhattan step if no path
        for move, (mdx, mdy) in FARMER_MOVES.items():
            nx, ny = sx + mdx, sy + mdy
            if 0 <= nx < board_size and 0 <= ny < board_size and tiles[ny][nx] != "LOCKED":
                if manhattan((nx, ny), target) < manhattan(start, target):
                    return move
        return "PASS"

    # Follow parent from start towards target
    # Since dist is from target, find neighbor of start with minimal distance to target
    best_move = "PASS"
    min_d = 999999
    for move, (mdx, mdy) in FARMER_MOVES.items():
        nx, ny = sx + mdx, sy + mdy
        pos = (nx, ny)
        if pos in dist and dist[pos] < min_d:
            min_d = dist[pos]
            best_move = move

    return best_move

# ======================================================================
# SECTION: engine/world_model.py
# ======================================================================
"""
=============================================================================
ENGINE: WORLD MODEL & TRANSITION SIMULATOR
=============================================================================
Represents complete state of both farms, market, shed, and inventories.
Supports forward state transitions for rolling-horizon planning.
=============================================================================
"""



class TilePlant:
    def __init__(self, crop, planted_day, watered_today=False, yield_units=0, fertilized_until_day=-1):
        self.crop = crop
        self.planted_day = planted_day
        self.watered_today = watered_today
        self.yield_units = yield_units
        self.fertilized_until_day = fertilized_until_day

    def clone(self):
        return TilePlant(
            self.crop,
            self.planted_day,
            self.watered_today,
            self.yield_units,
            self.fertilized_until_day
        )


class TileAnimal:
    def __init__(self, animal_type, placed_day, fed_today=False, cared_today=False, yield_units=0, fertilizer_available=False):
        self.animal_type = animal_type
        self.placed_day = placed_day
        self.fed_today = fed_today
        self.cared_today = cared_today
        self.yield_units = yield_units
        self.fertilizer_available = fertilizer_available

    def clone(self):
        return TileAnimal(
            self.animal_type,
            self.placed_day,
            self.fed_today,
            self.cared_today,
            self.yield_units,
            self.fertilizer_available
        )


class WorldState:
    def __init__(self, obs=None):
        if obs is None:
            return

        self.player = obs.get("player", 0)
        self.day = obs.get("day", 0)
        self.hour = obs.get("hour", 0)
        self.step = obs.get("step", self.day * 24 + self.hour)

        farms = obs.get("farms", [])
        self.farm = farms[self.player] if farms and self.player < len(farms) else {}
        self.opp_farm = farms[1 - self.player] if farms and len(farms) > 1 else {}

        self.money = float(self.farm.get("money", 0.0))
        self.opp_money = float(self.opp_farm.get("money", 0.0))

        self.farmer_pos = tuple(self.farm.get("farmer", [4, 4]))
        self.hands = [tuple(h) for h in self.farm.get("hands", [])]
        self.hires_today = int(self.farm.get("hires_today", 0))
        self.unlocked_quadrants = list(self.farm.get("unlocked_quadrants", ["NW"]))
        self.opp_unlocked_quadrants = list(self.opp_farm.get("unlocked_quadrants", ["NW"]))

        self.tiles = self.farm.get("tiles", [[None]*10 for _ in range(10)])
        self.opp_tiles = self.opp_farm.get("tiles", [[None]*10 for _ in range(10)])

        private = obs.get("private", {}) or {}
        self.shed = dict(private.get("shed", {}))
        self.seeds = dict(private.get("seeds", {}))
        self.inventories = [dict(inv) for inv in private.get("inventories", [{}])]

        market = obs.get("market", {}) or {}
        self.market_inv = dict(market.get("inventory", {}))
        self.market_prices = dict(market.get("prices", {}))

        town = obs.get("town", {}) or {}
        self.unlocked_shops = list(town.get("unlocked_shops", []))

    def clone(self):
        ws = WorldState()
        ws.player = self.player
        ws.day = self.day
        ws.hour = self.hour
        ws.step = self.step
        ws.money = self.money
        ws.opp_money = self.opp_money
        ws.farmer_pos = self.farmer_pos
        ws.hands = list(self.hands)
        ws.hires_today = self.hires_today
        ws.unlocked_quadrants = list(self.unlocked_quadrants)
        ws.opp_unlocked_quadrants = list(self.opp_unlocked_quadrants)
        ws.tiles = copy.deepcopy(self.tiles)
        ws.opp_tiles = copy.deepcopy(self.opp_tiles)
        ws.shed = dict(self.shed)
        ws.seeds = dict(self.seeds)
        ws.inventories = [dict(inv) for inv in self.inventories]
        ws.market_inv = dict(self.market_inv)
        ws.market_prices = dict(self.market_prices)
        ws.unlocked_shops = list(self.unlocked_shops)
        return ws

    def get_unlocked_tile_count(self):
        return len(self.unlocked_quadrants) * 25

    def get_empty_tiles(self):
        empty = []
        for y in range(len(self.tiles)):
            for x in range(len(self.tiles[0])):
                if self.tiles[y][x] is None:
                    empty.append((x, y))
        return empty

    def get_active_plants(self):
        plants = []
        for y in range(len(self.tiles)):
            for x in range(len(self.tiles[0])):
                t = self.tiles[y][x]
                if isinstance(t, dict) and t.get("kind") == "PLANT":
                    plants.append(((x, y), t))
        return plants

    def get_active_animals(self):
        animals = []
        for y in range(len(self.tiles)):
            for x in range(len(self.tiles[0])):
                t = self.tiles[y][x]
                if isinstance(t, dict) and "animal" in t and t.get("animal"):
                    animals.append(((x, y), t))
        return animals

# ======================================================================
# SECTION: engine/market_model.py
# ======================================================================
"""
=============================================================================
ENGINE: MARKET DYNAMICS & PRICE SLIPPAGE MODEL
=============================================================================
Models non-linear price curves, inventory slippage, and optimal batch sizing.
=============================================================================
"""



class MarketModel:
    def __init__(self):
        self.params = MARKET_PARAMS

    def get_spot_price(self, item, inventory):
        return compute_market_price(item, inventory, self.params)

    def simulate_sell_revenue(self, item, starting_inventory, quantity):
        """
        Simulate total revenue from selling `quantity` units sequentially,
        accounting for progressive market price depression as inventory increases.
        """
        if quantity <= 0:
            return 0.0

        total_revenue = 0.0
        cur_inv = starting_inventory
        for _ in range(quantity):
            price = self.get_spot_price(item, cur_inv)
            total_revenue += price
            cur_inv += 1
            
        return total_revenue

    def calculate_price_slippage(self, item, starting_inventory, quantity):
        """
        Calculates the percentage price drop caused by selling `quantity` units.
        """
        if quantity <= 0:
            return 0.0
        p_initial = self.get_spot_price(item, starting_inventory)
        p_final = self.get_spot_price(item, starting_inventory + quantity)
        return max(0.0, (p_initial - p_final) / max(1.0, float(p_initial)))

    def get_optimal_sell_batch(self, item, starting_inventory, available_qty, max_allowed_slippage=0.20):
        """
        Computes the maximum batch quantity to sell without depressing price
        beyond `max_allowed_slippage`.
        """
        if available_qty <= 0:
            return 0

        p_initial = self.get_spot_price(item, starting_inventory)
        best_qty = available_qty

        for q in range(1, available_qty + 1):
            p_curr = self.get_spot_price(item, starting_inventory + q)
            slippage = (p_initial - p_curr) / max(1.0, float(p_initial))
            if slippage > max_allowed_slippage:
                return max(1, q - 1)

        return best_qty

# ======================================================================
# SECTION: engine/town_model.py
# ======================================================================
"""
=============================================================================
ENGINE: TOWN DEMAND & CONSUMPTION TIMING MODEL
=============================================================================
Forecasts periodic town shop consumption ticks and identifies scarcity peaks.
=============================================================================
"""



class TownDemandModel:
    def __init__(self):
        self.shops_def = SHOPS

    def get_shop_demand_weights(self, unlocked_shops):
        """
        Computes the relative demand intensity for each commodity based on active shops.
        """
        weights = {p: 0 for p in PRODUCTS}
        for shop in unlocked_shops:
            prods = self.shops_def.get(shop, [])
            # Single-product shops consume at 2x intensity
            mult = 2 if len(prods) == 1 else 1
            for p in prods:
                weights[p] += mult
        return weights

    def is_post_consumption_window(self, step):
        """
        Checks if the current step immediately follows a shop or town center consumption tick.
        Shop consumption occurs at step % 4 == 0.
        Town center consumption occurs at step % 12 == 0.
        """
        # Step % 4 == 1 or Step % 4 == 0 are peak scarcity arbitrage moments
        return (step % 4 == 0) or (step % 4 == 1) or (step % 12 == 0) or (step % 12 == 1)

    def steps_until_next_consumption(self, step):
        """
        Computes remaining steps until the next market inventory drain.
        """
        return 4 - (step % 4)

# ======================================================================
# SECTION: engine/economic_evaluator.py
# ======================================================================
"""
=============================================================================
ENGINE: DYNAMIC ECONOMIC VALUATION & ASSET EVALUATOR
=============================================================================
Computes exact Net Present Value (NPV), Marginal Expected Return on Capital (ROI),
and Payback Period for all crops, livestock, structures, and land.
=============================================================================
"""



class EconomicEvaluator:
    def __init__(self, market_model, town_model):
        self.market_model = market_model
        self.town_model = town_model

    def evaluate_crop_roi(self, crop, current_day, market_inv, unlocked_shops, opp_crop_count=0):
        """
        Computes expected net profit per tile across remaining season days.
        """
        remaining_days = 29 - current_day
        if remaining_days < 2:
            return -9999.0

        cdata = CROPS[crop]
        seed_cost = cdata["seed"]
        cur_price = self.market_model.get_spot_price(crop, market_inv.get(crop, 10000))
        shop_weights = self.town_model.get_shop_demand_weights(unlocked_shops)
        
        shop_boost = shop_weights.get(crop, 0) * 8.0
        opp_penalty = opp_crop_count * 1.5
        scarcity_factor = max(0.0, (10000 - market_inv.get(crop, 10000)) * 0.03)

        if not cdata["ongoing"]:
            growth_days = cdata["max_yield_day"]
            if remaining_days < cdata["first_yield_day"]:
                return -9999.0

            cycles = remaining_days // growth_days
            rem_days = remaining_days % growth_days

            expected_units = cdata["max_yield"] if crop == "MELON" else cdata["base_yield"]
            if crop == "CARROT": expected_units = 3
            elif crop == "WHEAT": expected_units = 4

            cycle_revenue = self.market_model.simulate_sell_revenue(crop, market_inv.get(crop, 10000), expected_units)
            total_net_profit = cycles * (cycle_revenue - seed_cost)

            if rem_days >= cdata["first_yield_day"]:
                rem_units = cdata["base_yield"]
                rem_rev = self.market_model.simulate_sell_revenue(crop, market_inv.get(crop, 10000), rem_units)
                total_net_profit += (rem_rev - seed_cost)

            daily_roi = (total_net_profit / max(1.0, float(remaining_days))) + shop_boost + scarcity_factor - opp_penalty
            return daily_roi

        else:
            first_day = cdata["first_yield_day"]
            if remaining_days < first_day:
                return -9999.0

            num_harvests = (remaining_days - first_day) // cdata["interval"] + 1
            units_per_harvest = cdata["base_yield"]
            total_units = num_harvests * units_per_harvest

            total_revenue = self.market_model.simulate_sell_revenue(crop, market_inv.get(crop, 10000), total_units)
            total_net_profit = total_revenue - seed_cost

            daily_roi = (total_net_profit / max(1.0, float(remaining_days))) + shop_boost + scarcity_factor - opp_penalty
            return daily_roi

    def evaluate_animal_npv(self, animal, current_day, market_inv, unlocked_shops):
        """
        Computes expected net lifetime cash contribution for purchasing an animal on current_day.
        """
        adata = ANIMALS[animal]
        cost = adata["cost"]
        prod = adata["product"]
        remaining_days = 29 - current_day
        
        if remaining_days < adata["first_yield_day"]:
            return -cost

        num_harvests = (remaining_days - adata["first_yield_day"]) // adata["interval"] + 1
        units_per_harvest = adata["max_held"]
        total_prod_units = num_harvests * units_per_harvest

        product_rev = self.market_model.simulate_sell_revenue(prod, market_inv.get(prod, 10000), total_prod_units)
        
        # Fertilizer cash value (1 per day from placement)
        fert_units = remaining_days
        fert_rev = self.market_model.simulate_sell_revenue("FERTILIZER", market_inv.get("FERTILIZER", 10000), fert_units)

        # Feed cost: 1 wheat per day ($30 store cost, or $10 if homegrown)
        feed_cost = remaining_days * 25.0
        
        net_npv = product_rev + fert_rev - feed_cost - cost
        return net_npv

    def evaluate_land_expansion(self, current_quadrants_count, current_money, current_day, expected_daily_tile_profit):
        """
        Evaluates whether buying the next land quadrant is economically positive.
        """
        n_unlocked = current_quadrants_count - 1
        if n_unlocked >= len(LAND_PRICES):
            return False

        cost = LAND_PRICES[n_unlocked]
        remaining_days = 29 - current_day

        # 25 new tiles
        potential_gross_profit = 25 * expected_daily_tile_profit * remaining_days
        
        # Payback condition: profit must exceed cost by at least 50% buffer and preserve liquidity
        if potential_gross_profit > cost * 1.5 and current_money >= cost + 250:
            return True

        return False

# ======================================================================
# SECTION: engine/opponent_model.py
# ======================================================================
"""
=============================================================================
ENGINE: OPPONENT RADAR & HARVEST PREDICTOR
=============================================================================
Scans opponent farm state, predicts harvest timings, classifies strategic archetypes,
and generates anti-glut frontrunning signals.
=============================================================================
"""



class OpponentModel:
    def __init__(self):
        pass

    def analyze_opponent_farm(self, opp_tiles, current_day):
        """
        Analyzes visible opponent farm tiles and predicts imminent harvests.
        """
        crop_counts = {p: 0 for p in PRODUCTS}
        imminent_harvests = {p: 0 for p in PRODUCTS}
        animal_counts = {"COW": 0, "SHEEP": 0, "GOOSE": 0}

        for row in opp_tiles:
            for t in row:
                if isinstance(t, dict):
                    kind = t.get("kind")
                    if kind == "PLANT":
                        crop = t.get("crop")
                        if crop in crop_counts:
                            crop_counts[crop] += 1
                            planted = t.get("planted_day", 0)
                            age = current_day - planted
                            cdata = CROPS.get(crop, {})
                            
                            if not cdata.get("ongoing", False):
                                max_d = cdata.get("max_yield_day", 4)
                                # Flag imminent harvest if within 1 day of max yield
                                if age >= max_d - 1:
                                    imminent_harvests[crop] += 1
                            else:
                                first_d = cdata.get("first_yield_day", 10)
                                if age >= first_d:
                                    imminent_harvests[crop] += 1

                    elif "animal" in t and t.get("animal"):
                        animal = t.get("animal")
                        if animal in animal_counts:
                            animal_counts[animal] += 1
                            if animal == "COW": crop_counts["MILK"] += 1
                            elif animal == "SHEEP": crop_counts["WOOL"] += 1
                            elif animal == "GOOSE": crop_counts["EGG"] += 1

        # Classify archetype
        total_crops = sum(crop_counts[c] for c in ["MELON", "STRAWBERRY", "TOMATO", "CARROT", "WHEAT"])
        total_animals = sum(animal_counts.values())

        if total_animals >= 2:
            archetype = "LIVESTOCK_HYBRID"
        elif crop_counts["STRAWBERRY"] >= 15:
            archetype = "STRAWBERRY_HEAVY"
        elif crop_counts["MELON"] >= 15:
            archetype = "MELON_BURST"
        else:
            archetype = "BALANCED_CROP"

        return {
            "archetype": archetype,
            "crop_counts": crop_counts,
            "animal_counts": animal_counts,
            "imminent_harvests": imminent_harvests
        }

    def should_frontrun_opponent(self, product, imminent_count):
        """
        Determines if we must dump our inventory of `product` immediately
        before the opponent floods the market.
        """
        # If opponent has 6+ units maturing within 1 day, frontrun now!
        return imminent_count >= 6

# ======================================================================
# SECTION: engine/labor_scheduler.py
# ======================================================================
"""
=============================================================================
ENGINE: HIGH-PERFORMANCE UNIFIED LABOR SCHEDULER (KAGGRICULTURE APEX)
=============================================================================
Coordinates the Farmer and hired Farm Hands with deadline-aware prioritization:
1. Animal Care & Feeding (Prevent starvation & maximize care bonuses)
2. Immediate Harvests (Crops & Livestock products)
3. Weed Digging & Daily Watering (Prevent plant decay)
4. Pasture & Coop Construction + Animal Logistics (Pickup from Shed & Placement)
5. Crop Planting & Fertilizer Spreading
6. Optimal Spatial Assignment using Priority-Distance Bipartite Scoring
=============================================================================
"""



class LaborScheduler:
    def __init__(self):
        pass

    def compute_daily_hire_count(self, world_state, pending_chore_count):
        """
        Calculates optimal farm hands to hire for the day at hour 0.
        """
        if world_state.hour != 0:
            return world_state.hires_today

        unlocked_quads = len(world_state.unlocked_quadrants)
        money = world_state.money

        if unlocked_quads == 1:
            target_workers = min(4, max(2, (pending_chore_count + 6) // 8))
        elif unlocked_quads == 2:
            target_workers = min(5, max(3, (pending_chore_count + 8) // 9))
        else:
            target_workers = min(6, max(4, (pending_chore_count + 10) // 10))

        target_hands = max(0, target_workers - 1)

        # Strict liquidity protection
        if money < 15:
            target_hands = 0
        elif money < 50:
            target_hands = min(1, target_hands)
        elif money < 200:
            target_hands = min(2, target_hands)
        elif money < 500:
            target_hands = min(3, target_hands)

        return target_hands

    def assign_worker_actions(self, world_state, chores, structures_to_build=None, care_animals=True, use_fert_on_crops=False):
        """
        Unified spatial worker assignment for all crop and livestock tasks.
        """
        num_workers = 1 + len(world_state.hands)
        worker_positions = [world_state.farmer_pos] + list(world_state.hands)
        worker_inventories = [dict(inv) for inv in world_state.inventories]
        while len(worker_inventories) < num_workers:
            worker_inventories.append({})

        available_seeds = dict(world_state.seeds)
        shed = dict(world_state.shed)
        unlocked_sheds = get_unlocked_shed_tiles(world_state.tiles)

        actions = [["PASS"] for _ in range(num_workers)]
        unassigned_workers = list(range(num_workers))
        assigned_chore_positions = set()

        pastures_to_build = structures_to_build.get("pastures", 0) if structures_to_build else 0
        coops_to_build = structures_to_build.get("coops", 0) if structures_to_build else 0

        # Pass 1: Stand-on chores (Instant execution at current worker tile)
        for w_idx in list(unassigned_workers):
            pos = worker_positions[w_idx]
            x, y = pos
            tile = world_state.tiles[y][x]
            inv = worker_inventories[w_idx]

            if isinstance(tile, dict):
                kind = tile.get("kind")
                if kind == "WEED":
                    actions[w_idx] = ["DIG"]
                    unassigned_workers.remove(w_idx)
                    assigned_chore_positions.add(pos)
                    continue

                elif "animal" in tile:
                    # Livestock Stand-on Chores
                    if not tile.get("fed_today", False) and inv.get("WHEAT", 0) > 0:
                        actions[w_idx] = ["FEED"]
                        inv["WHEAT"] -= 1
                        unassigned_workers.remove(w_idx)
                        assigned_chore_positions.add(pos)
                        continue

                    if tile.get("yield_units", 0) > 0:
                        actions[w_idx] = ["HARVEST"]
                        unassigned_workers.remove(w_idx)
                        assigned_chore_positions.add(pos)
                        continue

                    if tile.get("fertilizer_available", False):
                        actions[w_idx] = ["COLLECT_FERTILIZER"]
                        unassigned_workers.remove(w_idx)
                        assigned_chore_positions.add(pos)
                        continue

                    if care_animals and not tile.get("cared_today", False):
                        actions[w_idx] = ["CARE"]
                        unassigned_workers.remove(w_idx)
                        assigned_chore_positions.add(pos)
                        continue

                elif kind == "PASTURE" and "animal" not in tile:
                    if inv.get("COW", 0) > 0:
                        actions[w_idx] = ["PLACE", "COW"]
                        inv["COW"] -= 1
                        unassigned_workers.remove(w_idx)
                        assigned_chore_positions.add(pos)
                        continue
                    elif inv.get("SHEEP", 0) > 0:
                        actions[w_idx] = ["PLACE", "SHEEP"]
                        inv["SHEEP"] -= 1
                        unassigned_workers.remove(w_idx)
                        assigned_chore_positions.add(pos)
                        continue

                elif kind == "COOP" and "animal" not in tile:
                    if inv.get("GOOSE", 0) > 0:
                        actions[w_idx] = ["PLACE", "GOOSE"]
                        inv["GOOSE"] -= 1
                        unassigned_workers.remove(w_idx)
                        assigned_chore_positions.add(pos)
                        continue

                elif kind == "PLANT":
                    # Crop Harvest
                    pos_harvest = any(c["pos"] == pos and c["type"] == "HARVEST" for c in chores)
                    if pos_harvest:
                        actions[w_idx] = ["HARVEST"]
                        unassigned_workers.remove(w_idx)
                        assigned_chore_positions.add(pos)
                        continue

                    # Crop Water
                    if not tile.get("watered_today", False):
                        actions[w_idx] = ["WATER"]
                        unassigned_workers.remove(w_idx)
                        assigned_chore_positions.add(pos)
                        continue

                    # Fertilizer application on high value crops
                    if use_fert_on_crops and tile.get("crop") == "MELON" and tile.get("fertilized_until_day", -1) < world_state.day and inv.get("FERTILIZER", 0) > 0:
                        actions[w_idx] = ["FERTILIZE"]
                        inv["FERTILIZER"] -= 1
                        unassigned_workers.remove(w_idx)
                        assigned_chore_positions.add(pos)
                        continue

            elif tile is None:
                # Stand-on structure building or planting
                if pastures_to_build > 0:
                    actions[w_idx] = ["BUILD_PASTURE"]
                    pastures_to_build -= 1
                    unassigned_workers.remove(w_idx)
                    assigned_chore_positions.add(pos)
                    continue
                elif coops_to_build > 0:
                    actions[w_idx] = ["BUILD_COOP"]
                    coops_to_build -= 1
                    unassigned_workers.remove(w_idx)
                    assigned_chore_positions.add(pos)
                    continue
                elif world_state.day <= 26:
                    for sc in ["MELON", "STRAWBERRY", "CARROT", "WHEAT", "TOMATO"]:
                        if available_seeds.get(sc, 0) > 0:
                            actions[w_idx] = ["PLANT", sc]
                            available_seeds[sc] -= 1
                            unassigned_workers.remove(w_idx)
                            assigned_chore_positions.add(pos)
                            break

        # Pass 2: Shed Logistics & Spatial Routing
        remaining_chores = [c for c in chores if c["pos"] not in assigned_chore_positions]

        # Check for empty pastures waiting for animals
        empty_pastures = []
        empty_coops = []
        for y in range(len(world_state.tiles)):
            for x in range(len(world_state.tiles[0])):
                t = world_state.tiles[y][x]
                if isinstance(t, dict):
                    if t.get("kind") == "PASTURE" and "animal" not in t:
                        empty_pastures.append((x, y))
                    elif t.get("kind") == "COOP" and "animal" not in t:
                        empty_coops.append((x, y))

        for w_idx in list(unassigned_workers):
            w_pos = worker_positions[w_idx]
            inv = worker_inventories[w_idx]

            # If worker is carrying an animal and there is an empty structure, route to it
            if inv.get("COW", 0) > 0 or inv.get("SHEEP", 0) > 0:
                if empty_pastures:
                    target = min(empty_pastures, key=lambda p: manhattan(w_pos, p))
                    actions[w_idx] = [get_next_step(w_pos, target, world_state.tiles)]
                    unassigned_workers.remove(w_idx)
                    continue
            if inv.get("GOOSE", 0) > 0:
                if empty_coops:
                    target = min(empty_coops, key=lambda p: manhattan(w_pos, p))
                    actions[w_idx] = [get_next_step(w_pos, target, world_state.tiles)]
                    unassigned_workers.remove(w_idx)
                    continue

            # Shed pickup for animals or feed
            if w_pos in unlocked_sheds:
                if shed.get("COW", 0) > 0 and inv.get("COW", 0) == 0 and empty_pastures:
                    actions[w_idx] = ["PICKUP", "COW", 1]
                    shed["COW"] -= 1
                    unassigned_workers.remove(w_idx)
                    continue
                elif shed.get("SHEEP", 0) > 0 and inv.get("SHEEP", 0) == 0 and empty_pastures:
                    actions[w_idx] = ["PICKUP", "SHEEP", 1]
                    shed["SHEEP"] -= 1
                    unassigned_workers.remove(w_idx)
                    continue
                elif shed.get("GOOSE", 0) > 0 and inv.get("GOOSE", 0) == 0 and empty_coops:
                    actions[w_idx] = ["PICKUP", "GOOSE", 1]
                    shed["GOOSE"] -= 1
                    unassigned_workers.remove(w_idx)
                    continue
                elif shed.get("WHEAT", 0) > 0 and inv.get("WHEAT", 0) == 0:
                    # Pick up feed for livestock
                    feed_take = min(4, shed["WHEAT"])
                    actions[w_idx] = ["PICKUP", "WHEAT", feed_take]
                    shed["WHEAT"] -= feed_take
                    unassigned_workers.remove(w_idx)
                    continue

        # Pass 3: Route remaining workers to nearest high-priority chore
        for w_idx in unassigned_workers:
            w_pos = worker_positions[w_idx]

            if remaining_chores:
                best_chore = None
                best_score = -999999.0
                for chore in remaining_chores:
                    dist = manhattan(w_pos, chore["pos"])
                    score = chore["weight"] - dist * 2.0
                    if score > best_score:
                        best_score = score
                        best_chore = chore

                if best_chore:
                    target_pos = best_chore["pos"]
                    remaining_chores.remove(best_chore)
                    assigned_chore_positions.add(target_pos)
                    actions[w_idx] = [get_next_step(w_pos, target_pos, world_state.tiles)]
                    continue

            # Default: head to shed if away, else pass
            if w_pos not in unlocked_sheds and unlocked_sheds:
                actions[w_idx] = [get_next_step(w_pos, unlocked_sheds[0], world_state.tiles)]
            else:
                actions[w_idx] = ["PASS"]

        return {
            "farmer": actions[0],
            "hands": actions[1:] if len(actions) > 1 else []
        }

# ======================================================================
# SECTION: engine/macro_planner.py
# ======================================================================
"""
=============================================================================
ENGINE: MACRO PORTFOLIO PLANNER & ARBITRAGE EXECUTOR (TITAN APEX V4)
=============================================================================
High-Throughput Harvest Liquidation Pipeline & Dynamic Arbitrage Engine.
Eliminates inventory logjams and maximizes realized harvest cash flow.
=============================================================================
"""



class MacroPlanner:
    def __init__(self):
        self.market_model = MarketModel()
        self.town_model = TownDemandModel()
        self.evaluator = EconomicEvaluator(self.market_model, self.town_model)
        self.opponent_model = OpponentModel()
        self.labor_scheduler = LaborScheduler()

    def plan_turn(self, world_state):
        day = world_state.day
        hour = world_state.hour
        step = world_state.step
        money = world_state.money

        # 1. Opponent Radar & Supply Monitoring
        opp_analysis = self.opponent_model.analyze_opponent_farm(world_state.opp_tiles, day)
        opp_imminent = opp_analysis["imminent_harvests"]
        opp_crops = opp_analysis["crop_counts"]

        # 2. Extract Chores & Labor Needs
        chores = []
        weed_count = 0
        unwatered_count = 0
        harvestable_count = 0

        board_size = len(world_state.tiles)
        for y in range(board_size):
            for x in range(board_size):
                t = world_state.tiles[y][x]
                pos = (x, y)
                if t is None or t == "LOCKED":
                    continue
                if isinstance(t, dict):
                    kind = t.get("kind")
                    if kind == "WEED":
                        chores.append({"type": "DIG", "pos": pos, "weight": 92})
                        weed_count += 1
                    elif kind == "PLANT":
                        crop = t["crop"]
                        age = day - t.get("planted_day", 0)
                        cd = CROPS.get(crop, {})
                        watered = t.get("watered_today", False)
                        yield_units = t.get("yield_units", 0)

                        if not watered:
                            chores.append({"type": "WATER", "pos": pos, "weight": 82})
                            unwatered_count += 1

                        is_harvest = False
                        if cd.get("ongoing", False):
                            if age >= cd["first_yield_day"] and yield_units > 0:
                                is_harvest = True
                        else:
                            if crop == "MELON":
                                if age >= 10 or yield_units >= 6 or (day >= 28 and yield_units >= 1):
                                    is_harvest = True
                            elif crop == "CARROT":
                                if age >= 3 or yield_units >= 3 or (day >= 28 and yield_units >= 1):
                                    is_harvest = True
                            elif crop == "WHEAT":
                                if age >= 4 or yield_units >= 4 or (day >= 28 and yield_units >= 1):
                                    is_harvest = True
                            else:
                                if age >= cd.get("max_yield_day", 4) and yield_units > 0:
                                    is_harvest = True

                        if is_harvest:
                            chores.append({"type": "HARVEST", "pos": pos, "weight": 100})
                            harvestable_count += 1

        empty_tiles = world_state.get_empty_tiles()
        total_seeds_held = sum(world_state.seeds.values())
        if total_seeds_held > 0 and day <= 26:
            for pos in empty_tiles:
                chores.append({"type": "PLANT", "pos": pos, "weight": 70})

        total_pending_chores = weed_count + unwatered_count + harvestable_count + len(empty_tiles)

        # 3. Plan Daily Labor Fleet
        planned_hires = self.labor_scheduler.compute_daily_hire_count(world_state, total_pending_chores)

        # 4. Generate Market Orders
        orders = []

        # A. HIRE FARM HANDS at hour 0 (Priority 1)
        if hour == 0 and planned_hires > world_state.hires_today:
            needed = planned_hires - world_state.hires_today
            for _ in range(needed):
                cost = fib_hire_cost(world_state.hires_today + len([o for o in orders if o[0] == "HIRE"]))
                if money >= cost:
                    orders.append(["HIRE"])
                    money -= cost

        # B. DAY-0 50-TILE EXPANSION & SW SCALING
        n_unlocked = len(world_state.unlocked_quadrants) - 1
        if n_unlocked < 2:
            cost = LAND_PRICES[n_unlocked]
            should_buy_land = False
            if n_unlocked == 0 and money >= cost + 250: # NE Land ($1,000)
                should_buy_land = True
            elif n_unlocked == 1 and money >= cost + 500 and day <= 13: # SW Land ($2,000)
                should_buy_land = True
            
            if should_buy_land and len(orders) < 10:
                orders.append(["BUY_LAND"])
                money -= cost

        # Labor Liquidity Protection ($30 reserve)
        RESERVE_CASH = 30.0
        spendable = max(0.0, money - RESERVE_CASH)

        # C. ADAPTIVE CROP PORTFOLIO EVALUATOR
        needed_seeds = max(0, len(empty_tiles) - total_seeds_held)

        if needed_seeds > 0 and day <= 26 and len(orders) < 10 and spendable > 0:
            remaining_days = 29 - day
            opp_melon_flood = opp_crops.get("MELON", 0) >= 16

            portfolio = {}
            if day <= 12 and remaining_days >= 12:
                # Early Season: High-yield Melon Compounding (Proven 65% Melon baseline)
                if opp_melon_flood:
                    melon_c = int(needed_seeds * 0.45)
                    straw_c = int(needed_seeds * 0.25)
                    carrot_c = int(needed_seeds * 0.20)
                    wheat_c = needed_seeds - melon_c - straw_c - carrot_c
                    if melon_c > 0: portfolio["MELON"] = melon_c
                    if straw_c > 0: portfolio["STRAWBERRY"] = straw_c
                    if carrot_c > 0: portfolio["CARROT"] = carrot_c
                    if wheat_c > 0: portfolio["WHEAT"] = wheat_c
                else:
                    melon_c = int(needed_seeds * 0.65)
                    carrot_c = int(needed_seeds * 0.25)
                    wheat_c = needed_seeds - melon_c - carrot_c
                    if melon_c > 0: portfolio["MELON"] = melon_c
                    if carrot_c > 0: portfolio["CARROT"] = carrot_c
                    if wheat_c > 0: portfolio["WHEAT"] = wheat_c

            elif day <= 19 and remaining_days >= 10:
                # Mid Season: Melons (50%) + Carrots (35%) + Wheat (15%)
                melon_c = int(needed_seeds * 0.50)
                carrot_c = int(needed_seeds * 0.35)
                wheat_c = needed_seeds - melon_c - carrot_c
                if melon_c > 0: portfolio["MELON"] = melon_c
                if carrot_c > 0: portfolio["CARROT"] = carrot_c
                if wheat_c > 0: portfolio["WHEAT"] = wheat_c

            elif remaining_days >= 3:
                # Late Season: Fast Carrots (75%) + Wheat (25%)
                carrot_c = int(needed_seeds * 0.75)
                wheat_c = needed_seeds - carrot_c
                if carrot_c > 0: portfolio["CARROT"] = carrot_c
                if wheat_c > 0: portfolio["WHEAT"] = wheat_c

            for crop, count in portfolio.items():
                if len(orders) >= 10:
                    break
                seed_price = CROPS[crop]["seed"]
                affordable = min(count, int(spendable // seed_price))
                if affordable > 0:
                    orders.append(["BUY_SEED", crop, affordable])
                    spendable -= affordable * seed_price
                    money -= affordable * seed_price

        # D. HIGH-THROUGHPUT HARVEST LIQUIDATION PIPELINE (Zero Inventory Choke)
        is_scarcity_window = self.town_model.is_post_consumption_window(step)

        sell_priority = ["MELON", "WOOL", "MILK", "STRAWBERRY", "FERTILIZER", "TOMATO", "EGG", "CARROT", "WHEAT"]
        for prod in sell_priority:
            if len(orders) >= 10:
                break
            qty = world_state.shed.get(prod, 0)
            if qty > 0:
                cur_p = world_state.market_prices.get(prod, 1)
                opp_frontrun = self.opponent_model.should_frontrun_opponent(prod, opp_imminent.get(prod, 0))

                should_sell = False
                if day >= 26 or sum(world_state.shed.values()) >= 25:
                    should_sell = True
                elif opp_frontrun:
                    should_sell = True
                elif is_scarcity_window and cur_p > 1:
                    should_sell = True
                elif cur_p > 1:
                    should_sell = True

                if should_sell:
                    # High-throughput liquidation batch: 12-16 units per turn
                    sell_amount = min(qty, 14) if day < 26 else qty
                    orders.append(["SELL", prod, sell_amount])

        # 5. Assign Worker Actions
        worker_actions = self.labor_scheduler.assign_worker_actions(world_state, chores)

        return {
            "farmer": worker_actions.get("farmer", ["PASS"]),
            "hands": worker_actions.get("hands", []),
            "market": orders[:10]
        }

# ======================================================================
# SECTION: engine/unified_agent.py
# ======================================================================
"""
=============================================================================
ENGINE: UNIFIED AGENT ENTRY POINT
=============================================================================
"""


_PLANNER = None


def get_planner():
    global _PLANNER
    if _PLANNER is None:
        _PLANNER = MacroPlanner()
    return _PLANNER


def agent(obs):
    try:
        world_state = WorldState(obs)
        planner = get_planner()
        return planner.plan_turn(world_state)
    except Exception as e:
        print(f"Error in unified agent: {e}")
        return {"farmer": ["PASS"], "hands": [], "market": []}
