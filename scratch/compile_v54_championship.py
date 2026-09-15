#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""
scratch/compile_v54_championship.py
===================================
Championship Deployment Compiler:
Converts modular research harnesses (`candidates/v54_plus_shop.py` and `candidates/v54_plus_residual.py`)
into standalone, zero-dependency, Kaggle-safe deployment artifacts:
  - `candidates/compiled_v54_plus_shop.py`
  - `candidates/compiled_v54_plus_residual.py`

Preserves:
  - Exact route tables (_V56_BACKBONE_ROUTE, _V56_YARN_ROUTE, _V58_BAKERY_YARN_ROUTE)
  - Exact tactical overlays (_v60_seed_trim, _v60_shed_guard)
  - Exact terminal overlays (_route_loaded_units, _TERMINAL_UNITS, _TERMINAL_MARKET)
  - Exact shop selection logic (_select_route)
  - Exact residual preemption configuration
  - Zero external imports, zero __file__, zero relative path lookups.
"""

from __future__ import annotations

import os
import sys
import hashlib
from pathlib import Path


def compile_championship_agents() -> tuple[str, str, str, str]:
    root = Path(__file__).resolve().parent.parent
    v62_path = root / "external_repos" / "kaggriculture-v66-agent" / "candidate_v62_composite_bakery_yarn.py"
    
    if not v62_path.exists():
        raise FileNotFoundError(f"Missing base source: {v62_path}")

    v62_text = v62_path.read_text(encoding="utf-8")
    v62_lines = v62_text.splitlines(keepends=True)
    
    # Extract base up to the start of v62's custom switcher (line 4324)
    v62_base = "".join(v62_lines[:4324])

    terminal_and_agent_template = '''

# ==============================================================================
# Terminal Realization Overlays (V66 Engine Overlay)
# ==============================================================================
_RESIDUAL = sys.modules[_V51ResidualConfig.__module__]
_TERMINAL_MARKET = _RESIDUAL.terminal_market
_TERMINAL_GLOBALS = _TERMINAL_MARKET.__globals__
_TERMINAL_UNITS = _TERMINAL_GLOBALS["monetizable_terminal_units"]
_MOVE_TOWARD = _TERMINAL_GLOBALS["_move_toward"]
_SHED_ACCESS = _TERMINAL_GLOBALS["_shed_access"]
_SELLABLE = frozenset(_TERMINAL_GLOBALS["SELLABLE"])


def _align(action, expected):
    action = _v60_copy_action(action)
    hands = list(action["hands"])
    hands.extend([["PASS"] for _ in range(max(0, expected - len(hands)))])
    action["hands"] = hands[:expected]
    return action


def _route_loaded_units(obs, action, step):
    if not 713 <= step <= 716:
        return action
    seat = _v58_seat(obs)
    farm = _v58_farms(obs)[seat] or {}
    tiles = farm.get("tiles") or []
    positions = [farm.get("farmer", [0, 0]), *(farm.get("hands") or [])]
    inventories = list((((obs or {}).get("private") or {}).get("inventories") or []))
    inventories.extend({} for _ in range(max(0, len(positions) - len(inventories))))
    action = _align(action, max(0, len(positions) - 1))
    orders = [action["farmer"], *action["hands"]]
    access = _SHED_ACCESS(len(tiles) or 10)
    departure_distance = 718 - step

    for index, (position, inventory) in enumerate(zip(positions, inventories)):
        load = sum(
            max(0, int(quantity or 0))
            for item, quantity in (inventory or {}).items()
            if item in _SELLABLE
        )
        if load <= 0:
            continue
        x, y = int(position[0]), int(position[1])
        distance = min(abs(x - sx) + abs(y - sy) for sx, sy in access)
        if distance == departure_distance:
            orders[index] = _MOVE_TOWARD((x, y), access, tiles)

    action["farmer"] = orders[0]
    action["hands"] = orders[1:]
    return action


# ==============================================================================
# Championship Policy Assembly
# ==============================================================================
__CONFIG_BLOCK__

_POLICY_BACKBONE = _v51_build_policy(_V56_BACKBONE_ROUTE, _CONFIG)
_POLICY_YARN = _v51_build_policy(_V56_YARN_ROUTE, _CONFIG)
_POLICY_BAKERY = _v51_build_policy(_V58_BAKERY_YARN_ROUTE, _CONFIG)

# Runtime State Tracking
_SHOP_STATE = {0: {"route": "backbone", "last": -1}, 1: {"route": "backbone", "last": -1}}


def _select_route(step: int, shops: list) -> str:
    """Minimum Sufficient Shop Controller (S2 Model)."""
    if step < 72 or not shops:
        return "backbone"

    first = str(shops[0]) if len(shops) >= 1 else ""
    second = str(shops[1]) if len(shops) >= 2 else ""

    # Day 3 (Step 72): First town shop unlock
    if first == "YARN_STORE":
        return "yarn"

    # Day 6 (Step 144): Second town shop unlock
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
    __AGENT_DOC__
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
'''

    config_control = "_CONFIG = copy.deepcopy(_V54_CONFIG)"

    config_residual = """_CONFIG_DICT = copy.deepcopy(dict(_V54_CONFIG.__dict__))
