# SPDX-License-Identifier: MIT
"""Unit tests for Phase 020 Diagnostic Transformation Library."""

import copy
import pytest
from aec.ir.economic_state import EconomicState
from aec.ir.farm_state import FarmState
from aec.ir.market_state import MarketState
from aec.ir.opponent_state import OpponentState
from aec.ir.worker_state import WorkerEntity, WorkerState
from aec.opportunities.diagnostic_transformations import (
    DiagnosticTransformationGenerator,
    DiagnosticEvaluator,
    TransformationPrimitive,
    OpportunityFamily,
    BackboneDivergenceClass,
)


def create_mock_econ_state(step: int = 100, cash: float = 1200.0) -> EconomicState:
    workers = [
        WorkerEntity(worker_id=0, position=(4, 4), task="PASS", cargo={}),
        WorkerEntity(worker_id=1, position=(4, 4), task="PASS", cargo={}),
    ]
    tiles = [[{"kind": "SOIL"} for _ in range(10)] for _ in range(10)]
    farm = FarmState(
        cash=cash,
        tiles=tiles,
        shed_inventory={"WHEAT": 20, "CARROT": 10},
    )
    market = MarketState(
        current_prices={"WHEAT": 25.0, "CARROT": 30.0, "FERTILIZER": 15.0},
        steps_to_town_tick=12,
    )
    opp = OpponentState(supply_forecast={"WHEAT": 0}, sale_pressure={}, observed_animals={})
    return EconomicState(
        step=step,
        day=step // 24,
        hour=step % 24,
        farm=farm,
        market=market,
        workers=WorkerState(workers=workers),
        opponent=opp,
    )


def test_transformation_generation_and_tranche_tagging():
    """Verify that generator produces valid candidates and strictly tags tranche actions."""
    gen = DiagnosticTransformationGenerator()
    econ_state = create_mock_econ_state()

    base_action = {
        "farmer": ["MOVE", "NORTH"],
        "hands": [["PASS"]],
        "market": [["BUY", "FERTILIZER", 2], ["SELL", "CARROT", 5]],
    }
    continuation = [
        {"farmer": ["PASS"], "hands": [["PASS"]], "market": [["BUY", "WHEAT", 5]]}
    ]

    candidates = gen.generate_candidates(econ_state, base_action, continuation)
    assert len(candidates) > 0

    # Verify tranche tagging: any candidate selling held wheat earlier must have is_tranche_related = True
    tranche_candidates = [c for c in candidates if c.is_tranche_related]
    non_tranche_candidates = [c for c in candidates if not c.is_tranche_related]

    assert len(tranche_candidates) >= 1
    for tc in tranche_candidates:
        assert tc.family == OpportunityFamily.MARKET_TIMING
        assert tc.patch.mechanism_family == "AUTONOMOUS_TRANCHE_ORDER_SYNTHESIZER"

    # Non-tranche candidates must NOT be autonomous tranche synthesizers
    for ntc in non_tranche_candidates:
        assert ntc.patch.mechanism_family != "AUTONOMOUS_TRANCHE_ORDER_SYNTHESIZER"
        assert ntc.primitive in TransformationPrimitive


def test_market_order_swap_candidate():
    """Verify SWAP_ACTION_ORDER reorders sells before buys."""
    gen = DiagnosticTransformationGenerator()
    econ_state = create_mock_econ_state()

    # Base action has BUY before SELL
    base_action = {
        "farmer": ["PASS"],
        "hands": [["PASS"]],
        "market": [["BUY", "FERTILIZER", 2], ["SELL", "CARROT", 5]],
    }
    candidates = gen.generate_candidates(econ_state, base_action)
    swap_cand = next((c for c in candidates if c.primitive == TransformationPrimitive.SWAP_ACTION_ORDER), None)
    assert swap_cand is not None
    assert swap_cand.is_tranche_related is False

    patched_act = swap_cand.patch.apply(base_action)
    assert patched_act["market"][0][0] == "SELL"
    assert patched_act["market"][1][0] == "BUY"


def test_worker_reassignment_candidate():
    """Verify REASSIGN_WORKER creates co-located worker delegation."""
    gen = DiagnosticTransformationGenerator()
    econ_state = create_mock_econ_state()

    base_action = {
        "farmer": ["TILL"],
        "hands": [["PASS"]],
        "market": [],
    }
    candidates = gen.generate_candidates(econ_state, base_action)
    reassign_cand = next((c for c in candidates if c.primitive == TransformationPrimitive.REASSIGN_WORKER), None)
    assert reassign_cand is not None
    assert reassign_cand.family == OpportunityFamily.WORKER_ALLOCATION
    assert reassign_cand.is_tranche_related is False

    patched = reassign_cand.patch.apply(base_action)
    assert patched["farmer"] == ["PASS"]
    assert patched["hands"][0] == ["TILL"]


def test_diagnostic_evaluator_stage1_probe():
    """Verify that Stage 1 local evaluator computes immediate directional signals."""
    evaluator = DiagnosticEvaluator()
    econ_state = create_mock_econ_state()
    gen = DiagnosticTransformationGenerator()

    base_action = {
        "farmer": ["TILL"],
        "hands": [["PASS"]],
        "market": [["BUY", "FERTILIZER", 2]],
    }
    candidates = gen.generate_candidates(econ_state, base_action)
    for c in candidates:
        sig = evaluator.evaluate_stage1_local(econ_state, c, base_action)
        assert isinstance(sig, float)
        assert c.estimated_local_signal == sig
