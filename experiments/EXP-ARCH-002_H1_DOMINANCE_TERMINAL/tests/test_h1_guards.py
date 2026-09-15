# SPDX-License-Identifier: MIT
"""Entry-guard unit tests G0–G7 (prereg §10.1).

Every test asserts the frozen reason code AND exact live-baseline
passthrough on abstention (abstain-to-baseline identity).
"""

import copy

from conftest import cow_tile, make_obs, wheat_tile


def _act(overlay, fresh_baseline, obs, config):
    live = fresh_baseline.call(copy.deepcopy(obs), copy.deepcopy(config))
    out = overlay.act(copy.deepcopy(obs), copy.deepcopy(config))
    record = overlay.open_records.get(int(obs.get("player", 0)))
    return live, out, record


# ------------------------------------------------------------------ G0
def test_g0_bad_board_size_abstains(overlay, fresh_baseline,
                                    full_config):
    cfg = dict(full_config, boardSize=9)
    obs = make_obs(712)
    live, out, record = _act(overlay, fresh_baseline, obs, cfg)
    assert record["reason"] == "ABSTAIN_CONFIG"
    assert record["subcause"]["pin"] == "boardSize"
    assert out == live


def test_g0_each_pin_enforced(overlay, fresh_baseline, full_config):
    bad = {"boardSize": 8, "turnsPerDay": 12, "episodeSteps": 700,
           "shedCapacity": 50, "maxMarketOrdersPerTurn": 5}
    for key, value in bad.items():
        cfg = dict(full_config)
        cfg[key] = value
        ov = type(overlay)(fresh_baseline)
        live, out, record = _act(ov, fresh_baseline, make_obs(712),
                                 cfg)
        assert record["reason"] == "ABSTAIN_CONFIG", key
        assert record["subcause"]["pin"] == key, key
        assert out == live, key


def test_g0_none_config_uses_dmitrii_defaults(overlay, fresh_baseline):
    # Mirror of Dmitrii _settings/_settings_guard: missing keys fall
    # back to the validated engine values, then equality is checked.
    obs = make_obs(712)
    live, out, record = _act(overlay, fresh_baseline, obs, None)
    assert record["reason"] != "ABSTAIN_CONFIG"
    if record["reason"] != "OK_ACTIVATED":
        assert out == live


# ------------------------------------------------------------------ G1
def test_g1_overfull_shed_abstains(overlay, fresh_baseline,
                                   full_config):
    obs = make_obs(712, shed={"WHEAT": 101})
    live, out, record = _act(overlay, fresh_baseline, obs,
                             full_config)
    assert record["reason"] == "ABSTAIN_SHED"
    assert out == live


def test_g1_negative_shed_abstains(overlay, fresh_baseline,
                                   full_config):
    obs = make_obs(712, shed={"WHEAT": -1})
    live, out, record = _act(overlay, fresh_baseline, obs,
                             full_config)
    assert record["reason"] == "ABSTAIN_SHED"
    assert out == live


def test_g1_float_shed_abstains_strict_int(overlay, fresh_baseline,
                                           full_config):
    obs = make_obs(712, shed={"WHEAT": 5.0})
    live, out, record = _act(overlay, fresh_baseline, obs,
                             full_config)
    assert record["reason"] == "ABSTAIN_SHED"
    assert out == live


def test_g1_zero_animal_keys_admitted(overlay, fresh_baseline,
                                      full_config):
    # Engine zero-valued animal keys must NOT trip G1/G2.
    obs = make_obs(712, shed={"WHEAT": 5, "GOOSE": 0, "COW": 0,
                              "SHEEP": 0})
    live, out, record = _act(overlay, fresh_baseline, obs,
                             full_config)
    assert record["reason"] not in ("ABSTAIN_SHED", "ABSTAIN_ITEMS")


# ------------------------------------------------------------------ G2
def test_g2_live_animal_in_shed_abstains(overlay, fresh_baseline,
                                         full_config):
    obs = make_obs(712, shed={"WHEAT": 5, "GOOSE": 1})
    live, out, record = _act(overlay, fresh_baseline, obs,
                             full_config)
    assert record["reason"] == "ABSTAIN_ITEMS"
    assert out == live


def test_g2_unknown_item_abstains(overlay, fresh_baseline,
                                  full_config):
    obs = make_obs(712, shed={"WHEAT": 5, "UNOBTANIUM": 2})
    live, out, record = _act(overlay, fresh_baseline, obs,
                             full_config)
    assert record["reason"] == "ABSTAIN_ITEMS"
    assert out == live


def test_g2_inventory_shape_mismatch_abstains(overlay, fresh_baseline,
                                              full_config):
    obs = make_obs(712, hands=((4, 5), (5, 4)))
    obs["private"]["inventories"] = [{}, {}]  # 2 vs 3 workers
    live, out, record = _act(overlay, fresh_baseline, obs,
                             full_config)
    assert record["reason"] == "ABSTAIN_ITEMS"
    assert out == live


