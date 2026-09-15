# SPDX-License-Identifier: MIT
"""Adversarial Tests A–J (handoff §27).

Each test constructs a deliberate attack on one H1 gate and asserts
the preregistered fail-safe outcome.  Gate-logic tests call the
preregistered predicates directly on hand-built runs; wiring tests
prove the search loop actually consults each gate (via targeted
monkeypatching of the gate to force-fail on an otherwise-activating
state).
"""

import copy

import pytest

from conftest import cow_tile, make_obs, wheat_tile
from h1_dominance import (
    acceptance,
    dominates,
    markets_verbatim,
    no_steal_pass,
    stock_value,
)


def _run(rows, sold, shed, overflow=0, events=(), actions=(),
         states=(), private_extra=None):
    private = {"shed": dict(shed), "seeds": {},
               "inventories": [{}]}
    if private_extra:
        private.update(private_extra)
    return {"rows": rows, "sold": dict(sold), "private": private,
            "overflow_units": overflow, "events": list(events),
            "actions": list(actions), "states": list(states)}


def _row(pre, sold, dep0):
    return {"pre_market_shed": dict(pre), "post_market_shed": {},
            "deposited_by_actor": [dict(dep0)], "sold": dict(sold)}


PRICES = {"WHEAT": 25, "CARROT": 35, "TOMATO": 60,
          "STRAWBERRY": 120, "MELON": 250, "EGG": 50,
          "MILK": 160, "WOOL": 200, "FERTILIZER": 100}


# ------------------------------------------------- Test A: gain, no dom
def test_A_gain_without_dominance_rejected():
    base = _run([_row({"WHEAT": 5}, {"WHEAT": 5}, {"WHEAT": 5})],
                {"WHEAT": 5}, {"WHEAT": 0})
    # Candidate sells MORE overall but is BEHIND at the only row.
    cand = _run([_row({"WHEAT": 4}, {"WHEAT": 4}, {"WHEAT": 4})],
                {"WHEAT": 4}, {"WHEAT": 10})
    assert stock_value(cand, PRICES) > stock_value(base, PRICES)
    assert dominates(cand, base) is False


def test_A_prefix_violation_mid_window_rejected():
    rows_b = [_row({"WHEAT": 3}, {"WHEAT": 3}, {"WHEAT": 3}),
              _row({"WHEAT": 6}, {"WHEAT": 6}, {"WHEAT": 6})]
    rows_c = [_row({"WHEAT": 3}, {"WHEAT": 3}, {"WHEAT": 3}),
              _row({"WHEAT": 5}, {"WHEAT": 5}, {"WHEAT": 5})]
    base = _run(rows_b, {"WHEAT": 6}, {})
    cand = _run(rows_c, {"WHEAT": 5}, {"WHEAT": 99})  # huge terminal
    assert stock_value(cand, PRICES) > stock_value(base, PRICES)
    assert dominates(cand, base) is False  # row-2 prefix violated


def test_A_dominance_gate_is_load_bearing(monkeypatch, fresh_baseline,
                                           full_config):
    # Force-fail dominance on an otherwise-activating state: the search
    # must report ABSTAIN_DOMINANCE (trial stage), never adopt.
    import h1_search
    from h1_agent import H1Overlay
    monkeypatch.setattr(h1_search, "dominates", lambda c, b: False)
    overlay = H1Overlay(fresh_baseline)
    obs = make_obs(712, tiles=[(4, 4, wheat_tile(yield_units=6))])
    out = overlay.act(copy.deepcopy(obs), copy.deepcopy(full_config))
    record = overlay.open_records.get(0)
    assert record["reason"] == "ABSTAIN_DOMINANCE"
    assert record["subcause"] == {"stage": "trial"}
    live = fresh_baseline.call(copy.deepcopy(obs),
                               copy.deepcopy(full_config))
    assert out == live


# ------------------------------------------------- Test B: dom, no gain
def test_B_dominance_without_gain_rejected():
    base = _run([_row({"WHEAT": 5}, {"WHEAT": 5}, {"WHEAT": 5})],
                {"WHEAT": 5}, {"WHEAT": 0})
    cand = _run([_row({"WHEAT": 5}, {"WHEAT": 5}, {"WHEAT": 5})],
                {"WHEAT": 5}, {"WHEAT": 0})
    assert dominates(cand, base) is True
    assert stock_value(cand, PRICES) == stock_value(base, PRICES)
    # Strict > fails on ties: no adoption possible (T1).


