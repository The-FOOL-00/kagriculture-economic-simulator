# SPDX-License-Identifier: MIT
"""Machine-Readable Safety Certificate (§14, §15)."""

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
    spatial_consistency_check: bool = True
    fidelity_check: bool = True
    
    # Extended Route-Splicing Safety Invariants (§15)
    spatial_validity_check: bool = True
    timing_validity_check: bool = True
    route_continuity_check: bool = True
    worker_consistency_check: bool = True
    resource_consistency_check: bool = True
    obligation_consistency_check: bool = True
    market_consistency_check: bool = True

    # Extended Resource & Feed Security Safety Invariants (§17, §18)
    resource_conservation_check: bool = True
    negative_inventory_check: bool = True
    conversion_precondition_check: bool = True
    feed_security_check: bool = True
    capacity_consistency_check: bool = True
    cash_liquidity_check: bool = True
    temporal_availability_check: bool = True
    reservation_consistency_check: bool = True
    terminal_resource_check: bool = True
    
    # Fidelity classification (§14): VERIFIED, PARTIAL, UNKNOWN, FAILED
    counterfactual_fidelity: str = "VERIFIED"
    
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
            and self.spatial_consistency_check
            and self.fidelity_check
            and self.spatial_validity_check
            and self.timing_validity_check
            and self.route_continuity_check
            and self.worker_consistency_check
            and self.resource_consistency_check
            and self.obligation_consistency_check
            and self.market_consistency_check
            and self.resource_conservation_check
            and self.negative_inventory_check
            and self.conversion_precondition_check
            and self.feed_security_check
            and self.capacity_consistency_check
            and self.cash_liquidity_check
            and self.temporal_availability_check
            and self.reservation_consistency_check
            and self.terminal_resource_check
            and self.counterfactual_fidelity != "FAILED"
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "patch_id": self.patch_id,
            "baseline": self.baseline_summary,
            "candidate": self.candidate_summary,
            "delta_our_money": round(self.delta_our_money, 2),
            "delta_opp_money": round(self.delta_opponent_money, 2),
            "delta_terminal_margin": round(self.delta_terminal_margin, 2),
            "counterfactual_fidelity": self.counterfactual_fidelity,
            "checks": {
                "overflow": self.overflow_check,
                "obligation": self.obligation_check,
                "purchase": self.purchase_check,
                "intermediate_solvency": self.intermediate_solvency_check,
                "terminal_feasibility": self.terminal_feasibility_check,
                "market_collision": self.market_collision_check,
                "determinism": self.determinism_check,
                "spatial_consistency": self.spatial_consistency_check,
                "fidelity": self.fidelity_check,
                "spatial_validity": self.spatial_validity_check,
                "timing_validity": self.timing_validity_check,
                "route_continuity": self.route_continuity_check,
                "worker_consistency": self.worker_consistency_check,
                "resource_consistency": self.resource_consistency_check,
                "obligation_consistency": self.obligation_consistency_check,
                "market_consistency": self.market_consistency_check,
                "resource_conservation": self.resource_conservation_check,
                "negative_inventory": self.negative_inventory_check,
                "conversion_precondition": self.conversion_precondition_check,
                "feed_security": self.feed_security_check,
                "capacity_consistency": self.capacity_consistency_check,
                "cash_liquidity": self.cash_liquidity_check,
                "temporal_availability": self.temporal_availability_check,
                "reservation_consistency": self.reservation_consistency_check,
                "terminal_resource": self.terminal_resource_check,
            },
            "commit_decision": self.commit_decision,
            "abstain_reason": self.abstain_reason,
            "metadata": self.metadata,
        }
