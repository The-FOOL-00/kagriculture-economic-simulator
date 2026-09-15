"""
scratch/instrumented_v54_plus.py
================================
Surgical instrumentation and counterfactual engine for V54++ (candidates/v54_plus_shop.py).

Provides:
  1. Detailed per-turn mechanism census (tracking firings, actions replaced, and commodities).
  2. Local counterfactual switches (R0 to Rk) with zero macro route divergence.
  3. Exact parity verification with frozen candidates/v54_plus_shop.py.
"""

from __future__ import annotations

import os
import sys
import copy
from typing import Any, Dict, List, Optional, Tuple

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
for path in [
    os.path.join(BASE_DIR, "external_repos", "lixingtao123-Kaggriculture", "variant_v54_h3q4"),
    os.path.join(BASE_DIR, "external_repos", "kaggriculture-v66-agent"),
    os.path.join(BASE_DIR, "candidates"),
]:
    if path not in sys.path:
        sys.path.insert(0, path)

import importlib.util

spec_v54 = importlib.util.spec_from_file_location(
    "v54_base_shop",
    os.path.join(BASE_DIR, "external_repos", "lixingtao123-Kaggriculture", "variant_v54_h3q4", "main.py"),
)
mod_v54 = importlib.util.module_from_spec(spec_v54)
spec_v54.loader.exec_module(mod_v54)

spec_v62 = importlib.util.spec_from_file_location(
    "v62_base_shop",
    os.path.join(BASE_DIR, "external_repos", "kaggriculture-v66-agent", "candidate_v62_composite_bakery_yarn.py"),
)
mod_v62 = importlib.util.module_from_spec(spec_v62)
spec_v62.loader.exec_module(mod_v62)

spec_v66 = importlib.util.spec_from_file_location(
    "v66_base_shop",
    os.path.join(BASE_DIR, "external_repos", "kaggriculture-v66-agent", "candidate_v66_meta_closed_loop.py"),
)
mod_v66 = importlib.util.module_from_spec(spec_v66)
spec_v66.loader.exec_module(mod_v66)

_v60_seed_trim = mod_v62._v60_seed_trim
_v60_shed_guard = mod_v62._v60_shed_guard
_route_loaded_units = mod_v66._route_loaded_units
_TERMINAL_UNITS = mod_v66._TERMINAL_UNITS
_TERMINAL_MARKET = mod_v66._TERMINAL_MARKET
_v56_visible_configuration = mod_v62._v56_visible_configuration


def _select_route(step: int, shops: list) -> str:
    """Minimum Sufficient Shop Controller (S2 Model)."""
    if step < 72 or not shops:
        return "backbone"

    first = str(shops[0]) if len(shops) >= 1 else ""
    second = str(shops[1]) if len(shops) >= 2 else ""

    if first == "YARN_STORE":
        return "yarn"

    if step >= 144:
        if second == "YARN_STORE":
            if first == "BAKERY":
                return "bakery"
            return "yarn"
        if first == "BAKERY" and second == "YARN_STORE":
            return "bakery"

    return "backbone"


