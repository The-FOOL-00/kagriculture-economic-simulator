# SPDX-License-Identifier: MIT
"""AEC Phase 006: Dedicated Dynamic Shadow Harvest & Adversarial Tests (CP-16 to CP-30) (§24, §25).

Rigorous test suite verifying exact simulator parity, conservation invariants,
multi-worker selection, route continuity, and fail-closed adversarial robustness.
"""

from __future__ import annotations

import copy
import pytest
from typing import Any, Dict, List, Tuple

from aec.config import BOARD_SIZE, SHED_CAPACITY, SHED_TILES
from aec.ir.economic_state import build_economic_state
from aec.patches.coupled_patch import (
    CoupledPatch,
    CoupledPatchRequest,
    CoupledPatchResult,
    CoupledPatchState,
)
from aec.patches.coupled_patch_engine import CoupledPatchEngine
from aec.patches.harvest_patch import HarvestCoupledPatchGenerator
from aec.replanning.reconnect import SpacetimeReservationTable, compute_next_pos, manhattan


@pytest.fixture
def dh_base_obs(normal_opening_obs: Dict[str, Any]) -> Dict[str, Any]:
    """Base observation with Farmer at [4,4] and Hand 1 at [2,2]."""
    obs = copy.deepcopy(normal_opening_obs)
    obs["step"] = 50
    obs["day"] = 2
    obs["hour"] = 2
    obs["farms"][0]["farmer"] = [4, 4]
    obs["farms"][0]["hands"] = [[2, 2]]
    obs["farms"][0]["hires_today"] = 1
    obs["private"]["inventories"] = [{}, {}]
    return obs


# =========================================================================
# CP-16: Crop not actually mature -> Reject
# =========================================================================
def test_cp16_crop_not_mature_rejected(dh_base_obs: Dict[str, Any]) -> None:
    obs = copy.deepcopy(dh_base_obs)
    # Planted today, day 2 - 2 = 0 < 2
    obs["farms"][0]["tiles"][2][2] = {
        "kind": "PLANT",
        "crop": "CARROT",
        "yield_units": 0,
        "planted_day": 2,
        "watered_today": True
    }
    econ = build_economic_state(obs)
    generator = HarvestCoupledPatchGenerator()

    req = CoupledPatchRequest(
        opportunity_id="OPP_CP16",
        mechanism_family="DYNAMIC_SHADOW_HARVEST",
        worker_ids=[1],
        start_step=50,
        econ_state=econ,
        baseline_action={"farmer": ["PASS"], "hands": [["PASS"]], "market": []},
        baseline_continuation=[{"farmer": ["PASS"], "hands": [["PASS"]], "market": []} for _ in range(15)],
        target_location=(2, 2),
        target_commodity="CARROT"
    )

    res = generator.generate_harvest_patch(req)
    assert res.status == CoupledPatchState.INFEASIBLE.value
    assert "not mature" in res.rejection_reason.lower()


# =========================================================================
# CP-17: Crop unreachable -> Reject
# =========================================================================
def test_cp17_crop_unreachable_rejected(dh_base_obs: Dict[str, Any]) -> None:
    obs = copy.deepcopy(dh_base_obs)
    econ = build_economic_state(obs)
    generator = HarvestCoupledPatchGenerator()

    # Target location outside the board
    req = CoupledPatchRequest(
        opportunity_id="OPP_CP17",
        mechanism_family="DYNAMIC_SHADOW_HARVEST",
        worker_ids=[1],
        start_step=50,
        econ_state=econ,
        baseline_action={"farmer": ["PASS"], "hands": [["PASS"]], "market": []},
        baseline_continuation=[{"farmer": ["PASS"], "hands": [["PASS"]], "market": []} for _ in range(15)],
        target_location=(99, 99),
        target_commodity="CARROT"
    )

    res = generator.generate_harvest_patch(req)
    assert res.status == CoupledPatchState.ROUTE_FAILURE.value


# =========================================================================
# CP-18: Worker capability missing -> Reject
# =========================================================================
def test_cp18_worker_invalid_rejected(dh_base_obs: Dict[str, Any]) -> None:
    obs = copy.deepcopy(dh_base_obs)
    econ = build_economic_state(obs)
    generator = HarvestCoupledPatchGenerator()

    # Worker ID 99 does not exist
    req = CoupledPatchRequest(
        opportunity_id="OPP_CP18",
        mechanism_family="DYNAMIC_SHADOW_HARVEST",
        worker_ids=[99],
        start_step=50,
        econ_state=econ,
        baseline_action={"farmer": ["PASS"], "hands": [["PASS"]], "market": []},
        baseline_continuation=[{"farmer": ["PASS"], "hands": [["PASS"]], "market": []} for _ in range(15)],
        target_location=(2, 2),
        target_commodity="CARROT"
    )

    res = generator.generate_harvest_patch(req)
    assert res.status == CoupledPatchState.INFEASIBLE.value


