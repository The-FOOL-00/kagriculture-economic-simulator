# SPDX-License-Identifier: MIT
"""Unit tests for Phase 019 Uncertainty-Aware Robustness & Decision Audit Engine."""

import pytest
from aec.config import (
    build_phase019_u0_config,
    build_phase019_u1_config,
    build_phase019_u2_config,
    build_phase019_u3_config,
    build_phase019_u4_config,
)
from aec.evaluation.shadow_robustness import (
    RobustnessCategory,
    RobustnessVector,
    ShadowAuditRecord,
    ShadowRobustnessEvaluator,
)


def test_robustness_vector_to_dict():
    vec = RobustnessVector(
        local_delta=50.0,
        long_horizon_delta=85.0,
        terminal_delta=85.0,
        min_neighbor_delta=12.0,
        median_neighbor_delta=80.0,
        max_neighbor_delta=95.0,
        sign_stability=True,
        quantity_sensitivity=10.0,
        timing_sensitivity=5.0,
        macro_boundary_distance=24,
        safety_margin=70.0,
        foundation_relative_delta=52.0,
        runner_up_gap=35.0,
    )
    d = vec.to_dict()
    assert d["local_delta"] == 50.0
    assert d["min_neighbor_delta"] == 12.0
    assert d["sign_stability"] is True
    assert d["safety_margin"] == 70.0
    assert d["runner_up_gap"] == 35.0


def test_shadow_audit_record_to_dict():
    rec = ShadowAuditRecord(
        step=120,
        committed_patch_id="PATCH_TRANCHE_1",
        committed_mechanism="AUTONOMOUS_TRANCHE_ORDER_SYNTHESIZER",
        committed_delta=45.0,
        best_admissible_alt_id="PATCH_TRANCHE_ALT",
        best_admissible_alt_delta=40.0,
        selection_regret=0.0,
        abstention_regret=0.0,
        foundation_patch_id="PATCH_MARKET_TIMING",
        foundation_delta=33.0,
        foundation_opportunity_cost=-12.0,
        robustness_category=RobustnessCategory.R0_ROBUST_POSITIVE,
        would_abstain=False,
    )
    d = rec.to_dict()
    assert d["step"] == 120
    assert d["category"] == "R0_ROBUST_POSITIVE"
    assert d["selection_regret"] == 0.0
    assert d["foundation_opportunity_cost"] == -12.0


def test_robustness_categorization():
    evaluator = ShadowRobustnessEvaluator(
        simulator=None,
        macro_detector=None,
        v3_agent_callable=None,
    )

    class DummyOutcome:
        macro_escalated = False
        macro_induced_continuation_delta = 0.0

    dummy_out = DummyOutcome()

    # 1. R5: Clearly negative
    cat, abstain, _ = evaluator._categorize_candidate(
        comm_delta=-10.0,
        vec=RobustnessVector(),
        neighbor_deltas={},
        committed_outcome=dummy_out,
        fnd_opp_cost=None,
        selection_regret=0.0,
    )
    assert cat == RobustnessCategory.R5_CLEARLY_NEGATIVE
    assert abstain is True

    # 2. R3: Ranking-dependent (foundation strictly better)
    cat, abstain, _ = evaluator._categorize_candidate(
        comm_delta=25.0,
        vec=RobustnessVector(),
        neighbor_deltas={},
        committed_outcome=dummy_out,
        fnd_opp_cost=30.0,  # foundation exceeds by $30
        selection_regret=0.0,
    )
    assert cat == RobustnessCategory.R3_RANKING_DEPENDENT
    assert abstain is True

    # 3. R4: Macro-sensitive
    macro_out = DummyOutcome()
    macro_out.macro_escalated = True
    macro_out.macro_induced_continuation_delta = -150.0
    cat, abstain, _ = evaluator._categorize_candidate(
        comm_delta=30.0,
        vec=RobustnessVector(min_neighbor_delta=10.0, sign_stability=True),
        neighbor_deltas={"q-1": 10.0},
        committed_outcome=macro_out,
        fnd_opp_cost=None,
        selection_regret=0.0,
    )
    assert cat == RobustnessCategory.R4_MACRO_SENSITIVE
    assert abstain is True

    # 4. R1: Sensitive positive (fragile neighbor <= 0)
    cat, abstain, _ = evaluator._categorize_candidate(
        comm_delta=40.0,
        vec=RobustnessVector(min_neighbor_delta=-15.0, sign_stability=False),
        neighbor_deltas={"q+1": -15.0},
        committed_outcome=dummy_out,
        fnd_opp_cost=None,
        selection_regret=0.0,
    )
    assert cat == RobustnessCategory.R1_SENSITIVE_POSITIVE
    assert abstain is True

    # 5. R2: Marginal advantage
    cat, abstain, _ = evaluator._categorize_candidate(
        comm_delta=12.0,
        vec=RobustnessVector(min_neighbor_delta=5.0, sign_stability=True, safety_margin=-3.0),
        neighbor_deltas={"q+1": 5.0},
        committed_outcome=dummy_out,
        fnd_opp_cost=None,
        selection_regret=0.0,
    )
    assert cat == RobustnessCategory.R2_MARGINAL
    assert abstain is False

    # 6. R0: Robustly positive
    cat, abstain, _ = evaluator._categorize_candidate(
        comm_delta=50.0,
        vec=RobustnessVector(min_neighbor_delta=20.0, sign_stability=True, safety_margin=35.0),
        neighbor_deltas={"q-1": 20.0, "q+1": 45.0},
        committed_outcome=dummy_out,
        fnd_opp_cost=-10.0,
        selection_regret=0.0,
    )
    assert cat == RobustnessCategory.R0_ROBUST_POSITIVE
    assert abstain is False


def test_config_arm_isolation():
    u0 = build_phase019_u0_config()
    u1 = build_phase019_u1_config()
    u2 = build_phase019_u2_config()
    u3 = build_phase019_u3_config()
    u4 = build_phase019_u4_config()

    # U0 has reservation ON, discrimination ON, shadow OFF, gates OFF
    assert u0.enable_funnel_reservation is True
    assert u0.enable_market_patch_discrimination is True
    assert u0.enable_shadow_robustness_audit is False
    assert u0.enable_robust_abstention_gate is False

    # U1 differs from U0 SOLELY by enable_shadow_robustness_audit=True
    assert u1.enable_shadow_robustness_audit is True
    assert u1.enable_robust_abstention_gate is False
    assert u1.enable_robust_relative_selection is False

    # U2 has robust abstention gate ON
    assert u2.enable_shadow_robustness_audit is True
    assert u2.enable_robust_abstention_gate is True
    assert u2.enable_robust_relative_selection is False

    # U3 has relative selection ON
    assert u3.enable_shadow_robustness_audit is True
    assert u3.enable_robust_relative_selection is True
    assert u3.enable_robust_abstention_gate is False

    # U4 has adaptive breadth ON
    assert u4.enable_shadow_robustness_audit is True
    assert u4.enable_adaptive_shadow_breadth is True
