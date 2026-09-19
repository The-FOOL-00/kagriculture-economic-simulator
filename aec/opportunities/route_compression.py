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
        tiles = getattr(econ_state.farm, "tiles", [])
        current_prices = econ_state.market.current_prices

        for w in target_workers:
            wid = w.worker_id
            if getattr(w, "is_frozen", False):
                continue

            best_shed = min(
                SHED_TILES,
                key=lambda st: abs(w.position[0] - st[0]) + abs(w.position[1] - st[1])
            )

            # 1. Detour Task Compaction: Harvest mature crop in detour radius (1-3 steps)
            if hasattr(econ_state.farm, "crops") and econ_state.farm.crops:
                for c in econ_state.farm.crops:
                    cpos = getattr(c, "position", (0, 0))
                    dist = abs(w.position[0] - cpos[0]) + abs(w.position[1] - cpos[1])
                    if 1 <= dist <= 3:
                        ctype = getattr(c, "crop_type", "MELON")
                        price = float(current_prices.get(ctype, 35.0))
                        dist_to_shed = abs(cpos[0] - best_shed[0]) + abs(cpos[1] - best_shed[1])
                        orig_steps = dist + dist_to_shed + 6
                        comp_steps = dist + 1 + dist_to_shed + 1
                        saved = max(1, orig_steps - comp_steps)
                        opportunities.append(RouteCompressionOpportunity(
                            opportunity_id=f"RCOMP_{econ_state.step}_W{wid}_{cpos[0]}_{cpos[1]}",
                            category="ROUTE",
                            event_trigger=None,
                            affected_entities=[wid, cpos],
                            estimated_economic_relevance=price * 2,
                            candidate_transformation_family="ROUTE_COMPRESSION",
                            dependency_info={
                                "worker_id": wid,
                                "target_pos": cpos,
                                "crop": ctype,
                                "yield_units": 2,
                                "target_tasks": ["HARVEST", "DROP"],
                                "saved_steps": saved,
                                "original_route_steps": orig_steps,
                                "compressed_route_steps": comp_steps,
                            },
                            required_horizon=max(12, comp_steps + 6),
                            rationale=f"Worker {wid} compresses route ({saved} turns saved): compacts {ctype} at {cpos}.",
                            scientific_status=ScientificStatus.PLAUSIBLE_UNPROVEN,
                            original_route_steps=orig_steps,
                            compressed_route_steps=comp_steps,
                            saved_steps=saved,
                            target_tasks=["HARVEST", "DROP"],
                            worker_id=wid,
                            target_pos=cpos,
                            crop_type=ctype,
                        ))

            if tiles:
                for y, row in enumerate(tiles):
                    for x, tile in enumerate(row):
                        if isinstance(tile, dict) and tile.get("kind") == "PLANT":
                            yield_u = int(tile.get("yield_units", 0) or 0)
                            crop = tile.get("crop")
                            if yield_u > 0 and crop:
                                crop_pos = (x, y)
                                dist = abs(w.position[0] - x) + abs(w.position[1] - y)
                                if 1 <= dist <= 3:
                                    price = float(current_prices.get(crop, 35.0))
                                    dist_to_shed = abs(x - best_shed[0]) + abs(y - best_shed[1])
                                    orig_steps = dist + dist_to_shed + 6
                                    comp_steps = dist + 1 + dist_to_shed + 1
                                    saved = max(1, orig_steps - comp_steps)

                                    opportunities.append(RouteCompressionOpportunity(
                                        opportunity_id=f"RCOMP_{econ_state.step}_W{wid}_{x}_{y}",
                                        category="ROUTE",
                                        event_trigger=None,
                                        affected_entities=[wid, crop_pos],
                                        estimated_economic_relevance=price * yield_u,
                                        candidate_transformation_family="ROUTE_COMPRESSION",
                                        dependency_info={
                                            "worker_id": wid,
                                            "target_pos": crop_pos,
                                            "crop": crop,
                                            "yield_units": yield_u,
                                            "target_tasks": ["HARVEST", "DROP"],
                                            "saved_steps": saved,
                                            "original_route_steps": orig_steps,
                                            "compressed_route_steps": comp_steps,
                                        },
                                        required_horizon=max(12, comp_steps + 6),
                                        rationale=(
                                            f"Worker {wid} economic route compression ({saved} turns saved): "
                                            f"compacts {crop} harvest at {crop_pos} with transit to shed."
                                        ),
                                        scientific_status=ScientificStatus.PLAUSIBLE_UNPROVEN,
                                        original_route_steps=orig_steps,
                                        compressed_route_steps=comp_steps,
                                        saved_steps=saved,
                                        target_tasks=["HARVEST", "DROP"],
                                        worker_id=wid,
                                        target_pos=crop_pos,
                                        crop_type=crop,
                                    ))

            # 2. Direct Cargo Transit Compaction: Eliminate wandering/delays to shed
            if w.total_cargo_units > 0:
                direct_dist = abs(w.position[0] - best_shed[0]) + abs(w.position[1] - best_shed[1])
                deposit_len = getattr(w, "deposit_path_len", direct_dist + 2)
                if deposit_len > direct_dist or (w.position != best_shed and direct_dist <= 4):
                    saved = max(1, deposit_len - direct_dist)
                    cargo_val = sum(q * float(current_prices.get(it, 25.0)) for it, q in w.cargo.items())
                    opportunities.append(RouteCompressionOpportunity(
                        opportunity_id=f"RCOMP_SHED_{econ_state.step}_W{wid}",
                        category="ROUTE",
                        event_trigger=None,
                        affected_entities=[wid, best_shed],
                        estimated_economic_relevance=max(10.0, cargo_val),
                        candidate_transformation_family="ROUTE_COMPRESSION",
                        dependency_info={
                            "worker_id": wid,
                            "target_pos": best_shed,
                            "target_tasks": ["DROP"],
                            "saved_steps": saved,
                            "original_route_steps": deposit_len,
                            "compressed_route_steps": direct_dist,
                        },
                        required_horizon=max(8, direct_dist + 4),
                        rationale=(
                            f"Worker {wid} direct shed transit ({saved} turns saved): "
                            f"expedites delivery of {w.total_cargo_units} cargo units."
                        ),
                        scientific_status=ScientificStatus.PLAUSIBLE_UNPROVEN,
                        original_route_steps=deposit_len,
                        compressed_route_steps=direct_dist,
                        saved_steps=saved,
                        target_tasks=["DROP"],
                        worker_id=wid,
                        target_pos=best_shed,
                    ))

        # Sort opportunities by estimated economic relevance descending, capped at 6
        opportunities.sort(key=lambda o: o.estimated_economic_relevance, reverse=True)
        return opportunities[:6]
