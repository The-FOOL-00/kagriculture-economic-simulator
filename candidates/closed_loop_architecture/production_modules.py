"""
PRODUCTION MODULES: Modular economic engines for Kaggriculture.
Enables the Closed-Loop Architecture to select, parameterize, and execute distinct
production regimes rather than hardcoding Dmitrii's Plan 0 everywhere.
"""
from dataclasses import dataclass
from typing import Dict, List, Any, Optional
import json
import os

@dataclass
class ProductionModuleConfig:
    module_id: str
    name: str
    description: str
    target_shops: List[str]
    primary_commodities: List[str]
    livestock_type: str  # 'SHEEP', 'COW', 'MIXED', 'NONE'
    expected_daily_cash_velocity: float
    requires_fertilizer_pipeline: bool
    plan_index: Optional[int] = None
    custom_tape_path: Optional[str] = None

class ProductionModuleManager:
    def __init__(self, actions_path: str = "extracted_agents/dmitrii_lb2800/actions.json"):
        self.actions_path = actions_path
        self._raw_plans: Optional[List[Any]] = None
        self._custom_tapes: Dict[str, List[Any]] = {}
        self.modules: Dict[str, ProductionModuleConfig] = {
            # MODULE A: Dmitrii-style fertilized strawberry engine
            "MODULE_A_FERT_STRAWBERRY": ProductionModuleConfig(
                module_id="MODULE_A_FERT_STRAWBERRY",
                name="Fertilized Strawberry Industrial Engine",
                description="61-fertilization schedule with 5 Sheep, high Strawberry compounding",
                target_shops=["YARN_STORE", "UNIVERSAL"],
                primary_commodities=["STRAWBERRY", "WOOL", "WHEAT"],
                livestock_type="SHEEP",
                expected_daily_cash_velocity=3200.0,
                requires_fertilizer_pipeline=True,
                plan_index=0
            ),
            
            # MODULE B: Dairy / cow-milk engine
            "MODULE_B_DAIRY_COW": ProductionModuleConfig(
                module_id="MODULE_B_DAIRY_COW",
                name="Dairy & Cow-Milk Engine",
                description="2-day Cow feeding loop, milk harvesting and delivery for Dairy worlds",
                target_shops=["SMOOTHIE_SHOP", "ICE_CREAM_SHOP", "PIZZA_SHOP"],
                primary_commodities=["MILK", "STRAWBERRY", "WHEAT"],
                livestock_type="COW",
                expected_daily_cash_velocity=3800.0,
                requires_fertilizer_pipeline=True,
                custom_tape_path="scratch/safe_liquidity_dairy_tape.json"
            ),
            
            # MODULE C: Carrot-heavy engine
            "MODULE_C_CARROT_FAST": ProductionModuleConfig(
                module_id="MODULE_C_CARROT_FAST",
                name="Carrot Fast-Turnover Engine",
                description="Rapid 3-day turnaround crop cycle, maximizing Pet Cafe & Farmers Market absorption",
                target_shops=["PET_CAFE", "FARMERS_MARKET"],
                primary_commodities=["CARROT", "WHEAT"],
                livestock_type="SHEEP",
                expected_daily_cash_velocity=2900.0,
                requires_fertilizer_pipeline=False,
                plan_index=10
            ),
            
            # MODULE D: Mixed diversified engine
            "MODULE_D_MIXED_DIVERSIFIED": ProductionModuleConfig(
                module_id="MODULE_D_MIXED_DIVERSIFIED",
                name="Mixed Diversified Engine (Pizza / Bakery / Brunch)",
                description="Multi-crop allocation (Tomato, Wheat, Strawberry, Milk) with dual demand capture",
                target_shops=["PIZZA_SHOP", "BAKERY", "BRUNCH_SPOT"],
                primary_commodities=["TOMATO", "MILK", "WHEAT", "STRAWBERRY"],
                livestock_type="MIXED",
                expected_daily_cash_velocity=3400.0,
                requires_fertilizer_pipeline=True,
                plan_index=7
            ),
            
            # MODULE E: Minimal-liquidity-safe engine
            "MODULE_E_MINIMAL_LIQUIDITY": ProductionModuleConfig(
                module_id="MODULE_E_MINIMAL_LIQUIDITY",
                name="Minimal-Liquidity Safe Engine",
                description="Zero speculative holding, immediate sales, high cash runway buffer",
                target_shops=["UNIVERSAL"],
                primary_commodities=["STRAWBERRY", "WHEAT", "WOOL"],
                livestock_type="SHEEP",
                expected_daily_cash_velocity=2600.0,
                requires_fertilizer_pipeline=True,
                plan_index=1
            )
        }

    def load_plans(self):
        if self._raw_plans is None:
            if os.path.exists(self.actions_path):
                with open(self.actions_path, "r") as f:
                    self._raw_plans = json.load(f)
            else:
                self._raw_plans = []

    def get_module_action_tape(self, module_id: str) -> List[Any]:
        self.load_plans()
        config = self.modules.get(module_id)
        if not config:
            return self._raw_plans[0] if self._raw_plans else []

        if config.custom_tape_path and os.path.exists(config.custom_tape_path):
            if module_id not in self._custom_tapes:
                with open(config.custom_tape_path, "r") as f:
                    self._custom_tapes[module_id] = json.load(f)
            return self._custom_tapes[module_id]

        if config.plan_index is not None and self._raw_plans and config.plan_index < len(self._raw_plans):
            return self._raw_plans[config.plan_index]

        return self._raw_plans[0] if self._raw_plans else []
