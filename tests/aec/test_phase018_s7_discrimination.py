# SPDX-License-Identifier: MIT
"""Phase 018 Repair A2: S7/S9 market-patch discrimination tests."""

from types import SimpleNamespace

from aec.config import (
    build_phase015_treatment_config,
    build_phase018_arm_b2_control_config,
    build_phase018_arm_b2_s1_config,
    build_phase018_arm_b2_s1b_config,
    build_robust_qualified_config,
)
from aec.funnel.candidate_funnel import InferenceBudget, OpportunityCandidateFunnel
from aec.ir import build_economic_state
from aec.opportunities.base import Opportunity
from aec.patches.generator import PatchGenerator


def _market_patch(pid, family, relevance, anchor):
    p = SimpleNamespace(
        patch_id=pid,
        opportunity_id="opp_" + pid,
        mechanism_family=family,
        candidate_transformation_family=family,
        market_mutations=[["SELL", "WHEAT", 1]],
        worker_mutations={},
        source_relevance=relevance,
        anchor_index=anchor,
        estimated_economic_value=0.0,
        estimated_economic_relevance=0.0,
        worker_id=0,
        target_pos=(0, 0),
        step=100,
        duration_steps=1,
        detour_cost=0,
        dependency_info={},
        required_cash=0.0,
        estimated_revenue=relevance,
        labor_opportunity_cost=0.0,
        required_shed_space=0,
    )
    return p


def _worker_opp(oid, family, relevance):
    return Opportunity(
        opportunity_id=oid,
        category="LABOR",
        event_trigger=None,
        affected_entities=[0, (2, 3)],
        estimated_economic_relevance=relevance,
        candidate_transformation_family=family,
        required_horizon=8,
    )


def _econ(normal_opening_obs):
    st = build_economic_state(normal_opening_obs)
    st.step = 100
    return st


# --- S7 exemption ---------------------------------------------------------------

def test_s7_collapses_market_patches_when_off(normal_opening_obs):
    st = _econ(normal_opening_obs)
    cands = [_market_patch("p1", "AUTONOMOUS_TRANCHE_ORDER_SYNTHESIZER", 500.0, 0),
             _market_patch("p2", "AUTONOMOUS_TRANCHE_ORDER_SYNTHESIZER", 100.0, 1),
             _market_patch("p3", "DEPENDENCY_AWARE_MARKET_TIMING", 80.0, 0)]
    funnel = OpportunityCandidateFunnel(InferenceBudget(max_exact_simulations=8))
    out, telem = funnel.filter_candidates(list(cands), st)
    assert [c.patch_id for c in out] == ["p1"]  # legacy: single group, first wins
    s7 = next(r for r in telem.stage_records if r.stage.value == "S7_DOMINANCE_PRUNING")
    assert s7.eliminated_count == 2


def test_s7_exempts_market_patches_when_on(normal_opening_obs):
    st = _econ(normal_opening_obs)
    cands = [_market_patch("p1", "AUTONOMOUS_TRANCHE_ORDER_SYNTHESIZER", 500.0, 0),
             _market_patch("p2", "AUTONOMOUS_TRANCHE_ORDER_SYNTHESIZER", 100.0, 1),
             _market_patch("p3", "DEPENDENCY_AWARE_MARKET_TIMING", 80.0, 0)]
    funnel = OpportunityCandidateFunnel(
        InferenceBudget(max_exact_simulations=8), market_discrimination=True)
    out, telem = funnel.filter_candidates(list(cands), st)
    assert sorted(c.patch_id for c in out) == ["p1", "p2", "p3"]
    s7 = next(r for r in telem.stage_records if r.stage.value == "S7_DOMINANCE_PRUNING")
    assert s7.elimination_reasons.get("S7_MARKET_EXEMPT_PASSTHROUGH") == 3


def test_s7_worker_task_collapse_preserved_when_on(normal_opening_obs):
    st = _econ(normal_opening_obs)
    # Cross-family worker/task collapse (test_int_05 semantic) still applies.
    funnel = OpportunityCandidateFunnel(
        InferenceBudget(max_exact_simulations=8), market_discrimination=True)
    out, _ = funnel.filter_candidates(
        [_worker_opp("low", "DYNAMIC_SHADOW_HARVEST", 35.0),
         _worker_opp("high", "ROUTE_COMPRESSION", 70.0)], st)
    assert [o.opportunity_id for o in out] == ["high"]


def test_weed_dig_patch_not_exempt(normal_opening_obs):
    st = _econ(normal_opening_obs)
    weed = _market_patch("weed", "LOCAL_WEED_DIG", 10.0, 0)
    weed.market_mutations = None
    weed.worker_mutations = {0: ["DIG"]}
    cands = [weed, _market_patch("p1", "AUTONOMOUS_TRANCHE_ORDER_SYNTHESIZER", 500.0, 0)]
    funnel = OpportunityCandidateFunnel(
        InferenceBudget(max_exact_simulations=8), market_discrimination=True)
    out, _ = funnel.filter_candidates(list(cands), st)
    # Weed patch joins a legacy worker group; market patch exempt: separate groups.
    assert "p1" in [c.patch_id for c in out]
    assert len(out) == 2


