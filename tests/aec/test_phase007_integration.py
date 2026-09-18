# SPDX-License-Identifier: MIT
"""Phase 007 Multi-Mechanism Integration Tests (§36, §37)."""

import pytest
import copy

from aec.patches.coupled_patch import CoupledPatch
from aec.patches.composition import PatchCompositionEngine, CompositionRelation
from aec.funnel.candidate_funnel import OpportunityCandidateFunnel, InferenceBudget
from aec.macro.macro_controller import MacroController, MacroStrategy, MacroPosture, CashPosture, MarketPosture
from aec.meta.meta_policy import MetaOrchestrator, AECMode
from aec.counterfactual.opponent_pressure import OpponentPressureState
from aec.ir.economic_state import EconomicState
from aec.ir.farm_state import FarmState
from aec.ir.market_state import MarketState
from aec.ir.worker_state import WorkerState, WorkerEntity
from aec.ir.opponent_state import OpponentState
from aec.opportunities.base import Opportunity


def test_int_01_harvest_and_market_timing():
    """Scenario 1: Harvest (worker-based) and Market Timing (market-only) fire simultaneously.
    
    Composition engine confirms they operate on disjoint systems (PARALLEL) and can co-exist.
    """
    engine = PatchCompositionEngine()

    p_harvest = CoupledPatch(
        patch_id="patch_harvest",
        source_opportunity_id="opp_harvest",
        worker_ids=[0],
        mechanism_family="DYNAMIC_SHADOW_HARVEST",
        actions=[{"farmer": ["HARVEST"]}],
        rationale="Harvest strawberry"
    )

    p_market = CoupledPatch(
        patch_id="patch_market",
        source_opportunity_id="opp_market",
        worker_ids=[],  # No worker used
        mechanism_family="DEPENDENCY_AWARE_MARKET_TIMING",
        market_mutations=[["SELL", "WHEAT", 5, 25]],
        rationale="Frontload wheat sale"
    )

    report = engine.analyze_pair(p_harvest, p_market)
    assert report.compatible is True
    assert report.relation == CompositionRelation.PARALLEL


def test_int_02_harvest_and_cargo_ferry():
    """Scenario 2: Harvest (Worker 0) and Cargo Ferry (Worker 1) fire simultaneously.
    
    Workers are disjoint and paths do not collide: PARALLEL composition approved.
    """
    engine = PatchCompositionEngine()

    p_primary = CoupledPatch(
        patch_id="patch_primary_harvest",
        source_opportunity_id="opp_prim",
        worker_ids=[0],
        mechanism_family="DYNAMIC_SHADOW_HARVEST",
        actions=[{"farmer": ["HARVEST"]}],
        rationale="Primary farmer harvest"
    )

    p_aux = CoupledPatch(
        patch_id="patch_aux_ferry",
        source_opportunity_id="opp_aux",
        worker_ids=[1],
        mechanism_family="CARGO_FERRY",
        actions=[{"hands": [["MOVE_UP"]]}],
        rationale="Auxiliary hand ferry"
    )

    report = engine.analyze_pair(p_primary, p_aux)
    assert report.compatible is True
    assert report.relation == CompositionRelation.PARALLEL


def test_int_03_harvest_and_terminal_sweep_contention():
    """Scenario 3: Harvest and Terminal Sweep contest the same worker.
    
    Composition engine detects contention and dominance: rejects simultaneous double-execution.
    """
    engine = PatchCompositionEngine()

    # Terminal sweep has higher value ($250 vs $60) in fewer/equal steps
    p_routine_harvest = CoupledPatch(
        patch_id="patch_routine",
        source_opportunity_id="opp_routine",
        worker_ids=[0],
        mechanism_family="DYNAMIC_SHADOW_HARVEST",
        economic_effect=60.0,
        actions=[{"farmer": ["HARVEST"]}],
        rationale="Routine harvest"
    )

    p_terminal_sweep = CoupledPatch(
        patch_id="patch_terminal",
        source_opportunity_id="opp_term",
        worker_ids=[0],
        mechanism_family="TERMINAL_HARVEST_SWEEP",
        economic_effect=250.0,
        actions=[{"farmer": ["HARVEST"]}],
        rationale="High-value terminal melon harvest"
    )

    report = engine.analyze_pair(p_terminal_sweep, p_routine_harvest)
    assert report.compatible is False
    assert report.relation in (CompositionRelation.DOMINATES, CompositionRelation.MUTUALLY_EXCLUSIVE)


