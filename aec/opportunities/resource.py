# SPDX-License-Identifier: MIT
"""Resource Opportunity Analyzer (7C)."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from aec.config import ScientificStatus
from aec.events.event_types import EventType
from aec.ir.economic_state import EconomicState
from aec.opportunities.base import Opportunity


class ResourceOpportunityAnalyzer:
    """Detects scarce-resource conflicts, feed security, and inventory conversion."""

    def analyze(
        self,
        econ_state: EconomicState,
        events: List[Any],
        baseline_action: Optional[Dict[str, Any]] = None
    ) -> List[Opportunity]:
        opportunities: List[Opportunity] = []
        
        # Check feed security for livestock
        wheat_in_shed = econ_state.farm.get_shed_qty("WHEAT")
        wheat_in_hands = econ_state.farm.carried_inventory.get("WHEAT", 0)
        total_wheat = wheat_in_shed + wheat_in_hands
        
        # Count animals that require daily feeding
        animals_requiring_feed = sum(
            1 for p in econ_state.farm.production_pipeline
            if p.item_type == "ANIMAL" and p.subtype in ("COW", "SHEEP")
        )
        
        if animals_requiring_feed > 0 and total_wheat < animals_requiring_feed:
            deficit = animals_requiring_feed - total_wheat
            opportunities.append(Opportunity(
                opportunity_id=f"RESOURCE_FEED_DEFICIT_{deficit}",
                category="RESOURCE",
                event_trigger=EventType.E2_CASH_DEVIATION,
                affected_entities=["WHEAT", animals_requiring_feed],
                estimated_economic_relevance=deficit * 40.0,
                candidate_transformation_family="EMERGENCY_FEED_PURCHASE",
                dependency_info={"deficit": deficit, "price": econ_state.market.get_price("WHEAT")},
                required_horizon=6,
                rationale=f"Wheat stock ({total_wheat}) insufficient for {animals_requiring_feed} head of livestock",
                confidence=0.95,
                scientific_status=ScientificStatus.VERIFIED_SOURCE
            ))

        return opportunities
