# SPDX-License-Identifier: MIT
"""V32 R1 evaluation CLI (system python3, torch CPU for RouterPredictor).

Evaluates baselines + oracles + trained routers on a split and writes
machine-readable metrics. LOCKED is opened only with --locked (once).

Usage: python3 scripts/v32_router_evaluate.py --split test [--locked]
       [--ckpt name ...] [--out results/v32_r1_eval_test.json]
"""

import json
import os
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, REPO_ROOT)

from v32.router import baselines as B  # noqa: E402
from v32.router import evaluate as E  # noqa: E402
from v32.router import leakage_checks as LC  # noqa: E402
from v32.router import metrics as M  # noqa: E402
from v32.router import oracle as O  # noqa: E402
from v32.router.dataset import load_rows  # noqa: E402
from v32.router.inference import RouterPredictor  # noqa: E402
from v32.router.split import ROUTER_CLASSES, SHORT  # noqa: E402

RESULTS = os.path.join(REPO_ROOT, "results")


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", default="test",
                    choices=["train", "val", "test", "locked", "test_locked"])
    ap.add_argument("--locked", action="store_true",
                    help="include LOCKED rows (confirmatory only, run once)")
    ap.add_argument("--ckpt", nargs="*", default=[],
                    help="checkpoint names (results/v32_r1_<name>.npz)")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    if args.split in ("locked", "test_locked") and not args.locked:
        raise SystemExit("refusing to open LOCKED without --locked")

    rows_full, rows_cont = load_rows(include_locked=args.locked)
    LC.audit_rows(rows_full)
    LC.audit_rows(rows_cont)
    want = {"train": ["train"], "val": ["val"], "test": ["test"],
            "locked": ["locked"],
            "test_locked": ["test", "locked"]}[args.split]

    out = {}
    for lmode, rows in (("b1", rows_full), ("b2", rows_cont)):
        sub = [r for r in rows if r["split"] in want]
        tr = [r for r in rows if r["split"] == "train"]
        if not sub:
            continue
        protos = E.all_predictors(tr)
        pred = {n: p.predict(sub) for n, p in protos.items()}
        pred["oracle_cash"] = [O.oracle_cash(r) for r in sub]
        pred["oracle_wl"] = [O.oracle_wl(r) for r in sub]
        for ck in args.ckpt:
            path = os.path.join(RESULTS, "v32_r1_%s.npz" % ck)
            rp = RouterPredictor(path)
            if rp.meta["label_mode"] != lmode:
                continue
            pred["router_" + ck] = rp.predict(sub)
        summ = E.summarize(sub, pred, "%s/%s" % (args.split, lmode))
        a7 = pred["always_A7"]
        for line in E.report_table(summ, a7):
            print("[%s] %s" % (lmode, line))
        # paired CIs vs A7 + drop-one-seed for routers
        extra = {}
        for name, sel in pred.items():
            if name == "always_A7":
                continue
            extra[name] = {
                "lift_vs_a7_ci": M.seed_bootstrap_ci(sub, sel, a7),
                "drop_one_seed_min": min(
                    M.drop_one_seed(sub, sel, a7).values()),
            }
        out[lmode] = {
            "metrics": {n: m for n, (m, _) in summ.items()},
            "paired": extra,
            "per_row": {n: pr for n, (_, pr) in summ.items()},
        }
    if args.out:
        with open(args.out, "w") as f:
            json.dump(out, f, indent=1, sort_keys=True, default=str)
        print("wrote %s" % args.out)


if __name__ == "__main__":
    main()
