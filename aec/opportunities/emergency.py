# SPDX-License-Identifier: MIT
"""Generalized Emergency Recovery Opportunity Architecture (§20)."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from aec.config import ScientificStatus
from aec.ir.economic_state import EconomicState
from aec.opportunities.base import Opportunity


class EmergencyThreatType(str, Enum):
    """The formal causal threat category prompting emergency intervention (§20)."""
    LIVESTOCK_STARVATION = "LIVESTOCK_STARVATION"       # Animal death imminent
    CRITICAL_CASH_INSOLVENCY = "CRITICAL_CASH_INSOLVENCY" # Cash insufficient to pay mandatory wages
    SHED_OVERFLOW_COLLAPSE = "SHED_OVERFLOW_COLLAPSE"   # Shed stock discard imminent
    TERMINAL_FAILURE_TO_LIQUIDATE = "TERMINAL_FAILURE_TO_LIQUIDATE" # Assets stranded at step 718


@dataclass
class EmergencyRecoveryOpportunity(Opportunity):
    """A high-priority rescue opportunity responding to a state-threatening situation (§20).
    
    Adheres to strict causal discipline:
    1. Causal purpose verified against threatened asset.
    2. Exact obligation preservation without arbitrary safety buffers ($150 buffer removed).
    3. Fail-closed: Must pass exact counterfactual simulation.
    """
    threat_type: EmergencyThreatType = EmergencyThreatType.LIVESTOCK_STARVATION
    urgency_steps: int = 12
    threatened_value: float = 0.0
    rescue_action_family: str = "EMERGENCY_FEED"


class EmergencyRecoveryDetector:
    """Detects existential threats to farm assets and formulates causal rescue opportunities."""

    def detect(
        self,
        econ_state: EconomicState,
        baseline_action: Optional[Dict[str, Any]] = None
    ) -> List[EmergencyRecoveryOpportunity]:
        opportunities: List[EmergencyRecoveryOpportunity] = []
        step = econ_state.step
        cash = econ_state.cash

        # 1. Livestock Starvation Check
        for animal in getattr(econ_state.farm, "animals", []):
            starve_steps = getattr(animal, "turns_to_starve", 999)
            if starve_steps <= 12:
                atype = getattr(animal, "animal_type", "ANIMAL")
                cost = 300.0 if atype == "GOOSE" else (400.0 if atype == "COW" else 500.0)
                opportunities.append(EmergencyRecoveryOpportunity(
                    opportunity_id=f"EMR_STARVE_{step}_{atype}",
                    category="RESOURCE",
                    event_trigger=None,
                    affected_entities=[atype],
                    estimated_economic_relevance=cost,
                    candidate_transformation_family="EMERGENCY_RECOVERY",
                    required_horizon=max(6, starve_steps),
                    rationale=f"Emergency rescue: {atype} will starve in {starve_steps} turns without feed.",
                    scientific_status=ScientificStatus.PLAUSIBLE_UNPROVEN,
                    threat_type=EmergencyThreatType.LIVESTOCK_STARVATION,
                    urgency_steps=starve_steps,
                    threatened_value=cost,
                    rescue_action_family="EMERGENCY_FEED",
                ))

        # 2. Critical Cash Insolvency (Wage Default Risk)
        num_hands = max(0, len(econ_state.workers.workers) - 1)
        wages_due_tonight = num_hands * 100.0
        steps_to_night = 23 - (step % 24)
        if wages_due_tonight > 0 and cash < wages_due_tonight and steps_to_night <= 6:
            deficit = wages_due_tonight - cash
            opportunities.append(EmergencyRecoveryOpportunity(
                opportunity_id=f"EMR_WAGE_{step}",
                category="MARKET",
                event_trigger=None,
                affected_entities=["WAGES"],
                estimated_economic_relevance=float(deficit * 2.0),
                candidate_transformation_family="EMERGENCY_RECOVERY",
                required_horizon=steps_to_night,
                rationale=f"Emergency cash rescue: ${deficit:.1f} deficit before nightly wage deduction.",
                scientific_status=ScientificStatus.PLAUSIBLE_UNPROVEN,
                threat_type=EmergencyThreatType.CRITICAL_CASH_INSOLVENCY,
                urgency_steps=steps_to_night,
                threatened_value=wages_due_tonight,
                rescue_action_family="EMERGENCY_LIQUIDATE",
            ))

        return opportunities
