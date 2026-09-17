# SPDX-License-Identifier: MIT
"""AEC V1.1 Development Fixes Verification Suite.

Validates the four development fixes identified in the Activation Integrity Audit:
1. FRONTLOAD_ORDERS official market pricing & causal commit under rival dump.
2. LOCAL_WEED_DIG grounded labor opportunity cost & biological/terminal cutoff.
3. Separation of REALIZED counterfactual value from PROJECTED downstream value.
4. Continuation spatial desynchronization detection and fail-closed safety.

Covers all 17 required categories (A through Q):
A. Official market pricing
B. Frontload positive causal commit (with required frontload trace)
C. Frontload negative abstention
D. Frontload no-op
E. Frontload no-sell
F. Weed realized vs projected valuation
G. Weed biological feasibility
H. Weed downstream dependency (with required weed trace)
I. Weed false-positive prevention
J. Labor-cost semantics
K. Route-tape spatial consistency
L. Stale continuation rejection
M. Baseline passthrough
N. Deterministic replay
O. Safety rejection
P. Terminal redundancy
Q. Phase-shutdown redundancy
"""

from __future__ import annotations

import copy
from typing import Any, Dict, List, Tuple
import pytest

from aec.config import AECConfig, FINAL_STEP, MECHANISM_REGISTRY, ScientificStatus, TURNS_PER_DAY
from aec.counterfactual.opponent_pressure import OpponentPressureModel
from aec.counterfactual.simulator import (
    CounterfactualSimulator,
    ShadowRolloutState,
    SimulationOutcome,
    execute_market_lockstep,
    simulate_rollout,
)
from aec.evaluation.asset_value import DownstreamAssetEvaluator, WeedValuation
from aec.evaluation.win_model import EvaluationResult, WinModel
from aec.events.detectors import detect_events
from aec.integration.backbone_adapter import BackboneAdapter
from aec.integration.executor import AECExecutor
from aec.ir.economic_state import build_economic_state
from aec.opportunities import OpportunityEngine
from aec.opportunities.market import MarketOpportunityAnalyzer
from aec.patches.generator import PatchGenerator, reorder_frontload
from aec.patches.patch import CoupledPatch
from aec.safety.checks import SafetyChecker
from config import CROPS, MARKET_PARAMS, compute_market_price, fib_hire_cost


# =============================================================================
# CATEGORY A: OFFICIAL MARKET PRICING
# =============================================================================

class TestCategoryAOfficialPricing:
    """Verifies that simulator uses authoritative compute_market_price rather than toy rule."""

    def test_official_pricing_formula_invoked(self):
        """Official pricing computes non-linear price degradation from inventory."""
        base_p = compute_market_price("WHEAT", 10000)
        p_50 = compute_market_price("WHEAT", 10050)
        p_100 = compute_market_price("WHEAT", 10100)

        assert base_p == 25
        assert p_50 == 22
        assert p_100 == 21
        assert p_50 < base_p
        assert p_100 < p_50

    def test_simulator_market_lockstep_uses_official_prices(self, normal_opening_obs):
        """Simulation rollout updates prices and cash via official compute_market_price."""
        obs = copy.deepcopy(normal_opening_obs)
        obs["private"]["shed"]["WHEAT"] = 100
        econ_state = build_economic_state(obs)

        # Baseline: Sell 50 wheat into 10000 inventory
        action = {
            "farmer": ["PASS"], "hands": [],
            "market": [["SELL", "WHEAT", 50]]
        }
        opp_model = OpponentPressureModel(econ_state.opponent)
        rollout = simulate_rollout(
            econ_state=econ_state,
            initial_action=action,
            horizon=1,
            opp_model=opp_model
        )

        assert rollout.cumulative_sold["WHEAT"] == 50
        # Inventory after 50 units sold
        assert rollout.market_inv["WHEAT"] == 10050
        # Market price matches official formula
        assert rollout.market_prices["WHEAT"] == compute_market_price("WHEAT", 10050)
        assert rollout.market_prices["WHEAT"] == 22


# =============================================================================
# CATEGORY B & 14: FRONTLOAD POSITIVE CAUSAL COMMIT & REQUIRED TRACE
# =============================================================================