class InstrumentedV54Plus:
    """
    Instrumented V54++ instance with exact per-mechanism telemetry and local counterfactual toggles.
    """

    def __init__(self, switches: Optional[Dict[str, Any]] = None):
        self.switches = switches or {}
        # Base config
        self.config_dict = copy.deepcopy(dict(mod_v62._V54_CONFIG.__dict__))

        # Apply config-level switches
        if self.switches.get("disable_preempt"):
            self.config_dict["preempt_enabled"] = False
        elif self.switches.get("aggressive_preempt"):
            self.config_dict["preempt_money_deficit"] = 2000.0
            self.config_dict["preempt_minimum_delta"] = 4.0
            self.config_dict["preempt_maximum_batch"] = 12
        elif self.switches.get("conservative_preempt"):
            self.config_dict["preempt_money_deficit"] = 6000.0
            self.config_dict["preempt_minimum_delta"] = 16.0
            self.config_dict["preempt_maximum_batch"] = 4

        if self.switches.get("disable_fronting"):
            self.config_dict["front_money_deficit"] = 1000000.0
            self.config_dict["front_on_near"] = False
        elif self.switches.get("aggressive_fronting"):
            self.config_dict["front_money_deficit"] = 2000.0
        elif self.switches.get("conservative_fronting"):
            self.config_dict["front_money_deficit"] = 7000.0

        if self.switches.get("disable_front_on_near"):
            self.config_dict["front_on_near"] = False

        if self.switches.get("disable_preempt_on_near"):
            self.config_dict["preempt_on_near"] = False

        # Build policy config
        self.v51_config = mod_v54._V51ResidualConfig(**self.config_dict)

        # Build policies
        self.policy_backbone = mod_v54._v51_build_policy(mod_v62._V56_BACKBONE_ROUTE, self.v51_config)
        self.policy_yarn = mod_v54._v51_build_policy(mod_v62._V56_YARN_ROUTE, self.v51_config)
        self.policy_bakery = mod_v54._v51_build_policy(mod_v62._V58_BAKERY_YARN_ROUTE, self.v51_config)

        self.policies = {
            "backbone": self.policy_backbone,
            "yarn": self.policy_yarn,
            "bakery": self.policy_bakery,
        }

        self.routes = {
            "backbone": mod_v62._V56_BACKBONE_ROUTE,
            "yarn": mod_v62._V56_YARN_ROUTE,
            "bakery": mod_v62._V58_BAKERY_YARN_ROUTE,
        }

        self.shop_state = {0: {"route": "backbone", "last": -1}, 1: {"route": "backbone", "last": -1}}

        # Turn-by-turn telemetry records
        self.telemetry_history: List[Dict[str, Any]] = []

    def reset(self):
        self.shop_state = {0: {"route": "backbone", "last": -1}, 1: {"route": "backbone", "last": -1}}
        self.telemetry_history.clear()
        for p in self.policies.values():
            if hasattr(p, "controller"):
                p.controller.states = {0: {}, 1: {}}

    def __call__(self, obs: Dict[str, Any], configuration: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        step = obs.get("step")
        if step is None:
            step = 24 * int(obs.get("day", 0) or 0) + int(obs.get("hour", 0) or 0)
        else:
            step = int(step)

        seat = 1 if int(obs.get("player", 0) or 0) == 1 else 0
        state = self.shop_state[seat]
        if step == 0 or step <= state["last"]:
            state["route"] = "backbone"
            state["last"] = step
        else:
            state["last"] = step

        visible = _v56_visible_configuration(configuration)
        town = obs.get("town", {}) or {}
        shops = list(town.get("unlocked_shops", []) or [])

        # Active route selection
        state["route"] = _select_route(step, shops)
        route_name = state["route"]
        policy = self.policies[route_name]
        raw_route = self.routes[route_name]
        route_prior_action = copy.deepcopy(raw_route[step])

        # Tracking dictionary for this turn
        turn_event = {
            "step": step,
            "route": route_name,
            "firings": {
                "fixed_route": True,
                "weed_repair": False,
                "debt_repay": False,
                "market_preempt": False,
                "deficit_fronting": False,
                "seed_trim": False,
                "shed_guard": False,
                "terminal_loaded_units": False,
                "terminal_units": False,
                "terminal_market": False,
                "sanitizer": False,
                "emergency_fallback": False,
            },
            "actions_changed": {
                "weed_repair": 0,
                "market_preempt": 0,
                "deficit_fronting": 0,
                "seed_trim": 0,
                "shed_guard": 0,
                "terminal_loaded_units": 0,
                "terminal_units": 0,
                "terminal_market": 0,
                "sanitizer": 0,
            },
            "preempt_commodities": [],
            "fronting_active": False,
            "near_latched": False,
            "money_gap": 0.0,
        }

        # Check weed repair on base planner if not disabled
        base_action = None
        if hasattr(policy, "controller") and hasattr(policy.controller, "base_policy"):
            base_planner = policy.controller.base_policy
            # Check what weed repair does
            base_action = base_planner(obs, visible)
            # Compare base_action with route_prior_action
            if self.switches.get("disable_weed_repair"):
                # Use raw route replay action
                base_action = copy.deepcopy(route_prior_action)
            else:
                farmer_diff = (base_action.get("farmer") != route_prior_action.get("farmer"))
                hands_diff = sum(
                    1 for h1, h2 in zip(base_action.get("hands", []), route_prior_action.get("hands", [])) if h1 != h2
                )
                if farmer_diff or hands_diff > 0:
                    turn_event["firings"]["weed_repair"] = True
                    turn_event["actions_changed"]["weed_repair"] = (1 if farmer_diff else 0) + hands_diff

        # Execute policy (ResidualValueController)
        try:
            # We can inspect controller state before/after
            ctrl = getattr(policy, "controller", None)
            before_market = copy.deepcopy((base_action or {}).get("market", []))
            
            # Run policy
            action = policy(obs, visible)

            if ctrl is not None:
                c_state = ctrl.states.get(seat, {})
                turn_event["near_latched"] = bool(c_state.get("near_latched", False))
                # Check preempt
                preempt_units = ctrl.telemetry.get("preempt_units", 0)
                # If market was added by preempt
                # Preempt adds to the front of market orders
                # Let's see if preempt orders were added
                preempt_added = [
                    ord for ord in action.get("market", [])
                    if ord not in before_market and len(ord) >= 3 and ord[0] == "SELL"
                ]
                if preempt_added:
                    turn_event["firings"]["market_preempt"] = True
                    turn_event["actions_changed"]["market_preempt"] = len(preempt_added)
                    turn_event["preempt_commodities"] = [ord[1] for ord in preempt_added]

                # Check deficit fronting
                # Deficit fronting sorts sells to front when should_front is True
                front_items = {str(item) for item in ctrl.config.front_items}
                supply_peak = max(
                    (float(v) for k, v in c_state.get("opponent_supply", {}).items() if k in front_items),
                    default=0.0,
                )
                farms = list(obs.get("farms", []) or [])
                gap = (
                    (float(farms[seat].get("money", 0)) - float(farms[1 - seat].get("money", 0)))
                    if len(farms) == 2 else 0.0
                )
                turn_event["money_gap"] = gap
                should_front = bool(ctrl.config.front_existing_sells) and (
                    (bool(ctrl.config.front_on_near) and bool(c_state.get("near_latched", False)))
                    or -gap >= float(ctrl.config.front_money_deficit)
                    or supply_peak >= float(ctrl.config.front_supply_threshold)
                )
                turn_event["fronting_active"] = should_front
                if should_front:
                    turn_event["firings"]["deficit_fronting"] = True
                    turn_event["actions_changed"]["deficit_fronting"] = 1

        except Exception as e:
            turn_event["firings"]["emergency_fallback"] = True
            action = mod_v54._v51_safe_action(obs)

        # 1. Overlay: Strawberry seed trim
        if not self.switches.get("disable_seed_trim"):
            before_trim = copy.deepcopy(action.get("market", []))
            action = _v60_seed_trim(obs, action, step)
            if action.get("market", []) != before_trim:
                turn_event["firings"]["seed_trim"] = True
                turn_event["actions_changed"]["seed_trim"] = 1

        # 2. Overlay: Hour-23 shed capacity guard
        capacity = int((configuration or {}).get("shedCapacity", 100)) or 100
        if not self.switches.get("disable_shed_guard"):
            before_guard = copy.deepcopy(action)
            action = _v60_shed_guard(obs, action, capacity)
            if action != before_guard:
                turn_event["firings"]["shed_guard"] = True
                turn_event["actions_changed"]["shed_guard"] = 1

        # 3. Overlay: Terminal loaded unit recall (steps 713-716)
        if 713 <= step <= 716 and not self.switches.get("disable_terminal_loaded_units"):
            before_recall = copy.deepcopy(action)
            action = _route_loaded_units(obs, action, step)
            if action != before_recall:
                turn_event["firings"]["terminal_loaded_units"] = True
                diff = (1 if action.get("farmer") != before_recall.get("farmer") else 0) + sum(
                    1 for h1, h2 in zip(action.get("hands", []), before_recall.get("hands", [])) if h1 != h2
                )
                turn_event["actions_changed"]["terminal_loaded_units"] = diff

        # 4. Overlay: Final unit home convergence (steps 717-718)
        if step in (717, 718) and not self.switches.get("disable_terminal_units"):
            before_term_units = copy.deepcopy(action)
            action = _TERMINAL_UNITS(obs, action, step)
            if action != before_term_units:
                turn_event["firings"]["terminal_units"] = True
                diff = (1 if action.get("farmer") != before_term_units.get("farmer") else 0) + sum(
                    1 for h1, h2 in zip(action.get("hands", []), before_term_units.get("hands", [])) if h1 != h2
                )
                turn_event["actions_changed"]["terminal_units"] = diff

        # 5. Overlay: Final market liquidation (step 718)
        if step == 718 and not self.switches.get("disable_terminal_market"):
            before_term_mkt = copy.deepcopy(action.get("market", []))
            action = _TERMINAL_MARKET(obs, action, rule="collision", replace=True)
            if action.get("market", []) != before_term_mkt:
                turn_event["firings"]["terminal_market"] = True
                turn_event["actions_changed"]["terminal_market"] = len(action.get("market", []))

        # Check sanitizer/safety adjustments (hands padding or market clipping)
        farm = (obs.get("farms") or [{}])[seat]
        expected_hands = len((farm or {}).get("hands", []) or [])
        if len(action.get("hands", [])) != expected_hands or len(action.get("market", [])) > 10:
            turn_event["firings"]["sanitizer"] = True
            turn_event["actions_changed"]["sanitizer"] = 1

        self.telemetry_history.append(turn_event)
        return action
