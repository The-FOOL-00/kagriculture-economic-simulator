"""
scratch/test_omni_shop_residual.py
==================================
Tests the Omni-Shop Residual Architecture:
Expands the verified shop controller to include the ICE_CREAM_SHOP route (ice_minimax)
and KNOWN_YARN route, wrapped with the causally-proven Residual Controller.
"""

import copy
import importlib.util
import os
import sys

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, BASE_DIR)
sys.path.insert(0, os.path.join(BASE_DIR, "external_repos", "kaggriculture-cppsim"))

import kagsim

V54_PATH = os.path.join(BASE_DIR, "external_repos", "lixingtao123-Kaggriculture", "variant_v54_h3q4", "main.py")
V62_PATH = os.path.join(BASE_DIR, "external_repos", "kaggriculture-v66-agent", "candidate_v62_composite_bakery_yarn.py")
V66_PATH = os.path.join(BASE_DIR, "external_repos", "kaggriculture-v66-agent", "candidate_v66_meta_closed_loop.py")
V54_RESIDUAL_PATH = os.path.join(BASE_DIR, "candidates", "v54_plus_residual.py")

for p in [V54_PATH, V62_PATH, V66_PATH, os.path.dirname(V54_RESIDUAL_PATH)]:
    if p not in sys.path:
        sys.path.insert(0, p)

# Load V54
spec_v54 = importlib.util.spec_from_file_location("v54_omni", V54_PATH)
mod_v54 = importlib.util.module_from_spec(spec_v54)
spec_v54.loader.exec_module(mod_v54)

# Load V62
spec_v62 = importlib.util.spec_from_file_location("v62_omni", V62_PATH)
mod_v62 = importlib.util.module_from_spec(spec_v62)
spec_v62.loader.exec_module(mod_v62)

# Load V66
spec_v66 = importlib.util.spec_from_file_location("v66_omni", V66_PATH)
mod_v66 = importlib.util.module_from_spec(spec_v66)
spec_v66.loader.exec_module(mod_v66)

# Load Control Baseline
spec_ctrl = importlib.util.spec_from_file_location("ctrl_omni", V54_RESIDUAL_PATH)
mod_ctrl = importlib.util.module_from_spec(spec_ctrl)
spec_ctrl.loader.exec_module(mod_ctrl)

# Build Residual Config
cfg_dict = copy.deepcopy(dict(mod_v62._V54_CONFIG.__dict__))
cfg_dict["preempt_money_deficit"] = 2000.0
cfg_dict["preempt_minimum_delta"] = 4.0
cfg_dict["preempt_maximum_batch"] = 12
config = mod_v54._V51ResidualConfig(**cfg_dict)

# Build Policies
_POLICY_BACKBONE = mod_v54._v51_build_policy(mod_v62._V56_BACKBONE_ROUTE, config)
_POLICY_YARN = mod_v54._v51_build_policy(mod_v62._V56_YARN_ROUTE, config)
_POLICY_BAKERY = mod_v54._v51_build_policy(mod_v62._V58_BAKERY_YARN_ROUTE, config)
_POLICY_ICE = mod_v54._v51_build_policy(mod_v66._ROUTES["ice_minimax"], config)
_POLICY_KNOWN_YARN = mod_v54._v51_build_policy(mod_v66._ROUTES["known_yarn"], config)

# Overlays
_v60_seed_trim = mod_v62._v60_seed_trim
_v60_shed_guard = mod_v62._v60_shed_guard
_route_loaded_units = mod_v66._route_loaded_units
_TERMINAL_UNITS = mod_v66._TERMINAL_UNITS
_TERMINAL_MARKET = mod_v66._TERMINAL_MARKET
_v56_visible_configuration = mod_v62._v56_visible_configuration


