"""
=============================================================================
ENGINE: WORLD MODEL & TRANSITION SIMULATOR
=============================================================================
Represents complete state of both farms, market, shed, and inventories.
Supports forward state transitions for rolling-horizon planning.
=============================================================================
"""

import copy
from config import CROPS, ANIMALS, PRODUCTS, LAND_ORDER, LAND_PRICES, SHOPS, compute_market_price


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
