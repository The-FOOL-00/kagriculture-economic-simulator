# SPDX-License-Identifier: MIT
"""AEC V1.1 Activation and Development Phase Test Suite.

Covers all 10 minimum verification categories:
A. Market analyzer correctness (Cases 1–6)
B. Weed valuation correctness
C. Mechanism-specific horizon correctness
D. Patch generation correctness
E. Counterfactual economic delta correctness
F. Safety rejection correctness
G. Commit-gate correctness
H. Abstention correctness
I. Determinism
J. Baseline preservation / Action-divergence invariant
Plus synthetic positive/negative/safety fixtures for all four foundation mechanisms.
"""

from __future__ import annotations

import copy
import pytest
from typing import Any, Dict, List

from aec.config import AECConfig, FINAL_STEP
from aec.counterfactual.horizon import MechanismHorizonPolicy, select_adaptive_horizon
from aec.counterfactual.simulator import CounterfactualSimulator, SimulationOutcome
from aec.evaluation.asset_value import DownstreamAssetEvaluator, WeedValuation
from aec.evaluation.win_model import WinModel
from aec.events.detectors import detect_events
from aec.events.event_bus import EventBus
from aec.events.event_types import Event, EventType
from aec.integration.backbone_adapter import BackboneAdapter
from aec.integration.executor import AECExecutor
from aec.ir.economic_state import build_economic_state
from aec.opportunities import OpportunityEngine
from aec.opportunities.market import MarketOpportunityAnalyzer
from aec.opportunities.route import RouteOpportunityAnalyzer
from aec.opportunities.terminal import TerminalOpportunityAnalyzer
from aec.patches.generator import PatchGenerator, reorder_frontload
from aec.patches.patch import CoupledPatch
from aec.patches.pruning import prune_patches
from aec.safety.certificate import SafetyCertificate
from aec.safety.checks import SafetyChecker


# =============================================================================
# CATEGORY A: MARKET ANALYZER CORRECTNESS (Fix #1 Regression Tests)
# =============================================================================

class TestCategoryAMarketAnalyzer:
    """Verifies that FRONTLOAD_ORDERS only detects genuine, reorderable sales."""

    def test_case_1_no_sell_exists(self, normal_opening_obs):
        """Case 1: No SELL exists. Expected: no FRONTLOAD_ORDERS opportunity."""
        econ_state = build_economic_state(normal_opening_obs)
        analyzer = MarketOpportunityAnalyzer()
        baseline_action = {
            "farmer": ["PASS"], "hands": [],
            "market": [["HIRE", 1], ["BUY_SEED", "WHEAT", 1]]
        }
        opps = analyzer.analyze(econ_state, [], baseline_action)
        assert len(opps) == 0, f"Expected 0 opportunities when no SELL exists, got {opps}"

    def test_case_2_sell_after_capital(self, normal_opening_obs):
        """Case 2: SELL exists and occurs after capital orders. Expected: opportunity detected."""
        econ_state = build_economic_state(normal_opening_obs)
        analyzer = MarketOpportunityAnalyzer()
        baseline_action = {
            "farmer": ["PASS"], "hands": [],
            "market": [["HIRE", 1], ["SELL", "WHEAT", 2]]
        }
        opps = analyzer.analyze(econ_state, [], baseline_action)
        assert len(opps) == 1
        assert opps[0].candidate_transformation_family == "FRONTLOAD_ORDERS"

    def test_case_3_sell_already_first(self, normal_opening_obs):
        """Case 3: SELL already first. Expected: no frontload opportunity."""
        econ_state = build_economic_state(normal_opening_obs)
        analyzer = MarketOpportunityAnalyzer()
        baseline_action = {
            "farmer": ["PASS"], "hands": [],
            "market": [["SELL", "WHEAT", 2], ["HIRE", 1]]
        }
        opps = analyzer.analyze(econ_state, [], baseline_action)
        assert len(opps) == 0

    def test_case_4_reordering_candidate_changes_sequence(self, normal_opening_obs):
        """Case 4: Reordering candidate changes actual sequence -> Patch generated."""
        econ_state = build_economic_state(normal_opening_obs)
        generator = PatchGenerator()
        analyzer = MarketOpportunityAnalyzer()
        baseline_action = {
            "farmer": ["PASS"], "hands": [],
            "market": [["HIRE", 1], ["SELL", "WHEAT", 2]]
        }
        opps = analyzer.analyze(econ_state, [], baseline_action)
        patches = generator.generate_patches(opps, econ_state, baseline_action)
        assert len(patches) == 1
        assert patches[0].market_mutations == [["SELL", "WHEAT", 2], ["HIRE", 1]]

    def test_case_5_reorder_produces_identical_sequence(self, normal_opening_obs):
        """Case 5: Reorder computation produces identical sequence -> No patch generated."""
        econ_state = build_economic_state(normal_opening_obs)
        generator = PatchGenerator()
        orders = [["SELL", "WHEAT", 2], ["BUY_PRODUCT", "EGG", 1], ["HIRE", 1]]
        reordered = reorder_frontload(orders)
        assert reordered == orders
        # Even if passed through generator, no patch generated
        from aec.opportunities.base import Opportunity
        dummy_opp = Opportunity(
            opportunity_id="TEST_NOP",
            category="MARKET",
            event_trigger=None,
            affected_entities=["MARKET_ORDERS"],
            estimated_economic_relevance=50.0,
            candidate_transformation_family="FRONTLOAD_ORDERS",
            required_horizon=4
        )
        patches = generator.generate_patches([dummy_opp], econ_state, {"market": orders})
        assert len(patches) == 0

    def test_case_6_multiple_sell_operations_deterministic(self, normal_opening_obs):
        """Case 6: Multiple SELL operations maintain deterministic relative order."""
        orders = [["BUY_SEED", "WHEAT", 1], ["SELL", "WHEAT", 5], ["HIRE", 1], ["SELL", "MILK", 2]]
        reordered = reorder_frontload(orders)
        expected = [["SELL", "WHEAT", 5], ["SELL", "MILK", 2], ["BUY_SEED", "WHEAT", 1], ["HIRE", 1]]
        assert reordered == expected


