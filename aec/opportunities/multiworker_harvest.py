# SPDX-License-Identifier: MIT
"""Phase 020: Multi-Worker Harvest Synchronization Opportunity Detector (§10, §33).

Detects unharvested mature crop plots where auxiliary farmhands can synchronize
and harvest immediately, accelerating the production pipeline without distorting
cash or depleting shed inventory.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from aec.config import ScientificStatus
from aec.events.event_types import EventType
from aec.ir.economic_state import EconomicState
from aec.opportunities.base import Opportunity


def manhattan(p1: Tuple[int, int], p2: Tuple[int, int]) -> int:
    return abs(p1[0] - p2[0]) + abs(p1[1] - p2[1])


class MultiworkerHarvestDetector:
    """Detects multi-worker harvest coordination opportunities."""

    def __init__(self, min_step: int = 144) -> None:
        self.min_step = min_step

    def detect(
        self,
        econ_state: EconomicState,
        baseline_action: Optional[Dict[str, Any]] = None,
    ) -> List[Opportunity]:
        opportunities: List[Opportunity] = []
        step = econ_state.step
        if step < self.min_step:
            return opportunities

        workers = getattr(econ_state.workers, "workers", [])
        if len(workers) < 2:
            return opportunities

        tiles = getattr(econ_state.farm, "tiles", [])
        if not tiles:
            return opportunities

        prices = getattr(econ_state.market, "current_prices", {})
        farmer_act = baseline_action.get("farmer", ["PASS"]) if baseline_action else ["PASS"]

        # Collect mature crop plots
        mature_plots: List[Tuple[Tuple[int, int], str, float]] = []
        for y, row in enumerate(tiles):
            for x, tile in enumerate(row):
                if isinstance(tile, dict) and (tile.get("kind") == "PLANT" or tile.get("crop")):
                    growth = tile.get("growth_stage", 0)
                    yield_u = tile.get("yield_units", 0)
                    if growth >= 2 or yield_u > 0:
                        crop = tile.get("crop", "WHEAT")
                        price = float(prices.get(crop, 30.0))
                        mature_plots.append(((x, y), crop, price))

        if not mature_plots:
            return opportunities

        # For each mature plot, check if a farmhand is positioned to harvest
        farmer_pos = workers[0].position
        for (px, py), crop, price in mature_plots:
            # Skip if farmer is already actively harvesting this exact plot
            if farmer_pos == (px, py) and len(farmer_act) > 0 and farmer_act[0] == "HARVEST":
                continue

            for h_idx in range(1, len(workers)):
                hand_w = workers[h_idx]
                if hand_w.position == (px, py):
                    # Farmhand is on the tile! Can harvest immediately
                    opportunities.append(Opportunity(
                        opportunity_id=f"OPP_MW_HARVEST_{px}_{py}_H{h_idx}_{step}",
                        category="LABOR",
                        event_trigger=EventType.E7_PRODUCTION_DEADLINE,
                        affected_entities=[h_idx, (px, py), crop],
                        estimated_economic_relevance=price * 1.5,
                        candidate_transformation_family="MULTIWORKER_HARVEST_SYNCHRONIZATION",
                        dependency_info={"hand_id": h_idx, "target_pos": (px, py), "crop": crop, "price": price},
                        required_horizon=24,
                        rationale=f"Synchronized harvest: hand {h_idx} harvests mature {crop} at {(px, py)}",
                        confidence=0.90,
                        scientific_status=ScientificStatus.EXPERIMENTAL,
                    ))
                    break  # Assign at most 1 hand per plot

        return opportunities
