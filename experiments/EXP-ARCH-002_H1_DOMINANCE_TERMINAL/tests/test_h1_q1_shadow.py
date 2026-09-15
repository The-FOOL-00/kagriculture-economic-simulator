# SPDX-License-Identifier: MIT
"""Q1 engine-exactness battery (prereg §11/Q1).

Hand-constructed port states (NO game seeds): each case builds a
prescribed physical state directly inside the validated 1.32.7 port,
rolls the H1 shadow transition and the port step function side by
side over 7 window steps (712–718) with a passive opponent, and
asserts EXACT agreement on: tiles, positions, carried inventories
(incl. zero-key deletion), shed, seeds, sold quantities, DROP
overflow, money (unilateral revenue projection), shared inventory,
and refreshed quotes.

PASS bar (prereg): 100% agreement on this frozen battery.
"""

import copy
import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
H1_DIR = os.path.dirname(HERE)
REPO_ROOT = os.path.abspath(os.path.join(H1_DIR, "..", ".."))
PORT_DIR = os.path.join(
    REPO_ROOT, "experiments/EXP-DEV-006_HORIZON_KILLTEST/port")
if PORT_DIR not in sys.path:
    sys.path.insert(0, PORT_DIR)

from kagsim_py import api as papi  # noqa: E402
from kagsim_py import sim as psim  # noqa: E402

PRODUCTS_9 = ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON",
              "EGG", "MILK", "WOOL", "FERTILIZER")
ITEM_INDEX = {name: i for i, name in enumerate(psim.ITEM_NAMES)}
CROP_INDEX = {"WHEAT": 0, "CARROT": 1, "TOMATO": 2, "STRAWBERRY": 3,
              "MELON": 4}
ANIMAL_INDEX = {"GOOSE": 9, "COW": 10, "SHEEP": 11}


def _tile(spec):
    """Obs-style tile dict → port Tile object."""
    t = psim.Tile()
    if spec is None:
        t.kind = psim.T_EMPTY
        return t
    if spec == "LOCKED":
        t.kind = psim.T_LOCKED
        return t
    kind = spec.get("kind")
    if kind == "WEED":
        t.kind = psim.T_WEED
        return t
    if kind == "PLANT":
        t.kind = psim.T_PLANT
        t.what = CROP_INDEX[spec["crop"]]
        t.planted_day = spec.get("planted_day", 0)
        t.watered_today = bool(spec.get("watered_today", False))
        t.consecutive_dry = spec.get("consecutive_unwatered", 0)
        t.yield_units = spec.get("yield_units", 0)
        t.max_lifespan_step = spec.get("max_lifespan_step", -1)
        t.fertilized_until_day = spec.get("fertilized_until_day", -1)
        return t
    if kind in ("COOP", "PASTURE"):
        t.kind = psim.T_COOP if kind == "COOP" else psim.T_PASTURE
        if "animal" in spec:
            t.has_animal = True
            t.what = ANIMAL_INDEX[spec["animal"]]
            t.planted_day = spec.get("placed_day", 0)
            t.yield_units = spec.get("yield_units", 0)
            t.consecutive_dry = spec.get("consecutive_unfed", 0)
            t.fed_today = bool(spec.get("fed_today", False))
            t.cared_today = bool(spec.get("cared_today", False))
            t.fertilizer_available = bool(
                spec.get("fertilizer_available", False))
            t.pending_care_bonus = spec.get("pending_care_bonus", 0)
        return t
    raise ValueError("bad tile spec: %r" % (spec,))


