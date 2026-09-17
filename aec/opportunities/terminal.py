# SPDX-License-Identifier: MIT
"""Terminal Opportunity Analyzer (7F)."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from aec.config import FINAL_STEP, ScientificStatus
from aec.events.event_types import EventType
from aec.ir.economic_state import EconomicState
from aec.opportunities.base import Opportunity


class TerminalOpportunityAnalyzer:
    """Detects phase shutdown cutoffs, terminal harvest sweep, and step 718 liquidation."""

    def analyze(
        self,
        econ_state: EconomicState,
        events: List[Any],
        baseline_action: Optional[Dict[str, Any]] = None
    ) -> List[Opportunity]:
        opportunities: List[Opportunity] = []
        step = econ_state.step

        # Step 718 Terminal Liquidation
        if step == FINAL_STEP:
            shed_total = econ_state.farm.shed_total_units
            if shed_total > 0:
                opportunities.append(Opportunity(
                    opportunity_id=f"TERMINAL_LIQUIDATE_STEP_{step}",
                    category="TERMINAL",
                    event_trigger=EventType.E8_TERMINAL_TRANSITION,
                    affected_entities=["SHED_LIQUIDATION"],
                    estimated_economic_relevance=float(shed_total * 50),
                    candidate_transformation_family="TERMINAL_LIQUIDATION",
                    dependency_info={"shed": econ_state.farm.shed_inventory},
                    required_horizon=1,
                    rationale=f"Step 718 final liquidation of {shed_total} units in shed",
                    confidence=1.0,
                    scientific_status=ScientificStatus.REUSED_SAFETY
                ))

        # Late-Game Harvest Sweep (steps 696–717)
        elif step >= 696:
            # Check if any mature crops are unharvested
            mature_crops = sum(econ_state.farm.expected_harvests.values())
            if mature_crops > 0:
                opportunities.append(Opportunity(
                    opportunity_id=f"TERMINAL_SWEEP_STEP_{step}",
                    category="TERMINAL",
                    event_trigger=EventType.E8_TERMINAL_TRANSITION,
                    affected_entities=["HARVEST_SWEEP"],
                    estimated_economic_relevance=float(mature_crops * 80),
                    candidate_transformation_family="TERMINAL_HARVEST_SWEEP",
                    dependency_info={"mature_crops": mature_crops},
                    required_horizon=max(1, FINAL_STEP - step),
                    rationale=f"Terminal harvest sweep: {mature_crops} mature units awaiting collection",
                    confidence=0.9,
                    scientific_status=ScientificStatus.REUSED_SAFETY
                ))

        # Phase Shutdown: Prevent dead-capital planting
        if step >= 574:
            for crop, feasible in econ_state.crop_feasibility.items():
                if not feasible:
                    opportunities.append(Opportunity(
                        opportunity_id=f"TERMINAL_SHUTDOWN_{crop}_{step}",
                        category="TERMINAL",
                        event_trigger=EventType.E7_PRODUCTION_DEADLINE,
                        affected_entities=[crop],
                        estimated_economic_relevance=50.0,
                        candidate_transformation_family="PHASE_SHUTDOWN",
                        dependency_info={"crop": crop, "cutoff_step": step},
                        required_horizon=6,
                        rationale=f"Halt {crop} planting: cannot mature before game end",
                        confidence=1.0,
                        scientific_status=ScientificStatus.VERIFIED_SOURCE
                    ))

        return opportunities
