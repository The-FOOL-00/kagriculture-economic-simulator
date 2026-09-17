# SPDX-License-Identifier: MIT
"""Test A — Economic IR Construction, Determinism, and Isolation."""

import copy
from aec.ir import build_economic_state, EconomicState


def test_economic_ir_deterministic_construction(normal_opening_obs):
    state1 = build_economic_state(normal_opening_obs)
    state2 = build_economic_state(normal_opening_obs)
    
    assert state1.step == state2.step == 0
    assert state1.phase == state2.phase == "OPENING"
    assert state1.farm.cash == state2.farm.cash == 3000.0
    assert state1.workers.total_workers == state2.workers.total_workers == 1
    assert state1.remaining_horizon == state2.remaining_horizon == 718


def test_economic_ir_no_live_mutation(normal_opening_obs):
    obs_copy = copy.deepcopy(normal_opening_obs)
    state = build_economic_state(obs_copy)
    
    # Mutate raw observation after construction
    obs_copy["farms"][0]["money"] = 99999.0
    obs_copy["private"]["shed"]["WHEAT"] = 500
    
    # Assert state remains completely isolated
    assert state.farm.cash == 3000.0
    assert state.farm.shed_inventory.get("WHEAT", 0) == 0


def test_economic_ir_correct_extraction(weed_obstruction_obs):
    state = build_economic_state(weed_obstruction_obs)
    
    assert state.step == 48
    assert state.day == 2
    assert state.farm.cash == 2500.0
    assert state.workers.total_workers == 2
    assert state.farm.shed_inventory.get("WHEAT") == 10
    
    # Farmer position should be (4, 4)
    farmer = state.workers.get_worker(0)
    assert farmer is not None
    assert farmer.position == (4, 4)
    assert farmer.deposit_path_len == 0  # (4, 4) is a shed corner
