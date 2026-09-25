# SPDX-License-Identifier: MIT
"""R1 evaluation driver: predictors -> metrics tables + JSON."""

from v32.router import baselines as B
from v32.router import metrics as M
from v32.router import oracle as O
from v32.router.split import ROUTER_CLASSES, SHORT


def all_predictors(train_rows):
    """Fixed baselines + oracles-as-functions + M1 lookup (TRAIN-fit)."""
    m1 = B.PerOpponentLookup()
    m1.fit(train_rows)
    protos = {
        "always_A7": B.FixedExpert("E2_A7"),
        "always_best_fixed": B.FixedExpert(
            ROUTER_CLASSES[B.global_best_fixed(train_rows)]),
        "always_W72": B.FixedExpert("E6_W72"),
        "random": B.RandomExpert(0),
        "per_opp_lookup_M1": m1,
    }
    return protos


def summarize(rows, pred_map, tag):
    """pred_map: name -> sel list. Returns {name: (metrics, per_row)}."""
    out = {}
    for name, sel in pred_map.items():
        out[name] = M.evaluate(rows, sel, tag="%s/%s" % (tag, name))
    return out


def report_table(summary, a7_sel):
    """Print compact comparison table. Returns lines."""
    lines = []
    lines.append("%-18s %6s %9s %9s %11s %11s %7s %5s" % (
        "predictor", "n", "mean_cash", "median", "mean_regr",
        "median_regr", "W-L-T", "cat"))
    for name, (m, _) in summary.items():
        lines.append("%-18s %6d %9.0f %9.0f %11.0f %11.0f %d-%d-%d %5d" % (
            name, m["n"], m["mean_cash"], m["median_cash"], m["mean_regret"],
            m["median_regret"], m["W"], m["L"], m["T"], m["catastrophic"]))
    return lines
