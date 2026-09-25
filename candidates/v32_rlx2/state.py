# SPDX-License-Identifier: MIT
"""Kagriculture V32 RL-X2 Economic State Representation.

Extracts strongly typed, interpretable, and vectorized economic states across
four representation tiers (S0, S1, S2, S3) with zero observation leakage.
"""

from __future__ import annotations
import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
import numpy as np

try:
    from rlx2_config import (
        ANIMALS, BOARD_SIZE, CROPS, PRODUCTS, SEED_PRICES,
        TURNS_PER_DAY, fib_hire_cost
    )
except ImportError:
    from candidates.v32_rlx2.rlx2_config import (
        ANIMALS, BOARD_SIZE, CROPS, PRODUCTS, SEED_PRICES,
        TURNS_PER_DAY, fib_hire_cost
    )


@dataclass
class EconomicFeatures:
    """Strongly typed snapshot of economic, physical, and opponent state."""
    # 1. Capital & Runway
    cash: float
    wage_runway_days: float
    liquid_inventory_value: float
    committed_wages_today: float
    
    # 2. Labor
    active_workers: int
    hires_today: int
    next_hire_cost: int
    idle_hands_count: int
    chore_backlog: int
    
    # 3. Crops & Farm Tiles
    planted_crop_counts: Dict[str, int]
    unwatered_crops_count: int
    vacant_arable_count: int
    weed_count: int
    
    # 4. Livestock
    cow_count: int
    sheep_count: int
    goose_count: int
    unfed_animals_count: int
    uncared_animals_count: int
    empty_pastures_count: int
    feed_reserve_days: float
    wheat_in_shed: int
    
    # 5. Land
    unlocked_quadrants: int
    next_land_cost: int
    
    # 6. Market & Inventory
    spot_prices: Dict[str, float]
    price_deltas: Dict[str, float]
    market_inventory: Dict[str, int]
    shed_inventory: Dict[str, int]
    unlocked_shops: List[str]
    
    # 7. Time & Horizon
    step: int
    day: int
    hour: int
    remaining_steps: int
    is_terminal_window: bool
    
    # 8. Opponent Observables (S2)
    opp_cash: float
    opp_workers: int
    opp_cows: int
    opp_sheep: int
    opp_geese: int
    opp_crops: int
    opp_quadrants: int
    opp_recent_sell_volume: Dict[str, int] = field(default_factory=dict)
    
    # 9. Derived Opportunities (S3)
    preempt_sell_signals: Dict[str, float] = field(default_factory=dict)
    market_glut_signals: Dict[str, float] = field(default_factory=dict)
    liquidity_stress: float = 0.0


