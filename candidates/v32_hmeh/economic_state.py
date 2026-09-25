# SPDX-License-Identifier: MIT
"""HMEH Economic State Representation Layer.

Extracts a strongly typed, interpretable snapshot of economic, physical,
and labor state from the simulator observation at every turn.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple

try:
    from config import CROPS_INFO, PRODUCTS, SEED_PRICES, fib_hire_cost
except ImportError:
    from candidates.v32_hmeh.config import CROPS_INFO, PRODUCTS, SEED_PRICES, fib_hire_cost


@dataclass
class EconomicState:
    # 1. Capital
    cash: float
    committed_wages_today: float
    wage_runway_days: float
    liquid_inventory_value: float
    estimated_near_term_revenue: float
    
    # 2. Labor
    active_workers: int              # Farmer (1) + hired hands
    hires_today: int
    next_hire_cost: int
    worker_utilization: float        # Chores assigned / active workers
    idle_hands_count: int
    pending_chore_count: int
    expected_labor_requirement: int
    
    # 3. Crops
    planted_crops: Dict[str, int]
    crop_stages: List[Dict[str, Any]]
    unwatered_crop_tiles: List[Tuple[int, int]]
    vacant_arable_tiles: List[Tuple[int, int]]
    expected_harvest_value: float
    
    # 4. Livestock
    cow_count: int
    sheep_count: int
    goose_count: int
    unfed_animal_tiles: List[Tuple[int, int]]
    uncared_animal_tiles: List[Tuple[int, int]]
    empty_pastures: List[Tuple[int, int]]
    feed_reserve_days: float
    wheat_in_shed: int
    
    # 5. Land
    unlocked_quadrants: int          # 1 to 4
    occupied_tiles: int
    available_tiles: int
    weed_tiles: List[Tuple[int, int]]
    next_land_cost: int
    
    # 6. Market & Town
    spot_prices: Dict[str, float]
    price_trends: Dict[str, float]
    unlocked_shops: List[str]
    shed_inventory: Dict[str, int]
    carried_inventory: List[Dict[str, int]]
    seed_inventory: Dict[str, int]
    
    # 7. Time & Horizon
    step: int
    day: int
    hour: int
    remaining_steps: int
    is_terminal_window: bool
    
    # 8. Robustness & Internal Tracking
    consecutive_stalls: int = 0
    cash_stress_level: float = 0.0   # 0.0 = comfortable, 1.0 = severe stress


def extract_economic_state(
    observation: Dict[str, Any],
    player: int = 0,
    prev_state: Optional[EconomicState] = None,
    consecutive_stalls: int = 0
) -> EconomicState:
    """Parses raw observation into typed EconomicState."""
    farms = observation.get("farms", [])
    farm = farms[player] if farms and player < len(farms) else {}
    cash = float(farm.get("money", 0.0) or 0.0)
    
    farmer_pos = tuple(farm.get("farmer", [4, 4]))
    hands = [tuple(h) for h in farm.get("hands", [])]
    active_workers = 1 + len(hands)
    hires_today = int(farm.get("hires_today", 0))
    next_hire_cost = fib_hire_cost(hires_today)
    
    # Projected daily wage burden for hired hands: $5 per worker per day
    # (or step-based wage depending on simulator configuration)
    daily_wage_burden = max(1.0, len(hands) * 24.0 * 1.0)
    wage_runway_days = cash / daily_wage_burden
    
    unlocked_quads = list(farm.get("unlocked_quadrants", ["NW"]))
    unlocked_quadrants = len(unlocked_quads)
    next_land_cost = (
        1000 if unlocked_quadrants == 1
        else (2000 if unlocked_quadrants == 2 else 4000)
    )
    
    tiles = farm.get("tiles", [[None] * 10 for _ in range(10)])
    
    private = observation.get("private", {}) or {}
    shed = {k: max(0, int(v)) for k, v in dict(private.get("shed", {})).items()}
    seeds = {k: max(0, int(v)) for k, v in dict(private.get("seeds", {})).items()}
    inventories = [dict(inv or {}) for inv in private.get("inventories", [{}])]
    
    market = observation.get("market", {}) or {}
    spot_prices = {k: float(v) for k, v in dict(market.get("prices", {})).items()}
    
    town = observation.get("town", {}) or {}
    unlocked_shops = list(town.get("unlocked_shops", []))
    
    step = int(observation.get("step", 0) or 0)
    day = int(observation.get("day", step // 24) or 0)
    hour = int(observation.get("hour", step % 24) or 0)
    remaining_steps = max(0, 718 - step)
    is_terminal_window = (step >= 712)
    
    # Tile scan
    planted_crops: Dict[str, int] = {}
    crop_stages: List[Dict[str, Any]] = []
    unwatered_crop_tiles: List[Tuple[int, int]] = []
    vacant_arable_tiles: List[Tuple[int, int]] = []
    weed_tiles: List[Tuple[int, int]] = []
    empty_pastures: List[Tuple[int, int]] = []
    unfed_animal_tiles: List[Tuple[int, int]] = []
    uncared_animal_tiles: List[Tuple[int, int]] = []
    
    cow_count = 0
    sheep_count = 0
    goose_count = 0
    occupied_tiles = 0
    available_tiles = 0
    expected_harvest_value = 0.0
    pending_chores = 0
    
    for y in range(len(tiles)):
        for x in range(len(tiles[0])):
            t = tiles[y][x]
            pos = (x, y)
            if t == "LOCKED":
                continue
            available_tiles += 1
            if t is None:
                vacant_arable_tiles.append(pos)
            elif isinstance(t, dict):
                occupied_tiles += 1
                kind = t.get("kind")
                if kind == "WEED":
                    weed_tiles.append(pos)
                    pending_chores += 1
                elif kind == "PASTURE":
                    if "animal" in t and t.get("animal"):
                        a_type = t.get("animal")
                        if a_type == "COW":
                            cow_count += 1
                        elif a_type == "SHEEP":
                            sheep_count += 1
                        if not t.get("fed_today", False):
                            unfed_animal_tiles.append(pos)
                            pending_chores += 1
                        if not t.get("cared_today", False):
                            uncared_animal_tiles.append(pos)
                            pending_chores += 1
                        if t.get("yield_units", 0) > 0:
                            pending_chores += 1
                    else:
                        empty_pastures.append(pos)
                elif kind == "PLANT":
                    crop = t.get("crop")
                    planted_crops[crop] = planted_crops.get(crop, 0) + 1
                    age = day - t.get("planted_day", 0)
                    yield_u = t.get("yield_units", 0)
                    crop_stages.append({
                        "pos": pos,
                        "crop": crop,
                        "age": age,
                        "yield_units": yield_u,
                        "watered_today": t.get("watered_today", False)
                    })
                    if not t.get("watered_today", False):
                        unwatered_crop_tiles.append(pos)
                        pending_chores += 1
                    if yield_u > 0:
                        pending_chores += 1
                        expected_harvest_value += yield_u * spot_prices.get(crop, 20.0)
    
    # Liquid inventory valuation
    liquid_inventory_value = sum(
        qty * spot_prices.get(prod, 0.0)
        for prod, qty in shed.items()
    )
    
    # Price trends
    price_trends: Dict[str, float] = {}
    if prev_state and prev_state.spot_prices:
        for p in PRODUCTS:
            price_trends[p] = spot_prices.get(p, 0.0) - prev_state.spot_prices.get(p, 0.0)
    else:
        for p in PRODUCTS:
            price_trends[p] = 0.0
            
    # Labor metrics
    expected_labor_requirement = max(1, (pending_chores + len(vacant_arable_tiles) + 6) // 8)
    worker_utilization = min(1.0, pending_chores / max(1, active_workers))
    idle_hands_count = max(0, active_workers - pending_chores)
    
    wheat_in_shed = shed.get("WHEAT", 0)
    total_animals = cow_count + sheep_count + goose_count
    feed_reserve_days = (wheat_in_shed / max(1, total_animals)) if total_animals > 0 else 99.0
    
    # Cash stress calculation
    cash_stress_level = 0.0
    if wage_runway_days < 1.0:
        cash_stress_level = 1.0
    elif wage_runway_days < 2.5:
        cash_stress_level = (2.5 - wage_runway_days) / 1.5
        
    return EconomicState(
        cash=cash,
        committed_wages_today=daily_wage_burden,
        wage_runway_days=wage_runway_days,
        liquid_inventory_value=liquid_inventory_value,
        estimated_near_term_revenue=expected_harvest_value,
        active_workers=active_workers,
        hires_today=hires_today,
        next_hire_cost=next_hire_cost,
        worker_utilization=worker_utilization,
        idle_hands_count=idle_hands_count,
        pending_chore_count=pending_chores,
        expected_labor_requirement=expected_labor_requirement,
        planted_crops=planted_crops,
        crop_stages=crop_stages,
        unwatered_crop_tiles=unwatered_crop_tiles,
        vacant_arable_tiles=vacant_arable_tiles,
        expected_harvest_value=expected_harvest_value,
        cow_count=cow_count,
        sheep_count=sheep_count,
        goose_count=goose_count,
        unfed_animal_tiles=unfed_animal_tiles,
        uncared_animal_tiles=uncared_animal_tiles,
        empty_pastures=empty_pastures,
        feed_reserve_days=feed_reserve_days,
        wheat_in_shed=wheat_in_shed,
        unlocked_quadrants=unlocked_quadrants,
        occupied_tiles=occupied_tiles,
        available_tiles=available_tiles,
        weed_tiles=weed_tiles,
        next_land_cost=next_land_cost,
        spot_prices=spot_prices,
        price_trends=price_trends,
        unlocked_shops=unlocked_shops,
        shed_inventory=shed,
        carried_inventory=inventories,
        seed_inventory=seeds,
        step=step,
        day=day,
        hour=hour,
        remaining_steps=remaining_steps,
        is_terminal_window=is_terminal_window,
        consecutive_stalls=consecutive_stalls,
        cash_stress_level=cash_stress_level
    )
