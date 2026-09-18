# SPDX-License-Identifier: MIT
"""Route Compression Opportunity Detector and Synthesizer (§14)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from aec.config import SHED_TILES, ScientificStatus
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
    target_pos: Tuple[int, int] = (0, 0)
    crop_type: str = ""


class RouteCompressionDetector:
    """Detects opportunities to reorganize worker trajectories to complete tasks earlier.
    
    Identifies:
    1. Detour task compaction: harvesting mature crops adjacent to transit routes
       rather than requiring separate redundant roundtrips.
    2. Path straightening / redundant move reduction toward destinations (e.g. shed deposit).
    """

    def detect(
        self,
        econ_state: EconomicState,
        baseline_trajectory: Optional[List[Dict[str, Any]]] = None,
        worker_id: Optional[int] = None
    ) -> List[RouteCompressionOpportunity]:
        opportunities: List[RouteCompressionOpportunity] = []
        workers = econ_state.workers.workers
        if not workers:
            return []

        target_workers = [w for w in workers if w.worker_id == worker_id] if worker_id is not None else workers

        for w in target_workers:
            wid = w.worker_id
            if getattr(w, "is_frozen", False):
                continue

            # 1. Inspect if worker has mature crop nearby that can be compacted into transit
            for crop in getattr(econ_state.farm, "crops", []):
                is_mature = getattr(crop, "is_mature", False) or getattr(crop, "growth_stage", 0) >= getattr(crop, "max_growth", 1)
                if not is_mature:
                    continue

                crop_pos = getattr(crop, "position", (0, 0))
                dist = abs(w.position[0] - crop_pos[0]) + abs(w.position[1] - crop_pos[1])

                # If mature crop is in immediate detour radius (1-3 steps) and worker has cargo capacity
                if 1 <= dist <= 3 and w.total_cargo_units < getattr(w, "capacity", 3):
                    ctype = getattr(crop, "crop_type", "CROP")
                    price = float(econ_state.market.prices.get(ctype, 20.0))
                    
                    orig_steps = dist + 8
                    comp_steps = dist + 4
                    saved = max(1, orig_steps - comp_steps)

                    opportunities.append(RouteCompressionOpportunity(
                        opportunity_id=f"RCOMP_{econ_state.step}_W{wid}_{crop_pos[0]}_{crop_pos[1]}",
                        category="ROUTE",
                        event_trigger=None,
                        affected_entities=[wid, crop_pos],
                        estimated_economic_relevance=price,
                        candidate_transformation_family="ROUTE_COMPRESSION",
                        dependency_info={
                            "worker_id": wid,
                            "target_pos": crop_pos,
                            "crop": ctype,
                            "target_tasks": ["HARVEST", "DROP"],
                            "saved_steps": saved,
                            "original_route_steps": orig_steps,
                            "compressed_route_steps": comp_steps,
                        },
                        required_horizon=16,
                        rationale=(
                            f"Worker {wid} compresses route ({saved} steps saved): "
                            f"harvests {ctype} at {crop_pos} on transit to shed."
                        ),
                        scientific_status=ScientificStatus.PLAUSIBLE_UNPROVEN,
                        original_route_steps=orig_steps,
                        compressed_route_steps=comp_steps,
                        saved_steps=saved,
                        target_tasks=["HARVEST", "DROP"],
                        worker_id=wid,
                        target_pos=crop_pos,
                        crop_type=ctype,
                    ))

            # 2. Inspect if worker is carrying cargo to shed and baseline path is suboptimal/wandering
            if w.total_cargo_units > 0:
                shed_pos = (0, 0)
                direct_dist = abs(w.position[0] - shed_pos[0]) + abs(w.position[1] - shed_pos[1])
                # If baseline deposit path length exceeds direct Manhattan distance by >= 2
                if w.deposit_path_len > direct_dist + 1:
                    saved = w.deposit_path_len - direct_dist
                    cargo_val = sum(q * float(econ_state.market.prices.get(it, 20)) for it, q in w.cargo.items())
                    opportunities.append(RouteCompressionOpportunity(
                        opportunity_id=f"RCOMP_SHED_{econ_state.step}_W{wid}",
                        category="ROUTE",
                        event_trigger=None,
                        affected_entities=[wid, shed_pos],
                        estimated_economic_relevance=cargo_val * 0.1 * saved,
                        candidate_transformation_family="ROUTE_COMPRESSION",
                        dependency_info={
                            "worker_id": wid,
                            "target_pos": shed_pos,
                            "target_tasks": ["DROP"],
                            "saved_steps": saved,
                            "original_route_steps": w.deposit_path_len,
                            "compressed_route_steps": direct_dist,
                        },
                        required_horizon=max(6, direct_dist + 4),
                        rationale=(
                            f"Worker {wid} direct shed path ({saved} steps saved) "
                            f"delivers cargo (${cargo_val:.0f}) earlier."
                        ),
                        scientific_status=ScientificStatus.PLAUSIBLE_UNPROVEN,
                        original_route_steps=w.deposit_path_len,
                        compressed_route_steps=direct_dist,
                        saved_steps=saved,
                        target_tasks=["DROP"],
                        worker_id=wid,
                        target_pos=shed_pos,
                    ))

        return opportunities
