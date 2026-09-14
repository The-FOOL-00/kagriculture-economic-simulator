# SPDX-License-Identifier: MIT
"""
=============================================================================
EXP-DEV-004 CANDIDATE TREATMENT: JOINT MACRO PRODUCTION SCHEDULER
=============================================================================
Candidate Identifier: dev_004_joint_macro_scheduler
Governing Protocol: DEVELOPMENT_EXPERIMENT_PROTOCOL_V1_3.md
Frozen Baseline: candidates/compiled_v54_plus_residual.py
Baseline SHA-256: 18402ec6fa3709b9b5ef90dd9c8d7b9c0e44aea55ab163e44a80a4adc0cb7eeb

Architectural Composition:
  Treatment = V54++ Residual Baseline + Joint Macro Production Planner

Core Hypothesis:
  Jointly planning crop mix, tile allocation, worker routing, watering,
  harvesting, market absorption, and terminal timing captures specialization
  upside while preventing the physical route desynchronization and lifespan
  cliff failures observed in DEV-003.

Preservation Invariants:
  1. Authoritative V54++ residual preemption engine strictly preserved:
     preempt_money_deficit = 2000.0, preempt_minimum_delta = 4.0, preempt_maximum_batch = 12
  2. Baseline Invariant: In all non-activating, unpromising, or ambiguous states,
     the candidate executes 100% default V54++ baseline behavior bit-for-bit.
  3. Zero-Leakage: Zero future-state information, zero seed knowledge.
=============================================================================
"""

import os
import sys
import copy
import math
import importlib.util
from typing import Dict, List, Any, Optional, Tuple

# Locate external repository sources and compiled baseline
current_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.abspath(os.path.join(current_dir, "..", ".."))
BASELINE_PATH = os.path.join(base_dir, "candidates", "compiled_v54_plus_residual.py")

if not os.path.exists(BASELINE_PATH):
    raise FileNotFoundError(f"Authoritative baseline missing at {BASELINE_PATH}")

# Frozen Parameter Registration (Protocol V1.3 Section 9)
TAU = 1500.0                  # Opportunity-Value Hurdle (coins)
L_MIN = 100.0                 # Minimum Liquidity Floor (coins)
SWITCHING_FRICTION = 200.0    # Path Realignment Friction (coins)
W_SAT = 1.0                   # Saturated Yield Waste Penalty Weight
W_LIFE = 2.0                  # Lifespan Cliff Waste Penalty Weight
W_DEAD = 0.5                  # Dead Terminal Inventory Penalty Weight

# Crop Constants (Public Game Rules)
CROP_SPECS = {
    "WHEAT":      {"seed_cost": 10.0, "maturity": 48,  "interval": 0,  "ongoing": False, "yield_units": 6, "lifespan": 720, "base_price": 25.0},
    "CARROT":     {"seed_cost": 20.0, "maturity": 72,  "interval": 0,  "ongoing": False, "yield_units": 4, "lifespan": 720, "base_price": 35.0},
    "TOMATO":     {"seed_cost": 50.0, "maturity": 192, "interval": 24, "ongoing": True,  "yield_units": 4, "lifespan": 288, "base_price": 60.0},
    "STRAWBERRY": {"seed_cost": 100.0,"maturity": 240, "interval": 48, "ongoing": True,  "yield_units": 4, "lifespan": 720, "base_price": 120.0},
    "MELON":      {"seed_cost": 80.0, "maturity": 288, "interval": 0,  "ongoing": False, "yield_units": 6, "lifespan": 720, "base_price": 250.0},
}

PRODUCT_SHOPS = {
    "STRAWBERRY": frozenset({"SMOOTHIE_SHOP", "ICE_CREAM_SHOP", "BRUNCH_SPOT", "FARMERS_MARKET"}),
    "TOMATO":     frozenset({"PIZZA_SHOP", "FARMERS_MARKET"}),
    "CARROT":     frozenset({"PET_CAFE", "FARMERS_MARKET"}),
    "WHEAT":      frozenset({"BAKERY", "PIZZA_SHOP", "BRUNCH_SPOT", "ICE_CREAM_SHOP", "FARMERS_MARKET"}),
    "WOOL":       frozenset({"YARN_STORE"}),
    "MILK":       frozenset({"PIZZA_SHOP", "SMOOTHIE_SHOP", "ICE_CREAM_SHOP"}),
    "EGG":        frozenset({"BAKERY", "BRUNCH_SPOT"}),
}

