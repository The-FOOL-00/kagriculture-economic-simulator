"""
scratch/step301_counterfactual_arms.py
======================================
Implements route-selection counterfactual arms R0 through R10 on top of V54++:
R0 = Frozen V54++
R1 = Force Backbone route
R2 = Force Yarn route
R3 = Force Bakery/Yarn route
R4 = V66 route choice
R5 = Step-72 shop only
R6 = Step-144 shop only
R7 = Step-216 shop only
R8 = Step-72 + Step-144 shops (V54++ reference)
R9 = Complete public shop history through Step 288
R10 = Random route assignment with matched frequencies
"""

import os
import sys
import copy
import numpy as np
from typing import Any, Dict, Optional

BASE_DIR = os.path.abspath(".")
V54PLUS_PATH = os.path.join(BASE_DIR, "candidates", "v54_plus_shop.py")

if os.path.dirname(V54PLUS_PATH) not in sys.path:
    sys.path.insert(0, os.path.dirname(V54PLUS_PATH))

import importlib.util
spec = importlib.util.spec_from_file_location("v54plus_base_r", V54PLUS_PATH)
mod_v54plus = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod_v54plus)

# Access routes and policies
mod_v54 = mod_v54plus.mod_v54
mod_v62 = mod_v54plus.mod_v62
_CONFIG = copy.deepcopy(mod_v54plus._CONFIG)

_POLICIES = {
    "backbone": mod_v54plus._POLICY_BACKBONE,
    "yarn": mod_v54plus._POLICY_YARN,
    "bakery": mod_v54plus._POLICY_BAKERY,
    "recovery": mod_v54._v51_build_policy(mod_v62._V58_RECOVERY_ROUTE, _CONFIG),
    "ice_minimax": mod_v54._v51_build_policy(mod_v62._V58_ICE_MINIMAX_ROUTE, _CONFIG),
}

_v60_seed_trim = mod_v54plus._v60_seed_trim
_v60_shed_guard = mod_v54plus._v60_shed_guard
_route_loaded_units = mod_v54plus._route_loaded_units
_TERMINAL_UNITS = mod_v54plus._TERMINAL_UNITS
_TERMINAL_MARKET = mod_v54plus._TERMINAL_MARKET
_v56_visible_configuration = mod_v54plus._v56_visible_configuration

class RouteSelectionArm:
    def __init__(self, arm_id: str, seed_offset: int = 0):
        self.arm_id = arm_id
        self.rng = np.random.RandomState(42 + seed_offset)
        self.state = {0: {"route": "backbone", "last": -1}, 1: {"route": "backbone", "last": -1}}
        
    def _select_route(self, step: int, shops: list, seat: int) -> str:
        s0 = str(shops[0]) if len(shops) >= 1 else ""
        s1 = str(shops[1]) if len(shops) >= 2 else ""
        s2 = str(shops[2]) if len(shops) >= 3 else ""
        s3 = str(shops[3]) if len(shops) >= 4 else ""
        
        if self.arm_id == "R0" or self.arm_id == "R8":
            # Frozen V54++ policy
            return mod_v54plus._select_route(step, shops)
            
        elif self.arm_id == "R1":
            # Always Backbone
            return "backbone"
            
        elif self.arm_id == "R2":
            # Always Yarn
            return "yarn"
            
        elif self.arm_id == "R3":
            # Always Bakery/Yarn
            return "bakery"
            
        elif self.arm_id == "R4":
            # V66 route choice
            if s0 == "YARN_STORE": return "yarn"
            if s0 == "BAKERY":
                if step >= 144 and s1 == "YARN_STORE": return "bakery"
                return "recovery"
            if s0 == "ICE_CREAM_SHOP": return "ice_minimax"
            return "backbone"
            
        elif self.arm_id == "R5":
            # Step-72 shop only
            if step >= 72:
                if s0 == "YARN_STORE": return "yarn"
                if s0 == "BAKERY": return "bakery"
            return "backbone"
            
        elif self.arm_id == "R6":
            # Step-144 shop only
            if step >= 144:
                if s1 == "YARN_STORE": return "yarn"
                if s1 == "BAKERY": return "bakery"
            return "backbone"
            
        elif self.arm_id == "R7":
            # Step-216 shop only
            if step >= 216:
                if s2 == "YARN_STORE": return "yarn"
                if s2 == "BAKERY": return "bakery"
            return "backbone"
            
        elif self.arm_id == "R9":
            # Full public shop history through Step 288
            # Look at all 4 unlocked shops
            all_shops = [s0, s1, s2, s3]
            if "YARN_STORE" in all_shops:
                # If bakery unlocked before yarn store
                if "BAKERY" in all_shops and all_shops.index("BAKERY") < all_shops.index("YARN_STORE"):
                    return "bakery"
                return "yarn"
            return "backbone"
            
        elif self.arm_id == "R10":
            # Random route assignment (matched ~60% backbone, 30% yarn, 10% bakery)
            if self.state[seat].get("rand_route") is None:
                r_val = self.rng.rand()
                if r_val < 0.60: self.state[seat]["rand_route"] = "backbone"
                elif r_val < 0.90: self.state[seat]["rand_route"] = "yarn"
                else: self.state[seat]["rand_route"] = "bakery"
            return self.state[seat]["rand_route"]
            
        return "backbone"
        
    def __call__(self, obs: Dict[str, Any], configuration: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        step = obs.get("step")
        if step is None:
            step = 24 * int(obs.get("day", 0) or 0) + int(obs.get("hour", 0) or 0)
        else:
            step = int(step)
            
        seat = 1 if int(obs.get("player", 0) or 0) == 1 else 0
        state = self.state[seat]
        if step == 0 or step <= state["last"]:
            state["route"] = "backbone"
            state["last"] = step
            state["rand_route"] = None
        else:
            state["last"] = step
            
        visible = _v56_visible_configuration(configuration)
        town = obs.get("town", {}) or {}
        shops = list(town.get("unlocked_shops", []) or [])
        
        # Select route
        route_name = self._select_route(step, shops, seat)
        state["route"] = route_name
        
        policy_fn = _POLICIES.get(route_name, _POLICIES["backbone"])
        action = policy_fn(obs, visible)
        
        # Tactical Overlays
        action = _v60_seed_trim(obs, action, step)
        capacity = int((configuration or {}).get("shedCapacity", 100)) or 100
        action = _v60_shed_guard(obs, action, capacity)
        
        if 713 <= step <= 716:
            action = _route_loaded_units(obs, action, step)
        if step in (717, 718):
            action = _TERMINAL_UNITS(obs, action, step)
        if step == 718:
            action = _TERMINAL_MARKET(obs, action, rule="collision", replace=True)
            
        return action

def get_route_arm(arm_id: str):
    return RouteSelectionArm(arm_id)
