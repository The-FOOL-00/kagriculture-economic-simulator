# SPDX-License-Identifier: MIT
"""META Orchestration Policy and Mode Controls (§12, §13, §33)."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

from aec.counterfactual.opponent_pressure import OpponentPressureState
from aec.ir.economic_state import EconomicState


class AECMode(str, Enum):
    """Explicit operational configuration modes (§33)."""
    ROBUST_MODE = "ROBUST_MODE"         # Scientifically cleared robust mechanisms only
    META_MODE = "META_MODE"             # Opponent-sensitive mechanisms + safe fallback to ROBUST
    RESEARCH_MODE = "RESEARCH_MODE"     # Diagnostic exploration across broader candidate sets


@dataclass
class MetaPolicyDecision:
    """The high-level policy determination by the META layer."""
    active_mode: AECMode
    effective_mode: AECMode             # May be downgraded from META to ROBUST if confidence is low
    authorized_families: Set[str]
    strategic_priorities: Dict[str, float]
    fallback_to_robust: bool = False
    rationale: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "active_mode": self.active_mode.value,
            "effective_mode": self.effective_mode.value,
            "fallback_to_robust": self.fallback_to_robust,
            "authorized_families": sorted(list(self.authorized_families)),
            "strategic_priorities": {k: round(v, 2) for k, v in self.strategic_priorities.items()},
            "rationale": self.rationale,
        }


class MetaOrchestrator:
    """Architectural META layer: Policy and orchestration layer (§12, §13).
    
    Consumes:
      - Opponent pressure
      - Market timing
      - Dependency impact
      - Labor economics
      - Counterfactual results
      
    Decides:
      - Which opportunity families deserve attention
      - How candidates should be prioritized
      - Fallback from META to ROBUST when opponent confidence is weak
    """

    # Families cleared for pure ROBUST operation
    ROBUST_FAMILIES: Set[str] = {
        "DEPENDENCY_AWARE_MARKET_TIMING",
        "TERMINAL_LIQUIDATION",
        "PHASE_SHUTDOWN",
        "DYNAMIC_SHADOW_HARVEST",
        "TERMINAL_HARVEST_SWEEP",
        "ROUTE_COMPRESSION",
        "CARGO_FERRY",
        "TERMINAL_CONVERSION",
    }

    # Additional families enabled in META operation
    META_FAMILIES: Set[str] = {
        "OPPONENT_PREEMPT_SELL",
        "MARKET_COLLISION_TIMING",
        "TOWN_CYCLE_TIMING",
    }

    # Additional experimental families in RESEARCH mode
    RESEARCH_FAMILIES: Set[str] = {
        "SHOP_ARBITRAGE",
        "PRODUCTION_ARBITRAGE",
        "EMERGENCY_RECOVERY",
    }

    def __init__(
        self,
        mode: AECMode = AECMode.ROBUST_MODE,
        confidence_threshold: float = 0.40
    ) -> None:
        self.configured_mode = mode
        self.confidence_threshold = confidence_threshold

    def orchestrate(
        self,
        pressure_state: OpponentPressureState,
        econ_state: EconomicState,
        override_mode: Optional[AECMode] = None
    ) -> MetaPolicyDecision:
        """Determine effective operational mode and authorize candidate families (§12, §13)."""
        mode = override_mode or self.configured_mode

        if mode == AECMode.ROBUST_MODE:
            return MetaPolicyDecision(
                active_mode=mode,
                effective_mode=AECMode.ROBUST_MODE,
                authorized_families=set(self.ROBUST_FAMILIES),
                strategic_priorities={},
                fallback_to_robust=False,
                rationale="ROBUST_MODE: Relying exclusively on foundation economics, harvest, and robust fallback."
            )

        if mode == AECMode.META_MODE:
            # Check opponent model confidence
            if pressure_state.confidence < self.confidence_threshold:
                # Safe fallback to ROBUST (§13)
                return MetaPolicyDecision(
                    active_mode=mode,
                    effective_mode=AECMode.ROBUST_MODE,
                    authorized_families=set(self.ROBUST_FAMILIES),
                    strategic_priorities={},
                    fallback_to_robust=True,
                    rationale=f"META fallback to ROBUST: Opponent confidence {pressure_state.confidence:.2f} < threshold {self.confidence_threshold:.2f}."
                )

            # META authorized families
            meta_authorized = set(self.ROBUST_FAMILIES) | set(self.META_FAMILIES)
            priorities: Dict[str, float] = {}

            # Prioritize based on pressure signals
            if pressure_state.timing_pressure >= 0.5:
                priorities["DEPENDENCY_AWARE_MARKET_TIMING"] = 1.5
                priorities["OPPONENT_PREEMPT_SELL"] = 2.0

            if pressure_state.terminal_pressure >= 0.6:
                priorities["TERMINAL_HARVEST_SWEEP"] = 2.5
                priorities["TERMINAL_CONVERSION"] = 2.0

            return MetaPolicyDecision(
                active_mode=mode,
                effective_mode=AECMode.META_MODE,
                authorized_families=meta_authorized,
                strategic_priorities=priorities,
                fallback_to_robust=False,
                rationale="META_MODE: Opponent pressure confidence verified; strategic timing & preemption enabled."
            )

        # RESEARCH_MODE
        research_authorized = set(self.ROBUST_FAMILIES) | set(self.META_FAMILIES) | set(self.RESEARCH_FAMILIES)
        return MetaPolicyDecision(
            active_mode=mode,
            effective_mode=AECMode.RESEARCH_MODE,
            authorized_families=research_authorized,
            strategic_priorities={},
            fallback_to_robust=False,
            rationale="RESEARCH_MODE: Diagnostic exploration across all architectural mechanisms."
        )

    def prioritize_candidates(
        self,
        candidates: List[Any],
        policy_decision: MetaPolicyDecision,
        pressure_state: OpponentPressureState
    ) -> List[Any]:
        """Adjust candidate scores according to strategic policy without bypassing gates (§9)."""
        scored = []
        for c in candidates:
            family = str(getattr(c, "mechanism_family", "") or getattr(c, "candidate_transformation_family", ""))
            base_val = float(getattr(c, "estimated_economic_value", 0.0) or getattr(c, "estimated_economic_relevance", 0.0))
            
            # Multiplier from meta priorities
            mult = policy_decision.strategic_priorities.get(family, 1.0)
            strategic_bonus = pressure_state.candidate_strategic_priority(c)
            
            adjusted_score = base_val * mult + strategic_bonus
            scored.append((adjusted_score, c))

        scored.sort(key=lambda pair: -pair[0])
        return [pair[1] for pair in scored]
