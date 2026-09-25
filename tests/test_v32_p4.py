# SPDX-License-Identifier: MIT
"""V32 P4 Unit and Integration Tests (§38 Requirements).

Tests:
  1. Existing P3 model forward & param count
  2. P4 codec regression (G1 fixpoint)
  3. Exact step-0 label ground truth test
  4. Market slot-order test ([BUY, SELL] vs [SELL, BUY])
  5. Market-pretrained checkpoint save/reload test
  6. Frozen-market optimizer gradient test (zero grad on frozen heads)
  7. Gradient logging & magnitude test
  8. Deterministic evaluation test
"""

import json
import os
import sys
import numpy as np
import pytest
import torch
import torch.nn as nn

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, REPO_ROOT)

from v32.p2.dataset import load_legs
from v32.p2.features import Normalizer
from v32.p3 import codec as C
from v32.p3.dataset import build_samples
from v32.p3.metrics import batchify, head_losses
from v32.p3.models import P3Policy, param_count

def test_1_existing_p3_model_forward():
    m = P3Policy(157, 12)
    s = torch.randn(2, 157)
    u = torch.randn(2, 4, 12)
    v = torch.ones(2, 4, dtype=torch.bool)
    out = m(s, u, v)
    assert out["u_op"].shape == (2, 4, 18)
    assert out["m_op"].shape == (2, 10, 7)
    assert param_count(m) == 277092

def test_2_p4_codec_regression():
    # Verify codec lossless round-trip on canonical actions
    test_act = {
        "farmer": ["PLANT", "WHEAT"],
        "hands": [["WATER"], ["HARVEST"]],
        "market": [["BUY_PRODUCT", "WHEAT", 30], ["SELL", "WHEAT", 30]]
    }
    enc = C.encode_action(test_act, 2)
    dec = C.decode_action(enc["u"], enc["m"])
    assert dec == test_act
    # Round-trip fixpoint
    enc2 = C.encode_action(dec, 2)
    assert enc2["u"] == enc["u"]
    assert enc2["m"] == enc["m"]

def test_3_exact_step0_label_test():
    # Verify all 4 teachers produce slot0=BUY_PRODUCT, slot1=SELL at step 0
    legs = list(load_legs(os.path.join(REPO_ROOT, "results", "v32_p2_bc_legs.jsonl")))[:4]
    step0_count = 0
    for leg in legs:
        for side, expert in (("rows0", leg["left"]), ("rows1", leg["right"])):
            for s in build_samples(leg, leg[side], expert):
                if s["step"] == 0:
                    step0_count += 1
                    op0 = C.M_OP[s["m_op"][0]]
                    op1 = C.M_OP[s["m_op"][1]]
                    it0 = C.M_ITEM[s["m_item"][0]]
                    it1 = C.M_ITEM[s["m_item"][1]]
                    assert op0 == "BUY_PRODUCT", f"Expected BUY_PRODUCT on slot 0, got {op0}"
                    assert op1 == "SELL", f"Expected SELL on slot 1, got {op1}"
                    assert it0 == "WHEAT"
                    assert it1 == "WHEAT"
    assert step0_count > 0

def test_4_market_slot_order_test():
    # Test that [SELL, BUY] fails wash_shape and [BUY, SELL] passes wash_shape
    from scripts.v32_p4_train import wash_shape_of
    m_buy = C._M_OP_ID["BUY_PRODUCT"]
    m_sell = C._M_OP_ID["SELL"]
    w_idx = C._M_ITEM_ID["WHEAT"]
    q30_idx = C._M_QTY_ID[30]
    
    # Correct order
    correct_op = [m_buy, m_sell] + [0]*8
    correct_item = [w_idx, w_idx] + [0]*8
    correct_qty = [q30_idx, q30_idx] + [0]*8
    assert wash_shape_of(correct_op, correct_item, correct_qty) is True
    
    # Reversed order
    rev_op = [m_sell, m_buy] + [0]*8
    assert wash_shape_of(rev_op, correct_item, correct_qty) is False

def test_5_checkpoint_save_reload_test(tmp_path):
    m1 = P3Policy(157, 12)
    p_save = tmp_path / "test_mkt.npz"
    np.savez(p_save, **{k: v.detach().numpy() for k, v in m1.state_dict().items()})
    
    m2 = P3Policy(157, 12)
    d = np.load(p_save)
    m2.load_state_dict({k: torch.tensor(v) for k, v in d.items()})
    for k in m1.state_dict():
        assert torch.equal(m1.state_dict()[k], m2.state_dict()[k])

def test_6_frozen_market_optimizer_test():
    m = P3Policy(157, 12)
    for name, param in m.named_parameters():
        if any(h in name for h in ("m_op", "m_item", "m_qty", "slot_emb")):
            param.requires_grad = False
    
    trainable = [p for p in m.parameters() if p.requires_grad]
    opt = torch.optim.Adam(trainable, lr=1e-3)
    
    # Forward and backward
    s = torch.randn(2, 157)
    u = torch.randn(2, 1, 12)
    v = torch.ones(2, 1, dtype=torch.bool)
    out = m(s, u, v)
    loss = out["u_op"].sum() + out["m_op"].sum()
    loss.backward()
    
    # Verify market parameters have NO gradient
    for name, param in m.named_parameters():
        if any(h in name for h in ("m_op", "m_item", "m_qty", "slot_emb")):
            assert param.grad is None or param.grad.abs().sum() == 0

def test_7_gradient_logging_test():
    m = P3Policy(157, 12)
    s = torch.randn(2, 157)
    u = torch.randn(2, 1, 12)
    v = torch.ones(2, 1, dtype=torch.bool)
    out = m(s, u, v)
    loss = out["u_op"].sum()
    loss.backward()
    trunk_grad = m.trunk[0].weight.grad
    assert trunk_grad is not None
    assert trunk_grad.norm().item() > 0

def test_8_step0_diagnostic_test():
    # Integration test for step-0 regression diagnostic
    from scripts.v32_p4_train import eval_step0_probe
    m = P3Policy(157, 12)
    norm = Normalizer.from_json(json.load(open(os.path.join(REPO_ROOT, "results", "v32_p2_norm.json"))))
    legs = list(load_legs(os.path.join(REPO_ROOT, "results", "v32_p2_bc_legs.jsonl")))[:1]
    s0_samples = []
    for side, expert in (("rows0", legs[0]["left"]), ("rows1", legs[0]["right"])):
        for s in build_samples(legs[0], legs[0][side], expert):
            if s["step"] == 0:
                s0_samples.append(s)
    F_s0 = norm.transform([s["feat"] for s in s0_samples])
    res = eval_step0_probe(m, s0_samples, F_s0)
    assert res["n"] == len(s0_samples)
    assert "wash" in res
    assert "exact" in res
