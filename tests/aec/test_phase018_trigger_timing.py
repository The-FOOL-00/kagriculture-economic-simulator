# SPDX-License-Identifier: MIT
"""Phase 018 Repair C: trigger timing variant tests (§38.10–§38.12, §38.13)."""

from aec.config import (
    build_phase015_treatment_config,
    build_phase018_arm_c1_config,
    build_phase018_arm_c2_config,
    build_phase018_arm_c3_config,
)
from aec.ir import build_economic_state
from aec.opportunities.asset_holding import (
    AssetHoldingFingerprint,
    AssetHoldingOpportunityAnalyzer,
    AssetHoldingValuationTrigger,
    HoldingOpportunityType,
    StructuralHoldingFeatures,
)


def _feat(commodity="MELON", qty=5, price=300.0, base=250.0, step_rem=400,
          deficit=0.0, rival=999, storage=0.3, traj="STABLE", phase="MID"):
    ratio = price / base
    fp = AssetHoldingFingerprint(commodity, qty // 10, int(round(ratio / 0.05)),
                                 phase, "UNCOMMITTED", "LOW")
    return StructuralHoldingFeatures(
        commodity, qty, qty, price, base, ratio, traj, storage, step_rem,
        3000.0, 100.0, deficit, rival, ["KEEP", "SELL_NOW"], fp)


def _class_a_feat(**kw):
    # ratio 1.20, qty 5 -> favorable Class A; premium = 50*5 = 250.
    return _feat(**kw)


# --- §38.10: persistence ----------------------------------------------------------

def test_c1_first_observation_suppressed_second_emits():
    t = AssetHoldingValuationTrigger()
    audit1: dict = {}
    assert t.evaluate_opportunity(_class_a_feat(), step=100,
                                  persistence_required=True, audit=audit1) is None
    assert audit1["suppressed_by"] == "C1_NONPERSISTENT"
    audit2: dict = {}
    res = t.evaluate_opportunity(_class_a_feat(), step=101,
                                 persistence_required=True, audit=audit2)
    assert res is not None and res[0] == HoldingOpportunityType.FAVOURABLE_MARKET_HOLDING
    assert audit2["emitted"] == "FAVOURABLE_MARKET_HOLDING"


def test_c1_nonconsecutive_resets():
    t = AssetHoldingValuationTrigger()
    assert t.evaluate_opportunity(_class_a_feat(), step=100,
                                  persistence_required=True) is None
    # Gap at 101 -> 102 is a fresh first observation, suppressed again.
    assert t.evaluate_opportunity(_class_a_feat(), step=102,
                                  persistence_required=True) is None
    assert t.evaluate_opportunity(_class_a_feat(), step=103,
                                  persistence_required=True) is not None


def test_c1_run_continues_past_two():
    t = AssetHoldingValuationTrigger()
    assert t.evaluate_opportunity(_class_a_feat(), step=100,
                                  persistence_required=True) is None
    assert t.evaluate_opportunity(_class_a_feat(), step=101,
                                  persistence_required=True) is not None
    assert t.evaluate_opportunity(_class_a_feat(), step=102,
                                  persistence_required=True) is not None


def test_c1_tracks_commodities_independently():
    t = AssetHoldingValuationTrigger()
    assert t.evaluate_opportunity(_class_a_feat(commodity="MELON"), step=100,
                                  persistence_required=True) is None
    # WHEAT first observation at 101 does not inherit MELON's run.
    assert t.evaluate_opportunity(_class_a_feat(commodity="WHEAT", price=30.0, base=25.0),
                                  step=101, persistence_required=True) is None
    # MELON consecutive at 101 emits.
    assert t.evaluate_opportunity(_class_a_feat(commodity="MELON"), step=101,
                                  persistence_required=True) is not None


# --- §38.11: premature single-unit / sub-scale firing -------------------------------

def test_c2_premium_floor_filters_flicker():
    t = AssetHoldingValuationTrigger()
    # Wheat ratio 1.16, qty 3: premium = 4*3 = 12 < 15 -> suppressed.
    small = _feat(commodity="WHEAT", qty=3, price=29.0, base=25.0)
    audit: dict = {}
    assert t.evaluate_opportunity(small, min_premium_class_a=15.0, audit=audit) is None
    assert audit["suppressed_by"] == "C2_MIN_PREMIUM"
    # Same ratio, qty 5: premium = 20 >= 15 -> emits.
    big = _feat(commodity="WHEAT", qty=5, price=29.0, base=25.0)
    res = t.evaluate_opportunity(big, min_premium_class_a=15.0)
    assert res is not None and res[0] == HoldingOpportunityType.FAVOURABLE_MARKET_HOLDING


def test_c3_tape_separation_suppresses_taped_commodity_only():
    t = AssetHoldingValuationTrigger()
    audit: dict = {}
    assert t.evaluate_opportunity(_class_a_feat(commodity="MELON"),
                                  tape_sells={"MELON"}, audit=audit) is None
    assert audit["suppressed_by"] == "C3_TAPE_SEPARATION"
    res = t.evaluate_opportunity(_class_a_feat(commodity="WHEAT", price=30.0, base=25.0),
                                 tape_sells={"MELON"})
    assert res is not None and res[0] == HoldingOpportunityType.FAVOURABLE_MARKET_HOLDING


