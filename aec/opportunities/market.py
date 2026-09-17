# SPDX-License-Identifier: MIT
"""Market Opportunity Analyzer (7E)."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from aec.config import ScientificStatus
from aec.events.event_types import EventType
from aec.ir.economic_state import EconomicState
from aec.opportunities.base import Opportunity


class MarketOpportunityAnalyzer:
    """Detects market order interleaving, front-loading, and town-cycle opportunities."""

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
            # Check if any SELL order is preceded by non-SELL orders (HIRE, BUY_LAND, BUY_SEED, BUY_ANIMAL, BUY_PRODUCT)
            has_sell = False
            seen_non_sell = False
            has_suboptimal_order = False
            for order in market_orders:
                if isinstance(order, (list, tuple)) and order:
                    op = order[0]
                    if op == "SELL":
                        has_sell = True
                        if seen_non_sell:
                            has_suboptimal_order = True
                    elif op in ("HIRE", "BUY_LAND", "BUY_SEED", "BUY_ANIMAL", "BUY_PRODUCT"):
                        seen_non_sell = True

            if has_sell and has_suboptimal_order:
                opportunities.append(Opportunity(
                    opportunity_id=f"MARKET_FRONTLOAD_STEP_{econ_state.step}",
                    category="MARKET",
                    event_trigger=None,
                    affected_entities=["MARKET_ORDERS"],
                    estimated_economic_relevance=80.0,
                    candidate_transformation_family="FRONTLOAD_ORDERS",
                    dependency_info={"original_orders": market_orders},
                    required_horizon=4,
                    rationale="Interleave SELL orders to index 0 to capture pre-impact quoting priority",
                    confidence=1.0,
                    scientific_status=ScientificStatus.VERIFIED_SOURCE
                ))

        return opportunities
