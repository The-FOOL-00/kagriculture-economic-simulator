# SPDX-License-Identifier: MIT
"""Phase 011 Group 1 Mechanism Rescue Micro-Validation Matrix (§12).

Adversarial synthetic states and activation patterns for:
1. DYNAMIC_SHADOW_HARVEST (10+ patterns)
2. TERMINAL_HARVEST_SWEEP (10+ patterns)
3. ROUTE_COMPRESSION (10+ patterns)
4. CARGO_FERRY (10+ patterns)
"""

from __future__ import annotations

import copy
import pytest
from typing import Any, Dict, List, Tuple

from aec.config import BOARD_SIZE, SHED_CAPACITY, SHED_TILES
from aec.ir.economic_state import build_economic_state
from aec.opportunities.labor import LaborOpportunityAnalyzer
from aec.patches.coupled_patch import (
    CoupledPatch,
    CoupledPatchRequest,
    CoupledPatchResult,
    CoupledPatchState,
)
from aec.patches.harvest_patch import HarvestCoupledPatchGenerator
from aec.replanning.reconnect import SpacetimeReservationTable, extract_all_worker_trajectories


@pytest.fixture
def matrix_base_obs(normal_opening_obs: Dict[str, Any]) -> Dict[str, Any]:
    """Base observation with 1 Farmer at [4, 4] and 1 Hand at [2, 2]."""
    obs = copy.deepcopy(normal_opening_obs)
    obs["step"] = 50
    obs["day"] = 2
    obs["hour"] = 2
    obs["farms"][0]["farmer"] = [4, 4]
    obs["farms"][0]["hands"] = [[2, 2]]
    obs["farms"][0]["hires_today"] = 1
    obs["farms"][0]["cash"] = 250
    obs["farms"][0]["shed"] = {}
    obs["private"]["inventories"] = [{}, {}]
    return obs


# =============================================================================
# 1. DYNAMIC SHADOW HARVEST: 10+ ACTIVATION & ADVERSARIAL PATTERNS (§4, §12)
# =============================================================================

def test_dh_01_crop_adjacent_to_worker(matrix_base_obs: Dict[str, Any]) -> None:
    """DH-01: Crop immediately adjacent to worker -> fast harvest, immediate delivery."""
    obs = copy.deepcopy(matrix_base_obs)
    # Hand at (2, 2), crop at (2, 3) -> tiles[y=3][x=2]
    obs["farms"][0]["tiles"][3][2] = {
        "kind": "PLANT",
        "crop": "CARROT",
        "yield_units": 3,
        "planted_day": 0,
        "watered_today": True,
    }
    econ = build_economic_state(obs)
    gen = HarvestCoupledPatchGenerator()

    req = CoupledPatchRequest(
        opportunity_id="OPP_DH_01",
        mechanism_family="DYNAMIC_SHADOW_HARVEST",
        worker_ids=[1],
        start_step=50,
        econ_state=econ,
        baseline_action={"farmer": ["PASS"], "hands": [["PASS"]], "market": []},
        baseline_continuation=[{"farmer": ["PASS"], "hands": [["PASS"]], "market": []} for _ in range(15)],
        target_location=(2, 3),
        target_commodity="CARROT",
    )
    res = gen.generate_harvest_patch(req)
    assert res.status == "ACCEPTED"
    assert res.patch is not None
    assert res.patch.actions[0]["hands"][0] == ["SOUTH"]


def test_dh_02_crop_moderately_distant(matrix_base_obs: Dict[str, Any]) -> None:
    """DH-02: Crop moderately distant (d=4) -> valid route generated and reconnect preserved."""
    obs = copy.deepcopy(matrix_base_obs)
    # Hand at (2, 2), crop at (4, 4) -> tiles[y=4][x=4]
    obs["farms"][0]["tiles"][4][4] = {
        "kind": "PLANT",
        "crop": "CARROT",
        "yield_units": 3,
        "planted_day": 0,
        "watered_today": True,
    }
    econ = build_economic_state(obs)
    gen = HarvestCoupledPatchGenerator()

    req = CoupledPatchRequest(
        opportunity_id="OPP_DH_02",
        mechanism_family="DYNAMIC_SHADOW_HARVEST",
        worker_ids=[1],
        start_step=50,
        econ_state=econ,
        baseline_action={"farmer": ["PASS"], "hands": [["PASS"]], "market": []},
        baseline_continuation=[{"farmer": ["PASS"], "hands": [["PASS"]], "market": []} for _ in range(20)],
        target_location=(4, 4),
        target_commodity="CARROT",
    )
    res = gen.generate_harvest_patch(req)
    assert res.patch is not None
    assert res.patch.route_cost > 2


def test_dh_03_crop_requiring_shed_delivery(matrix_base_obs: Dict[str, Any]) -> None:
    """DH-03: Full lifecycle route to crop -> harvest -> route to shed -> DROP verified."""
    obs = copy.deepcopy(matrix_base_obs)
    # Hand at (2, 2), crop at (2, 3) -> tiles[3][2]
    obs["farms"][0]["tiles"][3][2] = {
        "kind": "PLANT",
        "crop": "CARROT",
        "yield_units": 2,
        "planted_day": 0,
        "watered_today": True,
    }
    econ = build_economic_state(obs)
    gen = HarvestCoupledPatchGenerator()

    req = CoupledPatchRequest(
        opportunity_id="OPP_DH_03",
        mechanism_family="DYNAMIC_SHADOW_HARVEST",
        worker_ids=[1],
        start_step=50,
        econ_state=econ,
        baseline_action={"farmer": ["PASS"], "hands": [["PASS"]], "market": []},
        baseline_continuation=[{"farmer": ["PASS"], "hands": [["PASS"]], "market": []} for _ in range(20)],
        target_location=(2, 3),
        target_commodity="CARROT",
    )
    res = gen.generate_harvest_patch(req)
    assert res.patch is not None
    all_cmds = [a["hands"][0][0] for a in res.patch.actions]
    assert "HARVEST" in all_cmds
    assert "DROP" in all_cmds


def test_dh_04_multiple_nearby_mature_crops_cluster(matrix_base_obs: Dict[str, Any]) -> None:
    """DH-04: Cluster harvest sweeps multiple adjacent mature crops before heading to shed."""
    obs = copy.deepcopy(matrix_base_obs)
    # Hand at (2, 2). Mature crops at (2, 3) -> tiles[3][2] and (2, 4) -> tiles[4][2]
    obs["farms"][0]["tiles"][3][2] = {
        "kind": "PLANT",
        "crop": "CARROT",
        "yield_units": 2,
        "planted_day": 0,
        "watered_today": True,
    }
    obs["farms"][0]["tiles"][4][2] = {
        "kind": "PLANT",
        "crop": "CARROT",
        "yield_units": 2,
        "planted_day": 0,
        "watered_today": True,
    }
    econ = build_economic_state(obs)
    gen = HarvestCoupledPatchGenerator()

    req = CoupledPatchRequest(
        opportunity_id="OPP_DH_04",
        mechanism_family="DYNAMIC_SHADOW_HARVEST",
        worker_ids=[1],
        start_step=50,
        econ_state=econ,
        baseline_action={"farmer": ["PASS"], "hands": [["PASS"]], "market": []},
        baseline_continuation=[{"farmer": ["PASS"], "hands": [["PASS"]], "market": []} for _ in range(25)],
        target_location=(2, 3),
        target_commodity="CARROT",
    )
    res = gen.generate_harvest_patch(req)
    assert res.patch is not None
    # Verify multiple crops harvested
    all_cmds = [a["hands"][0][0] for a in res.patch.actions]
    harvest_count = all_cmds.count("HARVEST")
    assert harvest_count >= 2


