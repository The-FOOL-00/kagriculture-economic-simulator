# SPDX-License-Identifier: MIT
"""Opportunity Engine Analyzers for AEC (§23, §24)."""

from typing import Any, Dict, Iterable, List, Optional, Set

from aec.config import AECConfig, ENABLED_FOUNDATION_MECHANISMS
from aec.counterfactual.opponent_pressure import OpponentPressureState
from aec.events.event_types import Event
from aec.ir.economic_state import EconomicState
from aec.opportunities.arbitrage import ProductionArbitrageDetector, ShopArbitrageDetector
from aec.opportunities.base import Opportunity
from aec.opportunities.cargo_ferry import CargoFerryDetector
from aec.opportunities.emergency import EmergencyRecoveryDetector
from aec.opportunities.labor import LaborOpportunityAnalyzer
from aec.opportunities.market import MarketOpportunityAnalyzer
from aec.opportunities.preemption import OpponentPreemptionDetector
from aec.opportunities.registry import GLOBAL_OPPORTUNITY_REGISTRY
from aec.opportunities.resource import ResourceOpportunityAnalyzer
from aec.opportunities.route import RouteOpportunityAnalyzer
from aec.opportunities.route_compression import RouteCompressionDetector
from aec.opportunities.terminal import TerminalOpportunityAnalyzer
from aec.opportunities.timing import TimingOpportunityAnalyzer
from aec.opportunities.town_cycle import TownCycleSignalDetector
from aec.terminal.conversion import TerminalConversionDetector


class OpportunityEngine:
    """Orchestrates all opportunity analyzers across categories with explicit mechanism gating (§7, §9, §23)."""

    def __init__(
        self,
        config: Optional[AECConfig] = None,
        enabled_mechanisms: Optional[Iterable[str]] = None,
        mode: str = "frozen"
    ) -> None:
        if config is not None:
            self.enabled_mechanisms: Set[str] = set(config.enabled_mechanisms)
            self.mode: str = "frozen" if config.frozen_mode else "development"
        elif enabled_mechanisms is not None:
            self.enabled_mechanisms = set(enabled_mechanisms)
            self.mode = mode
        else:
            self.enabled_mechanisms = set(ENABLED_FOUNDATION_MECHANISMS)
            self.mode = mode

        # Foundation analyzers
        self.labor_analyzer = LaborOpportunityAnalyzer()
        self.route_analyzer = RouteOpportunityAnalyzer()
        self.resource_analyzer = ResourceOpportunityAnalyzer()
        self.timing_analyzer = TimingOpportunityAnalyzer()
        self.market_analyzer = MarketOpportunityAnalyzer()
        self.terminal_analyzer = TerminalOpportunityAnalyzer()

        # Phase 007 expanded opportunity analyzers (§14-§22)
        self.route_compression_detector = RouteCompressionDetector()
        self.cargo_ferry_detector = CargoFerryDetector()
        self.production_arbitrage_detector = ProductionArbitrageDetector()
        self.shop_arbitrage_detector = ShopArbitrageDetector()
        self.terminal_conversion_detector = TerminalConversionDetector()
        self.opponent_preemption_detector = OpponentPreemptionDetector()
        self.emergency_recovery_detector = EmergencyRecoveryDetector()
        self.town_cycle_detector = TownCycleSignalDetector()

        # Telemetry / quarantine tracking per step
        self.last_quarantined_opportunities: List[Opportunity] = []

    def detect_opportunities(
        self,
        econ_state: EconomicState,
        events: List[Event],
        baseline_action: Optional[Dict[str, Any]] = None,
        max_opportunities: int = 16,
        config: Optional[AECConfig] = None,
        pressure_state: Optional[OpponentPressureState] = None,
    ) -> List[Opportunity]:
        enabled = set(config.enabled_mechanisms) if config is not None else self.enabled_mechanisms
        is_frozen = config.frozen_mode if config is not None else (self.mode == "frozen")

        raw_opportunities: List[Opportunity] = []

        # 1. Foundation Analyzers
        raw_opportunities.extend(self.route_analyzer.analyze(econ_state, events, baseline_action))
        raw_opportunities.extend(self.market_analyzer.analyze(econ_state, events, baseline_action))
        raw_opportunities.extend(self.terminal_analyzer.analyze(econ_state, events, baseline_action))
        raw_opportunities.extend(self.resource_analyzer.analyze(econ_state, events, baseline_action))
        raw_opportunities.extend(self.labor_analyzer.analyze(econ_state, events, baseline_action))
        raw_opportunities.extend(self.timing_analyzer.analyze(econ_state, events, baseline_action))

        # 2. Phase 007 Analyzers
        raw_opportunities.extend(self.route_compression_detector.detect(econ_state, worker_id=0))
        raw_opportunities.extend(self.cargo_ferry_detector.detect(econ_state, baseline_action))
        raw_opportunities.extend(self.production_arbitrage_detector.detect(econ_state))
        raw_opportunities.extend(self.shop_arbitrage_detector.detect(econ_state))
        raw_opportunities.extend(self.terminal_conversion_detector.detect(econ_state))
        raw_opportunities.extend(self.opponent_preemption_detector.detect(econ_state, pressure_state))
        raw_opportunities.extend(self.emergency_recovery_detector.detect(econ_state, baseline_action))

        # Layer 1 Mechanism Filtering (§9, §34)
        actionable: List[Opportunity] = []
        quarantined: List[Opportunity] = []

        for opp in raw_opportunities:
            fam = opp.candidate_transformation_family
            if is_frozen:
                if fam in enabled or fam == "LOCAL_WEED_DIG":
                    actionable.append(opp)
                else:
                    quarantined.append(opp)
            else:
                actionable.append(opp)

        self.last_quarantined_opportunities = quarantined

        # Sort by economic relevance descending, bounded by max_opportunities
        actionable.sort(key=lambda o: -o.estimated_economic_relevance)
        return actionable[:max_opportunities]

    def get_quarantined_proposals_by_mechanism(self) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for opp in self.last_quarantined_opportunities:
            fam = opp.candidate_transformation_family
            counts[fam] = counts.get(fam, 0) + 1
        return counts


__all__ = [
    "Opportunity",
    "OpportunityEngine",
    "LaborOpportunityAnalyzer",
    "RouteOpportunityAnalyzer",
    "ResourceOpportunityAnalyzer",
    "TimingOpportunityAnalyzer",
    "MarketOpportunityAnalyzer",
    "TerminalOpportunityAnalyzer",
    "RouteCompressionDetector",
    "CargoFerryDetector",
    "ProductionArbitrageDetector",
    "ShopArbitrageDetector",
    "TerminalConversionDetector",
    "OpponentPreemptionDetector",
    "EmergencyRecoveryDetector",
    "TownCycleSignalDetector",
]
