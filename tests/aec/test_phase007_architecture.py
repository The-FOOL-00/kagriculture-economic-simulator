# SPDX-License-Identifier: MIT
"""Phase 007 Architecture Unit Tests (A7-01 through A7-08)."""

import pytest
from aec.config import AECConfig, ScientificStatus
from aec.opportunities.registry import OpportunityRegistry, OpportunityFamilySpec
from aec.funnel.candidate_funnel import (
    OpportunityCandidateFunnel, InferenceBudget, FunnelStage
)
from aec.macro.macro_controller import (
    MacroController, MacroStrategy, MacroPosture, CashPosture, MarketPosture
)
from aec.tactical.tactical_planner import (
    TacticalPlanner, TacticalProposal, TacticalCategory
)
from aec.integration.fallback import RobustFallbackPolicy, FallbackReason
from aec.meta.meta_policy import MetaOrchestrator, AECMode
from aec.replanning.event_replanner import (
    EventTriggeredReplanner, ReplanTrigger, ReplanEscalationLevel, ReplanPolicy
)
from aec.ir.economic_state import EconomicState
from aec.ir.farm_state import FarmState
from aec.ir.market_state import MarketState
from aec.ir.worker_state import WorkerState, WorkerEntity
from aec.ir.opponent_state import OpponentState
from aec.opportunities.base import Opportunity
from aec.counterfactual.opponent_pressure import OpponentPressureState


def test_a7_01_registry_completeness():
    """A7-01: Verify that all 14 planned opportunity families are registered."""
    reg = OpportunityRegistry.default_registry()
    families = reg.list_families()
    assert len(families) == 14, f"Expected 14 registered families, found {len(families)}"

    expected = {
        "DEPENDENCY_AWARE_MARKET_TIMING",
        "DYNAMIC_SHADOW_HARVEST",
        "TERMINAL_HARVEST_SWEEP",
        "ROUTE_COMPRESSION",
        "CARGO_FERRY",
        "RESOURCE_CONVERSION",
        "SHOP_ARBITRAGE",
        "PRODUCTION_ARBITRAGE",
        "TERMINAL_CONVERSION",
        "OPPONENT_PREEMPT_SELL",
        "EMERGENCY_RECOVERY",
        "TOWN_CYCLE",
        "TERMINAL_LIQUIDATION",
        "PHASE_SHUTDOWN",
    }
    registered_names = {f.name for f in families}
    assert registered_names == expected, f"Missing families: {expected - registered_names}"

    for spec in families:
        assert isinstance(spec, OpportunityFamilySpec)
        assert spec.worker_requirements in ("PRIMARY_ONLY", "AUXILIARY_ONLY", "ANY", "NONE")
        assert isinstance(spec.scientific_status, ScientificStatus)


def test_a7_02_mechanism_status_isolation():
    """A7-02: Verify quarantine and live-eligibility isolation across layers."""
    reg = OpportunityRegistry.default_registry()
    rc_spec = reg.get_spec("RESOURCE_CONVERSION")
    assert rc_spec is not None
    assert rc_spec.scientific_status == ScientificStatus.QUARANTINED
    assert rc_spec.is_live_eligible is False

    config = AECConfig()
    assert config.is_family_live_eligible("RESOURCE_CONVERSION") is False
    assert config.resource_conversion_enabled is False

    # Foundation cleared family
    assert config.is_family_live_eligible("DEPENDENCY_AWARE_MARKET_TIMING") is True
    assert config.is_family_live_eligible("TERMINAL_LIQUIDATION") is True


