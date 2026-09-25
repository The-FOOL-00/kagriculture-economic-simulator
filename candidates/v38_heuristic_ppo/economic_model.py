# SPDX-License-Identifier: MIT
"""Kagriculture V38 Economic Model: Financial Valuation and Opportunity Cost."""

from __future__ import annotations
from typing import Any, Dict, List, Optional
import numpy as np

try:
    from config import PRODUCTS, SEED_PRICES, ANIMAL_COSTS, WAGE_PER_HAND_PER_DAY
    from state_features import EconomicFeatures, PhysicalFeatures
except ImportError:
    from candidates.v38_heuristic_ppo.config import PRODUCTS, SEED_PRICES, ANIMAL_COSTS, WAGE_PER_HAND_PER_DAY
    from candidates.v38_heuristic_ppo.state_features import EconomicFeatures, PhysicalFeatures


class EconomicModel:
    """Evaluates enterprise balance sheet value, liquidity safety, and economic headroom."""
    
    def __init__(self):
        self.rolling_prices: Dict[str, List[float]] = {p: [] for p in PRODUCTS}
        
    def update_market_history(self, prices: Dict[str, float]):
        for p, px in prices.items():
            if p in self.rolling_prices:
                self.rolling_prices[p].append(px)
                if len(self.rolling_prices[p]) > 24:
                    self.rolling_prices[p].pop(0)

    def compute_liquidity_health(self, econ: EconomicFeatures) -> Dict[str, Any]:
        """Calculates liquidity buffer, wage stress, and insolvency risk."""
        runway = econ.days_of_wage_runway
        is_stressed = runway < 2.0 and econ.step < 680
        is_critical = runway < 1.0 and econ.step < 680
        safe_cash_floor = max(150.0, 2.0 * econ.daily_wage_commitment)
        
        return {
            "runway_days": runway,
            "is_stressed": is_stressed,
            "is_critical": is_critical,
            "safe_cash_floor": safe_cash_floor,
            "excess_cash": max(0.0, econ.cash - safe_cash_floor)
        }

    def evaluate_opportunity_cost(
        self,
        econ: EconomicFeatures,
        phys: PhysicalFeatures
    ) -> Dict[str, float]:
        """Estimates marginal return of capital across expansion, labor, and crop choices."""
        health = self.compute_liquidity_health(econ)
        excess = health["excess_cash"]
        
        # 1. Land Expansion ROI
        land_roi = -1.0
        if phys.unlocked_quadrants < 4 and excess >= econ.next_quadrant_cost:
            # Expected revenue from 25 new tiles over remaining days
            days_left = max(0, (718 - econ.step) // 24)
            if days_left >= 10:  # Enough time for at least 1 melon cycle
                land_roi = (days_left * 20.0 * 25) / econ.next_quadrant_cost
                
        # 2. Labor Expansion ROI
        labor_roi = -1.0
        if excess >= econ.next_hire_cost and phys.empty_tiles + phys.weed_tiles > phys.worker_count * 2:
            days_left = max(0, (718 - econ.step) // 24)
            labor_cost = econ.next_hire_cost + days_left * WAGE_PER_HAND_PER_DAY
            expected_labor_val = days_left * 80.0  # Approx daily chore contribution
            labor_roi = expected_labor_val / max(1.0, labor_cost)
            
        # 3. Livestock Expansion ROI
        cow_roi = -1.0
        if excess >= ANIMAL_COSTS["COW"] and phys.empty_pastures > 0 and econ.feed_runway_days >= 3.0:
            days_left = max(0, (718 - econ.step) // 24)
            if days_left >= 6:
                milk_price = econ.spot_prices.get("MILK", 30.0)
                cow_roi = (days_left * milk_price) / ANIMAL_COSTS["COW"]
                
        return {
            "land_roi": land_roi,
            "labor_roi": labor_roi,
            "cow_roi": cow_roi,
            "excess_cash": excess
        }
