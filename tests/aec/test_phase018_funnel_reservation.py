# SPDX-License-Identifier: MIT
"""Phase 018 Repair A: funnel reservation tests (§38.1–§38.4, §38.13–§38.15)."""

import hashlib
import os
from types import SimpleNamespace

from aec.config import (
    ENABLED_FOUNDATION_MECHANISMS,
    build_phase015_treatment_config,
    build_phase018_arm_a2_config,
)
from aec.events import detect_events
from aec.funnel.candidate_funnel import OpportunityCandidateFunnel
from aec.funnel.reservation import (
    FunnelReservationPolicy,
    SlotClass,
    apply_reservation,
    reserved_seats_for_k,
)
from aec.integration.backbone_adapter import BackboneAdapter
from aec.integration.executor import AECExecutor
from aec.ir import build_economic_state
from aec.opportunities import OpportunityEngine
from aec.patches.pruning import prune_patches

EXP = "AUTONOMOUS_TRANCHE_ORDER_SYNTHESIZER"
FOUND = "DEPENDENCY_AWARE_MARKET_TIMING"


def _ranked(n_exp, n_found, found_first=False):
    """Build pre-ranked synthetic items (best rank first)."""
    items = []
    if found_first:
        for i in range(n_found):
            items.append(_item(f"F{i}", FOUND, 1000 - i))
        for i in range(n_exp):
            items.append(_item(f"E{i}", EXP, 100 - i))
    else:
        for i in range(n_exp):
            items.append(_item(f"E{i}", EXP, 1000 - i))
        for i in range(n_found):
            items.append(_item(f"F{i}", FOUND, 100 - i))
    return items


def _item(pid, family, value):
    return SimpleNamespace(
        patch_id=pid,
        opportunity_id=pid,
        mechanism_family=family,
        candidate_transformation_family=family,
        estimated_economic_value=value,
        estimated_economic_relevance=value,
        worker_id=0,
        target_pos=(4, 4),
        step=100,
        duration_steps=1,
        detour_cost=0,
        dependency_info={},
        required_cash=0.0,
        estimated_revenue=value,
        labor_opportunity_cost=0.0,
        required_shed_space=0,
        market_mutations=None,
        worker_mutations={},
    )


def _enabled_policy():
    return FunnelReservationPolicy(enabled=True)


# --- §38.1: foundation candidate survives crowding ----------------------------

def test_foundation_survives_crowding():
    items = _ranked(n_exp=20, n_found=1)  # foundation ranked dead last
    selected, telem = apply_reservation(items, 8, _enabled_policy(), site="T")
    ids = [i.patch_id for i in selected]
    assert "F0" in ids
    assert len(selected) == 8
    assert telem.foundation_selected >= 1
    assert any(s["id"] == "F0" for s in telem.saved_by_reservation)
    assert len(telem.displaced_by_reservation) == len(telem.saved_by_reservation)
    assert all("mechanism" in d for d in telem.displaced_by_reservation)


def test_displacement_removes_lowest_ranked_first():
    items = _ranked(n_exp=20, n_found=1)
    selected, telem = apply_reservation(items, 8, _enabled_policy(), site="T")
    ids = [i.patch_id for i in selected]
    # Pure top-8 would be E0..E7; minimal displacement evicts E7 (lowest selected).
    assert "E7" not in ids
    assert "E6" in ids
    assert telem.displaced_by_reservation[0]["id"] == "E7"
    assert telem.displaced_by_reservation[0]["mechanism"] == EXP


# --- §38.2: experimental candidates cannot exhaust all slots ------------------

def test_experimental_cannot_exhaust_all_slots():
    items = _ranked(n_exp=8, n_found=20, found_first=True)
    selected, telem = apply_reservation(items, 8, _enabled_policy(), site="T")
    # K=8 -> R=2 foundation seats, >=6 general seats preserved.
    assert telem.general_selected >= 6
    assert telem.foundation_selected <= 2


def test_no_fabrication_and_backfill_on_underflow():
    items = _ranked(n_exp=3, n_found=1)  # only 4 items, K=8: no truncation at all
    selected, telem = apply_reservation(items, 8, _enabled_policy(), site="T")
    assert [i.patch_id for i in selected] == [i.patch_id for i in items]
    assert telem.saved_by_reservation == []
    assert telem.displaced_by_reservation == []
    # Underflow with truncation pressure: every selected item pre-existed.
    items = _ranked(n_exp=10, n_found=0)
    selected, _ = apply_reservation(items, 8, _enabled_policy(), site="T")
    assert len(selected) == 8
    assert all(any(s is o for o in items) for s in selected)