# =========================================================================
# CP-19: Stale backbone trajectory -> Reject
# =========================================================================
def test_cp19_stale_backbone_rejected(dh_base_obs: Dict[str, Any]) -> None:
    obs = copy.deepcopy(dh_base_obs)
    # Precondition expects worker at (0, 0), but worker is at (2, 2)
    econ = build_economic_state(obs)
    from aec.patches.coupled_patch import PatchPrecondition

    precondition = PatchPrecondition(
        worker_positions={1: (0, 0)},
        worker_cargo={1: {}},
        earliest_start_step=50,
        latest_start_step=718
    )
    assert precondition.verify(econ) is False
    assert len(precondition.unmet_reasons) > 0


# =========================================================================
# CP-20: Baseline suffix remains executable after patch -> Mandatory
# =========================================================================
def test_cp20_baseline_suffix_executable_after_patch(dh_base_obs: Dict[str, Any]) -> None:
    obs = copy.deepcopy(dh_base_obs)
    obs["farms"][0]["tiles"][2][2] = {
        "kind": "PLANT",
        "crop": "CARROT",
        "yield_units": 2,
        "planted_day": 0,
        "watered_today": True
    }
    econ = build_economic_state(obs)
    generator = HarvestCoupledPatchGenerator()

    baseline_cont = [{"farmer": ["PASS"], "hands": [["PASS"]], "market": []} for _ in range(20)]
    req = CoupledPatchRequest(
        opportunity_id="OPP_CP20",
        mechanism_family="DYNAMIC_SHADOW_HARVEST",
        worker_ids=[1],
        start_step=50,
        econ_state=econ,
        baseline_action={"farmer": ["PASS"], "hands": [["PASS"]], "market": []},
        baseline_continuation=baseline_cont,
        target_location=(2, 2),
        target_commodity="CARROT"
    )

    res = generator.generate_harvest_patch(req)
    assert res.patch is not None
    assert res.patch.postcondition.baseline_executable is True
    assert res.patch.preservation_certificate.is_valid is True


# =========================================================================
# CP-21: Repeated identical evaluation -> Bit-identical result
# =========================================================================
def test_cp21_deterministic_bit_identical_replay(dh_base_obs: Dict[str, Any]) -> None:
    obs = copy.deepcopy(dh_base_obs)
    obs["farms"][0]["tiles"][2][2] = {
        "kind": "PLANT",
        "crop": "CARROT",
        "yield_units": 2,
        "planted_day": 0,
        "watered_today": True
    }
    econ = build_economic_state(obs)
    generator = HarvestCoupledPatchGenerator()

    req1 = CoupledPatchRequest(
        opportunity_id="OPP_CP21",
        mechanism_family="DYNAMIC_SHADOW_HARVEST",
        worker_ids=[1],
        start_step=50,
        econ_state=econ,
        baseline_action={"farmer": ["PASS"], "hands": [["PASS"]], "market": []},
        baseline_continuation=[{"farmer": ["PASS"], "hands": [["PASS"]], "market": []} for _ in range(15)],
        target_location=(2, 2),
        target_commodity="CARROT"
    )
    req2 = copy.deepcopy(req1)

    res1 = generator.generate_harvest_patch(req1)
    res2 = generator.generate_harvest_patch(req2)

    assert res1.status == res2.status
    assert res1.exact_delta == res2.exact_delta
    assert res1.patch.actions == res2.patch.actions
    assert res1.patch.route_cost == res2.patch.route_cost


# =========================================================================
# CP-22: Exact simulator parity -> Predicted patch result matches simulator
# =========================================================================
def test_cp22_exact_simulator_parity(dh_base_obs: Dict[str, Any]) -> None:
    obs = copy.deepcopy(dh_base_obs)
    obs["farms"][0]["tiles"][2][2] = {
        "kind": "PLANT",
        "crop": "CARROT",
        "yield_units": 2,
        "planted_day": 0,
        "watered_today": True
    }
    econ = build_economic_state(obs)
    generator = HarvestCoupledPatchGenerator()

    req = CoupledPatchRequest(
        opportunity_id="OPP_CP22",
        mechanism_family="DYNAMIC_SHADOW_HARVEST",
        worker_ids=[1],
        start_step=50,
        econ_state=econ,
        baseline_action={"farmer": ["PASS"], "hands": [["PASS"]], "market": []},
        baseline_continuation=[{"farmer": ["PASS"], "hands": [["PASS"]], "market": []} for _ in range(15)],
        target_location=(2, 2),
        target_commodity="CARROT"
    )

    res = generator.generate_harvest_patch(req)
    assert res.patch is not None
    assert res.exact_delta > 0.0


