# SPDX-License-Identifier: MIT
"""V32 P3 step-0 wash probe (G3).

Mode 1 (probe, default): train P3Policy on step-0 samples ONLY — single-teacher
A7 (60 near-identical inputs, 1 wash label) then mixture (240 inputs, 4 wash
labels). P2 precedent: pointer head never memorized 60 identical samples
(argmax all-NO-OP). Pass = wash shape reproduced; mixture mode additionally
diagnoses the 4-teacher label conflict.

Mode 2 (--ckpt): evaluate a trained checkpoint's argmax on all 240 step-0
samples: wash-shape rate + per-teacher exact-literal match matrix.

Writes results/v32_p3_step0_report.json.
"""

import json
import os
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, REPO_ROOT)

import numpy as np
import torch
import torch.nn as nn

from v32.p2.dataset import load_legs  # noqa: E402
from v32.p2.features import Normalizer  # noqa: E402
from v32.p3 import codec as C  # noqa: E402
from v32.p3.dataset import build_samples  # noqa: E402
from v32.p3.metrics import batchify, head_losses, head_metrics  # noqa: E402
from v32.p3.models import P3Policy  # noqa: E402


def load_step0():
    out = []
    for leg in load_legs(os.path.join(REPO_ROOT, "results",
                                      "v32_p2_bc_legs.jsonl")):
        for side, expert in (("rows0", leg["left"]), ("rows1", leg["right"])):
            for s in build_samples(leg, leg[side], expert):
                if s["step"] == 0:
                    out.append(s)
    return out


def wash_shape_of(m_op, m_item, m_qty):
    """True iff slots 0-1 are [BUY_PRODUCT,WHEAT,n>0],[SELL,WHEAT,m>0]."""
    b_idx = C._M_OP_ID["BUY_PRODUCT"]
    s_idx = C._M_OP_ID["SELL"]
    w_idx = C._M_ITEM_ID["WHEAT"]
    n = C.M_QTY[m_qty[0]]
    m = C.M_QTY[m_qty[1]]
    return (m_op[0] == b_idx and m_item[0] == w_idx and n > 0
            and m_op[1] == s_idx and m_item[1] == w_idx and m > 0)


@torch.no_grad()
def eval_step0(model, idxs, samples, F):
    model.eval()
    b = batchify(idxs, samples, F)
    out = model(b["state"], b["uctx"], b["valid"])
    pu = {k: out[k].argmax(-1).tolist() for k in
          ("m_op", "m_item", "m_qty", "u_op")}
    rows = []
    for r, i in enumerate(idxs):
        s = samples[i]
        pred_m = ([pu["m_op"][r][j] for j in range(10)],
                  [pu["m_item"][r][j] for j in range(10)],
                  [pu["m_qty"][r][j] for j in range(10)])
        wash = wash_shape_of(*pred_m)
        # exact = decoded market literals equal (don't-care item/qty on
        # NOOP slots cannot mismatch; this is the executable-object metric)
        exact = all(
            C.decode_market(pred_m[0][j], pred_m[1][j], pred_m[2][j])
            == C.decode_market(s["m_op"][j], s["m_item"][j], s["m_qty"][j])
            for j in range(10))
        lit = C.decode_market(pred_m[0][0], pred_m[1][0], pred_m[2][0])
        lit1 = C.decode_market(pred_m[0][1], pred_m[1][1], pred_m[2][1])
        rows.append({"teacher": s["teacher"], "seed": s["seed"],
                     "wash": wash, "exact": exact,
                     "pred_m0": lit, "pred_m1": lit1})
    return rows


def summarize(rows):
    by_teacher = {}
    for t in sorted(set(r["teacher"] for r in rows)):
        tr = [r for r in rows if r["teacher"] == t]
        by_teacher[t] = {"n": len(tr),
                         "wash": sum(r["wash"] for r in tr),
                         "exact": sum(r["exact"] for r in tr)}
    return {"n": len(rows), "wash": sum(r["wash"] for r in rows),
            "exact": sum(r["exact"] for r in rows),
            "by_teacher": by_teacher}


def probe(idxs, samples, F, epochs, tag):
    torch.manual_seed(0)
    np.random.seed(0)
    model = P3Policy()
    opt = torch.optim.Adam(model.parameters(), lr=3e-4)
    ce = nn.CrossEntropyLoss(reduction="none")
    curve = []
    N = len(idxs)
    for ep in range(epochs):
        model.train()
        perm = np.random.permutation(N)
        for a in range(0, N, 64):
            bidx = [idxs[i] for i in perm[a:a + 64].tolist()]
            b = batchify(bidx, samples, F)
            loss = head_losses(model(b["state"], b["uctx"], b["valid"]), b,
                               ce)["total"]
            opt.zero_grad()
            loss.backward()
            opt.step()
        if ep % 25 == 0 or ep == epochs - 1:
            m = head_metrics(model, idxs, samples, F, semantic=True)
            rows = eval_step0(model, idxs, samples, F)
            sm = summarize(rows)
            curve.append({"ep": ep, "full": m["full_exact"], **sm})
            print("%s ep=%d full=%.3f wash=%d/%d exact=%d/%d" % (
                tag, ep, m["full_exact"], sm["wash"], sm["n"], sm["exact"],
                sm["n"]), flush=True)
    return {"curve": curve, "final": summarize(
        eval_step0(model, idxs, samples, F)),
        "final_rows": eval_step0(model, idxs, samples, F)}


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--epochs", type=int, default=150)
    ap.add_argument("--ckpt", default=None)
    ap.add_argument("--out", default="results/v32_p3_step0_report.json")
    args = ap.parse_args()
    samples = load_step0()
    print("step0 samples=%d" % len(samples), flush=True)
    assert len(samples) == 240, len(samples)
    norm = Normalizer.from_json(json.load(open(os.path.join(
        REPO_ROOT, "results", "v32_p2_norm.json"))))
    F = norm.transform([s["feat"] for s in samples])
    rep = {}
    if args.ckpt:
        import torch as _t
        d = np.load(os.path.join(REPO_ROOT, args.ckpt), allow_pickle=True)
        model = P3Policy()
        model.load_state_dict({k: _t.tensor(v) for k, v in d.items()
                               if k != "meta"})
        model.eval()
        rows = eval_step0(model, list(range(len(samples))), samples, F)
        rep["ckpt_eval"] = {"ckpt": args.ckpt, **summarize(rows),
                            "rows": rows}
        print("ckpt %s: wash=%d/240 exact=%d/240" % (
            args.ckpt, rep["ckpt_eval"]["wash"], rep["ckpt_eval"]["exact"]))
        for t, v in rep["ckpt_eval"]["by_teacher"].items():
            print("  %s: wash=%d/%d exact=%d/%d" % (t, v["wash"], v["n"],
                                                    v["exact"], v["n"]))
    else:
        a7 = [i for i, s in enumerate(samples) if s["teacher"] == "E2_A7"]
        rep["a7_probe"] = probe(a7, samples, F, args.epochs, "a7")
        rep["mixture_probe"] = probe(list(range(len(samples))), samples, F,
                                     args.epochs, "mix")
    with open(os.path.join(REPO_ROOT, args.out), "w") as f:
        json.dump(rep, f, indent=1, sort_keys=True, default=str)
    print("wrote %s" % args.out)


if __name__ == "__main__":
    main()
