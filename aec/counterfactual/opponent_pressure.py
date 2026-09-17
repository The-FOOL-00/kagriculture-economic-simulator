# SPDX-License-Identifier: MIT
"""Opponent Market and Physical Pressure Modeling in Counterfactual Simulation."""

from __future__ import annotations

from typing import Any, Dict, List

from aec.config import PRODUCTS
from aec.ir.opponent_state import OpponentState


class OpponentPressureModel:
    """Generates plausible rival market actions during forward simulation."""

    def __init__(self, opponent_state: OpponentState) -> None:
        self.state = opponent_state

    def generate_simulated_opponent_market(
        self,
        step: int,
        offset: int
    ) -> List[List[Any]]:
        """Synthesize plausible opponent market orders for simulated step (step + offset)."""
        orders: List[List[Any]] = []
        
        # Check products where opponent exerts high sale pressure
        for item in PRODUCTS:
            pressure = self.state.sale_pressure.get(item, 0.0)
            forecast_qty = self.state.supply_forecast.get(item, 0.0)
            
            # If significant pressure, rival sells 1-2 units when step aligns with drop cycle
            if pressure >= 0.4 and forecast_qty >= 1.0:
                # Disperse sales across simulation steps
                if (step + offset) % 3 == 0:
                    sell_qty = min(3, max(1, int(forecast_qty // 2)))
                    orders.append(["SELL", item, sell_qty])

        return orders[:10]