def test_int_04_market_timing_and_opponent_pressure():
    """Scenario 4: Opponent sale pressure accelerates our market timing order.
    
    META orchestrator prioritizes preemptive sale when rival dump pressure is high.
    """
    meta = MetaOrchestrator(mode=AECMode.META_MODE)

    pressure = OpponentPressureState(
        sale_pressure={"STRAWBERRY": 0.85},
        timing_pressure=0.90,
        shared_resource_collision={"STRAWBERRY": 0.70},
        confidence=0.85
    )

    econ = EconomicState(
        step=150,
        farm=FarmState(cash=800.0, shed_inventory={"STRAWBERRY": 10}),
        market=MarketState(current_prices={"STRAWBERRY": 120}),
        workers=WorkerState(workers=[WorkerEntity(worker_id=0, position=(5, 5))]),
        opponent=OpponentState(observed_cash=1500.0)
    )

    decision = meta.orchestrate(pressure, econ)
    assert decision.effective_mode == AECMode.META_MODE
    assert "OPPONENT_PREEMPT_SELL" in decision.authorized_families
    # Check strategic priority increased for preemptive sell
    assert decision.strategic_priorities.get("OPPONENT_PREEMPT_SELL", 0.0) > 0.0


def test_int_05_route_compression_and_harvest_contention():
    """Scenario 5: Route compression and direct harvest compete for the same worker.
    
    Candidate funnel ranks and dominance-prunes duplicate actions for Worker 0.
    """
    funnel = OpportunityCandidateFunnel(InferenceBudget(max_exact_simulations=2))

    econ = EconomicState(
        step=100,
        farm=FarmState(cash=500.0, shed_inventory={}),
        market=MarketState(current_prices={"CARROT": 35}),
        workers=WorkerState(workers=[WorkerEntity(worker_id=0, position=(2, 2))]),
        opponent=OpponentState()
    )

    opp1 = Opportunity(
        opportunity_id="opp_harvest_direct",
        category="LABOR",
        event_trigger=None,
        affected_entities=[0, (2, 3)],
        estimated_economic_relevance=35.0,
        candidate_transformation_family="DYNAMIC_SHADOW_HARVEST",
        required_horizon=8
    )

    opp2 = Opportunity(
        opportunity_id="opp_route_compressed",
        category="ROUTE",
        event_trigger=None,
        affected_entities=[0, (2, 3)],
        estimated_economic_relevance=70.0,  # Compressed path reaps double value
        candidate_transformation_family="ROUTE_COMPRESSION",
        required_horizon=12
    )

    survivors, telem = funnel.filter_candidates([opp1, opp2], econ)
    # Dominance pruning on same worker and same target position retains only the superior one
    assert len(survivors) == 1
    assert survivors[0].opportunity_id == "opp_route_compressed"


def test_int_06_emergency_recovery_takes_precedence():
    """Scenario 6: Emergency animal starvation takes precedence over routine labor.
    
    Emergency opportunity receives top strategic priority in candidate funnel.
    """
    funnel = OpportunityCandidateFunnel(InferenceBudget(max_exact_simulations=1))

    econ = EconomicState(
        step=200,
        farm=FarmState(cash=600.0, shed_inventory={}),
        market=MarketState(current_prices={"MILK": 160}),
        workers=WorkerState(workers=[WorkerEntity(worker_id=0, position=(5, 5))]),
        opponent=OpponentState()
    )

    routine_opp = Opportunity(
        opportunity_id="routine_wheat",
        category="LABOR",
        event_trigger=None,
        affected_entities=[0, (1, 1)],
        estimated_economic_relevance=25.0,
        candidate_transformation_family="DYNAMIC_SHADOW_HARVEST",
        required_horizon=6
    )

    emergency_opp = Opportunity(
        opportunity_id="emergency_cow_feed",
        category="RESOURCE",
        event_trigger=None,
        affected_entities=[0, (5, 5)],
        estimated_economic_relevance=400.0,  # Cow asset loss prevention
        candidate_transformation_family="EMERGENCY_RECOVERY",
        required_horizon=8
    )

    survivors, _ = funnel.filter_candidates([routine_opp, emergency_opp], econ)
    assert len(survivors) == 1
    assert survivors[0].opportunity_id == "emergency_cow_feed"


