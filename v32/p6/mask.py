# SPDX-License-Identifier: MIT
"""V32 P6 Source-Grounded Semantic Action Mask.

Derived strictly from kaggle_environments.envs.kaggriculture.kaggriculture:
- _apply_unit_action
- _shed_access_tiles
- _is_shed_adjacent

Invariants:
- Never masks an action that the simulator would execute.
- Always masks an action that the simulator would reject as a silent no-op.
"""

import numpy as np
from v32.p3 import codec as C

ANIMALS = {
    "COW": {"structure": "PASTURE"},
    "SHEEP": {"structure": "PASTURE"},
    "GOOSE": {"structure": "COOP"},
}


def is_shed_adjacent(pos, board_size=10):
    half = board_size // 2
    shed_tiles = {(half - 1, half - 1), (half, half - 1), (half - 1, half), (half, half)}
    return tuple(pos) in shed_tiles


def get_unit_pos(ess, unit_idx):
    if unit_idx == 0:
        return ess.get("farmer", [4, 4])
    hands = ess.get("hands", []) or []
    if unit_idx - 1 < len(hands):
        return hands[unit_idx - 1]
    return [4, 4]


def get_unit_inv(ess, unit_idx):
    invs = ess.get("inv", []) or []
    if unit_idx < len(invs) and isinstance(invs[unit_idx], dict):
        return invs[unit_idx]
    return {}


def compute_unit_op_mask(ess, unit_idx, raw_tiles=None, board_size=10):
    """Returns a boolean mask of length 18 (True = Valid/Legal, False = Invalid/Rejected)."""
    mask = [False] * len(C.U_OP)
    pos = get_unit_pos(ess, unit_idx)
    fx, fy = int(pos[0]), int(pos[1])
    inv = get_unit_inv(ess, unit_idx)
    shed = ess.get("shed", {}) or {}
    seeds = ess.get("seeds", {}) or {}

    # PASS is always valid
    mask[C._U_OP_ID["PASS"]] = True

    # Directional moves
    if 0 <= fx < board_size and 0 <= fy - 1 < board_size:
        mask[C._U_OP_ID["NORTH"]] = True
    if 0 <= fx < board_size and 0 <= fy + 1 < board_size:
        mask[C._U_OP_ID["SOUTH"]] = True
    if 0 <= fx + 1 < board_size and 0 <= fy < board_size:
        mask[C._U_OP_ID["EAST"]] = True
    if 0 <= fx - 1 < board_size and 0 <= fy < board_size:
        mask[C._U_OP_ID["WEST"]] = True

    adjacent = is_shed_adjacent((fx, fy), board_size)

    # DROP: requires shed adjacent and having at least 1 item in inventory
    if adjacent and sum(inv.values()) > 0:
        mask[C._U_OP_ID["DROP"]] = True

    # PICKUP: requires shed adjacent and having at least 1 non-seed item in shed
    if adjacent and sum(shed.values()) > 0:
        mask[C._U_OP_ID["PICKUP"]] = True

    # Tile-specific operations if raw_tiles available
    if raw_tiles is not None and 0 <= fy < len(raw_tiles) and 0 <= fx < len(raw_tiles[0]):
        tile = raw_tiles[fy][fx]
        if tile != "LOCKED":
            # BUILD_COOP / BUILD_PASTURE: empty tile
            if tile is None:
                mask[C._U_OP_ID["BUILD_COOP"]] = True
                mask[C._U_OP_ID["BUILD_PASTURE"]] = True
                # PLANT: empty tile and seeds available
                if sum(seeds.values()) > 0:
                    mask[C._U_OP_ID["PLANT"]] = True
            elif isinstance(tile, dict):
                k = tile.get("kind")
                has_animal = "animal" in tile
                # WATER / FERTILIZE: plant tile
                if k == "PLANT":
                    if not tile.get("watered_today"):
                        mask[C._U_OP_ID["WATER"]] = True
                    if inv.get("FERTILIZER", 0) > 0:
                        mask[C._U_OP_ID["FERTILIZE"]] = True
                # HARVEST: plant or animal with yield > 0
                if tile.get("yield_units", 0) > 0:
                    mask[C._U_OP_ID["HARVEST"]] = True
                # FEED / COLLECT_FERTILIZER / CARE: animal tile
                if has_animal:
                    if not tile.get("fed_today") and inv.get("WHEAT", 0) > 0:
                        mask[C._U_OP_ID["FEED"]] = True
                    if tile.get("fertilizer_available"):
                        mask[C._U_OP_ID["COLLECT_FERTILIZER"]] = True
                    if not tile.get("cared_today"):
                        mask[C._U_OP_ID["CARE"]] = True
                # DIG: any structure/plant without animal
                if not has_animal:
                    mask[C._U_OP_ID["DIG"]] = True
                # PLACE on animal structure
                for an, spec in ANIMALS.items():
                    if k == spec["structure"] and not has_animal and inv.get(an, 0) > 0:
                        mask[C._U_OP_ID["PLACE"]] = True
    else:
        # Fallback when raw_tiles not directly passed: ucode from ess
        ucode = ess.get("ucode", [0])[unit_idx] if unit_idx < len(ess.get("ucode", [])) else 0
        # ucode: 0 = empty unlocked, 1 = locked/other, 2 = weed, 3 = harvest plant, 4 = plant, 5 = coop, 6 = pasture, 7 = animal, 8 = animal+fert
        if ucode == 0:
            mask[C._U_OP_ID["BUILD_COOP"]] = True
            mask[C._U_OP_ID["BUILD_PASTURE"]] = True
            if sum(seeds.values()) > 0:
                mask[C._U_OP_ID["PLANT"]] = True
        elif ucode in (3, 4):
            mask[C._U_OP_ID["WATER"]] = True
            if inv.get("FERTILIZER", 0) > 0:
                mask[C._U_OP_ID["FERTILIZE"]] = True
            if ucode == 3:
                mask[C._U_OP_ID["HARVEST"]] = True
            mask[C._U_OP_ID["DIG"]] = True
        elif ucode in (7, 8):
            if inv.get("WHEAT", 0) > 0:
                mask[C._U_OP_ID["FEED"]] = True
            if ucode == 8:
                mask[C._U_OP_ID["COLLECT_FERTILIZER"]] = True
            mask[C._U_OP_ID["CARE"]] = True
        elif ucode in (5, 6):
            mask[C._U_OP_ID["DIG"]] = True
            if ucode == 6 and (inv.get("COW", 0) > 0 or inv.get("SHEEP", 0) > 0):
                mask[C._U_OP_ID["PLACE"]] = True
            if ucode == 5 and inv.get("GOOSE", 0) > 0:
                mask[C._U_OP_ID["PLACE"]] = True

    # PLACE into shed: if adjacent and having any animal/item in inventory
    if adjacent and sum(inv.values()) > 0:
        mask[C._U_OP_ID["PLACE"]] = True

    return mask


def apply_mask_to_logits(logits, mask, fill_value=-1e9):
    """Applies boolean mask (True=valid, False=invalid) to raw logits."""
    masked = logits.copy()
    for i, valid in enumerate(mask):
        if not valid:
            masked[i] = fill_value
    return masked