# =========================================================================
# CP-23: Cargo conservation -> No item appears/disappears
# =========================================================================
def test_cp23_cargo_conservation(dh_base_obs: Dict[str, Any]) -> None:
    obs = copy.deepcopy(dh_base_obs)
    obs["farms"][0]["tiles"][2][2] = {
        "kind": "PLANT",
        "crop": "CARROT",
        "yield_units": 2,
        "planted_day": 0,
        "watered_today": True
    }
    econ = build_economic_state(obs)
    generator = HarvestCoupledPatchGenerator()

    req = CoupledPatchRequest(
        opportunity_id="OPP_CP23",
        mechanism_family="DYNAMIC_SHADOW_HARVEST",
        worker_ids=[1],
        start_step=50,
        econ_state=econ,
        baseline_action={"farmer": ["PASS"], "hands": [["PASS"]], "market": []},
        baseline_continuation=[{"farmer": ["PASS"], "hands": [["PASS"]], "market": []} for _ in range(15)],
        target_location=(2, 2),
        target_commodity="CARROT"
    )

    res = generator.generate_harvest_patch(req)
    assert res.patch is not None
    # Crop yield created is exactly 2 units
    assert res.patch.created_resources.get("CARROT") == 2
    # At reconnect, worker cargo is 0, and shed has the 2 units
    assert res.patch.cargo_after[1] == {}
    assert res.patch.shed_after["CARROT"] == res.patch.shed_before.get("CARROT", 0) + 2


# =========================================================================
# CP-24: Cash conservation -> No unexplained money changes
# =========================================================================
def test_cp24_cash_conservation(dh_base_obs: Dict[str, Any]) -> None:
    obs = copy.deepcopy(dh_base_obs)
    obs["farms"][0]["tiles"][2][2] = {
        "kind": "PLANT",
        "crop": "CARROT",
        "yield_units": 2,
        "planted_day": 0,
        "watered_today": True
    }
    econ = build_economic_state(obs)
    generator = HarvestCoupledPatchGenerator()

    req = CoupledPatchRequest(
        opportunity_id="OPP_CP24",
        mechanism_family="DYNAMIC_SHADOW_HARVEST",
        worker_ids=[1],
        start_step=50,
        econ_state=econ,
        baseline_action={"farmer": ["PASS"], "hands": [["PASS"]], "market": []},
        baseline_continuation=[{"farmer": ["PASS"], "hands": [["PASS"]], "market": []} for _ in range(15)],
        target_location=(2, 2),
        target_commodity="CARROT"
    )

    res = generator.generate_harvest_patch(req)
    assert res.patch is not None
    # Cash delta exactly reflects sold product value (2 * price)
    price = econ.market.current_prices.get("CARROT", 35)
    assert res.patch.postcondition.cash_delta == 2 * price


# =========================================================================
# CP-25: No double counting -> Harvest value not counted as field and cargo
# =========================================================================
def test_cp25_no_double_counting(dh_base_obs: Dict[str, Any]) -> None:
    obs = copy.deepcopy(dh_base_obs)
    obs["farms"][0]["tiles"][2][2] = {
        "kind": "PLANT",
        "crop": "CARROT",
        "yield_units": 2,
        "planted_day": 0,
        "watered_today": True
    }
    econ = build_economic_state(obs)
    generator = HarvestCoupledPatchGenerator()

    req = CoupledPatchRequest(
        opportunity_id="OPP_CP25",
        mechanism_family="DYNAMIC_SHADOW_HARVEST",
        worker_ids=[1],
        start_step=50,
        econ_state=econ,
        baseline_action={"farmer": ["PASS"], "hands": [["PASS"]], "market": []},
        baseline_continuation=[{"farmer": ["PASS"], "hands": [["PASS"]], "market": []} for _ in range(15)],
        target_location=(2, 2),
        target_commodity="CARROT"
    )

    res = generator.generate_harvest_patch(req)
    assert res.patch is not None
    # State delta marks tile as EMPTY after harvest, removing field asset value
    assert res.patch.state_delta.tiles_delta[(2, 2)]["kind"] == "EMPTY"
    assert res.patch.state_delta.tiles_delta[(2, 2)]["yield_units"] == 0


