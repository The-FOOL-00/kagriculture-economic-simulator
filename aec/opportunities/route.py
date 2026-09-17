# SPDX-License-Identifier: MIT
"""Route Opportunity Analyzer (7B)."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from aec.config import ScientificStatus
from aec.events.event_types import EventType
from aec.ir.economic_state import EconomicState
from aec.opportunities.base import Opportunity


class RouteOpportunityAnalyzer:
    """Detects local obstructions, collisions, and path compression opportunities."""

    def analyze(
        self,
        econ_state: EconomicState,
        events: List[Any],
        baseline_action: Optional[Dict[str, Any]] = None
    ) -> List[Opportunity]:
        opportunities: List[Opportunity] = []
        tiles = econ_state.farm.tiles

        # Check for weed obstruction on worker tile
        for w in econ_state.workers.workers:
            x, y = w.position
            if 0 <= y < len(tiles) and 0 <= x < len(tiles[y]):
                t = tiles[y][x]
                if isinstance(t, dict) and t.get("kind") == "WEED":
                    opportunities.append(Opportunity(
                        opportunity_id=f"ROUTE_WEED_DIG_W{w.worker_id}_{x}_{y}",
                        category="ROUTE",
                        event_trigger=EventType.E1_FARM_OBSTRUCTION,
                        affected_entities=[w.worker_id, (x, y)],
                        estimated_economic_relevance=100.0,
                        candidate_transformation_family="LOCAL_WEED_DIG",
                        dependency_info={"worker_id": w.worker_id, "tile": (x, y)},
                        required_horizon=4,
                        rationale=f"Worker {w.worker_id} standing on weed at {(x, y)}; DIG clears path",
                        confidence=1.0,
                        scientific_status=ScientificStatus.QUARANTINED
                    ))

        return opportunities
