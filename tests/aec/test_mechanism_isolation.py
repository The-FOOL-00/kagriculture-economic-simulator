# SPDX-License-Identifier: MIT
"""
AEC Mechanism Isolation & Treatment Gate Test Suite.

Mandatory verification tests for EXP-AEC-001 preregistration alignment:
- Test 1: Enabled foundation mechanisms produce actionable candidates
- Test 2: OPPONENT_PREEMPT_SELL is quarantined at every layer
- Test 3: DYNAMIC_SHADOW_HARVEST is quarantined
- Test 4: EMERGENCY_FEED_PURCHASE is quarantined
- Test 5: CARGO_FERRY_PRIORITY is quarantined
- Test 6: TERMINAL_HARVEST_SWEEP is quarantined
- Test 7: TOWN_CYCLE cannot influence candidate generation or commit
- Test 8: Final commit guard blocks forged unauthorized patches with MECHANISM_POLICY_VIOLATION
- Test 9: Quarantined mechanisms are observable in telemetry
"""

import copy
import pytest
from typing import Any, Dict

from aec.config import (
    AECConfig,
    ENABLED_FOUNDATION_MECHANISMS,
    QUARANTINED_MECHANISMS,
)
from aec.evaluation.win_model import EvaluationResult, LeadState
from aec.events.detectors import detect_events
from aec.events.event_types import Event, EventType
from aec.integration.backbone_adapter import BackboneAdapter, BaselineResult
from aec.integration.executor import AECExecutor
from aec.ir.economic_state import build_economic_state
from aec.opportunities import OpportunityEngine
from aec.opportunities.base import Opportunity
from aec.patches.generator import PatchGenerator
from aec.patches.patch import CoupledPatch
from aec.safety.certificate import SafetyCertificate


# =============================================================================
# TEST 1 — ENABLED FOUNDATION
# =============================================================================
def test_1_enabled_foundation_mechanisms(weed_obstruction_obs, terminal_proximity_obs):
    """Verify each enabled foundation mechanism can produce actionable candidates."""
    config = AECConfig()
    engine = OpportunityEngine(config=config)
    generator = PatchGenerator(config=config)

    # 1. LOCAL_WEED_DIG
    econ_weed = build_economic_state(weed_obstruction_obs)
    events_weed = detect_events(econ_weed, None, {"farmer": ["PASS"], "hands": [["PASS"]], "market": []}, config)
    opps_weed = engine.detect_opportunities(econ_weed, events_weed, {"farmer": ["PASS"], "hands": [["PASS"]], "market": []}, config=config)
    weed_opps = [o for o in opps_weed if o.candidate_transformation_family == "LOCAL_WEED_DIG"]
    assert len(weed_opps) > 0, "LOCAL_WEED_DIG opportunity not detected on weed obstruction"
    patches_weed = generator.generate_patches(weed_opps, econ_weed, {"farmer": ["PASS"], "hands": [["PASS"]], "market": []}, config=config)
    assert len(patches_weed) > 0
    assert patches_weed[0].mechanism_family == "LOCAL_WEED_DIG"

    # 2. FRONTLOAD_ORDERS
    econ_normal = build_economic_state(weed_obstruction_obs)
    baseline_suboptimal = {
        "farmer": ["PASS"],
        "hands": [["PASS"]],
        "market": [["BUY_SEED", "WHEAT", 2], ["SELL", "STRAWBERRY", 5]]
    }
    opps_mkt = engine.detect_opportunities(econ_normal, [], baseline_suboptimal, config=config)
    frontload_opps = [o for o in opps_mkt if o.candidate_transformation_family == "FRONTLOAD_ORDERS"]
    assert len(frontload_opps) > 0, "FRONTLOAD_ORDERS opportunity not detected"
    patches_fl = generator.generate_patches(frontload_opps, econ_normal, baseline_suboptimal, config=config)
    assert len(patches_fl) > 0
    assert patches_fl[0].mechanism_family == "FRONTLOAD_ORDERS"
    assert patches_fl[0].market_mutations[0][0] == "SELL"

    # 3. TERMINAL_LIQUIDATION
    econ_term = build_economic_state(terminal_proximity_obs)
    events_term = detect_events(econ_term, None, {"farmer": ["PASS"], "hands": [["PASS"]], "market": []}, config)
    opps_term = engine.detect_opportunities(econ_term, events_term, {"farmer": ["PASS"], "hands": [["PASS"]], "market": []}, config=config)
    liq_opps = [o for o in opps_term if o.candidate_transformation_family == "TERMINAL_LIQUIDATION"]
    assert len(liq_opps) > 0, "TERMINAL_LIQUIDATION opportunity not detected at step 718"
    patches_liq = generator.generate_patches(liq_opps, econ_term, {"farmer": ["PASS"], "hands": [["PASS"]], "market": []}, config=config)
    assert len(patches_liq) > 0
    assert patches_liq[0].mechanism_family == "TERMINAL_LIQUIDATION"

    # 4. PHASE_SHUTDOWN
    # Step 600, BUY_SEED MELON (melon requires 10 days = 240 steps; 600+240 = 840 > 718, cannot mature)
    late_obs = copy.deepcopy(weed_obstruction_obs)
    late_obs["step"] = 600
    econ_late = build_economic_state(late_obs)
    baseline_dead_seed = {
        "farmer": ["PASS"],
        "hands": [["PASS"]],
        "market": [["BUY_SEED", "MELON", 2]]
    }
    opps_late = engine.detect_opportunities(econ_late, [], baseline_dead_seed, config=config)
    shutdown_opps = [o for o in opps_late if o.candidate_transformation_family == "PHASE_SHUTDOWN"]
    assert len(shutdown_opps) > 0, "PHASE_SHUTDOWN opportunity not detected for dead-capital seeds"
    patches_sd = generator.generate_patches(shutdown_opps, econ_late, baseline_dead_seed, config=config)
    assert len(patches_sd) > 0
    assert patches_sd[0].mechanism_family == "PHASE_SHUTDOWN"


