# SPDX-License-Identifier: MIT
"""AEC Phase 009: Synthetic Activation Matrix for All 10 Transformational Mechanisms.

Verifies end-to-end execution across:
1. Synthetic opportunity state
2. Candidate generated?
3. Patch generated?
4. Exact simulation reached?
5. Safety passed?
6. Commit / Abstain determined?
"""

from __future__ import annotations

import copy
from typing import Any, Dict, List
import pytest

from aec.config import AECConfig
from aec.counterfactual.simulator import CounterfactualSimulator
from aec.events.event_types import Event, EventType
from aec.ir.economic_state import EconomicState
from aec.ir.farm_state import FarmState
from aec.ir.market_state import MarketState
from aec.ir.worker_state import WorkerEntity, WorkerState
from aec.ir.opponent_state import OpponentState
from aec.opportunities.arbitrage import ProductionArbitrageDetector, ShopArbitrageDetector
from aec.opportunities.cargo_ferry import CargoFerryDetector
from aec.opportunities.labor import LaborOpportunityAnalyzer
from aec.opportunities.market import MarketOpportunityAnalyzer
from aec.opportunities.resource import ResourceOpportunityAnalyzer
from aec.opportunities.route_compression import RouteCompressionDetector
from aec.opportunities.terminal import TerminalOpportunityAnalyzer
from aec.opportunities.terminal_conversion import TerminalConversionDetector
from aec.opportunities.town_cycle import TownCycleSignalDetector
from aec.patches.generator import PatchGenerator
from aec.patches.patch import CoupledPatch
from aec.safety.checks import SafetyChecker
from aec.evaluation.win_model import WinModel


@pytest.fixture
def base_synth_state() -> EconomicState:
    workers = [
        WorkerEntity(worker_id=0, position=(4, 4), task="PASS", cargo={}),
        WorkerEntity(worker_id=1, position=(2, 2), task="PASS", cargo={}),
    ]
    tiles = [[{"kind": "SOIL"} for _ in range(10)] for _ in range(10)]
    farm = FarmState(cash=1000.0, tiles=tiles, shed_inventory={"WHEAT": 10, "CARROT": 5})
    market = MarketState(
        current_prices={"WHEAT": 25, "CARROT": 35, "TOMATO": 60, "STRAWBERRY": 120, "MELON": 250},
        steps_to_town_tick=2,
        expected_absorption={"STRAWBERRY": 2, "WHEAT": 1},
        unlocked_shops=["BAKERY", "SMOOTHIE_SHOP"]
    )
    opponent = OpponentState(supply_forecast={"STRAWBERRY": 0}, sale_pressure={}, observed_animals={})
    return EconomicState(
        step=100,
        day=4,
        hour=4,
        farm=farm,
        market=market,
        workers=WorkerState(workers=workers),
        opponent=opponent,
    )


