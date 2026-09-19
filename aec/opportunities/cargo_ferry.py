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

        # Check auxiliary hands availability
        idle_hands = [
            h for h in hands
            if not getattr(h, "is_frozen", False) and h.total_cargo_units < getattr(h, "capacity", 3)
        ]
        if not idle_hands:
            return []

        # Shed remaining capacity check
        shed_inv = econ_state.farm.shed_inventory
        shed_capacity_remaining = max(0, 100 - sum(shed_inv.values()))
        if shed_capacity_remaining < 2:
            return []

        current_prices = econ_state.market.current_prices
        tiles = getattr(econ_state.farm, "tiles", [])

        # 1. Inspect tiles for mature crops reachable by auxiliary hands
        for hand in idle_hands:
            hid = hand.worker_id
            if tiles:
                for y, row in enumerate(tiles):
                    for x, tile in enumerate(row):
                        if isinstance(tile, dict) and tile.get("kind") == "PLANT":
                            yield_u = int(tile.get("yield_units", 0) or 0)
                            crop = tile.get("crop")
                            if yield_u > 0 and crop and yield_u <= shed_capacity_remaining:
                                cpos = (x, y)
                                dist_hand = abs(hand.position[0] - x) + abs(hand.position[1] - y)
                                dist_primary = abs(primary.position[0] - x) + abs(primary.position[1] - y)

                                # Hand is within reasonable reach (<= 4 steps)
                                if dist_hand <= 4:
                                    val = float(current_prices.get(crop, 35.0)) * yield_u
                                    opportunities.append(CargoFerryOpportunity(
                                        opportunity_id=f"FERRY_{econ_state.step}_H{hid}_{x}_{y}",
                                        category="LABOR",
                                        event_trigger=None,
                                        affected_entities=[hid, primary.worker_id, cpos],
                                        estimated_economic_relevance=val,
                                        candidate_transformation_family="CARGO_FERRY",
                                        dependency_info={
                                            "ferry_worker_id": hid,
                                            "worker_id": hid,
                                            "target_pos": cpos,
                                            "target_xy": cpos,
                                            "crop": crop,
                                            "yield_units": yield_u,
                                            "source_worker_id": primary.worker_id,
                                            "dist_hand": dist_hand,
                                            "dist_primary": dist_primary,
                                        },
                                        required_horizon=24,
                                        rationale=(
                                            f"Auxiliary Hand {hid} ferries {crop} from {cpos} to shed, "
                                            f"saving Primary Worker ({dist_primary} steps distant) for core field labor."
                                        ),
                                        scientific_status=ScientificStatus.PLAUSIBLE_UNPROVEN,
                                        source_worker_id=primary.worker_id,
                                        ferry_worker_id=hid,
                                        target_pos=cpos,
                                        cargo_item=crop,
                                        cargo_quantity=yield_u,
                                    ))

            # 2. Backwards compatibility for mocked farm.crops in legacy tests
            if hasattr(econ_state.farm, "crops") and econ_state.farm.crops:
                for c in econ_state.farm.crops:
                    cpos = getattr(c, "position", (0, 0))
                    dist_hand = abs(hand.position[0] - cpos[0]) + abs(hand.position[1] - cpos[1])
                    if dist_hand <= 4:
                        ctype = getattr(c, "crop_type", "MELON")
                        val = float(current_prices.get(ctype, 35.0)) * 2
                        opportunities.append(CargoFerryOpportunity(
                            opportunity_id=f"FERRY_{econ_state.step}_H{hid}_{cpos[0]}_{cpos[1]}",
                            category="LABOR",
                            event_trigger=None,
                            affected_entities=[hid, primary.worker_id, cpos],
                            estimated_economic_relevance=val,
                            candidate_transformation_family="CARGO_FERRY",
                            dependency_info={
                                "ferry_worker_id": hid,
                                "worker_id": hid,
                                "target_pos": cpos,
                                "target_xy": cpos,
                                "crop": ctype,
                                "yield_units": 2,
                                "source_worker_id": primary.worker_id,
                            },
                            required_horizon=24,
                            rationale=f"Auxiliary Hand {hid} ferries {ctype} from {cpos} to shed.",
                            scientific_status=ScientificStatus.PLAUSIBLE_UNPROVEN,
                            source_worker_id=primary.worker_id,
                            ferry_worker_id=hid,
                            target_pos=cpos,
                            cargo_item=ctype,
                            cargo_quantity=2,
                        ))

        # Sort opportunities by estimated economic relevance descending, capped at 6
        opportunities.sort(key=lambda o: o.estimated_economic_relevance, reverse=True)
        return opportunities[:6]
