# SPDX-License-Identifier: MIT
"""V32 P4 Pilot Diagnostic:
Tests whether market-only training on the full 138k dataset learns the wash,
and tests critical-weighting lambda values.
"""

import json
import os
import sys
import numpy as np
import torch
import torch.nn as nn

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, REPO_ROOT)

from v32.p2.dataset import BC_VAL_SEEDS, load_legs
from v32.p2.features import Normalizer
from v32.p3 import codec as C
from v32.p3.dataset import build_samples
from v32.p3.metrics import batchify, _op_mask
from v32.p3.models import P3Policy, M_ITEM_OPS, U_ARG_OPS, U_QTY_OPS

def run_pilot():
    norm = Normalizer.from_json(json.load(open(os.path.join(REPO_ROOT, "results", "v32_p2_norm.json"))))
    legs_path = os.path.join(REPO_ROOT, "results", "v32_p2_bc_legs.jsonl")
    tr_samples, va_samples = [], []
    all_step0 = []
    
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
                    
    F_tr = norm.transform([s["feat"] for s in tr_samples])
    F_s0 = norm.transform([s["feat"] for s in all_step0])
    b_s0 = batchify(list(range(len(all_step0))), all_step0, F_s0)

    ce = nn.CrossEntropyLoss(reduction="none")
    N = len(tr_samples)
    print(f"Step-0 in train: {sum(1 for s in tr_samples if s['step'] == 0)}", flush=True)

    for cond_name, use_market_only, crit_weight in [
        ("Cond 2: Joint + lambda_crit=50", False, 50.0),
        ("Cond 3: Joint + lambda_crit=100", False, 100.0),
    ]:
        print(f"\n=== Testing {cond_name} ===", flush=True)
        torch.manual_seed(0)
        np.random.seed(0)
        model = P3Policy(F_tr.shape[1], 12)
        opt = torch.optim.Adam(model.parameters(), lr=3e-3)
        
        for ep in range(5):
            model.train()
            perm = np.random.permutation(N)
            for a in range(0, N, 1024):
                bidx = perm[a:a + 1024].tolist()
                b = batchify(bidx, tr_samples, F_tr)
                out = model(b["state"], b["uctx"], b["valid"])
                
                # Market loss
                loss_m_op = ce(out["m_op"].reshape(-1, len(C.M_OP)), b["m_op"].reshape(-1)).mean()
                mm = _op_mask(b["m_op"], M_ITEM_OPS)
                loss_m_item = ce(out["m_item"][mm], b["m_item"][mm]).mean() if mm.any() else out["m_op"].sum() * 0.0
                loss_m_qty = ce(out["m_qty"][mm], b["m_qty"][mm]).mean() if mm.any() else out["m_op"].sum() * 0.0
                L_mkt = loss_m_op + loss_m_item + loss_m_qty
                
                vv = b["valid"]
                loss_u_op = ce(out["u_op"][vv], b["u_op"][vv]).mean()
                ma = _op_mask(b["u_op"], U_ARG_OPS) & vv
                loss_u_arg = ce(out["u_arg"][ma], b["u_arg"][ma]).mean() if ma.any() else out["u_op"].sum() * 0.0
                mq = _op_mask(b["u_op"], U_QTY_OPS) & vv
                loss_u_qty = ce(out["u_qty"][mq], b["u_qty"][mq]).mean() if mq.any() else out["u_op"].sum() * 0.0
                L_unit = loss_u_op + loss_u_arg + loss_u_qty
                
                # Critical pattern loss on step-0 samples
                is_s0 = torch.tensor([tr_samples[i]["step"] == 0 for i in bidx], dtype=torch.bool)
                if is_s0.any() and crit_weight > 0.0:
                    s0_m_op = ce(out["m_op"][is_s0].reshape(-1, len(C.M_OP)), b["m_op"][is_s0].reshape(-1)).mean()
                    s0_mm = _op_mask(b["m_op"][is_s0], M_ITEM_OPS)
                    s0_m_item = ce(out["m_item"][is_s0][s0_mm], b["m_item"][is_s0][s0_mm]).mean() if s0_mm.any() else out["u_op"].sum() * 0.0
                    s0_m_qty = ce(out["m_qty"][is_s0][s0_mm], b["m_qty"][is_s0][s0_mm]).mean() if s0_mm.any() else out["u_op"].sum() * 0.0
                    L_crit = s0_m_op + s0_m_item + s0_m_qty
                else:
                    L_crit = 0.0
                    
                loss = L_unit + L_mkt + crit_weight * L_crit
                    
                opt.zero_grad()
                loss.backward()
                torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                opt.step()
                
            # Eval step 0 after each epoch
            model.eval()
            with torch.no_grad():
                out_s0 = model(b_s0["state"], b_s0["uctx"], b_s0["valid"])
                m_op_logits = out_s0["m_op"]
                p_s0 = m_op_logits.softmax(-1)
                p_s0_buy = p_s0[:, 0, 4].mean().item()
                p_s0_sell = p_s0[:, 0, 6].mean().item()
                p_s1_buy = p_s0[:, 1, 4].mean().item()
                p_s1_sell = p_s0[:, 1, 6].mean().item()
                
                pred_s0_op = C.M_OP[m_op_logits[0, 0].argmax(-1)]
                pred_s1_op = C.M_OP[m_op_logits[0, 1].argmax(-1)]
                
                n_wash = 0
                for r in range(len(all_step0)):
                    o0 = m_op_logits[r, 0].argmax().item()
                    o1 = m_op_logits[r, 1].argmax().item()
                    it0 = out_s0["m_item"][r, 0].argmax().item()
                    it1 = out_s0["m_item"][r, 1].argmax().item()
                    q0 = C.M_QTY[out_s0["m_qty"][r, 0].argmax().item()]
                    q1 = C.M_QTY[out_s0["m_qty"][r, 1].argmax().item()]
                    if o0 == 4 and it0 == 0 and q0 > 0 and o1 == 6 and it1 == 0 and q1 > 0:
                        n_wash += 1
                        
                print(f"  Ep {ep}: Slot0=[{pred_s0_op} P(BUY)={p_s0_buy:.3f} P(SELL)={p_s0_sell:.3f}], Slot1=[{pred_s1_op} P(BUY)={p_s1_buy:.3f} P(SELL)={p_s1_sell:.3f}], Wash={n_wash}/240", flush=True)

if __name__ == "__main__":
    run_pilot()