def test_dh_05_negative_control_immature_crop(matrix_base_obs: Dict[str, Any]) -> None:
    """DH-05: Negative Control: crop not yet mature -> detector/patch generator abstains."""
    obs = copy.deepcopy(matrix_base_obs)
    obs["farms"][0]["tiles"][3][2] = {
        "kind": "PLANT",
        "crop": "CARROT",
        "yield_units": 0,
        "planted_day": 2,  # planted today, not mature
        "watered_today": True,
    }
    econ = build_economic_state(obs)
    gen = HarvestCoupledPatchGenerator()

    req = CoupledPatchRequest(
        opportunity_id="OPP_DH_05",
        mechanism_family="DYNAMIC_SHADOW_HARVEST",
        worker_ids=[1],
        start_step=50,
        econ_state=econ,
        baseline_action={"farmer": ["PASS"], "hands": [["PASS"]], "market": []},
        baseline_continuation=[{"farmer": ["PASS"], "hands": [["PASS"]], "market": []} for _ in range(15)],
        target_location=(2, 3),
        target_commodity="CARROT",
    )
    res = gen.generate_harvest_patch(req)
    assert res.status == CoupledPatchState.INFEASIBLE.value


def test_dh_06_negative_control_shed_full(matrix_base_obs: Dict[str, Any]) -> None:
    """DH-06: Negative Control: shed capacity exhausted -> rejected fail-closed."""
    obs = copy.deepcopy(matrix_base_obs)
    obs["private"]["shed"] = {"CARROT": SHED_CAPACITY}  # completely full
    obs["farms"][0]["tiles"][3][2] = {
        "kind": "PLANT",
        "crop": "CARROT",
        "yield_units": 3,
        "planted_day": 0,
        "watered_today": True,
    }
    econ = build_economic_state(obs)
    gen = HarvestCoupledPatchGenerator()

    req = CoupledPatchRequest(
        opportunity_id="OPP_DH_06",
        mechanism_family="DYNAMIC_SHADOW_HARVEST",
        worker_ids=[1],
        start_step=50,
        econ_state=econ,
        baseline_action={"farmer": ["PASS"], "hands": [["PASS"]], "market": []},
        baseline_continuation=[{"farmer": ["PASS"], "hands": [["PASS"]], "market": []} for _ in range(15)],
        target_location=(2, 3),
        target_commodity="CARROT",
    )
    res = gen.generate_harvest_patch(req)
    assert res.status in (CoupledPatchState.CARGO_UNRESOLVED.value, CoupledPatchState.INFEASIBLE.value)
    assert "shed" in res.rejection_reason.lower()


def test_dh_07_worker_currently_idle(matrix_base_obs: Dict[str, Any]) -> None:
    """DH-07: Idle worker with 0 opportunity cost readily commits to harvest."""
    obs = copy.deepcopy(matrix_base_obs)
    obs["farms"][0]["tiles"][3][2] = {
        "kind": "PLANT",
        "crop": "CARROT",
        "yield_units": 3,
        "planted_day": 0,
        "watered_today": True,
    }
    econ = build_economic_state(obs)
    gen = HarvestCoupledPatchGenerator()

    req = CoupledPatchRequest(
        opportunity_id="OPP_DH_07",
        mechanism_family="DYNAMIC_SHADOW_HARVEST",
        worker_ids=[1],
        start_step=50,
        econ_state=econ,
        baseline_action={"farmer": ["PASS"], "hands": [["PASS"]], "market": []},
        baseline_continuation=[{"farmer": ["PASS"], "hands": [["PASS"]], "market": []} for _ in range(15)],
        target_location=(2, 3),
        target_commodity="CARROT",
    )
    res = gen.generate_harvest_patch(req)
    assert res.status == "ACCEPTED"
    assert res.patch is not None
    assert res.patch.economic_effect > 0


def test_dh_08_reconnect_exactness_with_coworker_trajectories(matrix_base_obs: Dict[str, Any]) -> None:
    """DH-08: Reconnect rendezvous matches exact co-worker baseline position at turn k."""
    obs = copy.deepcopy(matrix_base_obs)
    obs["farms"][0]["tiles"][3][2] = {
        "kind": "PLANT",
        "crop": "CARROT",
        "yield_units": 2,
        "planted_day": 0,
        "watered_today": True,
    }
    econ = build_economic_state(obs)
    gen = HarvestCoupledPatchGenerator()

    # Hand at (2, 2) baseline is moving EAST then SOUTH
    baseline_actions = [
        {"farmer": ["PASS"], "hands": [["EAST"]], "market": []},
        {"farmer": ["PASS"], "hands": [["SOUTH"]], "market": []},
        {"farmer": ["PASS"], "hands": [["SOUTH"]], "market": []},
        {"farmer": ["PASS"], "hands": [["PASS"]], "market": []},
        {"farmer": ["PASS"], "hands": [["PASS"]], "market": []},
        {"farmer": ["PASS"], "hands": [["PASS"]], "market": []},
        {"farmer": ["PASS"], "hands": [["PASS"]], "market": []},
        {"farmer": ["PASS"], "hands": [["PASS"]], "market": []},
        {"farmer": ["PASS"], "hands": [["PASS"]], "market": []},
        {"farmer": ["PASS"], "hands": [["PASS"]], "market": []},
        {"farmer": ["PASS"], "hands": [["PASS"]], "market": []},
        {"farmer": ["PASS"], "hands": [["PASS"]], "market": []},
    ]

    co_worker_trajs = extract_all_worker_trajectories(econ, baseline_actions)

    req = CoupledPatchRequest(
        opportunity_id="OPP_DH_08",
        mechanism_family="DYNAMIC_SHADOW_HARVEST",
        worker_ids=[1],
        start_step=50,
        econ_state=econ,
        baseline_action=baseline_actions[0],
        baseline_continuation=baseline_actions[1:],
        co_worker_trajectories=co_worker_trajs,
        target_location=(2, 3),
        target_commodity="CARROT",
    )
    res = gen.generate_harvest_patch(req)
    assert res.patch is not None
    assert res.patch.reconnect_result is not None
    assert res.patch.reconnect_result.safety is True


def test_dh_09_market_timing_immediate_liquidation(matrix_base_obs: Dict[str, Any]) -> None:
    """DH-09: Patch automatically injects SELL order on DROP step for liquidity realization."""
    obs = copy.deepcopy(matrix_base_obs)
    obs["farms"][0]["tiles"][3][2] = {
        "kind": "PLANT",
        "crop": "CARROT",
        "yield_units": 3,
        "planted_day": 0,
        "watered_today": True,
    }
    econ = build_economic_state(obs)
    gen = HarvestCoupledPatchGenerator()

    req = CoupledPatchRequest(
        opportunity_id="OPP_DH_09",
        mechanism_family="DYNAMIC_SHADOW_HARVEST",
        worker_ids=[1],
        start_step=50,
        econ_state=econ,
        baseline_action={"farmer": ["PASS"], "hands": [["PASS"]], "market": []},
        baseline_continuation=[{"farmer": ["PASS"], "hands": [["PASS"]], "market": []} for _ in range(15)],
        target_location=(2, 3),
        target_commodity="CARROT",
    )
    res = gen.generate_harvest_patch(req)
    assert res.patch is not None
    # Find step with DROP
    drop_steps = [a for a in res.patch.actions if a["hands"][0][0] == "DROP"]
    assert len(drop_steps) == 1
    mkt = drop_steps[0].get("market", [])
    sell_orders = [o for o in mkt if o[0] == "SELL" and o[1] == "CARROT"]
    assert len(sell_orders) >= 1


