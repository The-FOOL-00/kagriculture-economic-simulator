"""
Kagriculture V25 - Prototype P1: Capital/Labor Macro Planner
Features:
1. Optimal Opening Capital Velocity (OPEN_UNITS = 30):
   Drastically reduces market slippage on step 0 wheat wash, preserving net liquid
   cash runway for day 1 hires and animal procurement.
2. Zero-Inventory In-Place Labor Dispatch:
   Eliminates passive PASS turns by executing zero-inventory in-place chores
   (watering dry crops, digging weeds) without altering worker coordinates.
   Preserves 100% spatial and inventory synchronization with V3's downstream routes.
"""

import os
import sys
import copy
import tarfile
import importlib.util

_v3_tar = os.path.join(os.path.dirname(__file__), "..", "submission_Vj_kc_v3.tar.gz")
if not os.path.exists(_v3_tar):
    _v3_tar = os.path.abspath("submission_Vj_kc_v3.tar.gz")

import tempfile
_v3_dir = tempfile.mkdtemp(prefix="v25_p1_base_")
with tarfile.open(_v3_tar, "r:gz") as tar:
    tar.extractall(_v3_dir)

sys.path.insert(0, _v3_dir)
import main as v3_module

_V3_AGENT = v3_module.agent

def _get(value, key, default=None):
    if isinstance(value, dict):
        return value.get(key, default)
    getter = getattr(value, "get", None)
    if callable(getter):
        return getter(key, default)
    return getattr(value, key, default)

def _int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default

def _tile_at(tiles, pos):
    try:
        x, y = int(pos[0]), int(pos[1])
        return tiles[y][x]
    except (TypeError, ValueError, IndexError):
        return "LOCKED"

def agent(observation, configuration=None):
    step = _int(_get(observation, "step", 0))

    # 1. Macro Capital Velocity: Opening Wash Optimization
    # Sdy623's V3 hardcoded OPEN_UNITS=50, incurring high market price slippage.
    # OPEN_UNITS=30 captures the volume turn with minimal slippage, conserving cash.
    if step == 0:
        return {
            "farmer": ["PASS"],
            "hands": [],
            "market": [["BUY_PRODUCT", "WHEAT", 30], ["SELL", "WHEAT", 30]]
        }

    # 2. Base Route-Compiled Action from V3 Chassis
    action = _V3_AGENT(observation, configuration)
    if not isinstance(action, dict):
        return {"farmer": ["PASS"], "hands": [], "market": []}

    try:
        p = _int(_get(observation, "player", 0))
        farms = _get(observation, "farms", [])
        if p >= len(farms):
            return action
        farm = farms[p]
        tiles = _get(farm, "tiles", [])
        farmer_pos = _get(farm, "farmer")
        hands = _get(farm, "hands", []) or []
        positions = [farmer_pos] + list(hands)

        units = [action.get("farmer") or ["PASS"]] + list(action.get("hands") or [])
        modified = False

        # 3. In-place Zero-Inventory Labor Dispatch
        # For units assigned PASS, execute non-disruptive in-place chores that do NOT
        # alter worker coordinates or add uncoordinated items to personal inventories.
        for i in range(min(len(units), len(positions))):
            act = units[i]
            pos = positions[i]
            if not act or act[0] != "PASS" or pos is None:
                continue

            x, y = int(pos[0]), int(pos[1])
            tile = _tile_at(tiles, (x, y))
            if not isinstance(tile, dict):
                continue

            kind = tile.get("kind")

            # Priority 1: Water Dry Growing Crop
            if kind == "PLANT" and not tile.get("watered_today", False):
                units[i] = ["WATER"]
                modified = True
                continue

            # Priority 2: Clear In-Place Weed
            if kind == "WEED":
                units[i] = ["DIG"]
                modified = True
                continue

        if modified:
            action = dict(action)
            action["farmer"] = units[0]
            action["hands"] = units[1:]

    except Exception:
        pass

    return action
