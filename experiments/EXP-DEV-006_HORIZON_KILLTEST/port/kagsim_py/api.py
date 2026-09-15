# SPDX-License-Identifier: MIT
"""Python-bindings layer port of python/kagsim.cpp (Game/Stream/run_episode).

Action conversion, observation schema, and episode loops mirror the C++ exactly.
"""
from .sim import (
    SimFull, Config, Tile,
    WHEAT, CARROT, TOMATO, STRAWBERRY, MELON, EGG, MILK, WOOL, FERTILIZER,
    GOOSE, COW, SHEEP, N_ITEMS, N_PRODUCTS, N_CROPS,
    OP_PASS, OP_NORTH, OP_SOUTH, OP_EAST, OP_WEST, OP_PICKUP, OP_DROP, OP_PLACE,
    OP_PLANT, OP_WATER, OP_HARVEST, OP_FERTILIZE, OP_DIG, OP_BUILD_COOP,
    OP_BUILD_PASTURE, OP_FEED, OP_COLLECT_FERTILIZER, OP_CARE, OP_INVALID,
    M_NONE, M_HIRE, M_BUY_LAND, M_BUY_SEED, M_BUY_PRODUCT, M_BUY_ANIMAL, M_SELL,
    T_EMPTY, T_LOCKED, T_WEED, T_COOP, T_PASTURE, T_PLANT,
    MAX_UNITS, MAX_SHOP_INSTANCES, N_SHOPS,
    ITEM_NAMES, SHOP_NAMES, QUAD_NAMES,
)

__version__ = "0.4.0.port1"
ENGINE_VERSION = "1.32.7"

OPI = {"PASS": 0, "NORTH": 1, "SOUTH": 2, "EAST": 3, "WEST": 4, "PICKUP": 5,
       "DROP": 6, "PLACE": 7, "PLANT": 8, "WATER": 9, "HARVEST": 10,
       "FERTILIZE": 11, "DIG": 12, "BUILD_COOP": 13, "BUILD_PASTURE": 14,
       "FEED": 15, "COLLECT_FERTILIZER": 16, "CARE": 17}
ITI = {"WHEAT": 0, "CARROT": 1, "TOMATO": 2, "STRAWBERRY": 3, "MELON": 4,
       "EGG": 5, "MILK": 6, "WOOL": 7, "FERTILIZER": 8, "GOOSE": 9, "COW": 10,
       "SHEEP": 11}
MOPI = {"HIRE": 1, "BUY_LAND": 2, "BUY_SEED": 3, "BUY_PRODUCT": 4,
        "BUY_ANIMAL": 5, "SELL": 6}


def _to_int16(v):
    try:
        n = int(v)
    except (TypeError, ValueError):
        return 1
    n = n & 0xFFFF
    return n - 0x10000 if n >= 0x8000 else n


def conv_unit(h):
    op, arg, n = OP_PASS, 0, 1
    if not isinstance(h, list):
        return (op, arg, n)
    v = h
    if len(v) == 0:
        return (op, arg, n)
    op = OPI.get(v[0], OP_INVALID) if isinstance(v[0], str) else OP_INVALID
    # NOTE: C++ does py::str(v[0]) cast which stringifies non-strings; agents
    # always send strings here. Non-string op falls back to INVALID (no-op).
    if len(v) >= 2 and isinstance(v[1], str):
        arg = ITI.get(v[1], 255)
    if len(v) >= 3:
        n = _to_int16(v[2])
    return (op, arg, n)


def conv_order(h):
    op, item, n = M_NONE, 0, 0
    if not isinstance(h, list):
        return (op, item, n)
    v = h
    if len(v) == 0:
        return (op, item, n)
    if not isinstance(v[0], str) or v[0] not in MOPI:
        return (op, item, n)
    code = MOPI[v[0]]
    if code == 1 or code == 2:
        return (code, 0, 1)
    if len(v) < 3:
        return (op, item, n)
    op = code
    item = ITI.get(v[1], 255) if isinstance(v[1], str) else 255
    try:
        n = int(v[2]) & 0xFFFFFFFF
        if n >= 0x80000000:
            n -= 0x100000000
    except (TypeError, ValueError):
        n = 0
        op = 0
    return (op, item, n)