def test_dh_10_adversarial_two_workers_targeting_same_tile(matrix_base_obs: Dict[str, Any]) -> None:
    """DH-10: Adversarial: Spacetime reservation prevents second worker from targeting reserved crop."""
    table = SpacetimeReservationTable()
    crop_pos = (2, 3)
    assert table.reserve_vertex(step=52, pos=crop_pos, worker_id=0) is True
    # Worker 1 trying to step into same cell at step 52 is blocked
    assert table.reserve_vertex(step=52, pos=crop_pos, worker_id=1) is False


# =============================================================================
# 2. TERMINAL HARVEST SWEEP: 10+ ACTIVATION & ADVERSARIAL PATTERNS (§5, §12)
# =============================================================================

def test_th_01_feasible_sweep_near_terminal(matrix_base_obs: Dict[str, Any]) -> None:
    """TH-01: At step 700, mature crop within 5 turns of shed is successfully swept."""
    obs = copy.deepcopy(matrix_base_obs)
    obs["step"] = 700
    obs["day"] = 29
    obs["hour"] = 4
    # Hand at (2, 2). Crop at (2, 3) -> tiles[3][2]
    obs["farms"][0]["tiles"][3][2] = {
        "kind": "PLANT",
        "crop": "CARROT",
        "yield_units": 3,
        "planted_day": 20,
        "watered_today": True,
    }
    econ = build_economic_state(obs)
    gen = HarvestCoupledPatchGenerator()

    req = CoupledPatchRequest(
        opportunity_id="OPP_TH_01",
        mechanism_family="TERMINAL_HARVEST_SWEEP",
        worker_ids=[1],
        start_step=700,
        econ_state=econ,
        baseline_action={"farmer": ["PASS"], "hands": [["PASS"]], "market": []},
        baseline_continuation=[{"farmer": ["PASS"], "hands": [["PASS"]], "market": []} for _ in range(18)],
        target_location=(2, 3),
        target_commodity="CARROT",
        is_terminal_sweep=True,
    )
    res = gen.generate_harvest_patch(req)
    assert res.status == "ACCEPTED"
    assert res.patch is not None
    assert res.exact_delta > 0.0


def test_th_02_stranded_cargo_salvage(matrix_base_obs: Dict[str, Any]) -> None:
    """TH-02: At step 710, worker carries stranded cargo -> direct DELIVER->SELL patch created."""
    obs = copy.deepcopy(matrix_base_obs)
    obs["step"] = 710
    obs["day"] = 29
    obs["hour"] = 14
    # Hand at (2, 2) carries 5 CARROT in cargo
    obs["private"]["inventories"][1] = {"CARROT": 5}
    econ = build_economic_state(obs)
    gen = HarvestCoupledPatchGenerator()

    req = CoupledPatchRequest(
        opportunity_id="OPP_TH_02",
        mechanism_family="TERMINAL_HARVEST_SWEEP",
        worker_ids=[1],
        start_step=710,
        econ_state=econ,
        baseline_action={"farmer": ["PASS"], "hands": [["PASS"]], "market": []},
        baseline_continuation=[{"farmer": ["PASS"], "hands": [["PASS"]], "market": []} for _ in range(8)],
        target_location=(2, 2),  # worker's own location
        target_commodity="CARROT",
        is_terminal_sweep=True,
    )
    res = gen.generate_harvest_patch(req)
    assert res.patch is not None
    all_cmds = [a["hands"][0][0] for a in res.patch.actions]
    assert "DROP" in all_cmds
    assert "HARVEST" not in all_cmds  # purely salvage cargo!


def test_th_03_runway_exceeded_hard_rejection(matrix_base_obs: Dict[str, Any]) -> None:
    """TH-03: At step 715 (runway=3), crop requires 8 turns -> hard TERMINAL_RISK rejection."""
    obs = copy.deepcopy(matrix_base_obs)
    obs["step"] = 715
    obs["day"] = 29
    obs["hour"] = 19
    # Hand at (0, 0), crop at (9, 9) -> distance 18 > 3 turns remaining
    obs["farms"][0]["hands"] = [[0, 0]]
    obs["farms"][0]["tiles"][9][9] = {
        "kind": "PLANT",
        "crop": "CARROT",
        "yield_units": 3,
        "planted_day": 20,
        "watered_today": True,
    }
    econ = build_economic_state(obs)
    gen = HarvestCoupledPatchGenerator()

    req = CoupledPatchRequest(
        opportunity_id="OPP_TH_03",
        mechanism_family="TERMINAL_HARVEST_SWEEP",
        worker_ids=[1],
        start_step=715,
        econ_state=econ,
        baseline_action={"farmer": ["PASS"], "hands": [["PASS"]], "market": []},
        baseline_continuation=[{"farmer": ["PASS"], "hands": [["PASS"]], "market": []} for _ in range(3)],
        target_location=(9, 9),
        target_commodity="CARROT",
        is_terminal_sweep=True,
    )
    res = gen.generate_harvest_patch(req)
    assert res.status in (CoupledPatchState.TERMINAL_RISK.value, CoupledPatchState.ROUTE_FAILURE.value)


def test_th_04_terminal_cluster_sweep(matrix_base_obs: Dict[str, Any]) -> None:
    """TH-04: At step 698, adjacent mature crops swept together before single deposit."""
    obs = copy.deepcopy(matrix_base_obs)
    obs["step"] = 698
    obs["day"] = 29
    obs["hour"] = 2
    # Hand at (2, 2). Mature crops at (2, 3) and (2, 4)
    obs["farms"][0]["tiles"][3][2] = {
        "kind": "PLANT",
        "crop": "CARROT",
        "yield_units": 2,
        "planted_day": 20,
        "watered_today": True,
    }
    obs["farms"][0]["tiles"][4][2] = {
        "kind": "PLANT",
        "crop": "CARROT",
        "yield_units": 2,
        "planted_day": 20,
        "watered_today": True,
    }
    econ = build_economic_state(obs)
    gen = HarvestCoupledPatchGenerator()

    req = CoupledPatchRequest(
        opportunity_id="OPP_TH_04",
        mechanism_family="TERMINAL_HARVEST_SWEEP",
        worker_ids=[1],
        start_step=698,
        econ_state=econ,
        baseline_action={"farmer": ["PASS"], "hands": [["PASS"]], "market": []},
        baseline_continuation=[{"farmer": ["PASS"], "hands": [["PASS"]], "market": []} for _ in range(20)],
        target_location=(2, 3),
        target_commodity="CARROT",
        is_terminal_sweep=True,
    )
    res = gen.generate_harvest_patch(req)
    assert res.patch is not None
    cmds = [a["hands"][0][0] for a in res.patch.actions]
    assert cmds.count("HARVEST") >= 1
    assert "DROP" in cmds


def test_th_05_terminal_opportunity_analyzer_detection(matrix_base_obs: Dict[str, Any]) -> None:
    """TH-05: TerminalOpportunityAnalyzer detects both stranded cargo and feasible crops."""
    from aec.opportunities.terminal import TerminalOpportunityAnalyzer
    obs = copy.deepcopy(matrix_base_obs)
    obs["step"] = 700
    obs["day"] = 29
    obs["hour"] = 4
    # Worker 1 has cargo
    obs["private"]["inventories"][1] = {"CARROT": 4}
    # Crop at (2, 3)
    obs["farms"][0]["tiles"][3][2] = {
        "kind": "PLANT",
        "crop": "CARROT",
        "yield_units": 3,
        "planted_day": 20,
        "watered_today": True,
    }
    econ = build_economic_state(obs)
    analyzer = TerminalOpportunityAnalyzer()
    opps = analyzer.analyze(econ, [])
    sweep_opps = [o for o in opps if o.candidate_transformation_family == "TERMINAL_HARVEST_SWEEP"]
    assert len(sweep_opps) >= 1
    # Check that cargo salvage was detected
    cargo_opps = [o for o in sweep_opps if o.dependency_info.get("is_cargo_deliver")]
    assert len(cargo_opps) >= 1


