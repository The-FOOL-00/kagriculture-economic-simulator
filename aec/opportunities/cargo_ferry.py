# SPDX-License-Identifier: MIT
"""Cargo Ferry Multi-Worker Opportunity Detector (§15)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from aec.config import SHED_TILES, ScientificStatus
from aec.ir.economic_state import EconomicState
from aec.opportunities.base import Opportunity


@dataclass
class CargoFerryOpportunity(Opportunity):
    """An opportunity where an idle auxiliary worker ferries cargo from an active worker or field to the shed (§15)."""
    source_worker_id: int = 0
    ferry_worker_id: int = 1
    target_pos: Tuple[int, int] = (0, 0)
    cargo_item: str = ""
    cargo_quantity: int = 1


class CargoFerryDetector:
    """Detects multi-worker cooperative hauling opportunities.
    
    Condition:
    Worker A (Primary/Active) is producing/busy.
    Worker B (Auxiliary) is idle and near a full cargo deposit or ready crop.
    B can perform the transport to shed, preserving A's continuous field labor.
    """

    def detect(
        self,
        econ_state: EconomicState,
        baseline_action: Optional[Dict[str, Any]] = None
    ) -> List[CargoFerryOpportunity]:
        opportunities: List[CargoFerryOpportunity] = []
        workers = econ_state.workers.workers
        if len(workers) < 2:
            return []

        primary = workers[0]
        hands = workers[1:]

        # Check if any auxiliary hand is idle
        idle_hands = [h for h in hands if not getattr(h, "is_frozen", False) and not h.cargo]
        if not idle_hands:
            return []

        # Check if primary worker is carrying high-value cargo or near ripe crops while busy
        for hand in idle_hands:
            # Look for ground deposits or ripe crop clusters that hand can ferry to shed
            for crop in getattr(econ_state.farm, "crops", []):
                is_mature = getattr(crop, "is_mature", False) or getattr(crop, "growth_stage", 0) >= getattr(crop, "max_growth", 1)
                if not is_mature:
                    continue

                cpos = getattr(crop, "position", (0, 0))
                dist = abs(hand.position[0] - cpos[0]) + abs(hand.position[1] - cpos[1])
                
                # Hand is close to crop (<= 3 steps) and shed has capacity
                if dist <= 3 and econ_state.farm.shed_inventory_count < 95:
                    ctype = getattr(crop, "crop_type", "CROP")
                    val = float(econ_state.market.prices.get(ctype, 30.0))
                    opportunities.append(CargoFerryOpportunity(
                        opportunity_id=f"FERRY_{econ_state.step}_H{hand.worker_id}_{cpos[0]}_{cpos[1]}",
                        category="LABOR",
                        event_trigger=None,
                        affected_entities=[hand.worker_id, primary.worker_id, cpos],
                        estimated_economic_relevance=val,
                        candidate_transformation_family="CARGO_FERRY",
                        required_horizon=24,
                        rationale=f"Auxiliary Hand {hand.worker_id} ferries {ctype} from {cpos} to shed, unburdening Primary Worker.",
                        scientific_status=ScientificStatus.PLAUSIBLE_UNPROVEN,
                        source_worker_id=primary.worker_id,
                        ferry_worker_id=hand.worker_id,
                        target_pos=cpos,
                        cargo_item=ctype,
                        cargo_quantity=1,
                    ))

        return opportunities