class TestCategoryBFrontloadPositiveCommit:
    """Proves FRONTLOAD_ORDERS commits on genuine causal market advantage."""

    def test_frontload_causal_commit_with_trace(self, normal_opening_obs):
        """Frontloading SELL before rival dump captures quoting priority and COMMITS."""
        obs = copy.deepcopy(normal_opening_obs)
        obs["private"]["shed"]["WHEAT"] = 50
        obs["step"] = 40
        obs["farms"][0]["money"] = 1000.0
        obs["farms"][1]["money"] = 1000.0

        # Opponent exerts high dump pressure on Wheat via observable mature crop on farm
        obs["farms"][1]["tiles"][0][0] = {
            "kind": "PLANT",
            "crop": "WHEAT",
            "yield_units": 50,
            "age": 48
        }

        # Baseline order: non-sell first, then SELL
        baseline_action = {
            "farmer": ["PASS"], "hands": [],
            "market": [["HIRE", 1], ["SELL", "WHEAT", 50]]
        }

        # 1. Opportunity detected
        econ_state = build_economic_state(obs)
        assert econ_state.opponent.sale_pressure.get("WHEAT", 0.0) >= 0.5
        assert econ_state.opponent.supply_forecast.get("WHEAT", 0.0) >= 50.0

        events = detect_events(econ_state)
        analyzer = MarketOpportunityAnalyzer()
        opps = analyzer.analyze(econ_state, events, baseline_action)
        assert len(opps) == 1
        assert opps[0].candidate_transformation_family == "FRONTLOAD_ORDERS"

        # 2. Correct patch generated
        generator = PatchGenerator()
        patches = generator.generate_patches(opps, econ_state, baseline_action)
        assert len(patches) == 1
        patch = patches[0]
        assert patch.market_mutations == [["SELL", "WHEAT", 50], ["HIRE", 1]]

        # 3. Candidate order differs from baseline
        candidate_action = patch.apply(baseline_action)
        assert candidate_action["market"] != baseline_action["market"]

        # 4 & 5. Simulator evaluation under rival dump
        simulator = CounterfactualSimulator()
        outcome = simulator.evaluate(
            candidate_patch=patch,
            baseline_action=baseline_action,
            econ_state=econ_state,
            horizon=4,
            trace=True
        )

        # Candidate simulation produces exact ground-truth lockstep advantage (sim.hpp:578-617)
        assert outcome.delta_our_money == 31.0
        assert outcome.delta_opponent_money == -30.0
        assert outcome.delta_terminal_margin == 61.0

        # 6. Safety verification passes
        checker = SafetyChecker()
        passed_safety, checks, abstain_reason = checker.verify(
            patch=patch,
            outcome=outcome,
            econ_state=econ_state,
            baseline_action=baseline_action
        )
        assert passed_safety is True
        assert checks["spatial_consistency_ok"] is True
        assert checks["solvency_ok"] is True

        # 7, 8, 9. Full AECExecutor commits candidate action
        adapter = BackboneAdapter(agent_fn=lambda o, c: copy.deepcopy(baseline_action))
        executor = AECExecutor(backbone_adapter=adapter)
        committed_action = executor.act(obs)

        assert executor.latest_telemetry.decision == "COMMIT"
        assert executor.latest_telemetry.committed_mechanism == "FRONTLOAD_ORDERS"
        assert committed_action == candidate_action

        # =====================================================================
        # REQUIRED FRONTLOAD TRACE (§14)
        # =====================================================================
        print("\n" + "=" * 70)
        print("REQUIRED FRONTLOAD TRACE (§14)")
        print("=" * 70)
        print("BASELINE:")
        print(f"  orders:           {baseline_action['market']}")
        print(f"  opponent orders:  [['SELL', 'WHEAT', 50]]")
        print(f"  market inventory: 10000 -> {outcome.baseline_trace[0]['market_inventory']['WHEAT']}")
        print(f"  initial prices:   WHEAT=${compute_market_price('WHEAT', 10000)}")
        print("\nCANDIDATE:")
        print(f"  orders:           {candidate_action['market']}")
        print(f"  opponent orders:  [['SELL', 'WHEAT', 50]]")
        print(f"  market inventory: 10000 -> {outcome.candidate_trace[0]['market_inventory']['WHEAT']}")
        print(f"  price evolution:  ${outcome.candidate_trace[0]['market_prices']['WHEAT']}")
        print("\nRESULTS:")
        print(f"  baseline money:   ${outcome.baseline_final_money:.2f}")
        print(f"  candidate money:  ${outcome.candidate_final_money:.2f}")
        print(f"  baseline margin:  ${outcome.baseline_final_money - outcome.baseline_opp_final_money:.2f}")
        print(f"  candidate margin: ${outcome.candidate_final_money - outcome.candidate_opp_final_money:.2f}")
        print(f"  delta_money:      +${outcome.delta_our_money:.2f}")
        print(f"  delta_margin:     +${outcome.delta_terminal_margin:.2f}")
        print(f"  safety result:    {passed_safety} ({checks})")
        print(f"  final decision:   {executor.latest_telemetry.decision} ({executor.latest_telemetry.committed_mechanism})")
        print("=" * 70 + "\n")


# =============================================================================
# CATEGORIES C, D, E: FRONTLOAD NEGATIVE, NO-OP, NO-SELL
# =============================================================================

class TestCategoryCDEFrontloadInvariants:
    """Verifies abstention and invariants for FRONTLOAD_ORDERS."""

    def test_category_c_frontload_negative_abstention(self, normal_opening_obs):
        """Negative case: Same reordering but no opposing market dump -> ABSTAIN."""
        obs = copy.deepcopy(normal_opening_obs)
        obs["private"]["shed"]["WHEAT"] = 50
        obs["farms"][0]["money"] = 1000.0

        # Opponent has NO mature crops -> zero sale pressure
        obs["farms"][1]["tiles"] = [[{"kind": "SOIL"} for _ in range(8)] for _ in range(8)]

        baseline_action = {
            "farmer": ["PASS"], "hands": [],
            "market": [["HIRE", 1], ["SELL", "WHEAT", 50]]
        }
        adapter = BackboneAdapter(agent_fn=lambda o, c: copy.deepcopy(baseline_action))
        executor = AECExecutor(backbone_adapter=adapter)
        action = executor.act(obs)

        # Without rival market dump, order sequence within slot 0/1 produces identical prices
        assert action == baseline_action
        assert executor.latest_telemetry.decision in ("BACKBONE", "ABSTAIN")
        assert executor.latest_telemetry.to_dict()["lifecycle"]["committed"] == 0

    def test_category_d_frontload_no_op(self, normal_opening_obs):
        """No-op case: SELL is already first -> No patch generated."""
        obs = copy.deepcopy(normal_opening_obs)
        econ_state = build_economic_state(obs)
        orders = [["SELL", "WHEAT", 10], ["HIRE", 1]]
        baseline_action = {"farmer": ["PASS"], "hands": [], "market": orders}

        analyzer = MarketOpportunityAnalyzer()
        opps = analyzer.analyze(econ_state, [], baseline_action)
        assert len(opps) == 0

        generator = PatchGenerator()
        patches = generator.generate_patches(opps, econ_state, baseline_action)
        assert len(patches) == 0

    def test_category_e_frontload_no_sell(self, normal_opening_obs):
        """No-sell case: No SELL order exists -> No opportunity."""
        obs = copy.deepcopy(normal_opening_obs)
        econ_state = build_economic_state(obs)
        baseline_action = {
            "farmer": ["PASS"], "hands": [],
            "market": [["HIRE", 1], ["BUY_SEED", "WHEAT", 2]]
        }
        analyzer = MarketOpportunityAnalyzer()
        opps = analyzer.analyze(econ_state, [], baseline_action)
        assert len(opps) == 0


