# SPDX-License-Identifier: MIT
"""Phase 007 Arbitrage Unit Tests (ARB-01 through ARB-05)."""

import pytest

from aec.opportunities.arbitrage import (
    ProductionArbitrageDetector,
    ProductionArbitrageOpportunity,
    ShopArbitrageDetector,
    ShopArbitrageOpportunity
)
from aec.ir.economic_state import EconomicState
from aec.ir.farm_state import FarmState
from aec.ir.market_state import MarketState
from aec.ir.worker_state import WorkerState, WorkerEntity
from aec.ir.opponent_state import OpponentState


def test_arb_01_input_production_sale():
    """ARB-01: Full production graph cash -> input -> production -> output -> sale evaluated."""
    detector = ProductionArbitrageDetector()

    # Step 100, cash $800, high strawberry market price ($180)
    econ = EconomicState(
        step=100,
        farm=FarmState(cash=800.0, shed_inventory={}),
        market=MarketState(current_prices={"STRAWBERRY": 180, "CARROT": 35, "TOMATO": 60, "WHEAT": 25, "MELON": 250}),
        workers=WorkerState(workers=[WorkerEntity(worker_id=0, position=(5, 5))]),
        opponent=OpponentState()
    )

    opps = detector.detect(econ, min_net_margin=40.0)
    assert len(opps) > 0
    straw_opp = next((o for o in opps if o.output_item == "STRAWBERRY"), None)
    assert straw_opp is not None
    assert straw_opp.input_cost > 0
    assert straw_opp.expected_gross_revenue == 180.0
    assert straw_opp.net_projected_profit == straw_opp.expected_gross_revenue - straw_opp.input_cost - 10.0
    assert straw_opp.net_projected_profit > 40.0


def test_arb_02_liquidity_constraint():
    """ARB-02: Arbitrage respects upfront cash and liquidity cushion."""
    detector = ProductionArbitrageDetector()

    # Cash is only $50 (cannot afford seed + $100 safety cushion)
    econ = EconomicState(
        step=100,
        farm=FarmState(cash=50.0, shed_inventory={}),
        market=MarketState(current_prices={"STRAWBERRY": 180, "MELON": 300}),
        workers=WorkerState(workers=[WorkerEntity(worker_id=0, position=(5, 5))]),
        opponent=OpponentState()
    )

    opps = detector.detect(econ)
    assert len(opps) == 0  # Rejects all candidates due to insufficient liquidity


def test_arb_03_terminal_cutoff():
    """ARB-03: Production pipeline that cannot mature before step 718 is rejected."""
    detector = ProductionArbitrageDetector()

    # Step 680 (late endgame, strawberry requires 3 days = 72 turns -> 680 + 72 + 8 = 760 > 718)
    econ = EconomicState(
        step=680,
        farm=FarmState(cash=2000.0, shed_inventory={}),
        market=MarketState(current_prices={"STRAWBERRY": 250, "MELON": 400}),
        workers=WorkerState(workers=[WorkerEntity(worker_id=0, position=(5, 5))]),
        opponent=OpponentState()
    )

    opps = detector.detect(econ)
    assert len(opps) == 0  # Strict cutoff: no impossible production cycles


def test_arb_04_labor_cost():
    """ARB-04: Labor requirement accounts for worker time displacement."""
    detector = ProductionArbitrageDetector()

    econ = EconomicState(
        step=100,
        farm=FarmState(cash=1000.0, shed_inventory={}),
        market=MarketState(current_prices={"CARROT": 45}),
        workers=WorkerState(workers=[WorkerEntity(worker_id=0, position=(5, 5))]),
        opponent=OpponentState()
    )

    opps = detector.detect(econ, min_net_margin=0.0)
    carrot_opp = next((o for o in opps if o.output_item == "CARROT"), None)
    if carrot_opp:
        # Net profit should explicitly deduct labor cost ($10) in addition to seed cost
        assert carrot_opp.net_projected_profit == carrot_opp.expected_gross_revenue - carrot_opp.input_cost - 10.0


def test_arb_05_market_timing():
    """ARB-05: Shop arbitrage links to 72-step town unlock windows."""
    detector = ShopArbitrageDetector()

    # Step 65 (7 turns before step 72 unlock)
    econ = EconomicState(
        step=65,
        farm=FarmState(cash=1000.0, shed_inventory={"CARROT": 10}),
        market=MarketState(current_prices={"CARROT": 35, "TOMATO": 60, "WHEAT": 25}),
        workers=WorkerState(workers=[WorkerEntity(worker_id=0, position=(5, 5))]),
        opponent=OpponentState()
    )

    opps = detector.detect(econ)
    assert len(opps) > 0
    opp = opps[0]
    assert isinstance(opp, ShopArbitrageOpportunity)
    assert opp.unlock_step == 72
    assert opp.expected_margin > 0
    assert opp.required_horizon == (72 - 65) + 6