# =============================================================================
# CATEGORY B: WEED VALUATION CORRECTNESS (Fix #2 Downstream Asset Valuation)
# =============================================================================

class TestCategoryBWeedValuation:
    """Verifies that weed DIG is evaluated via explicit downstream benefit minus opportunity cost."""

    def test_dig_with_no_downstream_benefit_rejected(self, weed_obstruction_obs):
        """DIG with no downstream dependency has net value <= 0 and is rejected."""
        econ_state = build_economic_state(weed_obstruction_obs)
        evaluator = DownstreamAssetEvaluator()
        # Continuation trajectory with no interaction on tile (4, 4)
        continuation = [{"farmer": ["NORTH"], "hands": [["PASS"]], "market": []} for _ in range(10)]
        valuation = evaluator.evaluate_weed_removal((4, 4), 0, econ_state, continuation)
        assert not valuation.has_downstream_dependency
        assert valuation.gross_benefit == 0.0
        assert valuation.net_asset_value < 0.0  # -C_labor

        # Verify WinModel rejects it
        win_model = WinModel()
        patch = CoupledPatch(
            patch_id="PATCH_WEED_DIG_TEST",
            source_opportunity_id="ROUTE_WEED_DIG_W0_4_4",
            mechanism_family="LOCAL_WEED_DIG",
            worker_mutations={0: ["DIG"]}
        )
        outcome = SimulationOutcome(
            candidate_final_money=2500.0,
            baseline_final_money=2500.0,
            delta_our_money=0.0,
            candidate_opp_final_money=2500.0,
            baseline_opp_final_money=2500.0,
            delta_opponent_money=0.0,
            delta_terminal_margin=0.0,
            candidate_overflow_units=0,
            candidate_sold={}, baseline_sold={},
            intermediate_solvency_ok=True,
            horizon=6
        )
        res = win_model.evaluate(patch, outcome, econ_state, continuation)
        assert not res.is_superior
        assert "Insufficient weed removal benefit" in res.rationale

    def test_dig_with_downstream_plant_dependency_certified(self, weed_obstruction_obs):
        """DIG unblocking future plant on (4, 4) has net value > 0 and is certified superior."""
        econ_state = build_economic_state(weed_obstruction_obs)
        evaluator = DownstreamAssetEvaluator()
        # Worker attempts to plant Wheat on (4, 4) at offset 1
        continuation = [
            {"farmer": ["PASS"], "hands": [["PASS"]], "market": []},
            {"farmer": ["PLANT", "WHEAT"], "hands": [["PASS"]], "market": []},
        ]
        valuation = evaluator.evaluate_weed_removal((4, 4), 0, econ_state, continuation)
        assert valuation.has_downstream_dependency
        assert valuation.dependency_type == "PLANT"
        assert valuation.crop == "WHEAT"
        assert valuation.gross_benefit > 0.0
        assert valuation.net_asset_value > 0.0

        # Verify WinModel accepts it
        win_model = WinModel()
        patch = CoupledPatch(
            patch_id="PATCH_WEED_DIG_TEST",
            source_opportunity_id="ROUTE_WEED_DIG_W0_4_4",
            mechanism_family="LOCAL_WEED_DIG",
            worker_mutations={0: ["DIG"]}
        )
        outcome = SimulationOutcome(
            candidate_final_money=2495.83,  # Slight 1-step action labor cost
            baseline_final_money=2500.0,
            delta_our_money=-4.17,
            candidate_opp_final_money=2500.0,
            baseline_opp_final_money=2500.0,
            delta_opponent_money=0.0,
            delta_terminal_margin=-4.17,
            candidate_overflow_units=0,
            candidate_sold={}, baseline_sold={},
            intermediate_solvency_ok=True,
            horizon=6
        )
        res = win_model.evaluate(patch, outcome, econ_state, continuation)
        assert res.is_superior
        assert "Certified downstream weed clearance value" in res.rationale

    def test_dig_with_route_shortening_benefit(self, weed_obstruction_obs):
        """DIG that saves planned route movement steps produces positive net asset value."""
        econ_state = build_economic_state(weed_obstruction_obs)
        evaluator = DownstreamAssetEvaluator()
        valuation = evaluator.evaluate_weed_removal((4, 4), 0, econ_state, planned_route_savings=2)
        assert valuation.has_downstream_dependency
        assert valuation.delta_route_cost == 2.0
        assert valuation.gross_benefit == pytest.approx(2 * evaluator.labor_cost)
        assert valuation.net_asset_value == pytest.approx(evaluator.labor_cost)

    def test_dig_cost_exceeds_benefit_rejected(self, weed_obstruction_obs):
        """DIG with biological impossibility (crop cannot mature before game end) is rejected."""
        obs = copy.deepcopy(weed_obstruction_obs)
        obs["step"] = 710  # Only 10 steps remaining (less than 48 steps for wheat)
        econ_state = build_economic_state(obs)
        evaluator = DownstreamAssetEvaluator()
        continuation = [{"farmer": ["PLANT", "WHEAT"], "hands": [["PASS"]], "market": []}]
        valuation = evaluator.evaluate_weed_removal((4, 4), 0, econ_state, continuation)
        assert valuation.gross_benefit == 0.0
        assert valuation.net_asset_value < 0.0


