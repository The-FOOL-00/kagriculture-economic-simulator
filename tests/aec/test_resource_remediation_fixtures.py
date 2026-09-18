# SPDX-License-Identifier: MIT
"""AEC-RESOURCE-CONVERSION REMEDIATION: Micro-Validation Test Battery (RC-R1..20).

Authoritative adversarial micro-validation scenarios testing:
- Objective A: Exact Working-Capital Liquidity & Causal Realizable Value (§3..8)
- Objective B: Strict Auxiliary Worker Precondition & Farmer Fallback Guard (§9..12)
- Objective C: Opportunity Family Audit & Classification Isolation (§13..18)
"""

from __future__ import annotations

import copy
import pytest
from typing import Any, Dict, List

from aec.config import AECConfig
from aec.coordination.assignment import LaborOpportunityCost, WorkerAssignment
from aec.coordination.dominance import MultiWorkerDominancePruner
from aec.coordination.scheduler import MultiWorkerLogisticsCoordinator
from aec.coordination.task_model import TaskActionFamily, TaskPriority, WorkerTask
from aec.coordination.worker_model import WorkerCapability, WorkerState, extract_farm_workers
from aec.counterfactual.simulator import CounterfactualSimulator
from aec.ir.economic_state import build_economic_state
from aec.opportunities.resource import ResourceOpportunityAnalyzer
from aec.patches.generator import PatchGenerator
from aec.patches.patch import CoupledPatch
from aec.resource.conversions import (
    ConversionCatalog,
    ConversionDiscoveryEngine,
    ConversionExecutionPlan,
    ConversionPath,
)
from aec.resource.labor import (
    ConversionLaborClass,
    ConversionLaborPreconditionValidator,
)
from aec.resource.liquidity import (
    ConversionCausalPathType,
    ConversionLiquidityAnalyzer,
    ConversionLiquidityProfile,
)
from aec.safety.checks import SafetyChecker
from aec.terminal.obligations import (
    BaselineObligationSet,
    ObligationClassification,
    TerminalObligation,
)


@pytest.fixture
def base_cow_obs(normal_opening_obs: Dict[str, Any]) -> Dict[str, Any]:
    obs = copy.deepcopy(normal_opening_obs)
    obs["farms"][0]["tiles"][2][2] = {"animal": "COW"}
    return obs


# =========================================================================
# RC-R1: Conversion requires cash, but exact baseline obligations cannot remain funded -> ABSTAIN
# =========================================================================
def test_rc_r1_baseline_obligations_cannot_remain_funded(base_cow_obs: Dict[str, Any]) -> None:
    obs = copy.deepcopy(base_cow_obs)
    # Available cash: $30
    obs["farms"][0]["money"] = 30.0
    econ = build_economic_state(obs)

    analyzer = ConversionLiquidityAnalyzer()
    # Baseline has mandatory wage payment of $20 at turn 5
    baseline_trajectory = [
        {"step": 5, "farms": [{"money": 10.0, "farmer": [4, 4], "hands": [[3, 4]]}], "wage_due": 20.0}
    ]
    # Conversion requires $25 upfront (30 - 25 = 5 remaining, wage 20 cannot be paid)
    profile = analyzer.analyze_profile(
        candidate_target="MILK",
        upfront_cost=25.0,
        duration_steps=48,
        expected_revenue=160.0,
        econ_state=econ,
        baseline_trajectory=baseline_trajectory,
        context={"mandatory_wage": 20.0}
    )
    # Must detect working capital insolvency and fail-closed
    assert not profile.is_solvent_trajectory
    assert "deadlock" in (profile.insolvency_reason or "").lower() or "insolvent" in (profile.insolvency_reason or "").lower()


# =========================================================================
# RC-R2: Conversion temporarily reduces cash but future exact revenue restores obligations -> FEASIBLE
# =========================================================================
def test_rc_r2_temporary_cash_reduction_restores_solvency(base_cow_obs: Dict[str, Any]) -> None:
    obs = copy.deepcopy(base_cow_obs)
    obs["farms"][0]["money"] = 100.0  # Plenty of cash to absorb temporary $25 dip
    econ = build_economic_state(obs)

    analyzer = ConversionLiquidityAnalyzer()
    profile = analyzer.analyze_profile(
        candidate_target="MILK",
        upfront_cost=25.0,
        duration_steps=48,
        expected_revenue=160.0,
        econ_state=econ
    )
    assert profile.is_solvent_trajectory
    assert profile.insolvency_reason is None
    assert profile.value_path_type == ConversionCausalPathType.SALEABLE_OUTPUT


