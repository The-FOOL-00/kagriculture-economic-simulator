# SPDX-License-Identifier: MIT
"""Bit-exact pure-Python port of sim/sim.hpp (Kaggriculture engine 1.32.7).

Scope: exactly the semantics consumed by Game/Stream/run_episode/run_many.
Op order, integer widths, RNG call order, and observation schema mirror the C++.
Validated by golden-trace replay + frozen DEV-005 replay (see port/validate_*.py).
"""
import math
from .mt import PyRandom

# ---------------------------------------------------------------- item space
WHEAT, CARROT, TOMATO, STRAWBERRY, MELON, EGG, MILK, WOOL, FERTILIZER = range(9)
GOOSE, COW, SHEEP = 9, 10, 11
N_ITEMS = 12
N_PRODUCTS = 9
N_CROPS = 5
N_ANIMALS = 3

ITEM_NAMES = ["WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON", "EGG", "MILK",
              "WOOL", "FERTILIZER", "GOOSE", "COW", "SHEEP"]

# ---------------------------------------------------------------- unit ops
(OP_PASS, OP_NORTH, OP_SOUTH, OP_EAST, OP_WEST, OP_PICKUP, OP_DROP, OP_PLACE,
 OP_PLANT, OP_WATER, OP_HARVEST, OP_FERTILIZE, OP_DIG, OP_BUILD_COOP,
 OP_BUILD_PASTURE, OP_FEED, OP_COLLECT_FERTILIZER, OP_CARE, OP_INVALID) = range(19)

(M_NONE, M_HIRE, M_BUY_LAND, M_BUY_SEED, M_BUY_PRODUCT, M_BUY_ANIMAL,
 M_SELL) = range(7)

# ---------------------------------------------------------------- static data
# CropDef: seed, first_yield_day, max_yield_day, interval, max_yield, ongoing
CROPS = [
    (10, 2, 4, 0, 6, False),   # WHEAT
    (20, 2, 3, 0, 4, False),   # CARROT
    (50, 8, 8, 1, 4, True),    # TOMATO
    (100, 10, 10, 2, 4, True),  # STRAWBERRY
    (80, 10, 12, 0, 6, False),  # MELON
]

ST_COOP, ST_PASTURE = 0, 1
# AnimalDef: cost, structure, first_yield_day, interval, max_held, product
ANIMALS = [
    (300, ST_COOP, 4, 1, 4, EGG),    # GOOSE
    (400, ST_PASTURE, 8, 2, 6, MILK),  # COW
    (500, ST_PASTURE, 6, 3, 6, WOOL),  # SHEEP
]

(F_LINEAR, F_SQ, F_SQRT, F_LOG, F_LOG10, F_HINGE) = range(6)
# MarketDef: base, I0, T, below_f, below_t, above_f, above_t
MARKET = [
    (25, 10000, 400, F_SQRT, 0.80, F_LOG, 0.20),    # WHEAT
    (35, 10000, 450, F_HINGE, 1.00, F_SQRT, 0.70),  # CARROT
    (60, 10000, 200, F_HINGE, 0.40, F_SQRT, 0.60),  # TOMATO
    (120, 10000, 100, F_SQRT, 0.70, F_LINEAR, 1.60),  # STRAWBERRY
    (250, 10000, 300, F_LOG, 0.20, F_SQ, 3.60),     # MELON
    (50, 10000, 332, F_HINGE, 0.40, F_LOG, 0.20),   # EGG
    (160, 10000, 122, F_SQRT, 0.60, F_LINEAR, 1.60),  # MILK
    (200, 10000, 105, F_LOG, 0.20, F_SQ, 3.20),     # WOOL
    (100, 10000, 200, F_LINEAR, 0.40, F_LINEAR, 0.40),  # FERTILIZER
]


