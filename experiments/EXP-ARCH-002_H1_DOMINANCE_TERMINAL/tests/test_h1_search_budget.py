# SPDX-License-Identifier: MIT
"""Search-budget enforcement (prereg §7/S5, §9/T5–T6).

Proves programmatically: fixed candidate ordering, hard simulation
cap, per-worker (not per-offset) proposal cap, no adaptive expansion,
and fail-safe behavior on a deliberate budget-exceeding attempt.
"""

import copy

from conftest import make_obs, wheat_tile


def _rich_obs():
    tiles = [(x, y, wheat_tile(yield_units=6))
             for x in range(10) for y in range(10)]
    return make_obs(712, hands=tuple((x, 0) for x in range(9)),
                    tiles=tiles, shed={"WHEAT": 20})


def test_simulations_never_exceed_128(fresh_baseline, full_config):
    from h1_agent import H1Overlay
    overlay = H1Overlay(fresh_baseline)
    overlay.act(copy.deepcopy(_rich_obs()),
                copy.deepcopy(full_config))
    record = overlay.open_records.get(0)
    if record["simulations"] is not None:
        assert record["simulations"] <= 128
    if record["reason"] == "ABSTAIN_BUDGET":
        assert record["subcause"] == {"simulations": 128}


def test_per_worker_cap_not_per_offset(fresh_baseline):
    # The ≤8 cap applies across ALL offsets of one worker: with 7
    # offsets each able to generate variants, one worker still yields
    # at most 8 proposals total.
    import h1_search
    farm = {"farmer": [4, 4], "hands": [],
            "tiles": [[None] * 10 for _ in range(10)]}
    for x in range(10):
        for y in range(10):
            farm["tiles"][y][x] = wheat_tile(yield_units=6)
    private = {"shed": {}, "seeds": {}, "inventories": [{}]}
    rows = [{"pre_market_shed": {}, "post_market_shed": {},
             "deposited_by_actor": [{}], "sold": {}} for _ in range(7)]
    best = {"rows": rows, "states": [(farm, private)] * 7,
            "events": []}
    prices = {p: 10 for p in
              ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON",
               "EGG", "MILK", "WOOL", "FERTILIZER")}
    props = h1_search.proposals(best, 0, prices)
    assert len(props) <= 8
    assert len({p[1] for p in props}) >= 1  # offsets represented
    # ...but a per-offset reading would admit up to 7×8 = 56.
    assert len(props) < 56


def test_budget_exceeded_attempt_fails_safe(monkeypatch, fresh_baseline,
                                            full_config):
    # Adversarial: shrink the budget to 1 sim.  Planning must honor it
    # exactly (≤1 trial sim) and report a budget-consistent outcome.
    import h1_search
    from h1_agent import H1Overlay
    monkeypatch.setattr(h1_search, "MAX_SIMULATIONS", 1)
    overlay = H1Overlay(fresh_baseline)
    obs = _rich_obs()
    live = fresh_baseline.call(copy.deepcopy(obs),
                               copy.deepcopy(full_config))
    out = overlay.act(copy.deepcopy(obs), copy.deepcopy(full_config))
    record = overlay.open_records.get(0)
    if record["reason"] == "ABSTAIN_BUDGET":
        assert record["subcause"] == {"simulations": 1}
        assert out == live
    elif record["reason"] == "OK_ACTIVATED":
        assert record["simulations"] <= 1
    else:
        # NO_GAIN/DOMINANCE/etc. after ≤1 trial: still consistent.
        assert out == live or record["reason"] == "OK_ACTIVATED"


def test_no_adaptive_expansion_hook(fresh_baseline, full_config):
    # The search loop reads the frozen cap; there is no code path that
    # grows the budget based on intermediate results.
    import inspect
    import h1_search
    src = inspect.getsource(h1_search.plan_terminal)
    assert "MAX_SIMULATIONS" in src
    # Exactly two counters: the gating sim budget + a non-gating
    # telemetry mirror.  No other accumulator can grow the budget.
    stripped = src.replace("simulations += 1", "").replace(
        "trials_evaluated += 1", "")
    assert "+=" not in stripped
    assert "-=" not in stripped
    assert src.count("simulations +=") == 1


def test_fixed_enumeration_order(fresh_baseline):
    # Worker-major, offset-minor enumeration is structural: proposals
    # for one worker sort by (-net, offset, route) — verify total
    # order on a crafted set with ties.
    import h1_search
    farm = {"farmer": [4, 4], "hands": [],
            "tiles": [[None] * 10 for _ in range(10)]}
    farm["tiles"][4][5] = wheat_tile(yield_units=6)
    farm["tiles"][5][4] = wheat_tile(yield_units=6)
    private = {"shed": {}, "seeds": {}, "inventories": [{}]}
    rows = [{"pre_market_shed": {}, "post_market_shed": {},
             "deposited_by_actor": [{}], "sold": {}} for _ in range(7)]
    best = {"rows": rows, "states": [(farm, private)] * 7,
            "events": []}
    prices = {p: 10 for p in
              ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON",
               "EGG", "MILK", "WOOL", "FERTILIZER")}
    first = h1_search.proposals(best, 0, prices)
    keys = [(-p[0], p[1], tuple(tuple(c) for c in p[2]))
            for p in first]
    assert keys == sorted(keys)  # total order honored
    second = h1_search.proposals(copy.deepcopy(best), 0,
                                 dict(prices))
    assert first == second
