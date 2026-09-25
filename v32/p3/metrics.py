# SPDX-License-Identifier: MIT
"""V32 P3 shared training utilities: batching, masked head losses, metrics."""

import numpy as np
import torch

from v32.p3 import codec as C
from v32.p3.models import M_ITEM_OPS, U_ARG_OPS, U_QTY_OPS


def batchify(idxs, samples, F):
    B = len(idxs)
    U = max(len(samples[i]["uctx"]) for i in idxs)
    st = torch.tensor(F[idxs], dtype=torch.float32)
    uc = torch.zeros(B, U, 12)
    vv = torch.zeros(B, U, dtype=torch.bool)
    uo = torch.zeros(B, U, dtype=torch.long)
    ua = torch.zeros(B, U, dtype=torch.long)
    uq = torch.zeros(B, U, dtype=torch.long)
    for b, i in enumerate(idxs):
        s = samples[i]
        u = len(s["uctx"])
        uc[b, :u] = torch.tensor(np.asarray(s["uctx"]), dtype=torch.float32)
        vv[b, :u] = True
        uo[b, :u] = torch.tensor(s["u_op"], dtype=torch.long)
        ua[b, :u] = torch.tensor(s["u_arg"], dtype=torch.long)
        uq[b, :u] = torch.tensor(s["u_qty"], dtype=torch.long)
    mo = torch.tensor([samples[i]["m_op"] for i in idxs], dtype=torch.long)
    mi = torch.tensor([samples[i]["m_item"] for i in idxs], dtype=torch.long)
    mq = torch.tensor([samples[i]["m_qty"] for i in idxs], dtype=torch.long)
    return {"state": st, "uctx": uc, "valid": vv, "u_op": uo,
            "u_arg": ua, "u_qty": uq, "m_op": mo, "m_item": mi,
            "m_qty": mq}


def _op_mask(targ, classes):
    m = torch.zeros_like(targ, dtype=torch.bool)
    for c in classes:
        m = m | (targ == c)
    return m


def head_losses(out, b, ce):
    """Masked CE per head (masking from TARGET ops); total = sum of 6 means."""
    vv = b["valid"]
    losses = {}
    losses["u_op"] = ce(out["u_op"][vv], b["u_op"][vv]).mean()
    ma = _op_mask(b["u_op"], U_ARG_OPS) & vv
    losses["u_arg"] = ce(out["u_arg"][ma], b["u_arg"][ma]).mean() \
        if ma.any() else out["u_op"].sum() * 0.0
    mq = _op_mask(b["u_op"], U_QTY_OPS) & vv
    losses["u_qty"] = ce(out["u_qty"][mq], b["u_qty"][mq]).mean() \
        if mq.any() else out["u_op"].sum() * 0.0
    losses["m_op"] = ce(out["m_op"].reshape(-1, len(C.M_OP)),
                         b["m_op"].reshape(-1)).mean()
    mm = _op_mask(b["m_op"], M_ITEM_OPS)
    losses["m_item"] = ce(out["m_item"][mm], b["m_item"][mm]).mean() \
        if mm.any() else out["u_op"].sum() * 0.0
    losses["m_qty"] = ce(out["m_qty"][mm], b["m_qty"][mm]).mean() \
        if mm.any() else out["u_op"].sum() * 0.0
    losses["total"] = sum(losses[k] for k in
                          ("u_op", "u_arg", "u_qty", "m_op", "m_item",
                           "m_qty"))
    return losses