def run_activation_pipeline(
    opp,
    econ_state: EconomicState,
    baseline_action: Dict[str, Any],
    enabled_mechanisms: set,
    future_trajectory: List[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Execute the canonical compiler pipeline on a candidate opportunity."""
    result = {
        "candidate_generated": opp is not None,
        "patch_generated": False,
        "exact_simulation_reached": False,
        "safety_passed": False,
        "decision": "ABSTAIN",
        "patch": None,
    }

    if not opp:
        return result

    # 1. Patch Generation
    gen = PatchGenerator(enabled_mechanisms=enabled_mechanisms)
    baseline_cont = future_trajectory or [copy.deepcopy(baseline_action) for _ in range(24)]
    patches = gen.generate_patches([opp], econ_state, baseline_action, baseline_continuation=baseline_cont)

    if not patches:
        return result

    result["patch_generated"] = True
    patch = patches[0]
    result["patch"] = patch

    # 2. Exact Counterfactual Simulation
    sim = CounterfactualSimulator()
    sim_outcome = sim.evaluate(
        candidate_patch=patch,
        baseline_action=baseline_action,
        econ_state=econ_state,
        horizon=12,
        continuation_trajectory=baseline_cont[:11]
    )
    result["exact_simulation_reached"] = sim_outcome is not None

    # 3. Safety Verification
    safety_checker = SafetyChecker()
    passed_safety, checks, reason = safety_checker.verify(
        patch=patch,
        outcome=sim_outcome,
        econ_state=econ_state,
        baseline_action=baseline_action,
        future_trajectory=baseline_cont[:11]
    )
    result["safety_passed"] = passed_safety

    # 4. Economic Evaluation / Decision Gate
    win_model = WinModel()
    eval_res = win_model.evaluate(
        patch=patch,
        outcome=sim_outcome,
        econ_state=econ_state,
        continuation_trajectory=baseline_cont[:11],
        baseline_action=baseline_action
    )
    if passed_safety and (eval_res.is_superior or eval_res.terminal_margin_delta > 0):
        result["decision"] = "COMMIT"
    else:
        result["decision"] = "ABSTAIN"

    return result


def test_matrix_1_dynamic_shadow_harvest(base_synth_state: EconomicState):
    """1. Dynamic Shadow Harvest activation pipeline."""
    base_synth_state.farm.tiles[5][4] = {
        "kind": "PLANT", "crop": "CARROT", "yield_units": 3, "planted_day": 0
    }
    detector = LaborOpportunityAnalyzer()
    baseline_act = {"farmer": ["PASS"], "hands": [["PASS"]], "market": []}
    opps = detector.analyze(base_synth_state, [], baseline_act)
    harvest_opps = [o for o in opps if o.candidate_transformation_family == "DYNAMIC_SHADOW_HARVEST"]
    assert len(harvest_opps) > 0

    res = run_activation_pipeline(harvest_opps[0], base_synth_state, baseline_act, {"DYNAMIC_SHADOW_HARVEST"})
    assert res["candidate_generated"] is True
    assert res["patch_generated"] is True
    assert res["exact_simulation_reached"] is True
    assert res["safety_passed"] is True


def test_matrix_2_terminal_harvest_sweep(base_synth_state: EconomicState):
    """2. Terminal Harvest Sweep activation pipeline."""
    base_synth_state.step = 700
    base_synth_state.day = 29
    base_synth_state.farm.tiles[5][4] = {
        "kind": "PLANT", "crop": "CARROT", "yield_units": 2, "planted_day": 0
    }
    detector = TerminalOpportunityAnalyzer()
    baseline_act = {"farmer": ["PASS"], "hands": [["PASS"]], "market": []}
    opps = detector.analyze(base_synth_state, [])
    sweep_opps = [o for o in opps if o.candidate_transformation_family == "TERMINAL_HARVEST_SWEEP"]
    assert len(sweep_opps) > 0

    res = run_activation_pipeline(sweep_opps[0], base_synth_state, baseline_act, {"TERMINAL_HARVEST_SWEEP"})
    assert res["candidate_generated"] is True
    assert res["patch_generated"] is True
    assert res["exact_simulation_reached"] is True
    assert res["safety_passed"] is True


def test_matrix_3_route_compression(base_synth_state: EconomicState):
    """3. Route Compression activation pipeline."""
    detector = RouteCompressionDetector()
    crop_mock = type("CropMock", (), {
        "crop_type": "MELON", "position": (4, 5), "is_mature": True, "growth_stage": 4, "max_growth": 4
    })()
    base_synth_state.farm.crops = [crop_mock]
    baseline_act = {"farmer": ["PASS"], "hands": [["PASS"]], "market": []}
    opps = detector.detect(base_synth_state, worker_id=0)
    assert len(opps) > 0

    res = run_activation_pipeline(opps[0], base_synth_state, baseline_act, {"ROUTE_COMPRESSION"})
    assert res["candidate_generated"] is True
    assert res["patch_generated"] is True
    assert res["exact_simulation_reached"] is True
    assert res["safety_passed"] is True


def test_matrix_4_cargo_ferry(base_synth_state: EconomicState):
    """4. Cargo Ferry activation pipeline."""
    detector = CargoFerryDetector()
    crop_mock = type("CropMock", (), {
        "crop_type": "MELON", "position": (2, 3), "is_mature": True, "growth_stage": 4, "max_growth": 4
    })()
    base_synth_state.farm.crops = [crop_mock]
    opps = detector.detect(base_synth_state)
    assert len(opps) > 0

    baseline_act = {"farmer": ["PASS"], "hands": [["PASS"]], "market": []}
    res = run_activation_pipeline(opps[0], base_synth_state, baseline_act, {"CARGO_FERRY"})
    assert res["candidate_generated"] is True
    assert res["patch_generated"] is True
    assert res["exact_simulation_reached"] is True
    assert res["safety_passed"] is True


def test_matrix_5_town_cycle(base_synth_state: EconomicState):
    """5. Town Cycle activation pipeline."""
    detector = TownCycleSignalDetector()
    baseline_act = {"farmer": ["PASS"], "hands": [["PASS"]], "market": [["SELL", "STRAWBERRY", 2]]}
    opps = detector.detect(base_synth_state, baseline_act)
    assert len(opps) > 0

    res = run_activation_pipeline(opps[0], base_synth_state, baseline_act, {"TOWN_CYCLE"})
    assert res["candidate_generated"] is True
    assert res["patch_generated"] is True
    assert res["exact_simulation_reached"] is True
    assert res["safety_passed"] is True


def test_matrix_6_production_arbitrage(base_synth_state: EconomicState):
    """6. Production Arbitrage activation pipeline."""
    detector = ProductionArbitrageDetector()
    opps = detector.detect(base_synth_state)
    assert len(opps) > 0

    baseline_act = {"farmer": ["PASS"], "hands": [["PASS"]], "market": []}
    res = run_activation_pipeline(opps[0], base_synth_state, baseline_act, {"PRODUCTION_ARBITRAGE"})
    assert res["candidate_generated"] is True
    assert res["patch_generated"] is True
    assert res["exact_simulation_reached"] is True
    assert res["safety_passed"] is True


def test_matrix_7_shop_arbitrage(base_synth_state: EconomicState):
    """7. Shop Arbitrage activation pipeline."""
    base_synth_state.step = 66  # 6 steps to 72 unlock
    detector = ShopArbitrageDetector()
    opps = detector.detect(base_synth_state)
    assert len(opps) > 0

    baseline_act = {"farmer": ["PASS"], "hands": [["PASS"]], "market": []}
    res = run_activation_pipeline(opps[0], base_synth_state, baseline_act, {"SHOP_ARBITRAGE"})
    assert res["candidate_generated"] is True
    assert res["patch_generated"] is True
    assert res["exact_simulation_reached"] is True
    assert res["safety_passed"] is True


def test_matrix_8_terminal_conversion(base_synth_state: EconomicState):
    """8. Terminal Conversion activation pipeline."""
    base_synth_state.step = 700
    base_synth_state.farm.shed_inventory["WHEAT"] = 4
    detector = TerminalConversionDetector()
    opps = detector.detect(base_synth_state)
    assert len(opps) > 0

    baseline_act = {"farmer": ["PASS"], "hands": [["PASS"]], "market": []}
    res = run_activation_pipeline(opps[0], base_synth_state, baseline_act, {"TERMINAL_CONVERSION"})
    assert res["candidate_generated"] is True
    assert res["patch_generated"] is True
    assert res["exact_simulation_reached"] is True
    assert res["safety_passed"] is True


def test_matrix_9_emergency_feed_purchase(base_synth_state: EconomicState):
    """9. Emergency Feed Purchase / Recovery activation pipeline."""
    # Place a cow needing feed with 0 wheat in inventory
    base_synth_state.farm.shed_inventory["WHEAT"] = 0
    base_synth_state.farm.tiles[2][2] = {
        "kind": "PASTURE", "animal": "COW", "subtype": "COW", "animal_id": "COW_0",
        "consecutive_unfed": 1, "fed_today": False, "cared_today": False, "placed_day": 0
    }
    detector = ResourceOpportunityAnalyzer()
    opps = detector.analyze(base_synth_state, [])
    feed_opps = [o for o in opps if o.candidate_transformation_family == "EMERGENCY_FEED_PURCHASE"]
    assert len(feed_opps) > 0

    baseline_act = {"farmer": ["PASS"], "hands": [["PASS"]], "market": []}
    res = run_activation_pipeline(feed_opps[0], base_synth_state, baseline_act, {"EMERGENCY_FEED_PURCHASE"})
    assert res["candidate_generated"] is True
    assert res["patch_generated"] is True
    assert res["exact_simulation_reached"] is True
    assert res["safety_passed"] is True


def test_matrix_10_market_timing_opponent_preemption(base_synth_state: EconomicState):
    """10. Dependency-Aware Market Timing / Opponent Preemption activation pipeline."""
    detector = MarketOpportunityAnalyzer()
    # Baseline action has buy seed followed by sell
    baseline_act = {
        "farmer": ["PASS"],
        "hands": [["PASS"]],
        "market": [["BUY_SEED", "WHEAT", 1], ["SELL", "WHEAT", 2]]
    }
    opps = detector.analyze(base_synth_state, [], baseline_act)
    timing_opps = [o for o in opps if o.candidate_transformation_family == "DEPENDENCY_AWARE_MARKET_TIMING"]
    assert len(timing_opps) > 0

    res = run_activation_pipeline(timing_opps[0], base_synth_state, baseline_act, {"DEPENDENCY_AWARE_MARKET_TIMING"})
    assert res["candidate_generated"] is True
    assert res["patch_generated"] is True
    assert res["exact_simulation_reached"] is True
    assert res["safety_passed"] is True