# =============================================================================
# CATEGORIES F, G, H, I & 15: WEED VALUATION, FEASIBILITY & REQUIRED TRACE
# =============================================================================

class TestCategoryFGHIWeedValuation:
    """Verifies realized vs projected valuation and biological/terminal constraints."""

    def test_category_f_realized_vs_projected_separation(self, weed_obstruction_obs):
        """DIG action realizes $0 cash delta; future crop value is isolated as projected."""
        econ_state = build_economic_state(weed_obstruction_obs)
        evaluator = DownstreamAssetEvaluator()
        continuation = [
            {"farmer": ["PLANT", "WHEAT"], "hands": [["PASS"]], "market": []}
            for _ in range(6)
        ]
        val = evaluator.evaluate_weed_removal((4, 4), 0, econ_state, continuation)

        assert val.realized_delta_money == 0.0
        assert val.projected_gross_profit > 0.0
        assert val.projection_status == "DETERMINISTIC_PROJECTION"
        assert "DETERMINISTIC_CROP_PROJECTION" in val.projected_asset_value_basis
        assert val.net_projected_asset_value == val.projected_gross_profit - val.action_opportunity_cost

    def test_category_g_weed_biological_feasibility_terminal_cutoff(self, weed_obstruction_obs):
        """Crop unable to mature before step 718 produces 0 projected benefit."""
        obs = copy.deepcopy(weed_obstruction_obs)
        obs["step"] = 675  # Plant at 676 + 48 turns growth = 724 > 718!
        econ_state = build_economic_state(obs)

        evaluator = DownstreamAssetEvaluator()
        continuation = [
            {"farmer": ["PLANT", "WHEAT"], "hands": [["PASS"]], "market": []}
            for _ in range(6)
        ]
        val = evaluator.evaluate_weed_removal((4, 4), 0, econ_state, continuation)

        assert val.projection_status == "INFEASIBLE_TERMINAL_CUTOFF"
        assert val.projected_gross_profit == 0.0
        assert val.net_projected_asset_value < 0.0

        # WinModel must reject
        win_model = WinModel()
        patch = CoupledPatch("P_WEED", "OPP_WEED", worker_mutations={0: ["DIG"]}, mechanism_family="LOCAL_WEED_DIG")
        outcome = SimulationOutcome(
            candidate_final_money=2500.0, baseline_final_money=2500.0,
            delta_our_money=0.0, candidate_opp_final_money=2500.0,
            baseline_opp_final_money=2500.0, delta_opponent_money=0.0,
            delta_terminal_margin=0.0, candidate_overflow_units=0,
            candidate_sold={}, baseline_sold={}, intermediate_solvency_ok=True,
            horizon=4
        )
        res = win_model.evaluate(patch, outcome, econ_state, continuation)
        assert res.is_superior is False
        assert "infeasible" in res.rationale

    def test_category_h_weed_quarantine_rejection_and_trace(self, weed_obstruction_obs):
        """LOCAL_WEED_DIG opportunity detected & attractive, but rejected under SCIENTIFIC_QUARANTINE (§3).
        
        Verifies all 7 mandated quarantine criteria:
        1. Opportunity detected
        2. Patch generated
        3. Candidate otherwise looks attractive (positive net projected value)
        4. Mechanism status is QUARANTINED in registry
        5. Final decision is ABSTAIN (not economically inferior)
        6. Exact baseline action returned
        7. Zero action divergence
        """
        obs = copy.deepcopy(weed_obstruction_obs)
        obs["step"] = 100
        obs["private"]["shed"]["WHEAT"] = 0
        obs["private"]["seeds"]["WHEAT"] = 2
        obs["farms"][0]["money"] = 2000.0

        base_act = {"farmer": ["PASS"], "hands": [["PASS"]], "market": []}
        continuation = [
            {"farmer": ["PLANT", "WHEAT"], "hands": [["PASS"]], "market": []}
            for _ in range(12)
        ]

        # 1. Opportunity detected
        econ_state = build_economic_state(obs)
        events = detect_events(econ_state)
        engine = OpportunityEngine()
        opps = engine.detect_opportunities(econ_state, events, base_act)
        weed_opps = [o for o in opps if o.candidate_transformation_family == "LOCAL_WEED_DIG"]
        assert len(weed_opps) == 1, "Expected LOCAL_WEED_DIG opportunity to be detected"

        # 2. Patch generated
        generator = PatchGenerator()
        patches = generator.generate_patches(weed_opps, econ_state, base_act)
        assert len(patches) == 1, "Expected LOCAL_WEED_DIG patch to be generated"
        assert patches[0].mechanism_family == "LOCAL_WEED_DIG"

        # 3. Candidate otherwise looks attractive
        evaluator = DownstreamAssetEvaluator()
        val = evaluator.evaluate_weed_removal((4, 4), 0, econ_state, continuation)
        assert val.net_projected_asset_value > 0.0, "Expected positive downstream valuation"

        # 4. Mechanism status is QUARANTINED in registry
        assert MECHANISM_REGISTRY["LOCAL_WEED_DIG"]["status"] == ScientificStatus.QUARANTINED

        # 5, 6, 7. Final executor evaluation under prospective default config
        adapter = BackboneAdapter(
            agent_fn=lambda o, c: copy.deepcopy(base_act),
            continuation_provider=lambda s, h, p, nh: continuation[:h-1]
        )
        executor = AECExecutor(backbone_adapter=adapter)
        action = executor.act(obs)

        # 5. Final decision ABSTAIN with explicit scientific quarantine reason
        assert executor.latest_telemetry.decision == "ABSTAIN"
        assert executor.latest_telemetry.abstain_reason == "SCIENTIFIC_QUARANTINE"
        assert executor.latest_telemetry.mechanism == "LOCAL_WEED_DIG"
        assert executor.latest_telemetry.committed_patch_id is None

        # 6 & 7. Exact baseline action returned; no action divergence
        assert action == base_act
        assert action["farmer"] == ["PASS"]

        cand = executor.latest_telemetry.candidates[0]
        assert cand.delta_money_realized == 0.0
        assert cand.projected_asset_value > 0.0
        assert cand.safety_rejection_reason == "SCIENTIFIC_QUARANTINE"

        # =====================================================================
        # REQUIRED WEED TRACE (§15, Updated with Quarantine Rationale)
        # =====================================================================
        print("\n" + "=" * 70)
        print("REQUIRED WEED TRACE (§15) — SCIENTIFIC QUARANTINE")
        print("=" * 70)
        print("STATE & TARGET:")
        print(f"  Current state:             step={obs['step']}, day={obs['day']} [REALIZED]")
        print(f"  weed location:             (4, 4) [REALIZED]")
        print(f"  candidate action:          DIG [PROPOSED]")
        print(f"  future dependency:         PLANT WHEAT on (4, 4) at offset +1 [HEURISTIC]")
        print(f"  plant timing:              step {obs['step'] + 1} [UNVERIFIED]")
        print(f"  growth duration:           48 turns [GAME CONSTANT]")
        print(f"  harvest timing:            step {obs['step'] + 1 + 48} [UNVERIFIED]")
        print(f"  sale timing:               step {obs['step'] + 1 + 48 + 1} [UNVERIFIED]")
        print(f"  terminal cutoff:           step 718 (final step 719) [GAME CONSTANT]")
        print("\nECONOMIC VALUATION & QUARANTINE STATUS:")
        print(f"  realized simulation delta: ${val.realized_delta_money:.2f} [REALIZED]")
        print(f"  projected gross profit:    ${val.projected_gross_profit:.2f} [HEURISTIC]")
        print(f"  labor/opportunity cost:    ${val.action_opportunity_cost:.4f} [UNVALIDATED /24]")
        print(f"  final net asset value:     +${val.net_projected_asset_value:.2f} [HYPOTHETICAL]")
        print(f"  scientific status:         {MECHANISM_REGISTRY['LOCAL_WEED_DIG']['status'].value}")
        print(f"  governance decision:       {executor.latest_telemetry.decision} ({executor.latest_telemetry.abstain_reason})")
        print(f"  returned action:           {action['farmer']} (exact baseline)")
        print("=" * 70 + "\n")

    def test_category_h_weed_research_override_can_commit(self, weed_obstruction_obs):
        """When research branch explicitly enables LOCAL_WEED_DIG, mechanism can commit."""
        obs = copy.deepcopy(weed_obstruction_obs)
        obs["step"] = 100
        obs["private"]["shed"]["WHEAT"] = 0
        obs["private"]["seeds"]["WHEAT"] = 2
        obs["farms"][0]["money"] = 2000.0

        base_act = {"farmer": ["PASS"], "hands": [["PASS"]], "market": []}
        continuation = [
            {"farmer": ["PLANT", "WHEAT"], "hands": [["PASS"]], "market": []}
            for _ in range(12)
        ]
        research_config = AECConfig(
            enabled_mechanisms=("LOCAL_WEED_DIG", "FRONTLOAD_ORDERS", "TERMINAL_LIQUIDATION", "PHASE_SHUTDOWN"),
            quarantined_mechanisms=()
        )
        adapter = BackboneAdapter(
            agent_fn=lambda o, c: copy.deepcopy(base_act),
            continuation_provider=lambda s, h, p, nh: continuation[:h-1],
            config=research_config
        )
        executor = AECExecutor(backbone_adapter=adapter, config=research_config)
        action = executor.act(obs)

        # In research mode with quarantine lifted, the mechanism commits
        assert action["farmer"] == ["DIG"]
        assert executor.latest_telemetry.decision == "COMMIT"
        assert executor.latest_telemetry.committed_mechanism == "LOCAL_WEED_DIG"

    def test_quarantining_weed_does_not_affect_active_mechanisms(self, normal_opening_obs, terminal_proximity_obs):
        """Quarantining LOCAL_WEED_DIG leaves FRONTLOAD, TERMINAL_LIQUIDATION, PHASE_SHUTDOWN intact (§3)."""
        config = AECConfig()
        assert "LOCAL_WEED_DIG" not in config.enabled_mechanisms
        assert "LOCAL_WEED_DIG" in config.quarantined_mechanisms
        assert "FRONTLOAD_ORDERS" in config.enabled_mechanisms
        assert "TERMINAL_LIQUIDATION" in config.enabled_mechanisms
        assert "PHASE_SHUTDOWN" in config.enabled_mechanisms

        # FRONTLOAD_ORDERS still detects and commits under default config
        obs = copy.deepcopy(normal_opening_obs)
        obs["private"]["shed"]["WHEAT"] = 50
        obs["farms"][1]["tiles"][0][0] = {"kind": "PLANT", "crop": "WHEAT", "yield_units": 50, "age": 48}
        baseline = {"farmer": ["PASS"], "hands": [], "market": [["HIRE", 1], ["SELL", "WHEAT", 50]]}
        adapter = BackboneAdapter(agent_fn=lambda o, c: copy.deepcopy(baseline), config=config)
        executor = AECExecutor(backbone_adapter=adapter, config=config)
        action = executor.act(obs)
        assert executor.latest_telemetry.decision == "COMMIT"
        assert executor.latest_telemetry.committed_mechanism == "FRONTLOAD_ORDERS"

    def test_category_i_weed_false_positive_prevention(self, weed_obstruction_obs):
        """Weed dig without downstream dependency is rejected (no false-positive commit)."""
        obs = copy.deepcopy(weed_obstruction_obs)
        base_act = {"farmer": ["PASS"], "hands": [["PASS"]], "market": []}
        # Continuation where worker moves away and never interacts with (4, 4)
        continuation = [
            {"farmer": ["NORTH"], "hands": [["PASS"]], "market": []}
            for _ in range(12)
        ]
        adapter = BackboneAdapter(
            agent_fn=lambda o, c: copy.deepcopy(base_act),
            continuation_provider=lambda s, h, p, nh: continuation[:h-1]
        )
        executor = AECExecutor(backbone_adapter=adapter)
        action = executor.act(obs)

        assert action == base_act
        assert executor.latest_telemetry.decision in ("BACKBONE", "ABSTAIN")
        assert executor.latest_telemetry.to_dict()["lifecycle"]["committed"] == 0


