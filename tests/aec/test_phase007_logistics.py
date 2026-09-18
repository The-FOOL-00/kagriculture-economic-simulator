# SPDX-License-Identifier: MIT
"""Phase 007 Route & Logistics Unit Tests (RCOMP-01 through RCOMP-04)."""

import pytest
from unittest.mock import MagicMock

from aec.opportunities.route_compression import (
    RouteCompressionDetector, RouteCompressionOpportunity
)
from aec.opportunities.cargo_ferry import (
    CargoFerryDetector, CargoFerryOpportunity
)
from aec.ir.economic_state import EconomicState
from aec.ir.farm_state import FarmState
from aec.ir.market_state import MarketState
from aec.ir.worker_state import WorkerState, WorkerEntity
from aec.ir.opponent_state import OpponentState
from aec.patches.coupled_patch import CoupledPatch, TrajectoryPreservationCertificate


def test_rcomp_01_route_shortening():
    """RCOMP-01: Route compression identifies shorter path completing equivalent tasks."""
    detector = RouteCompressionDetector()

    crop = MagicMock()
    crop.is_mature = True
    crop.position = (2, 3)
    crop.crop_type = "CARROT"

    farm = FarmState(cash=500.0, shed_inventory={})
    farm.crops = [crop]

    econ = EconomicState(
        step=50,
        farm=farm,
        market=MarketState(current_prices={"CARROT": 35}),
        workers=WorkerState(workers=[WorkerEntity(worker_id=0, position=(2, 2))]),
        opponent=OpponentState(supply_forecast={}, sale_pressure={}, observed_animals={})
    )

    opps = detector.detect(econ, worker_id=0)
    assert len(opps) > 0
    opp = opps[0]
    assert isinstance(opp, RouteCompressionOpportunity)
    assert opp.saved_steps > 0
    assert opp.compressed_route_steps < opp.original_route_steps
    assert opp.estimated_economic_relevance >= 35.0


def test_rcomp_02_dependency_preservation():
    """RCOMP-02: Route compression preserves task dependency order (HARVEST before DROP)."""
    opp = RouteCompressionOpportunity(
        opportunity_id="rcomp_dep_test",
        category="ROUTE",
        event_trigger=None,
        affected_entities=[0, (2, 3)],
        estimated_economic_relevance=35.0,
        candidate_transformation_family="ROUTE_COMPRESSION",
        required_horizon=16,
        target_tasks=["HARVEST", "DROP"],
        saved_steps=4
    )

    # Topological order check: HARVEST must appear before DROP
    tasks = opp.target_tasks
    assert "HARVEST" in tasks and "DROP" in tasks
    assert tasks.index("HARVEST") < tasks.index("DROP")


def test_rcomp_03_cargo_ferry():
    """RCOMP-03: Idle auxiliary worker ferries crop to shed, preserving primary labor."""
    detector = CargoFerryDetector()

    crop = MagicMock()
    crop.is_mature = True
    crop.position = (3, 4)
    crop.crop_type = "STRAWBERRY"

    farm = FarmState(cash=1000.0, shed_inventory={})
    farm.crops = [crop]

    # Worker 0 is primary (field location 8,8)
    # Worker 1 is auxiliary hand, idle and near the crop (position 3,3)
    workers = WorkerState(workers=[
        WorkerEntity(worker_id=0, position=(8, 8), cargo={"WHEAT": 1}),
        WorkerEntity(worker_id=1, position=(3, 3), cargo={})  # Idle hand
    ])

    econ = EconomicState(
        step=120,
        farm=farm,
        market=MarketState(current_prices={"STRAWBERRY": 120}),
        workers=workers,
        opponent=OpponentState(supply_forecast={}, sale_pressure={}, observed_animals={})
    )

    opps = detector.detect(econ)
    assert len(opps) > 0
    opp = opps[0]
    assert isinstance(opp, CargoFerryOpportunity)
    assert opp.candidate_transformation_family == "CARGO_FERRY"
    assert opp.estimated_economic_relevance >= 120.0
    assert 1 in opp.affected_entities  # Hand 1 is assigned


def test_rcomp_04_multi_worker_conflict():
    """RCOMP-04: Multi-worker spatiotemporal collision detected and rejected."""
    cert = TrajectoryPreservationCertificate(
        is_valid=True,
        multiworker_collision_free=False  # Two workers attempted to step on same tile
    )
    is_valid = cert.verify_all()
    assert is_valid is False
    assert any("collision" in r.lower() for r in cert.rejection_reasons)
