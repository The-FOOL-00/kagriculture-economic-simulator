# SPDX-License-Identifier: MIT
"""Downstream Asset Valuation and Execution Dependency Modeling for AEC (§7, V1.1).

NOTE: LOCAL_WEED_DIG is scientifically QUARANTINED for prospective execution.
Downstream weed removal valuation relies on unverified future assumptions (continuation
spatial stability, watering, harvest, transport, sale, market prices). The hiring-cost
heuristic fib_hire_cost / 24 is NOT an empirical marginal worker-turn opportunity cost.
This module is preserved strictly for research branch development and offline auditing.
"""

from __future__ import annotations

import math
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

try:
    from config import CROPS, FARMER_MOVES, compute_market_price, fib_hire_cost
except ImportError:
    import os
    import sys
    _REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    if _REPO not in sys.path:
        sys.path.insert(0, _REPO)
    from config import CROPS, FARMER_MOVES, compute_market_price, fib_hire_cost

# Standard expected baseline yields for mature crops (from kaggle-environments 1.32.7)
EXPECTED_CROP_YIELDS: Dict[str, int] = {
    "WHEAT": 4,       # yield range 1-6; 4 is standard nominal yield
    "CARROT": 4,      # max yield 4
    "TOMATO": 4,      # ongoing, 4 per cycle
    "STRAWBERRY": 4,  # ongoing, 4 per cycle
    "MELON": 6,       # max yield 6
}

# Grounded in hiring economics: fib(0)=$1 / 24 steps = $0.04167 per worker-step
DEFAULT_LABOR_COST_PER_STEP: float = float(fib_hire_cost(0)) / float(TURNS_PER_DAY)


@dataclass
class WeedValuation:
    """Explicit, auditable record of downstream weed removal value (§5, §6)."""
    tile: Tuple[int, int]
    worker_id: int
    has_downstream_dependency: bool
    dependency_type: Optional[str]               # "PLANT", "BUILD", "ROUTE"
    dependency_step_offset: Optional[int]
    crop: Optional[str]

    # Realized vs Projected Value Separation (§5)
    realized_delta_money: float = 0.0            # Always $0.0 at immediate DIG step
    projected_gross_profit: float = 0.0          # Deterministic downstream yield * price - seed
    action_opportunity_cost: float = 0.0         # Measured action / labor replacement cost
    net_projected_asset_value: float = 0.0       # projected_gross_profit - action_opportunity_cost

    # Audit and Feasibility Verification (§4, §5, §6)
    displaced_action: str = "PASS"               # Displaced baseline action
    projection_status: str = "NO_DEPENDENCY"     # "DETERMINISTIC_PROJECTION", "INFEASIBLE_TERMINAL_CUTOFF", etc.
    projected_asset_value_basis: str = ""

    delta_route_cost: float = 0.0
    delta_dependency_completion: float = 0.0
    rationale: str = ""

    # Backwards-compatibility properties for existing code/tests
    @property
    def gross_benefit(self) -> float:
        return self.projected_gross_profit

    @property
    def opportunity_cost(self) -> float:
        return self.action_opportunity_cost

    @property
    def net_asset_value(self) -> float:
        return self.net_projected_asset_value

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tile": self.tile,
            "worker_id": self.worker_id,
            "has_dependency": self.has_downstream_dependency,
            "dependency_type": self.dependency_type,
            "step_offset": self.dependency_step_offset,
            "crop": self.crop,
            "realized_delta_money": round(self.realized_delta_money, 2),
            "projected_gross_profit": round(self.projected_gross_profit, 2),
            "action_opportunity_cost": round(self.action_opportunity_cost, 4),
            "net_projected_asset_value": round(self.net_projected_asset_value, 2),
            "displaced_action": self.displaced_action,
            "projection_status": self.projection_status,
            "projected_asset_value_basis": self.projected_asset_value_basis,
            "gross_benefit": round(self.projected_gross_profit, 2),
            "opportunity_cost": round(self.action_opportunity_cost, 4),
            "net_asset_value": round(self.net_projected_asset_value, 2),
            "delta_route_cost": round(self.delta_route_cost, 2),
            "delta_dependency_completion": self.delta_dependency_completion,
            "rationale": self.rationale,
        }


