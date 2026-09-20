# SPDX-License-Identifier: MIT
"""Unit tests for Phase 020 Multi-Worker Harvest Synchronization Mechanism."""

import copy
import pytest
from aec.config import build_phase020_treatment_config, build_robust_qualified_config
from aec.ir.economic_state import EconomicState
from aec.ir.farm_state import FarmState
from aec.ir.market_state import MarketState
from aec.ir.opponent_state import OpponentState
from aec.ir.worker_state import WorkerEntity, WorkerState
from aec.opportunities.multiworker_harvest import MultiworkerHarvestDetector
from aec.patches.generator import PatchGenerator


def create_test_state(hand_pos=(3, 3), crop_mature=True) -> EconomicState:
    workers = [
        WorkerEntity(worker_id=0, position=(0, 0), task="PASS", cargo={}),
        WorkerEntity(worker_id=1, position=hand_pos, task="PASS", cargo={}),
    ]
    tiles = [[{"kind": "SOIL"} for _ in range(10)] for _ in range(10)]
    if crop_mature:
        tiles[3][3] = {
            "kind": "PLANT",
            "crop": "WHEAT",
            "growth_stage": 2,
            "yield_units": 5,
        }
    farm = FarmState(
        cash=1500.0,
        tiles=tiles,
        shed_inventory={"WHEAT": 20},
    )
    market = MarketState(
        current_prices={"WHEAT": 25.0},
        steps_to_town_tick=12,
    )
    opp = OpponentState(supply_forecast={}, sale_pressure={}, observed_animals={})
    return EconomicState(
        step=250,
        day=10,
        hour=10,
        farm=farm,
        market=market,
        workers=WorkerState(workers=workers),
        opponent=opp,
    )


def test_multiworker_harvest_detection():
    detector = MultiworkerHarvestDetector(min_step=144)
    econ = create_test_state(hand_pos=(3, 3), crop_mature=True)
    base_act = {"farmer": ["PASS"], "hands": [["PASS"]], "market": []}

    opps = detector.detect(econ, base_act)
    assert len(opps) == 1
    opp = opps[0]
    assert opp.candidate_transformation_family == "MULTIWORKER_HARVEST_SYNCHRONIZATION"
    assert opp.affected_entities[0] == 1  # Hand 1
    assert opp.affected_entities[1] == (3, 3)


def test_multiworker_harvest_patch_generation():
    detector = MultiworkerHarvestDetector(min_step=144)
    econ = create_test_state(hand_pos=(3, 3), crop_mature=True)
    base_act = {"farmer": ["PASS"], "hands": [["PASS"]], "market": [["BUY", "FERTILIZER", 2]]}

    opps = detector.detect(econ, base_act)
    assert len(opps) == 1

    cfg = build_phase020_treatment_config()
    patch_gen = PatchGenerator(config=cfg)

    patches = patch_gen.generate_patches(
        opportunities=opps,
        econ_state=econ,
        baseline_action=base_act,
        config=cfg,
    )

    assert len(patches) == 1
    p = patches[0]
    assert p.mechanism_family == "MULTIWORKER_HARVEST_SYNCHRONIZATION"

    # Verify application
    patched_act = p.apply(base_act)
    assert patched_act["farmer"] == ["PASS"]
    assert patched_act["hands"][0] == ["HARVEST"]
    assert patched_act["market"] == base_act["market"]  # Zero market distortion!


def test_treatment_config_invariants():
    cfg = build_phase020_treatment_config()
    assert cfg.enable_multiworker_harvest is True
    assert "MULTIWORKER_HARVEST_SYNCHRONIZATION" in cfg.enabled_mechanisms
    assert cfg.enable_funnel_reservation is True  # Preserves foundation seats
    assert cfg.enable_asset_holding_trigger is False  # Strict quarantine
    assert cfg.enable_tranche_synthesizer is False    # Strict quarantine
