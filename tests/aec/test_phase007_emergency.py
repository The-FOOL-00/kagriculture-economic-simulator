# SPDX-License-Identifier: MIT
"""Phase 007 Emergency Recovery Unit Tests (EMR-01 through EMR-04)."""

import pytest
from unittest.mock import MagicMock

from aec.opportunities.emergency import (
    EmergencyRecoveryDetector,
    EmergencyRecoveryOpportunity,
    EmergencyThreatType
)
from aec.ir.economic_state import EconomicState
from aec.ir.farm_state import FarmState
from aec.ir.market_state import MarketState
from aec.ir.worker_state import WorkerState, WorkerEntity
from aec.ir.opponent_state import OpponentState
from aec.opportunities.registry import OpportunityRegistry


def test_emr_01_causal_rescue():
    """EMR-01: Imminent animal starvation triggers targeted causal rescue opportunity."""
    detector = EmergencyRecoveryDetector()

    cow = MagicMock()
    cow.turns_to_starve = 8
    cow.animal_type = "COW"

    farm = FarmState(cash=800.0, shed_inventory={})
    farm.animals = [cow]

    econ = EconomicState(
        step=100,
        farm=farm,
        market=MarketState(current_prices={"MILK": 160}),
        workers=WorkerState(workers=[WorkerEntity(worker_id=0, position=(5, 5))]),
        opponent=OpponentState()
    )

    opps = detector.detect(econ)
    assert len(opps) > 0
    opp = opps[0]
    assert isinstance(opp, EmergencyRecoveryOpportunity)
    assert opp.threat_type == EmergencyThreatType.LIVESTOCK_STARVATION
    assert opp.threatened_value == 400.0  # Cow asset value
    assert opp.urgency_steps == 8
    assert opp.rescue_action_family == "EMERGENCY_FEED"


def test_emr_02_no_arbitrary_buffer():
    """EMR-02: Evaluates exact causal deficit without arbitrary $150 buffer."""
    detector = EmergencyRecoveryDetector()

    farm = FarmState(cash=150.0, shed_inventory={})
    # Step 20 -> 23 - (20 % 24) = 3 steps to night
    # 2 hired hands -> wages due = $200
    # Deficit = $200 - $150 = $50 exactly
    workers = WorkerState(workers=[
        WorkerEntity(worker_id=0, position=(5, 5)),
        WorkerEntity(worker_id=1, position=(2, 2)),
        WorkerEntity(worker_id=2, position=(3, 3))
    ])

    econ = EconomicState(
        step=20,
        farm=farm,
        market=MarketState(current_prices={}),
        workers=workers,
        opponent=OpponentState()
    )

    opps = detector.detect(econ)
    assert len(opps) > 0
    opp = opps[0]
    assert opp.threat_type == EmergencyThreatType.CRITICAL_CASH_INSOLVENCY
    assert opp.threatened_value == 200.0  # Exact wage obligation
    assert opp.urgency_steps == 3


def test_emr_03_obligation_preservation():
    """EMR-03: When cash is fully solvent, no emergency opportunity fires."""
    detector = EmergencyRecoveryDetector()

    farm = FarmState(cash=1000.0, shed_inventory={})  # Plentiful cash
    workers = WorkerState(workers=[
        WorkerEntity(worker_id=0, position=(5, 5)),
        WorkerEntity(worker_id=1, position=(2, 2))
    ])

    econ = EconomicState(
        step=20,
        farm=farm,
        market=MarketState(current_prices={}),
        workers=workers,
        opponent=OpponentState()
    )

    opps = detector.detect(econ)
    assert len(opps) == 0  # No crisis, zero false alarm


def test_emr_04_exact_counterfactual():
    """EMR-04: Emergency recovery requires exact counterfactual certification in registry."""
    reg = OpportunityRegistry.default_registry()
    spec = reg.get_spec("EMERGENCY_RECOVERY")
    assert spec is not None
    assert spec.counterfactual_required is True
    assert spec.is_live_eligible is False  # Must remain quarantined until empirical proof