def test_int_07_production_and_market_liquidity_bounds():
    """Scenario 7: Production capex is constrained by macro cash reserve policy.
    
    Ensures capex proposals that drain minimum operating capital are rejected.
    """
    macro = MacroController()
    strat = MacroStrategy(
        posture=MacroPosture.BALANCED_PRODUCTION,
        cash_posture=CashPosture.PRESERVE_CAPITAL,
        market_posture=MarketPosture.PATIENT_CYCLE,
        min_cash_reserve=300.0,
        crop_priorities=["STRAWBERRY"],
        allow_capital_expenditures=True
    )
    macro.set_strategy(strat)

    econ = EconomicState(
        step=100,
        farm=FarmState(cash=450.0, shed_inventory={}),  # $450 - $200 upfront = $250 < $300 min reserve
        market=MarketState(current_prices={"STRAWBERRY": 120}),
        workers=WorkerState(workers=[WorkerEntity(worker_id=0, position=(5, 5))]),
        opponent=OpponentState()
    )

    # Opportunity requiring $200 upfront
    opp = Opportunity(
        opportunity_id="expensive_capex",
        category="RESOURCE",
        event_trigger=None,
        affected_entities=["MELON"],
        estimated_economic_relevance=150.0,
        candidate_transformation_family="PRODUCTION_ARBITRAGE",
        required_horizon=24,
        dependency_info={"upfront_cost": 200.0}
    )

    funnel = OpportunityCandidateFunnel(InferenceBudget(max_exact_simulations=3), macro_controller=macro)
    # Candidate funnel enforces feasibility against macro reserve
    survivors, _ = funnel.filter_candidates([opp], econ)
    # Rejection: $450 - $200 = $250 < $300 minimum reserve
    assert len(survivors) == 0


def test_int_08_full_pipeline_operational_modes():
    """Scenario 8: Pipeline mode switching strictly isolates candidate family authorization."""
    # 1. ROBUST_MODE: Only cleared robust mechanisms
    meta_robust = MetaOrchestrator(mode=AECMode.ROBUST_MODE)
    pressure = OpponentPressureState(confidence=0.9)
    econ = EconomicState(step=100, farm=FarmState(cash=1000.0))

    dec_robust = meta_robust.orchestrate(pressure, econ)
    assert dec_robust.effective_mode == AECMode.ROBUST_MODE
    assert "DYNAMIC_SHADOW_HARVEST" in dec_robust.authorized_families
    assert "OPPONENT_PREEMPT_SELL" not in dec_robust.authorized_families
    assert "SHOP_ARBITRAGE" not in dec_robust.authorized_families

    # 2. META_MODE: Adds opponent-sensitive mechanisms
    meta_meta = MetaOrchestrator(mode=AECMode.META_MODE)
    dec_meta = meta_meta.orchestrate(pressure, econ)
    assert dec_meta.effective_mode == AECMode.META_MODE
    assert "OPPONENT_PREEMPT_SELL" in dec_meta.authorized_families

    # 3. RESEARCH_MODE: Diagnostic exploration across broader candidate sets
    meta_res = MetaOrchestrator(mode=AECMode.RESEARCH_MODE)
    dec_res = meta_res.orchestrate(pressure, econ)
    assert dec_res.effective_mode == AECMode.RESEARCH_MODE
    assert "SHOP_ARBITRAGE" in dec_res.authorized_families
    assert "PRODUCTION_ARBITRAGE" in dec_res.authorized_families
