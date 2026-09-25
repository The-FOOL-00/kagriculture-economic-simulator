# SPDX-License-Identifier: MIT
"""V32 P2 structured-temporal features (locked Groups A-D).

Online builder with explicit ring buffers: every temporal feature is a pure
function of already-observed essentials + own past actions. Same code path
for BC training (offline replay in step order), PPO rollout, and eval.

Schema versioned + hashed (frozen in V32_P2_ARCHITECTURE.json).
"""

import math
from collections import deque

SCHEMA_VERSION = "v32p2feat-v1"
WINDOWS = (1, 8, 32, 128)
EPISODE_STEPS = 720

PRODUCTS = ["WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON", "EGG",
            "MILK", "WOOL", "FERTILIZER"]
CROPS = ["WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON"]
ANIMALS = ["COW", "SHEEP", "GOOSE"]

# (name, scale) for GROUP B base vars, in fixed order.
B_BASE = [("cash", 1e5), ("shed_total", 100.0), ("seeds_total", 50.0),
          ("plants", 100.0), ("hands_n", 12.0), ("px_wheat", 250.0),
          ("px_fert", 250.0), ("px_milk", 250.0), ("px_wool", 250.0),
          ("mkt_wheat", 2e4), ("o_money", 1e5), ("shops_n", 8.0)]

UNIT_CATS = ["move", "plant", "water", "harvest", "fertilize",
             "animal_care", "build_dig", "carry", "pass"]
UNIT_OP2CAT = {"NORTH": "move", "SOUTH": "move", "EAST": "move",
               "WEST": "move", "PLANT": "plant", "WATER": "water",
               "HARVEST": "harvest", "FERTILIZE": "fertilize",
               "FEED": "animal_care", "CARE": "animal_care",
               "COLLECT_FERTILIZER": "animal_care", "DIG": "build_dig",
               "BUILD_COOP": "build_dig", "BUILD_PASTURE": "build_dig",
               "PICKUP": "carry", "PLACE": "carry", "DROP": "carry",
               "PASS": "pass"}


def _f(x, default=0.0):
    try:
        return float(x)
    except (TypeError, ValueError):
        return default


def _b_base(ess):
    shed = ess.get("shed", {}) or {}
    seeds = ess.get("seeds", {}) or {}
    prices = ess.get("prices", {}) or {}
    mkt = ess.get("mkt_inv", {}) or {}
    th = ess.get("thist", []) or []
    return [_f(ess.get("money")), sum(_f(v) for v in shed.values()),
            sum(_f(v) for v in seeds.values()),
            sum(_f(v) for v in th[:5]),
            float(len(ess.get("hands", []) or [])),
            _f(prices.get("WHEAT")), _f(prices.get("FERTILIZER")),
            _f(prices.get("MILK")), _f(prices.get("WOOL")),
            _f(mkt.get("WHEAT")), _f(ess.get("o_money")),
            float(len(ess.get("shops", []) or []))]


def _act_cats(act):
    """Own action -> (unit cat counts[9], n_units, buy_n, sell_n, sell_qty,
    buy_spend, hire_n)."""
    act = act or {}
    units = [act.get("farmer")] + list(act.get("hands") or [])
    cats = [0] * len(UNIT_CATS)
    n_units = 0
    for u in units:
        if not isinstance(u, list) or not u:
            continue
        n_units += 1
        c = UNIT_OP2CAT.get(u[0])
        if c is not None:
            cats[UNIT_CATS.index(c)] += 1
    buy_n = sell_n = hire_n = 0
    sell_qty = buy_spend = 0.0
    for o in (act.get("market") or []):
        if not isinstance(o, list) or not o:
            continue
        if o[0] == "SELL":
            sell_n += 1
            sell_qty += _f(o[2]) if len(o) > 2 else 0.0
        elif o[0] in ("BUY_SEED", "BUY_PRODUCT", "BUY_ANIMAL"):
            buy_n += 1
            buy_spend += _f(o[2]) if len(o) > 2 else 0.0
        elif o[0] == "HIRE":
            hire_n += 1
    return cats, n_units, buy_n, sell_n, sell_qty, buy_spend, hire_n