# --- §38.3: reservation does not force commits --------------------------------

def test_reservation_is_selection_only():
    items = _ranked(n_exp=20, n_found=1)
    selected, telem = apply_reservation(items, 8, _enabled_policy(), site="T")
    # Pure selection: identical objects, bounded count, rank order preserved.
    assert all(any(s is o for o in items) for s in selected)
    assert len(selected) <= 8
    ranks = [[o.patch_id for o in items].index(s.patch_id) for s in selected]
    assert ranks == sorted(ranks)
    # Telemetry exposes capacity facts only (no commit semantics).
    d = telem.to_dict()
    for key in ("before", "after", "k", "reserved_r", "saved", "displaced",
                "saturation", "foundation_displacement_rate"):
        assert key in d


# --- §38.4: deterministic slot allocation -------------------------------------

def test_deterministic_slot_allocation():
    items = _ranked(n_exp=20, n_found=3)
    first, t1 = apply_reservation(items, 8, _enabled_policy(), site="T")
    second, t2 = apply_reservation(items, 8, _enabled_policy(), site="T")
    assert [i.patch_id for i in first] == [i.patch_id for i in second]
    assert t1.to_dict() == t2.to_dict()


def test_zero_interference_when_floors_already_met():
    # 2 foundation inside pure top-8 -> output identical to plain truncation.
    items = _ranked(n_exp=6, n_found=0) + _ranked(n_exp=0, n_found=2)
    items = items[:6] + items[6:]  # E0..E5, F0, F1 ranked 6th/7th -> inside top-8
    items.extend(_ranked(n_exp=10, n_found=0))
    selected, telem = apply_reservation(items, 8, _enabled_policy(), site="T")
    assert [i.patch_id for i in selected] == [o.patch_id for o in items[:8]]
    assert telem.saved_by_reservation == []


def test_mechanism_agnostic_custom_classes():
    policy = FunnelReservationPolicy(enabled=True, reserved_mechanisms=frozenset({"X"}))
    items = [SimpleNamespace(patch_id=f"G{i}", mechanism_family="G",
                             candidate_transformation_family="G") for i in range(10)]
    items.append(SimpleNamespace(patch_id="X0", mechanism_family="X",
                                 candidate_transformation_family="X"))
    selected, telem = apply_reservation(items, 8, policy, site="T")
    assert "X0" in [i.patch_id for i in selected]
    assert telem.foundation_selected == 1


def test_reserved_seats_rule():
    assert reserved_seats_for_k(8) == 2
    assert reserved_seats_for_k(16) == 4
    assert reserved_seats_for_k(1) == 1
    assert reserved_seats_for_k(0) == 0
    policy = FunnelReservationPolicy(enabled=True)
    assert policy.classifier(_item("a", FOUND, 1)) == SlotClass.FOUNDATION
    assert policy.classifier(_item("b", EXP, 1)) == SlotClass.GENERAL
    assert set(ENABLED_FOUNDATION_MECHANISMS) == {
        "DEPENDENCY_AWARE_MARKET_TIMING", "TERMINAL_LIQUIDATION", "PHASE_SHUTDOWN",
    }


# --- Site integration: legacy equivalence when disabled -----------------------