def test_th_06_negative_control_immature_crop_terminal(matrix_base_obs: Dict[str, Any]) -> None:
    """TH-06: Negative Control: Immature crop at step 705 cannot be harvested -> rejects."""
    obs = copy.deepcopy(matrix_base_obs)
    obs["step"] = 705
    obs["day"] = 29
    obs["hour"] = 9
    obs["farms"][0]["tiles"][3][2] = {
        "kind": "PLANT",
        "crop": "CARROT",
        "yield_units": 0,
        "planted_day": 29,  # planted today, immature
        "watered_today": True,
    }
    econ = build_economic_state(obs)
    gen = HarvestCoupledPatchGenerator()

    req = CoupledPatchRequest(
        opportunity_id="OPP_TH_06",
        mechanism_family="TERMINAL_HARVEST_SWEEP",
        worker_ids=[1],
        start_step=705,
        econ_state=econ,
        baseline_action={"farmer": ["PASS"], "hands": [["PASS"]], "market": []},
        baseline_continuation=[{"farmer": ["PASS"], "hands": [["PASS"]], "market": []} for _ in range(13)],
        target_location=(2, 3),
        target_commodity="CARROT",
        is_terminal_sweep=True,
    )
    res = gen.generate_harvest_patch(req)
    assert res.status == CoupledPatchState.INFEASIBLE.value


def test_th_07_negative_control_shed_full_terminal(matrix_base_obs: Dict[str, Any]) -> None:
    """TH-07: Negative Control: Shed is at 100 capacity -> cannot sweep new crop."""
    obs = copy.deepcopy(matrix_base_obs)
    obs["step"] = 705
    obs["private"]["shed"] = {"CARROT": 100}
    obs["farms"][0]["tiles"][3][2] = {
        "kind": "PLANT",
        "crop": "CARROT",
        "yield_units": 3,
        "planted_day": 20,
        "watered_today": True,
    }
    econ = build_economic_state(obs)
    gen = HarvestCoupledPatchGenerator()

    req = CoupledPatchRequest(
        opportunity_id="OPP_TH_07",
        mechanism_family="TERMINAL_HARVEST_SWEEP",
        worker_ids=[1],
        start_step=705,
        econ_state=econ,
        baseline_action={"farmer": ["PASS"], "hands": [["PASS"]], "market": []},
        baseline_continuation=[{"farmer": ["PASS"], "hands": [["PASS"]], "market": []} for _ in range(13)],
        target_location=(2, 3),
        target_commodity="CARROT",
        is_terminal_sweep=True,
    )
    res = gen.generate_harvest_patch(req)
    assert res.status in (CoupledPatchState.CARGO_UNRESOLVED.value, CoupledPatchState.INFEASIBLE.value)


def test_th_08_multiworker_terminal_no_collision(matrix_base_obs: Dict[str, Any]) -> None:
    """TH-08: Two workers execute independent terminal routes without reservation collision."""
    table = SpacetimeReservationTable()
    # Farmer at (4, 4) reserves route to shed
    farmer_route = [(700, (4, 4)), (701, (4, 3)), (702, (4, 2)), (703, (5, 2))]
    assert table.reserve_trajectory(farmer_route, 0) is True
    # Hand at (2, 2) reserves route to shed via (2, 2), (3, 2), (4, 2 at step 702) -> collides with farmer!
    hand_route_colliding = [(700, (2, 2)), (701, (3, 2)), (702, (4, 2)), (703, (5, 2))]
    # Step 702 at (4, 2) is already occupied by worker 0
    assert table.reserve_trajectory(hand_route_colliding, 1) is False


def test_th_09_immediate_sell_on_terminal_drop(matrix_base_obs: Dict[str, Any]) -> None:
    """TH-09: Terminal harvest patch injects market SELL orders at the DROP turn."""
    obs = copy.deepcopy(matrix_base_obs)
    obs["step"] = 702
    obs["day"] = 29
    obs["hour"] = 6
    obs["farms"][0]["tiles"][3][2] = {
        "kind": "PLANT",
        "crop": "CARROT",
        "yield_units": 3,
        "planted_day": 20,
        "watered_today": True,
    }
    econ = build_economic_state(obs)
    gen = HarvestCoupledPatchGenerator()

    req = CoupledPatchRequest(
        opportunity_id="OPP_TH_09",
        mechanism_family="TERMINAL_HARVEST_SWEEP",
        worker_ids=[1],
        start_step=702,
        econ_state=econ,
        baseline_action={"farmer": ["PASS"], "hands": [["PASS"]], "market": []},
        baseline_continuation=[{"farmer": ["PASS"], "hands": [["PASS"]], "market": []} for _ in range(16)],
        target_location=(2, 3),
        target_commodity="CARROT",
        is_terminal_sweep=True,
    )
    res = gen.generate_harvest_patch(req)
    assert res.patch is not None
    drop_act = next((a for a in res.patch.actions if a["hands"][0][0] == "DROP"), None)
    assert drop_act is not None
    mkt = drop_act.get("market", [])
    assert any(o[0] == "SELL" and o[1] == "CARROT" for o in mkt)


def test_th_10_step_718_final_liquidation(matrix_base_obs: Dict[str, Any]) -> None:
    """TH-10: At exact step 718, terminal liquidation opportunity fires to monetize shed."""
    from aec.opportunities.terminal import TerminalOpportunityAnalyzer
    obs = copy.deepcopy(matrix_base_obs)
    obs["step"] = 718
    obs["private"]["shed"] = {"CARROT": 25, "TOMATO": 10}
    econ = build_economic_state(obs)
    analyzer = TerminalOpportunityAnalyzer()
    opps = analyzer.analyze(econ, [])
    liq_opps = [o for o in opps if o.candidate_transformation_family == "TERMINAL_LIQUIDATION"]
    assert len(liq_opps) == 1
    assert liq_opps[0].affected_entities == ["SHED_LIQUIDATION"]


# =============================================================================
# 3. ECONOMIC ROUTE COMPRESSION: 10+ ACTIVATION & ADVERSARIAL PATTERNS (§6, §12)
# =============================================================================

def test_rc_01_detour_task_compaction_detector(matrix_base_obs: Dict[str, Any]) -> None:
    """RC-01: RouteCompressionDetector identifies mature crop within 2 steps of worker."""
    from aec.opportunities.route_compression import RouteCompressionDetector
    obs = copy.deepcopy(matrix_base_obs)
    # Hand at (2, 2). Mature crop at (2, 3) -> tiles[3][2]
    obs["farms"][0]["tiles"][3][2] = {
        "kind": "PLANT",
        "crop": "CARROT",
        "yield_units": 3,
        "planted_day": 0,
        "watered_today": True,
    }
    econ = build_economic_state(obs)
    detector = RouteCompressionDetector()
    opps = detector.detect(econ)
    rc_opps = [o for o in opps if o.candidate_transformation_family == "ROUTE_COMPRESSION"]
    assert len(rc_opps) >= 1
    assert rc_opps[0].dependency_info["crop"] == "CARROT"


def test_rc_02_direct_shed_transit_compaction_detector(matrix_base_obs: Dict[str, Any]) -> None:
    """RC-02: RouteCompressionDetector identifies direct shed path when worker has cargo."""
    from aec.opportunities.route_compression import RouteCompressionDetector
    obs = copy.deepcopy(matrix_base_obs)
    # Worker carries 4 CARROT
    obs["private"]["inventories"][1] = {"CARROT": 4}
    econ = build_economic_state(obs)
    detector = RouteCompressionDetector()
    opps = detector.detect(econ)
    rc_opps = [o for o in opps if o.candidate_transformation_family == "ROUTE_COMPRESSION"]
    assert len(rc_opps) >= 1
    shed_opps = [o for o in rc_opps if "SHED" in o.opportunity_id]
    assert len(shed_opps) >= 1