# =========================================================================
# RC-R3: Conversion input purchase has no realizable downstream use -> ABSTAIN
# =========================================================================
def test_rc_r3_no_realizable_downstream_use(normal_opening_obs: Dict[str, Any]) -> None:
    obs = copy.deepcopy(normal_opening_obs)
    # No animals on tiles
    econ = build_economic_state(obs)

    analyzer = ConversionLiquidityAnalyzer()
    profile = analyzer.analyze_profile(
        candidate_target="MILK",  # Target requires cow, but no cow exists
        upfront_cost=25.0,
        duration_steps=48,
        expected_revenue=160.0,
        econ_state=econ
    )
    assert not profile.is_solvent_trajectory
    assert profile.value_path_type == ConversionCausalPathType.NO_REALIZABLE_PURPOSE
    assert "No realizable downstream value path" in (profile.insolvency_reason or "")


# =========================================================================
# RC-R4: Immediate positive symbolic value but future cash deadlock -> ABSTAIN
# =========================================================================
def test_rc_r4_positive_symbolic_value_causes_future_deadlock(base_cow_obs: Dict[str, Any]) -> None:
    obs = copy.deepcopy(base_cow_obs)
    obs["farms"][0]["money"] = 50.0
    econ = build_economic_state(obs)

    analyzer = ConversionLiquidityAnalyzer()
    # Symbolic net value is +$135, but turn 10 requires mandatory $40 debt/tax payment
    # If conversion takes $25, turn 10 cash is $25 < $40
    profile = analyzer.analyze_profile(
        candidate_target="MILK",
        upfront_cost=25.0,
        duration_steps=48,
        expected_revenue=160.0,
        econ_state=econ,
        context={"mandatory_future_debt": 40.0}
    )
    # Check custom deadlock verification
    assert not profile.is_solvent_trajectory


# =========================================================================
# RC-R5: Auxiliary worker available -> assign auxiliary
# =========================================================================
def test_rc_r5_auxiliary_worker_available_assigns_auxiliary(base_cow_obs: Dict[str, Any]) -> None:
    obs = copy.deepcopy(base_cow_obs)
    # Add auxiliary hand at (3, 4)
    obs["farms"][0]["hands"] = [[3, 4]]
    econ = build_economic_state(obs)

    workers = extract_farm_workers(econ, current_turn=0)
    assert len(workers) == 2  # Farmer + Hand 1

    validator = ConversionLaborPreconditionValidator()
    task = WorkerTask(
        task_id="TASK_FEED_COW",
        action_family=TaskActionFamily.FEED_ANIMAL,
        location=(2, 2),
        priority_class=TaskPriority.SCHEDULED_PRODUCTION,
        earliest_start=0,
        latest_completion=24,
        required_capabilities={WorkerCapability.FEED}
    )
    is_feas, plan, reason = validator.validate_and_schedule(
        tasks=[task],
        labor_class=ConversionLaborClass.AUXILIARY_WORKER_REQUIRED,
        workers=workers,
        baseline_action={"farmer": ["PASS"], "hands": [["PASS"]], "market": []},
        baseline_continuation=[],
        current_step=0
    )
    assert is_feas
    assert plan is not None
    # Must be assigned to auxiliary worker (worker_id 1), NOT Farmer (0)
    assert 1 in plan.worker_mutations
    assert 0 not in plan.worker_mutations


# =========================================================================
# RC-R6: Auxiliary worker unavailable -> ABSTAIN instead of Farmer fallback
# =========================================================================
def test_rc_r6_auxiliary_unavailable_abstains_no_farmer_fallback(base_cow_obs: Dict[str, Any]) -> None:
    obs = copy.deepcopy(base_cow_obs)
    # Hand 1 exists on farm, but is currently busy performing high-value harvest
    obs["farms"][0]["hands"] = [[3, 4]]
    econ = build_economic_state(obs)

    workers = extract_farm_workers(econ, current_turn=0)
    validator = ConversionLaborPreconditionValidator()

    task = WorkerTask(
        task_id="TASK_FEED_COW",
        action_family=TaskActionFamily.FEED_ANIMAL,
        location=(2, 2),
        priority_class=TaskPriority.SCHEDULED_PRODUCTION,
        earliest_start=0,
        latest_completion=24,
        required_capabilities={WorkerCapability.FEED}
    )
    # Hand 1 is busy with mandatory HARVEST, Farmer is busy with PLANT
    is_feas, plan, reason = validator.validate_and_schedule(
        tasks=[task],
        labor_class=ConversionLaborClass.AUXILIARY_WORKER_REQUIRED,
        workers=workers,
        baseline_action={"farmer": ["PLANT"], "hands": [["HARVEST"]], "market": []},
        baseline_continuation=[],
        current_step=0
    )
    # Must ABSTAIN and NOT divert Farmer!
    assert not is_feas
    assert plan is None or not plan.is_executable
    assert "auxiliary worker" in (reason or "").lower() or "farmer fallback prohibited" in (reason or "").lower()


