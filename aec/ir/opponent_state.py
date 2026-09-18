# SPDX-License-Identifier: MIT
"""Opponent Economic Pressure Representation within Economic IR."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from aec.config import ANIMALS, CROPS, PRODUCTS


@dataclass
class OpponentState:
    """Continuous observable economic pressure signals from the rival player."""
    
    # Continuous supply & pressure forecasts per product
    supply_forecast: Dict[str, float] = field(default_factory=dict)
    harvest_pressure: Dict[str, float] = field(default_factory=dict)
    sale_pressure: Dict[str, float] = field(default_factory=dict)
    buy_pressure: Dict[str, float] = field(default_factory=dict)
    market_collision_risk: Dict[str, float] = field(default_factory=dict)
    
    # Observable physical features
    observed_cash: float = 0.0
    cash: float = 0.0
    observed_hires_today: int = 0
    observed_worker_count: int = 1
    observed_mature_crops: Dict[str, int] = field(default_factory=dict)
    observed_animals: Dict[str, int] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.cash > 0.0 and self.observed_cash == 0.0:
            self.observed_cash = self.cash
        elif self.observed_cash > 0.0 and self.cash == 0.0:
            self.cash = self.observed_cash
    
    # Coordinate and behavioral signals
    tape_similarity: float = 0.0
    is_clone_suspect: bool = False
    
    # Diagnostic regime tag (diagnostic only, NOT main planning abstraction)
    diagnostic_regime: str = "UNKNOWN"

    def get_supply_pressure(self, item: str) -> float:
        return self.supply_forecast.get(item, 0.0)

    def get_collision_risk(self, item: str) -> float:
        return self.market_collision_risk.get(item, 0.0)


def extract_opponent_state(
    opp_farm: Dict[str, Any],
    step: int,
    market_prices: Dict[str, int],
    prev_opp_state: Optional[OpponentState] = None
) -> OpponentState:
    """Deterministically extract continuous opponent pressure from observable state."""
    cash = float(opp_farm.get("money", 0.0) or 0.0)
    farmer = opp_farm.get("farmer", [4, 4])
    hands = opp_farm.get("hands", []) or []
    worker_count = 1 + len(hands)
    hires = int(opp_farm.get("hires_today", 0) or 0)
    
    # Scan observable tiles
    tiles = opp_farm.get("tiles", []) or []
    mature_crops: Dict[str, int] = {c: 0 for c in CROPS}
    animals: Dict[str, int] = {a: 0 for a in ANIMALS}
    
    for row in tiles:
        for tile in row:
            if not isinstance(tile, dict):
                continue
            kind = tile.get("kind")
            if kind == "PLANT":
                crop = tile.get("crop")
                yield_units = int(tile.get("yield_units", 0) or 0)
                if crop in mature_crops and yield_units > 0:
                    mature_crops[crop] += yield_units
            elif kind in ("COOP", "PASTURE"):
                animal = tile.get("animal")
                if animal in animals:
                    animals[animal] += 1

    # Continuous pressure derivations
    supply_forecast: Dict[str, float] = {p: 0.0 for p in PRODUCTS}
    harvest_pressure: Dict[str, float] = {p: 0.0 for p in PRODUCTS}
    sale_pressure: Dict[str, float] = {p: 0.0 for p in PRODUCTS}
    buy_pressure: Dict[str, float] = {p: 0.0 for p in PRODUCTS}
    collision_risk: Dict[str, float] = {p: 0.0 for p in PRODUCTS}

    # Crops mature: direct harvest & sale pressure
    for crop, count in mature_crops.items():
        if count > 0:
            harvest_pressure[crop] = min(1.0, count / 8.0)
            sale_pressure[crop] = min(1.0, count / 6.0)
            supply_forecast[crop] = float(count)

    # Animals: periodic supply estimation
    if animals.get("SHEEP", 0) > 0:
        # Sheep sheared every 3 days; estimate rolling supply
        sheep_n = animals["SHEEP"]
        supply_forecast["WOOL"] += sheep_n * 0.33
        sale_pressure["WOOL"] = min(1.0, sheep_n / 4.0)
    if animals.get("COW", 0) > 0:
        cow_n = animals["COW"]
        supply_forecast["MILK"] += cow_n * 0.5
        sale_pressure["MILK"] = min(1.0, cow_n / 4.0)
    if animals.get("GOOSE", 0) > 0:
        goose_n = animals["GOOSE"]
        supply_forecast["EGG"] += goose_n * 1.0
        sale_pressure["EGG"] = min(1.0, goose_n / 4.0)

    # Collision risk: higher when both high supply forecast and low town absorption
    for p in PRODUCTS:
        if supply_forecast[p] > 1.0:
            collision_risk[p] = min(1.0, supply_forecast[p] / 10.0)

    # Diagnostic regime tagging (diagnostic only!)
    diagnostic = "GENERALIST"
    if animals.get("SHEEP", 0) >= 4:
        diagnostic = "WOOL_FOCUSED"
    elif mature_crops.get("STRAWBERRY", 0) >= 8:
        diagnostic = "STRAWBERRY_FOCUSED"

    return OpponentState(
        supply_forecast=supply_forecast,
        harvest_pressure=harvest_pressure,
        sale_pressure=sale_pressure,
        buy_pressure=buy_pressure,
        market_collision_risk=collision_risk,
        observed_cash=cash,
        observed_hires_today=hires,
        observed_worker_count=worker_count,
        observed_mature_crops=mature_crops,
        observed_animals=animals,
        diagnostic_regime=diagnostic,
    )
