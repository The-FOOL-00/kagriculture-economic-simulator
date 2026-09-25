# SPDX-License-Identifier: MIT
"""V32 P3 memorization gate (G2): can the native head fit expert actions at all?

Fixed 400-sample subset (deterministic, saved to results/v32_p3_mem_idx.json).
Trains (a) P3Policy (b) LinearControl, up to 300 epochs (P2 pointer ran 300 ->
55%; P2 linear control hit 100% by ep75). Reports loss + per-head accuracy +
full-exact + full-semantic curves. Mixture subset first (prereg §5); --teachers
for the single-teacher branch.
"""

import json
import os
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
from v32.p3.models import LinearControl, P3Policy, param_count  # noqa: E402

SUBSET = 400


def load_train(teachers=None, p2exact=False):
    import itertools
    out = []
    for leg in load_legs(os.path.join(REPO_ROOT, "results",
                                      "v32_p2_bc_legs.jsonl")):
        if p2exact:
            # P2's exact probe population: contiguous rows0[0:400] of the
            # (249635, left=E2_A7) leg. Recovered from P2 session archaeology.
            if leg["seed"] != 249635 or leg["left"] != "E2_A7":
                continue
            out.extend(itertools.islice(
                build_samples(leg, leg["rows0"], leg["left"]), SUBSET))
            break
        if leg["seed"] in BC_VAL_SEEDS:
            continue
        for side, expert in (("rows0", leg["left"]), ("rows1", leg["right"])):
            if teachers is not None and expert not in teachers:
                continue
            out.extend(build_samples(leg, leg[side], expert))
    return out


def run_fit(model, idxs, samples, F, epochs, batch, lr, tag, log_every=25):
    opt = torch.optim.Adam(model.parameters(), lr=lr)
    ce = nn.CrossEntropyLoss(reduction="none")
    curve = []
    t0 = time.time()
    N = len(idxs)
    for ep in range(epochs):
        model.train()
        perm = np.random.permutation(N)
        tot = 0.0
        nb = 0
        for a in range(0, N, batch):
            bidx = [idxs[i] for i in perm[a:a + batch].tolist()]
            b = batchify(bidx, samples, F)
            loss = head_losses(model(b["state"], b["uctx"], b["valid"]), b,
                               ce)["total"]
            opt.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            opt.step()
            tot += float(loss.detach())
            nb += 1
        if ep % log_every == 0 or ep == epochs - 1:
            m = head_metrics(model, idxs, samples, F, semantic=True)
            m["loss"] = tot / nb
            m["ep"] = ep
            curve.append(m)
            print("%s ep=%d loss=%.3f full=%.3f sem=%.3f uop=%.3f "
                  "farmer=%.3f mop=%.3f mqty=%.3f" % (tag, ep, m["loss"],
                                                      m["full_exact"],
                                                      m["full_semantic"],
                                                      m["u_op"], m["farmer"],
                                                      m["m_op"], m["m_qty"]),
                  flush=True)
    return {"curve": curve, "params": param_count(model),
            "wall_sec": round(time.time() - t0, 1)}


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--epochs", type=int, default=300)
    ap.add_argument("--batch", type=int, default=64)
    ap.add_argument("--lr", type=float, default=3e-4)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--teachers", default=None)
    ap.add_argument("--subset-mode", default="random",
                    choices=["random", "contiguous", "p2exact"],
                    help="random: 400 uniform samples; contiguous: first 400 "
                         "train rows; p2exact: P2's probe population "
                         "(249635/E2_A7/rows0 contiguous 400)")
    ap.add_argument("--out", default="results/v32_p3_mem_report.json")
    ap.add_argument("--idx", default="results/v32_p3_mem_idx.json")
    args = ap.parse_args()
    torch.manual_seed(args.seed)
    np.random.seed(args.seed)
    teachers = set(args.teachers.split(",")) if args.teachers else None

    samples = load_train(teachers, p2exact=(args.subset_mode == "p2exact"))
    norm = Normalizer.from_json(json.load(open(os.path.join(
        REPO_ROOT, "results", "v32_p2_norm.json"))))
    F = norm.transform([s["feat"] for s in samples])
    if args.subset_mode in ("contiguous", "p2exact"):
        assert len(samples) >= SUBSET, (args.subset_mode, len(samples))
        idxs = list(range(SUBSET))
    else:
        rng = np.random.RandomState(0)
        idxs = sorted(rng.choice(len(samples), SUBSET,
                                 replace=False).tolist())
    with open(os.path.join(REPO_ROOT, args.idx), "w") as f:
        json.dump({"idx": idxs, "teachers": sorted(teachers)
                   if teachers else "all", "pool": len(samples),
                   "subset_mode": args.subset_mode}, f)
    print("pool=%d subset=%d params_p3=%d params_lin=%d" % (
        len(samples), SUBSET, param_count(P3Policy()),
        param_count(LinearControl())), flush=True)

    torch.manual_seed(args.seed)
    rep = {"subset": SUBSET, "teachers": sorted(teachers)
           if teachers else "all", "epochs": args.epochs,
           "batch": args.batch, "lr": args.lr, "seed": args.seed}
    rep["p3"] = run_fit(P3Policy(), idxs, samples, F, args.epochs,
                        args.batch, args.lr, "p3")
    torch.manual_seed(args.seed)
    rep["linear"] = run_fit(LinearControl(), idxs, samples, F, args.epochs,
                            args.batch, args.lr, "linear")
    with open(os.path.join(REPO_ROOT, args.out), "w") as f:
        json.dump(rep, f, indent=1, sort_keys=True, default=str)
    print("wrote %s" % args.out)


if __name__ == "__main__":
    main()