# Production Profiles for Candidate Whole Routes
ROUTE_PROFILES = {
    "BASELINE_BACKBONE": {
        "crops": {"STRAWBERRY": 38, "CARROT": 6, "MELON": 12, "WHEAT": 187},
        "animals": {"COW": 9, "SHEEP": 5},
        "worker_harvest_cadence": {"STRAWBERRY": 48, "CARROT": 72, "WHEAT": 48, "MELON": 288},
    },
    "YARN_SPECIALIZED": {
        "crops": {"STRAWBERRY": 33, "CARROT": 9, "MELON": 12, "WHEAT": 185},
        "animals": {"COW": 6, "SHEEP": 11},
        "worker_harvest_cadence": {"STRAWBERRY": 48, "CARROT": 72, "WHEAT": 48, "MELON": 288},
    },
    "BAKERY_SPECIALIZED": {
        "crops": {"STRAWBERRY": 33, "CARROT": 9, "MELON": 12, "WHEAT": 185},
        "animals": {"COW": 6, "SHEEP": 11},
        "worker_harvest_cadence": {"STRAWBERRY": 48, "CARROT": 72, "WHEAT": 48, "MELON": 288},
    },
    "PET_SPECIALIZED": {
        "crops": {"STRAWBERRY": 33, "CARROT": 9, "MELON": 12, "WHEAT": 185},
        "animals": {"COW": 6, "SHEEP": 11},
        "worker_harvest_cadence": {"STRAWBERRY": 48, "CARROT": 72, "WHEAT": 48, "MELON": 288},
    },
    "SMOOTHIE_SPECIALIZED": {
        "crops": {"STRAWBERRY": 38, "CARROT": 6, "MELON": 12, "WHEAT": 187},
        "animals": {"COW": 6, "SHEEP": 9},
        "worker_harvest_cadence": {"STRAWBERRY": 48, "CARROT": 72, "WHEAT": 48, "MELON": 288},
    },
    "PIZZA_ADAPTIVE": {
        "crops": {"STRAWBERRY": 38, "CARROT": 13, "MELON": 12, "WHEAT": 192},
        "animals": {"COW": 7, "SHEEP": 6},
        "worker_harvest_cadence": {"STRAWBERRY": 48, "CARROT": 72, "WHEAT": 48, "MELON": 288},
    },
}