# =========================================================================
# RC-R7: Farmer is the only worker, baseline unaffected -> allowed by exact semantics
# =========================================================================
def test_rc_r7_farmer_only_worker_baseline_unaffected_allowed(base_cow_obs: Dict[str, Any]) -> None:
    obs = copy.deepcopy(base_cow_obs)
    # Zero hands, only Farmer
    obs["farms"][0]["hands"] = []
    econ = build_economic_state(obs)

    workers = extract_farm_workers(econ, current_turn=0)
    assert len(workers) == 1

    validator = ConversionLaborPreconditionValidator()
    task = WorkerTask(
        task_id="TASK_FEED_COW",
        action_family=TaskActionFamily.FEED_ANIMAL,
        location=(2, 2),
        priority_class=TaskPriority.SCHEDULED_PRODUCTION,
        earliest_start=0,
        latest_completion=24,
        required_capabilities={WorkerCapability.FEED}
    )
    # Baseline Farmer action is PASS (idle, no mandatory duties)
    is_feas, plan, reason = validator.validate_and_schedule(
        tasks=[task],
        labor_class=ConversionLaborClass.AUXILIARY_WORKER_REQUIRED,
        workers=workers,
        baseline_action={"farmer": ["PASS"], "hands": [], "market": []},
        baseline_continuation=[],
        current_step=0
    )
    # Allowed because Farmer is single worker and baseline has zero obligations
    assert is_feas
    assert plan is not None
    assert 0 in plan.worker_mutations


# =========================================================================
# RC-R8: Farmer diversion destroys mandatory high-value task -> ABSTAIN
# =========================================================================
def test_rc_r8_farmer_diversion_destroys_mandatory_task_abstains(base_cow_obs: Dict[str, Any]) -> None:
    obs = copy.deepcopy(base_cow_obs)
    obs["farms"][0]["hands"] = []
    econ = build_economic_state(obs)

    workers = extract_farm_workers(econ, current_turn=0)
    validator = ConversionLaborPreconditionValidator()

    task = WorkerTask(
        task_id="TASK_FEED_COW",
        action_family=TaskActionFamily.FEED_ANIMAL,
        location=(2, 2),
        priority_class=TaskPriority.SCHEDULED_PRODUCTION,
        earliest_start=0,
        latest_completion=24,
        required_capabilities={WorkerCapability.FEED}
    )
    # Baseline Farmer is actively harvesting a ripe crop (mandatory high value)
    is_feas, plan, reason = validator.validate_and_schedule(
        tasks=[task],
        labor_class=ConversionLaborClass.AUXILIARY_WORKER_REQUIRED,
        workers=workers,
        baseline_action={"farmer": ["HARVEST"], "hands": [], "market": []},
        baseline_continuation=[],
        current_step=0
    )
    # Must ABSTAIN
    assert not is_feas
    assert plan is None or not plan.is_executable
    assert "mandatory" in (reason or "").lower() or "farmer fallback prohibited" in (reason or "").lower()


# =========================================================================
# RC-R9: Farmer diversion destroys optional task only -> may remain feasible
# =========================================================================
def test_rc_r9_farmer_diversion_destroys_optional_task_only_feasible(base_cow_obs: Dict[str, Any]) -> None:
    obs = copy.deepcopy(base_cow_obs)
    obs["farms"][0]["hands"] = []
    econ = build_economic_state(obs)

    workers = extract_farm_workers(econ, current_turn=0)
    validator = ConversionLaborPreconditionValidator()

    task = WorkerTask(
        task_id="TASK_FEED_COW",
        action_family=TaskActionFamily.FEED_ANIMAL,
        location=(2, 2),
        priority_class=TaskPriority.SCHEDULED_PRODUCTION,
        earliest_start=0,
        latest_completion=24,
        required_capabilities={WorkerCapability.FEED}
    )
    # Farmer is wandering / idle stepping
    is_feas, plan, reason = validator.validate_and_schedule(
        tasks=[task],
        labor_class=ConversionLaborClass.AUXILIARY_WORKER_REQUIRED,
        workers=workers,
        baseline_action={"farmer": ["EAST"], "hands": [], "market": []},
        baseline_continuation=[],
        current_step=0
    )
    # Feasible since EAST is not an essential obligation
    assert is_feas
    assert plan is not None