@torch.no_grad()
def head_metrics(model, idxs, samples, F, chunk=4096, semantic=False):
    """Per-head accuracy + full-exact (+ full-semantic if asked)."""
    model.eval()
    tot = {"n": 0, "full": 0, "sem": 0, "u_op": 0, "u_n": 0,
           "farmer": 0, "u_arg": 0, "u_arg_n": 0, "u_qty": 0, "u_qty_n": 0,
           "m_op": 0, "m_item": 0, "m_qty": 0, "m_nn": 0,
           "m_op_nn": 0, "m_n": 0}
    for a in range(0, len(idxs), chunk):
        bidx = idxs[a:a + chunk]
        b = batchify(bidx, samples, F)
        out = model(b["state"], b["uctx"], b["valid"])
        pu = {k: out[k].argmax(-1) for k in
              ("u_op", "u_arg", "u_qty", "m_op", "m_item", "m_qty")}
        vv = b["valid"]
        tot["n"] += len(bidx)
        tot["u_op"] += int(((pu["u_op"] == b["u_op"]) & vv).sum())
        tot["u_n"] += int(vv.sum())
        tot["farmer"] += int((pu["u_op"][:, 0] == b["u_op"][:, 0]).sum())
        ma = _op_mask(b["u_op"], U_ARG_OPS) & vv
        tot["u_arg"] += int(((pu["u_arg"] == b["u_arg"]) & ma).sum())
        tot["u_arg_n"] += int(ma.sum())
        mq = _op_mask(b["u_op"], U_QTY_OPS) & vv
        tot["u_qty"] += int(((pu["u_qty"] == b["u_qty"]) & mq).sum())
        tot["u_qty_n"] += int(mq.sum())
        tot["m_op"] += int((pu["m_op"] == b["m_op"]).sum())
        tot["m_n"] += b["m_op"].numel()
        mm = _op_mask(b["m_op"], M_ITEM_OPS)
        tot["m_item"] += int(((pu["m_item"] == b["m_item"]) & mm).sum())
        tot["m_qty"] += int(((pu["m_qty"] == b["m_qty"]) & mm).sum())
        tot["m_nn"] += int(mm.sum())
        tot["m_op_nn"] += int(((pu["m_op"] == b["m_op"]) & mm).sum())
        full = (((pu["u_op"] == b["u_op"]) | ~vv).all(1)
                & ((pu["u_arg"] == b["u_arg"]) | ~ma).all(1)
                & ((pu["u_qty"] == b["u_qty"]) | ~mq).all(1)
                & (pu["m_op"] == b["m_op"]).all(1)
                & ((pu["m_item"] == b["m_item"]) | ~mm).all(1)
                & ((pu["m_qty"] == b["m_qty"]) | ~mm).all(1))
        tot["full"] += int(full.sum())
        if semantic:
            for r, i in enumerate(bidx):
                n_u = len(samples[i]["uctx"])
                pu_u = [(int(pu["u_op"][r, j]), int(pu["u_arg"][r, j]),
                         int(pu["u_qty"][r, j])) for j in range(n_u)]
                pu_m = [(int(pu["m_op"][r, s]), int(pu["m_item"][r, s]),
                         int(pu["m_qty"][r, s]))
                        for s in range(C.M_MARKET_SLOTS)]
                tu_u = list(zip(samples[i]["u_op"], samples[i]["u_arg"],
                                samples[i]["u_qty"]))
                tu_m = list(zip(samples[i]["m_op"], samples[i]["m_item"],
                                samples[i]["m_qty"]))
                if C.decode_action(pu_u, pu_m) == C.decode_action(tu_u, tu_m):
                    tot["sem"] += 1
    n = tot["n"]
    d = {"full_exact": tot["full"] / n, "u_op": tot["u_op"] / tot["u_n"],
         "farmer": tot["farmer"] / n,
         "u_arg": tot["u_arg"] / max(1, tot["u_arg_n"]),
         "u_qty": tot["u_qty"] / max(1, tot["u_qty_n"]),
         "m_op": tot["m_op"] / tot["m_n"],
         "m_item": tot["m_item"] / max(1, tot["m_nn"]),
         "m_qty": tot["m_qty"] / max(1, tot["m_nn"]),
         "m_op_nonnoop": tot["m_op_nn"] / max(1, tot["m_nn"])}
    if semantic:
        d["full_semantic"] = tot["sem"] / n
    return d
