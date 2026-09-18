# SPDX-License-Identifier: MIT
"""Resource Opportunity Analyzer (7C, §8, §9)."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from aec.config import ScientificStatus
from aec.events.event_types import EventType
from aec.ir.economic_state import EconomicState
from aec.opportunities.base import Opportunity
from aec.resource.conversions import ConversionDiscoveryEngine
from aec.resource.feed_security import FeedSecurityEngine


class ResourceOpportunityAnalyzer:
    """Detects scarce-resource conflicts, feed security deficits, and inventory conversions (§8, §9)."""

    def __init__(self) -> None:
        self.feed_engine = FeedSecurityEngine()
        self.conversion_engine = ConversionDiscoveryEngine()

    def analyze(
        self,
        econ_state: EconomicState,
        events: List[Any],
        baseline_action: Optional[Dict[str, Any]] = None
    ) -> List[Opportunity]:
        opportunities: List[Opportunity] = []

        # 1. Feed Security Analysis (§5, §6)
        animals = self.feed_engine.extract_livestock(econ_state)
        pipeline_animals = [
            p for p in econ_state.farm.production_pipeline
            if p.item_type == "ANIMAL" and p.subtype in ("COW", "SHEEP", "GOOSE")
        ]
        animals_requiring_feed = max(len(animals), len(pipeline_animals))

        wheat_in_shed = econ_state.farm.get_shed_qty("WHEAT")
        wheat_in_hands = econ_state.farm.carried_inventory.get("WHEAT", 0)
        total_wheat = wheat_in_shed + wheat_in_hands

        if animals_requiring_feed > 0 and total_wheat < animals_requiring_feed:
            deficit = animals_requiring_feed - total_wheat
            wheat_price = econ_state.market.get_price("WHEAT")
            
            # Check terminal feed feasibility (§10, §11, §13)
            is_feasible, reason = self.is_feed_purchase_terminally_feasible(econ_state, animals, deficit)
            if is_feasible:
                opportunities.append(Opportunity(
                    opportunity_id=f"RESOURCE_FEED_DEFICIT_{deficit}",
                    category="RESOURCE",
                    event_trigger=EventType.E2_CASH_DEVIATION,
                    affected_entities=["WHEAT", animals_requiring_feed],
                    estimated_economic_relevance=deficit * 40.0,
                    candidate_transformation_family="EMERGENCY_FEED_PURCHASE",
                    dependency_info={
                        "deficit": deficit,
                        "price": wheat_price,
                        "is_terminally_feasible": True,
                        "terminal_details": getattr(self, "last_terminal_details", {})
                    },
                    required_horizon=min(36, econ_state.remaining_horizon),
                    rationale=f"Wheat stock ({total_wheat}) insufficient for {animals_requiring_feed} head of livestock (COW/SHEEP/GOOSE)",
                    confidence=0.95,
                    scientific_status=ScientificStatus.VERIFIED_SOURCE
                ))

        # 2. Dynamic Inventory Conversion Discovery (§8, §9)
        conversion_paths = self.conversion_engine.discover_conversion_paths(econ_state)
        for path in conversion_paths:
            if path.is_feasible and path.net_value_est > 0:
                dep_info: Dict[str, Any] = {
                    "path_id": path.path_id,
                    "target": path.target_commodity,
                    "cost": path.total_cost_est,
                    "net_value": path.net_value_est,
                    "steps": path.total_steps,
                    "labor_class": path.labor_class.value if hasattr(path, "labor_class") else "AUXILIARY_WORKER_REQUIRED",
                    "opportunity_family": getattr(path, "opportunity_family", "RESOURCE_CONVERSION"),
                    "liquidity_profile": path.liquidity_profile.to_dict() if path.liquidity_profile else {},
                }
                if path.execution_plan is not None:
                    dep_info["execution_plan"] = path.execution_plan.to_dict()
                    dep_info["attribution_info"] = path.execution_plan.attribution_info

                opportunities.append(Opportunity(
                    opportunity_id=f"CONV_{path.path_id}",
                    category="RESOURCE",
                    event_trigger=EventType.E4_MARKET_REGIME_SHIFT,
                    affected_entities=[path.target_commodity],
                    estimated_economic_relevance=float(path.net_value_est),
                    candidate_transformation_family=getattr(path, "opportunity_family", "RESOURCE_CONVERSION"),
                    dependency_info=dep_info,
                    required_horizon=min(36, max(6, path.total_steps // 2)),
                    rationale=f"Feasible conversion path for {path.target_commodity} yielding net est ${path.net_value_est:.1f}",
                    confidence=0.85,
                    scientific_status=ScientificStatus.QUARANTINED
                ))

        return opportunities

    def is_feed_purchase_terminally_feasible(
        self,
        econ_state: EconomicState,
        animals: List[Any],
        deficit: int
    ) -> Tuple[bool, str]:
        """Validates that a feed purchase has realizable downstream purpose before terminal (§10, §11, §13)."""
        from aec.terminal.obligations import FeedTerminalCausalAnalyzer
        analyzer = FeedTerminalCausalAnalyzer()
        is_feasible, purpose_cat, reason, details = analyzer.assess_terminal_feed_purpose(
            econ_state=econ_state,
            animals=animals,
            deficit=deficit
        )
        self.last_terminal_details = details
        return is_feasible, reason