# --- S9 relevance ranking ----------------------------------------------------------

def test_s9_ranks_by_source_relevance_when_on(normal_opening_obs):
    st = _econ(normal_opening_obs)
    cands = [_market_patch("low", "AUTONOMOUS_TRANCHE_ORDER_SYNTHESIZER", 10.0, 0),
             _market_patch("high", "AUTONOMOUS_TRANCHE_ORDER_SYNTHESIZER", 900.0, 0),
             _market_patch("mid", "DEPENDENCY_AWARE_MARKET_TIMING", 80.0, 0)]
    funnel = OpportunityCandidateFunnel(
        InferenceBudget(max_exact_simulations=2), market_discrimination=True)
    out, _ = funnel.filter_candidates(list(cands), st)
    assert [c.patch_id for c in out] == ["high", "mid"]


def test_s9_anchor_orders_within_relevance(normal_opening_obs):
    st = _econ(normal_opening_obs)
    cands = [_market_patch("a2", "AUTONOMOUS_TRANCHE_ORDER_SYNTHESIZER", 500.0, 2),
             _market_patch("a0", "AUTONOMOUS_TRANCHE_ORDER_SYNTHESIZER", 500.0, 0),
             _market_patch("a1", "AUTONOMOUS_TRANCHE_ORDER_SYNTHESIZER", 500.0, 1)]
    funnel = OpportunityCandidateFunnel(
        InferenceBudget(max_exact_simulations=2), market_discrimination=True)
    out, _ = funnel.filter_candidates(list(cands), st)
    assert [c.patch_id for c in out] == ["a0", "a1"]


def test_s9_legacy_key_verbatim_when_off(normal_opening_obs):
    st = _econ(normal_opening_obs)
    cands = [_market_patch("b", "AUTONOMOUS_TRANCHE_ORDER_SYNTHESIZER", 900.0, 0),
             _market_patch("a", "AUTONOMOUS_TRANCHE_ORDER_SYNTHESIZER", 10.0, 0)]
    funnel = OpportunityCandidateFunnel(InferenceBudget(max_exact_simulations=8))
    out, _ = funnel.filter_candidates(list(cands), st)
    # Legacy: single S7 group keeps input-first ("b"); relevance ignored.
    assert [c.patch_id for c in out] == ["b"]


# --- Generator stamping ------------------------------------------------------------

def test_generator_stamps_priority(weed_obstruction_obs):
    from aec.events import detect_events
    st = build_economic_state(weed_obstruction_obs)
    events = detect_events(st)
    base = {"farmer": ["PASS"], "hands": [["PASS"]], "market": []}
    from aec.opportunities import OpportunityEngine
    opps = OpportunityEngine().detect_opportunities(
        st, events, base, max_opportunities=16,
        config=build_phase015_treatment_config())
    assert opps, "fixture must yield opportunities"
    patches = PatchGenerator(config=build_phase015_treatment_config()).generate_patches(
        opps, st, base, config=build_phase015_treatment_config())
    assert patches
    for p in patches:
        assert isinstance(p.source_relevance, float)
        assert isinstance(p.anchor_index, int) and p.anchor_index >= 0
    # Anchor order follows per-opportunity emission sequence.
    by_opp = {}
    for p in patches:
        by_opp.setdefault(p.source_opportunity_id, []).append(p.anchor_index)
    for seq in by_opp.values():
        assert seq == sorted(seq)


# --- Isolation ----------------------------------------------------------------------

def test_b2_configs_differ_only_by_intended_flags():
    s0 = build_phase015_treatment_config()
    s1 = build_phase018_arm_b2_s1_config()
    s1b = build_phase018_arm_b2_s1b_config()
    d0, d1, db = vars(s0), vars(s1), vars(s1b)
    assert [k for k in d0 if d0[k] != d1[k]] == ["enable_market_patch_discrimination"]
    assert [k for k in d1 if d1[k] != db[k]] == ["enable_boundary_safe_quantities"]
    assert s1.enable_boundary_safe_quantities is False
    assert s1.enable_funnel_reservation is False
    assert s1b.enable_funnel_reservation is False
    c0 = build_robust_qualified_config()
    c1 = build_phase018_arm_b2_control_config()
    e0, e1 = vars(c0), vars(c1)
    assert [k for k in e0 if e0[k] != e1[k]] == ["enable_market_patch_discrimination"]


def test_discrimination_off_by_default():
    from aec.config import AECConfig
    assert AECConfig().enable_market_patch_discrimination is False
    assert build_phase015_treatment_config().enable_market_patch_discrimination is False
    assert build_robust_qualified_config().enable_market_patch_discrimination is False
