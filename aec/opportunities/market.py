# SPDX-License-Identifier: MIT
"""Market Opportunity Analyzer (7E)."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from aec.config import ScientificStatus
from aec.events.event_types import EventType
from aec.ir.economic_state import EconomicState
from aec.opportunities.base import Opportunity


from aec.market.transformations import transform_dependency_aware_market_timing


class MarketOpportunityAnalyzer:
    """Detects causal market order timing and dependency-aware interleaving opportunities."""

    def analyze(
        self,
        econ_state: EconomicState,
        events: List[Any],
        baseline_action: Optional[Dict[str, Any]] = None
    ) -> List[Opportunity]:
        opportunities: List[Opportunity] = []
        if not baseline_action:
            return opportunities

        market_orders = baseline_action.get("market", [])
        if len(market_orders) >= 2:
            reordered, _ = transform_dependency_aware_market_timing(market_orders, econ_state)
            if reordered != market_orders:
                opportunities.append(Opportunity(
                    opportunity_id=f"MARKET_TIMING_STEP_{econ_state.step}",
                    category="MARKET",
                    event_trigger=None,
                    affected_entities=["MARKET_ORDERS"],
                    estimated_economic_relevance=80.0,
                    candidate_transformation_family="DEPENDENCY_AWARE_MARKET_TIMING",
                    dependency_info={"original_orders": market_orders, "reordered": reordered},
                    required_horizon=4,
                    rationale="Reorder uncoupled SELL orders ahead of capital expenditures while preserving same-asset order dependencies",
                    confidence=1.0,
                    scientific_status=ScientificStatus.EXPERIMENTAL
                ))

        return opportunities