def extract_economic_features(
    observation: Dict[str, Any],
    player: int = 0,
    prev_prices: Optional[Dict[str, float]] = None,
    prev_opp_market_inv: Optional[Dict[str, int]] = None
) -> EconomicFeatures:
    """Extracts typed features from standard Kaggle observation dictionary."""
    farms = observation.get("farms", [])
    farm = farms[player] if farms and player < len(farms) else {}
    opp_farm = farms[1 - player] if farms and len(farms) >= 2 else {}
    
    cash = float(farm.get("money", 0.0) or 0.0)
    farmer_pos = tuple(farm.get("farmer", [4, 4]))
    hands = [tuple(h) for h in farm.get("hands", [])]
    active_workers = 1 + len(hands)
    hires_today = int(farm.get("hires_today", 0))
    next_hire = fib_hire_cost(hires_today)
    
    daily_wages = max(1.0, len(hands) * 24.0 * 1.0)
    runway_days = cash / daily_wages
    
    # Private player inventory
    private = observation.get("private", {}) or {}
    shed = {p: int((private.get("shed", {}) or {}).get(p, 0)) for p in PRODUCTS}
    seeds = {c: int((private.get("seeds", {}) or {}).get(c, 0)) for c in CROPS}
    invs = private.get("inventories", []) or []
    
    # Market
    mkt = observation.get("market", {}) or {}
    prices = {p: float((mkt.get("prices", {}) or {}).get(p, 25.0)) for p in PRODUCTS}
    mkt_inv = {p: int((mkt.get("inventory", {}) or {}).get(p, 10000)) for p in PRODUCTS}
    
    # Liquid inventory value at spot prices
    liquid_val = sum(shed[p] * prices[p] for p in PRODUCTS)
    
    # Price deltas
    px_deltas = {}
    for p in PRODUCTS:
        if prev_prices and p in prev_prices:
            px_deltas[p] = prices[p] - prev_prices[p]
        else:
            px_deltas[p] = 0.0
            
    # Tiles scan
    tiles = farm.get("tiles", []) or []
    crop_counts = {c: 0 for c in CROPS}
    unwatered = 0
    vacant = 0
    weeds = 0
    cows = 0
    sheep = 0
    geese = 0
    unfed = 0
    uncared = 0
    empty_pastures = 0
    
    for r in range(len(tiles)):
        for c in range(len(tiles[r])):
            t = tiles[r][c]
            if t == "LOCKED":
                continue
            if t is None:
                vacant += 1
            elif isinstance(t, dict):
                k = t.get("kind")
                if k == "WEED":
                    weeds += 1
                elif k == "PLANT":
                    crop_name = t.get("crop")
                    if crop_name in crop_counts:
                        crop_counts[crop_name] += 1
                    if not t.get("watered_today", False):
                        unwatered += 1
                elif k in ("PASTURE", "COOP"):
                    animal = t.get("animal")
                    if animal is None:
                        empty_pastures += 1
                    else:
                        if animal == "COW":
                            cows += 1
                        elif animal == "SHEEP":
                            sheep += 1
                        elif animal == "GOOSE":
                            geese += 1
                        if not t.get("fed_today", False):
                            unfed += 1
                        if not t.get("cared_today", False):
                            uncared += 1
                            
    # Opponent visible farm scan
    opp_cash = float(opp_farm.get("money", 0.0) or 0.0)
    opp_hands = opp_farm.get("hands", []) or []
    opp_workers = 1 + len(opp_hands)
    opp_tiles = opp_farm.get("tiles", []) or []
    opp_cows = opp_sheep = opp_geese = opp_crops = 0
    opp_quads = len(opp_farm.get("unlocked_quadrants", [1]) or [1])
    
    for r in range(len(opp_tiles)):
        for c in range(len(opp_tiles[r])):
            t = opp_tiles[r][c]
            if isinstance(t, dict):
                k = t.get("kind")
                if k == "PLANT":
                    opp_crops += 1
                elif k in ("PASTURE", "COOP"):
                    anim = t.get("animal")
                    if anim == "COW":
                        opp_cows += 1
                    elif anim == "SHEEP":
                        opp_sheep += 1
                    elif anim == "GOOSE":
                        opp_geese += 1
                        
    # Town and time
    step = int(observation.get("step", 0) or 0)
    day = int(observation.get("day", step // TURNS_PER_DAY) or 0)
    hour = int(observation.get("hour", step % TURNS_PER_DAY) or 0)
    remaining = max(0, 719 - step)
    is_terminal = step >= 712
    quads = len(farm.get("unlocked_quadrants", [1]) or [1])
    next_land = 1000 if quads == 1 else (2000 if quads == 2 else (4000 if quads == 3 else 0))
    
    wheat_shed = shed.get("WHEAT", 0)
    total_animals = cows + sheep + geese
    feed_runway = wheat_shed / max(1.0, float(total_animals))
    
    town = observation.get("town", {}) or {}
    unlocked_shops = list(town.get("unlocked_shops", []) or [])
    
    # Derived Signals (S3)
    preempt_signals = {}
    glut_signals = {}
    for prod in ("MILK", "WOOL", "MELON", "STRAWBERRY"):
        held = shed[prod]
        px = prices[prod]
        # Opponent sell pressure or impending collapse
        preempt_signals[prod] = 1.0 if (held >= 4 and px >= 30.0) else 0.0
        glut_signals[prod] = 1.0 if (mkt_inv[prod] > 10040 and px < 20.0) else 0.0
        
    liq_stress = 1.0 if (runway_days < 1.5 or cash < 50.0) else (0.5 if runway_days < 2.5 else 0.0)
    
    return EconomicFeatures(
        cash=cash,
        wage_runway_days=runway_days,
        liquid_inventory_value=liquid_val,
        committed_wages_today=float(len(hands) * (24 - hour)),
        active_workers=active_workers,
        hires_today=hires_today,
        next_hire_cost=next_hire,
        idle_hands_count=max(0, active_workers - (unwatered + unfed + uncared + weeds)),
        chore_backlog=unwatered + unfed + uncared + weeds,
        planted_crop_counts=crop_counts,
        unwatered_crops_count=unwatered,
        vacant_arable_count=vacant,
        weed_count=weeds,
        cow_count=cows,
        sheep_count=sheep,
        goose_count=geese,
        unfed_animals_count=unfed,
        uncared_animals_count=uncared,
        empty_pastures_count=empty_pastures,
        feed_reserve_days=feed_runway,
        wheat_in_shed=wheat_shed,
        unlocked_quadrants=quads,
        next_land_cost=next_land,
        spot_prices=prices,
        price_deltas=px_deltas,
        market_inventory=mkt_inv,
        shed_inventory=shed,
        unlocked_shops=unlocked_shops,
        step=step,
        day=day,
        hour=hour,
        remaining_steps=remaining,
        is_terminal_window=is_terminal,
        opp_cash=opp_cash,
        opp_workers=opp_workers,
        opp_cows=opp_cows,
        opp_sheep=opp_sheep,
        opp_geese=opp_geese,
        opp_crops=opp_crops,
        opp_quadrants=opp_quads,
        preempt_sell_signals=preempt_signals,
        market_glut_signals=glut_signals,
        liquidity_stress=liq_stress
    )


def vectorize_features(features: EconomicFeatures, tier: str = "S2") -> np.ndarray:
    """Converts EconomicFeatures into a normalized flat 1D numpy vector."""
    # S0: Raw essentials
    # cash, liquid_val, shed_tot, plant_tot, hands, 9 prices, 4 shops
    shed_tot = sum(features.shed_inventory.values())
    plant_tot = sum(features.planted_crop_counts.values())
    s0 = [
        features.cash / 100000.0,
        features.liquid_inventory_value / 50000.0,
        shed_tot / 100.0,
        plant_tot / 50.0,
        features.active_workers / 12.0,
        features.step / 720.0,
    ] + [features.spot_prices[p] / 300.0 for p in PRODUCTS] + [
        1.0 if "BAKERY" in features.unlocked_shops else 0.0,
        1.0 if "DAIRY" in features.unlocked_shops else 0.0,
        1.0 if "TEXTILE" in features.unlocked_shops else 0.0,
        1.0 if "PET_CAFE" in features.unlocked_shops else 0.0,
    ]
    if tier == "S0":
        return np.asarray(s0, dtype=np.float32)
        
    # S1: Structured Economic Features
    s1 = list(s0) + [
        min(1.0, features.wage_runway_days / 10.0),
        features.committed_wages_today / 500.0,
        features.next_hire_cost / 100.0,
        features.chore_backlog / 30.0,
        features.idle_hands_count / 12.0,
        features.unwatered_crops_count / 30.0,
        features.vacant_arable_count / 50.0,
        features.weed_count / 20.0,
        features.cow_count / 10.0,
        features.sheep_count / 10.0,
        features.goose_count / 10.0,
        features.unfed_animals_count / 15.0,
        features.uncared_animals_count / 15.0,
        features.empty_pastures_count / 10.0,
        min(1.0, features.feed_reserve_days / 10.0),
        features.wheat_in_shed / 50.0,
        features.unlocked_quadrants / 4.0,
        features.next_land_cost / 4000.0,
        (features.step % 4) / 4.0,  # Town consumption phase
        (features.step % 24) / 24.0,  # Hour of day
        1.0 if features.is_terminal_window else 0.0,
    ] + [features.planted_crop_counts[c] / 20.0 for c in CROPS] \
      + [features.shed_inventory[p] / 50.0 for p in PRODUCTS] \
      + [features.price_deltas[p] / 50.0 for p in PRODUCTS]
      
    if tier == "S1":
        return np.asarray(s1, dtype=np.float32)
        
    # S2: S1 + Opponent Features
    s2 = list(s1) + [
        features.opp_cash / 100000.0,
        (features.cash - features.opp_cash) / 50000.0,
        features.opp_workers / 12.0,
        features.opp_crops / 50.0,
        features.opp_cows / 10.0,
        features.opp_sheep / 10.0,
        features.opp_geese / 10.0,
        features.opp_quadrants / 4.0,
    ]
    if tier == "S2":
        return np.asarray(s2, dtype=np.float32)
        
    # S3: S2 + Derived Opportunities & Stress Signals
    s3 = list(s2) + [
        features.liquidity_stress,
        features.preempt_sell_signals.get("MILK", 0.0),
        features.preempt_sell_signals.get("WOOL", 0.0),
        features.preempt_sell_signals.get("MELON", 0.0),
        features.preempt_sell_signals.get("STRAWBERRY", 0.0),
        features.market_glut_signals.get("MILK", 0.0),
        features.market_glut_signals.get("WOOL", 0.0),
        features.market_glut_signals.get("MELON", 0.0),
        features.market_glut_signals.get("STRAWBERRY", 0.0),
    ]
    return np.asarray(s3, dtype=np.float32)


def get_feature_dim(tier: str = "S2") -> int:
    """Returns the exact dimension of the feature vector for a given tier."""
    dummy = extract_economic_features({"player": 0, "step": 0})
    return len(vectorize_features(dummy, tier=tier))