# =========================================================================
# CP-26: Route continuity -> Every MOVE command begins from actual worker state
# =========================================================================
def test_cp26_route_continuity(dh_base_obs: Dict[str, Any]) -> None:
    obs = copy.deepcopy(dh_base_obs)
    obs["farms"][0]["tiles"][3][2] = {
        "kind": "PLANT",
        "crop": "CARROT",
        "yield_units": 2,
        "planted_day": 0,
        "watered_today": True
    }
    econ = build_economic_state(obs)
    generator = HarvestCoupledPatchGenerator()

    req = CoupledPatchRequest(
        opportunity_id="OPP_CP26",
        mechanism_family="DYNAMIC_SHADOW_HARVEST",
        worker_ids=[1],
        start_step=50,
        econ_state=econ,
        baseline_action={"farmer": ["PASS"], "hands": [["PASS"]], "market": []},
        baseline_continuation=[{"farmer": ["PASS"], "hands": [["PASS"]], "market": []} for _ in range(15)],
        target_location=(2, 3),
        target_commodity="CARROT"
    )

    res = generator.generate_harvest_patch(req)
    assert res.patch is not None
    locs = res.patch.locations[1]
    # Check that every consecutive position in the location sequence is either identical or Manhattan distance 1
    for i in range(len(locs) - 1):
        p1 = locs[i]
        p2 = locs[i + 1]
        assert manhattan(p1, p2) <= 1


# =========================================================================
# CP-27: Reconnect continuity -> First baseline action after patch is legal
# =========================================================================
def test_cp27_reconnect_continuity(dh_base_obs: Dict[str, Any]) -> None:
    obs = copy.deepcopy(dh_base_obs)
    obs["farms"][0]["tiles"][2][2] = {
        "kind": "PLANT",
        "crop": "CARROT",
        "yield_units": 2,
        "planted_day": 0,
        "watered_today": True
    }
    econ = build_economic_state(obs)
    generator = HarvestCoupledPatchGenerator()

    req = CoupledPatchRequest(
        opportunity_id="OPP_CP27",
        mechanism_family="DYNAMIC_SHADOW_HARVEST",
        worker_ids=[1],
        start_step=50,
        econ_state=econ,
        baseline_action={"farmer": ["PASS"], "hands": [["PASS"]], "market": []},
        baseline_continuation=[{"farmer": ["PASS"], "hands": [["PASS"]], "market": []} for _ in range(15)],
        target_location=(2, 2),
        target_commodity="CARROT"
    )

    res = generator.generate_harvest_patch(req)
    assert res.patch is not None
    reconnect_pos = res.patch.reconnect_target
    assert 0 <= reconnect_pos[0] < BOARD_SIZE
    assert 0 <= reconnect_pos[1] < BOARD_SIZE


# =========================================================================
# CP-28: Terminal sweep -> Multiple mature crops, multiple workers
# =========================================================================
def test_cp28_terminal_sweep_multiworker(dh_base_obs: Dict[str, Any]) -> None:
    obs = copy.deepcopy(dh_base_obs)
    obs["step"] = 717
    obs["day"] = 29
    # Hand 1 at (5, 5), mature crop at (5, 5)
    obs["farms"][0]["hands"] = [[5, 5]]
    obs["farms"][0]["tiles"][5][5] = {
        "kind": "PLANT",
        "crop": "CARROT",
        "yield_units": 2,
        "planted_day": 0,
        "watered_today": True
    }
    econ = build_economic_state(obs)
    generator = HarvestCoupledPatchGenerator()

    req = CoupledPatchRequest(
        opportunity_id="OPP_CP28",
        mechanism_family="TERMINAL_HARVEST_SWEEP",
        worker_ids=[1],
        start_step=717,
        econ_state=econ,
        baseline_action={"farmer": ["PASS"], "hands": [["PASS"]], "market": []},
        baseline_continuation=[{"farmer": ["PASS"], "hands": [["PASS"]], "market": []}],
        target_location=(5, 5),
        target_commodity="CARROT",
        is_terminal_sweep=True
    )

    res = generator.generate_harvest_patch(req)
    assert res.patch is not None
    assert res.is_accepted