def test_a7_03_candidate_funnel_determinism():
    """A7-03: Two runs with identical opportunities produce identical filtered top-K."""
    econ = EconomicState(
        step=100,
        farm=FarmState(cash=500.0, shed_inventory={}),
        market=MarketState(current_prices={"MILK": 10}),
        workers=WorkerState(workers=[WorkerEntity(worker_id=0, position=(5, 5))]),
        opponent=OpponentState(supply_forecast={}, sale_pressure={}, observed_animals={})
    )

    opps = [
        Opportunity(
            opportunity_id=f"opp_{i}",
            category="LABOR",
            event_trigger=None,
            affected_entities=[0, (i, i)],
            estimated_economic_relevance=float(100 - i * 5),
            candidate_transformation_family="DYNAMIC_SHADOW_HARVEST",
            required_horizon=10,
            rationale=f"harvest {i}"
        )
        for i in range(10)
    ]

    funnel1 = OpportunityCandidateFunnel(InferenceBudget(max_exact_simulations=3))
    res1, telem1 = funnel1.filter_candidates(opps, econ)

    funnel2 = OpportunityCandidateFunnel(InferenceBudget(max_exact_simulations=3))
    res2, telem2 = funnel2.filter_candidates(opps, econ)

    assert len(res1) == len(res2) == 3
    assert [o.opportunity_id for o in res1] == [o.opportunity_id for o in res2]
    assert [o.estimated_net_delta for o in res1] == [100.0, 95.0, 90.0]


def test_a7_04_inference_budget():
    """A7-04: Inference budget bounds candidate count and simulation attempts."""
    budget = InferenceBudget(max_exact_simulations=2, max_raw_candidates=5)
    funnel = OpportunityCandidateFunnel(budget)

    econ = EconomicState(
        step=100,
        farm=FarmState(cash=500.0, shed_inventory={}),
        market=MarketState(current_prices={"MILK": 10}),
        workers=WorkerState(workers=[WorkerEntity(worker_id=0, position=(5, 5))]),
        opponent=OpponentState(supply_forecast={}, sale_pressure={}, observed_animals={})
    )

    opps = [
        Opportunity(
            opportunity_id=f"opp_{i}",
            category="LABOR",
            event_trigger=None,
            affected_entities=[0, (i % 5, i % 5)],
            estimated_economic_relevance=float(50 + i),
            candidate_transformation_family="DYNAMIC_SHADOW_HARVEST",
            required_horizon=10,
            rationale=f"test {i}"
        )
        for i in range(20)
    ]

    survivors, telem = funnel.filter_candidates(opps, econ)
    assert len(survivors) <= 2
    assert telem.initial_candidates == 20
    assert telem.final_candidates == len(survivors)


def test_a7_05_macro_tactical_separation():
    """A7-05: Macro controller enforces cash reserve and strategy; tactical cannot override."""
    macro = MacroController()
    strat = MacroStrategy(
        posture=MacroPosture.BALANCED_PRODUCTION,
        cash_posture=CashPosture.PRESERVE_CAPITAL,
        market_posture=MarketPosture.PATIENT_CYCLE,
        min_cash_reserve=200.0,
        crop_priorities=["CARROT"],
        allow_capital_expenditures=True
    )
    macro.set_strategy(strat)

    planner = TacticalPlanner(macro_controller=macro)

    # Proposal that drains cash below 200
    p1 = TacticalProposal(
        proposal_id="prop_1",
        category=TacticalCategory.RESOURCE_CONVERSION,
        mechanism_family="RESOURCE_CONVERSION",
        affected_workers=[0],
        estimated_economic_value=50.0,
        duration_steps=15,
        payload={"upfront_cost": 400.0}
    )

    # If current cash is 450, 450 - 400 = 50 < 200 -> Invalid
    valid, reason = planner.validate_proposal_compatibility(p1, current_cash=450.0)
    assert not valid
    assert "cash reserve" in reason.lower()

    # Proposal with reasonable upfront cost
    p2 = TacticalProposal(
        proposal_id="prop_2",
        category=TacticalCategory.HARVEST,
        mechanism_family="DYNAMIC_SHADOW_HARVEST",
        affected_workers=[0],
        estimated_economic_value=80.0,
        duration_steps=5,
        payload={"upfront_cost": 50.0}
    )
    # 450 - 50 = 400 >= 200 -> Valid
    valid2, _ = planner.validate_proposal_compatibility(p2, current_cash=450.0)
    assert valid2


