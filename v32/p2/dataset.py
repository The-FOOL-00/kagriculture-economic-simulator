# SPDX-License-Identifier: MIT
"""V32 P2 BC dataset: capture legs -> (features, per-slot targets, masks).

Features replayed through the ONLINE builder in step order (identical code
path as rollout/eval). BC-val = P2-TRAIN seeds 249647-249649 held out of
gradient updates (BC early stopping + BC-vs-expert replay check).
"""

import json
import os

from v32.p2 import actions as A
from v32.p2.features import EpisodeFeatures, Normalizer, unit_ctx

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

BC_VAL_SEEDS = {249647, 249648, 249649}


def load_legs(path):
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)


def build_samples(leg, seat_rows, uidx, midx):
    """Replay one seat's rows through the online builder. Yields samples."""
    fb = EpisodeFeatures()
    prev = None
    for row in seat_rows:
        ess = row["e"]
        feat = fb.update(ess, prev)
        act = row["a"] or {}
        units = [act.get("farmer")] + list(act.get("hands") or [])
        n_u = 1 + len(ess.get("hands", []) or [])
        ut, ux = [], []
        for j in range(n_u):
            lit = units[j] if j < len(units) else ["PASS"]
            c = A.unit_from_literal(lit)
            ut.append(uidx.get(c, -1))
            ux.append(unit_ctx(ess, j))
        mk = act.get("market") or []
        mt = []
        for s in range(A.M_MARKET_SLOTS):
            lit = mk[s] if s < len(mk) else []
            c = A.market_from_literal(lit)
            mt.append(midx.get(c, -1))
        yield {"feat": feat, "uctx": ux, "u_targ": ut, "m_targ": mt,
               "mask": A.plant_mask(list(uidx), ess.get("seeds", {}) or {}),
               "step": ess.get("step"), "seed": leg["seed"]}
        prev = act


def coverage_report(samples):
    n_u = sum(len(s["u_targ"]) for s in samples)
    n_m = sum(len(s["m_targ"]) for s in samples)
    miss_u = sum(1 for s in samples for t in s["u_targ"] if t < 0)
    miss_m = sum(1 for s in samples for t in s["m_targ"] if t < 0)
    return {"unit_slots": n_u, "market_slots": n_m,
            "unit_miss": miss_u, "market_miss": miss_m}