def _empty_action():
    return {"units": [(OP_PASS, 0, 1)] * MAX_UNITS, "n_units": 1,
            "orders": [(M_NONE, 0, 0)] * 16, "n_orders": 0}


def conv_action(t):
    units = [(OP_PASS, 0, 1)] * MAX_UNITS
    orders = [(M_NONE, 0, 0)] * 16
    n_units = 1
    n_orders = 0
    if isinstance(t, dict):
        if "farmer" in t:
            units[0] = conv_unit(t["farmer"])
        nu = 1
        if "hands" in t:
            for hh in t["hands"]:
                if nu >= MAX_UNITS:
                    break
                units[nu] = conv_unit(hh)
                nu += 1
        n_units = nu
        if "market" in t:
            for oo in t["market"]:
                if n_orders >= 16:
                    break
                o = conv_order(oo)
                if o[0] != 0:
                    orders[n_orders] = o
                    n_orders += 1
    return {"units": units, "n_units": n_units, "orders": orders, "n_orders": n_orders}


def ser_tile(t):
    if t.kind == T_EMPTY:
        return None
    if t.kind == T_LOCKED:
        return "LOCKED"
    if t.kind == T_WEED:
        return {"kind": "WEED"}
    if t.kind == T_PLANT:
        return {"kind": "PLANT", "crop": ITEM_NAMES[t.what],
                "planted_day": int(t.planted_day),
                "watered_today": bool(t.watered_today),
                "consecutive_unwatered": int(t.consecutive_dry),
                "yield_units": int(t.yield_units),
                "max_lifespan_step": int(t.max_lifespan_step),
                "fertilized_until_day": int(t.fertilized_until_day)}
    if t.kind == T_COOP or t.kind == T_PASTURE:
        d = {"kind": "COOP" if t.kind == T_COOP else "PASTURE"}
        if t.has_animal:
            d["animal"] = ITEM_NAMES[t.what]
            d["placed_day"] = int(t.planted_day)
            d["yield_units"] = int(t.yield_units)
            d["consecutive_unfed"] = int(t.consecutive_dry)
            d["fed_today"] = bool(t.fed_today)
            d["cared_today"] = bool(t.cared_today)
            d["fertilizer_available"] = bool(t.fertilizer_available)
            d["pending_care_bonus"] = int(t.pending_care_bonus)
        return d
    return None


def ser_farm(f, bs):
    tiles = []
    for y in range(bs):
        row = []
        for x in range(bs):
            row.append(ser_tile(f.tiles[y][x]))
        tiles.append(row)
    return {"money": float(f.money), "tiles": tiles,
            "farmer": [int(f.pos_x[0]), int(f.pos_y[0])],
            "hands": [[int(f.pos_x[u]), int(f.pos_y[u])] for u in range(1, f.n_units)],
            "unlocked_quadrants": [QUAD_NAMES[q] for q in range(f.n_quadrants)],
            "hires_today": int(f.hires_today)}


def apply_forced_shops(cfg, shops):
    if shops is None:
        return
    items = list(shops)
    if len(items) > MAX_SHOP_INSTANCES:
        raise ValueError("at most 8 shops can be pinned")
    n = 0
    for h in items:
        idx = -1
        if isinstance(h, str):
            for i in range(N_SHOPS):
                if h == SHOP_NAMES[i]:
                    idx = i
                    break
            if idx < 0:
                raise ValueError("unknown shop name: " + h)
        else:
            idx = int(h)
            if idx < 0 or idx >= N_SHOPS:
                raise ValueError("shop index out of range")
        cfg.forced_shops[n] = idx
        n += 1
    cfg.n_forced_shops = n


class Stream:
    def __init__(self, acts):
        self.turns = [conv_action(t) for t in acts]

    def __len__(self):
        return len(self.turns)


