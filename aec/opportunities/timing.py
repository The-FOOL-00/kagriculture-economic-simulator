# SPDX-License-Identifier: MIT
"""Timing Opportunity Analyzer (7D)."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from aec.config import PRODUCTS, ScientificStatus
from aec.events.event_types import EventType
from aec.ir.economic_state import EconomicState
from aec.opportunities.base import Opportunity


class TimingOpportunityAnalyzer:
    """Proposes timing transformations (sell now vs hold, town-cycle pre-selling)."""

    def analyze(
        self,
        econ_state: EconomicState,
        events: List[Any],
        baseline_action: Optional[Dict[str, Any]] = None
    ) -> List[Opportunity]:
        opportunities: List[Opportunity] = []
        shed = econ_state.farm.shed_inventory
        prices = econ_state.market.current_prices
        steps_to_tick = econ_state.market.steps_to_town_tick
        
        # Check cash commodities available in shed for sale advancement
        cash_items = ("STRAWBERRY", "WOOL", "EGG", "MILK", "MELON")
        for item in cash_items:
            qty = shed.get(item, 0)
            if qty >= 2:
                cur_price = prices.get(item, 100)
                opp_pressure = econ_state.opponent.get_supply_pressure(item)
                
                # If opponent has imminent supply pressure, selling now is advantageous
                if opp_pressure > 0.5:
                    opportunities.append(Opportunity(
                        opportunity_id=f"TIMING_PREEMPT_SELL_{item}_{qty}",
                        category="TIMING",
                        event_trigger=EventType.E5_OPPONENT_SUPPLY_SHOCK,
                        affected_entities=[item, qty],
                        estimated_economic_relevance=qty * cur_price * 0.15,
                        candidate_transformation_family="OPPONENT_PREEMPT_SELL",
                        dependency_info={"item": item, "qty": qty, "price": cur_price},
                        required_horizon=12,
                        rationale=f"Preempt rival supply drop: {qty} {item} in shed before rival sells",
                        confidence=0.85,
                        scientific_status=ScientificStatus.PLAUSIBLE_UNPROVEN
                    ))

        return opportunities