def shape(f, x, T=0.0):
    if x < 0.0:
        x = 0.0
    if f == F_LINEAR:
        return x
    if f == F_SQ:
        return x * x
    if f == F_SQRT:
        return math.sqrt(x)
    if f == F_LOG:
        return math.log(1.0 + x)
    if f == F_LOG10:
        return math.log10(1.0 + x)
    if f == F_HINGE:
        if T <= 0.0:
            return x
        u = x / T
        e = u - 1.0
        if e < 0.0:
            e = 0.0
        return u + 8.0 * e * e
    return x


def _market_amps():
    amps = []
    for i in range(N_PRODUCTS):
        base, I0, T, below_f, below_t, above_f, above_t = MARKET[i]
        below = below_t * base / shape(below_f, float(T), float(T))
        above = above_t * base / shape(above_f, float(T), float(T))
        amps.append((below, above))
    return amps


_AMPS = _market_amps()


def market_price(item, inv):
    base, I0, T, below_f, below_t, above_f, above_t = MARKET[item]
    below_a, above_a = _AMPS[item]
    if inv < I0:
        price = base + below_a * shape(below_f, float(I0 - inv), float(T))
    else:
        price = base - above_a * shape(above_f, float(inv - I0), float(T))
    v = round(price)  # round-half-even == nearbyint default mode
    return v if v >= 1 else 1


# ---------------------------------------------------------------- shops / town
(SHOP_BAKERY, SHOP_BRUNCH_SPOT, SHOP_FARMERS_MARKET, SHOP_ICE_CREAM_SHOP,
 SHOP_PET_CAFE, SHOP_PIZZA_SHOP, SHOP_SMOOTHIE_SHOP, SHOP_YARN_STORE,
 N_SHOPS) = range(9)
SHOP_NAMES = ["BAKERY", "BRUNCH_SPOT", "FARMERS_MARKET", "ICE_CREAM_SHOP",
              "PET_CAFE", "PIZZA_SHOP", "SMOOTHIE_SHOP", "YARN_STORE"]
SHOP_MASK = [
    (1 << EGG) | (1 << WHEAT),
    (1 << EGG) | (1 << WHEAT) | (1 << STRAWBERRY),
    (1 << WHEAT) | (1 << CARROT) | (1 << TOMATO) | (1 << STRAWBERRY),
    (1 << STRAWBERRY) | (1 << MILK) | (1 << WHEAT),
    (1 << CARROT),
    (1 << MILK) | (1 << TOMATO) | (1 << WHEAT),
    (1 << STRAWBERRY) | (1 << MILK),
    (1 << WOOL),
]
SHOP_MULT = [1, 1, 1, 1, 2, 1, 1, 2]
MAX_SHOP_INSTANCES = 8
QUAD_NAMES = ["NW", "NE", "SW", "SE"]

# ---------------------------------------------------------------- config/state
(T_EMPTY, T_LOCKED, T_WEED, T_COOP, T_PASTURE, T_PLANT) = range(6)
MAX_UNITS = 40
BOARD = 10


class Config:
    def __init__(self, seed=0, episode_steps=720, board_size=10, starting_money=3000,
                 max_orders=10, turns_per_day=24, shed_capacity=100, weed_chance=0.005,
                 shop_unlock_interval=3, shop_sell_interval=4, center_sell_interval=24,
                 hire_mult=1):
        self.seed = seed
        self.episode_steps = episode_steps
        self.board_size = board_size
        self.starting_money = starting_money
        self.max_orders = max_orders
        self.turns_per_day = turns_per_day
        self.shed_capacity = shed_capacity
        self.weed_chance = weed_chance
        self.shop_unlock_interval = shop_unlock_interval
        self.shop_sell_interval = shop_sell_interval
        self.center_sell_interval = center_sell_interval
        self.hire_mult = hire_mult
        self.forced_shops = [0] * MAX_SHOP_INSTANCES
        self.n_forced_shops = 0