# =========================================================================
# RC-R10: Two workers available; one preserves baseline better -> Dominance selects
# =========================================================================
def test_rc_r10_dominance_selects_better_worker_assignment(base_cow_obs: Dict[str, Any]) -> None:
    task = WorkerTask(
        task_id="TASK_FEED",
        action_family=TaskActionFamily.FEED_ANIMAL,
        location=(2, 2),
        priority_class=TaskPriority.SCHEDULED_PRODUCTION,
        earliest_start=0,
        latest_completion=24,
        required_capabilities={WorkerCapability.FEED}
    )
    # Assignment A: diverts Farmer (worker_id 0)
    assign_a = [WorkerAssignment(worker_id=0, task=task, start_step=0, completion_step=4, transit_route=["NORTH"])]
    cost_a = LaborOpportunityCost(lost_mandatory_count=0, displaced_value_est=0.0, is_acceptable=True)

    # Assignment B: assigns Hand 1 (worker_id 1), keeping Farmer free
    assign_b = [WorkerAssignment(worker_id=1, task=task, start_step=0, completion_step=4, transit_route=["NORTH"])]
    cost_b = LaborOpportunityCost(lost_mandatory_count=0, displaced_value_est=0.0, is_acceptable=True)

    # Plan B dominates Plan A because auxiliary worker assignment is strictly preferred over Farmer diversion
    assert MultiWorkerDominancePruner.dominates(assign_b, cost_b, assign_a, cost_a)
    assert not MultiWorkerDominancePruner.dominates(assign_a, cost_a, assign_b, cost_b)


# =========================================================================
# RC-R11: Market-only seed purchase incorrectly classified -> classification corrected
# =========================================================================
def test_rc_r11_market_seed_purchase_classified_as_resource_acquisition(normal_opening_obs: Dict[str, Any]) -> None:
    obs = copy.deepcopy(normal_opening_obs)
    econ = build_economic_state(obs)

    engine = ConversionDiscoveryEngine()
    paths = engine.discover_conversion_paths(econ)

    carrot_paths = [p for p in paths if p.target_commodity == "CARROT"]
    assert len(carrot_paths) > 0
    # Must be classified as RESOURCE_ACQUISITION, NOT RESOURCE_CONVERSION
    assert carrot_paths[0].opportunity_family == "RESOURCE_ACQUISITION"
    assert carrot_paths[0].labor_class == ConversionLaborClass.NO_WORKER_REQUIRED

    # PatchGenerator must abstain from generating RESOURCE_CONVERSION patch for seed purchase
    cfg = AECConfig(enabled_mechanisms=("RESOURCE_CONVERSION",))
    analyzer = ResourceOpportunityAnalyzer()
    opps = analyzer.analyze(econ, [])
    gen = PatchGenerator(config=cfg)
    patches = gen.generate_patches(opps, econ, {"farmer": ["PASS"], "market": []}, config=cfg)

    # Zero carrot patches should be generated under RESOURCE_CONVERSION
    conv_carrot_patches = [p for p in patches if p.mechanism_family == "RESOURCE_CONVERSION" and "CARROT" in p.patch_id]
    assert len(conv_carrot_patches) == 0


# =========================================================================
# RC-R12: True physical conversion correctly classified -> conversion family retained
# =========================================================================
def test_rc_r12_true_physical_conversion_classified_as_resource_conversion(base_cow_obs: Dict[str, Any]) -> None:
    obs = copy.deepcopy(base_cow_obs)
    econ = build_economic_state(obs)

    engine = ConversionDiscoveryEngine()
    paths = engine.discover_conversion_paths(econ)

    cow_paths = [p for p in paths if p.target_commodity == "MILK"]
    assert len(cow_paths) > 0
    assert cow_paths[0].opportunity_family == "RESOURCE_CONVERSION"
    assert cow_paths[0].labor_class == ConversionLaborClass.AUXILIARY_WORKER_REQUIRED
    assert cow_paths[0].execution_plan is not None
    assert cow_paths[0].execution_plan.attribution_info["physical_conversion"] is True