def test_a7_06_robust_fallback():
    """A7-06: RobustFallbackPolicy safely logs and falls back to baseline."""
    policy = RobustFallbackPolicy()
    assert policy.fallback_count == 0

    rec = policy.record_fallback(
        step=120,
        reason=FallbackReason.RUNTIME_BUDGET_EXCEEDED,
        baseline_action={"worker_0": "MOVE_UP"},
        candidate_id="cand_bad",
        time_saved_ms=1850.0,
        rationale="Simulation budget expired"
    )

    assert rec.baseline_action == {"worker_0": "MOVE_UP"}
    assert policy.fallback_count == 1
    recs = policy.get_history()
    assert len(recs) == 1
    assert recs[0].reason == FallbackReason.RUNTIME_BUDGET_EXCEEDED
    assert recs[0].candidate_id == "cand_bad"


def test_a7_07_meta_fallback():
    """A7-07: MetaOrchestrator safely falls back to ROBUST_MODE when confidence is low."""
    meta = MetaOrchestrator(mode=AECMode.META_MODE, confidence_threshold=0.40)
    assert meta.current_mode == AECMode.META_MODE

    econ = EconomicState(
        step=200,
        farm=FarmState(cash=500.0, shed_inventory={}),
        market=MarketState(current_prices={"MILK": 10}),
        workers=WorkerState(workers=[WorkerEntity(worker_id=0, position=(5, 5))]),
        opponent=OpponentState(supply_forecast={}, sale_pressure={}, observed_animals={})
    )

    # Low confidence opponent state
    low_conf_pressure = OpponentPressureState(
        sale_pressure={"MILK": 0.1},
        buy_pressure={},
        route_interference_risk=0.0,
        terminal_pressure=0.0,
        confidence=0.2  # Below 0.40 threshold
    )

    decision = meta.orchestrate(
        pressure_state=low_conf_pressure,
        econ_state=econ
    )

    assert decision.effective_mode == AECMode.ROBUST_MODE
    assert decision.fallback_to_robust is True
    assert "fallback" in decision.rationale.lower()


def test_a7_08_event_triggered_replanning():
    """A7-08: State changes trigger appropriate ReplanTrigger and escalate through L1..L5."""
    replanner = EventTriggeredReplanner()

    prev_econ = EconomicState(
        step=50,
        farm=FarmState(cash=500.0, shed_inventory={"CARROT": 2}),
        market=MarketState(current_prices={"CARROT": 10}),
        workers=WorkerState(workers=[WorkerEntity(worker_id=0, position=(5, 5))]),
        opponent=OpponentState(supply_forecast={}, sale_pressure={}, observed_animals={})
    )

    # Current econ: cash dropped from 500 to 200 (material change > $150)
    curr_econ = EconomicState(
        step=51,
        farm=FarmState(cash=200.0, shed_inventory={"CARROT": 2}),
        market=MarketState(current_prices={"CARROT": 10}),
        workers=WorkerState(workers=[WorkerEntity(worker_id=0, position=(5, 5))]),
        opponent=OpponentState(supply_forecast={}, sale_pressure={}, observed_animals={})
    )

    events = replanner.detect_triggers(curr_econ, prev_econ)
    triggers = [e.trigger for e in events]
    assert ReplanTrigger.CASH_STATE_CHANGED in triggers

    # Cash change should escalate
    decision = replanner.classify_and_escalate(events, curr_econ)
    assert decision.escalation_level in (
        ReplanEscalationLevel.L3_ASSET_CASH_DEPENDENCY,
        ReplanEscalationLevel.L4_MULTI_WORKER_MARKET,
        ReplanEscalationLevel.L5_FULL_REMAINING_HORIZON
    )