class Tile:
    __slots__ = ("kind", "what", "has_animal", "watered_today", "fed_today",
                 "cared_today", "fertilizer_available", "consecutive_dry",
                 "yield_units", "pending_care_bonus", "planted_day",
                 "max_lifespan_step", "fertilized_until_day")

    def __init__(self):
        self.kind = T_EMPTY
        self.what = 0
        self.has_animal = False
        self.watered_today = False
        self.fed_today = False
        self.cared_today = False
        self.fertilizer_available = False
        self.consecutive_dry = 0
        self.yield_units = 0
        self.pending_care_bonus = 0
        self.planted_day = 0
        self.max_lifespan_step = -1
        self.fertilized_until_day = -1


class Farm:
    __slots__ = ("money", "tiles", "pos_x", "pos_y", "n_units", "n_quadrants",
                 "hires_today", "shed", "shed_total", "seeds", "inv",
                 "discarded", "produced", "sold_units", "sell_revenue",
                 "total_spend", "tel_sell_dead", "tel_refused_product",
                 "tel_refused_seed", "tel_refused_animal", "tel_refused_hire",
                 "tel_refused_land", "tel_hire_paid")

    def __init__(self, bs):
        self.money = 0.0
        self.tiles = [[Tile() for _ in range(bs)] for _ in range(bs)]
        self.pos_x = [0] * MAX_UNITS
        self.pos_y = [0] * MAX_UNITS
        self.n_units = 1
        self.n_quadrants = 1
        self.hires_today = 0
        self.shed = [0] * N_ITEMS
        self.shed_total = 0
        self.seeds = [0] * N_CROPS
        # Per-unit inventories: plain dicts (insertion-ordered like the C++
        # inv_keys model; inv_add/inv_erase/inv_take replicate its semantics).
        self.inv = [dict() for _ in range(MAX_UNITS)]
        self.discarded = [0] * N_ITEMS
        self.produced = [0] * N_ITEMS
        self.sold_units = [0] * N_ITEMS
        self.sell_revenue = 0.0
        self.total_spend = 0.0
        self.tel_sell_dead = 0
        self.tel_refused_product = 0
        self.tel_refused_seed = 0
        self.tel_refused_animal = 0
        self.tel_refused_hire = 0
        self.tel_refused_land = 0
        self.tel_hire_paid = 0

    def inv_add(self, u, item, n):
        if n <= 0:
            return
        d = self.inv[u]
        d[item] = d.get(item, 0) + n

    def inv_erase(self, u, item):
        d = self.inv[u]
        if item in d:
            del d[item]

    def inv_take(self, u, item, n):
        d = self.inv[u]
        if d.get(item, 0) < n:
            return False
        v = d[item] - n
        if v == 0:
            del d[item]
        else:
            d[item] = v
        return True

    def inv_clear(self, u):
        self.inv[u] = dict()


class Market:
    __slots__ = ("inventory", "prices")

    def __init__(self):
        self.inventory = [0] * N_PRODUCTS
        self.prices = [0] * N_PRODUCTS


class State:
    __slots__ = ("farms", "market", "shops", "n_shops", "step", "day", "hour", "done")

    def __init__(self, bs):
        self.farms = [Farm(bs), Farm(bs)]
        self.market = Market()
        self.shops = [0] * MAX_SHOP_INSTANCES
        self.n_shops = 0
        self.step = 0
        self.day = 0
        self.hour = 0
        self.done = False


def quadrant_of(x, y, bs):
    half = bs // 2
    return (0 if y < half else 2) + (0 if x < half else 1)


LAND_ORDER = [1, 2, 3]
LAND_PRICES = [1000, 2000, 4000]


def shed_access_tiles(bs):
    h = bs // 2
    return [(h - 1, h - 1), (h, h - 1), (h - 1, h), (h, h)]


def is_shed_adjacent(x, y, bs):
    h = bs // 2
    return (x == h - 1 or x == h) and (y == h - 1 or y == h)


def fib(n):
    a, b = 1, 1
    for _ in range(n):
        t = b
        b = a + b
        a = t
    return a