# =========================================================================
# RC-R13: Conversion path is multi-stage -> complete DAG required
# =========================================================================
def test_rc_r13_multi_stage_conversion_requires_complete_dag(base_cow_obs: Dict[str, Any]) -> None:
    obs = copy.deepcopy(base_cow_obs)
    econ = build_economic_state(obs)

    engine = ConversionDiscoveryEngine()
    paths = engine.discover_conversion_paths(econ)
    cow_path = next(p for p in paths if p.target_commodity == "MILK")

    # Multi-stage: Buy wheat -> Feed cow -> Produce milk
    assert len(cow_path.recipes) == 2
    assert cow_path.recipes[0].recipe_id == "BUY_WHEAT_FEED"
    assert cow_path.recipes[1].recipe_id == "FEED_LIVESTOCK_COW"
    assert cow_path.total_steps == 49


# =========================================================================
# RC-R14: Conversion produces output too late for use -> ABSTAIN
# =========================================================================
def test_rc_r14_conversion_output_too_late_abstains(base_cow_obs: Dict[str, Any]) -> None:
    obs = copy.deepcopy(base_cow_obs)
    # Only 10 steps remain until terminal step 718
    obs["step"] = 708
    econ = build_economic_state(obs)

    engine = ConversionDiscoveryEngine()
    paths = engine.discover_conversion_paths(econ)
    # Cow path takes 49 steps, exceeds remaining horizon 10
    cow_paths = [p for p in paths if p.target_commodity == "MILK"]
    assert len(cow_paths) == 0  # Bounded discovery prunes late paths


# =========================================================================
# RC-R15: Conversion requires terminal liquidation -> exact terminal purpose check
# =========================================================================
def test_rc_r15_terminal_liquidation_purpose_check(base_cow_obs: Dict[str, Any]) -> None:
    obs = copy.deepcopy(base_cow_obs)
    obs["step"] = 650  # Near terminal
    econ = build_economic_state(obs)

    analyzer = ConversionLiquidityAnalyzer()
    profile = analyzer.analyze_profile(
        candidate_target="MILK",
        upfront_cost=25.0,
        duration_steps=48,
        expected_revenue=160.0,
        econ_state=econ
    )
    # Steps 650 + 48 = 698 <= 718 (can be liquidated before terminal)
    assert profile.is_solvent_trajectory
    assert profile.value_path_type in (ConversionCausalPathType.SALEABLE_OUTPUT, ConversionCausalPathType.EXACT_TERMINAL_VALUE)


# =========================================================================
# RC-R16: Repeated identical state -> bit-exact deterministic result
# =========================================================================
def test_rc_r16_bit_exact_determinism(base_cow_obs: Dict[str, Any]) -> None:
    obs1 = copy.deepcopy(base_cow_obs)
    obs2 = copy.deepcopy(base_cow_obs)
    econ1 = build_economic_state(obs1)
    econ2 = build_economic_state(obs2)

    engine = ConversionDiscoveryEngine()
    paths1 = engine.discover_conversion_paths(econ1)
    paths2 = engine.discover_conversion_paths(econ2)

    assert len(paths1) == len(paths2)
    for p1, p2 in zip(paths1, paths2):
        assert p1.path_id == p2.path_id
        assert p1.net_value_est == p2.net_value_est
        assert p1.opportunity_family == p2.opportunity_family
        assert p1.labor_class == p2.labor_class


# =========================================================================
# RC-R17: Conversion candidate passes symbolic graph but exact simulator rejects -> ABSTAIN
# =========================================================================
def test_rc_r17_exact_simulator_rejects_infeasible_physical_patch(base_cow_obs: Dict[str, Any]) -> None:
    obs = copy.deepcopy(base_cow_obs)
    econ = build_economic_state(obs)

    # Candidate specifies illegal market op
    patch = CoupledPatch(
        patch_id="PATCH_ILLEGAL",
        source_opportunity_id="OPP_ILLEGAL",
        mechanism_family="RESOURCE_CONVERSION",
        market_mutations=[["ILLEGAL_ORDER_OP", "CARROT", 1]],
        expected_horizon=6
    )
    sim = CounterfactualSimulator()
    outcome = sim.evaluate(patch, {"farmer": ["PASS"], "hands": [], "market": []}, econ, horizon=6)
    checker = SafetyChecker()
    is_safe, _, _ = checker.verify(patch, outcome, econ, {"farmer": ["PASS"], "hands": [], "market": []})
    assert not is_safe or outcome.fidelity == "FAILED"


