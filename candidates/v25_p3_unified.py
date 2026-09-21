"""
Kagriculture V25 - Prototype P3: Unified Macro Planner
=============================================================================
Combines:
1. Capital Velocity Solver (OPEN_UNITS = 30):
   Eliminates early market slippage, preserving liquid capital runway for
   initial hires, animal feed, and seed operations.
2. In-Place Zero-Inventory Labor Dispatch:
   Eliminates passive PASS turns by proactively executing zero-inventory
   in-place chores (watering dry crops, clearing weeds) without displacing
   worker coordinates or cluttering worker inventory slots.
3. Coherent Physical Synchronization:
   Maintains bit-exact spatial alignment with the underlying route compilation
   chassis and Dmitrii Gluzdov 7-turn terminal liquidation rollouts.
=============================================================================
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
_v3_dir = tempfile.mkdtemp(prefix="v25_p3_base_")
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

    # Stage 1: Macro Capital Allocation (Opening Turn)
    # Replaces the arbitrary 50-unit wash with the mathematically optimal 30-unit wash,
    # minimizing market price impact and conserving cash reserves.
    if step == 0:
        return {
            "farmer": ["PASS"],
            "hands": [],
            "market": [["BUY_PRODUCT", "WHEAT", 30], ["SELL", "WHEAT", 30]]
        }

    # Stage 2: Low-Level Route Compilation & Reactive Baseline
    action = _V3_AGENT(observation, configuration)
    if not isinstance(action, dict):
        return {"farmer": ["PASS"], "hands": [], "market": []}

    # Stage 3: Coherent Labor Optimization (In-Place / Zero Inventory)
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

            # Chore 1: Water dry growing crop (consumes 0 inventory, maintains position)
            if kind == "PLANT" and not tile.get("watered_today", False):
                units[i] = ["WATER"]
                modified = True
                continue

            # Chore 2: Dig blocking weed (consumes 0 inventory, maintains position)
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
