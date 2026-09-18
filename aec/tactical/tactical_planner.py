# SPDX-License-Identifier: MIT
"""Tactical Layer Planning and Patch Framing (§10)."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from aec.macro.macro_controller import MacroStrategy


class TacticalCategory(str, Enum):
    """Categorization of tactical interventions (§10)."""
    HARVEST = "HARVEST"
    ROUTE_COMPRESSION = "ROUTE_COMPRESSION"
    CARGO_FERRY = "CARGO_FERRY"
    MARKET_TIMING = "MARKET_TIMING"
    LOCAL_WORKER_REASSIGNMENT = "LOCAL_WORKER_REASSIGNMENT"
    RESOURCE_CONVERSION = "RESOURCE_CONVERSION"
    TERMINAL_SWEEP = "TERMINAL_SWEEP"


@dataclass
class TacticalProposal:
    """A scoped tactical proposal submitted for compilation and simulation."""
    proposal_id: str
    category: TacticalCategory
    mechanism_family: str
    affected_workers: List[int]
    estimated_economic_value: float
    duration_steps: int = 1
    macro_compatible: bool = True
    rejection_reason: Optional[str] = None
    payload: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.proposal_id,
            "category": self.category.value,
            "family": self.mechanism_family,
            "workers": self.affected_workers,
            "est_value": round(self.estimated_economic_value, 2),
            "duration": self.duration_steps,
            "macro_ok": self.macro_compatible,
            "rejection": self.rejection_reason,
        }


class TacticalPlanner:
    """Coordinates tactical opportunity generation under macro constraints."""

    def filter_proposals_by_macro(
        self,
        proposals: List[TacticalProposal],
        strategy: MacroStrategy
    ) -> List[TacticalProposal]:
        """Ensure no tactical proposal violates macro direction (§10)."""
        approved: List[TacticalProposal] = []
        for prop in proposals:
            if not strategy.allow_capital_expenditures and prop.category == TacticalCategory.RESOURCE_CONVERSION:
                prop.macro_compatible = False
                prop.rejection_reason = "MACRO_CAPEX_DISABLED"
                continue
            prop.macro_compatible = True
            approved.append(prop)
        return approved
