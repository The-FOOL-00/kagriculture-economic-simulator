# SPDX-License-Identifier: MIT
"""AEC-RESOURCE: Dynamic Inventory Conversion Catalog and Bounded Discovery (§8, §9, §10, §11).

Defines exact game conversion recipes, multi-stage conversion chains,
cash liquidity coupling, shed capacity constraints, and bounded discovery.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple

from aec.config import (
    CROP_GROWTH_DAYS,
    CROP_SEED_PRICE,
    CROPS,
    PRODUCTS,
    SHED_CAPACITY,
    TURNS_PER_DAY,
)
from aec.ir.economic_state import EconomicState


@dataclass
class ConversionRecipe:
    """A discrete, physical or market transformation permitted by game rules (§8)."""
    recipe_id: str
    name: str
    input_resources: Dict[str, int]     # Commodity/item -> units required
    output_resources: Dict[str, int]    # Commodity/item -> units produced
    duration_steps: int                 # Steps from start to availability
    cash_cost_est: float = 0.0          # Immediate monetary cost
    requires_worker: bool = False
    requires_structure: Optional[str] = None # e.g. "PASTURE", "COOP", "PLANT"
    shed_capacity_delta: int = 0        # Net change in shed storage
    is_terminal_only: bool = False


@dataclass
class ConversionPath:
    """A single-step or multi-step conversion trajectory (§8)."""
    path_id: str
    target_commodity: str
    recipes: List[ConversionRecipe]
    total_steps: int
    total_cost_est: float
    expected_revenue_est: float
    net_value_est: float
    is_feasible: bool = True
    infeasibility_reason: Optional[str] = None


class ConversionCatalog:
    """Authoritative repository of exact game transformations."""

    @staticmethod
    def get_standard_recipes() -> Dict[str, ConversionRecipe]:
        return {
            "BUY_WHEAT_FEED": ConversionRecipe(
                recipe_id="BUY_WHEAT_FEED",
                name="Market Purchase of Wheat Feed",
                input_resources={"CASH": 25},
                output_resources={"WHEAT": 1},
                duration_steps=1,
                cash_cost_est=25.0,
                requires_worker=False,
                shed_capacity_delta=1
            ),
            "FEED_LIVESTOCK_COW": ConversionRecipe(
                recipe_id="FEED_LIVESTOCK_COW",
                name="Feed Cow for Milk Production",
                input_resources={"WHEAT": 1},
                output_resources={"MILK": 1, "FERTILIZER": 1},
                duration_steps=48,     # 2 days interval
                cash_cost_est=0.0,
                requires_worker=True,
                requires_structure="PASTURE",
                shed_capacity_delta=0  # Shed neutral until dropped
            ),
            "FEED_LIVESTOCK_SHEEP": ConversionRecipe(
                recipe_id="FEED_LIVESTOCK_SHEEP",
                name="Feed Sheep for Wool Production",
                input_resources={"WHEAT": 1},
                output_resources={"WOOL": 1, "FERTILIZER": 1},
                duration_steps=72,     # 3 days interval
                cash_cost_est=0.0,
                requires_worker=True,
                requires_structure="PASTURE",
                shed_capacity_delta=0
            ),
            "FEED_LIVESTOCK_GOOSE": ConversionRecipe(
                recipe_id="FEED_LIVESTOCK_GOOSE",
                name="Feed Goose for Egg Production",
                input_resources={"WHEAT": 1},
                output_resources={"EGG": 1, "FERTILIZER": 1},
                duration_steps=24,     # 1 day interval
                cash_cost_est=0.0,
                requires_worker=True,
                requires_structure="COOP",
                shed_capacity_delta=0
            ),
            "GROW_WHEAT_CROP": ConversionRecipe(
                recipe_id="GROW_WHEAT_CROP",
                name="Grow Wheat from Seed",
                input_resources={"CASH": 10},
                output_resources={"WHEAT": 4},
                duration_steps=CROP_GROWTH_DAYS["WHEAT"] * TURNS_PER_DAY, # 48 steps
                cash_cost_est=10.0,
                requires_worker=True,
                requires_structure=None,
                shed_capacity_delta=0
            ),
            "GROW_CARROT_CROP": ConversionRecipe(
                recipe_id="GROW_CARROT_CROP",
                name="Grow Carrot from Seed",
                input_resources={"CASH": 20},
                output_resources={"CARROT": 4},
                duration_steps=CROP_GROWTH_DAYS["CARROT"] * TURNS_PER_DAY, # 48 steps
                cash_cost_est=20.0,
                requires_worker=True,
                shed_capacity_delta=0
            ),
            "GROW_MELON_CROP": ConversionRecipe(
                recipe_id="GROW_MELON_CROP",
                name="Grow Melon from Seed",
                input_resources={"CASH": 80},
                output_resources={"MELON": 6},
                duration_steps=CROP_GROWTH_DAYS["MELON"] * TURNS_PER_DAY, # 240 steps
                cash_cost_est=80.0,
                requires_worker=True,
                shed_capacity_delta=0
            ),
            "TERMINAL_LIQUIDATE_COMMODITY": ConversionRecipe(
                recipe_id="TERMINAL_LIQUIDATE_COMMODITY",
                name="Step 718 Terminal Shed Liquidation",
                input_resources={"SHED_COMMODITY": 1},
                output_resources={"CASH": 1}, # Unit value resolved at pricing
                duration_steps=1,
                cash_cost_est=0.0,
                requires_worker=False,
                shed_capacity_delta=-1,
                is_terminal_only=True
            ),
        }


class ConversionDiscoveryEngine:
    """Discovers feasible, economically relevant conversion chains (§8, §10, §11, §12)."""

    def __init__(self) -> None:
        self.catalog = ConversionCatalog()

    def discover_conversion_paths(
        self,
        econ_state: EconomicState,
        max_horizon: int = 48
    ) -> List[ConversionPath]:
        """Bounded discovery of valid conversion paths constrained by cash, capacity, and terminal distance."""
        paths: List[ConversionPath] = []
        recipes = self.catalog.get_standard_recipes()
        current_cash = float(econ_state.farm.cash)
        current_shed_units = econ_state.farm.shed_total_units
        remaining_steps = econ_state.remaining_horizon

        # 1. Animal Feed Conversion Paths
        # Check active animals that produce high-value products
        tiles = econ_state.farm.tiles
        has_cow = False
        has_sheep = False
        has_goose = False

        for row in tiles:
            for tile in row:
                if isinstance(tile, dict) and "animal" in tile:
                    sub = tile["animal"]
                    if sub == "COW":
                        has_cow = True
                    elif sub == "SHEEP":
                        has_sheep = True
                    elif sub == "GOOSE":
                        has_goose = True

        wheat_price = float(econ_state.market.get_price("WHEAT"))
        milk_price = float(econ_state.market.get_price("MILK"))
        wool_price = float(econ_state.market.get_price("WOOL"))
        egg_price = float(econ_state.market.get_price("EGG"))

        # Cow chain: Buy Wheat -> Feed Cow -> Milk
        if has_cow and remaining_steps >= 48:
            cow_path = ConversionPath(
                path_id="CONV_CHAIN_WHEAT_TO_MILK",
                target_commodity="MILK",
                recipes=[recipes["BUY_WHEAT_FEED"], recipes["FEED_LIVESTOCK_COW"]],
                total_steps=49,
                total_cost_est=wheat_price,
                expected_revenue_est=milk_price,
                net_value_est=milk_price - wheat_price
            )
            is_feas, reason = self.check_path_feasibility(cow_path, econ_state)
            cow_path.is_feasible = is_feas
            cow_path.infeasibility_reason = reason
            paths.append(cow_path)

        # Goose chain: Buy Wheat -> Feed Goose -> Egg
        if has_goose and remaining_steps >= 24:
            goose_path = ConversionPath(
                path_id="CONV_CHAIN_WHEAT_TO_EGG",
                target_commodity="EGG",
                recipes=[recipes["BUY_WHEAT_FEED"], recipes["FEED_LIVESTOCK_GOOSE"]],
                total_steps=25,
                total_cost_est=wheat_price,
                expected_revenue_est=egg_price,
                net_value_est=egg_price - wheat_price
            )
            is_feas, reason = self.check_path_feasibility(goose_path, econ_state)
            goose_path.is_feasible = is_feas
            goose_path.infeasibility_reason = reason
            paths.append(goose_path)

        # Sheep chain: Buy Wheat -> Feed Sheep -> Wool
        if has_sheep and remaining_steps >= 72:
            sheep_path = ConversionPath(
                path_id="CONV_CHAIN_WHEAT_TO_WOOL",
                target_commodity="WOOL",
                recipes=[recipes["BUY_WHEAT_FEED"], recipes["FEED_LIVESTOCK_SHEEP"]],
                total_steps=73,
                total_cost_est=wheat_price,
                expected_revenue_est=wool_price,
                net_value_est=wool_price - wheat_price
            )
            is_feas, reason = self.check_path_feasibility(sheep_path, econ_state)
            sheep_path.is_feasible = is_feas
            sheep_path.infeasibility_reason = reason
            paths.append(sheep_path)

        # 2. Fast Crop Conversion: Carrot cycle
        carrot_price = float(econ_state.market.get_price("CARROT"))
        if remaining_steps >= 48:
            carrot_path = ConversionPath(
                path_id="CONV_CHAIN_SEED_TO_CARROT",
                target_commodity="CARROT",
                recipes=[recipes["GROW_CARROT_CROP"]],
                total_steps=48,
                total_cost_est=20.0,
                expected_revenue_est=carrot_price * 4,
                net_value_est=(carrot_price * 4) - 20.0
            )
            is_feas, reason = self.check_path_feasibility(carrot_path, econ_state)
            carrot_path.is_feasible = is_feas
            carrot_path.infeasibility_reason = reason
            paths.append(carrot_path)

        return paths

    def check_path_feasibility(
        self,
        path: ConversionPath,
        econ_state: EconomicState
    ) -> Tuple[bool, Optional[str]]:
        """Verify strict cash liquidity, shed capacity, and terminal horizon constraints (§10, §11, §12)."""
        current_cash = float(econ_state.farm.cash)
        current_shed = econ_state.farm.shed_total_units
        remaining_steps = econ_state.remaining_horizon

        # 1. Terminal feasibility (§12)
        if path.total_steps > remaining_steps:
            return False, f"Terminal infeasibility: path requires {path.total_steps} steps, but only {remaining_steps} remain"

        # 2. Cash liquidity feasibility (§10)
        accum_cash = current_cash
        for r in path.recipes:
            if accum_cash < r.cash_cost_est:
                return False, f"Cash liquidity hole: requires ${r.cash_cost_est:.1f} but available cash is ${accum_cash:.1f}"
            accum_cash -= r.cash_cost_est

        # 3. Shed capacity feasibility (§11)
        accum_shed = current_shed
        for r in path.recipes:
            accum_shed += r.shed_capacity_delta
            if accum_shed > SHED_CAPACITY:
                return False, f"Shed capacity overflow: projected storage {accum_shed} exceeds limit {SHED_CAPACITY}"

        return True, None
