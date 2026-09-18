# SPDX-License-Identifier: MIT
"""Opponent Continuous Economic Pressure State and Modeling (§8, §9)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from aec.config import ANIMALS, CROPS, PRODUCTS
from aec.ir.economic_state import EconomicState
from aec.ir.opponent_state import OpponentState


@dataclass
class OpponentPressureState:
    """Continuous observable economic pressure signals from the rival player (§8).

    This is an interpretable continuous pressure signal, not uncalibrated point predictions.
    """
    market_activity_level: float = 0.0          # 0.0 (passive) to 1.0 (hyperactive trading)
    observed_inventory: Dict[str, int] = field(default_factory=dict)
    observed_cash: float = 0.0
    sale_pressure: Dict[str, float] = field(default_factory=dict)         # per-product dump risk
    buy_pressure: Dict[str, float] = field(default_factory=dict)          # per-product demand risk
    timing_pressure: float = 0.0                # urgency: risk that waiting devalues our trade
    shared_resource_collision: Dict[str, float] = field(default_factory=dict)
    price_pressure: Dict[str, float] = field(default_factory=dict)        # price depression likelihood
    route_interference_risk: float = 0.0        # spatial conflict / obstruction risk
    terminal_pressure: float = 0.0              # endgame liquidation race pressure
    confidence: float = 0.5                     # 0.0 (uncertain/noisy) to 1.0 (high confidence)

    def is_baseline_degrading_if_waiting(self, product: Optional[str] = None) -> bool:
        """Is the current baseline likely to become worse if we wait? (§8)"""
        if product:
            return self.sale_pressure.get(product, 0.0) >= 0.5 or self.price_pressure.get(product, 0.0) >= 0.5
        return self.timing_pressure >= 0.6 or self.terminal_pressure >= 0.7

    def should_accelerate_opportunity(self, product: str) -> bool:
        """Should we evaluate or commit an earlier market or harvest opportunity? (§8)"""
        return self.sale_pressure.get(product, 0.0) >= 0.4 or self.shared_resource_collision.get(product, 0.0) >= 0.5

    def should_expand_horizon(self) -> bool:
        """Should horizon expand due to rival activity / collision? (§8)"""
        return self.market_activity_level >= 0.5 or self.terminal_pressure >= 0.6

    def has_market_collision(self, product: str) -> bool:
        """Is there an active or impending market collision on this product? (§8)"""
        return self.shared_resource_collision.get(product, 0.0) >= 0.4

    def candidate_strategic_priority(self, candidate: Any) -> float:
        """Score candidate strategic urgency without bypassing safety or counterfactuals (§9)."""
        family = str(getattr(candidate, "mechanism_family", "") or getattr(candidate, "candidate_transformation_family", ""))
        product = getattr(candidate, "target_product", None) or getattr(candidate, "entity", None)

        bonus = 0.0
        if family in ("DEPENDENCY_AWARE_MARKET_TIMING", "MARKET_TIMING", "OPPONENT_PREEMPT_SELL"):
            if product and product in self.sale_pressure:
                bonus += self.sale_pressure[product] * 20.0
            bonus += self.timing_pressure * 15.0

        if family in ("DYNAMIC_SHADOW_HARVEST", "TERMINAL_HARVEST_SWEEP"):
            bonus += self.terminal_pressure * 25.0

        return bonus

    def to_dict(self) -> Dict[str, Any]:
        return {
            "activity": round(self.market_activity_level, 3),
            "cash": round(self.observed_cash, 1),
            "timing_pressure": round(self.timing_pressure, 3),
            "route_interference": round(self.route_interference_risk, 3),
            "terminal_pressure": round(self.terminal_pressure, 3),
            "confidence": round(self.confidence, 3),
            "sale_pressure": {k: round(v, 2) for k, v in self.sale_pressure.items() if v > 0},
            "collision_risk": {k: round(v, 2) for k, v in self.shared_resource_collision.items() if v > 0},
        }


class ContinuousOpponentPressureAnalyzer:
    """Extracts continuous opponent pressure state across multiple dimensions (§8)."""

    def analyze(
        self,
        econ_state: EconomicState,
        prev_econ_state: Optional[EconomicState] = None
    ) -> OpponentPressureState:
        opp = econ_state.opponent
        if opp is None:
            return OpponentPressureState(confidence=0.1)

        cash = getattr(opp, "cash", 0.0)
        supply_fc = getattr(opp, "supply_forecast", {})
        sale_pr = getattr(opp, "sale_pressure", {})
        buy_pr = getattr(opp, "buy_pressure", {})
        collision = getattr(opp, "market_collision_risk", {})

        # Compute price pressure from supply and current market depth
        price_pr: Dict[str, float] = {}
        for p in PRODUCTS:
            fc = supply_fc.get(p, 0.0)
            if fc > 0:
                price_pr[p] = min(1.0, fc / 6.0)

        # Market activity level: track change in opponent cash or inventory
        activity = 0.0
        confidence = 0.6
        if prev_econ_state is not None and prev_econ_state.opponent is not None:
            prev_cash = getattr(prev_econ_state.opponent, "cash", 0.0)
            delta_cash = abs(cash - prev_cash)
            activity = min(1.0, delta_cash / 400.0)
            confidence = 0.85
        else:
            activity = 0.2

        # Timing pressure: max across sale pressure for high-value goods
        max_sale_p = max([sale_pr.get(p, 0.0) for p in ("STRAWBERRY", "MELON", "TOMATO", "WOOL")] or [0.0])
        timing_p = min(1.0, max_sale_p * 0.9 + activity * 0.3)

        # Terminal pressure: escalates as step approaches 720
        step = econ_state.step
        terminal_p = 0.0
        if step >= 640:
            terminal_p = min(1.0, (step - 640) / 78.0)

        # Route interference: check distance between opponent and our workers
        route_risk = 0.0
        opp_farmer = getattr(opp, "farmer_position", (5, 5))
        for w in econ_state.workers.workers:
            dist = abs(w.position[0] - opp_farmer[0]) + abs(w.position[1] - opp_farmer[1])
            if dist <= 2:
                route_risk = max(route_risk, 0.7)
            elif dist <= 4:
                route_risk = max(route_risk, 0.3)

        return OpponentPressureState(
            market_activity_level=activity,
            observed_inventory=getattr(opp, "observed_mature_crops", {}),
            observed_cash=cash,
            sale_pressure=dict(sale_pr),
            buy_pressure=dict(buy_pr),
            timing_pressure=timing_p,
            shared_resource_collision=dict(collision),
            price_pressure=price_pr,
            route_interference_risk=route_risk,
            terminal_pressure=terminal_p,
            confidence=confidence,
        )


class OpponentPressureModel:
    """Generates plausible rival market actions during forward simulation."""

    def __init__(
        self,
        opponent_state: Optional[OpponentState] = None,
        pressure_state: Optional[OpponentPressureState] = None,
        mode: str = "CALIBRATED_ESTIMATE"
    ) -> None:
        self.state = opponent_state
        self.pressure_state = pressure_state
        self.mode = mode

    def generate_simulated_opponent_market(
        self,
        step: int,
        offset: int
    ) -> List[List[Any]]:
        """Synthesize opponent market orders for simulated step (step + offset)."""
        if self.mode == "CONSERVATIVE_NEUTRAL":
            return []

        orders: List[List[Any]] = []
        for item in PRODUCTS:
            pressure = 0.0
            forecast_qty = 0.0
            if self.pressure_state is not None:
                pressure = self.pressure_state.sale_pressure.get(item, 0.0)
                forecast_qty = self.pressure_state.observed_inventory.get(item, 0)
            elif self.state is not None:
                pressure = self.state.sale_pressure.get(item, 0.0)
                forecast_qty = self.state.supply_forecast.get(item, 0.0)

            if pressure >= 0.5 and forecast_qty >= 1.0:
                if offset == 0:
                    sell_qty = max(1, min(100, int(forecast_qty)))
                    orders.append(["SELL", item, sell_qty])
                elif (step + offset) % 3 == 0:
                    sell_qty = min(3, max(1, int(forecast_qty // 2)))
                    orders.append(["SELL", item, sell_qty])
            elif pressure >= 0.4 and forecast_qty >= 1.0:
                if (step + offset) % 3 == 0:
                    sell_qty = min(3, max(1, int(forecast_qty // 2)))
                    orders.append(["SELL", item, sell_qty])

        return orders[:10]
