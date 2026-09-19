# SPDX-License-Identifier: MIT
"""Phase 018 Repair B: boundary-safe quantity tests (§38.5–§38.9, §38.13)."""

from aec.config import (
    build_phase015_treatment_config,
    build_phase018_arm_b1_config,
)
from aec.counterfactual.macro_detector import MacroRegimeTransitionDetector
from aec.ir import build_economic_state
from aec.market.tranche_synthesizer import AutonomousTrancheOrderSynthesizer
from aec.patches.patch import CoupledPatch


def _state(obs, cash=None, shed=None, prices=None, step=None, herd=0):
    st = build_economic_state(obs)
    if cash is not None:
        st.farm.cash = float(cash)
    if shed is not None:
        st.farm.shed_inventory.update(shed)
    if prices is not None:
        st.market.current_prices.update(prices)
    if step is not None:
        st.step = int(step)
    if herd:
        st.farm.animals = [object() for _ in range(herd)]
    return st


def _synth():
    return AutonomousTrancheOrderSynthesizer()


# --- §38.5: feed floor ---------------------------------------------------------

def test_boundary_quantity_respects_feed_floor(normal_opening_obs):
    st = _state(normal_opening_obs, cash=3000.0,
                shed={"WHEAT": 20}, prices={"WHEAT": 25.0}, step=400, herd=2)
    menu = _synth().compute_structural_quantities(
        st, "WHEAT", 14, baseline_market_orders=[], boundary_safe=True)
    assert (3, "BOUNDARY_SAFE") in menu  # min(20-12, 3) headroom/drop clamp
    q_safe = next(q for q, r in menu if r == "BOUNDARY_SAFE")
    assert 20 - q_safe >= 12 and q_safe <= 3


def test_no_feed_safe_anchor_when_floor_unavoidable(normal_opening_obs):
    st = _state(normal_opening_obs, cash=3000.0,
                shed={"WHEAT": 10}, prices={"WHEAT": 25.0}, step=400, herd=2)
    menu = _synth().compute_structural_quantities(
        st, "WHEAT", 4, baseline_market_orders=[], boundary_safe=True)
    reasons = [r for _, r in menu]
    assert "BOUNDARY_SAFE" not in reasons  # any sale trips; evaluator decides
    assert menu == [(1, "Q_SMALL"), (4, "Q_CURRENT")]


# --- §38.6: liquidity / merged-queue accounting --------------------------------

def test_sells_never_reduce_projected_cash(normal_opening_obs):
    st = _state(normal_opening_obs, cash=4500.0,
                shed={"MELON": 30}, prices={"MELON": 250.0}, step=500)
    s = _synth()
    menu = s.compute_structural_quantities(
        st, "MELON", 30, baseline_market_orders=[], boundary_safe=True)
    assert len(menu) >= 2
    for q, _ in menu:
        cash, _ = s.project_post_queue_cash(st, [], "MELON", q)
        assert cash >= 4500.0


def test_projection_accounts_for_baseline_queue(normal_opening_obs):
    st = _state(normal_opening_obs, cash=9800.0,
                shed={"WHEAT": 60}, prices={"WHEAT": 25.0}, step=500)
    s = _synth()
    base = [["SELL", "WHEAT", 10]]
    cash, shed = s.project_post_queue_cash(st, base, "WHEAT", 1)
    assert cash == 9800.0 + 10 * 25.0 + 1 * 25.0  # 10075: baseline + tranche
    assert shed["WHEAT"] == 60 - 11
    # Baseline alone already crosses 10000 -> no avoidable-cross anchor exists.
    menu = s.compute_structural_quantities(
        st, "WHEAT", 40, baseline_market_orders=base, boundary_safe=True)
    assert menu == [(1, "Q_SMALL"), (5, "Q_CURRENT")]


# --- §38.7: boundary-minus correctness -----------------------------------------

def test_boundary_safe_and_minus_generated_correctly(normal_opening_obs):
    st = _state(normal_opening_obs, cash=9600.0,
                shed={"CARROT": 40}, prices={"CARROT": 100.0}, step=500)
    menu = _synth().compute_structural_quantities(
        st, "CARROT", 40, baseline_market_orders=[], boundary_safe=True)
    # q_current=5 -> 10100 crosses 10000; safe<=9999 -> 3; minus<=9850 -> 2.
    assert menu == [(1, "Q_SMALL"), (5, "Q_CURRENT"),
                    (3, "BOUNDARY_SAFE"), (2, "BOUNDARY_MINUS")]


