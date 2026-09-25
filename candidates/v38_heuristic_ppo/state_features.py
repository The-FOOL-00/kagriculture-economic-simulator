# SPDX-License-Identifier: MIT
"""Kagriculture V38 State Representation: Physical vs Economic Abstraction.

Strictly adheres to legal observability (zero leakage of opponent hidden states,
seed oracles, or future steps). Separates:
- Physical state: What can physically happen?
- Economic state: What is financially valuable?
"""

from __future__ import annotations
import copy
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
import numpy as np

try:
    from config import (
        PRODUCTS, SEED_PRICES, ANIMAL_COSTS, ANIMAL_STRUCTURES,
        LAND_PRICES, EPISODE_STEPS, WAGE_PER_HAND_PER_DAY
    )
except ImportError:
    from candidates.v38_heuristic_ppo.config import (
        PRODUCTS, SEED_PRICES, ANIMAL_COSTS, ANIMAL_STRUCTURES,
        LAND_PRICES, EPISODE_STEPS, WAGE_PER_HAND_PER_DAY
    )


def _get(obj: Any, key: str, default: Any = None) -> Any:
    if isinstance(obj, dict):
        return obj.get(key, default)
    getter = getattr(obj, "get", None)
    if callable(getter):
        return getter(key, default)
    return getattr(obj, key, default)


def _int(val: Any, default: int = 0) -> int:
    try:
        return int(val)
    except (TypeError, ValueError):
        return default


def _float(val: Any, default: float = 0.0) -> float:
    try:
        return float(val)
    except (TypeError, ValueError):
        return default


@dataclass
class PhysicalFeatures:
    """Physical State: spatial layout, units, tiles, and biological maturity."""
    step: int = 0
    day: int = 0
    hour: int = 0
    board_size: int = 10
    farmer_pos: Tuple[int, int] = (0, 0)
    hand_positions: List[Tuple[int, int]] = field(default_factory=list)
    worker_count: int = 1
    unlocked_quadrants: int = 1
    
    # Tile censuses
    empty_tiles: int = 0
    weed_tiles: int = 0
    locked_tiles: int = 75
    crop_counts: Dict[str, int] = field(default_factory=dict)
    unwatered_crops: int = 0
    harvestable_crops: int = 0
    
    # Livestock
    animal_counts: Dict[str, int] = field(default_factory=dict)
    unfed_animals: int = 0
    uncared_animals: int = 0
    pasture_count: int = 0
    coop_count: int = 0
    empty_pastures: int = 0
    
    # Hand inventory states
    hands_carrying: int = 0
    hands_idle: int = 0


@dataclass
class EconomicFeatures:
    """Economic State: liquid capital, asset values, liabilities, and market signals."""
    step: int = 0
    cash: float = 0.0
    cash_velocity: float = 0.0
    shed_inventory: Dict[str, int] = field(default_factory=dict)
    shed_liquidation_value: float = 0.0
    seed_inventory: Dict[str, int] = field(default_factory=dict)
    
    # Spot prices & dynamics
    spot_prices: Dict[str, float] = field(default_factory=dict)
    price_deltas: Dict[str, float] = field(default_factory=dict)
    
    # Liabilities & commitments
    daily_wage_commitment: float = 0.0
    days_of_wage_runway: float = 0.0
    next_quadrant_cost: float = 1000.0
    next_hire_cost: float = 1.0
    
    # Livestock feed runway (wheat reserve / animals)
    feed_runway_days: float = 0.0
    
    # Market & town state
    unlocked_shop_count: int = 0
    town_consumption_tick: bool = False
    
    # Opponent observables (strictly legal)
    opp_cash: float = 0.0
    opp_cash_delta: float = 0.0
    opp_worker_count: int = 1
    opp_visible_crops: int = 0
    opp_visible_animals: int = 0
    opp_unlocked_quadrants: int = 1
    
    # Derived liquidity safety buffer
    liquidity_buffer: float = 0.0
    estimated_terminal_value: float = 0.0


