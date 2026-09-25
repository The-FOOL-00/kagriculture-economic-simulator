# SPDX-License-Identifier: MIT
"""HMEH Configuration and Macroeconomic Constants.

Defines commodity properties, crop life-cycle tables, Fibonacci hiring schedules,
and default economic policy parameters.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Tuple

# All tradeable products
PRODUCTS = (
    "WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON",
    "EGG", "MILK", "WOOL", "FERTILIZER"
)

# Seed prices
SEED_PRICES: Dict[str, int] = {
    "WHEAT": 10,
    "CARROT": 20,
    "TOMATO": 50,
    "STRAWBERRY": 100,
    "MELON": 80,
}

# Animal purchase costs and required structures
ANIMAL_COSTS: Dict[str, int] = {
    "GOOSE": 300,
    "COW": 400,
    "SHEEP": 500,
}

ANIMAL_STRUCTURES: Dict[str, str] = {
    "GOOSE": "COOP",
    "COW": "PASTURE",
    "SHEEP": "PASTURE",
}

# Expansion land quadrant costs (quadrant 2, 3, 4)
LAND_PRICES: Tuple[int, ...] = (1000, 2000, 4000)

# Grid movements
MOVES: Dict[str, Tuple[int, int]] = {
    "NORTH": (0, -1),
    "SOUTH": (0, 1),
    "EAST": (1, 0),
    "WEST": (-1, 0),
}

# High-value front-running targets
FRONT_RUN_ITEMS = ("MILK", "WOOL", "STRAWBERRY", "MELON")

# Crop life-cycle data
CROPS_INFO: Dict[str, Dict] = {
    "WHEAT": {
        "seed_cost": 10,
        "first_yield_day": 2,
        "max_yield_day": 4,
        "interval": 0,
        "max_yield": 6,
        "ongoing": False,
    },
    "CARROT": {
        "seed_cost": 20,
        "first_yield_day": 2,
        "max_yield_day": 3,
        "interval": 0,
        "max_yield": 4,
        "ongoing": False,
    },
    "TOMATO": {
        "seed_cost": 50,
        "first_yield_day": 8,
        "max_yield_day": 8,
        "interval": 1,
        "max_yield": 4,
        "ongoing": True,
    },
    "STRAWBERRY": {
        "seed_cost": 100,
        "first_yield_day": 10,
        "max_yield_day": 10,
        "interval": 2,
        "max_yield": 4,
        "ongoing": True,
    },
    "MELON": {
        "seed_cost": 80,
        "first_yield_day": 10,
        "max_yield_day": 12,
        "interval": 0,
        "max_yield": 6,
        "ongoing": False,
    },
}

def fib_hire_cost(n_prior_hires_today: int) -> int:
    """Marginal wage cost to hire the (n+1)-th worker today."""
    a, b = 1, 1
    for _ in range(n_prior_hires_today):
        a, b = b, a + b
    return a

@dataclass
class HMEHConfig:
    # Capital
    min_cash_reserve: float = 30.0
    wage_runway_stress_threshold: float = 2.0  # days of runway
    
    # Labor
    hire_initial_burst: int = 5
    max_workers: int = 11
    labor_mode: str = "static"  # "static" for HMEH-0, "adaptive" for HMEH-1+
    
    # Livestock
    cow_target: int = 8
    sheep_target: int = 4
    feed_reserve_days: int = 3
    cow_buy_threshold: float = 695.0
    sheep_buy_threshold: float = 595.0
    
    # Crops
    melon_seed_target: int = 12  # A7 enables 12 melon plants
    strawberry_seed_target: int = 38
    strawberry_start_step: int = 128
    
    # Land Milestones
    land_1_step: int = 150
    land_2_step: int = 265
    
    # Market & Selling
    sell_crops_start_step: int = 72
    sell_batch_size: int = 18
    market_mode: str = "static"  # "static" vs "adaptive" (HMEH-3+)
    min_sell_price: float = 2.0
    
    # Production Adaptation
    production_mode: str = "static"  # "static" vs "shop_conditioned" (HMEH-2+)
    
    # Terminal Liquidation
    terminal_mode: str = "static"  # "static" vs "search" (HMEH-4)
    terminal_step: int = 712
    
    # System
    shed_capacity: int = 100
    max_market_orders: int = 10
    board_size: int = 10
    total_steps: int = 720


# Re-exports for compatibility with external modules
try:
    import sys, os
    _root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    if _root_dir not in sys.path:
        sys.path.insert(0, _root_dir)
    import config as _root_config
    compute_market_price = getattr(_root_config, "compute_market_price", None)
    FARMER_MOVES = getattr(_root_config, "FARMER_MOVES", MOVES)
    SHOPS = getattr(_root_config, "SHOPS", {})
    MARKET_PARAMS = getattr(_root_config, "MARKET_PARAMS", {})
except Exception:
    pass