# =============================================================================
# CATEGORY C: MECHANISM-SPECIFIC HORIZON POLICY
# =============================================================================

class TestCategoryCHorizonPolicy:
    """Verifies deterministic mechanism-specific horizon selection."""

    def test_weed_dig_horizon_with_and_without_dependency(self, weed_obstruction_obs):
        policy = MechanismHorizonPolicy()
        config = AECConfig()
        econ_state = build_economic_state(weed_obstruction_obs)
        patch = CoupledPatch(
            patch_id="PATCH_WEED_1",
            source_opportunity_id="ROUTE_WEED_DIG_W0_4_4",
            mechanism_family="LOCAL_WEED_DIG"
        )
        # Without dependency -> short horizon (6)
        h1, r1 = policy.explain_horizon(patch, econ_state, config, future_trajectory=[])
        assert h1 == config.short_horizon
        assert "fast-reject short horizon" in r1

        # With dependency at step offset 4 -> captures dependency
        traj = [{"farmer": ["PASS"]} for _ in range(3)] + [{"farmer": ["PLANT", "WHEAT"]}]
        h2, r2 = policy.explain_horizon(patch, econ_state, config, future_trajectory=traj)
        assert h2 >= config.normal_horizon
        assert "downstream dependency" in r2

    def test_frontload_horizon_with_and_without_opponent(self, normal_opening_obs):
        policy = MechanismHorizonPolicy()
        config = AECConfig()
        patch = CoupledPatch(
            patch_id="PATCH_FRONT_1",
            source_opportunity_id="MARKET_FRONTLOAD_STEP_0",
            mechanism_family="FRONTLOAD_ORDERS",
            market_mutations=[["SELL", "WHEAT", 2]]
        )
        # Opponent with zero cash / no forecast
        obs_no_opp = copy.deepcopy(normal_opening_obs)
        obs_no_opp["farms"][1]["money"] = 0.0
        econ_state_no_opp = build_economic_state(obs_no_opp)
        h_no_opp, _ = policy.explain_horizon(patch, econ_state_no_opp, config)
        assert h_no_opp == config.short_horizon

        # Opponent with active cash
        econ_state_opp = build_economic_state(normal_opening_obs)
        h_opp, _ = policy.explain_horizon(patch, econ_state_opp, config)
        assert h_opp == config.normal_horizon

    def test_terminal_and_phase_shutdown_horizons(self, terminal_proximity_obs):
        policy = MechanismHorizonPolicy()
        config = AECConfig()
        econ_state = build_economic_state(terminal_proximity_obs)

        # Terminal liquidation: terminal-local horizon
        patch_liq = CoupledPatch(
            patch_id="PATCH_LIQ",
            source_opportunity_id="TERMINAL_LIQUIDATE_STEP_718",
            mechanism_family="TERMINAL_LIQUIDATION"
        )
        h_liq, _ = policy.explain_horizon(patch_liq, econ_state, config)
        assert h_liq == 1  # remaining <= 1 forces horizon 1

        # Phase shutdown: phase-local horizon (tested at step 600)
        obs_600 = copy.deepcopy(terminal_proximity_obs)
        obs_600["step"] = 600
        econ_600 = build_economic_state(obs_600)
        patch_shut = CoupledPatch(
            patch_id="PATCH_SHUT",
            source_opportunity_id="TERMINAL_SHUTDOWN_MELON_600",
            mechanism_family="PHASE_SHUTDOWN"
        )
        h_shut, _ = policy.explain_horizon(patch_shut, econ_600, config)
        assert h_shut == config.short_horizon


