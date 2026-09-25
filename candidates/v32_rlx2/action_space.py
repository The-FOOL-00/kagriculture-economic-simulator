# SPDX-License-Identifier: MIT
"""Kagriculture V32 RL-X2 Macro Action Space & Intent Definitions.

Defines the 10 discrete macro strategic actions, semantic mappings,
and hard legality masks. Action 0 is strictly FOLLOW_A7.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, List, Tuple
import numpy as np

try:
    from rlx2_config import ANIMAL_COSTS, LAND_PRICES, PRODUCTS, SEED_PRICES
    from state import EconomicFeatures
except ImportError:
    from candidates.v32_rlx2.rlx2_config import ANIMAL_COSTS, LAND_PRICES, PRODUCTS, SEED_PRICES
    from candidates.v32_rlx2.state import EconomicFeatures


ACTION_NAMES: Tuple[str, ...] = (
    "FOLLOW_A7",                 # 0: Bit-identical incumbent passthrough
    "OPPORTUNISTIC_SELL",        # 1: Monetize high-price shed inventory immediately
    "SELECTIVE_PREEMPT_SELL",    # 2: Front-run opponent sell dumps on volatile products
    "LIQUIDATE_SURPLUS",         # 3: Sell non-essential shed goods for immediate liquidity
    "CROP_EXPANSION_MELON",      # 4: Buy melon seeds and prioritize arable planting
    "CROP_EXPANSION_WHEAT",      # 5: Replenish livestock feed reserve
    "LIVESTOCK_EXPANSION_COW",   # 6: Acquire Cow + pasture if cash runway permits
    "LIVESTOCK_EXPANSION_SHEEP", # 7: Acquire Sheep + pasture if cash runway permits
    "PRESERVE_CASH",             # 8: Throttle hiring/land to defend cash buffer
    "EXPAND_LAND",               # 9: Unlock next farm quadrant
)

ACTION_SPACE_SIZE = len(ACTION_NAMES)


@dataclass
class MacroAction:
    index: int
    name: str


def get_action_mask(features: EconomicFeatures) -> np.ndarray:
    """Returns a boolean array of length 10 indicating strictly legal/feasible actions.
    
    Action 0 (FOLLOW_A7) is unconditionally legal (fail-closed bedrock).
    """
    mask = np.zeros(ACTION_SPACE_SIZE, dtype=bool)
    mask[0] = True  # FOLLOW_A7 is ALWAYS legal
    
    # 1: OPPORTUNISTIC_SELL
    has_sellable = any(
        features.shed_inventory.get(p, 0) >= 4 and features.spot_prices.get(p, 0) >= 10.0
        for p in PRODUCTS
    )
    mask[1] = has_sellable and not features.is_terminal_window
    
    # 2: SELECTIVE_PREEMPT_SELL
    has_volatile = any(
        features.shed_inventory.get(p, 0) >= 2 and features.spot_prices.get(p, 0) >= 25.0
        for p in ("MILK", "WOOL", "MELON", "STRAWBERRY")
    )
    mask[2] = has_volatile and not features.is_terminal_window
    
    # 3: LIQUIDATE_SURPLUS
    has_surplus = any(
        features.shed_inventory.get(p, 0) > 0 for p in PRODUCTS if p != "WHEAT"
    ) or (features.shed_inventory.get("WHEAT", 0) > 20)
    mask[3] = has_surplus and not features.is_terminal_window
    
    # 4: CROP_EXPANSION_MELON
    mask[4] = (
        features.cash >= SEED_PRICES["MELON"]
        and features.vacant_arable_count > 0
        and features.step < 450
        and features.wage_runway_days >= 2.0
    )
    
    # 5: CROP_EXPANSION_WHEAT
    mask[5] = (
        features.cash >= SEED_PRICES["WHEAT"]
        and features.vacant_arable_count > 0
        and features.step < 550
    )
    
    # 6: LIVESTOCK_EXPANSION_COW
    mask[6] = (
        features.cash >= ANIMAL_COSTS["COW"] + 100
        and features.vacant_arable_count >= 1
        and features.wage_runway_days >= 3.0
        and features.step < 450
    )
    
    # 7: LIVESTOCK_EXPANSION_SHEEP
    mask[7] = (
        features.cash >= ANIMAL_COSTS["SHEEP"] + 100
        and features.vacant_arable_count >= 1
        and features.wage_runway_days >= 3.0
        and features.step < 450
    )
    
    # 8: PRESERVE_CASH
    mask[8] = (features.active_workers > 1 or features.hires_today > 0)
    
    # 9: EXPAND_LAND
    mask[9] = (
        features.unlocked_quadrants < 4
        and features.next_land_cost > 0
        and features.cash >= features.next_land_cost + 100.0
        and features.step < 500
    )
    
    return mask