# =============================================================================
# TEST 2 — OPPONENT PREEMPT DISABLED
# =============================================================================
def test_2_opponent_preempt_disabled(shed_capacity_obs):
    """Construct a state triggering OPPONENT_PREEMPT_SELL and verify quarantine."""
    config = AECConfig()
    engine = OpportunityEngine(config=config)
    generator = PatchGenerator(config=config)

    econ = build_economic_state(shed_capacity_obs)
    # Force high opponent supply pressure on STRAWBERRY
    econ.opponent.supply_forecast["STRAWBERRY"] = 1.0
    econ.farm.shed_inventory["STRAWBERRY"] = 20

    events = [Event(event_type=EventType.E5_OPPONENT_SUPPLY_SHOCK, step=econ.step, severity=0.8)]

    # Layer 1: OpportunityEngine must NOT emit OPPONENT_PREEMPT_SELL
    actionable_opps = engine.detect_opportunities(econ, events, {"farmer": ["PASS"], "hands": [["PASS"]], "market": []}, config=config)
    preempt_opps = [o for o in actionable_opps if o.candidate_transformation_family == "OPPONENT_PREEMPT_SELL"]
    assert len(preempt_opps) == 0, "Layer 1 breach: OPPONENT_PREEMPT_SELL leaked into actionable opportunities"

    # Layer 2: Even if manually injected, PatchGenerator MUST reject it
    forged_opp = Opportunity(
        opportunity_id="FORGED_PREEMPT_OPP",
        category="TIMING",
        event_trigger=EventType.E5_OPPONENT_SUPPLY_SHOCK,
        affected_entities=["STRAWBERRY"],
        estimated_economic_relevance=10.0,
        candidate_transformation_family="OPPONENT_PREEMPT_SELL",
        dependency_info={"item": "STRAWBERRY", "qty": 5},
        rationale="Unlawful preempt attempt"
    )
    patches = generator.generate_patches([forged_opp], econ, {"farmer": ["PASS"], "hands": [["PASS"]], "market": []}, config=config)
    assert len(patches) == 0, "Layer 2 breach: PatchGenerator compiled quarantined OPPONENT_PREEMPT_SELL"
    assert generator.last_quarantined_count == 1
    assert generator.last_quarantined_by_mechanism.get("OPPONENT_PREEMPT_SELL") == 1


# =============================================================================
# TEST 3 — DYNAMIC SHADOW DISABLED
# =============================================================================
def test_3_dynamic_shadow_disabled(weed_obstruction_obs):
    """Verify DYNAMIC_SHADOW_HARVEST is quarantined and cannot produce patches."""
    config = AECConfig()
    engine = OpportunityEngine(config=config)
    generator = PatchGenerator(config=config)

    obs = copy.deepcopy(weed_obstruction_obs)
    # Place mature harvest crop near worker
    obs["farms"][0]["tiles"][4][5] = {"kind": "PLANT", "crop": "STRAWBERRY", "yield_units": 5}
    econ = build_economic_state(obs)

    actionable = engine.detect_opportunities(econ, [], {"farmer": ["PASS"], "hands": [["PASS"]], "market": []}, config=config)
    shadow_opps = [o for o in actionable if o.candidate_transformation_family == "DYNAMIC_SHADOW_HARVEST"]
    assert len(shadow_opps) == 0, "DYNAMIC_SHADOW_HARVEST leaked into actionable opportunities"

    # Verify quarantine in generator
    forged_opp = Opportunity(
        opportunity_id="FORGED_SHADOW",
        category="LABOR",
        event_trigger=None,
        affected_entities=[0],
        estimated_economic_relevance=10.0,
        candidate_transformation_family="DYNAMIC_SHADOW_HARVEST",
        dependency_info={"worker_id": 0, "target_xy": (4, 5)},
        rationale="Unlawful shadow harvest attempt"
    )
    patches = generator.generate_patches([forged_opp], econ, {"farmer": ["PASS"], "hands": [["PASS"]], "market": []}, config=config)
    assert len(patches) == 0


