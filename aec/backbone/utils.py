# SPDX-License-Identifier: MIT
"""Backbone common utilities: observation construction, hand alignment, fingerprinting."""

from __future__ import annotations

import copy
from typing import Any, Dict, List, Optional, Tuple

from aec.config import BOARD_SIZE, TURNS_PER_DAY


def _get(value: Any, key: str, default: Any = None) -> Any:
    if isinstance(value, dict):
        return value.get(key, default)
    getter = getattr(value, "get", None)
    if callable(getter):
        return getter(key, default)
    return getattr(value, key, default)


def _int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def align_hands(action: Dict[str, Any], n_hands: int) -> Dict[str, Any]:
    """Ensure hand count matches live farm topology."""
    act = copy.deepcopy(action)
    hands = act.get("hands", []) or []
    if not isinstance(hands, list):
        hands = []
    if len(hands) < n_hands:
        hands = hands + [["PASS"] for _ in range(n_hands - len(hands))]
    elif len(hands) > n_hands:
        hands = hands[:n_hands]
    act["hands"] = hands
    act.setdefault("farmer", ["PASS"])
    act.setdefault("market", [])
    return act


def build_simulated_observation(
    rollout: Any,
    player: int = 0,
    opponent_econ: Optional[Any] = None,
) -> Dict[str, Any]:
    """Construct a full Kaggle-compliant observation dict from a ShadowRolloutState (§11)."""
    cur_step = rollout.step
    day = cur_step // TURNS_PER_DAY
    hour = cur_step % TURNS_PER_DAY

    # Derive farm quadrants
    unlocked_quads = ["NW"]
    if hasattr(rollout, "tiles") and len(rollout.tiles) == 10:
        if rollout.tiles[0][9] != "LOCKED":
            unlocked_quads.append("NE")
        if rollout.tiles[9][0] != "LOCKED":
            unlocked_quads.append("SW")
        if rollout.tiles[9][9] != "LOCKED":
            unlocked_quads.append("SE")

    own_farm = {
        "money": rollout.money,
        "farmer": list(rollout.farmer_pos),
        "hands": [list(p) for p in rollout.hands_pos],
        "tiles": copy.deepcopy(rollout.tiles),
        "hires_today": rollout.hires_today,
        "unlocked_quadrants": list(unlocked_quads),
    }

    opp_cash = getattr(rollout, "opp_money", 3000.0)
    opp_farm = {
        "money": opp_cash,
        "farmer": [4, 4],
        "hands": [],
        "tiles": copy.deepcopy(rollout.tiles),
        "hires_today": 0,
        "unlocked_quadrants": ["NW"],
    }

    farms = [own_farm, opp_farm] if player == 0 else [opp_farm, own_farm]

    if hasattr(rollout, "get_private_dict") and callable(rollout.get_private_dict):
        private_dict = rollout.get_private_dict()
    else:
        private_dict = {
            "shed": getattr(rollout, "shed", {}),
            "seeds": getattr(rollout, "seeds", {}),
            "inventories": [{}, {}],
        }

    return {
        "remainingOverageTime": 60,
        "step": cur_step,
        "player": player,
        "farms": farms,
        "market": {
            "inventory": copy.deepcopy(rollout.market_inv),
            "prices": copy.deepcopy(rollout.market_prices),
        },
        "town": {
            "unlocked_shops": list(rollout.unlocked_shops),
        },
        "day": day,
        "hour": hour,
        "private": {
            "shed": copy.deepcopy(private_dict["shed"]),
            "seeds": copy.deepcopy(private_dict["seeds"]),
            "inventories": copy.deepcopy(private_dict["inventories"]),
        },
    }


def compute_base_macro_fingerprint(
    observation: Dict[str, Any],
    player: int = 0
) -> Dict[str, Any]:
    """Compute the standard macro economic fingerprint from an observation (§15)."""
    step = _int(_get(observation, "step", 0))
    farms = _get(observation, "farms", []) or []
    farm = farms[player] if player < len(farms) else {}
    money = float(_get(farm, "money", 0.0) or 0.0)
    farmer = _get(farm, "farmer", [4, 4])
    hands = _get(farm, "hands", []) or []
    worker_count = 1 + len(hands)

    private = _get(observation, "private", {}) or {}
    shed = dict(_get(private, "shed", {}) or {})
    seeds = dict(_get(private, "seeds", {}) or {})

    # Tiles census
    tiles = _get(farm, "tiles", []) or []
    plant_count = 0
    weed_count = 0
    animal_count = 0
    unwatered_crops = 0

    for row in tiles:
        if not isinstance(row, (list, tuple)):
            continue
        for tile in row:
            if not isinstance(tile, dict):
                continue
            kind = tile.get("kind")
            if kind == "PLANT":
                plant_count += 1
                if not tile.get("watered_today", False):
                    unwatered_crops += 1
            elif kind == "WEED":
                weed_count += 1
            elif kind in ("COOP", "PASTURE") and tile.get("animal") is not None:
                animal_count += 1

    town = _get(observation, "town", {}) or {}
    unlocked_shops = list(_get(town, "unlocked_shops", []) or [])

    # Terminal regime: steps >= 648 (Phase shutdown / terminal liquidation)
    terminal_phase = step >= 648

    return {
        "step": step,
        "money": round(money, 2),
        "worker_count": worker_count,
        "plant_count": plant_count,
        "unwatered_crops": unwatered_crops,
        "weed_count": weed_count,
        "animal_count": animal_count,
        "shed_total": sum(max(0, _int(v)) for v in shed.values()),
        "seeds_total": sum(max(0, _int(v)) for v in seeds.values()),
        "unlocked_shops": sorted(unlocked_shops),
        "terminal_phase": terminal_phase,
    }