def test_rc_03_patch_generation_from_route_compression_opp(matrix_base_obs: Dict[str, Any]) -> None:
    """RC-03: PatchGenerator produces valid CoupledPatch from RouteCompressionOpportunity."""
    from aec.opportunities.route_compression import RouteCompressionDetector
    from aec.patches.generator import PatchGenerator
    obs = copy.deepcopy(matrix_base_obs)
    obs["farms"][0]["tiles"][3][2] = {
        "kind": "PLANT",
        "crop": "CARROT",
        "yield_units": 3,
        "planted_day": 0,
        "watered_today": True,
    }
    econ = build_economic_state(obs)
    detector = RouteCompressionDetector()
    opps = detector.detect(econ)
    gen = PatchGenerator(enabled_mechanisms={"ROUTE_COMPRESSION"})
    base_act = {"farmer": ["PASS"], "hands": [["PASS"]], "market": []}
    base_cont = [{"farmer": ["PASS"], "hands": [["PASS"]], "market": []} for _ in range(20)]
    patches = gen.generate_patches(
        opportunities=opps,
        econ_state=econ,
        baseline_action=base_act,
        baseline_continuation=base_cont,
    )
    rc_patches = [p for p in patches if p.mechanism_family == "ROUTE_COMPRESSION"]
    assert len(rc_patches) >= 1
    assert rc_patches[0].reconnect_result is not None
    assert rc_patches[0].reconnect_result.safety is True


def test_rc_04_negative_control_no_crops_no_cargo(matrix_base_obs: Dict[str, Any]) -> None:
    """RC-04: Negative Control: Empty field and no carried cargo -> 0 route compression opps."""
    from aec.opportunities.route_compression import RouteCompressionDetector
    obs = copy.deepcopy(matrix_base_obs)
    econ = build_economic_state(obs)
    detector = RouteCompressionDetector()
    opps = detector.detect(econ)
    assert len(opps) == 0


def test_rc_05_negative_control_shed_full_rejection(matrix_base_obs: Dict[str, Any]) -> None:
    """RC-05: Negative Control: Full shed -> route compression patch generator rejects."""
    obs = copy.deepcopy(matrix_base_obs)
    obs["private"]["shed"] = {"CARROT": 100}
    obs["farms"][0]["tiles"][3][2] = {
        "kind": "PLANT",
        "crop": "CARROT",
        "yield_units": 3,
        "planted_day": 0,
        "watered_today": True,
    }
    econ = build_economic_state(obs)
    gen = HarvestCoupledPatchGenerator()

    req = CoupledPatchRequest(
        opportunity_id="OPP_RC_05",
        mechanism_family="ROUTE_COMPRESSION",
        worker_ids=[1],
        start_step=50,
        econ_state=econ,
        baseline_action={"farmer": ["PASS"], "hands": [["PASS"]], "market": []},
        baseline_continuation=[{"farmer": ["PASS"], "hands": [["PASS"]], "market": []} for _ in range(15)],
        target_location=(2, 3),
        target_commodity="CARROT",
    )
    res = gen.generate_harvest_patch(req)
    assert res.status in (CoupledPatchState.CARGO_UNRESOLVED.value, CoupledPatchState.INFEASIBLE.value)


def test_rc_06_route_replaces_idle_passes_with_productivity(matrix_base_obs: Dict[str, Any]) -> None:
    """RC-06: Route compression replaces baseline idle passes with active harvesting."""
    obs = copy.deepcopy(matrix_base_obs)
    obs["farms"][0]["tiles"][3][2] = {
        "kind": "PLANT",
        "crop": "CARROT",
        "yield_units": 2,
        "planted_day": 0,
        "watered_today": True,
    }
    econ = build_economic_state(obs)
    gen = HarvestCoupledPatchGenerator()

    req = CoupledPatchRequest(
        opportunity_id="OPP_RC_06",
        mechanism_family="ROUTE_COMPRESSION",
        worker_ids=[1],
        start_step=50,
        econ_state=econ,
        baseline_action={"farmer": ["PASS"], "hands": [["PASS"]], "market": []},
        baseline_continuation=[{"farmer": ["PASS"], "hands": [["PASS"]], "market": []} for _ in range(15)],
        target_location=(2, 3),
        target_commodity="CARROT",
    )
    res = gen.generate_harvest_patch(req)
    assert res.patch is not None
    # Baseline had only PASS; compressed patch actions have active moves
    assert res.patch.actions[0]["hands"][0] != ["PASS"]


def test_rc_07_spacetime_conflict_avoidance(matrix_base_obs: Dict[str, Any]) -> None:
    """RC-07: Route compression respects spacetime reservations and finds collision-free detour."""
    table = SpacetimeReservationTable()
    # Cell (2, 3) at step 51 reserved by worker 0
    table.reserve_vertex(step=51, pos=(2, 3), worker_id=0)
    # Worker 1 cannot step into (2, 3) at step 51
    assert table.is_vertex_available(step=51, pos=(2, 3), worker_id=1) is False
    # But cell (2, 3) at step 52 is free
    assert table.is_vertex_available(step=52, pos=(2, 3), worker_id=1) is True


def test_rc_08_exact_counterfactual_economic_advantage(matrix_base_obs: Dict[str, Any]) -> None:
    """RC-08: Exact forward simulation yields positive delta_terminal_margin for route compression."""
    obs = copy.deepcopy(matrix_base_obs)
    obs["farms"][0]["tiles"][3][2] = {
        "kind": "PLANT",
        "crop": "CARROT",
        "yield_units": 3,
        "planted_day": 0,
        "watered_today": True,
    }
    econ = build_economic_state(obs)
    gen = HarvestCoupledPatchGenerator()

    req = CoupledPatchRequest(
        opportunity_id="OPP_RC_08",
        mechanism_family="ROUTE_COMPRESSION",
        worker_ids=[1],
        start_step=50,
        econ_state=econ,
        baseline_action={"farmer": ["PASS"], "hands": [["PASS"]], "market": []},
        baseline_continuation=[{"farmer": ["PASS"], "hands": [["PASS"]], "market": []} for _ in range(18)],
        target_location=(2, 3),
        target_commodity="CARROT",
    )
    res = gen.generate_harvest_patch(req)
    assert res.patch is not None
    assert res.exact_delta > 0.0
    assert res.status == "ACCEPTED"


def test_rc_09_reconnect_fidelity_preserves_continuation(matrix_base_obs: Dict[str, Any]) -> None:
    """RC-09: Reconnect result contains safe spliced trajectory matching baseline suffix."""
    obs = copy.deepcopy(matrix_base_obs)
    obs["farms"][0]["tiles"][3][2] = {
        "kind": "PLANT",
        "crop": "CARROT",
        "yield_units": 2,
        "planted_day": 0,
        "watered_today": True,
    }
    econ = build_economic_state(obs)
    gen = HarvestCoupledPatchGenerator()

    req = CoupledPatchRequest(
        opportunity_id="OPP_RC_09",
        mechanism_family="ROUTE_COMPRESSION",
        worker_ids=[1],
        start_step=50,
        econ_state=econ,
        baseline_action={"farmer": ["PASS"], "hands": [["PASS"]], "market": []},
        baseline_continuation=[{"farmer": ["PASS"], "hands": [["PASS"]], "market": []} for _ in range(18)],
        target_location=(2, 3),
        target_commodity="CARROT",
    )
    res = gen.generate_harvest_patch(req)
    assert res.patch is not None
    assert res.patch.reconnect_result is not None
    assert len(res.patch.spliced_continuation) > 0