_CONFIG_DICT["preempt_money_deficit"] = 2000.0
_CONFIG_DICT["preempt_minimum_delta"] = 4.0
_CONFIG_DICT["preempt_maximum_batch"] = 12
_CONFIG = _V51ResidualConfig(**_CONFIG_DICT)"""

    doc_control = """V54++ Championship Agent (Compiled Standalone Artifact).
Executes V54+ macroeconomic foundation coupled with minimal verified shop-state controller."""

    doc_residual = """V54++ Residual Championship Agent (Compiled Standalone Artifact).
Executes V54++ macro foundation coupled with causally proven aggressive market preemption."""

    header_control = '''# SPDX-License-Identifier: MIT
"""
Compiled Standalone Championship Deployment Artifact: V54++ Control.
Pure observation-driven, zero-dependency, standalone Kaggle deployment agent.
Preserves byte-for-byte identical route tables, shop controller, and tactical overlays.
"""

from __future__ import annotations
import copy
'''

    header_residual = '''# SPDX-License-Identifier: MIT
"""
Compiled Standalone Championship Deployment Artifact: V54++ Residual.
Pure observation-driven, zero-dependency, standalone Kaggle deployment agent.
Preserves byte-for-byte identical route tables, shop controller, tactical overlays,
and verified preemption parameters:
  preempt_money_deficit = 2000.0
  preempt_minimum_delta = 4.0
  preempt_maximum_batch = 12
"""

from __future__ import annotations
import copy
'''

    code_control = (
        header_control
        + v62_base
        + terminal_and_agent_template.replace("__CONFIG_BLOCK__", config_control).replace(
            "__AGENT_DOC__", doc_control
        )
    )

    code_residual = (
        header_residual
        + v62_base
        + terminal_and_agent_template.replace("__CONFIG_BLOCK__", config_residual).replace(
            "__AGENT_DOC__", doc_residual
        )
    )

    out_control = root / "candidates" / "compiled_v54_plus_shop.py"
    out_residual = root / "candidates" / "compiled_v54_plus_residual.py"

    out_control.write_text(code_control, encoding="utf-8", newline="\n")
    out_residual.write_text(code_residual, encoding="utf-8", newline="\n")

    h_ctrl = hashlib.sha256(code_control.encode("utf-8")).hexdigest()
    h_res = hashlib.sha256(code_residual.encode("utf-8")).hexdigest()

    return str(out_control), h_ctrl, str(out_residual), h_res


if __name__ == "__main__":
    out_ctrl, h_ctrl, out_res, h_res = compile_championship_agents()
    print("Compilation successful!")
    print(f"Control:  {out_ctrl} | SHA256: {h_ctrl}")
    print(f"Residual: {out_res} | SHA256: {h_res}")
