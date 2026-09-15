# SPDX-License-Identifier: MIT
"""Fertilizer boundary (P6/R8), sparse markets (H1), DROP capacity.

* Fertilizer: H1 may only reap tiles flagged at E (reap-only-flagged);
  it never emits FERTILIZE; audit fields are populated.
* Sparse markets: empty/tiny markets are admitted (never assumed into
  a clearing shape); planning handles them.
* DROP: shed-capacity boundary behavior incl. overflow accounting.
"""

import copy

from conftest import cow_tile, make_obs, wheat_tile


def _activated(fresh_baseline, full_config, **obs_kwargs):
    from h1_agent import H1Overlay
    overlay = H1Overlay(fresh_baseline)
    obs = make_obs(712, **obs_kwargs)
    overlay.act(copy.deepcopy(obs), copy.deepcopy(full_config))
    record = overlay.open_records.get(0)
    assert record["reason"] == "OK_ACTIVATED", record
    return overlay, obs, record


# ------------------------------------------------- fertilizer boundary
def test_collect_only_flagged_at_E(fresh_baseline, full_config):
    flagged = cow_tile(fertilizer=True)
    unflagged = cow_tile(fertilizer=False)
    overlay, obs, _ = _activated(
        fresh_baseline, full_config,
        tiles=[(4, 4, flagged), (6, 6, unflagged)],
        shed={"WHEAT": 5})
    plan = overlay.plans[0]
    flagged_xy = {(x, y) for (x, y, t) in [(4, 4, flagged)]
                  if t.get("fertilizer_available")}
    for event in plan["final_run"]["events"]:
        if event.get("op") == "COLLECT_FERTILIZER":
            assert tuple(event["xy"]) in flagged_xy, event


def test_no_fertilize_emission(fresh_baseline, full_config):
    overlay, _, _ = _activated(
        fresh_baseline, full_config,
        tiles=[(4, 4, cow_tile(fertilizer=True))],
        shed={"WHEAT": 5})
    for action in overlay.plans[0]["actions"]:
        commands = [action.get("farmer", ["PASS"])] + list(
            action.get("hands", []) or [])
        for command in commands:
            assert command[0] != "FERTILIZE"


def test_fertilizer_audit_fields_populated(fresh_baseline,
                                           full_config):
    overlay, _, record = _activated(
        fresh_baseline, full_config,
        tiles=[(4, 4, cow_tile(fertilizer=True, yield_units=2))],
        shed={"WHEAT": 5})
    assert isinstance(record["fertilizer_reaped"], int)
    assert isinstance(record["fertilizer_baseline"], int)
    assert record["fertilizer_reaped"] >= 0
    assert record["fertilizer_baseline"] >= 0


def test_unflagged_cow_never_collected_by_search(fresh_baseline):
    # Generator-level: an unflagged animal tile yields no COLLECT op
    # even when it is the only bundle in range.
    import h1_search
    farm = {"farmer": [4, 5], "hands": [],
            "tiles": [[None] * 10 for _ in range(10)]}
    farm["tiles"][4][4] = cow_tile(yield_units=0, fertilizer=False)
    private = {"shed": {}, "seeds": {}, "inventories": [{}]}
    rows = [{"pre_market_shed": {}, "post_market_shed": {},
             "deposited_by_actor": [{}], "sold": {}} for _ in range(7)]
    best = {"rows": rows, "states": [(farm, private)] * 7,
            "events": []}
    prices = {p: 10 for p in
              ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON",
               "EGG", "MILK", "WOOL", "FERTILIZER")}
    props = h1_search.proposals(best, 0, prices)
    for _, _, route, _ in props:
        for command in route:
            assert command[0] != "COLLECT_FERTILIZER"