def build_game(seat_spec, market_inventory=None, shops=("BAKERY",),
               money=9000.0, shed=None, seeds=None, start_step=712):
    """Fresh port game with hand-built state (seed-0 shell, unused RNG).

    Window steps execute no RNG (no dawn), so the shell seed is
    irrelevant; every compared field is prescribed below.
    """
    game = papi.Game(seed=0)
    st = game.sim.st
    st.step = start_step
    st.day = start_step // 24
    st.hour = start_step % 24
    st.done = False
    # Passive opponent: one unit, empty farm, corner position.
    opp = st.farms[1]
    opp.money = 5000.0
    opp.pos_x[0] = 0
    opp.pos_y[0] = 0
    f = st.farms[0]
    f.money = float(money)
    f.n_units = 1 + len(seat_spec.get("hands", ()))
    positions = [seat_spec.get("farmer", [4, 4]),
                 *seat_spec.get("hands", ())]
    for u, (x, y) in enumerate(positions):
        f.pos_x[u] = x
        f.pos_y[u] = y
    for y in range(10):
        for x in range(10):
            f.tiles[y][x] = _tile(None)
    for (x, y, spec) in seat_spec.get("tiles", ()):
        f.tiles[y][x] = _tile(spec)
    for u, inv in enumerate(seat_spec.get("inventories", ())):
        for item, qty in inv.items():
            if qty:
                f.inv[u][ITEM_INDEX[item]] = qty
    for item, qty in (shed or {}).items():
        f.shed[ITEM_INDEX[item]] = qty
    f.shed_total = sum(f.shed)
    for item, qty in (seeds or {}).items():
        f.seeds[CROP_INDEX[item]] = qty
    inv = {p: 10000 for p in PRODUCTS_9}
    inv.update(market_inventory or {})
    for i, name in enumerate(psim.ITEM_NAMES[:9]):
        st.market.inventory[i] = inv[name]
    game.sim.refresh_prices()
    st.n_shops = 0
    for shop in shops:
        st.shops[st.n_shops] = psim.SHOP_NAMES.index(shop)
        st.n_shops += 1
    return game


def _pass_action(n_hands):
    return {"farmer": ["PASS"],
            "hands": [["PASS"]] * n_hands, "market": []}


def run_dual(fresh_baseline, full_config, game, schedule):
    """Roll port + shadow side by side; assert exact agreement/step."""
    from h1_shadow import ShadowCursor, simulate_step
    seat = 0
    obs0 = game.observe(seat)
    n_hands = len(obs0["farms"][seat]["hands"])
    # coverage_U=None: Q1 drives the sim directly (the G4 gate and
    # BUY money-fail defense are tested separately).
    cursor = ShadowCursor(fresh_baseline, seat, obs0, full_config,
                          full_config, {}, "q1", [],
                          coverage_U=None)
    opp_pass = _pass_action(0)
    for i, action in enumerate(schedule):
        t = 712 + i
        game.step(copy.deepcopy(action),
                  copy.deepcopy(opp_pass))
        simulate_step(cursor, copy.deepcopy(action), t, i)
        _compare_step(game, cursor, seat, t, i)
    return cursor


def _compare_step(game, cursor, seat, t, i):
    st = game.sim.st
    f = st.farms[seat]
    obs = game.observe(seat)
    farm_o = obs["farms"][seat]
    farm_s = cursor.farm
    assert farm_o["tiles"] == farm_s["tiles"], (t, "tiles")
    assert farm_o["farmer"] == farm_s["farmer"], (t, "farmer")
    assert farm_o["hands"] == farm_s["hands"], (t, "hands")
    assert farm_o["money"] == cursor.money(), (t, "money")
    priv_o = obs["private"]
    priv_s = cursor.private
    assert priv_o["shed"] == priv_s["shed"], (t, "shed")
    assert priv_o["seeds"] == priv_s["seeds"], (t, "seeds")
    assert priv_o["inventories"] == priv_s["inventories"], (
        t, "inventories")
    sold_port = {psim.ITEM_NAMES[j]: int(f.sold_units[j])
                 for j in range(9) if f.sold_units[j]}
    assert dict(cursor.sold) == sold_port, (t, "sold")
    assert cursor.overflow == sum(int(v) for v in f.discarded), (
        t, "overflow")
    for j, name in enumerate(psim.ITEM_NAMES[:9]):
        assert cursor.proj_inventory[name] == int(
            st.market.inventory[j]), (t, "inventory", name)
        assert cursor.proj_prices[name] == int(
            st.market.prices[j]), (t, "prices", name)
    # Row/event structural sanity (H1-side tracking invariants).
    assert len(cursor.rows) == i + 1
    row = cursor.rows[i]
    assert row["sold"] == dict(cursor.sold)
    assert len(row["deposited_by_actor"]) == cursor.n


