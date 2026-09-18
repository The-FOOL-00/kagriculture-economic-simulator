# SPDX-License-Identifier: MIT
"""Opportunity Abstraction for AEC."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from aec.config import ScientificStatus
from aec.events.event_types import EventType


@dataclass
class Opportunity:
    """A detected economic opportunity that can be compiled into a candidate patch.
    
    Opportunities propose candidate transformations; they do NOT alter game actions directly.
    """
    opportunity_id: str
    category: str                               # "LABOR", "ROUTE", "RESOURCE", "TIMING", "MARKET", "TERMINAL"
    event_trigger: Optional[EventType]
    affected_entities: List[Any]                 # Worker IDs, item names, or coordinate tuples
    estimated_economic_relevance: float         # Dynamic marginal value / utility estimate
    candidate_transformation_family: str        # e.g., "FRONTLOAD_SELL", "LOCAL_DIG_REPAIR"
    dependency_info: Dict[str, Any] = field(default_factory=dict)
    required_horizon: int = 12                  # Horizon needed to evaluate consequences
    rationale: str = ""
    confidence: float = 1.0
    scientific_status: ScientificStatus = ScientificStatus.PLAUSIBLE_UNPROVEN

    @property
    def mechanism_family(self) -> str:
        return self.candidate_transformation_family

    @property
    def estimated_net_delta(self) -> float:
        return self.estimated_economic_relevance

    @property
    def worker_id(self) -> int:
        for e in self.affected_entities:
            if isinstance(e, int):
                return e
        return 0

    @property
    def target_pos(self) -> Tuple[int, int]:
        if "target_pos" in self.dependency_info:
            return self.dependency_info["target_pos"]
        for e in self.affected_entities:
            if isinstance(e, (tuple, list)) and len(e) == 2:
                return (e[0], e[1])
        return (0, 0)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.opportunity_id,
            "category": self.category,
            "trigger": self.event_trigger.value if self.event_trigger else None,
            "entities": self.affected_entities,
            "relevance": round(self.estimated_economic_relevance, 2),
            "family": self.candidate_transformation_family,
            "horizon": self.required_horizon,
            "status": self.scientific_status.value,
            "rationale": self.rationale,
        }