# =============================================================================
# CATEGORY J: LABOR COST SEMANTICS
# =============================================================================

class TestCategoryJLaborCostSemantics:
    """Verifies that labor opportunity cost is grounded in Fibonacci hiring economics."""

    def test_fibonacci_hiring_economics_marginal_step_cost(self, normal_opening_obs):
        """Labor cost per step scales with Fibonacci daily hiring rate / 24 steps."""
        # hires_today = 0 -> fib(0) = 1 -> 1 / 24 = 0.04167
        obs0 = copy.deepcopy(normal_opening_obs)
        obs0["farms"][0]["hires_today"] = 0
        state0 = build_economic_state(obs0)
        eval0 = DownstreamAssetEvaluator()
        val0 = eval0.evaluate_weed_removal((4, 4), 0, state0)
        assert round(val0.action_opportunity_cost, 4) == round(1.0 / 24.0, 4)

        # hires_today = 3 -> fib(3) = 3 -> 3 / 24 = 0.125
        obs3 = copy.deepcopy(normal_opening_obs)
        obs3["farms"][0]["hires_today"] = 3
        state3 = build_economic_state(obs3)
        val3 = eval0.evaluate_weed_removal((4, 4), 0, state3)
        assert round(val3.action_opportunity_cost, 4) == round(3.0 / 24.0, 4)

        # Displacing active harvest costs task value (>= $25)
        val_harvest = eval0.evaluate_weed_removal(
            (4, 4), 0, state0, baseline_worker_action=["HARVEST"]
        )
        assert val_harvest.action_opportunity_cost >= 25.0


