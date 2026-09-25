# SPDX-License-Identifier: MIT
"""V32 P4 Forensic Audit Script: 14 check points and step-0 verification."""

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
from v32.p3.metrics import batchify, head_losses, _op_mask
from v32.p3.models import P3Policy, param_count, M_ITEM_OPS, U_ARG_OPS, U_QTY_OPS

def run_forensic_checks():
    print("=== STARTING P4 FORENSIC AUDIT ===")
    norm = Normalizer.from_json(json.load(open(os.path.join(REPO_ROOT, "results", "v32_p2_norm.json"))))
    
    # Load all legs and split
    legs_path = os.path.join(REPO_ROOT, "results", "v32_p2_bc_legs.jsonl")
    tr_samples = []
    va_samples = []
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
                    
    print(f"Dataset: train={len(tr_samples)} val={len(va_samples)} total_step0={len(all_step0)}")
    tr_step0 = [s for s in tr_samples if s["step"] == 0]
    va_step0 = [s for s in va_samples if s["step"] == 0]
    print(f"Step-0 samples: train={len(tr_step0)} val={len(va_step0)}")

    # 1. Market-label indexing check
    print("\n--- Check 1 & 2: Market label indexing & slot ordering ---")
    print(f"M_OP: {C.M_OP}")
    print(f"M_ITEM: {C.M_ITEM}")
    print(f"M_QTY length: {len(C.M_QTY)}")
    # Verify codec IDs
    for op in C.M_OP:
        assert C._M_OP_ID[op] == C.M_OP.index(op)
    for it in C.M_ITEM:
        assert C._M_ITEM_ID[it] == C.M_ITEM.index(it)
    for i, q in enumerate(C.M_QTY):
        assert C._M_QTY_ID[q] == i
    print("Label indexing: 100% verified consistent.")

    # 8. Check step-0 records duplication
    print("\n--- Check 8 & 14: Step-0 records and teacher alignment ---")
    # Examine teacher actions at step 0
    t_counts = {}
    t_targets = {}
    for s in tr_step0:
        t = s["teacher"]
        t_counts[t] = t_counts.get(t, 0) + 1
        m0_lit = C.decode_market(s["m_op"][0], s["m_item"][0], s["m_qty"][0])
        m1_lit = C.decode_market(s["m_op"][1], s["m_item"][1], s["m_qty"][1])
        t_targets[t] = (m0_lit, m1_lit)
    print("Train step-0 counts by teacher:", t_counts)
    print("Step-0 market slot targets by teacher:")
    for t, tg in t_targets.items():
        print(f"  {t}: slot0={tg[0]}, slot1={tg[1]}")
    
    # Are step-0 records identical features?
    f_step0 = norm.transform([s["feat"] for s in all_step0])
    diffs = []
    for i in range(1, len(f_step0)):
        diffs.append(np.max(np.abs(f_step0[i] - f_step0[0])))
    print(f"Max feature difference across all 240 step-0 samples: {max(diffs)}")

    # Check 11 & 13: Gradient forensics (unit vs market, shared trunk, slot magnitudes)
    print("\n--- Check 3, 4, 5, 9, 10, 11, 12, 13: Model, Loss, Optimizer & Gradients ---")
    F_tr = norm.transform([s["feat"] for s in tr_samples])
    
    # Instantiate P3 model
    torch.manual_seed(0)
    model = P3Policy(F_tr.shape[1], 12)
    ce = nn.CrossEntropyLoss(reduction="none")
    
    # Evaluate checkpoints on step 0
    ckpts = [
        ("v32_p3_bc.npz (LR 3e-4)", "results/v32_p3_bc.npz"),
        ("v32_p3_bc_lr3e3.npz (LR 3e-3)", "results/v32_p3_bc_lr3e3.npz")
    ]
    b_step0 = batchify(list(range(len(all_step0))), all_step0, f_step0)
    
    for name, pth in ckpts:
        full_pth = os.path.join(REPO_ROOT, pth)
        if os.path.exists(full_pth):
            d = np.load(full_pth, allow_pickle=True)
            model.load_state_dict({k: torch.tensor(v) for k, v in d.items() if k != "meta"})
            model.eval()
            with torch.no_grad():
                out = model(b_step0["state"], b_step0["uctx"], b_step0["valid"])
                m_op_logits = out["m_op"] # [240, 10, 7]
                m_item_logits = out["m_item"] # [240, 10, 12]
                m_qty_logits = out["m_qty"] # [240, 10, 77]
                
                # Check logits collapse
                print(f"\nCheckpoint {name}:")
                print(f"  m_op logits: min={m_op_logits.min().item():.3f}, max={m_op_logits.max().item():.3f}, std={m_op_logits.std().item():.3f}")
                
                # Check predictions for slot 0 and slot 1
                p_m_op = m_op_logits.softmax(-1)
                print(f"  Slot 0 mean probs: NOOP={p_m_op[:, 0, 0].mean():.3f}, BUY_PRODUCT={p_m_op[:, 0, 4].mean():.3f}, SELL={p_m_op[:, 0, 6].mean():.3f}")
                print(f"  Slot 1 mean probs: NOOP={p_m_op[:, 1, 0].mean():.3f}, BUY_PRODUCT={p_m_op[:, 1, 4].mean():.3f}, SELL={p_m_op[:, 1, 6].mean():.3f}")
                
                pred_s0_op = C.M_OP[m_op_logits[0, 0].argmax(-1)]
                pred_s1_op = C.M_OP[m_op_logits[0, 1].argmax(-1)]
                pred_s0_item = C.M_ITEM[m_item_logits[0, 0].argmax(-1)]
                pred_s1_item = C.M_ITEM[m_item_logits[0, 1].argmax(-1)]
                pred_s0_qty = C.M_QTY[m_qty_logits[0, 0].argmax(-1)]
                pred_s1_qty = C.M_QTY[m_qty_logits[0, 1].argmax(-1)]
                print(f"  Step 0 argmax action:")
                print(f"    Slot 0: [{pred_s0_op}, {pred_s0_item}, {pred_s0_qty}]")
                print(f"    Slot 1: [{pred_s1_op}, {pred_s1_item}, {pred_s1_qty}]")
                
                # Full exact wash check
                n_wash = 0
                for r in range(len(all_step0)):
                    m0 = [C.M_OP[m_op_logits[r, 0].argmax()], C.M_ITEM[m_item_logits[r, 0].argmax()], C.M_QTY[m_qty_logits[r, 0].argmax()]]
                    m1 = [C.M_OP[m_op_logits[r, 1].argmax()], C.M_ITEM[m_item_logits[r, 1].argmax()], C.M_QTY[m_qty_logits[r, 1].argmax()]]
                    if m0[0] == "BUY_PRODUCT" and m0[1] == "WHEAT" and m0[2] > 0 and m1[0] == "SELL" and m1[1] == "WHEAT" and m1[2] > 0:
                        n_wash += 1
                print(f"  Valid wash shape count: {n_wash}/{len(all_step0)}")

    # Now let's compute gradient norms and cosine similarity on representative batches
    print("\n--- Detailed Gradient Forensics on Training Batches ---")
    torch.manual_seed(0)
    model = P3Policy(F_tr.shape[1], 12)
    model.train()
    
    # Batch 1: purely random general batch of 1024
    rand_idxs = np.random.choice(len(tr_samples), 1024, replace=False).tolist()
    b_rand = batchify(rand_idxs, tr_samples, F_tr)
    
    # Compute gradients for unit loss and market loss separately
    out_rand = model(b_rand["state"], b_rand["uctx"], b_rand["valid"])
    losses_rand = head_losses(out_rand, b_rand, ce)
    
    L_unit = sum(losses_rand[k] for k in ("u_op", "u_arg", "u_qty"))
    L_mkt = sum(losses_rand[k] for k in ("m_op", "m_item", "m_qty"))
    
    # Gradients w.r.t trunk parameters
    trunk_params = list(model.trunk.parameters())
    grad_unit_trunk = torch.autograd.grad(L_unit, trunk_params, retain_graph=True)
    grad_mkt_trunk = torch.autograd.grad(L_mkt, trunk_params, retain_graph=True)
    
    flat_grad_unit = torch.cat([g.reshape(-1) for g in grad_unit_trunk])
    flat_grad_mkt = torch.cat([g.reshape(-1) for g in grad_mkt_trunk])
    
    norm_unit = flat_grad_unit.norm().item()
    norm_mkt = flat_grad_mkt.norm().item()
    cos_sim = torch.cosine_similarity(flat_grad_unit, flat_grad_mkt, dim=0).item()
    
    print(f"Random Batch (1024):")
    print(f"  L_unit={L_unit.item():.4f}, L_mkt={L_mkt.item():.4f}")
    print(f"  Trunk ||grad(L_unit)|| = {norm_unit:.4f}")
    print(f"  Trunk ||grad(L_mkt)||  = {norm_mkt:.4f}")
    print(f"  Trunk Ratio (unit/mkt) = {norm_unit / max(1e-6, norm_mkt):.2f}")
    print(f"  Cosine Similarity (unit vs mkt) = {cos_sim:.4f}")
    
    # Batch 2: Batch containing Step 0 samples
    # Let's create a batch with all 192 train step-0 samples + random samples to 1024
    tr_step0_idxs = [i for i, s in enumerate(tr_samples) if s["step"] == 0]
    rem_idxs = np.random.choice([i for i, s in enumerate(tr_samples) if s["step"] != 0], 1024 - len(tr_step0_idxs), replace=False).tolist()
    step0_batch_idxs = tr_step0_idxs + rem_idxs
    b_step0_batch = batchify(step0_batch_idxs, tr_samples, F_tr)
    
    out_s0 = model(b_step0_batch["state"], b_step0_batch["uctx"], b_step0_batch["valid"])
    losses_s0 = head_losses(out_s0, b_step0_batch, ce)
    
    L_unit_s0 = sum(losses_s0[k] for k in ("u_op", "u_arg", "u_qty"))
    L_mkt_s0 = sum(losses_s0[k] for k in ("m_op", "m_item", "m_qty"))
    
    grad_u_s0 = torch.cat([g.reshape(-1) for g in torch.autograd.grad(L_unit_s0, trunk_params, retain_graph=True)])
    grad_m_s0 = torch.cat([g.reshape(-1) for g in torch.autograd.grad(L_mkt_s0, trunk_params, retain_graph=True)])
    
    print(f"\nStep-0 Enriched Batch (192 step-0 + 832 other):")
    print(f"  L_unit={L_unit_s0.item():.4f}, L_mkt={L_mkt_s0.item():.4f}")
    print(f"  Trunk ||grad(L_unit)|| = {grad_u_s0.norm().item():.4f}")
    print(f"  Trunk ||grad(L_mkt)||  = {grad_m_s0.norm().item():.4f}")
    print(f"  Trunk Ratio (unit/mkt) = {grad_u_s0.norm().item() / max(1e-6, grad_m_s0.norm().item()):.2f}")
    print(f"  Cosine Similarity (unit vs mkt) = {torch.cosine_similarity(grad_u_s0, grad_m_s0, dim=0).item():.4f}")

    # Check 13: Per-slot gradient magnitudes for market head
    print("\n--- Check 13: Per-slot gradient magnitudes for market slots ---")
    # Gradients w.r.t slot embedding weights
    grad_slot_emb_s0 = torch.autograd.grad(L_mkt_s0, model.slot_emb.weight, retain_graph=True)[0]
    for slot_idx in range(10):
        print(f"  Slot {slot_idx} embedding grad norm: {grad_slot_emb_s0[slot_idx].norm().item():.4f}")

if __name__ == "__main__":
    run_forensic_checks()