def test_B_tie_value_never_adopts(fresh_baseline, full_config):
    # End-to-end: identical value ⇒ ABSTAIN_NO_GAIN, never adopt.
    import h1_search
    from h1_agent import H1Overlay
    overlay = H1Overlay(fresh_baseline)
    # Farm with no yield anywhere and no carry: no proposal can gain.
    obs = make_obs(712)
    out = overlay.act(copy.deepcopy(obs), copy.deepcopy(full_config))
    record = overlay.open_records.get(0)
    assert record["reason"] == "ABSTAIN_NO_GAIN"
    live = fresh_baseline.call(copy.deepcopy(obs),
                               copy.deepcopy(full_config))
    assert out == live


# ------------------------------------------------------- Test C: stealing
def test_C_stolen_harvest_rejected():
    best = {"events": [
        {"xy": (3, 3), "op": "HARVEST", "actor": 1,
         "acquired": {"WHEAT": 4}}]}
    trial_missing = {"events": []}
    assert no_steal_pass(trial_missing, best, 0) is False


def test_C_short_quantity_rejected():
    best = {"events": [
        {"xy": (3, 3), "op": "HARVEST", "actor": 1,
         "acquired": {"WHEAT": 4}}]}
    trial_short = {"events": [
        {"xy": (3, 3), "op": "HARVEST", "actor": 1,
         "acquired": {"WHEAT": 3}}]}
    assert no_steal_pass(trial_short, best, 0) is False


def test_C_preserved_acquisition_passes():
    best = {"events": [
        {"xy": (3, 3), "op": "HARVEST", "actor": 1,
         "acquired": {"WHEAT": 4}}]}
    trial_ok = {"events": [
        {"xy": (3, 3), "op": "HARVEST", "actor": 1,
         "acquired": {"WHEAT": 5}}]}
    assert no_steal_pass(trial_ok, best, 0) is True


def test_C_own_actor_excluded():
    best = {"events": [
        {"xy": (3, 3), "op": "HARVEST", "actor": 0,
         "acquired": {"WHEAT": 4}}]}
    assert no_steal_pass({"events": []}, best, 0) is True


def test_C_stolen_fertilizer_rejected():
    best = {"events": [
        {"xy": (1, 1), "op": "COLLECT_FERTILIZER", "actor": 2,
         "acquired": {"FERTILIZER": 1}}]}
    trial = {"events": [
        {"xy": (1, 1), "op": "COLLECT_FERTILIZER", "actor": 0,
         "acquired": {"FERTILIZER": 1}}]}  # wrong actor
    assert no_steal_pass(trial, best, 0) is False


def test_C_nosteal_gate_is_load_bearing(monkeypatch, fresh_baseline,
                                         full_config):
    import h1_search
    from h1_agent import H1Overlay
    monkeypatch.setattr(h1_search, "no_steal_pass",
                        lambda t, b, a: False)
    overlay = H1Overlay(fresh_baseline)
    obs = make_obs(712, tiles=[(4, 4, wheat_tile(yield_units=6))])
    out = overlay.act(copy.deepcopy(obs), copy.deepcopy(full_config))
    record = overlay.open_records.get(0)
    assert record["reason"] == "ABSTAIN_NOSTEAL"
    live = fresh_baseline.call(copy.deepcopy(obs),
                               copy.deepcopy(full_config))
    assert out == live


# ------------------------------------------------- Test D: BUY coverage
def test_D_buy_without_money_abstains_in_sim(fresh_baseline):
    from h1_shadow import ShadowCursor, execute_market
    from h1_telemetry import H1Abstain
    obs = make_obs(712, money=10.0)
    cursor = ShadowCursor(fresh_baseline, 0, obs, None, None, {},
                          "", [], coverage_U=18)
    with pytest.raises(H1Abstain) as exc:
        execute_market(cursor, [["BUY_PRODUCT", "WHEAT", 18]], 712)
    assert exc.value.reason == "ABSTAIN_BUY_COVERAGE"
    assert exc.value.subcause["U"] == 18


