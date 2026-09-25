# SPDX-License-Identifier: MIT
"""V32 P2 architecture-aligned BC training (CASE B: no compatible EXP-2 head).

Trains the LOCKED pointer-head policy on expert legs (P2-TRAIN seeds;
BC-val 249647-249649 held out). Loss = sum of per-slot masked CEs.
Writes results/v32_p2_bc.npz + results/v32_p2_bc_report.json.
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

from v32.p2 import actions as A  # noqa: E402
from v32.p2.dataset import BC_VAL_SEEDS, build_samples, load_legs  # noqa: E402
from v32.p2.features import Normalizer  # noqa: E402
from v32.p2.models import P2Policy, param_count  # noqa: E402


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
    ap.add_argument("--teachers", default=None,
                    help="comma-separated expert IDs; keep only rows where "
                         "the acting seat's expert is listed (ablation)")
    ap.add_argument("--out", default="results/v32_p2_bc.npz")
    ap.add_argument("--report", default="results/v32_p2_bc_report.json")
    args = ap.parse_args()
    torch.manual_seed(args.seed)
    np.random.seed(args.seed)

    vocab = json.load(open(os.path.join(REPO_ROOT, "results", "v32_p2_vocab.json")))
    norm = Normalizer.from_json(json.load(open(
        os.path.join(REPO_ROOT, "results", "v32_p2_norm.json"))))
    uvoc = [tuple(c) for c in vocab["unit_vocab"]]
    mvoc = [tuple(c) for c in vocab["market_vocab"]]
    uidx = {c: i for i, c in enumerate(uvoc)}
    midx = {c: i for i, c in enumerate(mvoc)}

    teachers = set(args.teachers.split(",")) if args.teachers else None
    tr_samples, va_samples = [], []
    for leg in load_legs(os.path.join(REPO_ROOT, "results", "v32_p2_bc_legs.jsonl")):
        store = va_samples if leg["seed"] in BC_VAL_SEEDS else tr_samples
        for side, expert in (("rows0", leg["left"]), ("rows1", leg["right"])):
            if teachers is not None and expert not in teachers:
                continue
            store.extend(build_samples(leg, leg[side], uidx, midx))
    print("train=%d val=%d" % (len(tr_samples), len(va_samples)), flush=True)
    assert all(t >= 0 for s in tr_samples + va_samples
               for t in s["u_targ"] + s["m_targ"]), "vocab miss (TEST 11)"

    F_tr = norm.transform([s["feat"] for s in tr_samples])
    F_va = norm.transform([s["feat"] for s in va_samples])

    model = P2Policy(F_tr.shape[1], 12, uvoc, mvoc, vocab["ops"], vocab["items"])
    print("params=%d" % param_count(model), flush=True)
    opt = torch.optim.Adam(model.parameters(), lr=args.lr)
    ce = nn.CrossEntropyLoss(reduction="none")

    def batchify(idxs, samples, F):
        B = len(idxs)
        U = max(len(samples[i]["uctx"]) for i in idxs)
        st = torch.tensor(F[idxs], dtype=torch.float32)
        uc = torch.zeros(B, U, 12)
        vv = torch.zeros(B, U, dtype=torch.bool)
        ut = torch.zeros(B, U, dtype=torch.long)
        for b, i in enumerate(idxs):
            s = samples[i]
            u = len(s["uctx"])
            uc[b, :u] = torch.tensor(np.asarray(s["uctx"]), dtype=torch.float32)
            vv[b, :u] = True
            ut[b, :u] = torch.tensor(s["u_targ"], dtype=torch.long)
        mt = torch.tensor([samples[i]["m_targ"] for i in idxs], dtype=torch.long)
        mk = torch.tensor([samples[i]["mask"] for i in idxs], dtype=torch.float32)
        return st, uc, vv, ut, mt, mk

    def metrics(idxs, samples, F):
        model.eval()
        tot = {"full": 0, "n": 0, "farmer": 0, "hands": 0, "hands_n": 0,
               "mkt": 0, "mkt_nn": 0, "mkt_nn_n": 0, "nll": 0.0}
        with torch.no_grad():
            for a in range(0, len(idxs), 4096):
                bidx = idxs[a:a + 4096]
                st, uc, vv, ut, mt, mk = batchify(bidx, samples, F)
                out = model(st, uc, vv, mk)
                pu = out["unit_logits"].argmax(-1)
                pm = out["market_logits"].argmax(-1)
                tot["n"] += len(bidx)
                tot["farmer"] += int(((pu[:, 0] == ut[:, 0]).sum()))
                hm = vv.clone()
                hm[:, 0] = False
                tot["hands"] += int(((pu == ut) & hm).sum())
                tot["hands_n"] += int(hm.sum())
                tot["mkt"] += int((pm == mt).sum())
                nnm = mt != midx[("NOOP", None, None)]
                tot["mkt_nn"] += int(((pm == mt) & nnm).sum())
                tot["mkt_nn_n"] += int(nnm.sum())
                full = ((pu == ut) | ~vv).all(1) & (pm == mt).all(1)
                tot["full"] += int(full.sum())
                tot["nll"] += float(
                    ce(out["unit_logits"][vv], ut[vv]).sum() +
                    ce(out["market_logits"].reshape(-1, len(mvoc)),
                       mt.reshape(-1)).sum())
        n = tot["n"]
        slots = n * 1 + tot["hands_n"] + n * 10
        return {"full_exact": tot["full"] / n, "farmer": tot["farmer"] / n,
                "hands": tot["hands"] / max(1, tot["hands_n"]),
                "market": tot["mkt"] / (n * 10),
                "market_nonnoop": tot["mkt_nn"] / max(1, tot["mkt_nn_n"]),
                "nll_per_slot": tot["nll"] / slots}

    N = len(tr_samples)
    best, best_state, since = -1.0, None, 0
    t0 = time.time()
    for ep in range(args.epochs):
        model.train()
        perm = np.random.permutation(N)
        for a in range(0, N, args.batch):
            bidx = perm[a:a + args.batch].tolist()
            st, uc, vv, ut, mt, mk = batchify(bidx, tr_samples, F_tr)
            out = model(st, uc, vv, mk)
            loss = (ce(out["unit_logits"][vv], ut[vv]).mean() +
                    ce(out["market_logits"].reshape(-1, len(mvoc)),
                       mt.reshape(-1)).mean())
            opt.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            opt.step()
        mv = metrics(list(range(len(va_samples))), va_samples, F_va)
        print("ep=%d val_full=%.3f farmer=%.3f hands=%.3f mkt=%.3f "
              "mkt_nn=%.3f nll=%.3f" % (ep, mv["full_exact"], mv["farmer"],
                                        mv["hands"], mv["market"],
                                        mv["market_nonnoop"],
                                        mv["nll_per_slot"]), flush=True)
        score = mv["full_exact"]
        if score > best + 1e-6:
            best, since = score, 0
            best_state = {k: v.detach().clone()
                          for k, v in model.state_dict().items()}
        else:
            since += 1
            if since >= 5:
                break
    model.load_state_dict(best_state)
    mv = metrics(list(range(len(va_samples))), va_samples, F_va)
    mt = metrics(list(range(N)), tr_samples, F_tr)
    meta = {"git": git_commit(), "epochs": args.epochs, "batch": args.batch,
            "lr": args.lr, "seed": args.seed, "params": param_count(model),
            "val": mv, "train": mt, "wall_sec": round(time.time() - t0, 1),
            "vocab_sha": hashlib.sha256(open(os.path.join(
                REPO_ROOT, "results", "v32_p2_vocab.json"), "rb").read()
            ).hexdigest()[:16]}
    meta["teachers"] = sorted(teachers) if teachers else "all"
    out = os.path.join(REPO_ROOT, args.out)
    np.savez(out, **{k: v.numpy() for k, v in best_state.items()},
             meta=json.dumps(meta, sort_keys=True, default=str))
    with open(os.path.join(REPO_ROOT, args.report), "w") as f:
        json.dump(meta, f, indent=1, sort_keys=True, default=str)
    print("wrote %s val_full=%.3f" % (out, mv["full_exact"]))


if __name__ == "__main__":
    main()
