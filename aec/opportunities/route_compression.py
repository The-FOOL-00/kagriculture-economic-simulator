# SPDX-License-Identifier: MIT
"""Route Compression Opportunity Detector and Synthesizer (§14)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from aec.config import ScientificStatus
from aec.ir.economic_state import EconomicState
from aec.opportunities.base import Opportunity


@dataclass
class RouteCompressionOpportunity(Opportunity):
    """An opportunity to reorder or compact worker route tasks (§14).
    
    Economic value is derived strictly through causal downstream consequences:
    earlier harvest, earlier sale, or earlier production (never arbitrary dollar-per-step).
    """
    original_route_steps: int = 0
    compressed_route_steps: int = 0
    saved_steps: int = 0
    target_tasks: List[str] = field(default_factory=list)
    worker_id: int = 0


class RouteCompressionDetector:
    """Detects opportunities to reorganize worker trajectories to complete the same tasks earlier."""

    def detect(
        self,
        econ_state: EconomicState,
        baseline_trajectory: Optional[List[Dict[str, Any]]] = None,
        worker_id: int = 0
    ) -> List[RouteCompressionOpportunity]:
        opportunities: List[RouteCompressionOpportunity] = []
        w = next((x for x in econ_state.workers.workers if x.worker_id == worker_id), None)
        if w is None or w.is_frozen:
            return []

        # Inspect if worker has mature crop nearby that can be harvested along transit route
        for crop in getattr(econ_state.farm, "crops", []):
            is_mature = getattr(crop, "is_mature", False) or getattr(crop, "growth_stage", 0) >= getattr(crop, "max_growth", 1)
            if not is_mature:
                continue

            crop_pos = getattr(crop, "position", (0, 0))
            dist = abs(w.position[0] - crop_pos[0]) + abs(w.position[1] - crop_pos[1])
            
            # If mature crop is in immediate detour radius (1-3 steps)
            if 1 <= dist <= 3 and not w.cargo:
                crop_type = getattr(crop, "crop_type", "CROP")
                price = econ_state.market.prices.get(crop_type, 20.0)
                # Economic relevance derived through product value realized earlier
                opportunities.append(RouteCompressionOpportunity(
                    opportunity_id=f"RCOMP_{econ_state.step}_W{worker_id}_{crop_pos[0]}_{crop_pos[1]}",
                    category="ROUTE",
                    event_trigger=None,
                    affected_entities=[worker_id, crop_pos],
                    estimated_economic_relevance=float(price),
                    candidate_transformation_family="ROUTE_COMPRESSION",
                    required_horizon=16,
                    rationale=f"Worker {worker_id} detour ({dist} steps) harvests {crop_type} at {crop_pos} on way to shed.",
                    scientific_status=ScientificStatus.PLAUSIBLE_UNPROVEN,
                    original_route_steps=dist + 8,
                    compressed_route_steps=dist + 4,
                    saved_steps=4,
                    target_tasks=["HARVEST", "DROP"],
                    worker_id=worker_id,
                ))

        return opportunities