class EpisodeFeatures:
    """Per-episode online feature state. reset() each episode."""

    def __init__(self):
        self.reset()

    def reset(self):
        self.t = -1
        self.b_hist = deque(maxlen=max(WINDOWS) + 1)
        # action history: per-step (unit cats, n_units, mkt cats...)
        self.a_hist = deque(maxlen=max(WINDOWS) + 1)
        self.f_hist = deque(maxlen=9)  # farmer op strings, t'<t + current None
        self.dim = None

    def update(self, ess, prev_act):
        """Advance one step. prev_act = own action at step t-1 (None at 0).
        Returns raw (unnormalized) feature list for the CURRENT essentials."""
        self.t += 1
        self.b_hist.append(_b_base(ess))
        self.a_hist.append(_act_cats(prev_act))
        f = (prev_act or {}).get("farmer")
        self.f_hist.append(f[0] if isinstance(f, list) and f else None)
        return self._build(ess)

    # ---- groups ----
    def _group_a(self, ess):
        shed = ess.get("shed", {}) or {}
        seeds = ess.get("seeds", {}) or {}
        prices = ess.get("prices", {}) or {}
        mkt = ess.get("mkt_inv", {}) or {}
        inv = ess.get("inv", []) or []
        hands = ess.get("hands", []) or []
        th = list((ess.get("thist", []) or []) + [0] * 12)[:12]
        fx, fy = (list(ess.get("farmer", [4, 4])) + [4, 4])[:2]
        cash = _f(ess.get("money"))
        n_units = 1 + len(hands)
        carry = sum(1 for v in inv if isinstance(v, dict) and
                    sum(_f(x) for x in v.values()) > 0)
        hx = [_f(h[0]) for h in hands if isinstance(h, (list, tuple))]
        hy = [_f(h[1]) for h in hands if isinstance(h, (list, tuple))]
        sx = (sum((x - sum(hx) / len(hx)) ** 2 for x in hx) / len(hx)) ** 0.5 \
            if hx else 0.0
        sy = (sum((y - sum(hy) / len(hy)) ** 2 for y in hy) / len(hy)) ** 0.5 \
            if hy else 0.0
        v = [_f(ess.get("step")) / EPISODE_STEPS, _f(ess.get("day")) / 30.0,
             _f(ess.get("hour")) / 24.0, cash / 1e5,
             math.copysign(math.log1p(abs(cash)), cash) / 12.0,
             sum(_f(x) for x in shed.values()) / 100.0,
             sum(_f(x) for x in seeds.values()) / 50.0,
             len(ess.get("shops", []) or []) / 8.0,
             _f(ess.get("quads")) / 4.0, _f(ess.get("hires")) / 12.0,
             len(hands) / 12.0]
        v += [_f(shed.get(k)) / 50.0 for k in PRODUCTS + ANIMALS]
        v += [_f(seeds.get(k)) / 20.0 for k in CROPS]
        v += [sum(sum(_f(x) for x in (iv or {}).values()) for iv in inv) / 50.0,
              carry / max(1, n_units)]
        v += [_f(x) / 100.0 for x in th]
        v += [_f(fx) / 10.0, _f(fy) / 10.0, sx / 10.0, sy / 10.0]
        v += [_f(prices.get(k)) / 250.0 for k in PRODUCTS]
        v += [_f(mkt.get(k)) / 2e4 for k in PRODUCTS]
        v += [_f(ess.get("o_money")) / 1e5,
              _f(ess.get("o_hands")) / 12.0, _f(ess.get("o_quads")) / 4.0,
              _f(ess.get("o_plant")) / 100.0, _f(ess.get("o_past")) / 100.0,
              _f(ess.get("o_weed")) / 100.0]
        v += [_f(shed.get(k)) / 20.0 for k in ANIMALS]
        return v

    def _group_b(self):
        out = []
        cur = self.b_hist[-1]
        for w in WINDOWS:
            if len(self.b_hist) > w:
                old = self.b_hist[-1 - w]
                out += [(c - o) / s for c, o, (_, s) in
                        zip(cur, old, B_BASE)]
            else:
                out += [0.0] * len(B_BASE)
        out += [1.0 if len(self.b_hist) > w else 0.0 for w in WINDOWS]
        return out

    def _group_c(self):
        out = []
        # a_hist[0] is the t=0 placeholder (prev_act=None); real history of
        # actions at steps 0..t-1 is a_hist[1:].
        past = list(self.a_hist)[1:]
        for w in (8, 32):
            hist = past[-w:]
            denom_u = max(1, sum(h[1] for h in hist))
            unit = [0.0] * len(UNIT_CATS)
            buy = sell = hire = 0.0
            sq = bs = 0.0
            for cats, _, b, s, q, e, hh in hist:
                for i, c in enumerate(cats):
                    unit[i] += c
                buy += b
                sell += s
                sq += q
                bs += e
                hire += hh
            out += [u / denom_u for u in unit]
            d = max(1, len(hist))
            out += [buy / d / 4.0, sell / d / 4.0, sq / d / 1000.0,
                    bs / d / 1000.0, hire / d]
        # repetition: frac of last-8 farmer ops equal to the most recent one
        fh = [x for x in list(self.f_hist)[1:]][-8:]
        if len(fh) >= 2 and fh[-1] is not None:
            out.append(sum(1 for x in fh[:-1] if x == fh[-1]) / (len(fh) - 1))
        else:
            out.append(0.0)
        return out

    def _group_d(self, ess):
        step = _f(ess.get("step"))
        return [step / (EPISODE_STEPS - 1), _f(ess.get("day")) / 30.0,
                (EPISODE_STEPS - 1 - step) / (EPISODE_STEPS - 1)]

    def _build(self, ess):
        v = self._group_a(ess) + self._group_b() + self._group_c() + \
            self._group_d(ess)
        if self.dim is None:
            self.dim = len(v)
        assert len(v) == self.dim
        return v