def _wheat(planted_day=20, yield_units=3, **over):
    d = {"kind": "PLANT", "crop": "WHEAT", "planted_day": planted_day,
         "watered_today": False, "consecutive_unwatered": 1,
         "yield_units": yield_units, "max_lifespan_step": -1,
         "fertilized_until_day": -1}
    d.update(over)
    return d


def _tomato(planted_day=10, yield_units=3, **over):
    d = {"kind": "PLANT", "crop": "TOMATO", "planted_day": planted_day,
         "watered_today": False, "consecutive_unwatered": 1,
         "yield_units": yield_units, "max_lifespan_step": -1,
         "fertilized_until_day": -1}
    d.update(over)
    return d


def _cow(yield_units=2, fertilizer=True, **over):
    d = {"kind": "PASTURE", "animal": "COW", "placed_day": 10,
         "yield_units": yield_units, "consecutive_unfed": 0,
         "fed_today": False, "cared_today": False,
         "fertilizer_available": bool(fertilizer),
         "pending_care_bonus": 0}
    d.update(over)
    return d


def _sched(first, n_hands=0):
    tail = [_pass_action(n_hands) for _ in range(6)]
    return [first, *tail]


# ---------------------------------------------------------------- cases
def test_q1_harvest_mature_wheat(fresh_baseline, full_config):
    game = build_game({"farmer": [4, 4],
                       "tiles": [(4, 4, _wheat(yield_units=6))]})
    run_dual(fresh_baseline, full_config, game, _sched(
        {"farmer": ["HARVEST"], "hands": [], "market": []}))


def test_q1_harvest_immature_noop(fresh_baseline, full_config):
    game = build_game({"farmer": [4, 4], "tiles": [
        (4, 4, _wheat(planted_day=29, yield_units=1))]})
    run_dual(fresh_baseline, full_config, game, _sched(
        {"farmer": ["HARVEST"], "hands": [], "market": []}))


def test_q1_harvest_ongoing_keeps_tile(fresh_baseline, full_config):
    game = build_game({"farmer": [4, 4],
                       "tiles": [(4, 4, _tomato(yield_units=3))]})
    run_dual(fresh_baseline, full_config, game, _sched(
        {"farmer": ["HARVEST"], "hands": [], "market": []}))


def test_q1_harvest_animal_milk(fresh_baseline, full_config):
    game = build_game({"farmer": [4, 4],
                       "tiles": [(4, 4, _cow(yield_units=2))]})
    run_dual(fresh_baseline, full_config, game, _sched(
        {"farmer": ["HARVEST"], "hands": [], "market": []}))


def test_q1_water_bonus_window(fresh_baseline, full_config):
    game = build_game({"farmer": [4, 4], "tiles": [
        (4, 4, _wheat(planted_day=25, yield_units=2))]})
    run_dual(fresh_baseline, full_config, game, _sched(
        {"farmer": ["WATER"], "hands": [], "market": []}))


def test_q1_water_already_noop(fresh_baseline, full_config):
    game = build_game({"farmer": [4, 4], "tiles": [
        (4, 4, _wheat(planted_day=25, yield_units=2,
                      watered_today=True))]})
    run_dual(fresh_baseline, full_config, game, _sched(
        {"farmer": ["WATER"], "hands": [], "market": []}))


def test_q1_water_ongoing_no_bonus(fresh_baseline, full_config):
    game = build_game({"farmer": [4, 4],
                       "tiles": [(4, 4, _tomato(yield_units=2))]})
    run_dual(fresh_baseline, full_config, game, _sched(
        {"farmer": ["WATER"], "hands": [], "market": []}))


def test_q1_collect_flagged(fresh_baseline, full_config):
    game = build_game({"farmer": [4, 4],
                       "tiles": [(4, 4, _cow(fertilizer=True))]})
    run_dual(fresh_baseline, full_config, game, _sched(
        {"farmer": ["COLLECT_FERTILIZER"], "hands": [],
         "market": []}))


def test_q1_collect_unflagged_noop(fresh_baseline, full_config):
    game = build_game({"farmer": [4, 4],
                       "tiles": [(4, 4, _cow(fertilizer=False))]})
    run_dual(fresh_baseline, full_config, game, _sched(
        {"farmer": ["COLLECT_FERTILIZER"], "hands": [],
         "market": []}))


