# SPDX-License-Identifier: MIT
"""V32 P6 Training Harness: Targeted Farmer-Head Rebalancing (Arm 2).

Retains:
- Step 0 Critical Weighting (lambda_crit = 50.0) -> wash + farmer PASS
- Early Horizon Weighting (lambda_early = 10.0) -> steps 1-10 operations
Adds:
- Step 2 Targeted Farmer Rebalancing (lambda_s2 = 50.0) -> enforces farmer SOUTH

Mathematical formulation:
  L_total = L_unit + L_mkt + lambda_crit * L_crit_s0 + lambda_early * L_early_1_10 + lambda_s2 * L_s2_farmer
"""

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
import numpy as np
import torch
import torch.nn as nn

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, REPO_ROOT)

from v32.p2.dataset import BC_VAL_SEEDS, load_legs
from v32.p2.features import Normalizer
from v32.p3 import codec as C
from v32.p3.dataset import build_samples
from v32.p3.metrics import batchify, head_losses, head_metrics, _op_mask
from v32.p3.models import P3Policy, param_count, M_ITEM_OPS, U_ARG_OPS, U_QTY_OPS


def git_commit():
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO_ROOT,
                              capture_output=True, text=True).stdout.strip()
    except Exception:
        return "unknown"


def wash_shape_of(m_op, m_item, m_qty):
    b_idx = C._M_OP_ID["BUY_PRODUCT"]
    s_idx = C._M_OP_ID["SELL"]
    w_idx = C._M_ITEM_ID["WHEAT"]
    n = C.M_QTY[m_qty[0]]
    m = C.M_QTY[m_qty[1]]
    return (m_op[0] == b_idx and m_item[0] == w_idx and n > 0
            and m_op[1] == s_idx and m_item[1] == w_idx and m > 0)


