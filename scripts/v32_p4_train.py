# SPDX-License-Identifier: MIT
"""V32 P4 Training Harness: Critical-Pattern Balanced BC & Market Pretraining / Freeze.

Implements P4 experimental arms under frozen P3 architecture (P3Policy, 277k params):
  Arm 0: Frozen baseline replication
  Arm 1: Critical-pattern balanced BC (L_joint + lambda_crit * L_crit)
  Arm 2: Market pretraining (L_mkt only on full dataset)
  Arm 3: Market-frozen joint BC (init from Arm 2, freeze market heads, train unit)
  Arm 4: Market-initialized, jointly unfrozen (init from Arm 2, all trainable)

Logs per epoch:
  - Step-0 wash shape rate (n/240) and per-teacher exact match
  - Slot 0 and Slot 1 probabilities
  - Standard validation metrics on all heads (masked CE accuracy)
  - Gradient norms (unit, market, trunk)
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
def eval_step0_probe(model, step0_samples, F_s0):
    model.eval()
    b = batchify(list(range(len(step0_samples))), step0_samples, F_s0)
    out = model(b["state"], b["uctx"], b["valid"])
    pu_mo = out["m_op"].argmax(-1)
    pu_mi = out["m_item"].argmax(-1)
    pu_mq = out["m_qty"].argmax(-1)
    
    n_wash = 0
    n_exact = 0
    by_teacher = {}
    for r, s in enumerate(step0_samples):
        pred_m = (pu_mo[r].tolist(), pu_mi[r].tolist(), pu_mq[r].tolist())
        wash = wash_shape_of(pred_m[0], pred_m[1], pred_m[2])
        exact = all(
            C.decode_market(pred_m[0][j], pred_m[1][j], pred_m[2][j])
            == C.decode_market(s["m_op"][j], s["m_item"][j], s["m_qty"][j])
            for j in range(10)
        )
        if wash:
            n_wash += 1
        if exact:
            n_exact += 1
        t = s["teacher"]
        if t not in by_teacher:
            by_teacher[t] = {"n": 0, "wash": 0, "exact": 0}
        by_teacher[t]["n"] += 1
        if wash:
            by_teacher[t]["wash"] += 1
        if exact:
            by_teacher[t]["exact"] += 1
            
    p_s0 = out["m_op"].softmax(-1)
    s0_p_buy = float(p_s0[:, 0, C._M_OP_ID["BUY_PRODUCT"]].mean())
    s0_p_sell = float(p_s0[:, 0, C._M_OP_ID["SELL"]].mean())
    s1_p_buy = float(p_s0[:, 1, C._M_OP_ID["BUY_PRODUCT"]].mean())
    s1_p_sell = float(p_s0[:, 1, C._M_OP_ID["SELL"]].mean())
    
    return {
        "n": len(step0_samples),
        "wash": n_wash,
        "exact": n_exact,
        "s0_p_buy": s0_p_buy,
        "s0_p_sell": s0_p_sell,
        "s1_p_buy": s1_p_buy,
        "s1_p_sell": s1_p_sell,
        "pred_m0": C.decode_market(pred_m[0][0], pred_m[1][0], pred_m[2][0]),
        "pred_m1": C.decode_market(pred_m[0][1], pred_m[1][1], pred_m[2][1]),
        "by_teacher": by_teacher
    }

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", choices=["baseline", "arm1_balanced", "arm2_mkt_pretrain",
                                     "arm3_mkt_frozen", "arm4_mkt_unfrozen"], required=True)
    ap.add_argument("--epochs", type=int, default=30)
    ap.add_argument("--batch", type=int, default=1024)
    ap.add_argument("--lr", type=float, default=3e-3)
    ap.add_argument("--crit-weight", type=float, default=50.0)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--init-mkt", default=None, help="Checkpoint to initialize market head from")
    ap.add_argument("--freeze-mkt", action="store_true", help="Freeze market heads and slot_emb")
    ap.add_argument("--out", required=True)
    ap.add_argument("--report", required=True)
    args = ap.parse_args()

    torch.manual_seed(args.seed)
    np.random.seed(args.seed)

    print(f"=== LAUNCHING V32 P4: {args.arm} ===", flush=True)
    print(f"Config: epochs={args.epochs} lr={args.lr} batch={args.batch} crit_weight={args.crit_weight}", flush=True)

    norm = Normalizer.from_json(json.load(open(os.path.join(REPO_ROOT, "results", "v32_p2_norm.json"))))
    legs_path = os.path.join(REPO_ROOT, "results", "v32_p2_bc_legs.jsonl")
    tr_samples, va_samples, all_step0 = [], [], []

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

    print(f"Loaded: train={len(tr_samples)} val={len(va_samples)} step0_total={len(all_step0)}", flush=True)
    F_tr = norm.transform([s["feat"] for s in tr_samples])
    F_va = norm.transform([s["feat"] for s in va_samples])
    F_s0 = norm.transform([s["feat"] for s in all_step0])

    model = P3Policy(F_tr.shape[1], 12)

    # Initialize from market checkpoint if requested
    if args.init_mkt:
        init_path = os.path.join(REPO_ROOT, args.init_mkt)
        print(f"Initializing market heads from {init_path}", flush=True)
        mkt_d = np.load(init_path, allow_pickle=True)
        sd = model.state_dict()
        loaded = 0
        for k, v in mkt_d.items():
            if k in sd and any(h in k for h in ("m_op", "m_item", "m_qty", "slot_emb", "trunk")):
                sd[k] = torch.tensor(v)
                loaded += 1
        model.load_state_dict(sd)
        print(f"Loaded {loaded} parameter tensors from {args.init_mkt}", flush=True)

    # Freeze market heads if requested
    if args.freeze_mkt:
        print("Freezing market heads (m_op, m_item, m_qty, slot_emb)", flush=True)
        for name, param in model.named_parameters():
            if any(h in name for h in ("m_op", "m_item", "m_qty", "slot_emb")):
                param.requires_grad = False
                print(f"  Frozen: {name}", flush=True)

    trainable_params = [p for p in model.parameters() if p.requires_grad]
    print(f"Total params: {param_count(model)}, Trainable: {sum(p.numel() for p in trainable_params)}", flush=True)
    opt = torch.optim.Adam(trainable_params, lr=args.lr)
    ce = nn.CrossEntropyLoss(reduction="none")

    N = len(tr_samples)
    best_wash, best_val_full = -1, -1.0
    best_state = None
    curve = []
    t0 = time.time()

    for ep in range(args.epochs):
        model.train()
        perm = np.random.permutation(N)
        ep_loss_unit, ep_loss_mkt, ep_loss_crit = 0.0, 0.0, 0.0
        n_batches = 0

        for a in range(0, N, args.batch):
            bidx = perm[a:a + args.batch].tolist()
            b = batchify(bidx, tr_samples, F_tr)
            out = model(b["state"], b["uctx"], b["valid"])

            # Market loss
            loss_m_op = ce(out["m_op"].reshape(-1, len(C.M_OP)), b["m_op"].reshape(-1)).mean()
            mm = _op_mask(b["m_op"], M_ITEM_OPS)
            loss_m_item = ce(out["m_item"][mm], b["m_item"][mm]).mean() if mm.any() else out["m_op"].sum() * 0.0
            loss_m_qty = ce(out["m_qty"][mm], b["m_qty"][mm]).mean() if mm.any() else out["m_op"].sum() * 0.0
            L_mkt = loss_m_op + loss_m_item + loss_m_qty

            # Unit loss
            vv = b["valid"]
            loss_u_op = ce(out["u_op"][vv], b["u_op"][vv]).mean()
            ma = _op_mask(b["u_op"], U_ARG_OPS) & vv
            loss_u_arg = ce(out["u_arg"][ma], b["u_arg"][ma]).mean() if ma.any() else out["u_op"].sum() * 0.0
            mq = _op_mask(b["u_op"], U_QTY_OPS) & vv
            loss_u_qty = ce(out["u_qty"][mq], b["u_qty"][mq]).mean() if mq.any() else out["u_op"].sum() * 0.0
            L_unit = loss_u_op + loss_u_arg + loss_u_qty

            # Critical loss
            L_crit = torch.tensor(0.0, device=out["m_op"].device)
            if args.arm in ("arm1_balanced", "arm2_mkt_pretrain") and args.crit_weight > 0.0:
                is_s0 = torch.tensor([tr_samples[i]["step"] == 0 for i in bidx], dtype=torch.bool)
                if is_s0.any():
                    s0_m_op = ce(out["m_op"][is_s0].reshape(-1, len(C.M_OP)), b["m_op"][is_s0].reshape(-1)).mean()
                    s0_mm = _op_mask(b["m_op"][is_s0], M_ITEM_OPS)
                    s0_m_item = ce(out["m_item"][is_s0][s0_mm], b["m_item"][is_s0][s0_mm]).mean() if s0_mm.any() else 0.0
                    s0_m_qty = ce(out["m_qty"][is_s0][s0_mm], b["m_qty"][is_s0][s0_mm]).mean() if s0_mm.any() else 0.0
                    L_crit = s0_m_op + s0_m_item + s0_m_qty

            if args.arm == "arm2_mkt_pretrain":
                loss = L_mkt + args.crit_weight * L_crit
            elif args.arm == "arm3_mkt_frozen":
                loss = L_unit
            elif args.arm == "arm1_balanced":
                loss = L_unit + L_mkt + args.crit_weight * L_crit
            else: # baseline or arm4
                loss = L_unit + L_mkt

            opt.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(trainable_params, 1.0)
            opt.step()

            ep_loss_unit += L_unit.item()
            ep_loss_mkt += L_mkt.item()
            ep_loss_crit += L_crit.item()
            n_batches += 1

        # Per-epoch validation and step-0 diagnostics
        mv = head_metrics(model, list(range(len(va_samples))), va_samples, F_va, semantic=True)
        s0_diag = eval_step0_probe(model, all_step0, F_s0)
        
        ep_rec = {
            "ep": ep,
            "loss_unit": ep_loss_unit / n_batches,
            "loss_mkt": ep_loss_mkt / n_batches,
            "loss_crit": ep_loss_crit / n_batches,
            **mv,
            **s0_diag
        }
        curve.append(ep_rec)

        print(f"ep={ep:2d} val_full={mv['full_exact']:.3f} farmer={mv['farmer']:.3f} uop={mv['u_op']:.3f} "
              f"mop={mv['m_op']:.3f} mop_nn={mv['m_op_nonnoop']:.3f} | "
              f"Step0: Wash={s0_diag['wash']}/240 exact={s0_diag['exact']}/240 "
              f"M0={s0_diag['pred_m0']} M1={s0_diag['pred_m1']} "
              f"S0_P(B)={s0_diag['s0_p_buy']:.2f} S0_P(S)={s0_diag['s0_p_sell']:.2f}",
              flush=True)

        # Decision criterion for saving:
        # For P4, recovering the wash is a required gate, alongside global validation accuracy
        score = s0_diag["wash"] * 1000 + mv["full_exact"]
        if score > best_wash:
            best_wash = score
            best_state = {k: v.detach().clone() for k, v in model.state_dict().items()}

    # Save best checkpoint
    model.load_state_dict(best_state)
    final_mv = head_metrics(model, list(range(len(va_samples))), va_samples, F_va, semantic=True)
    final_s0 = eval_step0_probe(model, all_step0, F_s0)

    meta = {
        "git": git_commit(),
        "arch": "v32p3-a1",
        "arm": args.arm,
        "epochs": args.epochs,
        "batch": args.batch,
        "lr": args.lr,
        "crit_weight": args.crit_weight,
        "seed": args.seed,
        "init_mkt": args.init_mkt,
        "freeze_mkt": args.freeze_mkt,
        "params": param_count(model),
        "val": final_mv,
        "step0": final_s0,
        "curve": curve,
        "wall_sec": round(time.time() - t0, 1),
    }

    out_npz = os.path.join(REPO_ROOT, args.out)
    np.savez(out_npz, **{k: v.numpy() for k, v in best_state.items()},
             meta=json.dumps(meta, sort_keys=True, default=str))
    
    out_rep = os.path.join(REPO_ROOT, args.report)
    with open(out_rep, "w") as f:
        json.dump(meta, f, indent=1, sort_keys=True, default=str)

    print(f"WROTE {out_npz} & {out_rep}", flush=True)
    print(f"FINAL: Wash={final_s0['wash']}/240 exact={final_s0['exact']}/240 val_full={final_mv['full_exact']:.3f}", flush=True)

if __name__ == "__main__":
    main()
