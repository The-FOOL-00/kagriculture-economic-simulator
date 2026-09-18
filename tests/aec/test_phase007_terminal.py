# SPDX-License-Identifier: MIT
"""Phase 007 Terminal Unit Tests (TERM-01 through TERM-04)."""

import pytest

from aec.terminal.conversion import (
    TerminalConversionDetector,
    TerminalConversionOpportunity
)
from aec.ir.economic_state import EconomicState
from aec.ir.farm_state import FarmState
from aec.ir.market_state import MarketState
from aec.ir.worker_state import WorkerState, WorkerEntity
from aec.ir.opponent_state import OpponentState


def test_term_01_conversion_realization():
    """TERM-01: Terminal conversion yields positive terminal liquidated cash."""
    detector = TerminalConversionDetector()

    # Step 690 (within 680-716 window), 10 wheat in shed
    econ = EconomicState(
        step=690,
        farm=FarmState(cash=1000.0, shed_inventory={"WHEAT": 10}),
        market=MarketState(current_prices={"WHEAT": 25}),
        workers=WorkerState(workers=[
            WorkerEntity(worker_id=0, position=(5, 5)),
            WorkerEntity(worker_id=1, position=(2, 2))
        ]),
        opponent=OpponentState()
    )

    opps = detector.detect(econ)
    assert len(opps) > 0
    opp = opps[0]
    assert isinstance(opp, TerminalConversionOpportunity)
    assert opp.projected_terminal_value == 10 * 25.0
    assert opp.input_units == 10
    assert opp.required_horizon <= (718 - 690)


def test_term_02_terminal_cutoff():
    """TERM-02: Conversions outside terminal window or after step 716 are rejected."""
    detector = TerminalConversionDetector()

    # Mid-game (step 400): Terminal conversion should NOT fire
    econ_mid = EconomicState(
        step=400,
        farm=FarmState(cash=1000.0, shed_inventory={"WHEAT": 10}),
        market=MarketState(current_prices={"WHEAT": 25}),
        workers=WorkerState(workers=[WorkerEntity(worker_id=0, position=(5, 5))]),
        opponent=OpponentState()
    )
    assert len(detector.detect(econ_mid)) == 0

    # Past step 716 (step 717): Cannot complete conversion before cutoff 718
    econ_past = EconomicState(
        step=717,
        farm=FarmState(cash=1000.0, shed_inventory={"WHEAT": 10}),
        market=MarketState(current_prices={"WHEAT": 25}),
        workers=WorkerState(workers=[WorkerEntity(worker_id=0, position=(5, 5))]),
        opponent=OpponentState()
    )
    assert len(detector.detect(econ_past)) == 0


def test_term_03_cargo_liquidation():
    """TERM-03: Cargo liquidation prioritizes auxiliary hands to unburden primary farmer."""
    detector = TerminalConversionDetector()

    econ = EconomicState(
        step=700,
        farm=FarmState(cash=500.0, shed_inventory={"WHEAT": 5}),
        market=MarketState(current_prices={"WHEAT": 20}),
        workers=WorkerState(workers=[
            WorkerEntity(worker_id=0, position=(8, 8)),  # Farmer
            WorkerEntity(worker_id=1, position=(2, 2))   # Hand
        ]),
        opponent=OpponentState()
    )

    opps = detector.detect(econ)
    assert len(opps) > 0
    # Assigned to worker 1 (auxiliary hand) rather than primary farmer
    assert opps[0].worker_id == 1


def test_term_04_unsold_value_rejected():
    """TERM-04: If conversion produces goods with remaining steps < duration, rejected."""
    detector = TerminalConversionDetector()

    # Step 715, rem_steps = 718 - 715 = 3 < 6 required
    econ = EconomicState(
        step=715,
        farm=FarmState(cash=500.0, shed_inventory={"WHEAT": 5}),
        market=MarketState(current_prices={"WHEAT": 20}),
        workers=WorkerState(workers=[WorkerEntity(worker_id=0, position=(5, 5))]),
        opponent=OpponentState()
    )

    opps = detector.detect(econ)
    # Since rem_steps is 3 (< 6 required steps to complete and realize), detector rejects
    assert len(opps) == 0
