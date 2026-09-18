# SPDX-License-Identifier: MIT
"""AEC Phase 006: Dedicated Coupled Patch Tests (CP-01 through CP-15).

Tests the formal CoupledPatch abstraction, trajectory-preservation contract,
reconnection compiler, and state machine transitions (§24).
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
    PatchPrecondition,
    PatchPostcondition,
    PatchStateDelta,
    TrajectoryPreservationCertificate,
)
from aec.patches.coupled_patch_engine import CoupledPatchEngine
from aec.patches.harvest_patch import HarvestCoupledPatchGenerator
from aec.replanning.reconnect import SpacetimeReservationTable, manhattan


@pytest.fixture
def cp_base_obs(normal_opening_obs: Dict[str, Any]) -> Dict[str, Any]:
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
# CP-01: Idle worker -> nearby crop -> harvest -> deposit -> reconnect
# =========================================================================
def test_cp01_idle_worker_harvest_deposit_reconnect(cp_base_obs: Dict[str, Any]) -> None:
    obs = copy.deepcopy(cp_base_obs)
    # Mature CARROT at (2, 3), 1 step south of Hand 1 at (2, 2)
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
        opportunity_id="OPP_CP01",
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
    patch = res.patch

    # Verify multi-phase spliced actions exist
    assert len(patch.actions) >= 4  # MOVE -> HARVEST -> MOVE -> DROP
    assert patch.precondition is not None
    assert patch.precondition.is_met is True
    assert patch.postcondition is not None
    assert patch.postcondition.is_satisfied is True
    assert patch.preservation_certificate is not None
    assert patch.preservation_certificate.is_valid is True
    assert patch.preservation_certificate.cargo_state_consistent is True
    assert patch.preservation_certificate.worker_positions_aligned is True


# =========================================================================
# CP-02: Idle worker -> distant crop -> route planning
# =========================================================================
def test_cp02_idle_worker_distant_crop_routing(cp_base_obs: Dict[str, Any]) -> None:
    obs = copy.deepcopy(cp_base_obs)
    # Crop at (0, 0), Hand 1 at (4, 4)
    obs["farms"][0]["hands"] = [[4, 4]]
    obs["farms"][0]["tiles"][0][0] = {
        "kind": "PLANT",
        "crop": "CARROT",
        "yield_units": 2,
        "planted_day": 0,
        "watered_today": True
    }
    econ = build_economic_state(obs)
    generator = HarvestCoupledPatchGenerator()

    req = CoupledPatchRequest(
        opportunity_id="OPP_CP02",
        mechanism_family="DYNAMIC_SHADOW_HARVEST",
        worker_ids=[1],
        start_step=50,
        econ_state=econ,
        baseline_action={"farmer": ["PASS"], "hands": [["PASS"]], "market": []},
        baseline_continuation=[{"farmer": ["PASS"], "hands": [["PASS"]], "market": []} for _ in range(25)],
        target_location=(0, 0),
        target_commodity="CARROT",
        horizon=25
    )

    res = generator.generate_harvest_patch(req)
    assert res.patch is not None
    # Distance from (4,4) to (0,0) is 8 moves
    assert res.patch.route_cost >= 8


# =========================================================================
# CP-03: Harvest with existing cargo -> safely resolved or fail-closed
# =========================================================================
def test_cp03_harvest_with_existing_cargo(cp_base_obs: Dict[str, Any]) -> None:
    obs = copy.deepcopy(cp_base_obs)
    # Hand 1 already has 2 WHEAT
    obs["private"]["inventories"][1] = {"WHEAT": 2}
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
        opportunity_id="OPP_CP03",
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
    # After DROP, worker cargo is completely cleared to empty, ensuring no lingering cargo
    assert res.patch.cargo_after[1] == {}
    assert res.patch.postcondition.worker_cargo[1] == {}


# =========================================================================
# CP-04: Harvest with insufficient cargo capacity -> no commit
# =========================================================================
def test_cp04_harvest_insufficient_shed_capacity(cp_base_obs: Dict[str, Any]) -> None:
    obs = copy.deepcopy(cp_base_obs)
    # Fill shed to capacity 200
    obs["private"]["shed"] = {"WHEAT": SHED_CAPACITY}
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
        opportunity_id="OPP_CP04",
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
    # Must reject due to full shed
    assert res.status == CoupledPatchState.CARGO_UNRESOLVED.value
    assert not res.is_accepted


# =========================================================================
# CP-05: Harvest causes baseline route desynchronization -> reject if no reconnect
# =========================================================================
def test_cp05_harvest_without_reconnect_rejected(cp_base_obs: Dict[str, Any]) -> None:
    obs = copy.deepcopy(cp_base_obs)
    obs["farms"][0]["tiles"][2][2] = {
        "kind": "PLANT",
        "crop": "CARROT",
        "yield_units": 2,
        "planted_day": 0,
        "watered_today": True
    }
    econ = build_economic_state(obs)
    generator = HarvestCoupledPatchGenerator()

    # Pass an empty baseline continuation where reconnect is impossible
    req = CoupledPatchRequest(
        opportunity_id="OPP_CP05",
        mechanism_family="DYNAMIC_SHADOW_HARVEST",
        worker_ids=[1],
        start_step=50,
        econ_state=econ,
        baseline_action={"farmer": ["PASS"], "hands": [["PASS"]], "market": []},
        baseline_continuation=[],  # Empty continuation in mid-game
        target_location=(2, 2),
        target_commodity="CARROT",
        is_terminal_sweep=False
    )

    res = generator.generate_harvest_patch(req)
    assert res.status == CoupledPatchState.RECONNECT_FAILURE.value


# =========================================================================
# CP-06: Complete coupled patch vs one-turn harvest
# =========================================================================
def test_cp06_coupled_patch_preserves_trajectory_over_one_turn(cp_base_obs: Dict[str, Any]) -> None:
    obs = copy.deepcopy(cp_base_obs)
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
        opportunity_id="OPP_CP06",
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
    # 1-turn patch would leave cargo in worker inventory
    # Coupled patch drops cargo in shed and reconnects
    assert res.patch.cargo_after[1] == {}
    assert res.patch.preservation_certificate.cargo_state_consistent is True
    assert res.patch.preservation_certificate.worker_positions_aligned is True


# =========================================================================
# CP-07: Busy worker with profitable baseline -> labor opportunity cost considered
# =========================================================================
def test_cp07_busy_worker_profitable_baseline_labor_cost(cp_base_obs: Dict[str, Any]) -> None:
    obs = copy.deepcopy(cp_base_obs)
    obs["farms"][0]["tiles"][2][2] = {
        "kind": "PLANT",
        "crop": "CARROT",
        "yield_units": 2,
        "planted_day": 0,
        "watered_today": True
    }
    econ = build_economic_state(obs)
    generator = HarvestCoupledPatchGenerator()

    # Hand 1 baseline is HARVESTING another crop at (2, 2)
    req = CoupledPatchRequest(
        opportunity_id="OPP_CP07",
        mechanism_family="DYNAMIC_SHADOW_HARVEST",
        worker_ids=[1],
        start_step=50,
        econ_state=econ,
        baseline_action={"farmer": ["PASS"], "hands": [["HARVEST"]], "market": []},
        baseline_continuation=[{"farmer": ["PASS"], "hands": [["PASS"]], "market": []} for _ in range(15)],
        target_location=(2, 2),
        target_commodity="CARROT"
    )

    res = generator.generate_harvest_patch(req)
    # Labor opportunity cost should be accounted for
    assert res.labor_opportunity_cost >= 0.0


# =========================================================================
# CP-08: Busy worker where harvest is economically superior
# =========================================================================
def test_cp08_busy_worker_economically_superior_harvest(cp_base_obs: Dict[str, Any]) -> None:
    obs = copy.deepcopy(cp_base_obs)
    # Strawberry requires day - planted_day >= 10. At step 288, day = 12.
    obs["step"] = 288
    obs["day"] = 12
    obs["farms"][0]["tiles"][2][2] = {
        "kind": "PLANT",
        "crop": "STRAWBERRY",
        "yield_units": 3,
        "planted_day": 0,
        "watered_today": True
    }
    econ = build_economic_state(obs)
    generator = HarvestCoupledPatchGenerator()

    req = CoupledPatchRequest(
        opportunity_id="OPP_CP08",
        mechanism_family="DYNAMIC_SHADOW_HARVEST",
        worker_ids=[1],
        start_step=288,
        econ_state=econ,
        baseline_action={"farmer": ["PASS"], "hands": [["PASS"]], "market": []},
        baseline_continuation=[{"farmer": ["PASS"], "hands": [["PASS"]], "market": []} for _ in range(15)],
        target_location=(2, 2),
        target_commodity="STRAWBERRY"
    )

    res = generator.generate_harvest_patch(req)
    assert res.patch is not None
    assert res.exact_delta > 0.0
    assert res.is_accepted


# =========================================================================
# CP-09: Peer absorption -> Hand 2 absorbs baseline obligation
# =========================================================================
def test_cp09_peer_absorption_coordination(cp_base_obs: Dict[str, Any]) -> None:
    obs = copy.deepcopy(cp_base_obs)
    # Add Hand 2
    obs["farms"][0]["hands"].append([2, 3])
    obs["farms"][0]["hires_today"] = 2
    obs["private"]["inventories"].append({})
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
        opportunity_id="OPP_CP09",
        mechanism_family="DYNAMIC_SHADOW_HARVEST",
        worker_ids=[1],
        start_step=50,
        econ_state=econ,
        baseline_action={"farmer": ["PASS"], "hands": [["PASS"], ["PASS"]], "market": []},
        baseline_continuation=[{"farmer": ["PASS"], "hands": [["PASS"], ["PASS"]], "market": []} for _ in range(15)],
        target_location=(2, 2),
        target_commodity="CARROT",
        co_worker_trajectories={2: [(2, 3) for _ in range(15)]}
    )

    res = generator.generate_harvest_patch(req)
    assert res.patch is not None
    assert res.trajectory_certificate.multiworker_collision_free is True


# =========================================================================
# CP-10: Multi-worker collision -> expected rejection
# =========================================================================
def test_cp10_multiworker_collision_rejected(cp_base_obs: Dict[str, Any]) -> None:
    table = SpacetimeReservationTable()
    # Worker 2 already reserved cell (2, 3) at step 51
    assert table.reserve_vertex(51, (2, 3), worker_id=2) is True
    # Worker 1 attempting to occupy same vertex must fail
    assert table.reserve_vertex(51, (2, 3), worker_id=1) is False


# =========================================================================
# CP-11: Shed contention -> expected safe sequencing or rejection
# =========================================================================
def test_cp11_shed_contention_reservation(cp_base_obs: Dict[str, Any]) -> None:
    table = SpacetimeReservationTable()
    shed_tile = SHED_TILES[0]
    assert table.reserve_building(55, shed_tile, worker_id=0) is True
    # Hand 1 attempting same shed building access at same step must fail
    assert table.reserve_building(55, shed_tile, worker_id=1) is False


# =========================================================================
# CP-12: Terminal harvest step 717 -> validates exact terminal completion
# =========================================================================
def test_cp12_terminal_harvest_step_717(cp_base_obs: Dict[str, Any]) -> None:
    obs = copy.deepcopy(cp_base_obs)
    obs["step"] = 717
    obs["day"] = 29
    obs["hour"] = 21
    # Hand 1 standing adjacent to shed at (5, 5)
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
        opportunity_id="OPP_CP12",
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
    # Harvest at 717, drop at 718 (both <= 718)
    assert res.patch.end_step <= 718
    assert res.exact_delta > 0.0


# =========================================================================
# CP-13: Terminal harvest step 718 -> deposit must complete before 719
# =========================================================================
def test_cp13_terminal_harvest_step_718_boundary(cp_base_obs: Dict[str, Any]) -> None:
    obs = copy.deepcopy(cp_base_obs)
    obs["step"] = 718
    obs["day"] = 29
    obs["hour"] = 22
    # Hand 1 is at (1, 1), 6 steps from shed
    obs["farms"][0]["hands"] = [[1, 1]]
    obs["farms"][0]["tiles"][1][1] = {
        "kind": "PLANT",
        "crop": "CARROT",
        "yield_units": 2,
        "planted_day": 0,
        "watered_today": True
    }
    econ = build_economic_state(obs)
    generator = HarvestCoupledPatchGenerator()

    req = CoupledPatchRequest(
        opportunity_id="OPP_CP13",
        mechanism_family="TERMINAL_HARVEST_SWEEP",
        worker_ids=[1],
        start_step=718,
        econ_state=econ,
        baseline_action={"farmer": ["PASS"], "hands": [["PASS"]], "market": []},
        baseline_continuation=[],
        target_location=(1, 1),
        target_commodity="CARROT",
        is_terminal_sweep=True
    )

    res = generator.generate_harvest_patch(req)
    # At step 718 with distant shed, deposit would happen at step > 718 -> TERMINAL_RISK rejection
    assert res.status == CoupledPatchState.TERMINAL_RISK.value


# =========================================================================
# CP-14: Terminal harvest step 719 -> episode already closed
# =========================================================================
def test_cp14_terminal_harvest_step_719_past_boundary(cp_base_obs: Dict[str, Any]) -> None:
    obs = copy.deepcopy(cp_base_obs)
    obs["step"] = 719
    obs["day"] = 29
    obs["farms"][0]["tiles"][7][7] = {
        "kind": "PLANT",
        "crop": "CARROT",
        "yield_units": 2,
        "planted_day": 0,
        "watered_today": True
    }
    econ = build_economic_state(obs)
    generator = HarvestCoupledPatchGenerator()

    req = CoupledPatchRequest(
        opportunity_id="OPP_CP14",
        mechanism_family="TERMINAL_HARVEST_SWEEP",
        worker_ids=[1],
        start_step=719,
        econ_state=econ,
        baseline_action={"farmer": ["PASS"], "hands": [["PASS"]], "market": []},
        baseline_continuation=[],
        target_location=(7, 7),
        target_commodity="CARROT",
        is_terminal_sweep=True
    )

    res = generator.generate_harvest_patch(req)
    assert res.status == CoupledPatchState.TERMINAL_RISK.value


# =========================================================================
# CP-15: Harvest without deposit before terminal -> correct economic rejection
# =========================================================================
def test_cp15_harvest_without_deposit_rejected(cp_base_obs: Dict[str, Any]) -> None:
    obs = copy.deepcopy(cp_base_obs)
    obs["step"] = 717
    # Hand at (0, 0), shed at (7, 7) (needs 14 steps)
    obs["farms"][0]["hands"] = [[0, 0]]
    obs["farms"][0]["tiles"][0][0] = {
        "kind": "PLANT",
        "crop": "CARROT",
        "yield_units": 2,
        "planted_day": 0,
        "watered_today": True
    }
    econ = build_economic_state(obs)
    generator = HarvestCoupledPatchGenerator()

    req = CoupledPatchRequest(
        opportunity_id="OPP_CP15",
        mechanism_family="TERMINAL_HARVEST_SWEEP",
        worker_ids=[1],
        start_step=717,
        econ_state=econ,
        baseline_action={"farmer": ["PASS"], "hands": [["PASS"]], "market": []},
        baseline_continuation=[],
        target_location=(0, 0),
        target_commodity="CARROT",
        is_terminal_sweep=True
    )

    res = generator.generate_harvest_patch(req)
    assert res.status == CoupledPatchState.TERMINAL_RISK.value
    assert not res.is_accepted