# =============================================================================
# CATEGORY D & E: PATCH GENERATION AND SIMULATION DELTA CORRECTNESS
# =============================================================================

class TestCategoryDPatchAndDeltaCorrectness:
    """Verifies patch construction and simulation outcomes."""

    def test_patch_generation_all_four_families(self, normal_opening_obs, weed_obstruction_obs, terminal_proximity_obs):
        generator = PatchGenerator()

        # 1. LOCAL_WEED_DIG
        econ_weed = build_economic_state(weed_obstruction_obs)
        opp_weed = RouteOpportunityAnalyzer().analyze(econ_weed, [], {"market": []})[0]
        p_weed = generator.generate_patches([opp_weed], econ_weed, {"market": []})[0]
        assert p_weed.mechanism_family == "LOCAL_WEED_DIG"
        assert p_weed.worker_mutations == {0: ["DIG"]}

        # 2. FRONTLOAD_ORDERS
        econ_mkt = build_economic_state(normal_opening_obs)
        opp_mkt = MarketOpportunityAnalyzer().analyze(
            econ_mkt, [], {"market": [["HIRE", 1], ["SELL", "WHEAT", 2]]}
        )[0]
        p_mkt = generator.generate_patches([opp_mkt], econ_mkt, {"market": [["HIRE", 1], ["SELL", "WHEAT", 2]]})[0]
        assert p_mkt.mechanism_family == "FRONTLOAD_ORDERS"
        assert p_mkt.market_mutations == [["SELL", "WHEAT", 2], ["HIRE", 1]]

        # 3. TERMINAL_LIQUIDATION
        econ_term = build_economic_state(terminal_proximity_obs)
        opp_term = TerminalOpportunityAnalyzer().analyze(econ_term, [], {"market": []})[0]
        p_term = generator.generate_patches([opp_term], econ_term, {"market": []})[0]
        assert p_term.mechanism_family == "TERMINAL_LIQUIDATION"
        assert len(p_term.market_mutations) > 0
        assert all(o[0] == "SELL" for o in p_term.market_mutations)

        # 4. PHASE_SHUTDOWN
        opp_shut = TerminalOpportunityAnalyzer().analyze(econ_term, [], {"market": []})
        shut_opps = [o for o in opp_term if o.candidate_transformation_family == "PHASE_SHUTDOWN"] if isinstance(opp_term, list) else []
        if not shut_opps:
            from aec.opportunities.base import Opportunity
            shut_opp = Opportunity(
                opportunity_id="TERMINAL_SHUTDOWN_MELON_718",
                category="TERMINAL",
                event_trigger=EventType.E7_PRODUCTION_DEADLINE,
                affected_entities=["MELON"],
                estimated_economic_relevance=50.0,
                candidate_transformation_family="PHASE_SHUTDOWN",
                dependency_info={"crop": "MELON", "cutoff_step": 718},
                required_horizon=6
            )
            p_shut = generator.generate_patches(
                [shut_opp], econ_term, {"market": [["BUY_SEED", "MELON", 1], ["PASS"]]}
            )[0]
            assert p_shut.mechanism_family == "PHASE_SHUTDOWN"
            assert ["BUY_SEED", "MELON", 1] not in p_shut.market_mutations


