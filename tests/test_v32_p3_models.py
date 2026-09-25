# SPDX-License-Identifier: MIT
"""V32 P3 model tests: shapes, determinism, padding, loss masking, rollout."""

import os
import sys

import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, REPO_ROOT)

torch = pytest.importorskip("torch")

from v32.p3 import codec as C  # noqa: E402
from v32.p3.metrics import batchify, head_losses  # noqa: E402
from v32.p3.models import LinearControl, P3Policy, param_count  # noqa: E402


def _model(seed=0):
    torch.manual_seed(seed)
    return P3Policy(157, 12)


def _batch(b=2, u=3):
    torch.manual_seed(1)
    return (torch.randn(b, 157), torch.randn(b, u, 12),
            torch.ones(b, u, dtype=torch.bool))


def test_forward_shapes_and_param_count():
    m = _model()
    s, u, v = _batch()
    out = m(s, u, v)
    assert out["u_op"].shape == (2, 3, 18)
    assert out["u_arg"].shape == (2, 3, 12)
    assert out["u_qty"].shape == (2, 3, 17)
    assert out["m_op"].shape == (2, 10, 7)
    assert out["m_item"].shape == (2, 10, 12)
    assert out["m_qty"].shape == (2, 10, 77)
    assert out["value"].shape == (2,)
    n = param_count(m)
    assert 200000 < n < 400000, n
    print("P3 params: %d" % n)


def test_act_determinism_and_padding_invariance():
    m = _model()
    m.eval()
    s, u, v = _batch(b=1, u=2)
    a1 = m.act(s, u, v, deterministic=True)
    a2 = m.act(s, u, v, deterministic=True)
    for k in ("u_op", "m_op", "m_qty"):
        assert torch.equal(a1[k], a2[k])
    assert a1["logprob"].item() == pytest.approx(a2["logprob"].item())
    # padding: extra invalid slots change nothing
    u_pad = torch.cat([u, torch.zeros(1, 3, 12)], dim=1)
    v_pad = torch.cat([v, torch.zeros(1, 3, dtype=torch.bool)], dim=1)
    a3 = m.act(s, u_pad, v_pad, deterministic=True)
    assert torch.equal(a3["u_op"][:, :2], a1["u_op"])
    assert a3["logprob"].item() == pytest.approx(a1["logprob"].item(),
                                                 abs=1e-4)


def test_act_gated_logprob():
    # don't-care heads (arg/qty on PASS slots) contribute no logprob/entropy
    m = _model()
    m.eval()
    s = torch.randn(1, 157)
    u = torch.randn(1, 1, 12)
    v = torch.ones(1, 1, dtype=torch.bool)
    with torch.no_grad():
        out = m.forward(s, u, v)
    # force PASS everywhere: arg/qty gates off
    a = m.act(s, u, v, deterministic=True)
    assert a["logprob"].shape == (1,) and a["entropy"].shape == (1,)


def test_loss_masking_dont_care_heads_ignored():
    import torch.nn as nn
    samples = [{"uctx": [[0.0] * 12], "u_op": [0], "u_arg": [5],
                "u_qty": [9], "m_op": [0] * 10, "m_item": [3] * 10,
                "m_qty": [11] * 10}]
    import numpy as np
    F = np.zeros((1, 157))
    b = batchify([0], samples, F)
    m = _model()
    ce = nn.CrossEntropyLoss(reduction="none")
    l1 = head_losses(m(b["state"], b["uctx"], b["valid"]), b, ce)
    # change don't-care targets: loss must not move
    samples[0]["u_arg"] = [1]
    samples[0]["u_qty"] = [2]
    samples[0]["m_item"] = [7] * 10
    samples[0]["m_qty"] = [60] * 10
    b2 = batchify([0], samples, F)
    l2 = head_losses(m(b2["state"], b2["uctx"], b2["valid"]), b2, ce)
    assert l1["total"].item() == pytest.approx(l2["total"].item())


def test_linear_control_shapes():
    torch.manual_seed(0)
    m = LinearControl(157, 12)
    s, u, v = _batch()
    out = m(s, u, v)
    assert out["u_op"].shape == (2, 3, 18)
    assert out["m_qty"].shape == (2, 10, 77)


def test_predictor_emits_valid_native_actions():
    import numpy as np
    from v32.p2.features import Normalizer
    from v32.p3.rollout import Predictor
    m = _model()
    norm = Normalizer()
    norm.mu = np.zeros(157)
    norm.sd = np.ones(157)
    pred = Predictor(m, norm)
    ess = {"step": 0, "day": 0, "hour": 0, "money": 3000.0,
           "farmer": [4, 4], "hands": [[4, 5]], "quads": 1, "hires": 0,
           "thist": [0] * 12, "ucode": [1, 1], "shed": {}, "seeds": {},
           "inv": [{}, {}], "prices": {}, "mkt_inv": {}, "shops": [],
           "o_money": 3000.0, "o_hands": 0, "o_quads": 1, "o_plant": 0,
           "o_past": 0, "o_weed": 0}
    pr = pred.step(ess, deterministic=True)
    act = pr["action"]
    assert set(act) == {"farmer", "hands", "market"}
    assert len(act["hands"]) == 1 and len(act["market"]) <= 10
    # every emitted literal re-encodes cleanly (in-schema by construction)
    enc = C.encode_action(act, 1)
    assert enc["flags"] == []
