# SPDX-License-Identifier: MIT
"""AEC-RESOURCE: Dynamic Inventory Conversion Catalog and Bounded Discovery (§8, §9, §10, §11).

Defines exact game conversion recipes, multi-stage conversion chains,
working-capital liquidity coupling, strict auxiliary labor classification,
and bounded discovery without arbitrary dollar thresholds.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple

from aec.config import (
    CROP_GROWTH_DAYS,
    CROP_SEED_PRICE,
    CROPS,
    PRODUCTS,
    SHED_CAPACITY,
    TURNS_PER_DAY,
)
from aec.ir.economic_state import EconomicState
from aec.resource.labor import (
    ConversionLaborClass,
    ConversionLaborPreconditionValidator,
)
from aec.resource.liquidity import (
    ConversionCausalPathType,
    ConversionLiquidityAnalyzer,
    ConversionLiquidityProfile,
)


@dataclass
class ConversionRecipe:
    """A discrete, physical or market transformation permitted by game rules (§8)."""
    recipe_id: str
    name: str
    input_resources: Dict[str, int]     # Commodity/item -> units required
    output_resources: Dict[str, int]    # Commodity/item -> units produced
    duration_steps: int                 # Steps from start to availability
    cash_cost_est: float = 0.0          # Immediate monetary cost
    requires_worker: bool = False
    requires_structure: Optional[str] = None # e.g. "PASTURE", "COOP", "PLANT"
    shed_capacity_delta: int = 0        # Net change in shed storage
    is_terminal_only: bool = False


@dataclass
class ConversionExecutionPlan:
    """Formal physical execution plan for a conversion path (§3, §4)."""
    plan_id: str
    conversion_id: str
    target_commodity: str
    required_inputs: Dict[str, int]
    produced_outputs: Dict[str, int]
    prerequisites: List[str] = field(default_factory=list)
    worker_id: Optional[int] = None
    target_location: Optional[Tuple[int, int]] = None
    market_actions: List[List[Any]] = field(default_factory=list)
    worker_actions: List[str] = field(default_factory=list)
    reconnect_required: bool = False
    start_step: int = 0
    estimated_duration: int = 1
    net_value_est: float = 0.0
    is_executable: bool = True
    infeasibility_reason: Optional[str] = None
    labor_class: ConversionLaborClass = ConversionLaborClass.AUXILIARY_WORKER_REQUIRED
    opportunity_family: str = "RESOURCE_CONVERSION"
    attribution_info: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "conversion_id": self.conversion_id,
            "target_commodity": self.target_commodity,
            "required_inputs": self.required_inputs,
            "produced_outputs": self.produced_outputs,
            "prerequisites": self.prerequisites,
            "worker_id": self.worker_id,
            "target_location": list(self.target_location) if self.target_location else None,
            "market_actions": self.market_actions,
            "worker_actions": self.worker_actions,
            "reconnect_required": self.reconnect_required,
            "start_step": self.start_step,
            "estimated_duration": self.estimated_duration,
            "net_value_est": self.net_value_est,
            "is_executable": self.is_executable,
            "infeasibility_reason": self.infeasibility_reason,
            "labor_class": self.labor_class.value if isinstance(self.labor_class, ConversionLaborClass) else str(self.labor_class),
            "opportunity_family": self.opportunity_family,
            "attribution_info": self.attribution_info,
        }


@dataclass
class ConversionPath:
    """A single-step or multi-step conversion trajectory (§8)."""
    path_id: str
    target_commodity: str
    recipes: List[ConversionRecipe]
    total_steps: int
    total_cost_est: float
    expected_revenue_est: float
    net_value_est: float
    is_feasible: bool = True
    infeasibility_reason: Optional[str] = None
    execution_plan: Optional[ConversionExecutionPlan] = None
    labor_class: ConversionLaborClass = ConversionLaborClass.AUXILIARY_WORKER_REQUIRED
    liquidity_profile: Optional[ConversionLiquidityProfile] = None
    opportunity_family: str = "RESOURCE_CONVERSION"


class ConversionCatalog:
    """Authoritative repository of exact game transformations."""

    @staticmethod
    def get_standard_recipes() -> Dict[str, ConversionRecipe]:
        return {
            "BUY_WHEAT_FEED": ConversionRecipe(
                recipe_id="BUY_WHEAT_FEED",
                name="Market Purchase of Wheat Feed",
                input_resources={"CASH": 25},
                output_resources={"WHEAT": 1},
                duration_steps=1,
                cash_cost_est=25.0,
                requires_worker=False,
                shed_capacity_delta=1
            ),
            "FEED_LIVESTOCK_COW": ConversionRecipe(
                recipe_id="FEED_LIVESTOCK_COW",
                name="Feed Cow for Milk Production",
                input_resources={"WHEAT": 1},
                output_resources={"MILK": 1, "FERTILIZER": 1},
                duration_steps=48,     # 2 days interval
                cash_cost_est=0.0,
                requires_worker=True,
                requires_structure="PASTURE",
                shed_capacity_delta=0  # Shed neutral until dropped
            ),
            "FEED_LIVESTOCK_SHEEP": ConversionRecipe(
                recipe_id="FEED_LIVESTOCK_SHEEP",
                name="Feed Sheep for Wool Production",
                input_resources={"WHEAT": 1},
                output_resources={"WOOL": 1, "FERTILIZER": 1},
                duration_steps=72,     # 3 days interval
                cash_cost_est=0.0,
                requires_worker=True,
                requires_structure="PASTURE",
                shed_capacity_delta=0
            ),
            "FEED_LIVESTOCK_GOOSE": ConversionRecipe(
                recipe_id="FEED_LIVESTOCK_GOOSE",
                name="Feed Goose for Egg Production",
                input_resources={"WHEAT": 1},
                output_resources={"EGG": 1, "FERTILIZER": 1},
                duration_steps=24,     # 1 day interval
                cash_cost_est=0.0,
                requires_worker=True,
                requires_structure="COOP",
                shed_capacity_delta=0
            ),
            "GROW_WHEAT_CROP": ConversionRecipe(
                recipe_id="GROW_WHEAT_CROP",
                name="Grow Wheat from Seed",
                input_resources={"CASH": 10},
                output_resources={"WHEAT": 4},
                duration_steps=CROP_GROWTH_DAYS["WHEAT"] * TURNS_PER_DAY, # 48 steps
                cash_cost_est=10.0,
                requires_worker=True,
                requires_structure=None,
                shed_capacity_delta=0
            ),
            "GROW_CARROT_CROP": ConversionRecipe(
                recipe_id="GROW_CARROT_CROP",
                name="Grow Carrot from Seed",
                input_resources={"CASH": 20},
                output_resources={"CARROT": 4},
                duration_steps=CROP_GROWTH_DAYS["CARROT"] * TURNS_PER_DAY, # 48 steps
                cash_cost_est=20.0,
                requires_worker=True,
                shed_capacity_delta=0
            ),
            "GROW_MELON_CROP": ConversionRecipe(
                recipe_id="GROW_MELON_CROP",
                name="Grow Melon from Seed",
                input_resources={"CASH": 80},
                output_resources={"MELON": 6},
                duration_steps=CROP_GROWTH_DAYS["MELON"] * TURNS_PER_DAY, # 240 steps
                cash_cost_est=80.0,
                requires_worker=True,
                shed_capacity_delta=0
            ),
            "TERMINAL_LIQUIDATE_COMMODITY": ConversionRecipe(
                recipe_id="TERMINAL_LIQUIDATE_COMMODITY",
                name="Step 718 Terminal Shed Liquidation",
                input_resources={"SHED_COMMODITY": 1},
                output_resources={"CASH": 1}, # Unit value resolved at pricing
                duration_steps=1,
                cash_cost_est=0.0,
                requires_worker=False,
                shed_capacity_delta=-1,
                is_terminal_only=True
            ),
        }


class ConversionDiscoveryEngine:
    """Discovers feasible, economically relevant conversion chains (§8, §10, §11, §12)."""

    def __init__(self) -> None:
        self.catalog = ConversionCatalog()
        self.liquidity_analyzer = ConversionLiquidityAnalyzer()
        self.labor_validator = ConversionLaborPreconditionValidator()

    def discover_conversion_paths(
        self,
        econ_state: EconomicState,
        max_horizon: int = 48,
        baseline_trajectory: Optional[List[Dict[str, Any]]] = None
    ) -> List[ConversionPath]:
        """Bounded discovery of valid conversion paths constrained by cash liquidity, capacity, and terminal distance."""
        paths: List[ConversionPath] = []
        recipes = self.catalog.get_standard_recipes()
        remaining_steps = econ_state.remaining_horizon

        # 1. Animal Feed Conversion Paths (genuine physical transformations)
        tiles = econ_state.farm.tiles
        has_cow = False
        has_sheep = False
        has_goose = False

        for row in tiles:
            for tile in row:
                if isinstance(tile, dict) and "animal" in tile:
                    sub = tile["animal"]
                    if sub == "COW":
                        has_cow = True
                    elif sub == "SHEEP":
                        has_sheep = True
                    elif sub == "GOOSE":
                        has_goose = True

        wheat_price = float(econ_state.market.get_price("WHEAT"))
        milk_price = float(econ_state.market.get_price("MILK"))
        wool_price = float(econ_state.market.get_price("WOOL"))
        egg_price = float(econ_state.market.get_price("EGG"))

        # Cow chain: Buy Wheat -> Feed Cow -> Milk
        if has_cow and remaining_steps >= 48:
            cow_path = ConversionPath(
                path_id="CONV_CHAIN_WHEAT_TO_MILK",
                target_commodity="MILK",
                recipes=[recipes["BUY_WHEAT_FEED"], recipes["FEED_LIVESTOCK_COW"]],
                total_steps=49,
                total_cost_est=wheat_price,
                expected_revenue_est=milk_price,
                net_value_est=milk_price - wheat_price,
                labor_class=ConversionLaborClass.AUXILIARY_WORKER_REQUIRED,
                opportunity_family="RESOURCE_CONVERSION"
            )
            is_feas, reason = self.check_path_feasibility(cow_path, econ_state, baseline_trajectory)
            cow_path.is_feasible = is_feas
            cow_path.infeasibility_reason = reason
            paths.append(cow_path)

        # Goose chain: Buy Wheat -> Feed Goose -> Egg
        if has_goose and remaining_steps >= 24:
            goose_path = ConversionPath(
                path_id="CONV_CHAIN_WHEAT_TO_EGG",
                target_commodity="EGG",
                recipes=[recipes["BUY_WHEAT_FEED"], recipes["FEED_LIVESTOCK_GOOSE"]],
                total_steps=25,
                total_cost_est=wheat_price,
                expected_revenue_est=egg_price,
                net_value_est=egg_price - wheat_price,
                labor_class=ConversionLaborClass.AUXILIARY_WORKER_REQUIRED,
                opportunity_family="RESOURCE_CONVERSION"
            )
            is_feas, reason = self.check_path_feasibility(goose_path, econ_state, baseline_trajectory)
            goose_path.is_feasible = is_feas
            goose_path.infeasibility_reason = reason
            paths.append(goose_path)

        # Sheep chain: Buy Wheat -> Feed Sheep -> Wool
        if has_sheep and remaining_steps >= 72:
            sheep_path = ConversionPath(
                path_id="CONV_CHAIN_WHEAT_TO_WOOL",
                target_commodity="WOOL",
                recipes=[recipes["BUY_WHEAT_FEED"], recipes["FEED_LIVESTOCK_SHEEP"]],
                total_steps=73,
                total_cost_est=wheat_price,
                expected_revenue_est=wool_price,
                net_value_est=wool_price - wheat_price,
                labor_class=ConversionLaborClass.AUXILIARY_WORKER_REQUIRED,
                opportunity_family="RESOURCE_CONVERSION"
            )
            is_feas, reason = self.check_path_feasibility(sheep_path, econ_state, baseline_trajectory)
            sheep_path.is_feasible = is_feas
            sheep_path.infeasibility_reason = reason
            sheep_path.execution_plan = self.synthesize_execution_plan(sheep_path, econ_state)
            paths.append(sheep_path)

        # 2. Fast Crop Cycle: Carrot cycle (Classified as RESOURCE_ACQUISITION §13, §14)
        carrot_price = float(econ_state.market.get_price("CARROT"))
        if remaining_steps >= 48:
            carrot_path = ConversionPath(
                path_id="CONV_CHAIN_SEED_TO_CARROT",
                target_commodity="CARROT",
                recipes=[recipes["GROW_CARROT_CROP"]],
                total_steps=48,
                total_cost_est=20.0,
                expected_revenue_est=carrot_price * 4,
                net_value_est=(carrot_price * 4) - 20.0,
                labor_class=ConversionLaborClass.NO_WORKER_REQUIRED,
                opportunity_family="RESOURCE_ACQUISITION"
            )
            is_feas, reason = self.check_path_feasibility(carrot_path, econ_state, baseline_trajectory)
            carrot_path.is_feasible = is_feas
            carrot_path.infeasibility_reason = reason
            carrot_path.execution_plan = self.synthesize_execution_plan(carrot_path, econ_state)
            paths.append(carrot_path)

        # Populate execution plans for paths
        for p in paths:
            if p.execution_plan is None and p.is_feasible:
                p.execution_plan = self.synthesize_execution_plan(p, econ_state)

        return paths

    def check_path_feasibility(
        self,
        path: ConversionPath,
        econ_state: EconomicState,
        baseline_trajectory: Optional[List[Dict[str, Any]]] = None
    ) -> Tuple[bool, Optional[str]]:
        """Verify strict cash liquidity, shed capacity, and terminal horizon constraints (§10, §11, §12)."""
        current_shed = econ_state.farm.shed_total_units
        remaining_steps = econ_state.remaining_horizon

        # 1. Terminal distance feasibility (§12)
        if path.total_steps > remaining_steps:
            return False, f"Terminal infeasibility: path requires {path.total_steps} steps, but only {remaining_steps} remain"

        # 2. Shed capacity feasibility (§11)
        accum_shed = current_shed
        for r in path.recipes:
            accum_shed += r.shed_capacity_delta
            if accum_shed > SHED_CAPACITY:
                return False, f"Shed capacity overflow: projected storage {accum_shed} exceeds limit {SHED_CAPACITY}"

        # 3. Exact Working-Capital Liquidity & Causal Realizable Value Analysis (§4, §5, §7)
        profile = self.liquidity_analyzer.analyze_profile(
            candidate_target=path.target_commodity,
            upfront_cost=path.total_cost_est,
            duration_steps=path.total_steps,
            expected_revenue=path.expected_revenue_est,
            econ_state=econ_state,
            baseline_trajectory=baseline_trajectory
        )
        path.liquidity_profile = profile

        if not profile.is_solvent_trajectory:
            return False, profile.insolvency_reason or "Working-capital liquidity failure"

        return True, None

    def synthesize_execution_plan(
        self,
        path: ConversionPath,
        econ_state: EconomicState
    ) -> Optional[ConversionExecutionPlan]:
        """Synthesizes physical market orders and worker actions for a feasible conversion path (§2, §3, §4)."""
        if not path.is_feasible:
            return None

        target_animal_map = {
            "MILK": "COW",
            "EGG": "GOOSE",
            "WOOL": "SHEEP"
        }

        if path.target_commodity in target_animal_map:
            animal_type = target_animal_map[path.target_commodity]
            target_loc = None
            tiles = econ_state.farm.tiles
            for y, row in enumerate(tiles):
                for x, tile in enumerate(row):
                    if isinstance(tile, dict) and tile.get("animal") == animal_type:
                        target_loc = (x, y)
                        break
                if target_loc:
                    break

            if not target_loc:
                return None

            wheat_in_shed = econ_state.farm.get_shed_qty("WHEAT")
            wheat_in_hands = econ_state.farm.carried_inventory.get("WHEAT", 0)

            # Prefer auxiliary worker if present
            worker_id = 1 if len(econ_state.workers.workers) > 1 else 0
            worker = econ_state.workers.get_worker(worker_id) or econ_state.workers.get_worker(0)
            if not worker:
                return None

            wx, wy = worker.position
            market_actions: List[List[Any]] = []
            worker_actions: List[str] = []
            reconnect_required = False

            if wheat_in_shed == 0 and wheat_in_hands == 0:
                market_actions.append(["BUY_PRODUCT", "WHEAT", 1])
                if (wx, wy) == target_loc:
                    worker_actions = ["PASS"]
                else:
                    reconnect_required = True
                    tx, ty = target_loc
                    if tx > wx: worker_actions = ["EAST"]
                    elif tx < wx: worker_actions = ["WEST"]
                    elif ty > wy: worker_actions = ["SOUTH"]
                    else: worker_actions = ["NORTH"]
            elif wheat_in_hands > 0:
                if (wx, wy) == target_loc:
                    worker_actions = ["FEED"]
                    reconnect_required = False
                else:
                    reconnect_required = True
                    tx, ty = target_loc
                    if tx > wx: worker_actions = ["EAST"]
                    elif tx < wx: worker_actions = ["WEST"]
                    elif ty > wy: worker_actions = ["SOUTH"]
                    else: worker_actions = ["NORTH"]
            else:
                # Wheat is in shed; worker pickups or approaches shed
                from aec.config import SHED_TILES
                is_shed_adj = (wx, wy) in SHED_TILES or any(abs(wx - sx) + abs(wy - sy) <= 1 for sx, sy in SHED_TILES)
                if is_shed_adj:
                    worker_actions = ["PICKUP", "WHEAT", 1]
                    reconnect_required = False
                else:
                    reconnect_required = True
                    sx, sy = 4, 4
                    if sx > wx: worker_actions = ["EAST"]
                    elif sx < wx: worker_actions = ["WEST"]
                    elif sy > wy: worker_actions = ["SOUTH"]
                    else: worker_actions = ["NORTH"]

            attribution = {
                "opportunity_family": path.opportunity_family,
                "resource_graph_path": f"WHEAT -> FEED -> {path.target_commodity}",
                "physical_conversion": True,
                "market_actions": market_actions,
                "worker_actions": worker_actions,
                "labor_class": path.labor_class.value,
                "input": "WHEAT",
                "output": path.target_commodity,
                "cash_effect": path.net_value_est,
                "capacity_effect": 0,
                "downstream_purpose": path.liquidity_profile.value_path_type.value if path.liquidity_profile else "SALEABLE_OUTPUT",
                "terminal_relevance": True
            }

            return ConversionExecutionPlan(
                plan_id=f"PLAN_{path.path_id}",
                conversion_id=path.path_id,
                target_commodity=path.target_commodity,
                required_inputs={"WHEAT": 1},
                produced_outputs={path.target_commodity: 1},
                worker_id=worker_id,
                target_location=target_loc,
                market_actions=market_actions,
                worker_actions=worker_actions,
                reconnect_required=reconnect_required,
                start_step=econ_state.step,
                estimated_duration=path.total_steps,
                net_value_est=path.net_value_est,
                is_executable=bool(market_actions or worker_actions),
                labor_class=path.labor_class,
                opportunity_family=path.opportunity_family,
                attribution_info=attribution
            )

        elif path.target_commodity == "CARROT":
            carrot_seeds = econ_state.farm.seeds.get("CARROT", 0)
            worker = econ_state.workers.get_worker(0)
            if not worker:
                return None
            wx, wy = worker.position
            market_actions = []
            worker_actions = []

            if carrot_seeds == 0 and float(econ_state.farm.cash) >= 20.0:
                market_actions.append(["BUY_SEED", "CARROT", 1])

            attribution = {
                "opportunity_family": "RESOURCE_ACQUISITION",
                "resource_graph_path": "CASH -> SEED -> CARROT",
                "physical_conversion": False,
                "market_actions": market_actions,
                "worker_actions": worker_actions,
                "labor_class": path.labor_class.value if isinstance(path.labor_class, ConversionLaborClass) else str(path.labor_class),
                "input": "CASH",
                "output": "CARROT",
                "cash_effect": path.net_value_est,
                "capacity_effect": 0,
                "downstream_purpose": "ACQUISITION_NOT_CONVERSION",
                "terminal_relevance": True
            }

            return ConversionExecutionPlan(
                plan_id=f"PLAN_{path.path_id}",
                conversion_id=path.path_id,
                target_commodity="CARROT",
                required_inputs={"CASH": 20},
                produced_outputs={"CARROT": 4},
                worker_id=0,
                target_location=(wx, wy),
                market_actions=market_actions,
                worker_actions=worker_actions,
                reconnect_required=False,
                start_step=econ_state.step,
                estimated_duration=path.total_steps,
                net_value_est=path.net_value_est,
                is_executable=bool(market_actions or worker_actions),
                labor_class=path.labor_class,
                opportunity_family=path.opportunity_family,
                attribution_info=attribution
            )

        # Non-livestock paths (e.g. pure seed purchases) are rejected from RESOURCE_CONVERSION
        return None


def decompose_conversion_to_tasks(
    plan: ConversionExecutionPlan,
    start_step: int = 0
) -> List[Any]:
    """Decompose a ConversionExecutionPlan into discrete WorkerTasks for multi-worker coordination (§14, §16)."""
    from aec.coordination.task_model import TaskActionFamily, TaskPriority, WorkerTask
    from aec.coordination.worker_model import WorkerCapability

    tasks: List[WorkerTask] = []
    loc = plan.target_location or (4, 4)

    # If physical worker actions are needed
    if plan.worker_actions:
        primary_op = plan.worker_actions[-1] if plan.worker_actions else "PASS"
        fam = {
            "FEED": TaskActionFamily.FEED_ANIMAL,
            "PICKUP": TaskActionFamily.PICKUP_RESOURCE,
            "DROP": TaskActionFamily.DROP_RESOURCE,
            "HARVEST": TaskActionFamily.HARVEST,
            "WATER": TaskActionFamily.WATER,
            "PLANT": TaskActionFamily.PLANT,
        }.get(primary_op, TaskActionFamily.WAIT)

        task = WorkerTask(
            task_id=f"CONV_{plan.conversion_id}_{start_step}",
            action_family=fam,
            location=loc,
            earliest_start=start_step,
            latest_completion=start_step + max(10, plan.estimated_duration),
            required_capabilities={WorkerCapability.MOVE},
            duration=1,
            resource_inputs=dict(plan.required_inputs),
            resource_outputs=dict(plan.produced_outputs),
            cash_effect=plan.net_value_est,
            priority_class=TaskPriority.SCHEDULED_PRODUCTION,
            is_mandatory=False,
            target_commodity=plan.target_commodity,
        )
        tasks.append(task)

    return tasks