# =============================================================================
# CATEGORIES K, L: ROUTE-TAPE SPATIAL CONSISTENCY & REJECTION (Fix C)
# =============================================================================

class TestCategoryKLSpatialConsistency:
    """Verifies route-tape spatial consistency and fail-closed rejection of desynchronization."""

    def test_case_a_candidate_market_only_preserves_spatial_consistency(self, normal_opening_obs):
        """CASE A: Candidate mutates market only; worker position matches baseline tape."""
        state = build_economic_state(normal_opening_obs)
        base_act = {"farmer": ["SOUTH"], "hands": [], "market": [["HIRE", 1]]}
        continuation = [
            {"farmer": ["SOUTH"], "hands": [], "market": []},
            {"farmer": ["EAST"], "hands": [], "market": []},
        ]
        patch = CoupledPatch("P_MKT", "OPP_MKT", market_mutations=[], mechanism_family="FRONTLOAD_ORDERS")
        sim = CounterfactualSimulator()
        outcome = sim.evaluate(patch, base_act, state, horizon=3, continuation_trajectory=continuation)

        assert outcome.spatial_consistency_ok is True
        assert outcome.desynchronization_reason == ""

    def test_case_b_and_l_movement_mutation_detects_desynchronization_and_rejects(self, normal_opening_obs):
        """CASE B & L: Candidate replaces MOVE with DIG; continuation commands desynchronize and fail closed."""
        state = build_economic_state(normal_opening_obs)
        # Baseline moves SOUTH from [4, 4] to [4, 5]
        base_act = {"farmer": ["SOUTH"], "hands": [], "market": []}
        # Candidate replaces SOUTH with DIG at [4, 4]
        patch = CoupledPatch("P_WEED", "OPP_WEED", worker_mutations={0: ["DIG"]}, mechanism_family="LOCAL_WEED_DIG")
        # Continuation expects worker to be at [4, 5] and plants/moves there
        continuation = [
            {"farmer": ["EAST"], "hands": [], "market": []},
            {"farmer": ["EAST"], "hands": [], "market": []},
        ]
        sim = CounterfactualSimulator()
        outcome = sim.evaluate(patch, base_act, state, horizon=3, continuation_trajectory=continuation, trace=True)

        # Spatial consistency check catches coordinate divergence
        assert outcome.spatial_consistency_ok is False
        assert "spatially desynchronized" in outcome.desynchronization_reason
        assert outcome.candidate_trace[1]["worker_actions"][0] == ["PASS"]

        # SafetyChecker rejects candidate
        checker = SafetyChecker()
        passed_safety, checks, abstain_reason = checker.verify(patch, outcome, state, base_act)
        assert passed_safety is False
        assert checks["spatial_consistency_ok"] is False
        assert "spatial desynchronization" in abstain_reason

        # WinModel also rejects candidate
        win_model = WinModel()
        eval_res = win_model.evaluate(patch, outcome, state, continuation)
        assert eval_res.is_superior is False
        assert "spatial desynchronization" in eval_res.rationale