class Sim:
    def __init__(self, cfg=None):
        self.cfg = cfg if cfg is not None else Config()
        self.st = None
        self.reset()

    def reset(self):
        cfg = self.cfg
        bs = cfg.board_size
        st = State(bs)
        h = bs // 2
        for p in range(2):
            f = st.farms[p]
            f.money = float(cfg.starting_money)
            for y in range(bs):
                for x in range(bs):
                    f.tiles[y][x].kind = T_EMPTY if quadrant_of(x, y, bs) == 0 else T_LOCKED
            f.n_units = 1
            f.pos_x[0] = h - 1
            f.pos_y[0] = h - 1
        for i in range(N_PRODUCTS):
            st.market.inventory[i] = MARKET[i][1]
            st.market.prices[i] = int(MARKET[i][0])
        self.st = st

    def reward(self, p):
        return self.st.farms[p].money

    def step(self, a0, a1):
        if self.st.done:
            return
        acts = (a0, a1)
        step_i = self.st.step
        day = step_i // self.cfg.turns_per_day
        for p in range(2):
            self.apply_unit_actions(p, acts[p], day)
        self.process_market(acts[0], acts[1])
        self.town_consume(step_i)
        for p in range(2):
            self.decay_plants(self.st.farms[p], step_i)
        if (step_i + 1) % self.cfg.turns_per_day == 0:
            self.end_of_day(day)
        self.st.step = step_i + 1
        self.st.day = self.st.step // self.cfg.turns_per_day
        self.st.hour = self.st.step % self.cfg.turns_per_day
        if step_i >= self.cfg.episode_steps - 2:
            self.st.done = True

    # ------------------------------------------------------------ unit actions
    def apply_unit_actions(self, p, a, day):
        f = self.st.farms[p]
        demand = [0] * N_CROPS
        for i in range(a["n_units"]):
            u = a["units"][i]
            if u[0] == OP_PLANT and u[1] < N_CROPS:
                demand[u[1]] += 1
        n = a["n_units"] if a["n_units"] < f.n_units else f.n_units
        blocked = [demand[c] > f.seeds[c] for c in range(N_CROPS)]
        for i in range(n):
            u = a["units"][i]
            if u[0] == OP_PLANT and u[1] < N_CROPS and blocked[u[1]]:
                continue
            self.apply_unit(f, i, u, day)

    def apply_unit(self, f, idx, u, day):
        bs = self.cfg.board_size
        fx = f.pos_x[idx]
        fy = f.pos_y[idx]
        inv = f.inv[idx]
        op, arg, nn = u[0], u[1], u[2]

        if op == OP_PASS:
            return
        if op in (OP_NORTH, OP_SOUTH, OP_EAST, OP_WEST):
            nx = fx + (1 if op == OP_EAST else 0) - (1 if op == OP_WEST else 0)
            ny = fy + (1 if op == OP_SOUTH else 0) - (1 if op == OP_NORTH else 0)
            if nx < 0 or nx >= bs or ny < 0 or ny >= bs:
                return
            f.pos_x[idx] = nx
            f.pos_y[idx] = ny
            return

        tile = f.tiles[fy][fx]

        if op == OP_DROP:
            if not is_shed_adjacent(fx, fy, bs):
                return
            keys = list(inv.keys())
            for it in keys:
                if inv.get(it, 0) <= 0:
                    f.inv_erase(idx, it)
                    continue
                room = cfg_shed_room(self.cfg.shed_capacity, f.shed_total)
                take = inv[it] if inv[it] < room else room
                if take > 0:
                    f.shed[it] += take
                    f.shed_total += take
                f.discarded[it] += inv[it] - take
                f.inv_erase(idx, it)
            return
        if op == OP_PICKUP:
            if not is_shed_adjacent(fx, fy, bs):
                return
            if nn <= 0 or arg >= N_ITEMS:
                return
            take = nn if nn < f.shed[arg] else f.shed[arg]
            if take <= 0:
                return
            f.shed[arg] -= take
            f.shed_total -= take
            f.inv_add(idx, arg, take)
            return
        if op == OP_PLACE:
            if arg >= N_ITEMS:
                return
            if GOOSE <= arg < N_ITEMS:
                ad = ANIMALS[arg - GOOSE]
                want = T_COOP if ad[1] == ST_COOP else T_PASTURE
                if tile.kind == want and not tile.has_animal:
                    if f.inv_take(idx, arg, 1):
                        t = Tile()
                        t.kind = want
                        t.what = arg
                        t.has_animal = True
                        t.planted_day = day
                        f.tiles[fy][fx] = t
                    return
            if is_shed_adjacent(fx, fy, bs):
                n = nn if nn < inv.get(arg, 0) else inv.get(arg, 0)
                if n <= 0:
                    return
                n = min(n, cfg_shed_room(self.cfg.shed_capacity, f.shed_total))
                if n <= 0:
                    return
                f.inv_take(idx, arg, n)
                f.shed[arg] += n
                f.shed_total += n
            return

        if tile.kind == T_LOCKED:
            return

        if op == OP_PLANT:
            if arg >= N_CROPS or tile.kind != T_EMPTY or f.seeds[arg] <= 0:
                return
            f.seeds[arg] -= 1
            cd = CROPS[arg]
            t = Tile()
            t.kind = T_PLANT
            t.what = arg
            t.planted_day = day
            t.consecutive_dry = 1
            t.yield_units = 0 if cd[5] else 1
            t.max_lifespan_step = -1 if cd[5] else (day + cd[2] + 1) * self.cfg.turns_per_day
            f.tiles[fy][fx] = t
            return
        if op == OP_WATER:
            if tile.kind != T_PLANT or tile.watered_today:
                return
            tile.watered_today = True
            cd = CROPS[tile.what]
            if not cd[5]:
                age = day - tile.planted_day
                w0 = (cd[2] + 1) // 2
                if w0 <= age <= cd[2]:
                    bonus = 2 if tile.fertilized_until_day >= day else 1
                    tile.yield_units = min(cd[4], tile.yield_units + bonus)
            return
        if op == OP_HARVEST:
            if tile.kind == T_EMPTY or tile.kind == T_WEED:
                return
            if tile.yield_units <= 0:
                return
            if tile.kind == T_PLANT:
                cd = CROPS[tile.what]
                if day - tile.planted_day < cd[1]:
                    return
                f.inv_add(idx, tile.what, tile.yield_units)
                f.produced[tile.what] += tile.yield_units
                tile.yield_units = 0
                if not cd[5]:
                    e = Tile()
                    e.kind = T_EMPTY
                    f.tiles[fy][fx] = e
            elif tile.has_animal:
                prod = ANIMALS[tile.what - GOOSE][5]
                f.inv_add(idx, prod, tile.yield_units)
                f.produced[prod] += tile.yield_units
                tile.yield_units = 0
            return
        if op == OP_FERTILIZE:
            if tile.kind != T_PLANT:
                return
            if not f.inv_take(idx, FERTILIZER, 1):
                return
            if tile.fertilized_until_day < day + 2:
                tile.fertilized_until_day = day + 2
            return
        if op == OP_DIG:
            if tile.kind == T_EMPTY:
                return
            if tile.has_animal:
                return
            e = Tile()
            e.kind = T_EMPTY
            f.tiles[fy][fx] = e
            return
        if op == OP_BUILD_COOP:
            if tile.kind != T_EMPTY:
                return
            t = Tile()
            t.kind = T_COOP
            f.tiles[fy][fx] = t
            return
        if op == OP_BUILD_PASTURE:
            if tile.kind != T_EMPTY:
                return
            t = Tile()
            t.kind = T_PASTURE
            f.tiles[fy][fx] = t
            return
        if op == OP_FEED:
            if not tile.has_animal or tile.fed_today:
                return
            if not f.inv_take(idx, WHEAT, 1):
                return
            tile.fed_today = True
            return
        if op == OP_COLLECT_FERTILIZER:
            if not tile.has_animal or not tile.fertilizer_available:
                return
            tile.fertilizer_available = False
            f.inv_add(idx, FERTILIZER, 1)
            f.produced[FERTILIZER] += 1
            return
        if op == OP_CARE:
            if not tile.has_animal or tile.cared_today:
                return
            tile.cared_today = True
            return
        return