def test_q1_care_sets_flag(fresh_baseline, full_config):
    game = build_game({"farmer": [4, 4],
                       "tiles": [(4, 4, _cow())]})
    run_dual(fresh_baseline, full_config, game, _sched(
        {"farmer": ["CARE"], "hands": [], "market": []}))


def test_q1_drop_full_room(fresh_baseline, full_config):
    game = build_game({"farmer": [4, 4],
                       "inventories": [{"WHEAT": 4, "MILK": 2}]},
                      shed={"WOOL": 10})
    run_dual(fresh_baseline, full_config, game, _sched(
        {"farmer": ["DROP"], "hands": [], "market": []}))


def test_q1_drop_partial_overflow(fresh_baseline, full_config):
    game = build_game({"farmer": [4, 4],
                       "inventories": [{"WOOL": 2}]},
                      shed={"WHEAT": 99})
    run_dual(fresh_baseline, full_config, game, _sched(
        {"farmer": ["DROP"], "hands": [], "market": []}))


def test_q1_drop_full_shed(fresh_baseline, full_config):
    game = build_game({"farmer": [4, 4],
                       "inventories": [{"WOOL": 3}]},
                      shed={"WHEAT": 100})
    run_dual(fresh_baseline, full_config, game, _sched(
        {"farmer": ["DROP"], "hands": [], "market": []}))


def test_q1_drop_not_adjacent_noop(fresh_baseline, full_config):
    game = build_game({"farmer": [0, 0],
                       "inventories": [{"WOOL": 2}]},
                      shed={"WHEAT": 10})
    run_dual(fresh_baseline, full_config, game, _sched(
        {"farmer": ["DROP"], "hands": [], "market": []}))


def test_q1_place_partial_room(fresh_baseline, full_config):
    game = build_game({"farmer": [4, 4],
                       "inventories": [{"WOOL": 5}]},
                      shed={"WHEAT": 98})
    run_dual(fresh_baseline, full_config, game, _sched(
        {"farmer": ["PLACE", "WOOL", 5], "hands": [],
         "market": []}))


def test_q1_sell_full(fresh_baseline, full_config):
    game = build_game({"farmer": [0, 0]}, shed={"WHEAT": 10})
    run_dual(fresh_baseline, full_config, game, _sched(
        {"farmer": ["PASS"], "hands": [],
         "market": [["SELL", "WHEAT", 10]]}))


def test_q1_sell_partial_stock(fresh_baseline, full_config):
    game = build_game({"farmer": [0, 0]}, shed={"WHEAT": 4})
    run_dual(fresh_baseline, full_config, game, _sched(
        {"farmer": ["PASS"], "hands": [],
         "market": [["SELL", "WHEAT", 10]]}))


def test_q1_sell_empty_noop(fresh_baseline, full_config):
    game = build_game({"farmer": [0, 0]}, shed={})
    run_dual(fresh_baseline, full_config, game, _sched(
        {"farmer": ["PASS"], "hands": [],
         "market": [["SELL", "WHEAT", 10]]}))


def test_q1_sell_dollar_rule_no_increment(fresh_baseline,
                                          full_config):
    # FERTILIZER at inventory 10500 quotes $1 → sale adds revenue but
    # no inventory (engine $1-rule, sim.py:639-640).
    game = build_game({"farmer": [0, 0]}, shed={"FERTILIZER": 3},
                      market_inventory={"FERTILIZER": 10500})
    run_dual(fresh_baseline, full_config, game, _sched(
        {"farmer": ["PASS"], "hands": [],
         "market": [["SELL", "FERTILIZER", 3]]}))


def test_q1_buy_success_multiunit(fresh_baseline, full_config):
    game = build_game({"farmer": [0, 0]}, money=50000.0,
                      shed={"WHEAT": 90})
    run_dual(fresh_baseline, full_config, game, _sched(
        {"farmer": ["PASS"], "hands": [],
         "market": [["BUY_PRODUCT", "WHEAT", 8]]}))


