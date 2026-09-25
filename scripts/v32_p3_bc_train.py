# SPDX-License-Identifier: MIT
"""V32 P3 BC training: native factorized heads on P2 expert legs.

Mirrors scripts/v32_p2_bc_train.py (Adam 3e-4, batch 1024, <=30 epochs,
early-stop patience 5 on val full-exact). Loss = sum of 6 masked-CE head
means. Writes results/v32_p3_bc.npz + results/v32_p3_bc_report.json.
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
import torch
import torch.nn as nn

from v32.p2.dataset import BC_VAL_SEEDS, load_legs  # noqa: E402
from v32.p2.features import Normalizer  # noqa: E402
from v32.p3.dataset import build_samples  # noqa: E402
from v32.p3.metrics import batchify, head_losses, head_metrics  # noqa: E402
from v32.p3.models import P3Policy, param_count  # noqa: E402


def git_commit():
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO_ROOT,
                              capture_output=True, text=True).stdout.strip()
    except Exception:  # noqa: BLE001
        return "unknown"


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--epochs", type=int, default=30)
    ap.add_argument("--batch", type=int, default=1024)
    ap.add_argument("--lr", type=float, default=3e-4)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--teachers", default=None)
    ap.add_argument("--out", default="results/v32_p3_bc.npz")
    ap.add_argument("--report", default="results/v32_p3_bc_report.json")
    args = ap.parse_args()
    torch.manual_seed(args.seed)
    np.random.seed(args.seed)
    teachers = set(args.teachers.split(",")) if args.teachers else None

    norm = Normalizer.from_json(json.load(open(os.path.join(
        REPO_ROOT, "results", "v32_p2_norm.json"))))
    tr_samples, va_samples = [], []
    for leg in load_legs(os.path.join(REPO_ROOT, "results",
                                      "v32_p2_bc_legs.jsonl")):
        store = va_samples if leg["seed"] in BC_VAL_SEEDS else tr_samples
        for side, expert in (("rows0", leg["left"]), ("rows1", leg["right"])):
            if teachers is not None and expert not in teachers:
                continue
            store.extend(build_samples(leg, leg[side], expert))
    print("train=%d val=%d" % (len(tr_samples), len(va_samples)), flush=True)
    F_tr = norm.transform([s["feat"] for s in tr_samples])
    F_va = norm.transform([s["feat"] for s in va_samples])

    model = P3Policy(F_tr.shape[1], 12)
    print("params=%d" % param_count(model), flush=True)
    opt = torch.optim.Adam(model.parameters(), lr=args.lr)
    ce = nn.CrossEntropyLoss(reduction="none")

    N = len(tr_samples)
    best, best_state, since = -1.0, None, 0
    curve = []
    t0 = time.time()
    for ep in range(args.epochs):
        model.train()
        perm = np.random.permutation(N)
        for a in range(0, N, args.batch):
            bidx = perm[a:a + args.batch].tolist()
            b = batchify(bidx, tr_samples, F_tr)
            loss = head_losses(model(b["state"], b["uctx"], b["valid"]), b,
                               ce)["total"]
            opt.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            opt.step()
        mv = head_metrics(model, list(range(len(va_samples))), va_samples,
                          F_va, semantic=True)
        mv["ep"] = ep
        curve.append(mv)
        print("ep=%d val_full=%.3f sem=%.3f uop=%.3f uarg=%.3f uqty=%.3f "
              "mop=%.3f mitem=%.3f mqty=%.3f mop_nn=%.3f"
              % (ep, mv["full_exact"], mv["full_semantic"], mv["u_op"],
                 mv["u_arg"], mv["u_qty"], mv["m_op"], mv["m_item"],
                 mv["m_qty"], mv["m_op_nonnoop"]), flush=True)
        if mv["full_exact"] > best + 1e-6:
            best, since = mv["full_exact"], 0
            best_state = {k: v.detach().clone()
                          for k, v in model.state_dict().items()}
        else:
            since += 1
            if since >= 5:
                break
    model.load_state_dict(best_state)
    mv = head_metrics(model, list(range(len(va_samples))), va_samples, F_va,
                      semantic=True)
    mt = head_metrics(model, list(range(N)), tr_samples, F_tr, semantic=True)
    meta = {"git": git_commit(), "arch": "v32p3-a1", "epochs": args.epochs,
            "batch": args.batch, "lr": args.lr, "seed": args.seed,
            "params": param_count(model), "val": mv, "train": mt,
            "curve": curve, "wall_sec": round(time.time() - t0, 1),
            "schema": "V32_P3_ACTION_SCHEMA.json",
            "vocab_sha": hashlib.sha256(open(os.path.join(
                REPO_ROOT, "results", "v32_p2_vocab.json"), "rb").read()
            ).hexdigest()[:16],
            "teachers": sorted(teachers) if teachers else "all"}
    out = os.path.join(REPO_ROOT, args.out)
    np.savez(out, **{k: v.numpy() for k, v in best_state.items()},
             meta=json.dumps(meta, sort_keys=True, default=str))
    with open(os.path.join(REPO_ROOT, args.report), "w") as f:
        json.dump(meta, f, indent=1, sort_keys=True, default=str)
    print("wrote %s val_full=%.3f sem=%.3f" % (out, mv["full_exact"],
                                                mv["full_semantic"]))


if __name__ == "__main__":
    main()