class Dev004JointMacroScheduler:
    """
    Joint Macro Production Scheduler with Whole-Route Adaptive Planning.
    Jointly evaluates physical feasibility (maturation, cadence, worker capacity,
    lifespan cliffs, market absorption) and selects complete physical routes
    while preserving V54++ residual preemption.
    """

    def __init__(self, baseline_module=None, seat: int = 0, seed: int = 0):
        self.seat = seat
        self.seed = seed
        self.decision_events: List[Dict[str, Any]] = []
        self.worker_telemetry: List[Dict[str, Any]] = []
        self.active_plan = "BASELINE_BACKBONE"
        self.active_policy = None

        # Load isolated baseline module instance
        if baseline_module is not None:
            self.baseline = baseline_module
        else:
            spec = importlib.util.spec_from_file_location(
                f"isolated_baseline_{id(self)}", BASELINE_PATH
            )
            self.baseline = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(self.baseline)

        # Build candidate policies using the baseline's authoritative preemption config
        config = self.baseline._CONFIG
        self.policy_registry = {
            "BASELINE_BACKBONE": self.baseline._POLICY_BACKBONE,
            "YARN_SPECIALIZED": self.baseline._v51_build_policy(self.baseline._V56_YARN_ROUTE, config),
            "BAKERY_SPECIALIZED": self.baseline._v51_build_policy(self.baseline._V58_BAKERY_YARN_ROUTE, config),
            "PET_SPECIALIZED": self.baseline._v51_build_policy(self.baseline._V57_PET_ROUTE, config),
            "SMOOTHIE_SPECIALIZED": self.baseline._v51_build_policy(self.baseline._V58_SMOOTHIE_ROUTE, config),
            "PIZZA_ADAPTIVE": self.baseline._v51_build_policy(self.baseline._V58_PIZZA_RECOVERY_ROUTE, config),
        }
        self.active_policy = self.policy_registry["BASELINE_BACKBONE"]

        # In-game state metrics
        self.saturation_events = 0
        self.lifespan_cliff_events = 0
        self.missed_harvest_events = 0

    def _assert_zero_leakage(self, obs: Dict[str, Any]):
        """Runtime assertion against future-state leakage and hidden variables."""
        forbidden_keys = {
            "future_shops", "terminal_score", "ground_truth", "future_market",
            "offline_trajectory", "oracle", "future_prices", "future_events"
        }
        intersection = forbidden_keys.intersection(obs.keys())
        if intersection:
            raise RuntimeError(f"Zero-Leakage Violation: Forbidden keys in obs: {intersection}")

    def evaluate_plan_feasibility_and_value(
        self,
        plan_name: str,
        obs: Dict[str, Any],
        step: int,
        unlocked_shops: List[str],
        prices: Dict[str, float],
        money: float
    ) -> Tuple[float, Dict[str, Any]]:
        """
        Physical Feasibility & Market Absorption Valuation Model (Protocol V1.3 Section 7 & 8).
        Estimates realistic realizable economic value of a candidate macro plan.
        """
        profile = ROUTE_PROFILES[plan_name]
        t_rem = max(0, 720 - step)

        # 1. Physical Feasibility Constraints
        penalties = 0.0
        total_revenue = 0.0
        total_costs = 0.0

        # Evaluate crops
        for crop_name, plant_count in profile["crops"].items():
            spec = CROP_SPECS[crop_name]
            mat = spec["maturity"]
            intv = spec["interval"]
            ongoing = spec["ongoing"]
            lifespan = spec["lifespan"]
            base_p = spec["base_price"]

            # Price modeling with shop matching
            spot_p = float(prices.get(crop_name, base_p) or base_p)
            has_shop = any(s in PRODUCT_SHOPS.get(crop_name, set()) for s in unlocked_shops)
            eff_p = spot_p if has_shop else (0.65 * spot_p)

            # Maturation check
            if t_rem < mat:
                # Cannot mature before horizon: total loss of seed investment
                cost = plant_count * spec["seed_cost"]
                total_costs += cost
                penalties += cost * 1.5
                continue

            # Usable harvest cycles
            if ongoing:
                # Ongoing crop (e.g. Strawberry)
                cadence = profile["worker_harvest_cadence"].get(crop_name, 48)
                usable_window = min(t_rem - mat, lifespan)
                # Check for lifespan cliff (DEV-003 failure mode)
                if lifespan < t_rem - mat:
                    cliff_steps = (t_rem - mat) - lifespan
                    penalties += W_LIFE * (cliff_steps / 24.0) * (plant_count * 15.0)

                # Worker service cadence vs yield interval
                harvest_cycles = max(0, usable_window // cadence)
                if intv > 0 and cadence > intv:
                    # Saturation waste
                    wasted_cycles = max(0, (usable_window // intv) - harvest_cycles)
                    penalties += W_SAT * wasted_cycles * spec["yield_units"] * eff_p * 0.5

                units_produced = plant_count * harvest_cycles * spec["yield_units"]
                total_costs += plant_count * spec["seed_cost"]
            else:
                # Single-harvest replanted crop (e.g. Wheat, Carrot)
                cycles = max(1, t_rem // mat)
                units_produced = plant_count * cycles * spec["yield_units"]
                total_costs += plant_count * cycles * spec["seed_cost"]

            # Market Absorption Model (Protocol V1.3 Section 7)
            # Shop pulls 1 unit / 4 steps (if matched), Town Center pulls 1 unit / 12 steps
            pull_rate = (1.0 / 4.0 if has_shop else 0.0) + (1.0 / 12.0)
            absorb_capacity = pull_rate * t_rem
            realized_sales = min(units_produced, absorb_capacity)
            dead_inventory = max(0.0, units_produced - realized_sales)

            total_revenue += realized_sales * eff_p
            penalties += W_DEAD * dead_inventory * (0.30 * eff_p)

        # Evaluate livestock products
        animals = profile["animals"]
        # Sheep -> Wool
        sheep_count = animals.get("SHEEP", 0)
        has_yarn = "YARN_STORE" in unlocked_shops
        wool_p = float(prices.get("WOOL", 200.0) or 200.0)
        eff_wool_p = wool_p if has_yarn else (0.60 * wool_p)
        wool_cycles = max(0, t_rem // 72)
        wool_units = sheep_count * wool_cycles * 2
        wool_pull = (1.0 / 4.0 if has_yarn else 0.0) + (1.0 / 12.0)
        wool_sold = min(wool_units, wool_pull * t_rem)
        total_revenue += wool_sold * eff_wool_p

        # Cow -> Milk
        cow_count = animals.get("COW", 0)
        has_milk_shop = any(s in {"PIZZA_SHOP", "SMOOTHIE_SHOP", "ICE_CREAM_SHOP"} for s in unlocked_shops)
        milk_p = float(prices.get("MILK", 160.0) or 160.0)
        eff_milk_p = milk_p if has_milk_shop else (0.65 * milk_p)
        milk_cycles = max(0, t_rem // 48)
        milk_units = cow_count * milk_cycles * 2
        milk_pull = (1.0 / 4.0 if has_milk_shop else 0.0) + (1.0 / 12.0)
        milk_sold = min(milk_units, milk_pull * t_rem)
        total_revenue += milk_sold * eff_milk_p

        # Liquidity Penalty
        liq_penalty = max(0.0, L_MIN - money) * 0.5
        penalties += liq_penalty

        # Switching friction if not currently on this plan
        if plan_name != self.active_plan and self.active_plan != "BASELINE_BACKBONE":
            penalties += SWITCHING_FRICTION

        net_val = total_revenue - total_costs - penalties
        metrics = {
            "plan": plan_name,
            "expected_revenue": round(total_revenue, 2),
            "expected_costs": round(total_costs, 2),
            "penalties": round(penalties, 2),
            "net_terminal_value": round(net_val, 2),
        }
        return net_val, metrics

    def evaluate_checkpoints(self, obs: Dict[str, Any], step: int):
        """
        Checkpoint Planning Decision Loop (Protocol V1.3 Section 8).
        Constructs baseline continuation and evaluates all candidate macro plans.
        """
        farms = obs.get("farms", [])
        seat = int(obs.get("player", self.seat) or 0)
        farm = farms[seat] if seat < len(farms) else {}
        money = float(farm.get("money", 0.0) or 0.0)

        town = obs.get("town", {}) or {}
        unlocked_shops = list(town.get("unlocked_shops", []) or [])
        market = obs.get("market", {}) or {}
        prices = {k: float(v) for k, v in (market.get("prices", {}) or {}).items()}

        # 1. Baseline continuation value
        v_base, base_metrics = self.evaluate_plan_feasibility_and_value(
            "BASELINE_BACKBONE", obs, step, unlocked_shops, prices, money
        )

        # 2. Evaluate all candidate macro plans
        candidate_scores = {}
        candidate_metrics = {}
        for plan_name in ROUTE_PROFILES.keys():
            v_cand, metrics = self.evaluate_plan_feasibility_and_value(
                plan_name, obs, step, unlocked_shops, prices, money
            )
            candidate_scores[plan_name] = v_cand
            candidate_metrics[plan_name] = metrics

        # 3. Find best candidate
        best_plan = "BASELINE_BACKBONE"
        best_delta = 0.0
        for plan_name, v_cand in candidate_scores.items():
            if plan_name == "BASELINE_BACKBONE":
                continue
            delta = v_cand - v_base
            if delta > best_delta:
                best_delta = delta
                best_plan = plan_name

        # 4. Gating Decision Rule (Protocol V1.3 Section 8)
        if best_delta >= TAU and money >= L_MIN:
            selected_plan = best_plan
            decision = "SPECIALIZE"
        else:
            selected_plan = "BASELINE_BACKBONE"
            decision = "BASELINE"

        # Apply plan transition if needed
        if selected_plan != self.active_plan:
            self.active_plan = selected_plan
            self.active_policy = self.policy_registry[selected_plan]

        # Record telemetry
        telemetry = {
            "seed": self.seed,
            "step": step,
            "unlocked_shops": ";".join(unlocked_shops) if unlocked_shops else "NONE",
            "cash": money,
            "baseline_value": round(v_base, 2),
            "best_candidate_plan": best_plan,
            "best_candidate_delta": round(best_delta, 2),
            "tau_hurdle": TAU,
            "selected_plan": selected_plan,
            "decision": decision,
        }
        self.decision_events.append(telemetry)

    def act(self, obs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main decision loop.
        Applies joint macro scheduler at checkpoints and executes synchronized whole-route policy.
        """
        self._assert_zero_leakage(obs)

        step = obs.get("step")
        if step is None:
            step = 24 * int(obs.get("day", 0) or 0) + int(obs.get("hour", 0) or 0)
        else:
            step = int(step)

        seat = int(obs.get("player", self.seat) or 0)
        self.seat = seat

        # Planning Checkpoints: Days 3, 6, 9, 12 (Steps 72, 144, 216, 288)
        if step in (72, 144, 216, 288):
            self.evaluate_checkpoints(obs, step)

        # Execute active policy (synchronized whole route + residual preemption)
        configuration = None
        visible = self.baseline._v56_visible_configuration(configuration)
        action = self.active_policy(obs, visible)

        # Apply standard championship tactical overlays
        action = self.baseline._v60_seed_trim(obs, action, step)
        capacity = int((configuration or {}).get("shedCapacity", 100)) or 100
        action = self.baseline._v60_shed_guard(obs, action, capacity)

        if 713 <= step <= 716:
            action = self.baseline._route_loaded_units(obs, action, step)
        if step in (717, 718):
            action = self.baseline._TERMINAL_UNITS(obs, action, step)
        if step == 718:
            action = self.baseline._TERMINAL_MARKET(obs, action, rule="collision", replace=True)

        return action


def kaggle_agent(obs: Dict[str, Any], configuration: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Kaggle-compliant entrypoint."""
    global _INSTANCE
    if "_INSTANCE" not in globals() or _INSTANCE is None:
        _INSTANCE = Dev004JointMacroScheduler()
    return _INSTANCE.act(obs)