def cfg_shed_room(cap, total):
    room = cap - total
    return room if room > 0 else 0


class _SimMarket:
    """Market/town/day phases, mixed into Sim below (kept separate for review)."""

    def process_market(self, a0, a1):
        acts = (a0, a1)
        nq = [0, 0]
        for p in range(2):
            nq[p] = acts[p]["n_orders"] if acts[p]["n_orders"] < self.cfg.max_orders else self.cfg.max_orders
        max_len = nq[0] if nq[0] > nq[1] else nq[1]
        for i in range(max_len):
            ostype = [0, 0]
            ositem = [0, 0]
            osrem = [0, 0]
            oslive = [False, False]
            for p in range(2):
                if i < nq[p]:
                    o = acts[p]["orders"][i]
                    if o[0] == M_HIRE or o[0] == M_BUY_LAND:
                        ostype[p] = o[0]
                        oslive[p] = True
                        osrem[p] = 1
                    elif o[0] != M_NONE and o[2] > 0:
                        ostype[p] = o[0]
                        ositem[p] = o[1]
                        osrem[p] = o[2]
                        oslive[p] = True
            for p in range(2):
                if not oslive[p]:
                    continue
                if ostype[p] == M_HIRE:
                    self.do_hire(self.st.farms[p])
                    oslive[p] = False
                elif ostype[p] == M_BUY_LAND:
                    self.do_buy_land(self.st.farms[p])
                    oslive[p] = False
            while True:
                qok = [False, False]
                qtype = [0, 0]
                qitem = [0, 0]
                qprice = [0, 0]
                for p in range(2):
                    if not oslive[p] or osrem[p] <= 0:
                        continue
                    t = ostype[p]
                    it = ositem[p]
                    if t == M_SELL and it < N_PRODUCTS:
                        qok[p] = True
                        qtype[p] = t
                        qitem[p] = it
                        qprice[p] = market_price(it, self.st.market.inventory[it])
                    elif t == M_BUY_PRODUCT and (it == WHEAT or it == FERTILIZER):
                        qok[p] = True
                        qtype[p] = t
                        qitem[p] = it
                        qprice[p] = market_price(it, self.st.market.inventory[it] - 1)
                    elif t == M_BUY_SEED and it < N_CROPS:
                        qok[p] = True
                        qtype[p] = t
                        qitem[p] = it
                        qprice[p] = CROPS[it][0]
                    elif t == M_BUY_ANIMAL and GOOSE <= it < N_ITEMS:
                        qok[p] = True
                        qtype[p] = t
                        qitem[p] = it
                        qprice[p] = ANIMALS[it - GOOSE][0]
                    else:
                        oslive[p] = False
                if not qok[0] and not qok[1]:
                    break
                committed = False
                for p in range(2):
                    if not qok[p]:
                        continue
                    if self.commit_unit(qtype[p], qitem[p], qprice[p], self.st.farms[p]):
                        osrem[p] -= 1
                        committed = True
                    else:
                        fp = self.st.farms[p]
                        if ostype[p] == M_SELL:
                            fp.tel_sell_dead += osrem[p]
                        elif ostype[p] == M_BUY_PRODUCT:
                            fp.tel_refused_product += osrem[p]
                        elif ostype[p] == M_BUY_SEED:
                            fp.tel_refused_seed += osrem[p]
                        elif ostype[p] == M_BUY_ANIMAL:
                            fp.tel_refused_animal += osrem[p]
                        oslive[p] = False
                if not committed:
                    break
            self.refresh_prices()

    def commit_unit(self, op, item, price, f):
        if op == M_SELL:
            if f.shed[item] <= 0:
                return False
            f.shed[item] -= 1
            f.shed_total -= 1
            f.money += price
            f.sold_units[item] += 1
            f.sell_revenue += price
            if price > 1:
                self.st.market.inventory[item] += 1
            return True
        if op == M_BUY_PRODUCT:
            if f.money < price:
                return False
            if f.shed_total >= self.cfg.shed_capacity:
                return False
            f.money -= price
            f.total_spend += price
            f.shed[item] += 1
            f.shed_total += 1
            self.st.market.inventory[item] -= 1
            return True
        if op == M_BUY_SEED:
            if f.money < price:
                return False
            f.money -= price
            f.total_spend += price
            f.seeds[item] += 1
            return True
        if op == M_BUY_ANIMAL:
            if f.money < price:
                return False
            if f.shed_total >= self.cfg.shed_capacity:
                return False
            f.money -= price
            f.total_spend += price
            f.shed[item] += 1
            f.shed_total += 1
            return True
        return False

    def refresh_prices(self):
        for i in range(N_PRODUCTS):
            self.st.market.prices[i] = market_price(i, self.st.market.inventory[i])

    def do_hire(self, f):
        cost = self.cfg.hire_mult * fib(f.hires_today)
        if f.money < cost or f.n_units >= MAX_UNITS:
            f.tel_refused_hire += 1
            return
        f.money -= cost
        f.total_spend += cost
        f.tel_hire_paid += cost
        f.hires_today += 1
        acc = shed_access_tiles(self.cfg.board_size)
        occ = [0, 0, 0, 0]
        for u in range(f.n_units):
            for k in range(4):
                if f.pos_x[u] == acc[k][0] and f.pos_y[u] == acc[k][1]:
                    occ[k] += 1
        best = 0
        for k in range(1, 4):
            if occ[k] < occ[best]:
                best = k
        idx = f.n_units
        f.n_units += 1
        f.pos_x[idx] = acc[best][0]
        f.pos_y[idx] = acc[best][1]
        f.inv_clear(idx)

    def do_buy_land(self, f):
        extra = f.n_quadrants - 1
        if extra >= 3:
            f.tel_refused_land += 1
            return
        cost = LAND_PRICES[extra]
        if f.money < cost:
            f.tel_refused_land += 1
            return
        f.money -= cost
        f.total_spend += cost
        quad = LAND_ORDER[extra]
        f.n_quadrants += 1
        for y in range(self.cfg.board_size):
            for x in range(self.cfg.board_size):
                if quadrant_of(x, y, self.cfg.board_size) == quad and f.tiles[y][x].kind == T_LOCKED:
                    f.tiles[y][x].kind = T_EMPTY

    # ------------------------------------------------------------ town / decay
    def town_consume(self, step_i):
        if step_i % self.cfg.shop_sell_interval == 0:
            for s in range(self.st.n_shops):
                mask = SHOP_MASK[self.st.shops[s]]
                mult = SHOP_MULT[self.st.shops[s]]
                for it in range(N_PRODUCTS):
                    if mask & (1 << it):
                        self.st.market.inventory[it] -= mult
        if step_i % self.cfg.center_sell_interval == 0:
            for it in range(N_PRODUCTS):
                if it != FERTILIZER:
                    self.st.market.inventory[it] -= 1
        self.refresh_prices()

    def decay_plants(self, f, step_i):
        if (self.cfg.turns_per_day % 2) == 0 and (step_i % 2) != 0:
            return
        for y in range(self.cfg.board_size):
            row = f.tiles[y]
            for x in range(self.cfg.board_size):
                t = row[x]
                if t.kind != T_PLANT:
                    continue
                if t.max_lifespan_step < 0 or step_i < t.max_lifespan_step:
                    continue
                if (step_i - t.max_lifespan_step) % 2 != 0:
                    continue
                t.yield_units -= 1
                if t.yield_units <= 0:
                    w = Tile()
                    w.kind = T_WEED
                    row[x] = w

    def end_of_day(self, day):
        rng = PyRandom(((self.cfg.seed * 1000003) ^ day) & 0xFFFFFFFFFFFFFFFF)
        for p in range(2):
            f = self.st.farms[p]
            self.daily_refresh_plants(f, day)
            self.daily_refresh_animals(f, day)
            self.spawn_weeds(f, rng)
            self.drop_inventories(f)
            h = self.cfg.board_size // 2
            f.n_units = 1
            f.pos_x[0] = h - 1
            f.pos_y[0] = h - 1
            f.hires_today = 0
            for u in range(MAX_UNITS):
                f.inv_clear(u)
        next_day = day + 1
        if next_day > 0 and next_day % self.cfg.shop_unlock_interval == 0 and self.st.n_shops < MAX_SHOP_INSTANCES:
            drawn = rng.choice_index(N_SHOPS)
            if self.st.n_shops < self.cfg.n_forced_shops:
                self.st.shops[self.st.n_shops] = self.cfg.forced_shops[self.st.n_shops]
            else:
                self.st.shops[self.st.n_shops] = drawn
            self.st.n_shops += 1

    def daily_refresh_plants(self, f, day):
        next_day = day + 1
        for y in range(self.cfg.board_size):
            row = f.tiles[y]
            for x in range(self.cfg.board_size):
                t = row[x]
                if t.kind != T_PLANT:
                    continue
                was_watered = t.watered_today
                t.consecutive_dry = 0 if was_watered else t.consecutive_dry + 1
                t.watered_today = False
                if t.consecutive_dry >= 2:
                    w = Tile()
                    w.kind = T_WEED
                    row[x] = w
                    continue
                cd = CROPS[t.what]
                if not cd[5]:
                    continue
                since = next_day - t.planted_day - cd[1]
                if since < 0:
                    continue
                if since % cd[3] != 0:
                    continue
                count = since // cd[3] + 1
                if count > cd[4]:
                    continue
                fert = was_watered and t.fertilized_until_day >= day
                t.yield_units = min(cd[4], t.yield_units + (2 if fert else 1))
                if count == cd[4]:
                    t.max_lifespan_step = (next_day + 1) * self.cfg.turns_per_day

    def daily_refresh_animals(self, f, day):
        next_day = day + 1
        for y in range(self.cfg.board_size):
            row = f.tiles[y]
            for x in range(self.cfg.board_size):
                t = row[x]
                if not t.has_animal:
                    continue
                t.consecutive_dry = 0 if t.fed_today else t.consecutive_dry + 1
                if t.consecutive_dry >= 2:
                    k = t.kind
                    s = Tile()
                    s.kind = k
                    row[x] = s
                    continue
                ad = ANIMALS[t.what - GOOSE]
                since = next_day - t.planted_day - ad[2]
                if since >= 0 and since % ad[3] == 0:
                    bonus = t.pending_care_bonus if t.fed_today else 0
                    t.yield_units = min(ad[4], t.yield_units + 1 + bonus)
                    t.pending_care_bonus = 0
                if t.cared_today and t.fed_today:
                    t.pending_care_bonus += 1
                t.fertilizer_available = True
                t.fed_today = False
                t.cared_today = False

    def spawn_weeds(self, f, rng):
        for y in range(self.cfg.board_size):
            row = f.tiles[y]
            for x in range(self.cfg.board_size):
                if row[x].kind == T_EMPTY and rng.random() < self.cfg.weed_chance:
                    row[x].kind = T_WEED

    def drop_inventories(self, f):
        for u in range(f.n_units):
            d = f.inv[u]
            keys = list(d.keys())
            for it in keys:
                if d.get(it, 0) <= 0:
                    f.inv_erase(u, it)
                    continue
                room = cfg_shed_room(self.cfg.shed_capacity, f.shed_total)
                take = d[it] if d[it] < room else room
                if take > 0:
                    f.shed[it] += take
                    f.shed_total += take
                f.discarded[it] += d[it] - take
                f.inv_erase(u, it)


class SimFull(Sim, _SimMarket):
    pass
