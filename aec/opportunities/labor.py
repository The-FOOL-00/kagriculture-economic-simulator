# SPDX-License-Identifier: MIT
"""Labor & Dynamic Shadow Price Opportunity Analyzer (7A)."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from aec.config import ScientificStatus
from aec.events.event_types import EventType
from aec.ir.economic_state import EconomicState
from aec.opportunities.base import Opportunity


def manhattan(p1: Tuple[int, int], p2: Tuple[int, int]) -> int:
    return abs(p1[0] - p2[0]) + abs(p1[1] - p2[1])


class LaborOpportunityAnalyzer:
    """Detects labor slack and calculates state-dependent marginal opportunity costs."""
    
    def analyze(
        self,
        econ_state: EconomicState,
        events: List[Any],
        baseline_action: Optional[Dict[str, Any]] = None
    ) -> List[Opportunity]:
        opportunities: List[Opportunity] = []
        tiles = econ_state.farm.tiles
        workers = econ_state.workers.workers
        prices = econ_state.market.current_prices

        # Scan for tiles with immediate high marginal value
        mature_harvest_tiles: List[Tuple[Tuple[int, int], str, int, float]] = []
        for y, row in enumerate(tiles):
            for x, tile in enumerate(row):
                if isinstance(tile, dict) and tile.get("kind") == "PLANT":
                    crop = tile.get("crop")
                    yield_u = int(tile.get("yield_units", 0) or 0)
                    if yield_u > 0 and crop:
                        val = yield_u * float(prices.get(crop, 50))
                        mature_harvest_tiles.append(((x, y), crop, yield_u, val))

        # Check each worker for potential labor reallocation
        for w in workers:
            w_act = "PASS"
            if baseline_action:
                if w.worker_id == 0:
                    farmer_cmd = baseline_action.get("farmer", ["PASS"])
                    w_act = farmer_cmd[0] if farmer_cmd else "PASS"
                else:
                    hands = baseline_action.get("hands", [])
                    h_idx = w.worker_id - 1
                    if h_idx < len(hands) and hands[h_idx]:
                        w_act = hands[h_idx][0]

            # If worker is passing or idle near mature crops
            if w_act == "PASS" and mature_harvest_tiles:
                # Find closest mature crop tile
                best_tile = None
                best_shadow_val = 0.0
                for (xy, crop, yield_u, val) in mature_harvest_tiles:
                    dist = manhattan(w.position, xy)
                    if dist <= 3:  # within local reach
                        shadow_val = val / max(1.0, dist + 1.0)
                        if shadow_val > best_shadow_val:
                            best_shadow_val = shadow_val
                            best_tile = (xy, crop, yield_u, val, dist)

                if best_tile:
                    xy, crop, yield_u, val, dist = best_tile
                    opportunities.append(Opportunity(
                        opportunity_id=f"LABOR_HARVEST_W{w.worker_id}_{crop}_{xy[0]}_{xy[1]}",
                        category="LABOR",
                        event_trigger=None,
                        affected_entities=[w.worker_id, crop],
                        estimated_economic_relevance=best_shadow_val,
                        candidate_transformation_family="DYNAMIC_SHADOW_HARVEST",
                        dependency_info={"worker_id": w.worker_id, "target_xy": xy, "crop": crop, "dist": dist},
                        required_horizon=max(6, dist * 2 + 2),
                        rationale=f"Worker {w.worker_id} idle near mature {crop} at {xy} (shadow value ${best_shadow_val:.1f})",
                        confidence=0.9,
                        scientific_status=ScientificStatus.PLAUSIBLE_UNPROVEN
                    ))

            # If worker is carrying heavy cargo but not moving to shed
            if w.total_cargo_units >= 3 and w.deposit_path_len > 0 and w_act not in ("NORTH", "SOUTH", "EAST", "WEST", "DROP"):
                cargo_val = sum(q * float(prices.get(it, 20)) for it, q in w.cargo.items())
                shadow_val = cargo_val / max(1.0, float(w.deposit_path_len))
                opportunities.append(Opportunity(
                    opportunity_id=f"LABOR_FERRY_W{w.worker_id}",
                    category="LABOR",
                    event_trigger=None,
                    affected_entities=[w.worker_id],
                    estimated_economic_relevance=shadow_val,
                    candidate_transformation_family="CARGO_FERRY_PRIORITY",
                    dependency_info={"worker_id": w.worker_id, "dist_shed": w.deposit_path_len},
                    required_horizon=max(6, w.deposit_path_len + 2),
                    rationale=f"Worker {w.worker_id} carrying {w.total_cargo_units} units ($ {cargo_val:.0f}) diverted to shed",
                    confidence=0.85,
                    scientific_status=ScientificStatus.PLAUSIBLE_UNPROVEN
                ))

        return opportunities
