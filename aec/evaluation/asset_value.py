# SPDX-License-Identifier: MIT
"""Downstream Asset Valuation and Execution Dependency Modeling for AEC (§7, V1.1).

Computes deterministic downstream execution benefit and non-monetary dominance
metrics for transformations whose value is delayed or indirect (e.g., LOCAL_WEED_DIG).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from aec.config import (
    CROP_GROWTH_DAYS,
    CROP_SEED_PRICE,
    FINAL_STEP,
    TURNS_PER_DAY,
)
from aec.ir.economic_state import EconomicState
from aec.ir.market_state import BASE_PRICES

# Standard expected baseline yields for mature crops (from kaggle-environments 1.32.7)
EXPECTED_CROP_YIELDS: Dict[str, int] = {
    "WHEAT": 4,       # yield range 1-6; 4 is standard nominal yield
    "CARROT": 4,      # max yield 4
    "TOMATO": 4,      # ongoing, 4 per cycle
    "STRAWBERRY": 4,  # ongoing, 4 per cycle
    "MELON": 6,       # max yield 6
}

# Derived from game hiring economics: $100 / day (24 turns) = $4.1667 per worker-step
LABOR_COST_PER_STEP: float = 100.0 / float(TURNS_PER_DAY)


@dataclass
class WeedValuation:
    """Explicit, auditable record of downstream weed removal value."""
    tile: Tuple[int, int]
    worker_id: int
    has_downstream_dependency: bool
    dependency_type: Optional[str]               # "PLANT", "BUILD", "ROUTE"
    dependency_step_offset: Optional[int]
    crop: Optional[str]
    gross_benefit: float
    opportunity_cost: float
    net_asset_value: float
    delta_route_cost: float = 0.0
    delta_dependency_completion: float = 0.0
    rationale: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tile": self.tile,
            "worker_id": self.worker_id,
            "has_dependency": self.has_downstream_dependency,
            "dependency_type": self.dependency_type,
            "step_offset": self.dependency_step_offset,
            "crop": self.crop,
            "gross_benefit": round(self.gross_benefit, 2),
            "opportunity_cost": round(self.opportunity_cost, 2),
            "net_asset_value": round(self.net_asset_value, 2),
            "delta_route_cost": round(self.delta_route_cost, 2),
            "delta_dependency_completion": self.delta_dependency_completion,
            "rationale": self.rationale,
        }


class DownstreamAssetEvaluator:
    """Deterministic evaluator for downstream dependency completion and execution asset value."""

    def __init__(self, labor_cost_per_step: float = LABOR_COST_PER_STEP) -> None:
        self.labor_cost = labor_cost_per_step

    def evaluate_weed_removal(
        self,
        tile: Tuple[int, int],
        worker_id: int,
        econ_state: EconomicState,
        continuation_actions: Optional[List[Dict[str, Any]]] = None,
        planned_route_savings: int = 0
    ) -> WeedValuation:
        """Evaluate the net economic value of clearing a weed tile at (x, y).

        WEED_VALUE = Downstream Execution Benefit - Action Opportunity Cost

        Opportunity Cost:
            1 worker-turn = $4.167 (derived from $100 / 24 steps).

        Downstream Benefit:
            1. Unblocks planned PLANT or BUILD on tile (x, y) that would otherwise fail.
            2. Unlocks crop gross margin (expected yield * price - seed cost), discounted
               by remaining lifespan.
            3. Saves planned route movement steps (if route detour was required).
        """
        tx, ty = tile
        opp_cost = self.labor_cost
        gross_benefit = 0.0
        dep_type: Optional[str] = None
        dep_offset: Optional[int] = None
        target_crop: Optional[str] = None
        delta_dep_completion = 0.0
        delta_route_cost = float(planned_route_savings)

        # 1. Route savings benefit (if digging eliminates movement friction / detour)
        if planned_route_savings > 0:
            gross_benefit += planned_route_savings * self.labor_cost

        # 2. Inspect continuation actions for direct tile dependencies (PLANT / BUILD)
        if continuation_actions:
            # Reconstruct worker position tracking across continuation
            worker = econ_state.workers.get_worker(worker_id)
            wx, wy = worker.position if worker else (tx, ty)

            for offset, act in enumerate(continuation_actions):
                # Check commands for this worker
                commands = []
                if worker_id == 0:
                    commands = act.get("farmer", ["PASS"])
                else:
                    hands = act.get("hands", []) or []
                    h_idx = worker_id - 1
                    commands = hands[h_idx] if h_idx < len(hands) else ["PASS"]

                if not isinstance(commands, (list, tuple)) or not commands:
                    continue

                op = commands[0]

                # Update virtual position for route tracking
                if op == "NORTH":
                    wy -= 1
                elif op == "SOUTH":
                    wy += 1
                elif op == "EAST":
                    wx += 1
                elif op == "WEST":
                    wx -= 1

                # If worker is at the target tile and attempting an operation blocked by weed:
                if (wx, wy) == (tx, ty):
                    if op == "PLANT" and len(commands) >= 2:
                        crop = commands[1]
                        dep_type = "PLANT"
                        dep_offset = offset + 1
                        target_crop = crop

                        # Verify biological feasibility: can this crop mature before game end?
                        step_at_plant = econ_state.step + dep_offset
                        growth_days = CROP_GROWTH_DAYS.get(crop, 2)
                        remaining_steps = max(0, FINAL_STEP - step_at_plant)
                        remaining_days = remaining_steps // TURNS_PER_DAY

                        if remaining_days >= growth_days:
                            # Feasible crop: calculate net yield profit
                            expected_yield = EXPECTED_CROP_YIELDS.get(crop, 4)
                            price = econ_state.market.current_prices.get(crop, BASE_PRICES.get(crop, 10))
                            seed_cost = CROP_SEED_PRICE.get(crop, 20)
                            crop_profit = max(0.0, float(expected_yield * price - seed_cost))
                            gross_benefit += crop_profit
                            delta_dep_completion = 1.0
                        else:
                            # Crop cannot mature before game ends: 0 gross benefit
                            gross_benefit += 0.0
                            delta_dep_completion = 0.0
                        break

                    elif op in ("BUILD_COOP", "BUILD_PASTURE"):
                        dep_type = op
                        dep_offset = offset + 1
                        # Structure placement value (enables subsequent animal placement)
                        gross_benefit += 50.0  # Conservative structure utility
                        delta_dep_completion = 1.0
                        break

        has_dep = bool(dep_type is not None or planned_route_savings > 0)
        net_val = gross_benefit - opp_cost

        if not has_dep:
            rationale = f"No downstream dependency on weed tile {(tx, ty)}; labor cost ${opp_cost:.2f} exceeds benefit $0.0"
        elif net_val > 0.0:
            rationale = (
                f"Downstream {dep_type} ({target_crop or ''}) at offset +{dep_offset} unblocked; "
                f"gross benefit ${gross_benefit:.2f} exceeds labor cost ${opp_cost:.2f} (net ${net_val:.2f})"
            )
        else:
            rationale = (
                f"Downstream {dep_type} detected but net value ${net_val:.2f} is non-positive "
                f"(gross ${gross_benefit:.2f} <= labor cost ${opp_cost:.2f})"
            )

        return WeedValuation(
            tile=tile,
            worker_id=worker_id,
            has_downstream_dependency=has_dep,
            dependency_type=dep_type,
            dependency_step_offset=dep_offset,
            crop=target_crop,
            gross_benefit=gross_benefit,
            opportunity_cost=opp_cost,
            net_asset_value=net_val,
            delta_route_cost=delta_route_cost,
            delta_dependency_completion=delta_dep_completion,
            rationale=rationale
        )
