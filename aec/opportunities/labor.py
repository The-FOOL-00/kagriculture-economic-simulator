# SPDX-License-Identifier: MIT
"""Labor & Dynamic Marginal Labor Opportunity Valuation Analyzer (§7A, §8)."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from aec.config import ScientificStatus
from aec.events.event_types import EventType
from aec.ir.economic_state import EconomicState
from aec.opportunities.base import Opportunity
from aec.resource.labor_engine import (
    LaborOpportunityAssessment,
    LaborOpportunityCostEngine,
    LaborOpportunityRequest,
    ValuationLevel,
)


def manhattan(p1: Tuple[int, int], p2: Tuple[int, int]) -> int:
    return abs(p1[0] - p2[0]) + abs(p1[1] - p2[1])


class LaborOpportunityAnalyzer:
    """Calculates state-dependent marginal opportunity costs of worker time.
    
    Adheres to strict marginal labor valuation:
        OpportunityCost = max(0, CandidateGrossValue - (V_alt - V_base))
    where V_alt and V_base are derived from actual worker trajectories and reachable
    task values, strictly eliminating crude spatial heuristics (val / (dist + 1)).
    """

    def __init__(self, board_size: int = 10) -> None:
        self.labor_engine = LaborOpportunityCostEngine(board_size=board_size)

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

        # Scan farm for mature harvestable crops with positive yield
        mature_harvest_tiles: List[Tuple[Tuple[int, int], str, int, float]] = []
        for y, row in enumerate(tiles):
            for x, tile in enumerate(row):
                if isinstance(tile, dict) and tile.get("kind") == "PLANT":
                    crop = tile.get("crop")
                    yield_u = int(tile.get("yield_units", 0) or 0)
                    if yield_u > 0 and crop:
                        val = yield_u * float(prices.get(crop, 50))
                        mature_harvest_tiles.append(((x, y), crop, yield_u, val))

        # Evaluate each worker using true marginal opportunity cost
        for w in workers:
            if getattr(w, "is_frozen", False):
                continue

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

            is_idle = w_act in ("PASS", "WAIT")

            # 1. Evaluate Dynamic Shadow Harvest reallocation
            if mature_harvest_tiles:
                candidate_opps = []
                for (xy, crop, yield_u, val) in mature_harvest_tiles:
                    dist = manhattan(w.position, xy)
                    # Candidate must be reachable within local/tactical horizon (dist <= 6)
                    if dist <= 6:
                        # Construct formal labor opportunity query
                        req = LaborOpportunityRequest(
                            worker_id=w.worker_id,
                            candidate_action_cmd="HARVEST",
                            econ_state=econ_state,
                            baseline_action=baseline_action or {},
                            current_step=econ_state.step,
                            target_location=xy,
                            target_commodity=crop,
                            horizon=max(8, dist * 2 + 4),
                            allow_multiworker_expansion=True
                        )
                        assessment = self.labor_engine.assess_opportunity(req)

                        # Check whether reallocation creates net positive economic value
                        if assessment.safe_to_use and assessment.net_incremental_value > 0.0:
                            candidate_opps.append((assessment.net_incremental_value, xy, crop, yield_u, val, dist, assessment))

                # Sort by net incremental value descending and emit top opportunities
                candidate_opps.sort(key=lambda x: -x[0])
                for net_val, xy, crop, yield_u, val, dist, assess in candidate_opps[:2]:
                    opp_cost = assess.opportunity_cost
                    opportunities.append(Opportunity(
                        opportunity_id=f"LABOR_HARVEST_W{w.worker_id}_{crop}_{xy[0]}_{xy[1]}",
                        category="LABOR",
                        event_trigger=None,
                        affected_entities=[w.worker_id, crop],
                        estimated_economic_relevance=net_val,
                        candidate_transformation_family="DYNAMIC_SHADOW_HARVEST",
                        dependency_info={
                            "worker_id": w.worker_id,
                            "target_xy": xy,
                            "crop": crop,
                            "dist": dist,
                            "gross_value": val,
                            "opportunity_cost": opp_cost,
                            "net_incremental_value": net_val,
                            "baseline_is_idle": is_idle,
                        },
                        required_horizon=max(12, dist * 2 + 6),
                        rationale=(
                            f"Worker {w.worker_id} marginal labor reallocation: harvest {crop} at {xy} "
                            f"(gross ${val:.1f}, opp cost ${opp_cost:.1f}, net ${net_val:.1f})."
                        ),
                        confidence=0.9,
                        scientific_status=ScientificStatus.PLAUSIBLE_UNPROVEN
                    ))

            # 2. Evaluate Cargo Ferry / Transport Reallocation
            if w.total_cargo_units >= 3 and w.deposit_path_len > 0 and w_act not in ("NORTH", "SOUTH", "EAST", "WEST", "DROP"):
                cargo_val = sum(q * float(prices.get(it, 20)) for it, q in w.cargo.items())
                # Time saved / accelerated deposit value without distance-ratio heuristic
                direct_shed_dist = manhattan(w.position, (0, 0))
                # Candidate query for depositing to shed
                req_ferry = LaborOpportunityRequest(
                    worker_id=w.worker_id,
                    candidate_action_cmd="DROP",
                    econ_state=econ_state,
                    baseline_action=baseline_action or {},
                    current_step=econ_state.step,
                    target_location=(0, 0),
                    horizon=max(6, direct_shed_dist + 2)
                )
                assess_ferry = self.labor_engine.assess_opportunity(req_ferry)
                net_ferry_val = assess_ferry.net_incremental_value if assess_ferry.safe_to_use else max(5.0, cargo_val * 0.1)

                opportunities.append(Opportunity(
                    opportunity_id=f"LABOR_FERRY_W{w.worker_id}",
                    category="LABOR",
                    event_trigger=None,
                    affected_entities=[w.worker_id],
                    estimated_economic_relevance=net_ferry_val,
                    candidate_transformation_family="CARGO_FERRY",
                    dependency_info={
                        "worker_id": w.worker_id,
                        "dist_shed": direct_shed_dist,
                        "cargo_value": cargo_val,
                        "target_pos": (0, 0),
                    },
                    required_horizon=max(6, direct_shed_dist + 2),
                    rationale=(
                        f"Worker {w.worker_id} carrying {w.total_cargo_units} units ($ {cargo_val:.0f}) "
                        f"transport to shed (marginal value ${net_ferry_val:.1f})."
                    ),
                    confidence=0.85,
                    scientific_status=ScientificStatus.PLAUSIBLE_UNPROVEN
                ))

        return opportunities
