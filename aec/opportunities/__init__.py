# SPDX-License-Identifier: MIT
"""Opportunity Engine Analyzers for AEC."""

from typing import Any, Dict, List, Optional

from aec.events.event_types import Event
from aec.ir.economic_state import EconomicState
from aec.opportunities.base import Opportunity
from aec.opportunities.labor import LaborOpportunityAnalyzer
from aec.opportunities.route import RouteOpportunityAnalyzer
from aec.opportunities.resource import ResourceOpportunityAnalyzer
from aec.opportunities.timing import TimingOpportunityAnalyzer
from aec.opportunities.market import MarketOpportunityAnalyzer
from aec.opportunities.terminal import TerminalOpportunityAnalyzer


class OpportunityEngine:
    """Orchestrates all opportunity analyzers across categories (§7, §9)."""

    def __init__(self) -> None:
        self.labor_analyzer = LaborOpportunityAnalyzer()
        self.route_analyzer = RouteOpportunityAnalyzer()
        self.resource_analyzer = ResourceOpportunityAnalyzer()
        self.timing_analyzer = TimingOpportunityAnalyzer()
        self.market_analyzer = MarketOpportunityAnalyzer()
        self.terminal_analyzer = TerminalOpportunityAnalyzer()

    def detect_opportunities(
        self,
        econ_state: EconomicState,
        events: List[Event],
        baseline_action: Optional[Dict[str, Any]] = None,
        max_opportunities: int = 16
    ) -> List[Opportunity]:
        opportunities: List[Opportunity] = []
        
        # Run analyzers
        opportunities.extend(self.route_analyzer.analyze(econ_state, events, baseline_action))
        opportunities.extend(self.market_analyzer.analyze(econ_state, events, baseline_action))
        opportunities.extend(self.terminal_analyzer.analyze(econ_state, events, baseline_action))
        opportunities.extend(self.resource_analyzer.analyze(econ_state, events, baseline_action))
        opportunities.extend(self.labor_analyzer.analyze(econ_state, events, baseline_action))
        opportunities.extend(self.timing_analyzer.analyze(econ_state, events, baseline_action))

        # Sort by economic relevance descending, bounded by max_opportunities
        opportunities.sort(key=lambda o: -o.estimated_economic_relevance)
        return opportunities[:max_opportunities]


__all__ = [
    "Opportunity",
    "OpportunityEngine",
    "LaborOpportunityAnalyzer",
    "RouteOpportunityAnalyzer",
    "ResourceOpportunityAnalyzer",
    "TimingOpportunityAnalyzer",
    "MarketOpportunityAnalyzer",
    "TerminalOpportunityAnalyzer",
]