# =============================================================================
# CATEGORIES M, N, O, P, Q: PASSTHROUGH, REPLAY, SAFETY & REDUNDANCY
# =============================================================================

class TestCategoryMNOPQSystemIntegrity:
    """Verifies determinism, safety invariants, and defense-in-depth redundancy."""

    def test_category_m_baseline_passthrough(self, normal_opening_obs):
        """When no opportunities exist, baseline action is passed through exactly."""
        base_act = {"farmer": ["SOUTH"], "hands": [], "market": []}
        adapter = BackboneAdapter(agent_fn=lambda o, c: copy.deepcopy(base_act))
        executor = AECExecutor(backbone_adapter=adapter)
        action = executor.act(normal_opening_obs)

        assert action == base_act
        assert executor.latest_telemetry.decision == "BACKBONE"

    def test_category_n_deterministic_replay(self, normal_opening_obs):
        """Repeated invocations on identical state yield identical decisions and traces."""
        base_act = {"farmer": ["PASS"], "hands": [], "market": [["HIRE", 1], ["SELL", "WHEAT", 10]]}
        adapter1 = BackboneAdapter(agent_fn=lambda o, c: copy.deepcopy(base_act))
        adapter2 = BackboneAdapter(agent_fn=lambda o, c: copy.deepcopy(base_act))
        exec1 = AECExecutor(backbone_adapter=adapter1)
        exec2 = AECExecutor(backbone_adapter=adapter2)

        res1 = exec1.act(normal_opening_obs)
        res2 = exec2.act(normal_opening_obs)

        assert res1 == res2
        t1 = exec1.latest_telemetry.to_dict()
        t2 = exec2.latest_telemetry.to_dict()
        # Telemetry decision, candidate counts, and lifecycle must be bit-exact
        assert t1["decision"] == t2["decision"]
        assert t1["opp_count"] == t2["opp_count"]
        assert t1["cand_count"] == t2["cand_count"]
        assert t1["sim_count"] == t2["sim_count"]
        assert t1["lifecycle"] == t2["lifecycle"]

    def test_category_o_safety_rejection_out_of_bounds(self, normal_opening_obs):
        """Out of bounds worker mutation is safely rejected."""
        state = build_economic_state(normal_opening_obs)
        base_act = {"farmer": ["PASS"], "hands": [], "market": []}
        # Worker at (0, 0) moving NORTH is illegal
        normal_opening_obs["farms"][0]["farmer"] = [0, 0]
        state_corner = build_economic_state(normal_opening_obs)

        patch = CoupledPatch("P_BAD", "OPP_BAD", worker_mutations={0: ["NORTH"]})
        outcome = SimulationOutcome(
            candidate_final_money=100.0, baseline_final_money=100.0,
            delta_our_money=0.0, candidate_opp_final_money=100.0,
            baseline_opp_final_money=100.0, delta_opponent_money=0.0,
            delta_terminal_margin=0.0, candidate_overflow_units=0,
            candidate_sold={}, baseline_sold={}, intermediate_solvency_ok=True,
            horizon=2
        )
        checker = SafetyChecker()
        passed, checks, reason = checker.verify(patch, outcome, state_corner, base_act)
        assert passed is False
        assert checks["feasibility_ok"] is False

    def test_category_p_terminal_redundancy_defense_in_depth(self, terminal_proximity_obs):
        """TERMINAL_LIQUIDATION remains defense-in-depth: when shed empty, it abstains."""
        obs = copy.deepcopy(terminal_proximity_obs)
        obs["private"]["shed"] = {}  # Empty shed (normal V3 endgame)
        base_act = {"farmer": ["PASS"], "hands": [["PASS"]], "market": []}
        adapter = BackboneAdapter(agent_fn=lambda o, c: copy.deepcopy(base_act))
        executor = AECExecutor(backbone_adapter=adapter)
        action = executor.act(obs)

        assert action == base_act
        assert executor.latest_telemetry.decision == "BACKBONE"

    def test_category_q_phase_shutdown_redundancy_defense_in_depth(self, terminal_proximity_obs):
        """PHASE_SHUTDOWN remains defense-in-depth: when no unfeasible seed bought, it abstains."""
        obs = copy.deepcopy(terminal_proximity_obs)
        obs["step"] = 650
        base_act = {"farmer": ["PASS"], "hands": [["PASS"]], "market": []}
        adapter = BackboneAdapter(agent_fn=lambda o, c: copy.deepcopy(base_act))
        executor = AECExecutor(backbone_adapter=adapter)
        action = executor.act(obs)

        assert action == base_act
        assert executor.latest_telemetry.decision == "BACKBONE"


