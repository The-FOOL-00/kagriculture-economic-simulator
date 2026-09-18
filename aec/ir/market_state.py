# SPDX-License-Identifier: MIT
"""Market State Representation within Economic IR."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Tuple

from aec.config import PRODUCTS

# Verified town shop consumption table from AUDIT #2
TOWN_SHOP_CONSUMPTION: Dict[str, Tuple[Tuple[str, int], ...]] = {
    "BAKERY": (("EGG", 1), ("WHEAT", 1)),
    "BRUNCH_SPOT": (("EGG", 1), ("WHEAT", 1), ("STRAWBERRY", 1)),
    "FARMERS_MARKET": (("WHEAT", 1), ("CARROT", 1), ("TOMATO", 1), ("STRAWBERRY", 1)),
    "ICE_CREAM_SHOP": (("STRAWBERRY", 1), ("MILK", 1), ("WHEAT", 1)),
    "PET_CAFE": (("CARROT", 2),),
    "PIZZA_SHOP": (("MILK", 1), ("TOMATO", 1), ("WHEAT", 1)),
    "SMOOTHIE_SHOP": (("STRAWBERRY", 1), ("MILK", 1)),
    "YARN_STORE": (("WOOL", 2),),
}

BASE_PRICES: Dict[str, int] = {
    "WHEAT": 25, "CARROT": 35, "TOMATO": 60, "STRAWBERRY": 120, "MELON": 250,
    "EGG": 50, "MILK": 160, "WOOL": 200, "FERTILIZER": 100
}


@dataclass
class MarketState:
    """Current public market and town economic state."""
    current_prices: Dict[str, int] = field(default_factory=dict)
    market_inventory: Dict[str, int] = field(default_factory=dict)
    unlocked_shops: List[str] = field(default_factory=list)
    steps_to_town_tick: int = 4
    expected_absorption: Dict[str, int] = field(default_factory=dict)
    liquidity_ratios: Dict[str, float] = field(default_factory=dict)
    market_pressure: Dict[str, float] = field(default_factory=dict)

    @property
    def prices(self) -> Dict[str, int]:
        return self.current_prices

    def get_price(self, item: str) -> int:
        return self.current_prices.get(item, BASE_PRICES.get(item, 1))

    def get_liquidity(self, item: str) -> float:
        return self.liquidity_ratios.get(item, 1.0)

    @property
    def is_town_tick_turn(self) -> bool:
        return self.steps_to_town_tick == 4 or self.steps_to_town_tick == 0


def compute_expected_absorption(unlocked_shops: List[str]) -> Dict[str, int]:
    """Calculate town absorption per 4-step interval from confirmed shops."""
    absorption: Dict[str, int] = {p: 0 for p in PRODUCTS}
    for shop in unlocked_shops:
        consumptions = TOWN_SHOP_CONSUMPTION.get(shop, ())
        for item, qty in consumptions:
            if item in absorption:
                absorption[item] += qty
    return absorption
