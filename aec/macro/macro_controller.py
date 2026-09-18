# SPDX-License-Identifier: MIT
"""Macro Layer Strategy and Governance Controller (§10)."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from aec.counterfactual.opponent_pressure import OpponentPressureState
from aec.ir.economic_state import EconomicState


class MacroPosture(str, Enum):
    """Macroeconomic stance of the farm (§10)."""
    EARLY_EXPANSION = "EARLY_EXPANSION"                 # Day 0-10: Rapid land and seed acquisition
    BALANCED_PRODUCTION = "BALANCED_PRODUCTION"         # Day 10-24: High-yield cash crop cultivation
    LIQUIDITY_CONSERVATIVE = "LIQUIDITY_CONSERVATIVE"   # Preserving cash for high-margin operations
    TERMINAL_HARVEST_RUN = "TERMINAL_HARVEST_RUN"       # Day 25-30: Strict endgame harvest & liquidation


class CashPosture(str, Enum):
    """Capital allocation posture."""
    PRESERVE_CAPITAL = "PRESERVE_CAPITAL"               # Retain safety cushion for seeds/wages
    REINVEST_ACTIVE = "REINVEST_ACTIVE"                 # Aggressively deploy capital into high-ROI assets
    MAX_LIQUIDATION = "MAX_LIQUIDATION"                 # Disinvest all assets into terminal cash


class MarketPosture(str, Enum):
    """Market engagement posture."""
    PATIENT_CYCLE = "PATIENT_CYCLE"                     # Wait for town price peaks
    IMMEDIATE_CLEARING = "IMMEDIATE_CLEARING"           # Rapid cash turn-around
    PREEMPTIVE = "PREEMPTIVE"                           # Frontrun opponent dumping


@dataclass
class MacroStrategy:
    """Explicit macro-level guidance for farm economic direction (§10)."""
    posture: MacroPosture
    cash_posture: CashPosture
    market_posture: MarketPosture
    crop_priorities: List[str]
    min_cash_reserve: float
    terminal_step_threshold: int = 672
    allow_capital_expenditures: bool = True
    allow_novel_planting: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "posture": self.posture.value,
            "cash_posture": self.cash_posture.value,
            "market_posture": self.market_posture.value,
            "crop_priorities": self.crop_priorities,
            "min_cash_reserve": self.min_cash_reserve,
            "allow_capex": self.allow_capital_expenditures,
            "allow_planting": self.allow_planting,
        }


class MacroController:
    """Macro Strategy Controller.
    
    Establishes high-level economic posture and certifies that tactical patches
    do not silently violate or subvert long-term farm direction.
    """

    def formulate_strategy(
        self,
        econ_state: EconomicState,
        pressure_state: Optional[OpponentPressureState] = None
    ) -> MacroStrategy:
        step = econ_state.step
        cash = econ_state.cash

        # Terminal Phase (Days 28-30, step >= 672)
        if step >= 672:
            return MacroStrategy(
                posture=MacroPosture.TERMINAL_HARVEST_RUN,
                cash_posture=CashPosture.MAX_LIQUIDATION,
                market_posture=MarketPosture.IMMEDIATE_CLEARING,
                crop_priorities=["STRAWBERRY", "TOMATO", "MELON", "CARROT", "WHEAT"],
                min_cash_reserve=0.0,
                terminal_step_threshold=672,
                allow_capital_expenditures=False,
                allow_novel_planting=False,
            )

        # Early Expansion Phase (Days 0-10, step < 240)
        if step < 240:
            return MacroStrategy(
                posture=MacroPosture.EARLY_EXPANSION,
                cash_posture=CashPosture.REINVEST_ACTIVE,
                market_posture=MarketPosture.PATIENT_CYCLE,
                crop_priorities=["STRAWBERRY", "TOMATO", "CARROT"],
                min_cash_reserve=100.0,
                allow_capital_expenditures=True,
                allow_novel_planting=True,
            )

        # Mid-Game Balanced Production (Days 10-27)
        # Check cash reserve against wage requirements
        num_hands = max(0, len(econ_state.workers.workers) - 1)
        wage_buffer = num_hands * 100.0

        market_p = MarketPosture.PATIENT_CYCLE
        if pressure_state and pressure_state.timing_pressure >= 0.6:
            market_p = MarketPosture.PREEMPTIVE

        allow_planting = step <= 576  # Don't plant 10-day crops if they won't mature

        return MacroStrategy(
            posture=MacroPosture.BALANCED_PRODUCTION,
            cash_posture=CashPosture.PRESERVE_CAPITAL,
            market_posture=market_p,
            crop_priorities=["STRAWBERRY", "MELON", "TOMATO"],
            min_cash_reserve=wage_buffer + 150.0,
            allow_capital_expenditures=cash > 1200.0,
            allow_novel_planting=allow_planting,
        )

    def validate_tactical_compatibility(
        self,
        candidate_patch: Any,
        strategy: MacroStrategy,
        econ_state: EconomicState
    ) -> Tuple[bool, Optional[str]]:
        """A tactical patch must not silently modify macro strategy (§10)."""
        family = str(getattr(candidate_patch, "mechanism_family", "") or getattr(candidate_patch, "candidate_transformation_family", ""))

        # 1. Terminal Run: reject any non-harvest, non-liquidation capex
        if strategy.posture == MacroPosture.TERMINAL_HARVEST_RUN:
            upfront = float(getattr(candidate_patch, "upfront_cost", 0.0) or getattr(candidate_patch, "required_cash", 0.0))
            if upfront > 0.0 and family not in ("DYNAMIC_SHADOW_HARVEST", "TERMINAL_HARVEST_SWEEP", "TERMINAL_CONVERSION"):
                return False, f"MACRO_POSTURE_VIOLATION: Capex forbidden in {strategy.posture.value}"

        # 2. Planting cutoff
        if not strategy.allow_novel_planting and family == "SEED_PLANTING":
            return False, "MACRO_POSTURE_VIOLATION: Novel planting shut down post-day 24"

        # 3. Minimum cash reserve
        upfront = float(getattr(candidate_patch, "upfront_cost", 0.0) or getattr(candidate_patch, "required_cash", 0.0))
        if upfront > 0:
            post_cash = econ_state.cash - upfront
            if post_cash < strategy.min_cash_reserve and strategy.posture != MacroPosture.TERMINAL_HARVEST_RUN:
                return False, f"MACRO_CASH_VIOLATION: Post-patch cash ${post_cash:.1f} breaches min reserve ${strategy.min_cash_reserve:.1f}"

        return True, None
