# SPDX-License-Identifier: MIT
"""R1 metrics. Rows are (seed, opponent); seeds are the sample unit."""

import math
import random
from collections import defaultdict

from v32.router.oracle import oracle_cash_value
from v32.router.split import ROUTER_CLASSES

A7_IDX = ROUTER_CLASSES.index("E2_A7")
CATASTROPHE = 25000.0


def _mean(xs):
    return sum(xs) / len(xs) if xs else 0.0


def _median(xs):
    xs = sorted(xs)
    return xs[len(xs) // 2] if xs else 0.0


def evaluate(rows, sel, tag=""):
    """sel: expert index per row. Returns metric dict + per-row table."""
    assert len(rows) == len(sel)
    cash, wins, regret, nreg, per_row = [], [], [], [], []
    per_seed = defaultdict(list)
    per_opp = defaultdict(list)
    for r, i in zip(rows, sel):
        c = r["cash"][i]
        a7 = r["cash"][A7_IDX]
        oc = oracle_cash_value(r)
        reg = oc - c
        base = oc - a7
        nr = reg / (abs(base) + 1e-9) if abs(base) > 1e-9 else (0.0 if reg == 0 else 1.0)
        cash.append(c)
        wins.append(r["win"][i])
        regret.append(reg)
        nreg.append(nr)
        per_seed[r["seed"]].append(c - a7)
        per_opp[r["opp"]].append(c - a7)
        per_row.append({"seed": r["seed"], "opp": r["opp"], "sel": i,
                        "cash": c, "a7": a7, "oracle": oc, "regret": reg,
                        "win": r["win"][i]})
    w = sum(1 for x in wins if x == 1.0)
    l = sum(1 for x in wins if x == 0.0)
    t = len(wins) - w - l
    tail = sorted(cash)[: max(1, int(0.05 * len(cash)) + 1)]
    cat = sum(1 for r, i in zip(rows, sel)
              if r["cash"][i] < r["cash"][A7_IDX] - CATASTROPHE)
    seed_lift = {s: _mean(v) for s, v in per_seed.items()}
    opp_lift = {o: _mean(v) for o, v in per_opp.items()}
    return {
        "tag": tag, "n": len(rows), "n_seeds": len(per_seed),
        "mean_cash": _mean(cash), "median_cash": _median(cash),
        "W": w, "L": l, "T": t,
        "mean_regret": _mean(regret), "median_regret": _median(regret),
        "mean_nreg": _mean(nreg),
        "worst5_mean": _mean(tail),
        "catastrophic": cat,
        "seed_positive_frac": sum(1 for v in seed_lift.values() if v > 0) / max(1, len(seed_lift)),
        "per_seed_lift": seed_lift, "per_opp_lift": opp_lift,
    }, per_row


def seed_bootstrap_ci(rows, sel_a, sel_b=None, n_boot=2000, seed=0):
    """95% CI for mean selected cash, or paired lift vs sel_b. Seeds resampled."""
    rng = random.Random(seed)
    by_seed = defaultdict(list)
    for j, r in enumerate(rows):
        va = r["cash"][sel_a[j]]
        by_seed[r["seed"]].append(va - r["cash"][sel_b[j]] if sel_b is not None else va)
    seeds = sorted(by_seed)
    est = _mean([x for s in seeds for x in by_seed[s]])
    boots = []
    for _ in range(n_boot):
        samp = [rng.choice(seeds) for _ in seeds]
        boots.append(_mean([x for s in samp for x in by_seed[s]]))
    boots.sort()
    lo = boots[int(0.025 * n_boot)]
    hi = boots[min(n_boot - 1, int(0.975 * n_boot))]
    return {"est": est, "lo": lo, "hi": hi, "n_boot": n_boot}


def drop_one_seed(rows, sel, base_sel):
    """Mean lift vs base dropping each seed (G6 sensitivity)."""
    seeds = sorted({r["seed"] for r in rows})
    out = {}
    for s in seeds:
        sub = [(r, i, b) for r, i, b in zip(rows, sel, base_sel)
               if r["seed"] != s]
        out[s] = _mean([r["cash"][i] - r["cash"][b] for r, i, b in sub])
    return out