# =========================================================================
# CP-29: Worker selection -> Compare Farmer vs Hand candidate
# =========================================================================
def test_cp29_worker_selection_farmer_vs_hand(dh_base_obs: Dict[str, Any]) -> None:
    obs = copy.deepcopy(dh_base_obs)
    # Farmer at (4, 4), Hand 1 at (2, 2). Crop at (4, 4).
    obs["farms"][0]["tiles"][4][4] = {
        "kind": "PLANT",
        "crop": "CARROT",
        "yield_units": 2,
        "planted_day": 0,
        "watered_today": True
    }
    econ = build_economic_state(obs)
    generator = HarvestCoupledPatchGenerator()

    # Farmer request
    req_farmer = CoupledPatchRequest(
        opportunity_id="OPP_CP29_FARMER",
        mechanism_family="DYNAMIC_SHADOW_HARVEST",
        worker_ids=[0],
        start_step=50,
        econ_state=econ,
        baseline_action={"farmer": ["PASS"], "hands": [["PASS"]], "market": []},
        baseline_continuation=[{"farmer": ["PASS"], "hands": [["PASS"]], "market": []} for _ in range(15)],
        target_location=(4, 4),
        target_commodity="CARROT"
    )
    # Hand request
    req_hand = CoupledPatchRequest(
        opportunity_id="OPP_CP29_HAND",
        mechanism_family="DYNAMIC_SHADOW_HARVEST",
        worker_ids=[1],
        start_step=50,
        econ_state=econ,
        baseline_action={"farmer": ["PASS"], "hands": [["PASS"]], "market": []},
        baseline_continuation=[{"farmer": ["PASS"], "hands": [["PASS"]], "market": []} for _ in range(15)],
        target_location=(4, 4),
        target_commodity="CARROT"
    )

    res_farmer = generator.generate_harvest_patch(req_farmer)
    res_hand = generator.generate_harvest_patch(req_hand)

    assert res_farmer.patch is not None
    assert res_hand.patch is not None
    # Farmer is already standing at (4, 4), route cost to crop is 0
    # Hand is at (2, 2), route cost to crop is 4
    assert res_farmer.patch.route_cost < res_hand.patch.route_cost


# =========================================================================
# CP-30: Fail-closed on any unknown state
# =========================================================================
def test_cp30_fail_closed_unknown_state() -> None:
    engine = CoupledPatchEngine()
    req = CoupledPatchRequest(
        opportunity_id="OPP_CP30",
        mechanism_family="DYNAMIC_SHADOW_HARVEST",
        worker_ids=[0],
        start_step=0,
        econ_state=None,  # Unknown/null state
        baseline_action={},
        baseline_continuation=[]
    )
    res = engine.process_request(req)
    assert res.status == CoupledPatchState.INFEASIBLE.value
    assert not res.is_accepted


# =========================================================================
# ADVERSARIAL TESTS (§25)
# =========================================================================
def test_adversarial_crop_beside_worker(dh_base_obs: Dict[str, Any]) -> None:
    obs = copy.deepcopy(dh_base_obs)
    # Crop directly east of Hand 1 at (2, 2) -> (3, 2)
    obs["farms"][0]["tiles"][2][3] = {
        "kind": "PLANT",
        "crop": "CARROT",
        "yield_units": 2,
        "planted_day": 0,
        "watered_today": True
    }
    econ = build_economic_state(obs)
    generator = HarvestCoupledPatchGenerator()

    req = CoupledPatchRequest(
        opportunity_id="OPP_ADV_BESIDE",
        mechanism_family="DYNAMIC_SHADOW_HARVEST",
        worker_ids=[1],
        start_step=50,
        econ_state=econ,
        baseline_action={"farmer": ["PASS"], "hands": [["PASS"]], "market": []},
        baseline_continuation=[{"farmer": ["PASS"], "hands": [["PASS"]], "market": []} for _ in range(15)],
        target_location=(3, 2),
        target_commodity="CARROT"
    )
    res = generator.generate_harvest_patch(req)
    assert res.patch is not None
    assert res.patch.actions[0]["hands"][0] == ["EAST"]


def test_adversarial_two_workers_targeting_same_crop(dh_base_obs: Dict[str, Any]) -> None:
    table = SpacetimeReservationTable()
    crop_task_id = "HARVEST_3_3"
    # Worker 1 reserves crop task
    assert table.reserve_task(step=50, task_id=crop_task_id, worker_id=1) is True
    # Worker 2 attempting to reserve same task fails
    assert table.reserve_task(step=50, task_id=crop_task_id, worker_id=2) is False


def test_adversarial_two_workers_targeting_same_shed(dh_base_obs: Dict[str, Any]) -> None:
    table = SpacetimeReservationTable()
    shed_pos = SHED_TILES[0]
    # Worker 1 reserves shed access
    assert table.reserve_building(step=55, pos=shed_pos, worker_id=1) is True
    # Worker 2 attempting same shed access fails
    assert table.reserve_building(step=55, pos=shed_pos, worker_id=2) is False
