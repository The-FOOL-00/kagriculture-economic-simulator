# SPDX-License-Identifier: MIT
"""Terminal Conversion Opportunity and Detector (§18)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from aec.config import EPISODE_STEPS, ScientificStatus
from aec.ir.economic_state import EconomicState
from aec.opportunities.base import Opportunity


@dataclass
class TerminalConversionOpportunity(Opportunity):
    """An opportunity to convert remaining raw inventory into liquidizable terminal assets (§18)."""
    input_item: str = ""
    input_units: int = 0
    output_item: str = ""
    output_units: int = 0
    conversion_steps: int = 2
    projected_terminal_value: float = 0.0
    worker_id: int = 0


class TerminalConversionDetector:
    """Detects late-game (steps 680-716) conversion opportunities to maximize liquidated cash before step 718.
    
    Acceptance criteria:
    1. Conversion completes before step 718.
    2. Output becomes realizable / sellable.
    3. No terminal loss (Output value > Input scrap value).
    4. No unsafe primary worker displacement from essential final harvests.
    """

    def detect(
        self,
        econ_state: EconomicState
    ) -> List[TerminalConversionOpportunity]:
        opportunities: List[TerminalConversionOpportunity] = []
        step = econ_state.step
        
        # Only active in endgame window (steps 680 to 716)
        if not (680 <= step <= 716):
            return []

        rem_steps = 718 - step
        shed = econ_state.farm.shed_inventory
        workers = econ_state.workers.workers
        if not workers:
            return []

        # Auxiliary hands preferred for terminal conversion
        worker = workers[-1]  # hand if available, else farmer

        # Check for unharvested milk or wool conversions or feed processing
        # Example: Wheat to animal feed if it yields high-value product before 718
        wheat_count = shed.get("WHEAT", 0)
        if wheat_count >= 2 and rem_steps >= 6:
            price_wheat = econ_state.market.prices.get("WHEAT", 15.0)
            # Evaluate converting wheat to liquidizable asset
            terminal_val = wheat_count * float(price_wheat)
            opportunities.append(TerminalConversionOpportunity(
                opportunity_id=f"TERM_CONV_{step}_WHEAT_{worker.worker_id}",
                category="TERMINAL",
                event_trigger=None,
                affected_entities=[worker.worker_id, "WHEAT"],
                estimated_economic_relevance=terminal_val,
                candidate_transformation_family="TERMINAL_CONVERSION",
                required_horizon=rem_steps,
                rationale=f"Terminal liquidation conversion of {wheat_count} wheat at step {step} ({rem_steps} steps to cutoff).",
                scientific_status=ScientificStatus.PLAUSIBLE_UNPROVEN,
                input_item="WHEAT",
                input_units=wheat_count,
                output_item="MONEY",
                output_units=wheat_count,
                conversion_steps=2,
                projected_terminal_value=terminal_val,
                worker_id=worker.worker_id,
            ))

        return opportunities
