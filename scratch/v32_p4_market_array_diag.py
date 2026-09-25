# SPDX-License-Identifier: MIT
"""V32 P4 Market Joint Array Diagnostics:
Measures individual slot accuracy vs full ordered market array accuracy across validation set.
"""

import json
import os
import sys
import numpy as np
import torch

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, REPO_ROOT)

from v32.p2.dataset import BC_VAL_SEEDS, load_legs
from v32.p2.features import Normalizer
from v32.p3 import codec as C
from v32.p3.dataset import build_samples
from v32.p3.metrics import batchify
from v32.p3.models import P3Policy

def run_diagnostics():
    norm = Normalizer.from_json(json.load(open(os.path.join(REPO_ROOT, "results", "v32_p2_norm.json"))))
    legs_path = os.path.join(REPO_ROOT, "results", "v32_p2_bc_legs.jsonl")
    va_samples = []
    
    for leg in load_legs(legs_path):
        if leg["seed"] in BC_VAL_SEEDS:
            for side, expert in (("rows0", leg["left"]), ("rows1", leg["right"])):
                va_samples.extend(build_samples(leg, leg[side], expert))
                
    F_va = norm.transform([s["feat"] for s in va_samples])
    N = len(va_samples)
    print(f"Validation transitions: {N}")

    ckpts = [
        ("P3 Baseline (3e-4)", "results/v32_p3_bc.npz"),
        ("P3 Baseline (3e-3)", "results/v32_p3_bc_lr3e3.npz"),
        ("P4 Arm 1 (Balanced)", "results/v32_p4_arm1_balanced.npz"),
        ("P4 Arm 2 (Mkt Pretrain)", "results/v32_p4_arm2_mkt_pretrain.npz"),
        ("P4 Arm 3 (Mkt Frozen)", "results/v32_p4_arm3_mkt_frozen.npz"),
        ("P4 Arm 4 (Mkt Unfrozen)", "results/v32_p4_arm4_mkt_unfrozen.npz")
    ]

    results = []

    for name, pth in ckpts:
        full_pth = os.path.join(REPO_ROOT, pth)
        if not os.path.exists(full_pth):
            continue
        d = np.load(full_pth, allow_pickle=True)
        model = P3Policy(F_va.shape[1], 12)
        model.load_state_dict({k: torch.tensor(v) for k, v in d.items() if k != "meta"})
        model.eval()

        slot_correct = np.zeros(10)
        full_array_exact = 0
        non_noop_correct = 0
        non_noop_total = 0

        chunk = 4096
        with torch.no_grad():
            for a in range(0, N, chunk):
                bidx = list(range(a, min(a + chunk, N)))
                b = batchify(bidx, va_samples, F_va)
                out = model(b["state"], b["uctx"], b["valid"])
                
                pu_m = out["m_op"].argmax(-1).numpy() # [B, 10]
                tu_m = b["m_op"].numpy() # [B, 10]

                # Per-slot op match
                matches = (pu_m == tu_m) # [B, 10]
                slot_correct += matches.sum(axis=0)

                # Full array exact match (all 10 slots match op)
                full_array_exact += matches.all(axis=1).sum()

                # Non-noop op match
                is_nn = (tu_m != C._M_OP_ID["NOOP"])
                non_noop_total += is_nn.sum()
                non_noop_correct += (matches & is_nn).sum()

        rec = {
            "name": name,
            "per_slot_acc": (slot_correct / N).tolist(),
            "full_array_exact_rate": float(full_array_exact / N),
            "mkt_nonnoop_acc": float(non_noop_correct / non_noop_total)
        }
        results.append(rec)
        print(f"\n{name}:")
        print(f"  Full 10-slot Array Exact: {rec['full_array_exact_rate']*100:.2f}%")
        print(f"  Non-NOOP Op Accuracy:     {rec['mkt_nonnoop_acc']*100:.2f}%")
        print(f"  Slot 0 Acc: {rec['per_slot_acc'][0]*100:.2f}% | Slot 1 Acc: {rec['per_slot_acc'][1]*100:.2f}% | Slot 2 Acc: {rec['per_slot_acc'][2]*100:.2f}%")

    out_file = os.path.join(REPO_ROOT, "results", "v32_p4_market_joint_diagnostics.json")
    with open(out_file, "w") as f:
        json.dump(results, f, indent=1)
    print(f"\nWrote diagnostics to {out_file}")

if __name__ == "__main__":
    run_diagnostics()