def schema_names():
    """Feature names in order (for the frozen schema record)."""
    e = EpisodeFeatures()
    a = ["step", "day", "hour", "cash", "cash_log", "shed_tot", "seeds_tot",
         "shops", "quads", "hires", "hands_n"]
    a += ["shed_%s" % k for k in PRODUCTS + ANIMALS]
    a += ["seed_%s" % k for k in CROPS]
    a += ["inv_tot", "carry_frac"]
    a += ["th_%d" % i for i in range(12)]
    a += ["fx", "fy", "spread_x", "spread_y"]
    a += ["px_%s" % k for k in PRODUCTS]
    a += ["mi_%s" % k for k in PRODUCTS]
    a += ["o_money", "o_hands", "o_quads", "o_plant", "o_past", "o_weed"]
    a += ["live_%s" % k for k in ANIMALS]
    b = []
    for w in WINDOWS:
        b += ["d%d_%s" % (w, n) for n, _ in B_BASE]
    b += ["valid_%d" % w for w in WINDOWS]
    c = []
    for w in (8, 32):
        c += ["a%d_%s" % (w, n) for n in UNIT_CATS]
        c += ["a%d_buy" % w, "a%d_sell" % w, "a%d_sellq" % w,
              "a%d_buyspend" % w, "a%d_hire" % w]
    c += ["repeat8"]
    d = ["turn", "progress_day", "terminal_prox"]
    names = (["A/%s" % n for n in a] + ["B/%s" % n for n in b] +
             ["C/%s" % n for n in c] + ["D/%s" % n for n in d])
    e.dim = len(names)
    return names


def unit_ctx(ess, unit_idx):
    """Per-unit query context: pos + tile one-hot(9) + inv size."""
    if unit_idx == 0:
        pos = list((ess.get("farmer") or [4, 4])[:2])
    else:
        hands = ess.get("hands", []) or []
        pos = list(hands[unit_idx - 1][:2]) if unit_idx - 1 < len(hands) \
            else [4, 4]
    ucodes = ess.get("ucode", []) or []
    code = ucodes[unit_idx] if unit_idx < len(ucodes) else 1
    inv = ess.get("inv", []) or []
    iv = inv[unit_idx] if unit_idx < len(inv) and isinstance(inv[unit_idx], dict) \
        else {}
    onehot = [1.0 if code == i else 0.0 for i in range(9)]
    return [_f(pos[0]) / 10.0, _f(pos[1]) / 10.0] + onehot + \
        [sum(_f(x) for x in iv.values()) / 20.0]


class Normalizer:
    def __init__(self):
        self.mu = self.sd = None

    def fit(self, X):
        import numpy as np
        X = np.asarray(X, dtype=float)
        self.mu = X.mean(axis=0)
        self.sd = X.std(axis=0)
        self.sd[self.sd < 1e-6] = 1.0

    def transform(self, X):
        import numpy as np
        return np.clip((np.asarray(X, dtype=float) - self.mu) / self.sd,
                       -8.0, 8.0)

    def to_json(self):
        return {"mu": list(map(float, self.mu)),
                "sd": list(map(float, self.sd)), "clip": 8.0}

    @classmethod
    def from_json(cls, d):
        import numpy as np
        n = cls()
        n.mu = np.array(d["mu"], dtype=float)
        n.sd = np.array(d["sd"], dtype=float)
        return n