# =============================================================================
# TEST 4 — EMERGENCY FEED DISABLED
# =============================================================================
def test_4_emergency_feed_disabled(normal_opening_obs):
    """Verify EMERGENCY_FEED_PURCHASE is quarantined."""
    config = AECConfig()
    engine = OpportunityEngine(config=config)

    econ = build_economic_state(normal_opening_obs)
    from aec.ir.farm_state import PipelineItem
    econ.farm.production_pipeline.append(
        PipelineItem(
            item_type="ANIMAL",
            subtype="COW",
            position=(0, 0),
            days_to_next_yield=1,
            yield_quantity=1,
            is_ongoing=True,
            requires_input=True
        )
    )
    econ.farm.shed_inventory["WHEAT"] = 0

    actionable = engine.detect_opportunities(econ, [], {"farmer": ["PASS"], "hands": [], "market": []}, config=config)
    feed_opps = [o for o in actionable if o.candidate_transformation_family == "EMERGENCY_FEED_PURCHASE"]
    assert len(feed_opps) == 0, "EMERGENCY_FEED_PURCHASE leaked into actionable opportunities"
    assert "EMERGENCY_FEED_PURCHASE" in engine.get_quarantined_proposals_by_mechanism()


# =============================================================================
# TEST 5 — CARGO FERRY DISABLED
# =============================================================================
def test_5_cargo_ferry_disabled(normal_opening_obs):
    """Verify CARGO_FERRY_PRIORITY is quarantined."""
    config = AECConfig()
    engine = OpportunityEngine(config=config)

    econ = build_economic_state(normal_opening_obs)
    worker = econ.workers.get_worker(0)
    if worker:
        worker.cargo = {"STRAWBERRY": 5}
        worker.deposit_path_len = 4

    actionable = engine.detect_opportunities(econ, [], {"farmer": ["PASS"], "hands": [], "market": []}, config=config)
    ferry_opps = [o for o in actionable if o.candidate_transformation_family == "CARGO_FERRY_PRIORITY"]
    assert len(ferry_opps) == 0, "CARGO_FERRY_PRIORITY leaked into actionable opportunities"


# =============================================================================
# TEST 6 — TERMINAL HARVEST SWEEP DISABLED
# =============================================================================
def test_6_terminal_harvest_sweep_disabled(terminal_proximity_obs):
    """Verify TERMINAL_HARVEST_SWEEP is quarantined in late-game."""
    config = AECConfig()
    engine = OpportunityEngine(config=config)

    obs = copy.deepcopy(terminal_proximity_obs)
    obs["step"] = 700  # Within steps 696-717
    econ = build_economic_state(obs)
    econ.farm.expected_harvests = {"STRAWBERRY": 10}

    actionable = engine.detect_opportunities(econ, [], {"farmer": ["PASS"], "hands": [["PASS"]], "market": []}, config=config)
    sweep_opps = [o for o in actionable if o.candidate_transformation_family == "TERMINAL_HARVEST_SWEEP"]
    assert len(sweep_opps) == 0, "TERMINAL_HARVEST_SWEEP leaked into actionable opportunities"
    assert "TERMINAL_HARVEST_SWEEP" in engine.get_quarantined_proposals_by_mechanism()


# =============================================================================
# TEST 7 — TOWN-CYCLE DISABLED
# =============================================================================
def test_7_town_cycle_disabled(normal_opening_obs):
    """Verify town-cycle signal cannot influence candidate generation or commit."""
    config = AECConfig()
    assert "TOWN_CYCLE" in config.quarantined_mechanisms
    assert not config.is_mechanism_enabled("TOWN_CYCLE")

    engine = OpportunityEngine(config=config)
    generator = PatchGenerator(config=config)
    econ = build_economic_state(normal_opening_obs)

    # In frozen mode, TOWN_CYCLE cannot produce actionable opportunities or patches
    forged_opp = Opportunity(
        opportunity_id="FORGED_TOWN_CYCLE",
        category="MARKET",
        event_trigger=None,
        affected_entities=["STRAWBERRY"],
        estimated_economic_relevance=10.0,
        candidate_transformation_family="TOWN_CYCLE",
        dependency_info={"item": "STRAWBERRY"},
        rationale="Town cycle timing exploit"
    )
    patches = generator.generate_patches([forged_opp], econ, {"farmer": ["PASS"], "hands": [], "market": []}, config=config)
    assert len(patches) == 0, "TOWN_CYCLE produced candidate patch"


