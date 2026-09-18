# SPDX-License-Identifier: MIT
"""Standard Opportunity Registry and Contract Lifecycle (§23, §24)."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

from aec.config import ScientificStatus
from aec.opportunities.base import Opportunity


@dataclass
class OpportunityFamilySpec:
    """Explicit declaration of an opportunity family's contracts and requirements (§23)."""
    name: str
    category: str                                   # "LABOR", "ROUTE", "RESOURCE", "TIMING", "MARKET", "TERMINAL"
    detector_cls: Any
    dependencies: List[str] = field(default_factory=list)
    worker_requirements: str = "ANY"                # "PRIMARY_ONLY", "AUXILIARY_ONLY", "ANY", "NONE"
    economic_model: str = "EXACT_COUNTERFACTUAL"    # "LOCAL_MARGINAL", "EXACT_COUNTERFACTUAL"
    patch_builder_cls: Optional[Any] = None
    counterfactual_required: bool = True
    terminal_sensitive: bool = False
    safety_invariants: List[str] = field(default_factory=list)
    scientific_status: ScientificStatus = ScientificStatus.PLAUSIBLE_UNPROVEN
    is_live_eligible: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "category": self.category,
            "worker_requirements": self.worker_requirements,
            "economic_model": self.economic_model,
            "cf_required": self.counterfactual_required,
            "status": self.scientific_status.value,
            "live_eligible": self.is_live_eligible,
        }


class OpportunityRegistry:
    """Central registry maintaining all architectural opportunity families (§23).
    
    Prevents the architecture from degenerating into fragmented special cases.
    """

    def __init__(self) -> None:
        self._families: Dict[str, OpportunityFamilySpec] = {}

    @classmethod
    def default_registry(cls) -> OpportunityRegistry:
        return GLOBAL_OPPORTUNITY_REGISTRY

    def register(self, spec: OpportunityFamilySpec) -> None:
        self._families[spec.name] = spec

    def get(self, name: str) -> Optional[OpportunityFamilySpec]:
        return self._families.get(name)

    def get_spec(self, name: str) -> Optional[OpportunityFamilySpec]:
        return self._families.get(name)

    def list_families(self) -> List[OpportunityFamilySpec]:
        return list(self._families.values())

    def is_live_eligible(self, name: str) -> bool:
        spec = self.get(name)
        return spec.is_live_eligible if spec else False

    def get_status(self, name: str) -> ScientificStatus:
        spec = self.get(name)
        return spec.scientific_status if spec else ScientificStatus.QUARANTINED


# Global Singleton Registry
GLOBAL_OPPORTUNITY_REGISTRY = OpportunityRegistry()