def _select_omni_route(step: int, shops: list) -> str:
    """Enhanced Pure-Public Shop Route Selector."""
    if step < 72 or not shops:
        return "backbone"
        
    first = str(shops[0]) if len(shops) >= 1 else ""
    second = str(shops[1]) if len(shops) >= 2 else ""
    
    # Day 3 (Step 72)
    if first == "YARN_STORE":
        return "known_yarn"
    if first in ("ICE_CREAM_SHOP", "SMOOTHIE_SHOP"):
        return "ice"
        
    # Day 6 (Step 144)
    if step >= 144:
        if second == "YARN_STORE":
            if first == "BAKERY":
                return "bakery"
            return "known_yarn"
        if first == "BAKERY" and second == "YARN_STORE":
            return "bakery"
        if second in ("ICE_CREAM_SHOP", "SMOOTHIE_SHOP") and first in ("ICE_CREAM_SHOP", "SMOOTHIE_SHOP"):
            return "ice"
            
    return "backbone"


def make_omni_agent():
    state = {"route": "backbone", "last": -1}
    def agent(obs, configuration=None):
        step = int(obs["day"] * 24 + obs["hour"])
        visible = _v56_visible_configuration(configuration)
        town = obs.get("town", {}) or {}
        shops = list(town.get("unlocked_shops", []) or [])
        
        state["route"] = _select_omni_route(step, shops)
        r = state["route"]
        
        if r == "known_yarn":
            action = _POLICY_KNOWN_YARN(obs, visible)
        elif r == "yarn":
            action = _POLICY_YARN(obs, visible)
        elif r == "bakery":
            action = _POLICY_BAKERY(obs, visible)
        elif r == "ice":
            action = _POLICY_ICE(obs, visible)
        else:
            action = _POLICY_BACKBONE(obs, visible)
            
        action = _v60_seed_trim(obs, action, step)
        capacity = int((configuration or {}).get("shedCapacity", 100)) if configuration else 100
        action = _v60_shed_guard(obs, action, capacity)
        
        if 713 <= step <= 716:
            action = _route_loaded_units(obs, action, step)
        if step in (717, 718):
            action = _TERMINAL_UNITS(obs, action, step)
        if step == 718:
            action = _TERMINAL_MARKET(obs, action, rule="collision", replace=True)
            
        return action
    return agent


def play_game(a0, a1, seed):
    game = kagsim.Game(seed)
    while not game.done:
        o0 = game.observe(0)
        o1 = game.observe(1)
        game.step(a0(o0), a1(o1))
    return game.reward(0), game.reward(1)


def run_test():
    seeds = [11, 23, 47, 100, 200, 300, 400, 500, 600, 700,
             1001, 1002, 1003, 1004, 1005, 1006, 1007, 1008, 1009, 1010]
    
    print("=" * 70)
    print("HEAD-TO-HEAD: Omni-Shop Residual vs V54++ Residual Baseline")
    print(f"{len(seeds)} Seeds x 2 Seats = {len(seeds)*2} Total Matches")
    print("=" * 70)
    
    margins = []
    wins, losses, ties = 0, 0, 0
    omni_scores = []
    ctrl_scores = []
    
    for s in seeds:
        # Seat 0
        r0, r1 = play_game(make_omni_agent(), mod_ctrl.agent, s)
        m0 = r0 - r1
        margins.append(m0)
        omni_scores.append(r0)
        ctrl_scores.append(r1)
        if m0 > 0: wins += 1
        elif m0 < 0: losses += 1
        else: ties += 1
        
        # Seat 1
        r1, r0 = play_game(mod_ctrl.agent, make_omni_agent(), s)
        m1 = r0 - r1
        margins.append(m1)
        omni_scores.append(r0)
        ctrl_scores.append(r1)
        if m1 > 0: wins += 1
        elif m1 < 0: losses += 1
        else: ties += 1
        
    mean_margin = sum(margins) / len(margins)
    mean_omni = sum(omni_scores) / len(omni_scores)
    mean_ctrl = sum(ctrl_scores) / len(ctrl_scores)
    winrate = wins / len(margins) * 100
    
    print(f"\nOmni-Shop Residual Mean: ${mean_omni:,.2f}")
    print(f"V54++ Residual Control : ${mean_ctrl:,.2f}")
    print(f"Net Margin             : {mean_margin:+,.2f}")
    print(f"Win / Loss / Tie       : {wins} / {losses} / {ties} ({winrate:.1f}% Win Rate)")
    print("=" * 70)


if __name__ == "__main__":
    run_test()