def test_rc_10_market_liquidation_bundle(matrix_base_obs: Dict[str, Any]) -> None:
    """RC-10: Route compression automatically injects SELL order on DROP step for liquidity realization."""
    obs = copy.deepcopy(matrix_base_obs)
    obs["farms"][0]["tiles"][3][2] = {
        "kind": "PLANT",
        "crop": "CARROT",
        "yield_units": 3,
        "planted_day": 0,
        "watered_today": True,
    }
    econ = build_economic_state(obs)
    gen = HarvestCoupledPatchGenerator()

    req = CoupledPatchRequest(
        opportunity_id="OPP_RC_10",
        mechanism_family="ROUTE_COMPRESSION",
        worker_ids=[1],
        start_step=50,
        econ_state=econ,
        baseline_action={"farmer": ["PASS"], "hands": [["PASS"]], "market": []},
        baseline_continuation=[{"farmer": ["PASS"], "hands": [["PASS"]], "market": []} for _ in range(18)],
        target_location=(2, 3),
        target_commodity="CARROT",
    )
    res = gen.generate_harvest_patch(req)
    assert res.patch is not None
    drop_act = next((a for a in res.patch.actions if a["hands"][0][0] == "DROP"), None)
    assert drop_act is not None
    assert any(o[0] == "SELL" and o[1] == "CARROT" for o in drop_act.get("market", []))


# =============================================================================
# 4. CARGO FERRY: 10+ ACTIVATION & ADVERSARIAL PATTERNS (§7, §12)
# =============================================================================

def test_cf_01_cargo_ferry_detector_identifies_opportunity(matrix_base_obs: Dict[str, Any]) -> None:
    """CF-01: CargoFerryDetector identifies auxiliary hand to ferry nearby mature crop."""
    from aec.opportunities.cargo_ferry import CargoFerryDetector
    obs = copy.deepcopy(matrix_base_obs)
    # Hand at (2, 2). Mature crop at (2, 3) -> tiles[3][2]. Farmer at (4, 4)
    obs["farms"][0]["tiles"][3][2] = {
        "kind": "PLANT",
        "crop": "CARROT",
        "yield_units": 3,
        "planted_day": 0,
        "watered_today": True,
    }
    econ = build_economic_state(obs)
    detector = CargoFerryDetector()
    opps = detector.detect(econ)
    cf_opps = [o for o in opps if o.candidate_transformation_family == "CARGO_FERRY"]
    assert len(cf_opps) >= 1
    assert cf_opps[0].ferry_worker_id == 1
    assert cf_opps[0].source_worker_id == 0


def test_cf_02_patch_generation_for_ferry_hand(matrix_base_obs: Dict[str, Any]) -> None:
    """CF-02: PatchGenerator produces CoupledPatch targeting ferry worker without mutating Farmer."""
    from aec.opportunities.cargo_ferry import CargoFerryDetector
    from aec.patches.generator import PatchGenerator
    obs = copy.deepcopy(matrix_base_obs)
    obs["farms"][0]["tiles"][3][2] = {
        "kind": "PLANT",
        "crop": "CARROT",
        "yield_units": 3,
        "planted_day": 0,
        "watered_today": True,
    }
    econ = build_economic_state(obs)
    detector = CargoFerryDetector()
    opps = detector.detect(econ)
    gen = PatchGenerator(enabled_mechanisms={"CARGO_FERRY"})
    base_act = {"farmer": ["PASS"], "hands": [["PASS"]], "market": []}
    base_cont = [{"farmer": ["PASS"], "hands": [["PASS"]], "market": []} for _ in range(20)]
    patches = gen.generate_patches(
        opportunities=opps,
        econ_state=econ,
        baseline_action=base_act,
        baseline_continuation=base_cont,
    )
    cf_patches = [p for p in patches if p.mechanism_family == "CARGO_FERRY"]
    assert len(cf_patches) >= 1
    # Check that Hand 1 is mutated
    assert 1 in cf_patches[0].worker_mutations
    # Farmer (0) is unmutated
    assert 0 not in cf_patches[0].worker_mutations


def test_cf_03_multiworker_reservation_avoids_collision(matrix_base_obs: Dict[str, Any]) -> None:
    """CF-03: Spacetime reservation guarantees ferry worker and farmer don't collide."""
    table = SpacetimeReservationTable()
    # Farmer reserves step 51 at (2, 3)
    table.reserve_vertex(step=51, pos=(2, 3), worker_id=0)
    # Ferry worker trying to reserve step 51 at (2, 3) fails
    assert table.reserve_vertex(step=51, pos=(2, 3), worker_id=1) is False
    # But step 52 at (2, 3) is free for ferry worker
    assert table.reserve_vertex(step=52, pos=(2, 3), worker_id=1) is True


def test_cf_04_negative_control_single_worker(matrix_base_obs: Dict[str, Any]) -> None:
    """CF-04: Negative Control: Solo farmer (0 hands) -> CargoFerryDetector abstains."""
    from aec.opportunities.cargo_ferry import CargoFerryDetector
    obs = copy.deepcopy(matrix_base_obs)
    obs["farms"][0]["hands"] = []
    obs["private"]["inventories"] = [{}]
    obs["farms"][0]["tiles"][3][2] = {
        "kind": "PLANT",
        "crop": "CARROT",
        "yield_units": 3,
        "planted_day": 0,
        "watered_today": True,
    }
    econ = build_economic_state(obs)
    detector = CargoFerryDetector()
    opps = detector.detect(econ)
    assert len(opps) == 0


def test_cf_05_negative_control_frozen_hand(matrix_base_obs: Dict[str, Any]) -> None:
    """CF-05: Negative Control: Auxiliary hand is frozen -> detector abstains."""
    from aec.opportunities.cargo_ferry import CargoFerryDetector
    obs = copy.deepcopy(matrix_base_obs)
    obs["farms"][0]["tiles"][3][2] = {
        "kind": "PLANT",
        "crop": "CARROT",
        "yield_units": 3,
        "planted_day": 0,
        "watered_today": True,
    }
    econ = build_economic_state(obs)
    # Mark hand as frozen
    econ.workers.workers[1].is_frozen = True
    detector = CargoFerryDetector()
    opps = detector.detect(econ)
    assert len(opps) == 0


def test_cf_06_negative_control_shed_full(matrix_base_obs: Dict[str, Any]) -> None:
    """CF-06: Negative Control: Shed is full (100 capacity) -> detector abstains."""
    from aec.opportunities.cargo_ferry import CargoFerryDetector
    obs = copy.deepcopy(matrix_base_obs)
    obs["private"]["shed"] = {"CARROT": 100}
    obs["farms"][0]["tiles"][3][2] = {
        "kind": "PLANT",
        "crop": "CARROT",
        "yield_units": 3,
        "planted_day": 0,
        "watered_today": True,
    }
    econ = build_economic_state(obs)
    detector = CargoFerryDetector()
    opps = detector.detect(econ)
    assert len(opps) == 0


def test_cf_07_idle_helper_low_opportunity_cost(matrix_base_obs: Dict[str, Any]) -> None:
    """CF-07: Idle helper executes ferry while baseline continues for Farmer."""
    obs = copy.deepcopy(matrix_base_obs)
    obs["farms"][0]["tiles"][3][2] = {
        "kind": "PLANT",
        "crop": "CARROT",
        "yield_units": 2,
        "planted_day": 0,
        "watered_today": True,
    }
    econ = build_economic_state(obs)
    gen = HarvestCoupledPatchGenerator()

    req = CoupledPatchRequest(
        opportunity_id="OPP_CF_07",
        mechanism_family="CARGO_FERRY",
        worker_ids=[1],
        start_step=50,
        econ_state=econ,
        baseline_action={"farmer": ["PASS"], "hands": [["PASS"]], "market": []},
        baseline_continuation=[{"farmer": ["PASS"], "hands": [["PASS"]], "market": []} for _ in range(16)],
        target_location=(2, 3),
        target_commodity="CARROT",
    )
    res = gen.generate_harvest_patch(req)
    assert res.patch is not None
    assert res.labor_opportunity_cost == 0.0