def test_unavoidable_crossing_yields_no_safe_anchor(normal_opening_obs):
    st = _state(normal_opening_obs, cash=9900.0,
                shed={"STRAWBERRY": 50}, prices={"STRAWBERRY": 120.0}, step=500)
    menu = _synth().compute_structural_quantities(
        st, "STRAWBERRY", 50, baseline_market_orders=[], boundary_safe=True)
    assert menu == [(1, "Q_SMALL"), (5, "Q_CURRENT")]  # even q=1 crosses 10000


def test_non_boundary_window_collapses_to_legacy_pair(normal_opening_obs):
    st = _state(normal_opening_obs, cash=3000.0,
                shed={"MELON": 30}, prices={"MELON": 250.0}, step=100)
    menu = _synth().compute_structural_quantities(
        st, "MELON", 30, baseline_market_orders=[], boundary_safe=True)
    assert menu == [(1, "Q_SMALL"), (5, "Q_CURRENT")]


# --- §38.8/§38.9: dedup + bounded menu ------------------------------------------

def test_no_duplicates_and_bounded_menu(normal_opening_obs):
    s = _synth()
    for cash in (100.0, 900.0, 1950.0, 4900.0, 7400.0, 9600.0, 11900.0, 15000.0):
        for uncommitted in (1, 2, 5, 9, 13, 40):
            for step in (100, 300, 500, 700):
                st = _state(normal_opening_obs, cash=cash,
                            shed={"WHEAT": 60, "MELON": 30},
                            prices={"WHEAT": 25.0, "MELON": 250.0},
                            step=step, herd=2)
                for commodity in ("WHEAT", "MELON"):
                    menu = s.compute_structural_quantities(
                        st, commodity, uncommitted,
                        baseline_market_orders=[], boundary_safe=True)
                    qs = [q for q, _ in menu]
                    assert len(qs) == len(set(qs)), (cash, uncommitted, step, menu)
                    assert len(menu) <= 4
                    assert all(1 <= q <= uncommitted for q in qs)


# --- Legacy equivalence + isolation --------------------------------------------

def test_legacy_menu_unchanged_when_flag_off(normal_opening_obs):
    st = _state(normal_opening_obs, cash=9600.0,
                shed={"CARROT": 40}, prices={"CARROT": 100.0}, step=500)
    s = _synth()
    legacy = s.compute_structural_quantities(st, "CARROT", 40)
    assert any(r == "MINIMAL_TRANCHE" for _, r in legacy)
    assert all(not r.startswith("BOUNDARY") and r not in ("Q_SMALL", "Q_CURRENT")
               for _, r in legacy)
    explicit_off = s.compute_structural_quantities(
        st, "CARROT", 40, baseline_market_orders=[], boundary_safe=False)
    assert explicit_off == legacy


def test_arm_b1_differs_from_b0_only_by_quantity_flag():
    b0 = build_phase015_treatment_config()
    b1 = build_phase018_arm_b1_config()
    d0, d1 = vars(b0), vars(b1)
    assert set(d0) == set(d1)
    assert [k for k in d0 if d0[k] != d1[k]] == ["enable_boundary_safe_quantities"]
    assert b1.enable_funnel_reservation is False  # isolation from Repair A
    assert b1.enable_boundary_safe_quantities is True


# --- Generator/probe consistency (read-only probe use) --------------------------

def test_safe_anchor_does_not_cross_cash_gate(normal_opening_obs):
    st = _state(normal_opening_obs, cash=9600.0,
                shed={"CARROT": 40}, prices={"CARROT": 100.0}, step=500)
    s = _synth()
    detector = MacroRegimeTransitionDetector()
    baseline_action = {"farmer": ["PASS"], "hands": [], "market": []}
    for q, reason in [(5, "Q_CURRENT"), (3, "BOUNDARY_SAFE"), (2, "BOUNDARY_MINUS")]:
        orders = s.construct_sequential_market_orders([], "CARROT", q)
        patch = CoupledPatch(
            patch_id=f"PATCH_TEST_q{q}", source_opportunity_id="OPP_TEST",
            mechanism_family="AUTONOMOUS_TRANCHE_ORDER_SYNTHESIZER",
            market_mutations=orders,
        )
        res = detector.probe_candidate(patch, baseline_action, st)
        if reason == "Q_CURRENT":
            assert res.requires_escalation and "CASH_GATE_CROSSED" in res.reason
        else:
            assert "CASH_GATE_CROSSED" not in res.reason, (q, res.reason)
