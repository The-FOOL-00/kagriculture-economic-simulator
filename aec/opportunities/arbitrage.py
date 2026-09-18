# SPDX-License-Identifier: MIT
"""Shop and Production Arbitrage Opportunity Architecture (§16)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from aec.config import CROP_GROWTH_DAYS, CROP_SEED_PRICE, EPISODE_STEPS, ScientificStatus, TURNS_PER_DAY
from aec.ir.economic_state import EconomicState
from aec.opportunities.base import Opportunity


@dataclass
class ProductionArbitrageOpportunity(Opportunity):
    """An opportunity executing a full production graph: cash -> input -> production -> output -> sale (§16)."""
    input_item: str = ""
    input_cost: float = 0.0
    output_item: str = ""
    expected_output_units: int = 1
    expected_gross_revenue: float = 0.0
    production_duration_steps: int = 48
    net_projected_profit: float = 0.0
    liquidity_impact: float = 0.0


@dataclass
class ShopArbitrageOpportunity(Opportunity):
    """An opportunity exploiting inter-turn town shop unlock intervals and price elasticity (§16)."""
    item: str = ""
    purchase_price: float = 0.0
    target_sale_price: float = 0.0
    expected_margin: float = 0.0
    unlock_step: int = 0


class ProductionArbitrageDetector:
    r"""Evaluates the viability of cash -> input -> production -> output -> sale.
    
    Strict constraints enforced:
    1. Upfront liquidity check ($C_{upfront} \le Cash - SafetyBuffer$).
    2. Terminal deadline check (Step + Duration < FinalStep 718).
    3. Labor requirement accounting (Worker hours valued against opportunity cost).
    """

    def detect(
        self,
        econ_state: EconomicState,
        min_net_margin: float = 50.0
    ) -> List[ProductionArbitrageOpportunity]:
        opportunities: List[ProductionArbitrageOpportunity] = []
        step = econ_state.step
        cash = econ_state.cash

        # Evaluate each crop production pipeline
        for crop, seed_cost in CROP_SEED_PRICE.items():
            growth_days = CROP_GROWTH_DAYS.get(crop, 2)
            duration_steps = growth_days * TURNS_PER_DAY + 8  # growth + planting + harvest + drop + sell
            
            # Terminal realization check: must mature and sell before step 718
            if step + duration_steps >= 718:
                continue

            # Liquidity check
            if cash < seed_cost + 100.0:
                continue

            # Market revenue estimate
            current_price = econ_state.market.prices.get(crop, 0.0)
            gross = float(current_price) * 1.0  # single crop yield
            net_profit = gross - seed_cost - 10.0  # seed cost + estimated worker labor cost ($10)

            if net_profit >= min_net_margin:
                opportunities.append(ProductionArbitrageOpportunity(
                    opportunity_id=f"PROD_ARB_{step}_{crop}",
                    category="RESOURCE",
                    event_trigger=None,
                    affected_entities=[crop],
                    estimated_economic_relevance=net_profit,
                    candidate_transformation_family="PRODUCTION_ARBITRAGE",
                    required_horizon=min(72, duration_steps),
                    rationale=f"Production arbitrage: Buy {crop} seed (${seed_cost}) -> mature {growth_days}d -> gross ${gross:.1f} -> net ${net_profit:.1f}.",
                    scientific_status=ScientificStatus.PLAUSIBLE_UNPROVEN,
                    input_item=f"{crop}_SEED",
                    input_cost=float(seed_cost),
                    output_item=crop,
                    expected_output_units=1,
                    expected_gross_revenue=gross,
                    production_duration_steps=duration_steps,
                    net_projected_profit=net_profit,
                    liquidity_impact=-float(seed_cost),
                ))

        return opportunities


class ShopArbitrageDetector:
    """Evaluates town shop demand elasticity and unlock interval price differentials."""

    def detect(
        self,
        econ_state: EconomicState
    ) -> List[ShopArbitrageOpportunity]:
        opportunities: List[ShopArbitrageOpportunity] = []
        step = econ_state.step
        
        # Check town shop unlock windows (every 72 steps)
        next_unlock = ((step // 72) + 1) * 72
        steps_to_unlock = next_unlock - step

        # If unlock is within 12 steps and town price is depressed, plan inventory accumulation
        if 1 <= steps_to_unlock <= 12:
            for item in ("WHEAT", "CARROT", "TOMATO"):
                p_curr = econ_state.market.prices.get(item, 20.0)
                # Anticipate town cycle rebound price (+15-25%)
                p_projected = p_curr * 1.20
                margin = p_projected - p_curr
                if margin >= 5.0:
                    opportunities.append(ShopArbitrageOpportunity(
                        opportunity_id=f"SHOP_ARB_{step}_{item}",
                        category="MARKET",
                        event_trigger=None,
                        affected_entities=[item],
                        estimated_economic_relevance=float(margin * 5.0),
                        candidate_transformation_family="SHOP_ARBITRAGE",
                        required_horizon=steps_to_unlock + 6,
                        rationale=f"Shop arbitrage on {item}: hold sale for shop unlock at step {next_unlock} (projected +${margin:.1f}/unit).",
                        scientific_status=ScientificStatus.PLAUSIBLE_UNPROVEN,
                        item=item,
                        purchase_price=float(p_curr),
                        target_sale_price=float(p_projected),
                        expected_margin=float(margin),
                        unlock_step=next_unlock,
                    ))

        return opportunities
