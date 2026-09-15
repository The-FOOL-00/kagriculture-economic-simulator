"""
candidates/v54_plus_residual.py
===============================
Championship Candidate: V54++ with Causally Validated Residual Controller Tuning.

Proven Residual Modification:
  Optimized Market Preemption parameters on top of V54++:
  - preempt_money_deficit = 2000.0 (was 4000.0)
  - preempt_minimum_delta = 4.0 (was 8.0)
  - preempt_maximum_batch = 12 (was 8)

STRICT CONSTRAINTS PRESERVED:
  - Byte-for-byte identical macro route prior.
  - Byte-for-byte identical public shop selection.
  - Zero opponent state, zero fingerprinting, zero seed memorization.
  - Zero worker pathing alterations.
"""

from __future__ import annotations

import os
import sys
import copy
import importlib.util
from typing import Any, Dict, Optional

# Locate external repository sources
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
V54_PATH = os.path.join(BASE_DIR, "external_repos", "lixingtao123-Kaggriculture", "variant_v54_h3q4", "main.py")
V62_PATH = os.path.join(BASE_DIR, "external_repos", "kaggriculture-v66-agent", "candidate_v62_composite_bakery_yarn.py")
V66_PATH = os.path.join(BASE_DIR, "external_repos", "kaggriculture-v66-agent", "candidate_v66_meta_closed_loop.py")

for p in [V54_PATH, V62_PATH, V66_PATH]:
    if not os.path.exists(p):
        raise FileNotFoundError(f"Required source repository missing: {p}")
    d = os.path.dirname(p)
    if d not in sys.path:
        sys.path.insert(0, d)

# Load V54 policy builder
spec_v54 = importlib.util.spec_from_file_location("v54_base_residual", V54_PATH)
mod_v54 = importlib.util.module_from_spec(spec_v54)
spec_v54.loader.exec_module(mod_v54)

# Load V62 candidate routes & overlays
spec_v62 = importlib.util.spec_from_file_location("v62_base_residual", V62_PATH)
mod_v62 = importlib.util.module_from_spec(spec_v62)
spec_v62.loader.exec_module(mod_v62)

# Load V66 terminal overlays
spec_v66 = importlib.util.spec_from_file_location("v66_base_residual", V66_PATH)
mod_v66 = importlib.util.module_from_spec(spec_v66)
spec_v66.loader.exec_module(mod_v66)

# Configuration with exactly ONE proven residual modification
_CONFIG_DICT = copy.deepcopy(dict(mod_v62._V54_CONFIG.__dict__))
_CONFIG_DICT["preempt_money_deficit"] = 2000.0
_CONFIG_DICT["preempt_minimum_delta"] = 4.0
_CONFIG_DICT["preempt_maximum_batch"] = 12
_CONFIG = mod_v54._V51ResidualConfig(**_CONFIG_DICT)

# Candidate Routes with validated residual controller
_POLICY_BACKBONE = mod_v54._v51_build_policy(mod_v62._V56_BACKBONE_ROUTE, _CONFIG)
_POLICY_YARN = mod_v54._v51_build_policy(mod_v62._V56_YARN_ROUTE, _CONFIG)
_POLICY_BAKERY = mod_v54._v51_build_policy(mod_v62._V58_BAKERY_YARN_ROUTE, _CONFIG)

# Verified Overlays
_v60_seed_trim = mod_v62._v60_seed_trim
_v60_shed_guard = mod_v62._v60_shed_guard
_route_loaded_units = mod_v66._route_loaded_units
_TERMINAL_UNITS = mod_v66._TERMINAL_UNITS
_TERMINAL_MARKET = mod_v66._TERMINAL_MARKET
_v56_visible_configuration = mod_v62._v56_visible_configuration

# Runtime State Tracking
_SHOP_STATE = {0: {"route": "backbone", "last": -1}, 1: {"route": "backbone", "last": -1}}


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


def agent(obs: Dict[str, Any], configuration: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    V54+ Residual Championship Agent.
    Executes V54++ macro foundation coupled with causally proven aggressive market preemption.
    """
    step = obs.get("step")
    if step is None:
        step = 24 * int(obs.get("day", 0) or 0) + int(obs.get("hour", 0) or 0)
    else:
        step = int(step)

    seat = 1 if int(obs.get("player", 0) or 0) == 1 else 0
    state = _SHOP_STATE[seat]
    if step == 0 or step <= state["last"]:
        state["route"] = "backbone"
        state["last"] = step
    else:
        state["last"] = step

    visible = _v56_visible_configuration(configuration)
    town = obs.get("town", {}) or {}
    shops = list(town.get("unlocked_shops", []) or [])

    # Update active route selection
    state["route"] = _select_route(step, shops)
    route = state["route"]

    # Execute active candidate policy
    if route == "yarn":
        action = _POLICY_YARN(obs, visible)
    elif route == "bakery":
        action = _POLICY_BAKERY(obs, visible)
    else:
        action = _POLICY_BACKBONE(obs, visible)

    # 1. Overlay: Strawberry seed trim
    action = _v60_seed_trim(obs, action, step)

    # 2. Overlay: Hour-23 shed capacity guard
    capacity = int((configuration or {}).get("shedCapacity", 100)) or 100
    action = _v60_shed_guard(obs, action, capacity)

    # 3. Overlay: Terminal loaded unit recall (steps 713-716)
    if 713 <= step <= 716:
        action = _route_loaded_units(obs, action, step)

    # 4. Overlay: Final unit home convergence (steps 717-718)
    if step in (717, 718):
        action = _TERMINAL_UNITS(obs, action, step)

    # 5. Overlay: Final market liquidation (step 718)
    if step == 718:
        action = _TERMINAL_MARKET(obs, action, rule="collision", replace=True)

    return action


def kaggle_agent(obs: Dict[str, Any], configuration: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    return agent(obs, configuration)