def test_q1_buy_room_fail_remainder_dead(fresh_baseline,
                                         full_config):
    game = build_game({"farmer": [0, 0]}, money=50000.0,
                      shed={"WHEAT": 100})
    run_dual(fresh_baseline, full_config, game, _sched(
        {"farmer": ["PASS"], "hands": [],
         "market": [["BUY_PRODUCT", "WHEAT", 8]]}))


def test_q1_buy_money_fail_shadow_abstains(fresh_baseline,
                                           full_config):
    # Port fails the order; the shadow must fail CLOSED (H1Abstain),
    # never silently model a divergent execution.
    import pytest as _pytest
    from h1_shadow import ShadowCursor, execute_market
    from h1_telemetry import H1Abstain
    game = build_game({"farmer": [0, 0]}, money=10.0, shed={})
    obs = game.observe(0)
    cursor = ShadowCursor(fresh_baseline, 0, obs, full_config,
                          full_config, {}, "q1", [], coverage_U=8)
    with _pytest.raises(H1Abstain) as exc:
        execute_market(cursor, [["BUY_PRODUCT", "WHEAT", 8]], 712)
    assert exc.value.reason == "ABSTAIN_BUY_COVERAGE"
    # Port-side truth: order dies on money (shed unchanged).
    game.step({"farmer": ["PASS"], "hands": [],
               "market": [["BUY_PRODUCT", "WHEAT", 8]]},
              _pass_action(0))
    assert game.observe(0)["private"]["shed"]["WHEAT"] == 0


def test_q1_town_ticks_712_716(fresh_baseline, full_config):
    game = build_game({"farmer": [0, 0]}, shops=("BAKERY",
                                                 "YARN_STORE"))
    run_dual(fresh_baseline, full_config, game,
             [_pass_action(0) for _ in range(7)])


def test_q1_mixed_sell_buy_yarn716_shape(fresh_baseline,
                                         full_config):
    game = build_game({"farmer": [0, 0]}, money=50000.0,
                      shed={"WHEAT": 10})
    run_dual(fresh_baseline, full_config, game, _sched(
        {"farmer": ["PASS"], "hands": [],
         "market": [["SELL", "WHEAT", 6],
                    ["BUY_PRODUCT", "WHEAT", 32]]}))


def test_q1_multiworker_mixed(fresh_baseline, full_config):
    game = build_game(
        {"farmer": [4, 4], "hands": [(5, 5), (4, 5)],
         "tiles": [(4, 4, _wheat(yield_units=4)),
                   (5, 5, _cow(yield_units=2, fertilizer=True))],
         "inventories": [{}, {}, {"WOOL": 3}]})
    run_dual(fresh_baseline, full_config, game, _sched(
        {"farmer": ["HARVEST"],
         "hands": [["COLLECT_FERTILIZER"], ["DROP"]],
         "market": []}, n_hands=2))


def test_q1_rot_to_weed(fresh_baseline, full_config):
    # Expired ongoing tomato (mls past, even steps) rots −1/step and
    # becomes WEED at 0 — identically in both sims.
    game = build_game({"farmer": [0, 0], "tiles": [
        (3, 3, _tomato(yield_units=2, max_lifespan_step=700))]})
    run_dual(fresh_baseline, full_config, game,
             [_pass_action(0) for _ in range(7)])
    assert game.observe(0)["farms"][0]["tiles"][3][3] == {
        "kind": "WEED"}


def test_q1_moves_and_pass(fresh_baseline, full_config):
    game = build_game({"farmer": [1, 1], "hands": [(8, 8)]})
    sched = [
        {"farmer": ["EAST"], "hands": [["NORTH"]], "market": []},
        {"farmer": ["SOUTH"], "hands": [["WEST"]], "market": []},
        _pass_action(1), _pass_action(1), _pass_action(1),
        _pass_action(1), _pass_action(1)]
    run_dual(fresh_baseline, full_config, game, sched)


def test_q1_sell_at_718_terminal(fresh_baseline, full_config):
    game = build_game({"farmer": [0, 0]},
                      shed={"WHEAT": 7, "MILK": 3})
    sched = [_pass_action(0) for _ in range(6)] + [
        {"farmer": ["PASS"], "hands": [],
         "market": [["SELL", "WHEAT", 7], ["SELL", "MILK", 3]]}]
    run_dual(fresh_baseline, full_config, game, sched)