# =============================================================================
# C++ SIM.HPP PARITY & ORDER-POSITION VERIFICATION (§5, §6, §7)
# =============================================================================

class TestMarketLockstepCppParity:
    """Proves exact parity with ground-truth sim.hpp:578-617 two-phase lockstep semantics."""

    def test_simulator_matches_cpp_market_lockstep_semantics(self, normal_opening_obs):
        """Direct parity test against independently derived sim.hpp values (§5, §6).
        
        Evaluates the authoritative known scenario:
        Baseline:
          Player 0: [["HIRE", 1], ["SELL", "WHEAT", 50]]
          Player 1: [["SELL", "WHEAT", 50]]
        Candidate:
          Player 0: [["SELL", "WHEAT", 50], ["HIRE", 1]]
          Player 1: [["SELL", "WHEAT", 50]]
        Starting wheat inventory: 10,000
        
        Expected engine semantics:
          BASELINE: Opponent sells 50 units first into 10000..10049. Player 0 sells into 10050..10099.
          CANDIDATE: Both players sell concurrently in slot 0 quoting against common pre-commit snapshot.
          
        Ground-truth sim.hpp result:
          candidate player money advantage: +$31.00
          opponent money delta:             -$30.00
          terminal margin delta:            +$61.00
        """
        # Independent mathematical derivation from authoritative pricing formula
        expected_p1_base_rev = sum(compute_market_price("WHEAT", 10000 + k) for k in range(50))
        expected_p0_base_rev = sum(compute_market_price("WHEAT", 10050 + k) for k in range(50))
        assert expected_p1_base_rev == 1127, f"Expected 1127, got {expected_p1_base_rev}"
        assert expected_p0_base_rev == 1066, f"Expected 1066, got {expected_p0_base_rev}"

        # In candidate slot 0, concurrent lockstep: unit k quotes against 10000 + 2*k
        expected_p0_cand_rev = sum(compute_market_price("WHEAT", 10000 + 2 * k) for k in range(50))
        expected_p1_cand_rev = sum(compute_market_price("WHEAT", 10000 + 2 * k) for k in range(50))
        assert expected_p0_cand_rev == 1097, f"Expected 1097, got {expected_p0_cand_rev}"
        assert expected_p1_cand_rev == 1097, f"Expected 1097, got {expected_p1_cand_rev}"

        expected_delta_p0 = float(expected_p0_cand_rev - expected_p0_base_rev)   # +31.00
        expected_delta_p1 = float(expected_p1_cand_rev - expected_p1_base_rev)   # -30.00
        expected_delta_margin = expected_delta_p0 - expected_delta_p1            # +61.00

        assert expected_delta_p0 == 31.00
        assert expected_delta_p1 == -30.00
        assert expected_delta_margin == 61.00

        # Build isolated state matching the exact scenario
        obs = copy.deepcopy(normal_opening_obs)
        obs["day"] = 2
        obs["step"] = 40
        obs["farms"][0]["money"] = 1000.0
        obs["farms"][1]["money"] = 1000.0
        obs["private"]["shed"]["WHEAT"] = 50
        obs["farms"][1]["tiles"][0][0] = {
            "kind": "PLANT", "crop": "WHEAT", "yield_units": 50, "age": 48
        }
        obs["market"]["inventory"]["WHEAT"] = 10000
        obs["market"]["prices"]["WHEAT"] = compute_market_price("WHEAT", 10000)

        econ_state = build_economic_state(obs)
        baseline_action = {
            "farmer": ["PASS"], "hands": [],
            "market": [["HIRE", 1], ["SELL", "WHEAT", 50]]
        }
        candidate_patch = CoupledPatch(
            patch_id="PATCH_FRONTLOAD_PARITY",
            source_opportunity_id="OPP_PARITY",
            market_mutations=[["SELL", "WHEAT", 50], ["HIRE", 1]],
            mechanism_family="FRONTLOAD_ORDERS"
        )

        simulator = CounterfactualSimulator()
        outcome = simulator.evaluate(
            candidate_patch=candidate_patch,
            baseline_action=baseline_action,
            econ_state=econ_state,
            horizon=4
        )

        # Assert exact sim.hpp numbers:
        # Starting cash $1000 - $1 hire cost + $1066 sales = $2065
        assert outcome.baseline_final_money == 2065.0
        # Starting cash $1000 - $1 hire cost + $1097 sales = $2096
        assert outcome.candidate_final_money == 2096.0
        assert outcome.baseline_opp_final_money == 2190.0
        assert outcome.candidate_opp_final_money == 2160.0

        # Exact parity deltas: MUST NOT be +62.0!
        assert outcome.delta_our_money == 31.00, f"Expected +31.0, got {outcome.delta_our_money}"
        assert outcome.delta_opponent_money == -30.00, f"Expected -30.0, got {outcome.delta_opponent_money}"
        assert outcome.delta_terminal_margin == 61.00, f"Expected +61.0 (got {outcome.delta_terminal_margin})"

    def test_order_position_case_a_both_players_sell_same_product(self, normal_opening_obs):
        """CASE A: Both players SELL same product in same slot -> identical pre-commit snapshot."""
        state = build_economic_state(normal_opening_obs)
        rollout = ShadowRolloutState(state)
        rollout.money = 1000.0
        rollout.opp_money = 1000.0
        rollout.shed["WHEAT"] = 50
        rollout.market_inv["WHEAT"] = 10000

        # Slot 0: Both sell 5 units of WHEAT
        execute_market_lockstep(rollout, [["SELL", "WHEAT", 5]], [["SELL", "WHEAT", 5]])

        # Both players quoted from identical pre-commit snapshots per iteration:
        # Expected revenue for each = sum(compute_market_price("WHEAT", 10000 + 2*k) for k in range(5))
        expected_gain = sum(compute_market_price("WHEAT", 10000 + 2 * k) for k in range(5))
        assert rollout.money - 1000.0 == float(expected_gain)
        assert rollout.opp_money - 1000.0 == float(expected_gain)
        assert rollout.money == rollout.opp_money
        assert rollout.market_inv["WHEAT"] == 10010

    def test_order_position_case_b_only_player_0_sells(self, normal_opening_obs):
        """CASE B: Only player 0 SELL -> player 0 quotes from current inventory."""
        state = build_economic_state(normal_opening_obs)
        rollout = ShadowRolloutState(state)
        rollout.money = 1000.0
        rollout.opp_money = 1000.0
        rollout.shed["WHEAT"] = 50
        rollout.market_inv["WHEAT"] = 10000

        execute_market_lockstep(rollout, [["SELL", "WHEAT", 5]], [])

        expected_gain = sum(compute_market_price("WHEAT", 10000 + k) for k in range(5))
        assert rollout.money - 1000.0 == float(expected_gain)
        assert rollout.opp_money == 1000.0
        assert rollout.market_inv["WHEAT"] == 10005

    def test_order_position_case_c_only_player_1_sells(self, normal_opening_obs):
        """CASE C: Only player 1 SELL -> player 1 quotes from current inventory."""
        state = build_economic_state(normal_opening_obs)
        rollout = ShadowRolloutState(state)
        rollout.money = 1000.0
        rollout.opp_money = 1000.0
        rollout.shed["WHEAT"] = 50
        rollout.market_inv["WHEAT"] = 10000

        execute_market_lockstep(rollout, [], [["SELL", "WHEAT", 5]])

        expected_gain = sum(compute_market_price("WHEAT", 10000 + k) for k in range(5))
        assert rollout.opp_money - 1000.0 == float(expected_gain)
        assert rollout.money == 1000.0
        assert rollout.market_inv["WHEAT"] == 10005

    def test_order_position_case_d_different_products(self, normal_opening_obs):
        """CASE D: Player 0 and Player 1 SELL different products -> independent pricing."""
        state = build_economic_state(normal_opening_obs)
        rollout = ShadowRolloutState(state)
        rollout.money = 1000.0
        rollout.opp_money = 1000.0
        rollout.shed["WHEAT"] = 50
        rollout.shed["CARROT"] = 50
        rollout.market_inv["WHEAT"] = 10000
        rollout.market_inv["CARROT"] = 10000

        # Player 0 sells WHEAT, Player 1 sells CARROT
        execute_market_lockstep(rollout, [["SELL", "WHEAT", 5]], [["SELL", "CARROT", 5]])

        expected_wheat_gain = sum(compute_market_price("WHEAT", 10000 + k) for k in range(5))
        expected_carrot_gain = sum(compute_market_price("CARROT", 10000 + k) for k in range(5))
        assert rollout.money - 1000.0 == float(expected_wheat_gain)
        assert rollout.opp_money - 1000.0 == float(expected_carrot_gain)
        assert rollout.market_inv["WHEAT"] == 10005
        assert rollout.market_inv["CARROT"] == 10005

    def test_order_position_case_e_insufficient_inventory_legality(self, normal_opening_obs):
        """CASE E: One side cannot commit due to insufficient inventory/legality -> fail-closed quote/commit."""
        state = build_economic_state(normal_opening_obs)
        rollout = ShadowRolloutState(state)
        rollout.money = 1000.0
        rollout.opp_money = 1000.0
        # Player 0 only has 2 units in shed, but order requests 5
        rollout.shed["WHEAT"] = 2
        rollout.market_inv["WHEAT"] = 10000

        execute_market_lockstep(rollout, [["SELL", "WHEAT", 5]], [["SELL", "WHEAT", 5]])

        # Units 0, 1: both sell concurrently (pre-commit inv 10000, 10002)
        # Unit 2: Player 0 shed is empty -> fails commit! Player 1 continues selling alone for units 2, 3, 4
        assert rollout.cumulative_sold["WHEAT"] == 2
        assert rollout.market_inv["WHEAT"] == 10007  # 2 from P0 + 5 from P1