@dataclass
class StateAbstraction:
    physical: PhysicalFeatures
    economic: EconomicFeatures


def extract_state_abstraction(
    observation: Dict[str, Any],
    player: int = 0,
    prev_econ: Optional[EconomicFeatures] = None
) -> StateAbstraction:
    """Extracts strongly-typed physical and economic state from legal observation."""
    step = _int(_get(observation, "step", 0))
    day = _int(_get(observation, "day", step // 24))
    hour = _int(_get(observation, "hour", step % 24))
    
    farms = _get(observation, "farms", []) or []
    farm = farms[player] if player < len(farms) else {}
    opp_farm = farms[1 - player] if len(farms) >= 2 and 1 - player < len(farms) else {}
    
    private = _get(observation, "private", {}) or {}
    shed = {k: max(0, _int(v)) for k, v in dict(_get(private, "shed", {}) or {}).items()}
    seeds = {k: max(0, _int(v)) for k, v in dict(_get(private, "seeds", {}) or {}).items()}
    invs = [dict(i or {}) for i in (_get(private, "inventories", []) or [])]
    
    market = _get(observation, "market", {}) or {}
    prices = {k: _float(v) for k, v in dict(_get(market, "prices", {}) or {}).items()}
    town = _get(observation, "town", {}) or {}
    shops = list(_get(town, "unlocked_shops", []) or [])
    
    # --- Physical Extraction ---
    tiles = _get(farm, "tiles", []) or []
    board_size = len(tiles) or 10
    farmer_pos = tuple(_get(farm, "farmer", [0, 0]) or [0, 0])
    raw_hands = _get(farm, "hands", []) or []
    hand_positions = [tuple(h) for h in raw_hands]
    worker_count = 1 + len(hand_positions)
    quads = len(list(_get(farm, "unlocked_quadrants", []) or [])) or 1
    
    empty_tiles = 0
    weed_tiles = 0
    locked_tiles = 0
    crop_counts = {p: 0 for p in ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON")}
    unwatered = 0
    harvestable = 0
    animal_counts = {"COW": 0, "SHEEP": 0, "GOOSE": 0}
    unfed = 0
    uncared = 0
    pasture_count = 0
    coop_count = 0
    empty_pastures = 0
    
    for row in tiles:
        for t in row:
            if t is None:
                empty_tiles += 1
            elif t == "LOCKED":
                locked_tiles += 1
            elif isinstance(t, dict):
                kind = t.get("kind")
                if kind == "WEED":
                    weed_tiles += 1
                elif kind == "PLANT":
                    c = t.get("crop")
                    if c in crop_counts:
                        crop_counts[c] += 1
                    if not t.get("watered_today", False):
                        unwatered += 1
                    if _int(t.get("yield_units", 0)) > 0:
                        harvestable += 1
                elif kind == "PASTURE":
                    pasture_count += 1
                    a = t.get("animal")
                    if a in animal_counts:
                        animal_counts[a] += 1
                        if not t.get("fed_today", False):
                            unfed += 1
                        if not t.get("cared_today", False):
                            uncared += 1
                    else:
                        empty_pastures += 1
                elif kind == "COOP":
                    coop_count += 1
                    a = t.get("animal")
                    if a in animal_counts:
                        animal_counts[a] += 1
                        if not t.get("fed_today", False):
                            unfed += 1
                        if not t.get("cared_today", False):
                            uncared += 1
    
    carrying = sum(1 for inv in invs if sum(_int(v) for v in inv.values()) > 0)
    idle = max(0, worker_count - carrying)
    
    phys = PhysicalFeatures(
        step=step,
        day=day,
        hour=hour,
        board_size=board_size,
        farmer_pos=farmer_pos,
        hand_positions=hand_positions,
        worker_count=worker_count,
        unlocked_quadrants=quads,
        empty_tiles=empty_tiles,
        weed_tiles=weed_tiles,
        locked_tiles=locked_tiles,
        crop_counts=crop_counts,
        unwatered_crops=unwatered,
        harvestable_crops=harvestable,
        animal_counts=animal_counts,
        unfed_animals=unfed,
        uncared_animals=uncared,
        pasture_count=pasture_count,
        coop_count=coop_count,
        empty_pastures=empty_pastures,
        hands_carrying=carrying,
        hands_idle=idle,
    )
    
    # --- Economic Extraction ---
    cash = _float(_get(farm, "money", 0.0))
    cash_vel = (cash - prev_econ.cash) if prev_econ else 0.0
    
    # Conservative shed liquidation value
    shed_val = sum(qty * prices.get(prod, 5.0) for prod, qty in shed.items())
    
    price_deltas = {}
    for p in PRODUCTS:
        prev_p = prev_econ.spot_prices.get(p, prices.get(p, 10.0)) if prev_econ else prices.get(p, 10.0)
        price_deltas[p] = prices.get(p, 10.0) - prev_p
        
    num_hands = len(hand_positions)
    daily_wages = num_hands * WAGE_PER_HAND_PER_DAY
    wage_runway = (cash / daily_wages) if daily_wages > 0 else 99.0
    
    # Next quadrant cost
    quad_costs = [1000.0, 2000.0, 4000.0]
    next_quad_cost = quad_costs[quads - 1] if quads - 1 < len(quad_costs) else 99999.0
    
    # Next hire cost
    hires_today = _int(_get(farm, "hires_today", 0))
    fib_costs = [1, 1, 2, 3, 5, 8, 13, 21, 34, 55]
    next_hire_cost = float(fib_costs[min(hires_today, len(fib_costs) - 1)])
    
    total_animals = sum(animal_counts.values())
    wheat_in_shed = shed.get("WHEAT", 0)
    feed_runway = (wheat_in_shed / total_animals) if total_animals > 0 else 99.0
    
    # Opponent observables
    opp_cash = _float(_get(opp_farm, "money", 0.0))
    opp_cash_delta = cash - opp_cash
    opp_hands = _get(opp_farm, "hands", []) or []
    opp_worker_count = 1 + len(opp_hands)
    opp_quads = len(list(_get(opp_farm, "unlocked_quadrants", []) or [])) or 1
    
    # Count visible opponent assets
    opp_tiles = _get(opp_farm, "tiles", []) or []
    opp_crops = 0
    opp_animals = 0
    for r in opp_tiles:
        for t in r:
            if isinstance(t, dict):
                if t.get("kind") == "PLANT":
                    opp_crops += 1
                elif t.get("kind") in ("PASTURE", "COOP") and t.get("animal"):
                    opp_animals += 1
                    
    # Liquidity safety buffer = cash available after 2 days of wages
    liquidity_buffer = max(0.0, cash - 2.0 * daily_wages)
    
    # Estimated terminal value approximation
    est_terminal = cash + shed_val + (total_animals * 350.0) + (sum(crop_counts.values()) * 40.0)
    
    econ = EconomicFeatures(
        step=step,
        cash=cash,
        cash_velocity=cash_vel,
        shed_inventory=shed,
        shed_liquidation_value=shed_val,
        seed_inventory=seeds,
        spot_prices=prices,
        price_deltas=price_deltas,
        daily_wage_commitment=daily_wages,
        days_of_wage_runway=min(wage_runway, 30.0),
        next_quadrant_cost=next_quad_cost,
        next_hire_cost=next_hire_cost,
        feed_runway_days=min(feed_runway, 30.0),
        unlocked_shop_count=len(shops),
        town_consumption_tick=(step % 4 == 0),
        opp_cash=opp_cash,
        opp_cash_delta=opp_cash_delta,
        opp_worker_count=opp_worker_count,
        opp_visible_crops=opp_crops,
        opp_visible_animals=opp_animals,
        opp_unlocked_quadrants=opp_quads,
        liquidity_buffer=liquidity_buffer,
        estimated_terminal_value=est_terminal,
    )
    
    return StateAbstraction(physical=phys, economic=econ)


def vectorize_economic_features(econ: EconomicFeatures, phys: Optional[PhysicalFeatures] = None) -> np.ndarray:
    """Vectorizes observable economic & macro-physical state for neural policy input.
    
    Total Dimension = 64 features, normalized to roughly [-1.0, 1.0].
    """
    vec = []
    
    # 1. Temporal Progress (3)
    vec.append(econ.step / 720.0)
    vec.append((econ.step % 24) / 24.0)
    vec.append(1.0 if econ.town_consumption_tick else 0.0)
    
    # 2. Capital & Liquidity (6)
    vec.append(min(econ.cash / 10000.0, 10.0))
    vec.append(np.clip(econ.cash_velocity / 500.0, -5.0, 5.0))
    vec.append(min(econ.shed_liquidation_value / 10000.0, 10.0))
    vec.append(min(econ.liquidity_buffer / 5000.0, 5.0))
    vec.append(min(econ.days_of_wage_runway / 10.0, 3.0))
    vec.append(min(econ.daily_wage_commitment / 100.0, 5.0))
    
    # 3. Spot Prices for 9 products (9)
    for p in PRODUCTS:
        vec.append(min(econ.spot_prices.get(p, 10.0) / 100.0, 3.0))
        
    # 4. Price Deltas for 9 products (9)
    for p in PRODUCTS:
        vec.append(np.clip(econ.price_deltas.get(p, 0.0) / 20.0, -3.0, 3.0))
        
    # 5. Shed Inventory Quantities (9)
    for p in PRODUCTS:
        vec.append(min(econ.shed_inventory.get(p, 0) / 50.0, 4.0))
        
    # 6. Seed Inventory (5)
    for c in ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON"):
        vec.append(min(econ.seed_inventory.get(c, 0) / 20.0, 3.0))
        
    # 7. Labor & Land Costs (4)
    vec.append(min(econ.next_hire_cost / 50.0, 2.0))
    vec.append(min(econ.next_quadrant_cost / 4000.0, 1.0))
    vec.append(min(econ.feed_runway_days / 10.0, 3.0))
    vec.append(econ.unlocked_shop_count / 10.0)
    
    # 8. Opponent Observables (6)
    vec.append(min(econ.opp_cash / 10000.0, 10.0))
    vec.append(np.clip(econ.opp_cash_delta / 5000.0, -5.0, 5.0))
    vec.append(econ.opp_worker_count / 10.0)
    vec.append(econ.opp_visible_crops / 25.0)
    vec.append(econ.opp_visible_animals / 10.0)
    vec.append(econ.opp_unlocked_quadrants / 4.0)
    
    # 9. Macro Physical Summary (if available) (13)
    if phys is not None:
        vec.append(phys.worker_count / 10.0)
        vec.append(phys.unlocked_quadrants / 4.0)
        vec.append(phys.empty_tiles / 25.0)
        vec.append(phys.weed_tiles / 10.0)
        vec.append(phys.unwatered_crops / 25.0)
        vec.append(phys.harvestable_crops / 25.0)
        vec.append(phys.animal_counts.get("COW", 0) / 5.0)
        vec.append(phys.animal_counts.get("SHEEP", 0) / 5.0)
        vec.append(phys.animal_counts.get("GOOSE", 0) / 5.0)
        vec.append(phys.unfed_animals / 5.0)
        vec.append(phys.empty_pastures / 5.0)
        vec.append(phys.hands_carrying / 10.0)
        vec.append(phys.hands_idle / 10.0)
    else:
        vec.extend([0.0] * 13)
        
    return np.array(vec, dtype=np.float32)

ECONOMIC_FEATURE_DIM = 64