# =========================================================================
# RC-R18: Conversion candidate passes worker schedule but violates liquidity -> ABSTAIN
# =========================================================================
def test_rc_r18_passes_worker_schedule_but_violates_liquidity(base_cow_obs: Dict[str, Any]) -> None:
    obs = copy.deepcopy(base_cow_obs)
    obs["farms"][0]["hands"] = [[3, 4]]
    # Cash is zero -> cannot buy wheat feed
    obs["farms"][0]["money"] = 0.0
    econ = build_economic_state(obs)

    cfg = AECConfig(enabled_mechanisms=("RESOURCE_CONVERSION",))
    analyzer = ResourceOpportunityAnalyzer()
    opps = analyzer.analyze(econ, [])
    gen = PatchGenerator(config=cfg)
    patches = gen.generate_patches(opps, econ, {"farmer": ["PASS"], "hands": [["PASS"]], "market": []}, config=cfg)

    # Worker was available, but liquidity was 0 -> zero conversion patches generated
    assert len([p for p in patches if p.mechanism_family == "RESOURCE_CONVERSION"]) == 0


# =========================================================================
# RC-R19: Conversion requires auxiliary worker but worker expires at day boundary -> ABSTAIN
# =========================================================================
def test_rc_r19_auxiliary_worker_expires_at_day_boundary_abstains(base_cow_obs: Dict[str, Any]) -> None:
    obs = copy.deepcopy(base_cow_obs)
    obs["farms"][0]["hands"] = [[3, 4]]
    # Step 23 is the last turn of Day 0 (hires expire at end of turn 23)
    obs["step"] = 23
    obs["hour"] = 23
    econ = build_economic_state(obs)

    workers = extract_farm_workers(econ, current_turn=23)
    validator = ConversionLaborPreconditionValidator()

    task = WorkerTask(
        task_id="TASK_FEED_COW",
        action_family=TaskActionFamily.FEED_ANIMAL,
        location=(2, 2),
        priority_class=TaskPriority.SCHEDULED_PRODUCTION,
        earliest_start=23,
        latest_completion=47,
        required_capabilities={WorkerCapability.FEED}
    )
    # Multi-step task duration = 5 steps, but auxiliary worker expires at step 23
    is_feas, plan, reason = validator.validate_and_schedule(
        tasks=[task],
        labor_class=ConversionLaborClass.AUXILIARY_WORKER_REQUIRED,
        workers=workers,
        baseline_action={"farmer": ["PASS"], "hands": [["PASS"]], "market": []},
        baseline_continuation=[],
        current_step=23,
        estimated_duration=5
    )
    # Must ABSTAIN due to day boundary expiration
    assert not is_feas
    assert "day boundary" in (reason or "").lower() or "expiry" in (reason or "").lower()


# =========================================================================
# RC-R20: Auxiliary worker feeds while Farmer remains on harvest -> validated by counterfactual
# =========================================================================
def test_rc_r20_auxiliary_feeds_farmer_remains_on_harvest_counterfactual(base_cow_obs: Dict[str, Any]) -> None:
    obs = copy.deepcopy(base_cow_obs)
    obs["farms"][0]["hands"] = [[3, 4]]
    obs["farms"][0]["money"] = 1000.0
    econ = build_economic_state(obs)

    cfg = AECConfig(enabled_mechanisms=("RESOURCE_CONVERSION",))
    analyzer = ResourceOpportunityAnalyzer()
    opps = [o for o in analyzer.analyze(econ, []) if o.candidate_transformation_family == "RESOURCE_CONVERSION"]
    assert len(opps) > 0

    gen = PatchGenerator(config=cfg)
    # Baseline: Farmer is harvesting, Hand is idle PASS
    baseline_action = {"farmer": ["HARVEST"], "hands": [["PASS"]], "market": []}
    patches = gen.generate_patches(opps, econ, baseline_action, config=cfg)

    # Must produce coordinated patch where Farmer continues harvesting (worker 0 unchanged) and Hand 1 feeds
    cow_patches = [p for p in patches if "MILK" in p.patch_id]
    assert len(cow_patches) > 0
    patch = cow_patches[0]
    assert 0 not in patch.worker_mutations
    assert 1 in patch.worker_mutations

    # Validate with exact counterfactual simulator
    sim = CounterfactualSimulator()
    outcome = sim.evaluate(patch, baseline_action, econ, horizon=6)
    assert outcome.fidelity == "VERIFIED"
    assert outcome.spatial_consistency_ok
    checker = SafetyChecker()
    is_safe, _, _ = checker.verify(patch, outcome, econ, baseline_action)
    assert is_safe
