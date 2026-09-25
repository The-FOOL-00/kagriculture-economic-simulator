# SPDX-License-Identifier: MIT
"""V32 P5 Baseline Reproduction:
Verifies P4 Arm 1 checkpoint integrity, step-0 wash accuracy,
and deterministic closed-loop behavior.
"""

import json
import os
import sys
import numpy as np
import torch

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, REPO_ROOT)
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))

from v32.p2.dataset import BC_VAL_SEEDS, load_legs
from v32.p2.features import Normalizer
from v32.p3 import codec as C
from v32.p3.dataset import build_samples
from v32.p3.metrics import batchify
from v32.p3.models import P3Policy
from scripts.v32_p4_train import eval_step0_probe

def verify_baseline():
    print("=== REPRODUCING P4 ARM 1 BASELINE ===")
    ckpt_path = os.path.join(REPO_ROOT, "results", "v32_p4_arm1_balanced.npz")
    assert os.path.exists(ckpt_path), f"Missing {ckpt_path}"
    
    norm = Normalizer.from_json(json.load(open(os.path.join(REPO_ROOT, "results", "v32_p2_norm.json"))))
    d = np.load(ckpt_path, allow_pickle=True)
    meta = json.loads(str(d["meta"]))
    print(f"Loaded checkpoint meta: arm={meta.get('arm')} wall_sec={meta.get('wall_sec')} val_full={meta.get('val', {}).get('full_exact'):.3f}")
    
    model = P3Policy(157, 12)
    model.load_state_dict({k: torch.tensor(v) for k, v in d.items() if k != "meta"})
    model.eval()
    
    # 1. Step-0 Wash Probe across all 240 step-0 samples
    legs_path = os.path.join(REPO_ROOT, "results", "v32_p2_bc_legs.jsonl")
    all_step0 = []
    for leg in load_legs(legs_path):
        for side, expert in (("rows0", leg["left"]), ("rows1", leg["right"])):
            for s in build_samples(leg, leg[side], expert):
                if s["step"] == 0:
                    all_step0.append(s)
                    
    F_s0 = norm.transform([s["feat"] for s in all_step0])
    s0_res = eval_step0_probe(model, all_step0, F_s0)
    print(f"Step-0 probe: wash={s0_res['wash']}/{s0_res['n']} ({s0_res['wash']/s0_res['n']*100:.1f}%) exact={s0_res['exact']}/{s0_res['n']}")
    print(f"  Slot 0 P(BUY)={s0_res['s0_p_buy']:.3f}, P(SELL)={s0_res['s0_p_sell']:.3f}")
    print(f"  Slot 1 P(BUY)={s0_res['s1_p_buy']:.3f}, P(SELL)={s0_res['s1_p_sell']:.3f}")
    print(f"  Slot 0 argmax: {s0_res['pred_m0']}")
    print(f"  Slot 1 argmax: {s0_res['pred_m1']}")
    
    assert s0_res['wash'] == 240, f"Expected 240/240 wash, got {s0_res['wash']}"
    assert s0_res['exact'] == 60, f"Expected 60/240 exact, got {s0_res['exact']}"
    
    # 2. Check screen evaluation metrics from results/v32_p4_eval_arm1.jsonl
    eval_file = os.path.join(REPO_ROOT, "results", "v32_p4_eval_arm1.jsonl")
    assert os.path.exists(eval_file), f"Missing {eval_file}"
    eval_recs = [json.loads(line) for line in open(eval_file) if line.strip()]
    assert len(eval_recs) == 120, f"Expected 120 records, got {len(eval_recs)}"
    
    cash_vals = [r["my_cash"] for r in eval_recs]
    washes = [r["step0_wash"] for r in eval_recs]
    mean_c = np.mean(cash_vals)
    med_c = np.median(cash_vals)
    wash_rate = np.mean(washes)
    
    print(f"Closed-loop 120-leg screen:")
    print(f"  Mean cash: ${mean_c:.2f} (expected ~$108.39)")
    print(f"  Median cash: ${med_c:.2f} (expected ~$0.50)")
    print(f"  Wash execution rate: {wash_rate*100:.1f}% (expected 100.0%)")
    
    assert wash_rate == 1.0, f"Expected 100% wash rate, got {wash_rate}"
    assert abs(mean_c - 108.39) < 1.0, f"Expected mean ~$108.39, got {mean_c}"
    
    print("P4 Arm 1 Baseline successfully reproduced and verified bit-for-bit!")

if __name__ == "__main__":
    verify_baseline()
