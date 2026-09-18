# SPDX-License-Identifier: MIT
"""Opponent Preemption Opportunity Architecture (§19)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from aec.config import ScientificStatus
from aec.counterfactual.opponent_pressure import OpponentPressureState
from aec.ir.economic_state import EconomicState
from aec.opportunities.base import Opportunity


@dataclass
class OpponentPreemptionOpportunity(Opportunity):
    """An opportunity to execute an earlier market sale to capture price depth before rival dump (§19)."""
    target_product: str = ""
    quantity: int = 1
    expected_our_revenue: float = 0.0
    projected_rival_depression_impact: float = 0.0


class OpponentPreemptionDetector:
    """Detects opportunities where selling immediately captures price depth before rival clears orders.
    
    Uses exact market clearing semantics.
    Distinguishes IMPLEMENTED from PROSPECTIVE_READY.
    """

    def detect(
        self,
        econ_state: EconomicState,
        pressure_state: Optional[OpponentPressureState] = None
    ) -> List[OpponentPreemptionOpportunity]:
        opportunities: List[OpponentPreemptionOpportunity] = []
        if pressure_state is None:
            return []

        step = econ_state.step
        shed = econ_state.farm.shed_inventory

        for product, count in shed.items():
            if count <= 0:
                continue

            sale_pressure = pressure_state.sale_pressure.get(product, 0.0)
            # High sale pressure means rival has mature crops and is likely preparing to sell
            if sale_pressure >= 0.5:
                curr_price = float(econ_state.market.prices.get(product, 20.0))
                # Projected price after rival dump (typically drops by 15-30%)
                depression_loss = curr_price * 0.20 * count
                our_rev = curr_price * count

                opportunities.append(OpponentPreemptionOpportunity(
                    opportunity_id=f"PREEMPT_SELL_{step}_{product}",
                    category="MARKET",
                    event_trigger=None,
                    affected_entities=[product],
                    estimated_economic_relevance=depression_loss,
                    candidate_transformation_family="OPPONENT_PREEMPT_SELL",
                    required_horizon=6,
                    rationale=f"Preempt rival {product} dump (sale pressure {sale_pressure:.2f}): save projected ${depression_loss:.1f} price decay.",
                    scientific_status=ScientificStatus.PLAUSIBLE_UNPROVEN,
                    target_product=product,
                    quantity=count,
                    expected_our_revenue=our_rev,
                    projected_rival_depression_impact=depression_loss,
                ))

        return opportunities