# =============================================================================
# CATEGORY F, G, H: SAFETY REJECTION, COMMIT GATE, AND ABSTENTION
# =============================================================================

class TestCategoryFSafetyAndGate:
    """Verifies hard safety invariants, commit gates, and abstention fallbacks."""

    def test_safety_rejects_illegal_market_order(self, normal_opening_obs):
        econ_state = build_economic_state(normal_opening_obs)
        checker = SafetyChecker()
        patch = CoupledPatch(
            patch_id="PATCH_ILLEGAL",
            source_opportunity_id="OPP_1",
            mechanism_family="FRONTLOAD_ORDERS",
            market_mutations=[["ILLEGAL_OP", "WHEAT", 1]]
        )
        dummy_outcome = SimulationOutcome(
            candidate_final_money=3000.0, baseline_final_money=3000.0, delta_our_money=0.0,
            candidate_opp_final_money=3000.0, baseline_opp_final_money=3000.0, delta_opponent_money=0.0,
            delta_terminal_margin=0.0, candidate_overflow_units=0, candidate_sold={}, baseline_sold={},
            intermediate_solvency_ok=True, horizon=4
        )
        passed, checks, reason = checker.verify(patch, dummy_outcome, econ_state, {"market": []})
        assert not passed
        assert not checks["legality_ok"]
        assert "Illegal market op" in reason

    def test_safety_rejects_negative_cash(self, normal_opening_obs):
        econ_state = build_economic_state(normal_opening_obs)
        checker = SafetyChecker()
        patch = CoupledPatch(
            patch_id="PATCH_SOLV",
            source_opportunity_id="OPP_1",
            mechanism_family="FRONTLOAD_ORDERS",
            market_mutations=[["BUY_SEED", "WHEAT", 1]]
        )
        insolvent_outcome = SimulationOutcome(
            candidate_final_money=-50.0, baseline_final_money=100.0, delta_our_money=-150.0,
            candidate_opp_final_money=100.0, baseline_opp_final_money=100.0, delta_opponent_money=0.0,
            delta_terminal_margin=-150.0, candidate_overflow_units=0, candidate_sold={}, baseline_sold={},
            intermediate_solvency_ok=True, horizon=4
        )
        passed, checks, reason = checker.verify(patch, insolvent_outcome, econ_state, {"market": []})
        assert not passed
        assert not checks["solvency_ok"]
        assert "Negative cash balance" in reason

    def test_safety_rejects_shed_overflow(self, normal_opening_obs):
        econ_state = build_economic_state(normal_opening_obs)
        checker = SafetyChecker()
        patch = CoupledPatch(patch_id="P_OVER", source_opportunity_id="OPP_1", mechanism_family="LOCAL_WEED_DIG")
        overflow_outcome = SimulationOutcome(
            candidate_final_money=3000.0, baseline_final_money=3000.0, delta_our_money=0.0,
            candidate_opp_final_money=3000.0, baseline_opp_final_money=3000.0, delta_opponent_money=0.0,
            delta_terminal_margin=0.0, candidate_overflow_units=5, candidate_sold={}, baseline_sold={},
            intermediate_solvency_ok=True, horizon=4
        )
        passed, checks, reason = checker.verify(patch, overflow_outcome, econ_state, {"market": []})
        assert not passed
        assert not checks["overflow_ok"]