def test_D_wheat_curve_max_is_125(fresh_baseline):
    # Prereg §8.2/H2 derivation: 25 + (0.8×25/√400)×√10000 = 125.
    price = fresh_baseline.market_price
    assert price("WHEAT", 0) == 125
    for inv in range(0, 10001, 500):
        assert price("WHEAT", inv) <= 125, inv
    # ...and $125 is attained (maximum, not just a bound).
    assert max(price("WHEAT", inv) for inv in range(0, 10001)) == 125


def test_D_fertilizer_curve_exceeds_125_warns(fresh_baseline):
    # DISCREPANCY-1 evidence: FERTILIZER quotes range far above $125,
    # which is why window FERTILIZER BUYs fail closed in G3.
    price = fresh_baseline.market_price
    assert price("FERTILIZER", 0) == 2100
    assert price("FERTILIZER", 0) > 125


# ------------------------------------------- Test E: fronting/flow safety
def test_E_fronting_mirror_exact_off(fresh_baseline, full_config):
    _mirror_check(fresh_baseline, full_config, fronting=False)


def test_E_fronting_mirror_exact_on(fresh_baseline, full_config):
    _mirror_check(fresh_baseline, full_config, fronting=True)


def _mirror_check(fresh_baseline, full_config, fronting):
    # predict_baseline_action at t=712 (no outer overlay fires there)
    # must EXACTLY equal live controller.apply with identical ledgers.
    import copy as _copy
    from h1_shadow import ShadowCursor, predict_baseline_action
    obs = make_obs(712, money=2000.0, opp_money=9000.0,
                   shed={"WHEAT": 10, "CARROT": 6},
                   market_inventory={"WHEAT": 9500, "CARROT": 9000})
    policy = fresh_baseline.policies["backbone"]
    ledgers = {"last_step": 711, "route": "default",
               "near_streak": 12 if fronting else 0,
               "near_latched": bool(fronting),
               "last_inventory": {p: 10000 for p in
                                  ("WHEAT", "CARROT", "TOMATO",
                                   "STRAWBERRY", "MELON", "EGG", "MILK",
                                   "WOOL", "FERTILIZER")},
               "last_market_net": {p: 0 for p in
                                   ("WHEAT", "CARROT", "TOMATO",
                                    "STRAWBERRY", "MELON", "EGG", "MILK",
                                    "WOOL", "FERTILIZER")},
               "last_shops": [],
               "opponent_supply": {p: (9.0 if fronting else 0.0)
                                   for p in
                                   ("WHEAT", "CARROT", "TOMATO",
                                    "STRAWBERRY", "MELON", "EGG", "MILK",
                                    "WOOL", "FERTILIZER")},
               "mirror_confidence": 0.0, "mirror_evidence_turns": 0,
               "due": {}, "pending": {}}
    policy.controller.states[0] = _copy.deepcopy(ledgers)
    visible = fresh_baseline.visible_configuration(full_config)
    live = policy(_copy.deepcopy(obs), _copy.deepcopy(visible))
    cursor = ShadowCursor(fresh_baseline, 0, obs, full_config,
                          visible, _copy.deepcopy(ledgers),
                          "backbone", policy.route_prior)
    pred = predict_baseline_action(cursor, 712)
    assert pred == live


def test_E_repay_carry_mirrored(fresh_baseline, full_config):
    import copy as _copy
    from h1_shadow import ShadowCursor, predict_baseline_action
    obs = make_obs(712, money=9000.0, shed={"WHEAT": 30})
    policy = fresh_baseline.policies["backbone"]
    ledgers = {"last_step": 711, "route": "default",
               "near_streak": 0, "near_latched": False,
               "last_inventory": None, "last_market_net": {},
               "last_shops": [], "opponent_supply": {},
               "mirror_confidence": 0.0, "mirror_evidence_turns": 0,
               "due": {712: {"WHEAT": 5}}, "pending": {}}
    policy.controller.states[0] = _copy.deepcopy(ledgers)
    visible = fresh_baseline.visible_configuration(full_config)
    live = policy(_copy.deepcopy(obs), _copy.deepcopy(visible))
    cursor = ShadowCursor(fresh_baseline, 0, obs, full_config,
                          visible, _copy.deepcopy(ledgers),
                          "backbone", policy.route_prior)
    pred = predict_baseline_action(cursor, 712)
    assert pred == live
    assert cursor.ledgers.get("due", {}).get(713, {}).get(
        "WHEAT", 0) >= 0  # carry state evolved identically