# =============================================================================
# TEST 8 — FINAL COMMIT GUARD
# =============================================================================
def test_8_final_commit_guard(weed_obstruction_obs):
    """Construct a forged patch with OPPONENT_PREEMPT_SELL and attempt commit."""
    config = AECConfig()
    mock_adapter = BackboneAdapter(
        agent_fn=lambda obs, cfg=None: {"farmer": ["PASS"], "hands": [["PASS"]], "market": []},
        config=config
    )
    executor = AECExecutor(backbone_adapter=mock_adapter, config=config)

    # Forged unauthorized patch
    forged_patch = CoupledPatch(
        patch_id="FORGED_PREEMPT_PATCH",
        source_opportunity_id="OPP_PREEMPT",
        mechanism_family="OPPONENT_PREEMPT_SELL",
        market_mutations=[["SELL", "STRAWBERRY", 10]],
        rationale="Forged attempt to bypass Layer 1 and Layer 2"
    )

    # Subvert generator to return forged patch directly
    executor.patch_generator.generate_patches = lambda *args, **kwargs: [forged_patch]

    # Subvert evaluator to certify forged patch
    mock_cert = SafetyCertificate(
        patch_id="FORGED_PREEMPT_PATCH",
        baseline_summary="",
        candidate_summary="",
        delta_our_money=100.0,
        delta_opponent_money=0.0,
        delta_terminal_margin=100.0,
        overflow_check=True,
        obligation_check=True,
        purchase_check=True,
        intermediate_solvency_check=True,
        terminal_feasibility_check=True,
        market_collision_check=True,
        determinism_check=True,
        commit_decision=True,
    )
    mock_eval = EvaluationResult(
        patch_id="FORGED_PREEMPT_PATCH",
        is_superior=True,
        expected_p_win=0.9,
        terminal_margin_delta=100.0,
        our_money_delta=100.0,
        opponent_money_delta=0.0,
        lead_state=LeadState.AHEAD,
        temporary_sacrifice_accepted=False,
        rationale="TEST",
    )
    executor.win_model.evaluate = lambda *args, **kwargs: mock_eval
    executor.safety_checker.verify = lambda *args, **kwargs: (True, {"overflow_ok": True, "obligation_ok": True, "terminal_feasible": True, "market_collision_ok": True, "determinism_ok": True}, None)

    # Execute turn
    action = executor.act(weed_obstruction_obs)

    # Final Defense Gate MUST trigger
    telemetry = executor.latest_telemetry
    assert telemetry is not None
    assert telemetry.decision == "ABSTAIN", f"Expected ABSTAIN, got {telemetry.decision}"
    assert telemetry.abstain_reason == "MECHANISM_POLICY_VIOLATION", f"Expected MECHANISM_POLICY_VIOLATION, got {telemetry.abstain_reason}"
    assert telemetry.committed_mechanism is None
    # Returned action MUST be baseline unchanged
    assert action == {"farmer": ["PASS"], "hands": [["PASS"]], "market": []}


# =============================================================================
# TEST 9 — TELEMETRY
# =============================================================================
def test_9_telemetry(shed_capacity_obs):
    """Verify quarantined mechanisms appear explicitly in telemetry."""
    config = AECConfig()
    mock_adapter = BackboneAdapter(
        agent_fn=lambda obs, cfg=None: {"farmer": ["PASS"], "hands": [["PASS"]], "market": []},
        config=config
    )
    executor = AECExecutor(backbone_adapter=mock_adapter, config=config)

    # Create observation that triggers timing/opponent pressure
    obs = copy.deepcopy(shed_capacity_obs)
    obs["private"]["shed"]["STRAWBERRY"] = 25
    # Trigger an event so AEC doesn't fast-path bypass
    obs["farms"][0]["tiles"][4][4] = {"kind": "WEED"}

    executor.act(obs)
    telem = executor.latest_telemetry
    assert telem is not None
    telem_dict = telem.to_dict()

    assert "quarantined_by_mechanism" in telem_dict
    assert "lifecycle" in telem_dict
    assert "quarantined" in telem_dict["lifecycle"]