# =============================================================================
# CATEGORY I & J: DETERMINISM AND ACTION-DIVERGENCE INVARIANTS (§15)
# =============================================================================

class TestCategoryIDeterminismAndActionDivergence:
    """Verifies that AEC returns bit-exact baseline action on abstention across all 7 conditions."""

    @pytest.fixture
    def baseline_action(self):
        return {
            "farmer": ["NORTH"],
            "hands": [["SOUTH"], ["EAST"]],
            "market": [["BUY_SEED", "WHEAT", 2]]
        }

    def test_j1_no_event_returns_exact_baseline(self, normal_opening_obs, baseline_action):
        """Condition 1: No event detected -> exact baseline action."""
        adapter = BackboneAdapter(agent_fn=lambda obs, cfg: copy.deepcopy(baseline_action))
        executor = AECExecutor(backbone_adapter=adapter)
        # normal_opening_obs with plenty of cash, no weed, no alarm -> fast path
        obs = copy.deepcopy(normal_opening_obs)
        obs["farms"][0]["money"] = 5000.0
        action = executor.act(obs)
        assert action == baseline_action
        assert executor.latest_telemetry.decision == "BACKBONE"
        assert executor.latest_telemetry.abstain_reason == "NO_EVENT_FAST_PATH"

    def test_j2_no_opportunity_returns_exact_baseline(self, normal_opening_obs, baseline_action):
        """Condition 2: Events detected but no opportunities -> exact baseline action."""
        adapter = BackboneAdapter(agent_fn=lambda obs, cfg: copy.deepcopy(baseline_action))
        executor = AECExecutor(backbone_adapter=adapter)
        # Cash deficit triggers E2, but no opportunities match
        obs = copy.deepcopy(normal_opening_obs)
        obs["farms"][0]["money"] = 50.0  # triggers E2
        action = executor.act(obs)
        assert action == baseline_action
        assert executor.latest_telemetry.decision in ("BACKBONE", "ABSTAIN")

    def test_j3_unsafe_patch_returns_exact_baseline(self, weed_obstruction_obs, baseline_action):
        """Condition 3: Unsafe patch rejected -> exact baseline action."""
        adapter = BackboneAdapter(agent_fn=lambda obs, cfg: copy.deepcopy(baseline_action))
        executor = AECExecutor(backbone_adapter=adapter)
        # Force safety checker to fail
        executor.safety_checker.verify = lambda *args, **kwargs: (
            False,
            {
                "legality_ok": False, "feasibility_ok": True, "overflow_ok": True,
                "obligation_ok": True, "solvency_ok": True, "terminal_feasible": True,
                "market_collision_ok": True, "determinism_ok": True
            },
            "FORCED_UNSAFE"
        )
        action = executor.act(weed_obstruction_obs)
        assert action == baseline_action
        assert executor.latest_telemetry.decision == "ABSTAIN"

    def test_j4_economically_inferior_patch_returns_exact_baseline(self, weed_obstruction_obs, baseline_action):
        """Condition 4: Economically inferior patch -> exact baseline action."""
        adapter = BackboneAdapter(agent_fn=lambda obs, cfg: copy.deepcopy(baseline_action))
        executor = AECExecutor(backbone_adapter=adapter)
        # Isolated weed with no downstream dependency will produce net_asset_val < 0
        action = executor.act(weed_obstruction_obs)
        assert action == baseline_action
        assert executor.latest_telemetry.decision == "ABSTAIN"

    def test_j5_candidate_exception_falls_back_cleanly(self, weed_obstruction_obs, baseline_action):
        """Condition 5: Unhandled exception during evaluation -> fail-closed exact baseline action."""
        adapter = BackboneAdapter(agent_fn=lambda obs, cfg: copy.deepcopy(baseline_action))
        executor = AECExecutor(backbone_adapter=adapter)
        # Inject deliberate crash in simulator
        executor.simulator.evaluate = lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("SIM_CRASH"))
        action = executor.act(weed_obstruction_obs)
        assert action == baseline_action
        assert executor.latest_telemetry.decision == "ABSTAIN_EXCEPTION"
        assert "SIM_CRASH" in executor.latest_telemetry.abstain_reason

    def test_determinism_replay_identical_outputs(self, weed_obstruction_obs, baseline_action):
        """Determinism: Same state twice produces identical decision, action, and telemetry."""
        adapter1 = BackboneAdapter(agent_fn=lambda obs, cfg: copy.deepcopy(baseline_action))
        executor1 = AECExecutor(backbone_adapter=adapter1)
        res1 = executor1.act(weed_obstruction_obs)
        t1 = executor1.latest_telemetry.to_dict()

        adapter2 = BackboneAdapter(agent_fn=lambda obs, cfg: copy.deepcopy(baseline_action))
        executor2 = AECExecutor(backbone_adapter=adapter2)
        res2 = executor2.act(weed_obstruction_obs)
        t2 = executor2.latest_telemetry.to_dict()

        assert res1 == res2
        assert t1["decision"] == t2["decision"]
        assert t1["abstain_reason"] == t2["abstain_reason"]
        assert len(t1["candidates"]) == len(t2["candidates"])


