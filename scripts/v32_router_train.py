# SPDX-License-Identifier: MIT
"""V32 R1 training CLI (system python3, torch CPU).

Builds the dataset, trains the preregistered configs, writes checkpoints
(results/v32_r1_<name>.npz) + run registry (results/v32_r1_runs.json).

Usage: python3 scripts/v32_router_train.py [--opp-holdout] [--quick]
"""

import hashlib
import json
import os
import subprocess
import sys
import time

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, REPO_ROOT)

import numpy as np

from v32.router import baselines as B  # noqa: E402
from v32.router import leakage_checks as LC  # noqa: E402
from v32.router import metrics as ME  # noqa: E402
from v32.router.dataset import load_rows  # noqa: E402
from v32.router.features import (Normalizer, build_a_id, build_b,  # noqa: E402
                                 dim_of)
from v32.router.labels import (hard_target, preference_target,  # noqa: E402
                               soft_target, wl_target)
from v32.router.split import OPP_PANEL, ROUTER_CLASSES, WASH_MICRO  # noqa: E402
from v32.router.train import save_checkpoint, train_model  # noqa: E402

RESULTS = os.path.join(REPO_ROOT, "results")


def git_commit():
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO_ROOT,
                              capture_output=True, text=True).stdout.strip()
    except Exception:  # noqa: BLE001
        return "unknown"


def file_sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for ch in iter(lambda: f.read(1 << 20), b""):
            h.update(ch)
    return h.hexdigest()


