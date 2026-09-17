# SPDX-License-Identifier: MIT
"""Machine-Readable Safety Certificate (§15)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class SafetyCertificate:
    """Explicit, machine-readable audit certificate generated for every candidate patch.
    
    If certification fails:
        ABSTAIN -> BACKBONE
    """
    patch_id: str
    baseline_summary: str
    candidate_summary: str
    
    delta_our_money: float
    delta_opponent_money: float
    delta_terminal_margin: float
    
    overflow_check: bool = True
    obligation_check: bool = True
    purchase_check: bool = True
    intermediate_solvency_check: bool = True
    terminal_feasibility_check: bool = True
    market_collision_check: bool = True
    determinism_check: bool = True
    
    commit_decision: bool = False
    abstain_reason: Optional[str] = None
    
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def all_checks_passed(self) -> bool:
        return (
            self.overflow_check
            and self.obligation_check
            and self.purchase_check
            and self.intermediate_solvency_check
            and self.terminal_feasibility_check
            and self.market_collision_check
            and self.determinism_check
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "patch_id": self.patch_id,
            "baseline": self.baseline_summary,
            "candidate": self.candidate_summary,
            "delta_our_money": round(self.delta_our_money, 2),
            "delta_opp_money": round(self.delta_opponent_money, 2),
            "delta_terminal_margin": round(self.delta_terminal_margin, 2),
            "checks": {
                "overflow": self.overflow_check,
                "obligation": self.obligation_check,
                "purchase": self.purchase_check,
                "intermediate_solvency": self.intermediate_solvency_check,
                "terminal_feasibility": self.terminal_feasibility_check,
                "market_collision": self.market_collision_check,
                "determinism": self.determinism_check,
            },
            "commit_decision": self.commit_decision,
            "abstain_reason": self.abstain_reason,
            "metadata": self.metadata,
        }
