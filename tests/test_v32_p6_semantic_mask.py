# SPDX-License-Identifier: MIT
"""Unit tests for V32 P6 Source-Grounded Semantic Action Mask.

Verifies zero discrepancies between compute_unit_op_mask and kaggriculture 1.32.7
_apply_unit_action across representative states and edge cases.
"""

import copy
import pytest
from kaggle_environments import make
import kaggle_environments.envs.kaggriculture.kaggriculture as kg

from v32.p3 import codec as C
from v32.p6.mask import compute_unit_op_mask, is_shed_adjacent
from v32.p2.essentials import essentialize


def test_shed_adjacency_exact_match():
    """Verify is_shed_adjacent exactly matches kg._is_shed_adjacent."""
    for x in range(10):
        for y in range(10):
            kg_res = kg._is_shed_adjacent((x, y), 10)
            p6_res = is_shed_adjacent((x, y), 10)
            assert kg_res == p6_res, f"Mismatch at ({x}, {y}): sim={kg_res}, p6={p6_res}"


def test_step2_farmer_pos_not_shed_adjacent():
    """Farmer at [4, 3] must NOT be shed adjacent, and PICKUP must be masked."""
    assert not is_shed_adjacent((4, 3), 10)
    ess = {
        "farmer": [4, 3],
        "shed": {"COW": 2, "SHEEP": 2},
        "inv": [{}],
        "seeds": {},
        "ucode": [0],
    }
    mask = compute_unit_op_mask(ess, 0, board_size=10)
    assert not mask[C._U_OP_ID["PICKUP"]], "PICKUP must be masked at [4, 3]"
    assert mask[C._U_OP_ID["SOUTH"]], "SOUTH must be valid at [4, 3]"
    assert mask[C._U_OP_ID["NORTH"]], "NORTH must be valid at [4, 3]"
    assert mask[C._U_OP_ID["PASS"]], "PASS must be valid at [4, 3]"


def test_step2_hand_pos_is_shed_adjacent():
    """Hand at [4, 4] IS shed adjacent and CAN pickup cow if shed has cows."""
    assert is_shed_adjacent((4, 4), 10)
    ess = {
        "farmer": [4, 3],
        "hands": [[4, 4]],
        "shed": {"COW": 2},
        "inv": [{}, {}],
        "seeds": {},
        "ucode": [0, 0],
    }
    mask_hand = compute_unit_op_mask(ess, 1, board_size=10)
    assert mask_hand[C._U_OP_ID["PICKUP"]], "Hand at [4, 4] must be allowed to PICKUP from shed"


def test_pickup_requires_items_in_shed():
    """Even if shed adjacent, PICKUP is invalid if shed has 0 items."""
    ess = {
        "farmer": [4, 4],
        "shed": {"COW": 0, "SHEEP": 0, "WHEAT": 0},
        "inv": [{}],
        "seeds": {},
        "ucode": [0],
    }
    mask = compute_unit_op_mask(ess, 0, board_size=10)
    assert not mask[C._U_OP_ID["PICKUP"]], "PICKUP must be masked if shed has 0 items"


def test_board_boundary_moves():
    """Directional moves that exit the board must be masked."""
    ess_top_left = {
        "farmer": [0, 0],
        "inv": [{}],
        "seeds": {},
        "ucode": [0],
    }
    mask = compute_unit_op_mask(ess_top_left, 0, board_size=10)
    assert not mask[C._U_OP_ID["NORTH"]], "NORTH out of bounds must be masked"
    assert not mask[C._U_OP_ID["WEST"]], "WEST out of bounds must be masked"
    assert mask[C._U_OP_ID["SOUTH"]], "SOUTH in bounds must be valid"
    assert mask[C._U_OP_ID["EAST"]], "EAST in bounds must be valid"


def test_simulator_discrepancy_corpus():
    """Run simulator step with mock units and assert zero discrepancies with _apply_unit_action."""
    env = make("kaggriculture", configuration={"seed": 249675})
    obs = env.reset()[0].observation
    ess = essentialize(obs, 0)
    tiles = obs["farms"][0]["tiles"]

    for op_name in C.U_OP:
        op_id = C._U_OP_ID[op_name]
        mask = compute_unit_op_mask(ess, 0, raw_tiles=tiles, board_size=10)
        is_masked = not mask[op_id]

        # Test against simulator _apply_unit_action
        farm_copy = copy.deepcopy(obs["farms"][0])
        priv_copy = copy.deepcopy(obs["private"])
        
        # Test literal
        action_lit = [op_name]
        if op_name in ("PICKUP", "PLACE"):
            action_lit = [op_name, "COW", 1]
        elif op_name == "PLANT":
            action_lit = [op_name, "WHEAT"]

        # Snapshot before
        f_before = copy.deepcopy(farm_copy)
        p_before = copy.deepcopy(priv_copy)

        kg._apply_unit_action(farm_copy, priv_copy, 0, action_lit, 10, 0, 24)

        # Did simulator mutate state?
        mutated = (farm_copy != f_before) or (priv_copy != p_before)

        if mutated:
            assert not is_masked, f"Mask incorrectly marked valid action {op_name} as masked!"