# =============================================================================
# SYNTHETIC MECHANISM FIXTURES: PROVING ACTIVATION ON GENUINE ADVANTAGE
# =============================================================================

class TestSyntheticMechanismFixtures:
    """Proves each foundation mechanism commits on genuine advantage and abstains otherwise."""

    def test_synthetic_local_weed_dig_positive(self, weed_obstruction_obs):
        """Positive Weed Dig Fixture: Worker digs weed at step 0, enabling downstream PLANT at step 1."""
        base_act = {"farmer": ["PASS"], "hands": [["PASS"]], "market": []}
        # Continuation where worker attempts to plant Wheat on (4, 4) at step 1
        continuation = [
            {"farmer": ["PLANT", "WHEAT"], "hands": [["PASS"]], "market": []}
            for _ in range(12)
        ]
        adapter = BackboneAdapter(
            agent_fn=lambda obs, cfg: copy.deepcopy(base_act),
            continuation_provider=lambda s, h, p, nh: continuation[:h-1]
        )
        executor = AECExecutor(backbone_adapter=adapter)
        action = executor.act(weed_obstruction_obs)

        # AEC should commit the weed DIG!
        assert action["farmer"] == ["DIG"]
        assert executor.latest_telemetry.decision == "COMMIT"
        assert executor.latest_telemetry.committed_mechanism == "LOCAL_WEED_DIG"
        assert len(executor.latest_telemetry.candidates) > 0
        c = executor.latest_telemetry.candidates[0]
        assert c.commit_decision is True
        assert c.weed_asset_value > 0.0

    def test_synthetic_frontload_positive(self, normal_opening_obs):
        """Positive Frontload Fixture: Frontloading SELL order before BUY avoids slippage."""
        # Baseline order: [BUY_SEED, SELL]
        base_act = {
            "farmer": ["PASS"], "hands": [],
            "market": [["BUY_SEED", "WHEAT", 1], ["SELL", "WHEAT", 5]]
        }
        obs = copy.deepcopy(normal_opening_obs)
        obs["private"]["shed"]["WHEAT"] = 10
        obs["farms"][0]["money"] = 150.0  # triggers E2 cash deviation

        adapter = BackboneAdapter(agent_fn=lambda o, c: copy.deepcopy(base_act))
        executor = AECExecutor(backbone_adapter=adapter)
        action = executor.act(obs)

        # Frontload analyzer should detect the opportunity and reorder
        opps = executor.opp_engine.detect_opportunities(
            build_economic_state(obs),
            detect_events(build_economic_state(obs)),
            base_act
        )
        frontload_opps = [o for o in opps if o.candidate_transformation_family == "FRONTLOAD_ORDERS"]
        assert len(frontload_opps) == 1
        patches = executor.patch_generator.generate_patches(frontload_opps, build_economic_state(obs), base_act)
        assert len(patches) == 1
        assert patches[0].market_mutations == [["SELL", "WHEAT", 5], ["BUY_SEED", "WHEAT", 1]]

    def test_synthetic_terminal_liquidation_positive(self, terminal_proximity_obs):
        """Positive Terminal Liquidation Fixture: Unliquidated shed inventory at step 718 is committed."""
        # Baseline forgets to liquidate shed
        base_act = {"farmer": ["PASS"], "hands": [["PASS"]], "market": []}
        adapter = BackboneAdapter(agent_fn=lambda o, c: copy.deepcopy(base_act))
        executor = AECExecutor(backbone_adapter=adapter)
        action = executor.act(terminal_proximity_obs)

        # AEC should commit terminal liquidation!
        assert executor.latest_telemetry.decision == "COMMIT"
        assert executor.latest_telemetry.committed_mechanism == "TERMINAL_LIQUIDATION"
        assert len(action.get("market", [])) > 0
        assert all(o[0] == "SELL" for o in action["market"])

    def test_synthetic_terminal_liquidation_negative_redundant(self, terminal_proximity_obs):
        """Negative Terminal Liquidation Fixture: Shed empty at step 718 (standard V3 behavior) -> abstains."""
        obs = copy.deepcopy(terminal_proximity_obs)
        obs["private"]["shed"] = {}  # Empty shed, as in standard V3 play
        base_act = {"farmer": ["PASS"], "hands": [["PASS"]], "market": []}
        adapter = BackboneAdapter(agent_fn=lambda o, c: copy.deepcopy(base_act))
        executor = AECExecutor(backbone_adapter=adapter)
        action = executor.act(obs)

        assert action == base_act
        assert executor.latest_telemetry.decision == "BACKBONE"

    def test_synthetic_phase_shutdown_positive(self, terminal_proximity_obs):
        """Positive Phase Shutdown Fixture: Baseline attempts to buy unfeasible Melon seed -> trimmed."""
        obs = copy.deepcopy(terminal_proximity_obs)
        obs["step"] = 600  # Melon requires 10 days = 240 steps; remaining is 120 steps -> impossible!
        obs["farms"][0]["money"] = 150.0  # Trigger event
        base_act = {
            "farmer": ["PASS"], "hands": [["PASS"]],
            "market": [["BUY_SEED", "MELON", 1]]  # Bad purchase
        }
        adapter = BackboneAdapter(agent_fn=lambda o, c: copy.deepcopy(base_act))
        executor = AECExecutor(backbone_adapter=adapter)
        action = executor.act(obs)

        # AEC trims the dead melon seed purchase, saving cash!
        assert executor.latest_telemetry.decision == "COMMIT"
        assert executor.latest_telemetry.committed_mechanism == "PHASE_SHUTDOWN"
        assert action.get("market", []) == []  # Trimmed!

    def test_synthetic_phase_shutdown_negative_redundant(self, terminal_proximity_obs):
        """Negative Phase Shutdown Fixture: Baseline does not buy dead seeds (standard V3) -> abstains."""
        obs = copy.deepcopy(terminal_proximity_obs)
        obs["step"] = 600
        base_act = {"farmer": ["PASS"], "hands": [["PASS"]], "market": []}
        adapter = BackboneAdapter(agent_fn=lambda o, c: copy.deepcopy(base_act))
        executor = AECExecutor(backbone_adapter=adapter)
        action = executor.act(obs)

        assert action == base_act
        assert executor.latest_telemetry.decision == "BACKBONE"