class DownstreamAssetEvaluator:
    """Deterministic evaluator for downstream dependency completion and execution asset value."""

    def __init__(self, labor_cost_per_step: Optional[float] = None) -> None:
        self._custom_labor_cost = labor_cost_per_step
        self.labor_cost = labor_cost_per_step if labor_cost_per_step is not None else DEFAULT_LABOR_COST_PER_STEP

    def evaluate_weed_removal(
        self,
        tile: Tuple[int, int],
        worker_id: int,
        econ_state: EconomicState,
        continuation_actions: Optional[List[Dict[str, Any]]] = None,
        planned_route_savings: int = 0,
        baseline_worker_action: Optional[List[Any]] = None,
    ) -> WeedValuation:
        """Evaluate the net economic value of clearing a weed tile at (x, y).

        Decomposition:
            WEED_VALUE = Physical Benefit + Deterministic Downstream Benefit - Action Opportunity Cost

        Opportunity Cost (§4):
            Derived from replacement hiring economics (fib_hire_cost(hires_today) / 24.0)
            and displaced action type.

        Downstream Benefit (§5, §6):
            1. Biological feasibility (growth duration).
            2. Terminal cutoff (harvest_step <= 718).
            3. Operational feasibility (seed availability / cash).
            4. Route movement step savings.
        """
        tx, ty = tile

        # 1. Determine action opportunity cost grounded in game semantics
        displaced_op = "PASS"
        if baseline_worker_action and isinstance(baseline_worker_action, (list, tuple)) and baseline_worker_action:
            displaced_op = str(baseline_worker_action[0])

        hires_today = int(getattr(econ_state.farm, "hires_today", 0) or 0)
        hire_step_cost = float(fib_hire_cost(hires_today)) / float(TURNS_PER_DAY)

        if self._custom_labor_cost is not None:
            opp_cost = float(self._custom_labor_cost)
        else:
            if displaced_op in ("PLANT", "HARVEST", "WATER", "FERTILIZE"):
                opp_cost = max(25.0, hire_step_cost)
            else:
                opp_cost = hire_step_cost

        projected_gross_profit = 0.0
        dep_type: Optional[str] = None
        dep_offset: Optional[int] = None
        target_crop: Optional[str] = None
        delta_dep_completion = 0.0
        delta_route_cost = float(planned_route_savings)
        projection_status = "NO_DEPENDENCY"
        projected_basis = ""

        # 2. Route savings benefit (if digging eliminates movement detour)
        if planned_route_savings > 0:
            projected_gross_profit += planned_route_savings * (self.labor_cost or hire_step_cost)
            projection_status = "ROUTE_SAVINGS"
            projected_basis = f"Route movement savings: {planned_route_savings} steps @ ${hire_step_cost:.4f}/step"

        # 3. Inspect continuation actions for direct tile dependencies (PLANT / BUILD)
        if continuation_actions:
            worker = econ_state.workers.get_worker(worker_id)
            wx, wy = worker.position if worker else (tx, ty)

            for offset, act in enumerate(continuation_actions):
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

                # If worker reaches target tile and attempts an operation blocked by weed:
                if (wx, wy) == (tx, ty):
                    if op == "PLANT" and len(commands) >= 2:
                        crop = commands[1]
                        dep_type = "PLANT"
                        dep_offset = offset + 1
                        target_crop = crop

                        step_at_plant = econ_state.step + dep_offset
                        growth_days = CROPS.get(crop, {}).get("first_yield_day", 2)
                        growth_steps = growth_days * TURNS_PER_DAY
                        harvest_step = step_at_plant + growth_steps

                        seed_cost = CROP_SEED_PRICE.get(crop, 10)
                        has_seed = econ_state.farm.seeds.get(crop, 0) > 0
                        has_cash = econ_state.farm.cash >= seed_cost

                        if harvest_step > 718:
                            # Terminal cutoff: cannot mature and be harvested/sold before step 719
                            projection_status = "INFEASIBLE_TERMINAL_CUTOFF"
                            projected_gross_profit = 0.0
                            projected_basis = (
                                f"INFEASIBLE: {crop} plant_step={step_at_plant} + "
                                f"growth={growth_steps} = harvest_step={harvest_step} > 718"
                            )
                        elif not (has_seed or has_cash):
                            # Operational constraint: cannot afford seed
                            projection_status = "INFEASIBLE_INSUFFICIENT_SEED"
                            projected_gross_profit = 0.0
                            projected_basis = (
                                f"INFEASIBLE: cannot afford {crop} seed (${seed_cost}) "
                                f"with cash ${econ_state.farm.cash:.1f} and 0 seeds"
                            )
                        else:
                            expected_yield = EXPECTED_CROP_YIELDS.get(crop, 4)
                            market_inv = econ_state.market.market_inventory.get(crop, 10000)
                            price = compute_market_price(crop, market_inv)
                            crop_profit = max(0.0, float(expected_yield * price - seed_cost))
                            projected_gross_profit += crop_profit
                            delta_dep_completion = 1.0
                            projection_status = "DETERMINISTIC_PROJECTION"
                            projected_basis = (
                                f"DETERMINISTIC_CROP_PROJECTION: {crop} yield={expected_yield} @ ${price} "
                                f"- seed ${seed_cost} (matures step {harvest_step} <= 718)"
                            )
                        break

                    elif op in ("BUILD_COOP", "BUILD_PASTURE"):
                        dep_type = op
                        dep_offset = offset + 1
                        projected_gross_profit += 50.0  # Structure placement utility
                        delta_dep_completion = 1.0
                        projection_status = "DETERMINISTIC_PROJECTION"
                        projected_basis = f"DETERMINISTIC_STRUCTURE_PROJECTION: {op} placement"
                        break

        has_dep = bool(dep_type is not None or planned_route_savings > 0)
        net_val = projected_gross_profit - opp_cost

        if not has_dep:
            rationale = f"No downstream dependency on weed tile {(tx, ty)}; labor cost ${opp_cost:.4f} exceeds benefit $0.00"
        elif projection_status.startswith("INFEASIBLE"):
            rationale = f"Downstream dependency rejected: {projected_basis}"
        elif net_val > 0.0:
            rationale = (
                f"Downstream {dep_type} ({target_crop or ''}) at offset +{dep_offset} unblocked; "
                f"gross profit ${projected_gross_profit:.2f} exceeds labor opp cost ${opp_cost:.4f} (net ${net_val:.2f})"
            )
        else:
            rationale = (
                f"Downstream {dep_type} detected but net value ${net_val:.2f} is non-positive "
                f"(gross ${projected_gross_profit:.2f} <= labor cost ${opp_cost:.4f})"
            )

        return WeedValuation(
            tile=tile,
            worker_id=worker_id,
            has_downstream_dependency=has_dep,
            dependency_type=dep_type,
            dependency_step_offset=dep_offset,
            crop=target_crop,
            realized_delta_money=0.0,
            projected_gross_profit=projected_gross_profit,
            action_opportunity_cost=opp_cost,
            net_projected_asset_value=net_val,
            displaced_action=displaced_op,
            projection_status=projection_status,
            projected_asset_value_basis=projected_basis,
            delta_route_cost=delta_route_cost,
            delta_dependency_completion=delta_dep_completion,
            rationale=rationale
        )
