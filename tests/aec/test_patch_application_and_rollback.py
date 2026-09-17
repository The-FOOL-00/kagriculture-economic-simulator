# SPDX-License-Identifier: MIT
"""Test E & Test F — Patch Application and Rollback Immutability."""

import copy
from aec.patches import CoupledPatch


def test_patch_application_modifies_only_targets():
    baseline = {
        "farmer": ["NORTH"],
        "hands": [["EAST"], ["SOUTH"]],
        "market": [["BUY_PRODUCT", "WHEAT", 10]]
    }
    baseline_copy = copy.deepcopy(baseline)
    
    # Patch only modifies farmer and market
    patch = CoupledPatch(
        patch_id="TEST_PATCH",
        source_opportunity_id="OPP_1",
        worker_mutations={0: ["DIG"]},
        market_mutations=[["SELL", "WHEAT", 10]],
        expected_horizon=4
    )
    
    modified = patch.apply(baseline)
    
    # 1. Targets changed correctly
    assert modified["farmer"] == ["DIG"]
    assert modified["market"] == [["SELL", "WHEAT", 10]]
    
    # 2. Unrelated targets (hands) remain untouched
    assert modified["hands"] == [["EAST"], ["SOUTH"]]
    
    # 3. Original baseline action is completely unmutated
    assert baseline == baseline_copy


def test_patch_rollback_restores_baseline():
    baseline = {
        "farmer": ["PASS"],
        "hands": [["PASS"]],
        "market": [["HIRE"]]
    }
    
    patch = CoupledPatch(
        patch_id="TEST_PATCH_2",
        source_opportunity_id="OPP_2",
        worker_mutations={1: ["WATER"]},
        market_mutations=[["SELL", "STRAWBERRY", 5]]
    )
    
    # Simulate candidate application
    candidate_action = patch.apply(baseline)
    assert candidate_action != baseline
    
    # Decision: ABSTAIN -> Emit original baseline
    final_action = baseline
    assert final_action["farmer"] == ["PASS"]
    assert final_action["market"] == [["HIRE"]]
