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

    @property
    def upfront_cost(self) -> float:
        return float(self.payload.get("upfront_cost", 0.0))


class TacticalPlanner:
    """Coordinates tactical opportunity generation under macro constraints."""

    def __init__(self, macro_controller: Optional[Any] = None) -> None:
        self.macro_controller = macro_controller

    def validate_proposal_compatibility(
        self,
        proposal: TacticalProposal,
        current_cash: float,
        strategy: Optional[MacroStrategy] = None
    ) -> Tuple[bool, str]:
        """Validate if proposal satisfies macro constraints and cash reserves (§10)."""
        strat = strategy
        if strat is None and self.macro_controller is not None:
            strat = getattr(self.macro_controller, "_fixed_strategy", None)

        if strat is not None:
            if proposal.upfront_cost > 0:
                post_cash = current_cash - proposal.upfront_cost
                if post_cash < strat.min_cash_reserve:
                    return False, f"Violates minimum cash reserve: {post_cash:.1f} < {strat.min_cash_reserve:.1f}"
            if not strat.allow_capital_expenditures and proposal.category == TacticalCategory.RESOURCE_CONVERSION:
                return False, "Macro policy prohibits capital expenditures"

        return True, ""

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
