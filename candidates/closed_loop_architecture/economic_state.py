"""
ECONOMIC STATE REPRESENTATION
Tracks all critical economic variables from observation:
cash, runway, mandatory expenditures, labor availability, shed occupancy,
animal feeding deadlines, fertilizer pipeline, and town shop demand.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional

@dataclass
class EconomicState:
    step: int
    day: int
    hour: int
    cash: float
    workers_count: int
    tiles: List[List[Any]]
    shed: Dict[str, int]
    shed_occupancy: int
    seeds: Dict[str, int]
    market_prices: Dict[str, float]
    unlocked_shops: List[str]
    
    # Derived Economic Variables
    next_mandatory_expenditure: float = 0.0
    cash_runway_hours: float = 999.0
    animal_counts: Dict[str, int] = field(default_factory=dict)
    animal_feeding_deadlines: Dict[str, int] = field(default_factory=dict)
    crop_counts: Dict[str, int] = field(default_factory=dict)
    crop_maturing_in_days: Dict[str, int] = field(default_factory=dict)
    expected_production_revenue_48h: float = 0.0
    town_shop_demand: Dict[str, int] = field(default_factory=dict)
    committed_capex_next_24h: float = 0.0

    @classmethod
    def from_obs(cls, obs: Dict[str, Any]) -> "EconomicState":
        step = obs.get("step", 0)
        day = obs.get("day", step // 24)
        hour = obs.get("hour", step % 24)
        player = obs.get("player", 0)
        
        farm = obs.get("farms", [{}, {}])[player]
        cash = float(farm.get("money", 0.0))
        tiles = farm.get("tiles", [])
        hands = farm.get("hands", [])
        workers_count = len(hands) + 1  # farmer + hands
        
        private = obs.get("private", {})
        shed_raw = private.get("shed", {})
        shed = {k: max(0, int(v)) for k, v in shed_raw.items()}
        shed_occupancy = sum(shed.values())
        
        seeds_raw = private.get("seeds", {})
        seeds = {k: max(0, int(v)) for k, v in seeds_raw.items()}
        
        market = obs.get("market", {})
        market_prices = {k: float(v) for k, v in market.get("prices", {}).items()}
        
        town = obs.get("town", {})
        unlocked_shops = list(town.get("unlocked_shops", []))
        
        state = cls(
            step=step,
            day=day,
            hour=hour,
            cash=cash,
            workers_count=workers_count,
            tiles=tiles,
            shed=shed,
            shed_occupancy=shed_occupancy,
            seeds=seeds,
            market_prices=market_prices,
            unlocked_shops=unlocked_shops
        )
        state._compute_derived_variables()
        return state

    def _compute_derived_variables(self):
        # 1. Animal populations & feeding deadlines
        self.animal_counts = {"SHEEP": 0, "COW": 0, "GOOSE": 0}
        self.crop_counts = {"STRAWBERRY": 0, "WHEAT": 0, "TOMATO": 0, "CARROT": 0, "MELON": 0}
        
        for r in self.tiles:
            for t in r:
                if isinstance(t, dict):
                    # Crops
                    if t.get("kind") == "PLANT":
                        c = t.get("crop")
                        if c in self.crop_counts:
                            self.crop_counts[c] += 1
                    # Animals
                    an = t.get("animal")
                    if an in self.animal_counts:
                        self.animal_counts[an] += 1
                        
        # 2. Next mandatory expenditure calculation
        # Morning hiring occurs at hour 0 of every day
        hours_until_dawn = (24 - self.hour) % 24
        if hours_until_dawn == 0:
            # It is dawn right now
            expected_hiring_cost = self.workers_count * 200.0
        else:
            expected_hiring_cost = self.workers_count * 200.0
            
        # Animal feed buffer: need 1 feed per sheep/cow every 2-3 days
        wheat_feed_available = self.shed.get("WHEAT", 0)
        total_animals = sum(self.animal_counts.values())
        feed_deficit = max(0, total_animals - wheat_feed_available)
        feed_cost_reserve = feed_deficit * 250.0  # market price if forced to buy
        
        # Day 10 Land Expansion capex
        if self.day == 10 and self.hour < 12:
            self.committed_capex_next_24h = 3000.0  # SW quadrant purchase
        else:
            self.committed_capex_next_24h = 0.0
            
        self.next_mandatory_expenditure = expected_hiring_cost + feed_cost_reserve + self.committed_capex_next_24h
        
        # 3. Cash Runway
        hourly_burn = (self.workers_count * 200.0) / 24.0
        if hourly_burn > 0:
            self.cash_runway_hours = self.cash / hourly_burn
        else:
            self.cash_runway_hours = 999.0
            
        # 4. Town Shop Demands
        SHOP_PRODUCTS = {
            "BAKERY": ["EGG", "WHEAT"],
            "BRUNCH_SPOT": ["EGG", "WHEAT", "STRAWBERRY"],
            "FARMERS_MARKET": ["CARROT", "TOMATO"],
            "ICE_CREAM_SHOP": ["MILK", "STRAWBERRY"],
            "PET_CAFE": ["CARROT"],
            "PIZZA_SHOP": ["MILK", "TOMATO", "WHEAT"],
            "SMOOTHIE_SHOP": ["STRAWBERRY", "MILK"],
            "YARN_STORE": ["WOOL"]
        }
        self.town_shop_demand = {p: 0 for p in ["WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON", "EGG", "MILK", "WOOL"]}
        for s in self.unlocked_shops:
            for p in SHOP_PRODUCTS.get(s, []):
                self.town_shop_demand[p] += 1
                
        # 5. Expected Near-term Production Revenue (48h)
        # Value of crops maturing soon or liquid inventory
        liquid_inv_value = sum(self.shed.get(p, 0) * self.market_prices.get(p, 100.0) for p in self.shed)
        self.expected_production_revenue_48h = liquid_inv_value