class Game:
    def __init__(self, seed, steps=720, shops=None):
        cfg = Config()
        cfg.seed = seed
        cfg.episode_steps = steps
        apply_forced_shops(cfg, shops)
        self.sim = SimFull(cfg)

    def observe(self, player):
        st = self.sim.st
        cfg = self.sim.cfg
        farms = [ser_farm(st.farms[0], cfg.board_size),
                 ser_farm(st.farms[1], cfg.board_size)]
        inv = {}
        prices = {}
        for i in range(N_PRODUCTS):
            inv[ITEM_NAMES[i]] = int(st.market.inventory[i])
            prices[ITEM_NAMES[i]] = int(st.market.prices[i])
        shops = [SHOP_NAMES[st.shops[i]] for i in range(st.n_shops)]
        f = st.farms[player]
        shed = {}
        for i in range(N_ITEMS):
            shed[ITEM_NAMES[i]] = int(f.shed[i])
        seeds = {}
        for i in range(N_CROPS):
            seeds[ITEM_NAMES[i]] = int(f.seeds[i])
        invs = []
        for u in range(f.n_units):
            iu = {}
            for item, qty in f.inv[u].items():
                iu[ITEM_NAMES[item]] = int(qty)
            invs.append(iu)
        return {"remainingOverageTime": 60, "step": int(st.step),
                "player": int(player), "farms": farms,
                "market": {"inventory": inv, "prices": prices},
                "town": {"unlocked_shops": shops},
                "day": int(st.day), "hour": int(st.hour),
                "private": {"shed": shed, "seeds": seeds, "inventories": invs}}

    def step(self, a, b):
        self.sim.step(conv_action(a), conv_action(b))

    @property
    def done(self):
        return self.sim.st.done

    def reward(self, p):
        return float(self.sim.reward(p))

    @property
    def step_count(self):
        return self.sim.st.step

    def telemetry(self, player):
        f = self.sim.st.farms[player]
        disc = sum(f.discarded)
        sold = sum(f.sold_units)
        return {"sell_dead_units": int(f.tel_sell_dead),
                "refused_buy_product": int(f.tel_refused_product),
                "refused_buy_seed": int(f.tel_refused_seed),
                "refused_buy_animal": int(f.tel_refused_animal),
                "refused_hire": int(f.tel_refused_hire),
                "refused_buy_land": int(f.tel_refused_land),
                "hire_paid": int(f.tel_hire_paid),
                "sell_revenue": float(f.sell_revenue),
                "total_spend": float(f.total_spend),
                "shed_discarded_units": int(disc),
                "sold_units": int(sold)}


def _run_episode_raw(sa, sb, seed, steps, shops=None):
    cfg = Config()
    cfg.seed = seed
    cfg.episode_steps = steps
    apply_forced_shops(cfg, shops)
    sim = SimFull(cfg)
    empty = _empty_action()
    t = 0
    while not sim.st.done:
        a = sa.turns[t] if t < len(sa.turns) else empty
        b = sb.turns[t] if t < len(sb.turns) else empty
        sim.step(a, b)
        t += 1
    return (float(sim.reward(0)), float(sim.reward(1)))


def run_episode(stream_a, stream_b, seed, steps=720, shops=None):
    probe = Config()
    apply_forced_shops(probe, shops)
    cfg = Config()
    cfg.seed = seed
    cfg.episode_steps = steps
    cfg.forced_shops = list(probe.forced_shops)
    cfg.n_forced_shops = probe.n_forced_shops
    sim = SimFull(cfg)
    empty = _empty_action()
    t = 0
    while not sim.st.done:
        a = stream_a.turns[t] if t < len(stream_a.turns) else empty
        b = stream_b.turns[t] if t < len(stream_b.turns) else empty
        sim.step(a, b)
        t += 1
        if t > steps + 8:
            break
    return (float(sim.reward(0)), float(sim.reward(1)))


def run_many(jobs, steps=720, threads=0):
    out = []
    for (a, b, seed) in jobs:
        out.append(_run_episode_raw(a, b, seed, steps))
    return out