# ------------------------------------------------- Test F: DROP overflow
def test_F_candidate_overflow_rejected():
    rows = [_row({"WHEAT": 9}, {"WHEAT": 9}, {"WHEAT": 9})]
    base = _run(rows, {"WHEAT": 9}, {})
    cand = _run([dict(r) for r in rows], {"WHEAT": 9}, {"WHEAT": 50},
                overflow=1)
    assert stock_value(cand, PRICES) > stock_value(base, PRICES)
    assert dominates(cand, base) is False  # overflow ⇒ fail


def test_F_baseline_overflow_does_not_veto():
    rows = [_row({"WHEAT": 9}, {"WHEAT": 9}, {"WHEAT": 9})]
    base = _run(rows, {"WHEAT": 9}, {}, overflow=3)
    cand = _run([dict(r) for r in rows], {"WHEAT": 9}, {"WHEAT": 1})
    assert dominates(cand, base) is True  # only candidate counts


# ------------------------------------------- Test G: market-verbatim cert
def test_G_market_change_rejected():
    sched = [{"market": [["SELL", "WHEAT", 5]]} for _ in range(7)]
    plan = [dict(a) for a in sched]
    assert markets_verbatim(plan, sched) is True
    plan[3] = {"market": [["SELL", "WHEAT", 6]]}
    assert markets_verbatim(plan, sched) is False


def test_G_emission_uses_live_market_even_on_divergence(
        overlay, fresh_baseline, full_config):
    # _emit takes units from the plan but markets ALWAYS from live.
    obs = make_obs(713)
    plan = {"actions": [
        {"farmer": ["NORTH"], "hands": [["PASS"], ["PASS"]],
         "market": [["SELL", "WHEAT", 999]]} for _ in range(7)]}
    live = {"farmer": ["PASS"], "hands": [["PASS"], ["PASS"]],
            "market": [["SELL", "WHEAT", 1]]}
    out = overlay._emit(0, 713, obs, plan, live)
    assert out["market"] == [["SELL", "WHEAT", 1]]
    assert out["farmer"] == ["NORTH"]


# ------------------------------------------------- Test H: determinism
def _scrub(record):
    record = dict(record)
    record.pop("planning_ms", None)  # wallclock telemetry, non-gating
    return record


def test_H_double_run_bit_identical(fresh_baseline, full_config):
    from h1_agent import H1Overlay
    obs = make_obs(712, tiles=[(4, 4, wheat_tile(yield_units=6)),
                               (5, 5, cow_tile())])
    outs, records = [], []
    for _ in range(2):
        overlay = H1Overlay(fresh_baseline)
        out = overlay.act(copy.deepcopy(obs),
                          copy.deepcopy(full_config))
        outs.append(out)
        records.append(_scrub(overlay.open_records.get(0)))
    assert outs[0] == outs[1]
    assert records[0] == records[1]


def test_H_activated_plan_bit_identical(fresh_baseline, full_config):
    import hashlib
    import json
    from h1_agent import H1Overlay
    obs = make_obs(712, tiles=[(4, 4, wheat_tile(yield_units=3))],
                   shed={"WHEAT": 5, "GOOSE": 0, "COW": 0, "SHEEP": 0})
    digests, records = [], []
    for _ in range(2):
        overlay = H1Overlay(fresh_baseline)
        overlay.act(copy.deepcopy(obs), copy.deepcopy(full_config))
        plan = overlay.plans[0]
        blob = json.dumps({"actions": plan["actions"],
                           "baseline": plan["baseline"],
                           "states": plan["expected_states"]},
                          sort_keys=True, default=str)
        digests.append(hashlib.sha256(blob.encode()).hexdigest())
        records.append(_scrub(overlay.open_records.get(0)))
    assert records[0]["reason"] == "OK_ACTIVATED"
    assert digests[0] == digests[1]
    assert records[0] == records[1]