def _spread_positions(cands):
    for i, c in enumerate(cands):
        c.target_pos = (i % 10, (i // 10) % 10)
        c.target_position = c.target_pos
    return cands


def test_funnel_s9_legacy_equivalence_when_disabled(normal_opening_obs):
    state = build_economic_state(normal_opening_obs)
    cands = _spread_positions(_ranked(n_exp=10, n_found=2))
    legacy = OpportunityCandidateFunnel()
    out_legacy, _ = legacy.filter_candidates(list(cands), state)
    gated = OpportunityCandidateFunnel(
        reservation_policy=FunnelReservationPolicy(enabled=False)
    )
    out_gated, _ = gated.filter_candidates(list(cands), state)
    assert [c.patch_id for c in out_legacy] == [c.patch_id for c in out_gated]
    assert gated.last_reservation_telemetry is None


def test_funnel_s9_reservation_saves_foundation(normal_opening_obs):
    state = build_economic_state(normal_opening_obs)
    cands = _spread_positions(_ranked(n_exp=10, n_found=1))
    legacy = OpportunityCandidateFunnel()
    out_legacy, _ = legacy.filter_candidates(list(cands), state)
    assert "F0" not in [c.patch_id for c in out_legacy]
    gated = OpportunityCandidateFunnel(
        reservation_policy=FunnelReservationPolicy(enabled=True)
    )
    out_gated, _ = gated.filter_candidates(list(cands), state)
    assert "F0" in [c.patch_id for c in out_gated]
    assert gated.last_reservation_telemetry is not None
    assert gated.last_reservation_telemetry.site == "S9_DETERMINISTIC_TOP_K"


def test_detect_opportunities_legacy_equivalence_when_disabled(cash_deficit_obs):
    state = build_economic_state(cash_deficit_obs)
    events = detect_events(state)
    base = {"farmer": ["PASS"], "hands": [["PASS"]], "market": []}
    engine = OpportunityEngine()
    cfg_off = build_phase015_treatment_config()
    assert cfg_off.enable_funnel_reservation is False
    full = engine.detect_opportunities(state, events, base, max_opportunities=1000,
                                       config=cfg_off)
    trunc = engine.detect_opportunities(state, events, base, max_opportunities=2,
                                        config=cfg_off)
    assert [o.opportunity_id for o in trunc] == [o.opportunity_id for o in full[:2]]
    assert engine.last_reservation_telemetry is None


def test_prune_patches_legacy_equivalence_when_disabled(normal_opening_obs):
    state = build_economic_state(normal_opening_obs)
    patches = _ranked(n_exp=10, n_found=0)
    assert [p.patch_id for p in prune_patches(list(patches), state, max_candidates=8)] == \
        [f"E{i}" for i in range(8)]
    out = prune_patches(list(patches), state, max_candidates=8,
                        reservation_policy=FunnelReservationPolicy(enabled=False))
    assert [p.patch_id for p in out] == [f"E{i}" for i in range(8)]
    policy = FunnelReservationPolicy(enabled=True)
    out = prune_patches(list(patches), state, max_candidates=8, reservation_policy=policy)
    assert [p.patch_id for p in out] == [f"E{i}" for i in range(8)]
    assert policy.last_telemetry is not None
    assert policy.last_telemetry.site == "PRUNE_PATCHES_CAP"


# --- §38.13: arm isolation -----------------------------------------------------

def test_arm_a2_differs_from_a1_only_by_reservation_flag():
    a1 = build_phase015_treatment_config()
    a2 = build_phase018_arm_a2_config()
    d1, d2 = vars(a1), vars(a2)
    assert set(d1) == set(d2)
    diffs = [k for k in d1 if d1[k] != d2[k]]
    assert diffs == ["enable_funnel_reservation"]
    assert a2.enable_funnel_reservation is True


def test_reservation_policies_off_by_default():
    from aec.config import AECConfig, build_robust_qualified_config
    assert AECConfig().enable_funnel_reservation is False
    assert build_robust_qualified_config().enable_funnel_reservation is False
    assert build_phase015_treatment_config().enable_funnel_reservation is False


# --- §38.14/15: V3 + evaluator path untouched ----------------------------------

def test_v3_tarball_sha_unchanged():
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    with open(os.path.join(repo_root, "submission_Vj_kc_v3.tar.gz"), "rb") as f:
        digest = hashlib.sha256(f.read()).hexdigest()
    assert digest == "845e0d10981b11b06d272048ff5cee30d70a0403dd757651a556a78c8bf18943"


def test_executor_carries_reservation_policy_and_telemetry(cash_deficit_obs):
    adapter = BackboneAdapter()
    assert adapter is not None
    ex_off = AECExecutor(backbone_adapter=BackboneAdapter(),
                         config=build_phase015_treatment_config())
    ex_on = AECExecutor(backbone_adapter=BackboneAdapter(),
                        config=build_phase018_arm_a2_config())
    assert ex_off._reservation_policy.enabled is False
    assert ex_on._reservation_policy.enabled is True
    assert ex_on.latest_telemetry is None
    ex_on.act(dict(cash_deficit_obs))
    telem = ex_on.latest_telemetry
    assert telem is not None
    assert isinstance(telem.funnel_reservation, dict)
    d = telem.to_dict()
    assert "funnel_reservation" in d
