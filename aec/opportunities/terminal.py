# SPDX-License-Identifier: MIT
"""Terminal Opportunity Analyzer (7F)."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from aec.config import FINAL_STEP, ScientificStatus
from aec.events.event_types import EventType
from aec.ir.economic_state import EconomicState
from aec.opportunities.base import Opportunity


class TerminalOpportunityAnalyzer:
    """Detects phase shutdown cutoffs, terminal harvest sweep, and step 718 liquidation."""

    def analyze(
        self,
        econ_state: EconomicState,
        events: List[Any],
        baseline_action: Optional[Dict[str, Any]] = None
    ) -> List[Opportunity]:
        opportunities: List[Opportunity] = []
        step = econ_state.step

        # Step 718 Terminal Liquidation
        if step == FINAL_STEP:
            shed_total = econ_state.farm.shed_total_units
            if shed_total > 0:
                opportunities.append(Opportunity(
                    opportunity_id=f"TERMINAL_LIQUIDATE_STEP_{step}",
                    category="TERMINAL",
                    event_trigger=EventType.E8_TERMINAL_TRANSITION,
                    affected_entities=["SHED_LIQUIDATION"],
                    estimated_economic_relevance=float(shed_total * 50),
                    candidate_transformation_family="TERMINAL_LIQUIDATION",
                    dependency_info={"shed": econ_state.farm.shed_inventory},
                    required_horizon=1,
                    rationale=f"Step 718 final liquidation of {shed_total} units in shed",
                    confidence=1.0,
                    scientific_status=ScientificStatus.REUSED_SAFETY
                ))

        # Late-Game Harvest & Liquidation Sweep (steps 672–717) (§5, §14)
        elif step >= 672:
            remaining_runway = FINAL_STEP - step
            tiles = econ_state.farm.tiles
            workers = [w for w in econ_state.workers.workers if not getattr(w, "is_frozen", False)]
            prices = econ_state.market.current_prices
            shed_inv = econ_state.farm.shed_inventory
            shed_capacity_remaining = max(0, 100 - sum(shed_inv.values()))

            # 1. Recover stranded cargo carried by active workers
            for w in workers:
                if w.total_cargo_units > 0 and shed_capacity_remaining >= w.total_cargo_units:
                    from aec.config import SHED_TILES
                    d_shed = min(abs(w.position[0] - st[0]) + abs(w.position[1] - st[1]) for st in SHED_TILES)
                    # Feasibility proof: worker must reach shed and DROP before FINAL_STEP
                    if d_shed + 1 <= remaining_runway:
                        cargo_val = sum(qty * float(prices.get(c, 50.0)) for c, qty in w.cargo.items())
                        primary_crop = max(w.cargo.keys(), key=lambda k: w.cargo[k]) if w.cargo else "CARROT"
                        opportunities.append(Opportunity(
                            opportunity_id=f"TERMINAL_SWEEP_DELIVER_W{w.worker_id}_S{step}",
                            category="TERMINAL",
                            event_trigger=EventType.E8_TERMINAL_TRANSITION,
                            affected_entities=[w.worker_id, "CARGO_DELIVER"],
                            estimated_economic_relevance=cargo_val,
                            candidate_transformation_family="TERMINAL_HARVEST_SWEEP",
                            dependency_info={
                                "worker_id": w.worker_id,
                                "target_xy": w.position,
                                "crop": primary_crop,
                                "yield_units": 0,
                                "dist": d_shed,
                                "is_cargo_deliver": True,
                            },
                            required_horizon=max(4, d_shed + 2),
                            rationale=f"Terminal cargo salvage: Worker {w.worker_id} deliver {w.total_cargo_units} carried units to shed before step {FINAL_STEP}",
                            confidence=0.98,
                            scientific_status=ScientificStatus.REUSED_SAFETY
                        ))

            # 2. Sweep mature field crops with hard feasibility proof
            mature_tiles = []
            for y, row in enumerate(tiles):
                for x, tile in enumerate(row):
                    if isinstance(tile, dict) and tile.get("kind") == "PLANT":
                        crop = tile.get("crop")
                        yield_u = int(tile.get("yield_units", 0) or 0)
                        if yield_u > 0 and crop and (yield_u <= shed_capacity_remaining):
                            mature_tiles.append(((x, y), crop, yield_u))

            if mature_tiles and workers:
                from aec.config import SHED_TILES
                for (xy, crop, yield_u) in mature_tiles:
                    # Find worker with feasible coupled trajectory: route(crop) + HARVEST + route(shed) + DROP <= runway
                    for w in workers:
                        d_to_crop = abs(w.position[0] - xy[0]) + abs(w.position[1] - xy[1])
                        d_crop_to_shed = min(abs(xy[0] - st[0]) + abs(xy[1] - st[1]) for st in SHED_TILES)
                        total_req_turns = d_to_crop + 1 + d_crop_to_shed + 1
                        if total_req_turns <= remaining_runway:
                            val = yield_u * float(prices.get(crop, 50.0))
                            opportunities.append(Opportunity(
                                opportunity_id=f"TERMINAL_SWEEP_W{w.worker_id}_{crop}_{xy[0]}_{xy[1]}",
                                category="TERMINAL",
                                event_trigger=EventType.E8_TERMINAL_TRANSITION,
                                affected_entities=[w.worker_id, crop],
                                estimated_economic_relevance=val - (total_req_turns * 0.1),
                                candidate_transformation_family="TERMINAL_HARVEST_SWEEP",
                                dependency_info={
                                    "worker_id": w.worker_id,
                                    "target_xy": xy,
                                    "crop": crop,
                                    "yield_units": yield_u,
                                    "dist": d_to_crop,
                                    "total_req_turns": total_req_turns,
                                },
                                required_horizon=min(remaining_runway, max(6, total_req_turns + 2)),
                                rationale=f"Terminal harvest sweep: Worker {w.worker_id} salvage {crop} at {xy} ({total_req_turns} turns <= {remaining_runway} runway).",
                                confidence=0.95,
                                scientific_status=ScientificStatus.REUSED_SAFETY
                            ))
                            break  # best worker found for this crop

            # Sort opportunities by estimated realizable economic relevance
            opportunities.sort(key=lambda o: o.estimated_economic_relevance, reverse=True)
            opportunities = opportunities[:8]

        # Phase Shutdown: Prevent dead-capital planting
        if step >= 574:
            for crop, feasible in econ_state.crop_feasibility.items():
                if not feasible:
                    opportunities.append(Opportunity(
                        opportunity_id=f"TERMINAL_SHUTDOWN_{crop}_{step}",
                        category="TERMINAL",
                        event_trigger=EventType.E7_PRODUCTION_DEADLINE,
                        affected_entities=[crop],
                        estimated_economic_relevance=50.0,
                        candidate_transformation_family="PHASE_SHUTDOWN",
                        dependency_info={"crop": crop, "cutoff_step": step},
                        required_horizon=6,
                        rationale=f"Halt {crop} planting: cannot mature before game end",
                        confidence=1.0,
                        scientific_status=ScientificStatus.VERIFIED_SOURCE
                    ))

        return opportunities