def feat_matrix(rows, regime, stack):
    if regime == "a_id":
        return np.array([build_a_id(r) for r in rows], dtype=float)
    return np.array([build_b(r, stack) for r in rows], dtype=float)


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--opp-holdout", action="store_true")
    ap.add_argument("--quick", action="store_true",
                    help="one seed, fewer epochs (smoke only)")
    args = ap.parse_args()

    t0 = time.time()
    rows_full, rows_cont = load_rows()
    audit_f = LC.audit_rows(rows_full)
    audit_c = LC.audit_rows(rows_cont)
    print("rows: full=%d %s | cont=%d %s"
          % (len(rows_full), audit_f, len(rows_cont), audit_c), flush=True)
    if args.opp_holdout:
        rows_full = [r for r in rows_full if r["opp"] not in WASH_MICRO]
        rows_cont = [r for r in rows_cont if r["opp"] not in WASH_MICRO]
        print("opp-holdout: dropped wash-micro opps from train/val", flush=True)

    # B1 labels use FULL-mode legs; B2 labels use CONT-mode legs.
    data = {"b1": rows_full, "b2": rows_cont}
    cfgs = [
        # (name, regime, stack, label-mode, model, seed, target, extra)
        ("M2_logistic_aid", "a_id", "longer", "b1", "logistic", 0, "soft", {}),
        ("M3_small_b1", "b", "longer", "b1", "small", 0, "soft", {}),
        ("M3_small_b1_s1", "b", "longer", "b1", "small", 1, "soft", {}),
        ("M3_stack_none_b1", "b", "none", "b1", "small", 0, "soft", {}),
        ("M3_stack_short_b1", "b", "short", "b1", "small", 0, "soft", {}),
        ("M3_shuffled_b1", "b", "longer", "b1", "small", 0, "soft", {"shuffle": 7}),
        ("M4_small_b2_s0", "b", "longer", "b2", "small", 0, "soft", {}),
        ("M4_small_b2_s1", "b", "longer", "b2", "small", 1, "soft", {}),
        ("M5_med_b2_s0", "b", "longer", "b2", "medium", 0, "soft", {}),
        ("M5_med_b2_s1", "b", "longer", "b2", "medium", 1, "soft", {}),
        ("M6_shuffled", "b", "longer", "b2", "small", 0, "soft", {"shuffle": 7}),
        ("M4_stack_none", "b", "none", "b2", "small", 0, "soft", {}),
        ("M4_stack_short", "b", "short", "b2", "small", 0, "soft", {}),
        ("M4_mt", "b", "longer", "b2", "small_mt", 0, "soft", {"mt": True}),
        ("M4_hard", "b", "longer", "b2", "small", 0, "hard", {}),
        ("M4_prefC", "b", "longer", "b2", "small", 0, "prefC", {}),
    ]
    if args.quick:
        cfgs = cfgs[:2]

    commit = git_commit()
    try:
        import torch
        torch_v = torch.__version__
    except Exception:  # noqa: BLE001
        torch_v = "none"
    runs = []
    for name, regime, stack, lmode, model, seed, target, extra in cfgs:
        rows = data[lmode]
        tr = [r for r in rows if r["split"] == "train"]
        va = [r for r in rows if r["split"] == "val"]
        assert tr and va, (name, len(tr), len(va))
        Xtr = feat_matrix(tr, regime, stack)
        Xva = feat_matrix(va, regime, stack)
        LC.audit_features(Xtr.tolist())
        norm = Normalizer()
        norm.fit(Xtr)
        Xn_tr, Xn_va = norm.transform(Xtr), norm.transform(Xva)
        if target == "soft":
            Ytr = [soft_target(r["cash"]) for r in tr]
            Yva = [soft_target(r["cash"]) for r in va]
        elif target == "hard":
            Ytr = [[1.0 if i == hard_target(r["cash"]) else 0.0
                    for i in range(5)] for r in tr]
            Yva = [[1.0 if i == hard_target(r["cash"]) else 0.0
                    for i in range(5)] for r in va]
        else:  # prefC
            Ytr = [preference_target(r["cash"]) for r in tr]
            Yva = [preference_target(r["cash"]) for r in va]
        if extra.get("shuffle") is not None:
            rng = np.random.RandomState(extra["shuffle"])
            Ytr = [Ytr[i] for i in rng.permutation(len(Ytr))]
        cash_tr = [r["cash"] for r in tr] if extra.get("mt") else None
        win_tr = [r["win"] for r in tr] if extra.get("mt") else None
        cflat = [c for r in tr for c in r["cash"]]
        mu, sd = float(np.mean(cflat)), float(np.std(cflat))
        t1 = time.time()
        state, hist, best_val, n_params = train_model(
            np.asarray(Xn_tr), np.asarray(Ytr), np.asarray(Xn_va),
            np.asarray(Yva), model, seed=seed,
            epochs=200 if args.quick else 2000,
            patience=50 if args.quick else 200,
            multitask=bool(extra.get("mt")), cash_tr=cash_tr,
            cash_mu=mu, cash_sd=sd, win_tr=win_tr)
        dt = time.time() - t1
        meta = {"name": name, "regime": regime, "stack": stack,
                "label_mode": lmode, "model": model, "train_seed": seed,
                "target": target, "extra": extra, "dim": dim_of(regime, stack),
                "n_params": n_params, "normalizer": norm.to_json(),
                "git_commit": commit, "torch": torch_v,
                "n_train": len(tr), "n_val": len(va),
                "best_val_soft_ce": best_val,
                "epochs_run": len(hist), "wall_sec": round(dt, 1),
                "opp_holdout": args.opp_holdout,
                "created": time.strftime("%Y-%m-%dT%H:%M:%S")}
        suffix = "_oh" if args.opp_holdout else ""
        path = os.path.join(RESULTS, "v32_r1_%s%s.npz" % (name, suffix))
        save_checkpoint(path, state, meta)
        meta["sha256"] = file_sha(path)
        runs.append(meta)
        print("%s: params=%d best_val=%.4f epochs=%d -> %s"
              % (name, n_params, best_val, len(hist), os.path.basename(path)),
              flush=True)
    reg = os.path.join(RESULTS, "v32_r1_runs%s.json" % ("_oh" if args.opp_holdout else ""))
    with open(reg, "w") as f:
        json.dump({"commit": commit, "wall_sec_total": round(time.time() - t0, 1),
                   "runs": runs}, f, indent=1, sort_keys=True)
    print("wrote %s (%d runs, %.0fs total)" % (reg, len(runs), time.time() - t0))


if __name__ == "__main__":
    main()