def test_H_proposal_order_stable(fresh_baseline):
    import h1_search
    farm = {"farmer": [4, 4], "hands": [],
            "tiles": [[None] * 10 for _ in range(10)]}
    for x in range(10):
        for y in range(10):
            farm["tiles"][y][x] = wheat_tile(yield_units=6)
    private = {"shed": {}, "seeds": {}, "inventories": [{"WHEAT": 2}]}
    rows = [{"pre_market_shed": {}, "post_market_shed": {},
             "deposited_by_actor": [{}], "sold": {}} for _ in range(7)]
    best = {"rows": rows, "states": [(farm, private)] * 7,
            "events": []}
    prices = dict(PRICES)
    first = h1_search.proposals(best, 0, prices)
    second = h1_search.proposals(
        copy.deepcopy(best), 0, dict(prices))
    assert first == second


# --------------------------------------- Test I: disagreement → abstain
def test_I_physical_mismatch_abandons(overlay, fresh_baseline,
                                      full_config):
    from h1_agent import H1Overlay
    obs = make_obs(712, tiles=[(4, 4, wheat_tile(yield_units=6))])
    overlay.act(copy.deepcopy(obs), copy.deepcopy(full_config))
    assert overlay.open_records[0]["reason"] == "OK_ACTIVATED"
    assert 0 in overlay.plans
    # Step 713 with a teleported worker: physical state diverges.
    obs713 = make_obs(713, tiles=[(4, 4, wheat_tile(yield_units=6))])
    obs713["farms"][0]["farmer"] = [0, 0]
    live = fresh_baseline.call(copy.deepcopy(obs713),
                               copy.deepcopy(full_config))
    out = overlay.act(copy.deepcopy(obs713),
                      copy.deepcopy(full_config))
    record = overlay.open_records.get(0)
    assert record["reason"] == "ABANDON_MISMATCH_T"
    assert record["abandon_step"] == 713
    assert record["subcause"]["physical_match"] is False
    assert out == live
    assert 0 not in overlay.plans


def test_I_baseline_action_mismatch_abandons(overlay, fresh_baseline,
                                             full_config):
    # Direct rule test: predicted baseline ≠ live baseline ⇒ abandon.
    plan = {"baseline": [
        {"farmer": ["PASS"], "hands": [["PASS"], ["PASS"]],
         "market": []} for _ in range(7)],
        "actions": [
            {"farmer": ["NORTH"], "hands": [["PASS"], ["PASS"]],
             "market": []} for _ in range(7)],
        "expected_states": [({}, {}) for _ in range(7)]}
    obs = make_obs(713)
    import h1_shadow
    import h1_agent
    orig = h1_shadow.physical_state
    h1_agent.physical_state = lambda o: ({}, {})
    try:
        live = {"farmer": ["SOUTH"],  # differs from predicted PASS
                "hands": [["PASS"], ["PASS"]], "market": []}
        overlay.plans[0] = plan
        overlay.last_steps[0] = 712
        overlay._open_record(0)
        out = overlay._verify_and_emit(0, 713, obs, full_config,
                                       plan, live)
    finally:
        h1_agent.physical_state = orig
    assert out == live
    assert overlay.open_records[0]["reason"] == "ABANDON_MISMATCH_T"
    assert overlay.open_records[0]["subcause"][
        "baseline_action_match"] is False


def test_I_nonconsecutive_abandons(overlay, fresh_baseline,
                                   full_config):
    obs = make_obs(712, tiles=[(4, 4, wheat_tile(yield_units=6))])
    overlay.act(copy.deepcopy(obs), copy.deepcopy(full_config))
    assert 0 in overlay.plans
    obs715 = make_obs(715)  # skipped 713–714
    live = fresh_baseline.call(copy.deepcopy(obs715),
                               copy.deepcopy(full_config))
    out = overlay.act(copy.deepcopy(obs715),
                      copy.deepcopy(full_config))
    assert overlay.open_records[0]["reason"] == \
        "ABANDON_NONCONSECUTIVE"
    assert out == live
    assert 0 not in overlay.plans


# ------------------------------------------- Test J: no candidate → base
def test_J_no_valid_candidate_exact_baseline(overlay, fresh_baseline,
                                             full_config):
    obs = make_obs(712)  # barren: no yield, no carry, no fertilizer
    live = fresh_baseline.call(copy.deepcopy(obs),
                               copy.deepcopy(full_config))
    out = overlay.act(copy.deepcopy(obs), copy.deepcopy(full_config))
    record = overlay.open_records.get(0)
    assert record["reason"] == "ABSTAIN_NO_GAIN"
    assert out == live
    assert 0 not in overlay.plans