def register_default_families() -> None:
    """Register all 14 architectural opportunity families into the global registry (§23)."""
    GLOBAL_OPPORTUNITY_REGISTRY.register(OpportunityFamilySpec(
        name="DEPENDENCY_AWARE_MARKET_TIMING",
        category="MARKET",
        detector_cls=None,
        worker_requirements="NONE",
        counterfactual_required=True,
        scientific_status=ScientificStatus.EXPERIMENTAL,
        is_live_eligible=True,
    ))
    GLOBAL_OPPORTUNITY_REGISTRY.register(OpportunityFamilySpec(
        name="DYNAMIC_SHADOW_HARVEST",
        category="LABOR",
        detector_cls=None,
        worker_requirements="ANY",
        counterfactual_required=True,
        scientific_status=ScientificStatus.EXPERIMENTAL,
        is_live_eligible=False,  # Candidate validated offline
    ))
    GLOBAL_OPPORTUNITY_REGISTRY.register(OpportunityFamilySpec(
        name="TERMINAL_HARVEST_SWEEP",
        category="TERMINAL",
        detector_cls=None,
        worker_requirements="ANY",
        counterfactual_required=True,
        terminal_sensitive=True,
        scientific_status=ScientificStatus.EXPERIMENTAL,
        is_live_eligible=False,
    ))
    GLOBAL_OPPORTUNITY_REGISTRY.register(OpportunityFamilySpec(
        name="ROUTE_COMPRESSION",
        category="ROUTE",
        detector_cls=None,
        worker_requirements="ANY",
        counterfactual_required=True,
        scientific_status=ScientificStatus.PLAUSIBLE_UNPROVEN,
        is_live_eligible=False,
    ))
    GLOBAL_OPPORTUNITY_REGISTRY.register(OpportunityFamilySpec(
        name="CARGO_FERRY",
        category="LABOR",
        detector_cls=None,
        worker_requirements="AUXILIARY_ONLY",
        counterfactual_required=True,
        scientific_status=ScientificStatus.PLAUSIBLE_UNPROVEN,
        is_live_eligible=False,
    ))
    GLOBAL_OPPORTUNITY_REGISTRY.register(OpportunityFamilySpec(
        name="RESOURCE_CONVERSION",
        category="RESOURCE",
        detector_cls=None,
        worker_requirements="AUXILIARY_ONLY",
        counterfactual_required=True,
        scientific_status=ScientificStatus.QUARANTINED,
        is_live_eligible=False,
    ))
    GLOBAL_OPPORTUNITY_REGISTRY.register(OpportunityFamilySpec(
        name="SHOP_ARBITRAGE",
        category="MARKET",
        detector_cls=None,
        worker_requirements="NONE",
        counterfactual_required=True,
        scientific_status=ScientificStatus.PLAUSIBLE_UNPROVEN,
        is_live_eligible=False,
    ))
    GLOBAL_OPPORTUNITY_REGISTRY.register(OpportunityFamilySpec(
        name="PRODUCTION_ARBITRAGE",
        category="RESOURCE",
        detector_cls=None,
        worker_requirements="ANY",
        counterfactual_required=True,
        scientific_status=ScientificStatus.PLAUSIBLE_UNPROVEN,
        is_live_eligible=False,
    ))
    GLOBAL_OPPORTUNITY_REGISTRY.register(OpportunityFamilySpec(
        name="TERMINAL_CONVERSION",
        category="TERMINAL",
        detector_cls=None,
        worker_requirements="ANY",
        counterfactual_required=True,
        terminal_sensitive=True,
        scientific_status=ScientificStatus.PLAUSIBLE_UNPROVEN,
        is_live_eligible=False,
    ))
    GLOBAL_OPPORTUNITY_REGISTRY.register(OpportunityFamilySpec(
        name="OPPONENT_PREEMPT_SELL",
        category="MARKET",
        detector_cls=None,
        worker_requirements="NONE",
        counterfactual_required=True,
        scientific_status=ScientificStatus.PLAUSIBLE_UNPROVEN,
        is_live_eligible=False,
    ))
    GLOBAL_OPPORTUNITY_REGISTRY.register(OpportunityFamilySpec(
        name="EMERGENCY_RECOVERY",
        category="RESOURCE",
        detector_cls=None,
        worker_requirements="ANY",
        counterfactual_required=True,
        scientific_status=ScientificStatus.PLAUSIBLE_UNPROVEN,
        is_live_eligible=False,
    ))
    GLOBAL_OPPORTUNITY_REGISTRY.register(OpportunityFamilySpec(
        name="TOWN_CYCLE",
        category="TIMING",
        detector_cls=None,
        worker_requirements="NONE",
        counterfactual_required=True,
        scientific_status=ScientificStatus.PLAUSIBLE_UNPROVEN,
        is_live_eligible=False,
    ))
    GLOBAL_OPPORTUNITY_REGISTRY.register(OpportunityFamilySpec(
        name="TERMINAL_LIQUIDATION",
        category="TERMINAL",
        detector_cls=None,
        worker_requirements="NONE",
        counterfactual_required=True,
        terminal_sensitive=True,
        scientific_status=ScientificStatus.VERIFIED_SOURCE,
        is_live_eligible=True,
    ))
    GLOBAL_OPPORTUNITY_REGISTRY.register(OpportunityFamilySpec(
        name="PHASE_SHUTDOWN",
        category="TERMINAL",
        detector_cls=None,
        worker_requirements="NONE",
        counterfactual_required=False,
        terminal_sensitive=True,
        scientific_status=ScientificStatus.VERIFIED_SOURCE,
        is_live_eligible=True,
    ))


register_default_families()