def test_c3_inactive_without_tape():
    t = AssetHoldingValuationTrigger()
    res = t.evaluate_opportunity(_class_a_feat(), tape_sells=None)
    assert res is not None
    res = t.evaluate_opportunity(_class_a_feat(), tape_sells=set())
    assert res is not None


def test_tape_extraction_window_and_shape():
    tape = [
        {"farmer": ["PASS"], "hands": [], "market": [["SELL", "MELON", 5]]},
        {"farmer": ["PASS"], "hands": [], "market": [["BUY_PRODUCT", "WHEAT", 2]]},
        {"farmer": ["PASS"], "hands": [], "market": [["SELL", "EGG", 3]]},
        "garbage",
    ]
    sells = AssetHoldingOpportunityAnalyzer.extract_tape_sells(tape, window=2)
    assert sells == {"MELON"}
    assert AssetHoldingOpportunityAnalyzer.extract_tape_sells(None) == set()
    assert AssetHoldingOpportunityAnalyzer.extract_tape_sells([]) == set()


# --- §38.12: genuine persistent opportunity retained ----------------------------------

def test_distress_classes_unaffected_by_c_gates():
    t = AssetHoldingValuationTrigger()
    gates = dict(persistence_required=True, min_premium_class_a=15.0,
                 tape_sells={"MELON", "WHEAT"})
    # Class B: terminal runway.
    b = _feat(commodity="MELON", qty=2, price=200.0, base=250.0,
              step_rem=40, phase="TERMINAL")
    res = t.evaluate_opportunity(b, step=700, **gates)
    assert res is not None and res[0] == HoldingOpportunityType.TERMINAL_HOLDING_RISK
    # Class C: liquidity deficit at acceptable price.
    c = _feat(commodity="WHEAT", qty=4, price=24.0, base=25.0, deficit=120.0)
    res = t.evaluate_opportunity(c, step=300, **gates)
    assert res is not None and res[0] == HoldingOpportunityType.LIQUIDITY_HOLDING_CONFLICT
    # Class E: rival pressure.
    e = _feat(commodity="MELON", qty=6, price=245.0, base=250.0, rival=2)
    res = t.evaluate_opportunity(e, step=300, **gates)
    assert res is not None and res[0] == HoldingOpportunityType.OPPONENT_PRESSURE


def test_class_a_baseline_deferral_preserved():
    t = AssetHoldingValuationTrigger()
    audit: dict = {}
    assert t.evaluate_opportunity(_class_a_feat(), baseline_has_sell=True,
                                  audit=audit) is None
    assert audit["suppressed_by"] == "BASELINE_SELLING"


# --- Firing log -----------------------------------------------------------------------

def test_firing_log_records_outcomes(shed_capacity_obs):
    st = build_economic_state(shed_capacity_obs)
    analyzer = AssetHoldingOpportunityAnalyzer()
    opps = analyzer.analyze(st, [], {"farmer": ["PASS"], "hands": [], "market": []})
    assert isinstance(opps, list)
    log = analyzer.last_firing_log
    assert log, "held commodities must produce firing records"
    for rec in log:
        for key in ("step", "commodity", "quantity_held", "uncommitted_quantity",
                    "current_price", "price_ratio", "price_trajectory"):
            assert key in rec
        assert (rec["emitted"] is None) != (rec["suppressed_by"] is None)


# --- Isolation ---------------------------------------------------------------------------

def test_c_legs_differ_only_by_intended_flags():
    c0 = build_phase015_treatment_config()
    for build, field in ((build_phase018_arm_c1_config, "enable_trigger_persistence"),
                         (build_phase018_arm_c2_config, "trigger_min_premium_class_a"),
                         (build_phase018_arm_c3_config, "enable_tape_separation")):
        leg = build()
        d0, d1 = vars(c0), vars(leg)
        assert set(d0) == set(d1)
        assert [k for k in d0 if d0[k] != d1[k]] == [field], field
        assert leg.enable_funnel_reservation is False
        assert leg.enable_boundary_safe_quantities is False
        assert leg.enable_market_patch_discrimination is False


def test_c_gates_off_by_default_and_legacy_equivalent():
    from aec.config import AECConfig
    cfg = AECConfig()
    assert cfg.enable_trigger_persistence is False
    assert cfg.trigger_min_premium_class_a is None
    assert cfg.enable_tape_separation is False
    t1, t2 = AssetHoldingValuationTrigger(), AssetHoldingValuationTrigger()
    f = _class_a_feat()
    r1 = t1.evaluate_opportunity(f)
    r2 = t2.evaluate_opportunity(f, step=100, persistence_required=False,
                                 min_premium_class_a=None, tape_sells=None,
                                 audit={})
    assert (r1 is None) == (r2 is None)
    assert r1 is not None and r1[0] == r2[0] and abs(r1[2] - r2[2]) < 1e-9
