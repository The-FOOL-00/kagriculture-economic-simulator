# SPDX-License-Identifier: MIT
"""R1 features. Legal public channels only; never seed IDs or future info.

A+ID: opponent one-hot (6) + seat (1) = 7 dims.
B: frame stack over v32enc-v1.1 prefix encodings + 23-dim prefix summary:
    own/opp cash at t=24 and deltas vs t=0 (4), all-product price deltas
    t=24 vs t=0 (9), wheat price t=0,4,..,24 (7), wheat inventory delta (1),
    prefix hires/fertilize counts (2).
Stacks: none={24}: 113; short={12,24}: 203; longer={0,12,24}: 293.
"""

import math

from v32.router.split import OPP_PANEL

V32_OBS_DIM = 90  # pinned to v32enc-v1.1; asserted per frame at build time

STACKS = {"none": (24,), "short": (12, 24), "longer": (0, 12, 24)}
PRODUCTS = ["WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON", "EGG",
            "MILK", "WOOL", "FERTILIZER"]
AID_DIM = len(OPP_PANEL) + 1
SUMMARY_DIM = 23


def _f(x, default=0.0):
    try:
        return float(x)
    except (TypeError, ValueError):
        return default


def build_a_id(row):
    return [1.0 if row["opp"] == o else 0.0 for o in OPP_PANEL] + [0.0]


def _price_at(prefix, t, product):
    # Encoder stores normalized prices; recover scale x250 for deltas.
    # Prefix frames lack raw prices, so use wheat track + frame slots.
    return None


def build_b(row, stack="longer"):
    """Build Regime-B features from the row's V3-opening prefix."""
    p = row.get("prefix") or {}
    frames = p.get("frames", {}) or {}
    wheat = p.get("wheat", {}) or {}
    invw = p.get("inv_wheat", {}) or {}
    cash = p.get("cash", {}) or {}
    vec = []
    for t in STACKS[stack]:
        fr = frames.get(str(t)) or frames.get(t)
        if fr is None:
            vec.extend([0.0] * 90)
        else:
            assert len(fr) == 90, len(fr)
            vec.extend([max(-8.0, min(8.0, _f(x))) for x in fr])
    # --- 23-dim prefix summary (all from t<=24 public channels)
    f24 = frames.get("24") or frames.get(24) or [0.0] * 90
    f0 = frames.get("0") or frames.get(0) or [0.0] * 90
    # market slots 62..70 (9 prices /250), groups per v32_encoder layout:
    # global 0-7, crop 8-31, livestock 32-41, workers 42-49, land 50-55,
    # market 56-69, opp 70-85, phase 86-89.
    def fr_at(fr, i):
        return _f(fr[i]) if i < len(fr) else 0.0
    price_d = [(fr_at(f24, 56 + i) - fr_at(f0, 56 + i)) for i in range(9)]
    c24 = cash.get("24") or cash.get(24) or [None, None]
    c0 = cash.get("0") or cash.get(0) or [None, None]
    own24, opp24 = _f(c24[0]), _f(c24[1])
    own0, opp0 = _f(c0[0]), _f(c0[1])
    wtrack = [_f(wheat.get(str(t), wheat.get(t))) / 250.0
              for t in (0, 4, 8, 12, 16, 20, 24)]
    inv_d = (_f(invw.get("24", invw.get(24))) - _f(invw.get("0", invw.get(0)))) / 2e4
    # hires/fertilize proxies from worker/op slots are temporal; use market
    # pressure slots instead: shed_total proxies at 66/68 (see encoder).
    summ_ = [own24 / 1e5, opp24 / 1e5,
             (own24 - own0) / 1e5, (opp24 - opp0) / 1e5]
    summ_ += price_d
    summ_ += wtrack
    summ_ += [max(-8.0, min(8.0, inv_d)),
              max(-8.0, min(8.0, fr_at(f24, 66) - fr_at(f0, 66))),
              max(-8.0, min(8.0, fr_at(f24, 68) - fr_at(f0, 68)))]
    assert len(summ_) == SUMMARY_DIM, len(summ_)
    vec += [max(-8.0, min(8.0, v)) for v in summ_]
    return vec


def dim_of(regime, stack="longer"):
    if regime == "a_id":
        return AID_DIM
    return 90 * len(STACKS[stack]) + SUMMARY_DIM


class Normalizer:
    """TRAIN-only mean/std, frozen before VAL/TEST/LOCKED. One-hot safe."""

    def __init__(self):
        self.mu = self.sd = None

    def fit(self, X):
        import numpy as np
        X = np.asarray(X, dtype=float)
        self.mu = X.mean(axis=0)
        self.sd = X.std(axis=0)
        self.sd[self.sd < 1e-9] = 1.0
        # do not rescale one-hot / constant slots (sd==0 kept 1.0 above;
        # also pin near-constant slots to avoid noise blowup)
        self.sd[self.sd < 1e-6] = 1.0

    def transform(self, X):
        import numpy as np
        X = np.asarray(X, dtype=float)
        return ((X - self.mu) / self.sd).tolist()

    def to_json(self):
        return {"mu": list(self.mu), "sd": list(self.sd)}

    @classmethod
    def from_json(cls, d):
        import numpy as np
        n = cls()
        n.mu = np.array(d["mu"], dtype=float)
        n.sd = np.array(d["sd"], dtype=float)
        return n