def test_cf_08_exact_counterfactual_simulation_advantage(matrix_base_obs: Dict[str, Any]) -> None:
    """CF-08: Exact forward simulation confirms positive delta_terminal_margin for ferry operation."""
    obs = copy.deepcopy(matrix_base_obs)
    obs["farms"][0]["tiles"][3][2] = {
        "kind": "PLANT",
        "crop": "CARROT",
        "yield_units": 3,
        "planted_day": 0,
        "watered_today": True,
    }
    econ = build_economic_state(obs)
    gen = HarvestCoupledPatchGenerator()

    req = CoupledPatchRequest(
        opportunity_id="OPP_CF_08",
        mechanism_family="CARGO_FERRY",
        worker_ids=[1],
        start_step=50,
        econ_state=econ,
        baseline_action={"farmer": ["PASS"], "hands": [["PASS"]], "market": []},
        baseline_continuation=[{"farmer": ["PASS"], "hands": [["PASS"]], "market": []} for _ in range(18)],
        target_location=(2, 3),
        target_commodity="CARROT",
    )
    res = gen.generate_harvest_patch(req)
    assert res.patch is not None
    assert res.exact_delta > 0.0
    assert res.status == "ACCEPTED"


def test_cf_09_reconnect_fidelity_for_ferry_hand(matrix_base_obs: Dict[str, Any]) -> None:
    """CF-09: Ferry hand patch includes clean rendezvous reconnection to baseline continuation."""
    obs = copy.deepcopy(matrix_base_obs)
    obs["farms"][0]["tiles"][3][2] = {
        "kind": "PLANT",
        "crop": "CARROT",
        "yield_units": 2,
        "planted_day": 0,
        "watered_today": True,
    }
    econ = build_economic_state(obs)
    gen = HarvestCoupledPatchGenerator()

    req = CoupledPatchRequest(
        opportunity_id="OPP_CF_09",
        mechanism_family="CARGO_FERRY",
        worker_ids=[1],
        start_step=50,
        econ_state=econ,
        baseline_action={"farmer": ["PASS"], "hands": [["PASS"]], "market": []},
        baseline_continuation=[{"farmer": ["PASS"], "hands": [["PASS"]], "market": []} for _ in range(18)],
        target_location=(2, 3),
        target_commodity="CARROT",
    )
    res = gen.generate_harvest_patch(req)
    assert res.patch is not None
    assert res.patch.reconnect_result is not None
    assert res.patch.reconnect_result.safety is True


def test_cf_10_immediate_liquidity_realization_on_ferry_drop(matrix_base_obs: Dict[str, Any]) -> None:
    """CF-10: Ferry patch bundles SELL orders into market actions at DROP step."""
    obs = copy.deepcopy(matrix_base_obs)
    obs["farms"][0]["tiles"][3][2] = {
        "kind": "PLANT",
        "crop": "CARROT",
        "yield_units": 3,
        "planted_day": 0,
        "watered_today": True,
    }
    econ = build_economic_state(obs)
    gen = HarvestCoupledPatchGenerator()

    req = CoupledPatchRequest(
        opportunity_id="OPP_CF_10",
        mechanism_family="CARGO_FERRY",
        worker_ids=[1],
        start_step=50,
        econ_state=econ,
        baseline_action={"farmer": ["PASS"], "hands": [["PASS"]], "market": []},
        baseline_continuation=[{"farmer": ["PASS"], "hands": [["PASS"]], "market": []} for _ in range(18)],
        target_location=(2, 3),
        target_commodity="CARROT",
    )
    res = gen.generate_harvest_patch(req)
    assert res.patch is not None
    drop_act = next((a for a in res.patch.actions if a["hands"][0][0] == "DROP"), None)
    assert drop_act is not None
    assert any(o[0] == "SELL" and o[1] == "CARROT" for o in drop_act.get("market", []))


# =============================================================================
# 5. CROSS-MECHANISM COUPLING & COMPOSITION TESTS (§8)
# =============================================================================

def test_comp_01_dynamic_harvest_and_route_compression_composition(matrix_base_obs: Dict[str, Any]) -> None:
    """COMP-01: Compose Dynamic Harvest (Farmer) + Route Compression (Hand 1)."""
    from aec.patches.composition import PatchCompositionEngine, CompositionRelation
    obs = copy.deepcopy(matrix_base_obs)
    # Plant at (5, 4) for Farmer (4, 4), Plant at (1, 2) for Hand (2, 2)
    obs["farms"][0]["tiles"][4][5] = {"kind": "PLANT", "crop": "CARROT", "yield_units": 2, "planted_day": 0, "watered_today": True}
    obs["farms"][0]["tiles"][2][1] = {"kind": "PLANT", "crop": "CARROT", "yield_units": 2, "planted_day": 0, "watered_today": True}
    econ = build_economic_state(obs)
    gen = HarvestCoupledPatchGenerator()

    # Patch A: Farmer (0) dynamic harvest
    req_a = CoupledPatchRequest(
        opportunity_id="OPP_DH",
        mechanism_family="DYNAMIC_SHADOW_HARVEST",
        worker_ids=[0],
        start_step=50,
        econ_state=econ,
        baseline_action={"farmer": ["PASS"], "hands": [["PASS"]], "market": []},
        baseline_continuation=[{"farmer": ["PASS"], "hands": [["PASS"]], "market": []} for _ in range(16)],
        target_location=(5, 4),
        target_commodity="CARROT",
    )
    res_a = gen.generate_harvest_patch(req_a)
    assert res_a.patch is not None

    # Patch B: Hand (1) route compression
    req_b = CoupledPatchRequest(
        opportunity_id="OPP_RC",
        mechanism_family="ROUTE_COMPRESSION",
        worker_ids=[1],
        start_step=50,
        econ_state=econ,
        baseline_action={"farmer": ["PASS"], "hands": [["PASS"]], "market": []},
        baseline_continuation=[{"farmer": ["PASS"], "hands": [["PASS"]], "market": []} for _ in range(16)],
        target_location=(1, 2),
        target_commodity="CARROT",
    )
    res_b = gen.generate_harvest_patch(req_b)
    assert res_b.patch is not None

    engine = PatchCompositionEngine()
    report = engine.analyze_pair(res_a.patch, res_b.patch)
    assert report.relation == CompositionRelation.PARALLEL
    assert report.compatible is True

    composite = engine.compose(res_a.patch, res_b.patch)
    assert composite is not None
    assert composite.worker_ids == [0, 1]
    assert 0 in composite.worker_mutations
    assert 1 in composite.worker_mutations
    assert composite.economic_effect == res_a.patch.economic_effect + res_b.patch.economic_effect