# ----------------------------------------------------------------- G3a
def test_g3a_plant_in_slice_abstains(overlay, fresh_baseline,
                                     full_config, monkeypatch):
    import copy as _copy
    table = _copy.deepcopy(
        fresh_baseline.policies["backbone"].route_prior)
    table[714]["farmer"] = ["PLANT", "WHEAT"]
    monkeypatch.setattr(fresh_baseline.policies["backbone"],
                        "route_prior", table)
    obs = make_obs(712)
    live, out, record = _act(overlay, fresh_baseline, obs,
                             full_config)
    assert record["reason"] == "ABSTAIN_WINDOW_OPS"
    assert record["subcause"] == {"step": 714, "op": "PLANT"}
    assert out == live


def test_g3a_build_in_slice_abstains(overlay, fresh_baseline,
                                     full_config, monkeypatch):
    import copy as _copy
    table = _copy.deepcopy(
        fresh_baseline.policies["backbone"].route_prior)
    table[712]["hands"][0] = ["BUILD_PASTURE"]
    monkeypatch.setattr(fresh_baseline.policies["backbone"],
                        "route_prior", table)
    obs = make_obs(712)
    live, out, record = _act(overlay, fresh_baseline, obs,
                             full_config)
    assert record["reason"] == "ABSTAIN_WINDOW_OPS"
    assert record["subcause"]["op"] == "BUILD_PASTURE"
    assert out == live


# ----------------------------------------------------------------- G3b
def test_g3b_hire_in_slice_abstains(overlay, fresh_baseline,
                                    full_config, monkeypatch):
    import copy as _copy
    table = _copy.deepcopy(
        fresh_baseline.policies["backbone"].route_prior)
    table[715]["market"] = [["HIRE"]]
    monkeypatch.setattr(fresh_baseline.policies["backbone"],
                        "route_prior", table)
    obs = make_obs(712)
    live, out, record = _act(overlay, fresh_baseline, obs,
                             full_config)
    assert record["reason"] == "ABSTAIN_MARKET_OP"
    assert out == live


def test_g3b_buy_seed_in_slice_abstains(overlay, fresh_baseline,
                                        full_config, monkeypatch):
    import copy as _copy
    table = _copy.deepcopy(
        fresh_baseline.policies["backbone"].route_prior)
    table[713]["market"] = [["BUY_SEED", "WHEAT", 3]]
    monkeypatch.setattr(fresh_baseline.policies["backbone"],
                        "route_prior", table)
    obs = make_obs(712)
    live, out, record = _act(overlay, fresh_baseline, obs,
                             full_config)
    assert record["reason"] == "ABSTAIN_MARKET_OP"
    assert out == live


# ----------------------------------------------------------------- G3c
def test_g3c_pending_nonempty_abstains(overlay, fresh_baseline,
                                       full_config, monkeypatch):
    states = fresh_baseline.policies["backbone"].controller.states
    monkeypatch.setitem(states, 0, {
        "last_step": 711, "route": "default",
        "pending": {"WHEAT": {"quantity": 4, "entry_step": 710,
                              "release_step": 712}}})
    obs = make_obs(712)
    live, out, record = _act(overlay, fresh_baseline, obs,
                             full_config)
    assert record["reason"] == "ABSTAIN_MARKET_OP"
    assert record["subcause"]["order"] == "pending-nonempty"
    assert out == live


def test_discrepancy1_fertilizer_buy_abstains(overlay, fresh_baseline,
                                              full_config, monkeypatch):
    # Conservative extension (see h1_agent): FERTILIZER BUYs are
    # unreachable in live window slices, but the frozen $125/U
    # derivation covers WHEAT only, so they must fail closed.
    import copy as _copy
    table = _copy.deepcopy(
        fresh_baseline.policies["backbone"].route_prior)
    table[716]["market"] = [["BUY_PRODUCT", "FERTILIZER", 2]]
    monkeypatch.setattr(fresh_baseline.policies["backbone"],
                        "route_prior", table)
    obs = make_obs(712, money=100000.0)
    live, out, record = _act(overlay, fresh_baseline, obs,
                             full_config)
    assert record["reason"] == "ABSTAIN_MARKET_OP"
    assert out == live


# ------------------------------------------------------------------ G4
def test_g4_insufficient_buy_coverage_abstains_yarn(
        overlay, fresh_baseline, full_config):
    # Yarn window BUYs: 18 + 32 = 50 U → requires $6,250 at E.
    obs = make_obs(712, money=100.0, shops=("YARN_STORE",))
    live, out, record = _act(overlay, fresh_baseline, obs,
                             full_config)
    assert record["reason"] == "ABSTAIN_BUY_COVERAGE"
    assert record["subcause"]["U"] == 50
    assert record["subcause"]["required"] == 6250
    assert out == live


