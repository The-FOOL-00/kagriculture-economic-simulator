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
from aec.opportunities.terminal_conversion import TerminalConversionDetector
from aec.opportunities.asset_holding import AssetHoldingOpportunityAnalyzer
from aec.opportunities.multiworker_harvest import MultiworkerHarvestDetector


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

        # Phase 015 persistent asset holding analyzer
        self.asset_holding_analyzer = AssetHoldingOpportunityAnalyzer()

        # Phase 020 Multi-Worker Harvest Synchronization detector
        self.multiworker_harvest_detector = MultiworkerHarvestDetector()

        # Telemetry / quarantine tracking per step
        self.last_quarantined_opportunities: List[Opportunity] = []
        self.last_reservation_telemetry: Optional[Any] = None
        self.last_firing_log: List[Dict[str, Any]] = []

    def detect_opportunities(
        self,
        econ_state: EconomicState,
        events: List[Event],
        baseline_action: Optional[Dict[str, Any]] = None,
        max_opportunities: int = 16,
        config: Optional[AECConfig] = None,
        pressure_state: Optional[OpponentPressureState] = None,
        v3_tape: Optional[List[Dict[str, Any]]] = None,
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
        raw_opportunities.extend(self.town_cycle_detector.detect(econ_state, baseline_action))

        # 3. Phase 015 Capability A: Asset-Holding Valuation Trigger
        trigger_active = (
            "ASSET_HOLDING_VALUATION_TRIGGER" in enabled
            or getattr(config, "enable_asset_holding_trigger", False)
            or not is_frozen
        )
        if trigger_active:
            trigger_options = {
                "persistence": bool(
                    config is not None
                    and getattr(config, "enable_trigger_persistence", False)
                ),
                "min_premium": (
                    getattr(config, "trigger_min_premium_class_a", None)
                    if config is not None else None
                ),
                "separation": bool(
                    config is not None
                    and getattr(config, "enable_tape_separation", False)
                ),
            }
            raw_opportunities.extend(
                self.asset_holding_analyzer.analyze(
                    econ_state, events, baseline_action, pressure_state,
                    trigger_options=trigger_options, v3_tape=v3_tape,
                )
            )
        self.last_firing_log = list(
            getattr(self.asset_holding_analyzer, "last_firing_log", []) or []
        )

        # 4. Phase 020: Multi-Worker Harvest Synchronization
        if (
            "MULTIWORKER_HARVEST_SYNCHRONIZATION" in enabled
            or getattr(config, "enable_multiworker_harvest", False)
            or not is_frozen
        ):
            raw_opportunities.extend(self.multiworker_harvest_detector.detect(econ_state, baseline_action))

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

        # Phase 018 Repair A: funnel reservation at the opportunity truncation.
        # Gated; legacy path executes verbatim when disabled.
        self.last_reservation_telemetry = None
        if config is not None and getattr(config, "enable_funnel_reservation", False):
            from aec.funnel.reservation import FunnelReservationPolicy, apply_reservation
            policy = FunnelReservationPolicy(
                enabled=True,
                reserved_fraction=float(
                    getattr(config, "funnel_reserved_fraction", 0.25) or 0.25
                ),
            )
            selected, res_telem = apply_reservation(
                actionable, max_opportunities, policy, site="OPPORTUNITY_TRUNCATION"
            )
            self.last_reservation_telemetry = res_telem
            return selected
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
    "AssetHoldingOpportunityAnalyzer",
]