def test_comp_02_dynamic_harvest_and_cargo_ferry_composition(matrix_base_obs: Dict[str, Any]) -> None:
    """COMP-02: Compose Dynamic Harvest (Farmer) + Cargo Ferry (Hand 1)."""
    from aec.patches.composition import PatchCompositionEngine, CompositionRelation
    obs = copy.deepcopy(matrix_base_obs)
    obs["farms"][0]["tiles"][4][5] = {"kind": "PLANT", "crop": "CARROT", "yield_units": 2, "planted_day": 0, "watered_today": True}
    obs["farms"][0]["tiles"][2][1] = {"kind": "PLANT", "crop": "CARROT", "yield_units": 3, "planted_day": 0, "watered_today": True}
    econ = build_economic_state(obs)
    gen = HarvestCoupledPatchGenerator()

    req_a = CoupledPatchRequest(
        opportunity_id="OPP_DH",
        mechanism_family="DYNAMIC_SHADOW_HARVEST",
        worker_ids=[0],
        start_step=50,
        econ_state=econ,
        baseline_action={"farmer": ["PASS"], "hands": [["PASS"]], "market": []},
        baseline_continuation=[{"farmer": ["PASS"], "hands": [["PASS"]], "market": []} for _ in range(16)],
        target_location=(5, 4),
        target_commodity="CARROT",
    )
    res_a = gen.generate_harvest_patch(req_a)
    assert res_a.patch is not None

    req_b = CoupledPatchRequest(
        opportunity_id="OPP_CF",
        mechanism_family="CARGO_FERRY",
        worker_ids=[1],
        start_step=50,
        econ_state=econ,
        baseline_action={"farmer": ["PASS"], "hands": [["PASS"]], "market": []},
        baseline_continuation=[{"farmer": ["PASS"], "hands": [["PASS"]], "market": []} for _ in range(16)],
        target_location=(1, 2),
        target_commodity="CARROT",
    )
    res_b = gen.generate_harvest_patch(req_b)
    assert res_b.patch is not None

    engine = PatchCompositionEngine()
    composite = engine.compose(res_a.patch, res_b.patch)
    assert composite is not None
    assert composite.worker_ids == [0, 1]
    assert composite.economic_effect > 0


def test_comp_03_terminal_harvest_and_cargo_ferry_composition(matrix_base_obs: Dict[str, Any]) -> None:
    """COMP-03: Compose Terminal Harvest (Farmer) + Cargo Ferry (Hand 1)."""
    from aec.patches.composition import PatchCompositionEngine, CompositionRelation
    obs = copy.deepcopy(matrix_base_obs)
    obs["step"] = 700
    obs["farms"][0]["tiles"][3][4] = {"kind": "PLANT", "crop": "CARROT", "yield_units": 2, "planted_day": 0, "watered_today": True}
    obs["farms"][0]["tiles"][3][2] = {"kind": "PLANT", "crop": "CARROT", "yield_units": 2, "planted_day": 0, "watered_today": True}
    econ = build_economic_state(obs)
    gen = HarvestCoupledPatchGenerator()

    req_a = CoupledPatchRequest(
        opportunity_id="OPP_TH",
        mechanism_family="TERMINAL_HARVEST_SWEEP",
        worker_ids=[0],
        start_step=700,
        econ_state=econ,
        baseline_action={"farmer": ["PASS"], "hands": [["PASS"]], "market": []},
        baseline_continuation=[{"farmer": ["PASS"], "hands": [["PASS"]], "market": []} for _ in range(18)],
        target_location=(4, 3),
        target_commodity="CARROT",
        is_terminal_sweep=True,
    )
    res_a = gen.generate_harvest_patch(req_a)
    assert res_a.patch is not None

    req_b = CoupledPatchRequest(
        opportunity_id="OPP_CF",
        mechanism_family="CARGO_FERRY",
        worker_ids=[1],
        start_step=700,
        econ_state=econ,
        baseline_action={"farmer": ["PASS"], "hands": [["PASS"]], "market": []},
        baseline_continuation=[{"farmer": ["PASS"], "hands": [["PASS"]], "market": []} for _ in range(18)],
        target_location=(2, 3),
        target_commodity="CARROT",
        is_terminal_sweep=True,
    )
    res_b = gen.generate_harvest_patch(req_b)
    assert res_b.patch is not None

    engine = PatchCompositionEngine()
    composite = engine.compose(res_a.patch, res_b.patch)
    assert composite is not None
    assert composite.worker_ids == [0, 1]


def test_comp_04_terminal_harvest_and_route_compression_composition(matrix_base_obs: Dict[str, Any]) -> None:
    """COMP-04: Compose Terminal Harvest (Farmer) + Route Compression (Hand 1)."""
    from aec.patches.composition import PatchCompositionEngine, CompositionRelation
    obs = copy.deepcopy(matrix_base_obs)
    obs["step"] = 700
    obs["farms"][0]["tiles"][3][4] = {"kind": "PLANT", "crop": "CARROT", "yield_units": 2, "planted_day": 0, "watered_today": True}
    obs["farms"][0]["tiles"][3][2] = {"kind": "PLANT", "crop": "CARROT", "yield_units": 2, "planted_day": 0, "watered_today": True}
    econ = build_economic_state(obs)
    gen = HarvestCoupledPatchGenerator()

    req_a = CoupledPatchRequest(
        opportunity_id="OPP_TH",
        mechanism_family="TERMINAL_HARVEST_SWEEP",
        worker_ids=[0],
        start_step=700,
        econ_state=econ,
        baseline_action={"farmer": ["PASS"], "hands": [["PASS"]], "market": []},
        baseline_continuation=[{"farmer": ["PASS"], "hands": [["PASS"]], "market": []} for _ in range(18)],
        target_location=(4, 3),
        target_commodity="CARROT",
        is_terminal_sweep=True,
    )
    res_a = gen.generate_harvest_patch(req_a)
    assert res_a.patch is not None

    req_b = CoupledPatchRequest(
        opportunity_id="OPP_RC",
        mechanism_family="ROUTE_COMPRESSION",
        worker_ids=[1],
        start_step=700,
        econ_state=econ,
        baseline_action={"farmer": ["PASS"], "hands": [["PASS"]], "market": []},
        baseline_continuation=[{"farmer": ["PASS"], "hands": [["PASS"]], "market": []} for _ in range(18)],
        target_location=(2, 3),
        target_commodity="CARROT",
        is_terminal_sweep=True,
    )
    res_b = gen.generate_harvest_patch(req_b)
    assert res_b.patch is not None

    engine = PatchCompositionEngine()
    composite = engine.compose(res_a.patch, res_b.patch)
    assert composite is not None
    assert composite.worker_ids == [0, 1]


def test_comp_05_same_worker_mutual_exclusion_rejection(matrix_base_obs: Dict[str, Any]) -> None:
    """COMP-05: Negative Control: Two patches competing for same worker (Farmer 0) cannot compose."""
    from aec.patches.composition import PatchCompositionEngine, CompositionRelation
    obs = copy.deepcopy(matrix_base_obs)
    obs["farms"][0]["tiles"][3][4] = {"kind": "PLANT", "crop": "CARROT", "yield_units": 2, "planted_day": 0, "watered_today": True}
    econ = build_economic_state(obs)
    gen = HarvestCoupledPatchGenerator()

    req_a = CoupledPatchRequest(
        opportunity_id="OPP_A",
        mechanism_family="DYNAMIC_SHADOW_HARVEST",
        worker_ids=[0],
        start_step=50,
        econ_state=econ,
        baseline_action={"farmer": ["PASS"], "hands": [["PASS"]], "market": []},
        baseline_continuation=[{"farmer": ["PASS"], "hands": [["PASS"]], "market": []} for _ in range(16)],
        target_location=(4, 3),
        target_commodity="CARROT",
    )
    res_a = gen.generate_harvest_patch(req_a)

    req_b = CoupledPatchRequest(
        opportunity_id="OPP_B",
        mechanism_family="ROUTE_COMPRESSION",
        worker_ids=[0],
        start_step=50,
        econ_state=econ,
        baseline_action={"farmer": ["PASS"], "hands": [["PASS"]], "market": []},
        baseline_continuation=[{"farmer": ["PASS"], "hands": [["PASS"]], "market": []} for _ in range(16)],
        target_location=(4, 3),
        target_commodity="CARROT",
    )
    res_b = gen.generate_harvest_patch(req_b)

    engine = PatchCompositionEngine()
    report = engine.analyze_pair(res_a.patch, res_b.patch)
    assert report.compatible is False
    assert report.relation in (CompositionRelation.DOMINATES, CompositionRelation.MUTUALLY_EXCLUSIVE)
    # compose must return None
    assert engine.compose(res_a.patch, res_b.patch) is None




