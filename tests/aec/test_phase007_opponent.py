# SPDX-License-Identifier: MIT
"""Phase 007 Opponent Pressure Unit Tests (OPP-01 through OPP-05)."""

import pytest
from aec.counterfactual.opponent_pressure import (
    ContinuousOpponentPressureAnalyzer,
    OpponentPressureState,
    OpponentPressureModel
)
from aec.ir.economic_state import EconomicState
from aec.ir.farm_state import FarmState
from aec.ir.market_state import MarketState
from aec.ir.worker_state import WorkerState, WorkerEntity
from aec.ir.opponent_state import OpponentState
from aec.safety.certificate import SafetyCertificate, SafetyInvariantChecker
from aec.patches.coupled_patch import CoupledPatch


def test_opp_01_pressure_extraction():
    """OPP-01: Correctly extract continuous pressure signals from opponent observations."""
    analyzer = ContinuousOpponentPressureAnalyzer()

    opp = OpponentState(
        supply_forecast={"STRAWBERRY": 4.0, "MILK": 2.0},
        sale_pressure={"STRAWBERRY": 0.8, "MILK": 0.3},
        observed_animals={"COW": 2},
        market_collision_risk={"STRAWBERRY": 0.6},
        cash=1200.0,
        observed_mature_crops={"STRAWBERRY": 4}
    )

    econ = EconomicState(
        step=650,  # Terminal window approaching
        farm=FarmState(cash=800.0),
        market=MarketState(current_prices={"STRAWBERRY": 120, "MILK": 160}),
        workers=WorkerState(workers=[WorkerEntity(worker_id=0, position=(5, 5))]),
        opponent=opp
    )

    pressure = analyzer.analyze(econ)
    assert isinstance(pressure, OpponentPressureState)
    assert pressure.observed_cash == 1200.0
    assert pressure.sale_pressure.get("STRAWBERRY") == 0.8
    assert pressure.price_pressure.get("STRAWBERRY") > 0.0
    assert pressure.timing_pressure > 0.5
    assert pressure.terminal_pressure > 0.0
    assert pressure.shared_resource_collision.get("STRAWBERRY") == 0.6


def test_opp_02_pressure_change_detection():
    """OPP-02: Pressure change detection reflects delta in opponent market activity."""
    analyzer = ContinuousOpponentPressureAnalyzer()

    opp_prev = OpponentState(
        supply_forecast={},
        sale_pressure={},
        observed_animals={},
        cash=500.0
    )
    prev_econ = EconomicState(
        step=100,
        farm=FarmState(cash=800.0),
        workers=WorkerState(workers=[WorkerEntity(worker_id=0, position=(5, 5))]),
        opponent=opp_prev
    )

    # Opponent suddenly gained $600 from sales
    opp_curr = OpponentState(
        supply_forecast={},
        sale_pressure={},
        observed_animals={},
        cash=1100.0
    )
    curr_econ = EconomicState(
        step=101,
        farm=FarmState(cash=800.0),
        workers=WorkerState(workers=[WorkerEntity(worker_id=0, position=(5, 5))]),
        opponent=opp_curr
    )

    pressure = analyzer.analyze(curr_econ, prev_econ_state=prev_econ)
    # Delta cash = 600 -> high market activity level
    assert pressure.market_activity_level >= 0.8
    assert pressure.confidence >= 0.8


def test_opp_03_opponent_uncertainty():
    """OPP-03: Incomplete or uncertain opponent observations produce low confidence."""
    analyzer = ContinuousOpponentPressureAnalyzer()

    econ = EconomicState(
        step=50,
        farm=FarmState(cash=800.0),
        workers=WorkerState(workers=[WorkerEntity(worker_id=0, position=(5, 5))]),
        opponent=None  # Opponent completely unobserved
    )

    pressure = analyzer.analyze(econ)
    assert pressure.confidence <= 0.2
    assert pressure.market_activity_level == 0.0


def test_opp_04_market_collision():
    """OPP-04: Detects impending market collision on shared goods."""
    pressure = OpponentPressureState(
        shared_resource_collision={"STRAWBERRY": 0.75, "MELON": 0.1},
        confidence=0.8
    )

    assert pressure.has_market_collision("STRAWBERRY") is True
    assert pressure.has_market_collision("MELON") is False
    assert pressure.should_accelerate_opportunity("STRAWBERRY") is True


def test_opp_05_no_override_of_safety():
    """OPP-05: Opponent pressure never bypasses safety certificate or invariants (§9)."""
    # Maximal opponent pressure across all dimensions
    extreme_pressure = OpponentPressureState(
        market_activity_level=1.0,
        timing_pressure=1.0,
        terminal_pressure=1.0,
        sale_pressure={"STRAWBERRY": 1.0},
        shared_resource_collision={"STRAWBERRY": 1.0},
        confidence=1.0
    )

    # An unsafe candidate patch that attempts to sell items we do not possess
    unsafe_patch = CoupledPatch(
        patch_id="unsafe_patch",
        source_opportunity_id="opp_extreme",
        worker_ids=[0],
        mechanism_family="OPPONENT_PREEMPT_SELL",
        market_mutations=[["SELL", "STRAWBERRY", 50, 100]],  # We have 0 strawberries
        expected_horizon=4,
        rationale="Desperate frontrunning"
    )

    econ = EconomicState(
        step=500,
        farm=FarmState(cash=200.0, shed_inventory={"STRAWBERRY": 0}),
        market=MarketState(current_prices={"STRAWBERRY": 120}),
        workers=WorkerState(workers=[WorkerEntity(worker_id=0, position=(5, 5))]),
        opponent=OpponentState(supply_forecast={}, sale_pressure={}, observed_animals={})
    )

    checker = SafetyInvariantChecker()
    is_safe, cert = checker.verify_patch_safety(unsafe_patch, econ)

    # Must reject despite extreme pressure
    assert is_safe is False
    assert cert.is_certified is False
    assert "inventory" in cert.failure_reason.lower() or "deficit" in cert.failure_reason.lower() or len(cert.violations) > 0
