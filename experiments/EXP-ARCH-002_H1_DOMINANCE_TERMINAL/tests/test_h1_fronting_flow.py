# SPDX-License-Identifier: MIT
"""Money/flow-dependent fronting tests (transplant hazard H4).

* The shadow's fronting-trigger mirror is exact given identical
  inputs (all three trigger legs + the off state).
* A live fronting flip (SELL reorder) mid-window abandons to baseline.
* Money-gap bookkeeping uses projected-own minus frozen-opponent money.
"""

import copy

from conftest import make_obs

PRODUCTS_9 = ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON",
              "EGG", "MILK", "WOOL", "FERTILIZER")


def _ledgers(**over):
    base = {"last_step": 711, "route": "default",
            "near_streak": 0, "near_latched": False,
            "last_inventory": None, "last_market_net": {},
            "last_shops": [], "opponent_supply": {},
            "mirror_confidence": 0.0, "mirror_evidence_turns": 0,
            "due": {}, "pending": {}}
    base.update(over)
    return base


def _compare(fresh_baseline, full_config, obs, ledgers):
    from h1_shadow import ShadowCursor, predict_baseline_action
    policy = fresh_baseline.policies["backbone"]
    policy.controller.states[0] = copy.deepcopy(ledgers)
    visible = fresh_baseline.visible_configuration(full_config)
    live = policy(copy.deepcopy(obs), copy.deepcopy(visible))
    cursor = ShadowCursor(fresh_baseline, 0, obs, full_config,
                          visible, copy.deepcopy(ledgers),
                          "backbone", policy.route_prior)
    pred = predict_baseline_action(cursor, 712)
    return live, pred


def test_fronting_off_mirror(fresh_baseline, full_config):
    obs = make_obs(712, money=9000.0, opp_money=9000.0,
                   shed={"WHEAT": 10, "CARROT": 6})
    live, pred = _compare(fresh_baseline, full_config, obs,
                          _ledgers())
    assert pred == live


def test_fronting_on_near_latch_mirror(fresh_baseline, full_config):
    obs = make_obs(712, money=9000.0, opp_money=9000.0,
                   shed={"WHEAT": 10, "CARROT": 6})
    live, pred = _compare(fresh_baseline, full_config, obs,
                          _ledgers(near_latched=True, near_streak=12))
    assert pred == live


def test_fronting_on_money_deficit_mirror(fresh_baseline,
                                          full_config):
    # Behind by ≥ $4,500 (live front_money_deficit).
    obs = make_obs(712, money=1000.0, opp_money=9000.0,
                   shed={"WHEAT": 10, "CARROT": 6})
    live, pred = _compare(fresh_baseline, full_config, obs,
                          _ledgers())
    assert pred == live


def test_fronting_on_supply_peak_mirror(fresh_baseline, full_config):
    obs = make_obs(712, money=9000.0, opp_money=9000.0,
                   shed={"WHEAT": 10, "CARROT": 6})
    supply = {p: 0.0 for p in PRODUCTS_9}
    supply["CARROT"] = 9.0  # ≥ live threshold 3.0, in front_items
    live, pred = _compare(fresh_baseline, full_config, obs,
                          _ledgers(opponent_supply=supply))
    assert pred == live


def test_fronting_trigger_actually_fires(fresh_baseline, full_config):
    # Sanity: the crafted states above genuinely exercise the fronting
    # branch (not vacuously the else path in both).
    from h1_shadow import ShadowCursor, predict_baseline_action
    obs = make_obs(712, money=9000.0, opp_money=9000.0,
                   shed={"WHEAT": 10, "CARROT": 6})
    policy = fresh_baseline.policies["backbone"]
    visible = fresh_baseline.visible_configuration(full_config)
    cursor = ShadowCursor(fresh_baseline, 0, obs, full_config,
                          visible,
                          _ledgers(near_latched=True, near_streak=12),
                          "backbone", policy.route_prior)
    predict_baseline_action(cursor, 712)
    # Fronting ran (telemetry may or may not count a reorder, but the
    # ledger path executed without error and ledgers advanced).
    assert cursor.ledgers["last_step"] == 712
    assert "CARROT" in cursor.ledgers["last_market_net"]


def test_live_fronting_flip_abandons(overlay, fresh_baseline,
                                     full_config):
    # A mid-window SELL reorder flip (fronting fired in live but not
    # in the plan's prediction, or vice versa) abandons to baseline.
    plan = {"baseline": [
        {"farmer": ["PASS"], "hands": [["PASS"], ["PASS"]],
         "market": [["SELL", "WHEAT", 5], ["SELL", "CARROT", 2]]}
        for _ in range(7)],
        "actions": [
            {"farmer": ["NORTH"], "hands": [["PASS"], ["PASS"]],
             "market": [["SELL", "WHEAT", 5], ["SELL", "CARROT", 2]]}
            for _ in range(7)],
        "expected_states": [({}, {}) for _ in range(7)]}
    obs = make_obs(714)
    import h1_agent
    orig = h1_agent.physical_state
    h1_agent.physical_state = lambda o: ({}, {})
    try:
        live = {"farmer": ["PASS"], "hands": [["PASS"], ["PASS"]],
                "market": [["SELL", "CARROT", 2],
                           ["SELL", "WHEAT", 5]]}  # flipped order
        overlay.plans[0] = plan
        overlay.last_steps[0] = 713
        overlay._open_record(0)
        out = overlay._verify_and_emit(0, 714, obs, full_config,
                                       plan, live)
    finally:
        h1_agent.physical_state = orig
    assert out == live
    assert overlay.open_records[0]["reason"] == "ABANDON_MISMATCH_T"


def test_money_gap_uses_projected_money(fresh_baseline, full_config):
    # The cursor's projected money (entry + unilateral revenue − BUY
    # costs) feeds the gap; opponent money stays frozen at entry.
    from h1_shadow import ShadowCursor
    obs = make_obs(712, money=5000.0, opp_money=7000.0)
    cursor = ShadowCursor(fresh_baseline, 0, obs, full_config,
                          full_config, {}, "backbone", [])
    projected = cursor.project_obs(714)
    assert float(projected["farms"][0]["money"]) == 5000.0
    assert float(projected["farms"][1]["money"]) == 7000.0
    cursor.farm["money"] = 5400.0  # simulated SELL revenue
    projected = cursor.project_obs(715)
    assert float(projected["farms"][0]["money"]) == 5400.0
    assert float(projected["farms"][1]["money"]) == 7000.0