@torch.no_grad()
def eval_early_probe(model, step0_samples, F_s0, early_samples, F_early):
    model.eval()
    # Step 0 probe
    b0 = batchify(list(range(len(step0_samples))), step0_samples, F_s0)
    out0 = model(b0["state"], b0["uctx"], b0["valid"])
    pu_uo = out0["u_op"].argmax(-1)
    pu_mo = out0["m_op"].argmax(-1)
    pu_mi = out0["m_item"].argmax(-1)
    pu_mq = out0["m_qty"].argmax(-1)

    n_wash = 0
    n_pass = 0
    for r, s in enumerate(step0_samples):
        wash = wash_shape_of(pu_mo[r].tolist(), pu_mi[r].tolist(), pu_mq[r].tolist())
        if wash:
            n_wash += 1
        if pu_uo[r, 0].item() == C._U_OP_ID["PASS"]:
            n_pass += 1

    # Step 1 probe
    s1_samples = [s for s in early_samples if s["step"] == 1]
    n_s1_north = 0
    n_s1_hire = 0
    if s1_samples:
        F_s1 = F_early[[i for i, s in enumerate(early_samples) if s["step"] == 1]]
        b1 = batchify(list(range(len(s1_samples))), s1_samples, F_s1)
        out1 = model(b1["state"], b1["uctx"], b1["valid"])
        p1_uo = out1["u_op"].argmax(-1)
        p1_mo = out1["m_op"].argmax(-1)
        for r in range(len(s1_samples)):
            if p1_uo[r, 0].item() == C._U_OP_ID["NORTH"]:
                n_s1_north += 1
            hires = sum(1 for sl in range(len(p1_mo[r])) if p1_mo[r, sl].item() == C._M_OP_ID["HIRE"])
            if hires >= 3:
                n_s1_hire += 1

    # Step 2 probe
    s2_samples = [s for s in early_samples if s["step"] == 2]
    n_s2_south = 0
    if s2_samples:
        F_s2 = F_early[[i for i, s in enumerate(early_samples) if s["step"] == 2]]
        b2 = batchify(list(range(len(s2_samples))), s2_samples, F_s2)
        out2 = model(b2["state"], b2["uctx"], b2["valid"])
        p2_uo = out2["u_op"].argmax(-1)
        for r in range(len(s2_samples)):
            if p2_uo[r, 0].item() == C._U_OP_ID["SOUTH"]:
                n_s2_south += 1

    return {
        "n_s0": len(step0_samples),
        "s0_wash": n_wash,
        "s0_pass": n_pass,
        "n_s1": len(s1_samples),
        "s1_north": n_s1_north,
        "s1_hire": n_s1_hire,
        "n_s2": len(s2_samples),
        "s2_south": n_s2_south,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--epochs", type=int, default=15)
    ap.add_argument("--lr", type=float, default=3e-4)
    ap.add_argument("--batch_size", type=int, default=128)
    ap.add_argument("--crit_weight", type=float, default=50.0)
    ap.add_argument("--early_weight", type=float, default=10.0)
    ap.add_argument("--s2_weight", type=float, default=50.0)
    ap.add_argument("--early_steps", type=int, default=10)
    ap.add_argument("--init_ckpt", default=None)
    ap.add_argument("--out", default=os.path.join(REPO_ROOT, "results", "v32_p6_arm2_rebalanced.npz"))
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    torch.manual_seed(args.seed)
    np.random.seed(args.seed)

    legs_path = os.path.join(REPO_ROOT, "results", "v32_p2_bc_legs.jsonl")
    norm = Normalizer.from_json(json.load(open(os.path.join(REPO_ROOT, "results", "v32_p2_norm.json"))))

    tr_samples = []
    va_samples = []
    all_step0 = []
    all_early = []

    for leg in load_legs(legs_path):
        is_val = leg["seed"] in BC_VAL_SEEDS
        for side, expert in (("rows0", leg["left"]), ("rows1", leg["right"])):
            samples = list(build_samples(leg, leg[side], expert))
            if is_val:
                va_samples.extend(samples)
            else:
                tr_samples.extend(samples)
            for s in samples:
                if s["step"] == 0:
                    all_step0.append(s)
                if 1 <= s["step"] <= args.early_steps:
                    all_early.append(s)

    print(f"Loaded dataset: {len(tr_samples)} train samples, {len(va_samples)} val samples")
    print(f"Probe samples: {len(all_step0)} step-0, {len(all_early)} early-horizon")

    F_tr = norm.transform(np.asarray([s["feat"] for s in tr_samples]))
    F_va = norm.transform(np.asarray([s["feat"] for s in va_samples]))
    F_s0 = norm.transform(np.asarray([s["feat"] for s in all_step0]))
    F_early = norm.transform(np.asarray([s["feat"] for s in all_early]))

    model = P3Policy(157, 12)
    if args.init_ckpt and os.path.exists(args.init_ckpt):
        print(f"Initializing from checkpoint: {args.init_ckpt}")
        d = np.load(args.init_ckpt, allow_pickle=True)
        model.load_state_dict({k: torch.tensor(v) for k, v in d.items() if k != "meta"})

    opt = torch.optim.Adam(model.parameters(), lr=args.lr)
    ce = nn.CrossEntropyLoss(reduction="none")

    best_score = -1.0
    best_weights = None
    curve = []

    print(f"Starting V32 P6 Arm 2 Training: epochs={args.epochs}, lr={args.lr}, "
          f"crit_wt={args.crit_weight}, early_wt={args.early_weight}, s2_wt={args.s2_weight}")

    for ep in range(1, args.epochs + 1):
        model.train()
        perm = np.random.permutation(len(tr_samples))
        t0 = time.time()
        ep_loss_unit = 0.0
        ep_loss_mkt = 0.0
        ep_loss_crit = 0.0
        ep_loss_early = 0.0
        ep_loss_s2 = 0.0
        n_batches = 0

        for start in range(0, len(tr_samples), args.batch_size):
            bidx = perm[start:start + args.batch_size].tolist()
            b = batchify(bidx, tr_samples, F_tr)
            out = model(b["state"], b["uctx"], b["valid"])

            # Base market loss
            loss_m_op = ce(out["m_op"].reshape(-1, len(C.M_OP)), b["m_op"].reshape(-1)).mean()
            mm = _op_mask(b["m_op"], M_ITEM_OPS)
            loss_m_item = ce(out["m_item"][mm], b["m_item"][mm]).mean() if mm.any() else out["m_op"].sum() * 0.0
            loss_m_qty = ce(out["m_qty"][mm], b["m_qty"][mm]).mean() if mm.any() else out["m_op"].sum() * 0.0
            L_mkt = loss_m_op + loss_m_item + loss_m_qty

            # Base unit loss
            vv = b["valid"]
            loss_u_op = ce(out["u_op"][vv], b["u_op"][vv]).mean()
            ma = _op_mask(b["u_op"], U_ARG_OPS) & vv
            loss_u_arg = ce(out["u_arg"][ma], b["u_arg"][ma]).mean() if ma.any() else out["u_op"].sum() * 0.0
            mq = _op_mask(b["u_op"], U_QTY_OPS) & vv
            loss_u_qty = ce(out["u_qty"][mq], b["u_qty"][mq]).mean() if mq.any() else out["u_op"].sum() * 0.0
            L_unit = loss_u_op + loss_u_arg + loss_u_qty

            # Step 0 Critical Loss
            L_crit = torch.tensor(0.0, device=out["m_op"].device)
            is_s0 = torch.tensor([tr_samples[i]["step"] == 0 for i in bidx], dtype=torch.bool)
            if is_s0.any() and args.crit_weight > 0.0:
                s0_u_op = ce(out["u_op"][is_s0, 0], b["u_op"][is_s0, 0]).mean()
                s0_m_op = ce(out["m_op"][is_s0].reshape(-1, len(C.M_OP)), b["m_op"][is_s0].reshape(-1)).mean()
                s0_mm = _op_mask(b["m_op"][is_s0], M_ITEM_OPS)
                s0_m_item = ce(out["m_item"][is_s0][s0_mm], b["m_item"][is_s0][s0_mm]).mean() if s0_mm.any() else 0.0
                s0_m_qty = ce(out["m_qty"][is_s0][s0_mm], b["m_qty"][is_s0][s0_mm]).mean() if s0_mm.any() else 0.0
                L_crit = s0_u_op + s0_m_op + s0_m_item + s0_m_qty

            # Bounded Early-Horizon Loss
            L_early = torch.tensor(0.0, device=out["m_op"].device)
            is_early = torch.tensor([1 <= tr_samples[i]["step"] <= args.early_steps for i in bidx], dtype=torch.bool)
            if is_early.any() and args.early_weight > 0.0:
                e_vv = vv[is_early]
                e_u_op = ce(out["u_op"][is_early][e_vv], b["u_op"][is_early][e_vv]).mean()
                e_m_op = ce(out["m_op"][is_early].reshape(-1, len(C.M_OP)), b["m_op"][is_early].reshape(-1)).mean()
                e_mm = _op_mask(b["m_op"][is_early], M_ITEM_OPS)
                e_m_item = ce(out["m_item"][is_early][e_mm], b["m_item"][is_early][e_mm]).mean() if e_mm.any() else 0.0
                e_m_qty = ce(out["m_qty"][is_early][e_mm], b["m_qty"][is_early][e_mm]).mean() if e_mm.any() else 0.0
                L_early = e_u_op + e_m_op + e_m_item + e_m_qty

            # Step 2 Farmer SOUTH Loss
            L_s2 = torch.tensor(0.0, device=out["m_op"].device)
            is_s2 = torch.tensor([tr_samples[i]["step"] == 2 for i in bidx], dtype=torch.bool)
            if is_s2.any() and args.s2_weight > 0.0:
                s2_u_op = ce(out["u_op"][is_s2, 0], b["u_op"][is_s2, 0]).mean()
                L_s2 = s2_u_op

            loss = L_unit + L_mkt + args.crit_weight * L_crit + args.early_weight * L_early + args.s2_weight * L_s2

            opt.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            opt.step()

            ep_loss_unit += L_unit.item()
            ep_loss_mkt += L_mkt.item()
            ep_loss_crit += L_crit.item()
            ep_loss_early += L_early.item()
            ep_loss_s2 += L_s2.item()
            n_batches += 1

        mv = head_metrics(model, list(range(len(va_samples))), va_samples, F_va, semantic=True)
        probe = eval_early_probe(model, all_step0, F_s0, all_early, F_early)

        print(f"ep={ep:2d} val_full={mv['full_exact']:.3f} farmer={mv['farmer']:.3f} | "
              f"S0: Wash={probe['s0_wash']}/{probe['n_s0']} Pass={probe['s0_pass']}/{probe['n_s0']} | "
              f"S1: North={probe['s1_north']}/{probe['n_s1']} Hire={probe['s1_hire']}/{probe['n_s1']} | "
              f"S2: South={probe['s2_south']}/{probe['n_s2']}", flush=True)

        score = (probe["s0_wash"] == probe["n_s0"] and probe["s0_pass"] == probe["n_s0"]) * 1000.0 + \
                probe["s1_north"] * 2.0 + probe["s1_hire"] * 2.0 + probe["s2_south"] * 5.0 + mv["full_exact"]

        if score > best_score:
            best_score = score
            best_weights = {k: v.cpu().numpy() for k, v in model.state_dict().items()}
            best_weights["meta"] = {
                "epoch": ep,
                "commit": git_commit(),
                "score": float(best_score),
                "val_full_exact": float(mv["full_exact"]),
                "probe": probe,
            }
            np.savez_compressed(args.out, **best_weights)

    print(f"Training complete. Best score: {best_score:.3f}. Saved to {args.out}")


if __name__ == "__main__":
    main()
