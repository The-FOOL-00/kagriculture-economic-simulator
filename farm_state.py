"""
Farm State representation and tile analysis for Kaggriculture.
"""

from config import CROPS, ANIMALS, PRODUCTS, LAND_ORDER, LAND_PRICES


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

                        # Check if harvestable
                        is_harvestable = False
                        if cd.get("ongoing", False):
                            if age >= cd["first_yield_day"] and yield_units > 0:
                                is_harvestable = True
                        else:
                            # One-time crop
                            # Harvest at max_yield_day, or if yield reaches max_yield cap, or if season ending
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

    def shed_item_count(self):
        return sum(self.shed.values())

    def next_land_price(self):
        n_unlocked = len(self.unlocked_quadrants) - 1
        if n_unlocked < len(LAND_PRICES):
            return LAND_PRICES[n_unlocked]
        return None
