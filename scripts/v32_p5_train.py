# SPDX-License-Identifier: MIT
"""V32 P5 Training Harness: Bounded Early-Horizon Weighted BC (Arm 2).

Retains P4 critical market weighting (lambda_crit = 50.0) and adds:
1. Step-0 Unit Protection: includes farmer unit head in L_crit (enforces PASS)
2. Bounded Early-Horizon Weighting: weights steps 1-10 with lambda_early = 10.0
   covering both unit operations and market hiring/livestock operations.

Mathematical formulation:
  L_total = L_unit + L_mkt + lambda_crit * L_crit_s0 + lambda_early * L_early_1_10

Where:
  L_crit_s0 = s0_u_op + s0_m_op + s0_m_item + s0_m_qty
  L_early_1_10 = early_u_op + early_u_arg + early_u_qty + early_m_op + early_m_item + early_m_qty
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
            # Check if hire is predicted in market slots 2..6
            hires = sum(1 for sl in range(len(p1_mo[r])) if p1_mo[r, sl].item() == C._M_OP_ID["HIRE"])
            if hires >= 3:
                n_s1_hire += 1
                
    return {
        "n_s0": len(step0_samples),
        "s0_wash": n_wash,
        "s0_pass": n_pass,
        "n_s1": len(s1_samples),
        "s1_north": n_s1_north,
        "s1_hire": n_s1_hire,
    }

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", default="arm2_early_weighting")
    ap.add_argument("--epochs", type=int, default=30)
    ap.add_argument("--batch", type=int, default=1024)
    ap.add_argument("--lr", type=float, default=3e-3)
    ap.add_argument("--crit-weight", type=float, default=50.0)
    ap.add_argument("--early-weight", type=float, default=10.0)
    ap.add_argument("--early-steps", type=int, default=10)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", required=True)
    ap.add_argument("--report", required=True)
    args = ap.parse_args()

    torch.manual_seed(args.seed)
    np.random.seed(args.seed)

    print(f"=== TRAINING V32 P5 ARM 2: BOUNDED EARLY-HORIZON WEIGHTING ===")
    print(f"Params: lr={args.lr}, crit_weight={args.crit_weight}, early_weight={args.early_weight}, early_steps={args.early_steps}, batch={args.batch}")

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
    print(f"Probe samples: {len(all_step0)} step-0 samples, {len(all_early)} early-horizon samples")

    F_tr = norm.transform([s["feat"] for s in tr_samples])
    F_va = norm.transform([s["feat"] for s in va_samples])
    F_s0 = norm.transform([s["feat"] for s in all_step0])
    F_early = norm.transform([s["feat"] for s in all_early])

    model = P3Policy(157, 12)
    opt = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=1e-4)
    ce = nn.CrossEntropyLoss(reduction="none")

    best_score = -1.0
    curve = []
    t0 = time.time()

    for ep in range(1, args.epochs + 1):
        model.train()
        perm = np.random.permutation(len(tr_samples))
        n_batches = 0
        ep_loss_unit = 0.0
        ep_loss_mkt = 0.0
        ep_loss_crit = 0.0
        ep_loss_early = 0.0

        for start in range(0, len(tr_samples), args.batch):
            bidx = perm[start:start + args.batch]
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

            # Step 0 Critical Loss (both market wash AND farmer PASS)
            L_crit = torch.tensor(0.0, device=out["m_op"].device)
            is_s0 = torch.tensor([tr_samples[i]["step"] == 0 for i in bidx], dtype=torch.bool)
            if is_s0.any() and args.crit_weight > 0.0:
                # Step 0 farmer unit op (must be PASS)
                s0_u_op = ce(out["u_op"][is_s0, 0], b["u_op"][is_s0, 0]).mean()
                # Step 0 market wash
                s0_m_op = ce(out["m_op"][is_s0].reshape(-1, len(C.M_OP)), b["m_op"][is_s0].reshape(-1)).mean()
                s0_mm = _op_mask(b["m_op"][is_s0], M_ITEM_OPS)
                s0_m_item = ce(out["m_item"][is_s0][s0_mm], b["m_item"][is_s0][s0_mm]).mean() if s0_mm.any() else 0.0
                s0_m_qty = ce(out["m_qty"][is_s0][s0_mm], b["m_qty"][is_s0][s0_mm]).mean() if s0_mm.any() else 0.0
                L_crit = s0_u_op + s0_m_op + s0_m_item + s0_m_qty

            # Bounded Early-Horizon Loss (steps 1 to early_steps)
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

            loss = L_unit + L_mkt + args.crit_weight * L_crit + args.early_weight * L_early

            opt.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            opt.step()

            ep_loss_unit += L_unit.item()
            ep_loss_mkt += L_mkt.item()
            ep_loss_crit += L_crit.item()
            ep_loss_early += L_early.item()
            n_batches += 1

        # Per-epoch validation
        mv = head_metrics(model, list(range(len(va_samples))), va_samples, F_va, semantic=True)
        probe = eval_early_probe(model, all_step0, F_s0, all_early, F_early)

        ep_rec = {
            "ep": ep,
            "loss_unit": ep_loss_unit / n_batches,
            "loss_mkt": ep_loss_mkt / n_batches,
            "loss_crit": ep_loss_crit / n_batches,
            "loss_early": ep_loss_early / n_batches,
            **mv,
            **probe,
        }
        curve.append(ep_rec)

        print(f"ep={ep:2d} val_full={mv['full_exact']:.3f} farmer={mv['farmer']:.3f} uop={mv['u_op']:.3f} "
              f"mop={mv['m_op']:.3f} | S0: Wash={probe['s0_wash']}/{probe['n_s0']} Pass={probe['s0_pass']}/{probe['n_s0']} | "
              f"S1: North={probe['s1_north']}/{probe['n_s1']} Hire={probe['s1_hire']}/{probe['n_s1']}", flush=True)

        # Composite score prioritizing step 0 correctness + step 1 correctness + global validation
        score = (probe["s0_wash"] == probe["n_s0"] and probe["s0_pass"] == probe["n_s0"]) * 1000.0 + \
                probe["s1_north"] * 2.0 + probe["s1_hire"] * 2.0 + mv["full_exact"]
        if score > best_score:
            best_score = score
            meta = {
                "arm": args.arm,
                "epochs": args.epochs,
                "batch": args.batch,
                "lr": args.lr,
                "crit_weight": args.crit_weight,
                "early_weight": args.early_weight,
                "early_steps": args.early_steps,
                "seed": args.seed,
                "git_commit": git_commit(),
                "val": mv,
                "probe": probe,
                "wall_sec": time.time() - t0,
            }
            state_dict = {k: v.cpu().numpy() for k, v in model.state_dict().items()}
            state_dict["meta"] = np.array(json.dumps(meta))
            np.savez_compressed(args.out, **state_dict)

    with open(args.report, "w") as f:
        json.dump(curve, f, indent=2)
    print(f"Training completed in {time.time()-t0:.1f}s. Checkpoint saved to {args.out}")

if __name__ == "__main__":
    main()
