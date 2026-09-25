# SPDX-License-Identifier: MIT
"""Kagriculture V34 Tactical Data Schemas & Types.

Defines:
1. TacticalCandidate: proposed small, localized deviation from A7.
2. TacticalContract: formal contract governing validated tactical patterns.
3. OpportunityLabel: classification of counterfactual outcomes.
4. TacticalOutcome: multi-horizon forward search outcome metrics.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple


class PromotionStatus(str, Enum):
    EXPERIMENTAL = "EXPERIMENTAL"
    VALIDATED = "VALIDATED"
    QUARANTINED = "QUARANTINED"
    PROMOTED = "PROMOTED"
    RETIRED = "RETIRED"


class OpportunityLabel(str, Enum):
    A7_DOMINANT = "A7_DOMINANT"
    SMALL_SAFE_GAIN = "SMALL_SAFE_GAIN"
    LARGE_SAFE_GAIN = "LARGE_SAFE_GAIN"
    LARGE_UNCERTAIN_GAIN = "LARGE_UNCERTAIN_GAIN"
    SMALL_RISKY_GAIN = "SMALL_RISKY_GAIN"
    CATASTROPHIC_RISK = "CATASTROPHIC_RISK"
    NO_ACTION = "NO_ACTION"


class HorizonTrajectory(str, Enum):
    REVERSING = "REVERSING"
    STABLE = "STABLE"
    COMPOUNDING = "COMPOUNDING"
    DECAYING = "DECAYING"
    DELAYED = "DELAYED"


@dataclass
class TacticalCandidate:
    """A localized, A7-compatible alternative action evaluated at step t."""
    action_id: str
    parent_a7_action: Dict[str, Any]
    candidate_action: Dict[str, Any]
    category: str  # "MARKET_TIMING", "PURCHASE_TIMING", "RESOURCE_ALLOCATION", "TERMINAL_TIMING"
    state_signature: str
    trigger_features: Dict[str, float]
    action_delta_description: str
    physical_impact: str = "CONSERVATIVE"
    market_impact: str = "NEUTRAL"
    compatible_horizon: int = 720
    status: PromotionStatus = PromotionStatus.EXPERIMENTAL


@dataclass
class MultiHorizonDeltas:
    """Cash differences (Candidate - A7) across time horizons."""
    delta_4: float = 0.0
    delta_8: float = 0.0
    delta_16: float = 0.0
    delta_32: float = 0.0
    delta_64: float = 0.0
    delta_128: float = 0.0
    delta_terminal: float = 0.0
    trajectory: HorizonTrajectory = HorizonTrajectory.STABLE


@dataclass
class TacticalOutcome:
    """Exact multi-horizon evaluation result for a candidate against an opponent."""
    candidate_id: str
    step: int
    seed: int
    opponent_id: str
    seat: int
    a7_terminal_cash: float
    cand_terminal_cash: float
    deltas: MultiHorizonDeltas
    a7_won: bool
    cand_won: bool
    min_cash: float
    physical_divergence_steps: int
    resync_success: bool
    liquidity_safe: bool
    opportunity_label: OpportunityLabel


@dataclass
class TacticalContract:
    """Formal governance contract for a promoted or validated tactical override."""
    id: str
    trigger_description: str
    category: str
    parent_a7_action_pattern: str
    alternative_action_generator: str
    observable_features_required: List[str]
    exact_search_score: float
    horizon: int
    expected_win_impact: float
    expected_cash_impact: float
    worst_observed_delta: float
    minimum_cash_required: float
    physical_safety_verified: bool
    liquidity_safety_verified: bool
    activation_conditions: Dict[str, Any]
    incompatibility_conditions: Dict[str, Any]
    promotion_status: PromotionStatus = PromotionStatus.EXPERIMENTAL

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "trigger_description": self.trigger_description,
            "category": self.category,
            "parent_a7_action_pattern": self.parent_a7_action_pattern,
            "alternative_action_generator": self.alternative_action_generator,
            "observable_features_required": self.observable_features_required,
            "exact_search_score": self.exact_search_score,
            "horizon": self.horizon,
            "expected_win_impact": self.expected_win_impact,
            "expected_cash_impact": self.expected_cash_impact,
            "worst_observed_delta": self.worst_observed_delta,
            "minimum_cash_required": self.minimum_cash_required,
            "physical_safety_verified": self.physical_safety_verified,
            "liquidity_safety_verified": self.liquidity_safety_verified,
            "activation_conditions": self.activation_conditions,
            "incompatibility_conditions": self.incompatibility_conditions,
            "promotion_status": self.promotion_status.value,
        }