def test_g4_sufficient_coverage_passes_gate(overlay, fresh_baseline,
                                            full_config):
    obs = make_obs(712, money=6250.0, shops=("YARN_STORE",))
    live, out, record = _act(overlay, fresh_baseline, obs,
                             full_config)
    assert record["reason"] != "ABSTAIN_BUY_COVERAGE"
    if record["reason"] != "OK_ACTIVATED":
        assert out == live


def test_g4_backbone_zero_buy_units(overlay, fresh_baseline,
                                    full_config):
    obs = make_obs(712, money=0.0)
    live, out, record = _act(overlay, fresh_baseline, obs,
                             full_config)
    # Backbone has no window BUYs (U=0): coverage cannot fail.
    assert record["reason"] != "ABSTAIN_BUY_COVERAGE"


# ------------------------------------------------------------------ G5
def test_g5_handshake_polices_skipped_shed_guard(
        overlay, fresh_baseline, full_config):
    # Inconsistent obs (hour 23 at step 712): the live shed-guard FIRES
    # (appends SELLs) while the shadow skips it by proof → the
    # handshake must catch the divergence and abstain.
    obs = make_obs(712, shed={"WHEAT": 90, "MILK": 9},
                   inventories=[{"WOOL": 5}, {}, {}])
    obs["hour"] = 23
    live, out, record = _act(overlay, fresh_baseline, obs,
                             full_config)
    assert record["reason"] == "ABSTAIN_HANDSHAKE"
    # NOTE: the shed-guard rewrites DROP→PASS (unit mutation) in
    # addition to appending SELLs, so the first-diverging field may be
    # farmer, hands, or market depending on the route slice.
    assert record["subcause"]["field"] in ("farmer", "hands", "market")
    assert out == live


def test_g5_handshake_passes_on_clean_state(overlay, fresh_baseline,
                                            full_config):
    obs = make_obs(712, tiles=[(4, 4, wheat_tile())])
    live, out, record = _act(overlay, fresh_baseline, obs,
                             full_config)
    assert record["reason"] != "ABSTAIN_HANDSHAKE"


# ------------------------------------------------------------------ G6
def test_g6_budget_exhaustion_abstains(monkeypatch, fresh_baseline,
                                       full_config):
    import h1_search
    from h1_agent import H1Overlay
    # Regression: tiny budget must be ENFORCED, never exceeded.
    monkeypatch.setattr(h1_search, "MAX_SIMULATIONS", 2)
    overlay = H1Overlay(fresh_baseline)
    tiles = [(x, y, wheat_tile(yield_units=6))
             for x in range(10) for y in range(10)]
    obs = make_obs(712, hands=tuple((x, 0) for x in range(9)),
                   tiles=tiles)
    live = fresh_baseline.call(copy.deepcopy(obs),
                               copy.deepcopy(full_config))
    out = overlay.act(copy.deepcopy(obs), copy.deepcopy(full_config))
    record = overlay.open_records.get(0)
    assert record["simulations"] is None or \
        record["simulations"] <= 2
    assert record["reason"] in ("ABSTAIN_BUDGET", "OK_ACTIVATED",
                                "ABSTAIN_NO_GAIN", "ABSTAIN_DOMINANCE",
                                "ABSTAIN_NOSTEAL", "ABSTAIN_ACCEPT")
    if record["reason"] == "ABSTAIN_BUDGET":
        assert record["subcause"] == {"simulations": 2}
        assert out == live


def test_g6_direct_reserve_and_cap_structure(fresh_baseline):
    # Structural: proposals() honors reservation + per-worker cap on a
    # synthetic best-run with many bundles.
    import h1_search
    from h1_dominance import entry_prices
    prices = {p: 10 for p in
              ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON",
               "EGG", "MILK", "WOOL", "FERTILIZER")}
    farm = {"farmer": [4, 4], "hands": [],
            "tiles": [[None] * 10 for _ in range(10)]}
    for x in range(10):
        for y in range(10):
            farm["tiles"][y][x] = wheat_tile(yield_units=6)
    private = {"shed": {}, "seeds": {},
               "inventories": [{"WHEAT": 3}]}
    rows = [{"pre_market_shed": {}, "post_market_shed": {},
             "deposited_by_actor": [{}], "sold": {}} for _ in range(7)]
    best = {"rows": rows,
            "states": [(farm, private)] * 7,
            "events": []}
    props = h1_search.proposals(best, 0, prices)
    assert len(props) <= 8
    assert len(props) == 8  # rich state saturates the cap
    assert all(p[3] == 0 for p in props[:2])  # direct reserves first
    assert all(p[0] > 0 for p in props[:2])