# ------------------------------------------------------- sparse markets
def test_empty_market_admitted(fresh_baseline, full_config,
                               monkeypatch):
    # Yarn t=718 route market is EMPTY; 712–717 must also tolerate
    # empties: blank the slice markets and confirm no MARKET_OP abstain
    # from sparsity alone (other reasons may still apply).
    import copy as _copy
    table = _copy.deepcopy(
        fresh_baseline.policies["backbone"].route_prior)
    for t in range(712, 718):
        table[t]["market"] = []
    monkeypatch.setattr(fresh_baseline.policies["backbone"],
                        "route_prior", table)
    from h1_agent import H1Overlay
    overlay = H1Overlay(fresh_baseline)
    obs = make_obs(712, tiles=[(4, 4, wheat_tile(yield_units=6))])
    out = overlay.act(copy.deepcopy(obs), copy.deepcopy(full_config))
    record = overlay.open_records.get(0)
    assert record["reason"] != "ABSTAIN_MARKET_OP"
    if record["reason"] != "OK_ACTIVATED":
        live = fresh_baseline.call(copy.deepcopy(obs),
                                   copy.deepcopy(full_config))
        assert out == live


def test_single_tiny_sell_admitted(fresh_baseline, full_config,
                                   monkeypatch):
    import copy as _copy
    table = _copy.deepcopy(
        fresh_baseline.policies["backbone"].route_prior)
    for t in range(712, 718):
        table[t]["market"] = [["SELL", "WOOL", 1]]
    monkeypatch.setattr(fresh_baseline.policies["backbone"],
                        "route_prior", table)
    from h1_agent import H1Overlay
    overlay = H1Overlay(fresh_baseline)
    obs = make_obs(712, tiles=[(4, 4, wheat_tile(yield_units=6))])
    overlay.act(copy.deepcopy(obs), copy.deepcopy(full_config))
    record = overlay.open_records.get(0)
    assert record["reason"] != "ABSTAIN_MARKET_OP"


# ------------------------------------------------------- DROP capacity
def test_drop_at_capacity_boundary(fresh_baseline):
    from h1_shadow import ShadowCursor, execute_units
    obs = make_obs(712, hands=(), shed={"WHEAT": 99},
                   inventories=[{"WOOL": 2}])
    obs["farms"][0]["farmer"] = [4, 4]  # shed access
    cursor = ShadowCursor(fresh_baseline, 0, obs, None, None, {},
                          "", [])
    execute_units(cursor, {"farmer": ["DROP"], "hands": [],
                           "market": []}, 712, 0)
    assert cursor.private["shed"]["WHEAT"] == 99
    assert cursor.private["shed"]["WOOL"] == 1
    assert cursor.overflow == 1
    assert cursor.private["inventories"][0] == {}


def test_drop_full_shed_all_destroyed(fresh_baseline):
    from h1_dominance import dominates
    from h1_shadow import ShadowCursor, execute_units
    obs = make_obs(712, hands=(), shed={"WHEAT": 100},
                   inventories=[{"WOOL": 3}])
    obs["farms"][0]["farmer"] = [4, 4]
    cursor = ShadowCursor(fresh_baseline, 0, obs, None, None, {},
                          "", [])
    execute_units(cursor, {"farmer": ["DROP"], "hands": [],
                           "market": []}, 712, 0)
    assert cursor.overflow == 3
    assert cursor.private["shed"] == {"WHEAT": 100}
    # ...and any candidate overflowing is dominance-rejected.
    run = {"rows": [{"pre_market_shed": {}, "post_market_shed": {},
                     "deposited_by_actor": [{}], "sold": {}}],
           "overflow_units": 3}
    base = {"rows": [{"pre_market_shed": {}, "post_market_shed": {},
                      "deposited_by_actor": [{}], "sold": {}}],
            "overflow_units": 0}
    assert dominates(run, base) is False


def test_drop_away_from_shed_noop(fresh_baseline):
    from h1_shadow import ShadowCursor, execute_units
    obs = make_obs(712, hands=(), shed={"WHEAT": 10},
                   inventories=[{"WOOL": 2}])
    obs["farms"][0]["farmer"] = [0, 0]  # not shed access
    cursor = ShadowCursor(fresh_baseline, 0, obs, None, None, {},
                          "", [])
    execute_units(cursor, {"farmer": ["DROP"], "hands": [],
                           "market": []}, 712, 0)
    assert cursor.overflow == 0
    assert cursor.private["shed"] == {"WHEAT": 10}
    assert cursor.private["inventories"][0] == {"WOOL": 2}
