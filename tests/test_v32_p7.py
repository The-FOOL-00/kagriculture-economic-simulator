# SPDX-License-Identifier: MIT
"""V32 P7 test suite (protocol Sections 39-40).

1. P6 checkpoint loads
2. prefix extraction is deterministic
3. prefix labels exactly match source demonstrations
4. prefix loss has no hidden future state (+ uniform within window)
5. free-running prefix rollout uses only current policy state
   (+ truncated == env.run equivalence on both seats)
6. state-distance calculation is deterministic
7. phase derivation uses only observable state
8. phase derivation is deterministic
9. no teacher action is injected into inference
10. no action tape exists
11. no step-indexed action override exists
12. competition artifacts remain unchanged
"""

import ast
import copy
import inspect
import json
import os
import sys

import numpy as np
import pytest
import torch

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, REPO_ROOT)
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))

from v32_common import assert_frozen, load_agent  # noqa: E402
from v32.p2.dataset import load_legs  # noqa: E402
from v32.p2.essentials import essentialize  # noqa: E402
from v32.p2.features import Normalizer  # noqa: E402
from v32.p3 import codec as C  # noqa: E402
from v32.p3.dataset import build_samples  # noqa: E402
from v32.p3.metrics import batchify  # noqa: E402
from v32.p3.models import P3Policy  # noqa: E402
from v32.p7.loss import prefix_loss, prefix_window_mask  # noqa: E402
from v32.p7.metrics import (first_divergence, prefix_exact_match,  # noqa: E402
                            wash_order_correct)
from v32.p7.phase import detect_phase, phase_name  # noqa: E402
from v32.p7.prefix import extract_prefix_steps  # noqa: E402
from v32.p7.rollout import (full_episode_trace, shared_obs,  # noqa: E402
                            truncated_rollout)
from v32.p7.state import state_distance  # noqa: E402

P6_CKPT = os.path.join(REPO_ROOT, "results", "v32_p6_arm2_rebalanced.npz")
NORM_PATH = os.path.join(REPO_ROOT, "results", "v32_p2_norm.json")
LEGS_PATH = os.path.join(REPO_ROOT, "results", "v32_p2_bc_legs.jsonl")


def _first_leg_rows():
    leg = next(load_legs(LEGS_PATH))
    return leg, leg["rows0"], leg["left"]


def test_01_p6_checkpoint_loads():
    assert os.path.exists(P6_CKPT)
    d = np.load(P6_CKPT, allow_pickle=True)
    m = P3Policy(157, 12)
    m.load_state_dict({k: torch.tensor(v) for k, v in d.items()
                       if k != "meta"})
    m.eval()
    assert sum(p.numel() for p in m.parameters()) == 277092


def test_02_prefix_extraction_deterministic():
    leg, rows, teacher = _first_leg_rows()
    a = extract_prefix_steps(rows, teacher, leg["seed"], 8)
    b = extract_prefix_steps(rows, teacher, leg["seed"], 8)
    assert a is not None and b is not None
    for ra, rb in zip(a, b):
        assert ra["step"] == rb["step"]
        assert ra["ess"] == rb["ess"]
        assert ra["action"] == rb["action"]
        assert np.allclose(ra["feat"], rb["feat"])
        assert ra["u_op"] == rb["u_op"] and ra["m_op"] == rb["m_op"]


def test_03_prefix_labels_match_demonstrations():
    """Prefix features/targets are bit-identical to build_samples + codec."""
    leg, rows, teacher = _first_leg_rows()
    pref = extract_prefix_steps(rows, teacher, leg["seed"], 4)
    ref = list(build_samples(leg, rows, teacher))[:5]
    assert len(pref) == 5 and len(ref) == 5
    for p, r in zip(pref, ref):
        assert np.allclose(p["feat"], r["feat"])
        assert p["uctx"] == r["uctx"]
        for k in ("u_op", "u_arg", "u_qty", "m_op", "m_item", "m_qty"):
            assert p[k] == r[k], k
        # native round-trip: targets decode to the recorded literal
        n_u = len(p["uctx"])
        dec = C.decode_action(list(zip(p["u_op"], p["u_arg"], p["u_qty"]))[:n_u],
                              list(zip(p["m_op"], p["m_item"], p["m_qty"])))
        assert dec["farmer"] == (p["action"].get("farmer") or ["PASS"])


def test_04_prefix_loss_uniform_no_future():
    """L(batch) == mean of per-row L (uniformity) and window-masked."""
    torch.manual_seed(0)
    model = P3Policy(157, 12)
    model.eval()
    leg, rows, teacher = _first_leg_rows()
    samples = list(build_samples(leg, rows, teacher))[:8]
    F = np.random.RandomState(0).randn(len(samples), 157)
    ce = torch.nn.CrossEntropyLoss(reduction="none")
    b = batchify(list(range(len(samples))), samples, F)
    out = model(b["state"], b["uctx"], b["valid"])
    steps = [s["step"] for s in samples]
    H = 4
    joint = prefix_loss(out, b, steps, H, ce)
    # mean of single-row losses over the same window rows
    singles = []
    for i, s in enumerate(samples):
        if s["step"] <= H:
            bi = batchify([i], samples, F)
            oi = model(bi["state"], bi["uctx"], bi["valid"])
            singles.append(prefix_loss(oi, bi, [s["step"]], H, ce).item())
    assert joint.item() == pytest.approx(float(np.mean(singles)), abs=1e-4)
    # rows past H are excluded: permuting them cannot change the loss
    perm = list(range(len(samples)))
    ws = [i for i in perm if samples[i]["step"] <= H]
    os_ = [i for i in perm if samples[i]["step"] > H]
    alt = ws + os_[::-1]
    ba = batchify(alt, samples, F)
    oa = model(ba["state"], ba["uctx"], ba["valid"])
    assert prefix_loss(oa, ba, [steps[i] for i in alt], H, ce).item() == \
        pytest.approx(joint.item(), abs=1e-5)
    assert prefix_window_mask([0, 4, 5], 4).tolist() == [True, True, False]


def test_05_truncated_rollout_equivalent_and_current_state_only():
    """Truncated rollouts equal env.run's first H steps on both seats."""
    from kaggle_environments import make
    make_fn = lambda s: make("kaggriculture", configuration={"seed": s})  # noqa: E731
    for seat in (0, 1):
        ag = [load_agent("E2_A7"), load_agent("E0_V3")]
        ag2 = [load_agent("E2_A7"), load_agent("E0_V3")]
        tr, _ = truncated_rollout(make_fn, 249675, ag, 8, trace_seat=seat,
                                  ess_fn=essentialize)
        fu, _ = full_episode_trace(make_fn, 249675, ag2, trace_seat=seat,
                                   ess_fn=essentialize)
        assert len(tr) == 9
        for t in range(9):
            assert tr[t]["actions"][seat] == fu[t]["action"]
            assert tr[t]["ess"] == fu[t]["ess"]
    # rollout module takes generic agents: no teacher param anywhere
    sig = inspect.signature(truncated_rollout)
    assert "teacher" not in sig.parameters
    src = inspect.getsource(shared_obs) + inspect.getsource(truncated_rollout)
    assert "teacher" not in src.lower()


def test_06_state_distance_deterministic():
    leg, rows, _ = _first_leg_rows()
    a, b = rows[0]["e"], rows[5]["e"]
    d1, d2 = state_distance(a, b), state_distance(a, b)
    assert d1 == d2
    assert state_distance(a, copy.deepcopy(a))["total"] == 0.0
    assert set(d1["components"]) == {"position", "hands", "cash",
                                     "inventory", "livestock", "crops",
                                     "market"}


def test_07_phase_uses_only_observable_state():
    import v32.p7.phase as P
    tree = ast.parse(inspect.getsource(P))
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            names.add(node.id)
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            names.add("str:" + node.value)
    for bad in ("step", "teacher", "seed", "future", "tape", "route",
                "str:step", "str:teacher", "str:seed"):
        assert bad not in names, bad
    # step index cannot leak through renamed access either
    src = inspect.getsource(P.detect_phase)
    assert "step" not in src


def test_08_phase_deterministic_and_sane():
    leg, rows, _ = _first_leg_rows()
    e0 = rows[0]["e"]
    assert detect_phase(e0) == detect_phase(copy.deepcopy(e0)) == 0
    assert phase_name(e0) == "OPENING_CAPITAL"
    hired = copy.deepcopy(e0)
    hired["hands"] = [[4, 4]]
    assert detect_phase(hired) == 1  # hands, no livestock
    stocked = copy.deepcopy(hired)
    stocked["shed"] = dict(stocked.get("shed", {}))
    stocked["shed"]["SHEEP"] = 2
    assert detect_phase(stocked) == 2  # livestock, no structures


def _ast_names(mod):
    tree = ast.parse(inspect.getsource(mod))
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            names.add(node.id)
        elif isinstance(node, ast.Attribute):
            names.add(node.attr)
    return names


def test_09_no_teacher_action_in_inference():
    import v32_p6_eval_screen as P6E
    import v32.p7.rollout as R
    import v32.p7.loss as L
    # inference entry points take no teacher inputs
    assert "teacher" not in inspect.signature(P6E.MaskedPredictor.step).parameters
    assert "teacher" not in _ast_names(R)
    assert "teacher" not in _ast_names(L)
    step_src = inspect.getsource(P6E.MaskedPredictor.step)
    assert "teacher" not in step_src.lower()


def test_10_no_action_tape():
    import v32.p7.prefix as PX
    import v32.p7.rollout as R
    import v32.p7.loss as L
    import v32.p7.metrics as M
    for mod in (PX, R, L, M):
        names = _ast_names(mod)
        src = inspect.getsource(mod)
        assert "_TRACE" not in src  # protocol literal (§40)
        assert "action_tape" not in src.lower()
        assert "routes[" not in src
        assert "routes" not in names


def test_11_no_step_indexed_override_or_spike():
    import v32.p7.loss as L
    import v32.p6.mask as MK
    loss_src = inspect.getsource(L)
    assert "lambda_s3" not in loss_src and "lambda_s4" not in loss_src
    assert "step == 3" not in loss_src and "step == 4" not in loss_src
    mask_src = inspect.getsource(MK.compute_unit_op_mask)
    assert "if step ==" not in mask_src
    assert 'return ["SOUTH"]' not in mask_src
    train_src = open(os.path.join(REPO_ROOT, "scripts",
                                  "v32_p7_train.py")).read()
    assert "s3_weight" not in train_src and "s4_weight" not in train_src
    assert "lambda_s3" not in train_src and "lambda_s4" not in train_src


def test_12_competition_artifacts_unchanged():
    assert_frozen()


def test_13_prefix_metrics_and_wash_order():
    t = [{"step": i, "ess": {"farmer": [4, 4], "hands": [], "money": 3000.0},
          "action": {"farmer": ["PASS"], "hands": [], "market": []}}
         for i in range(5)]
    p = copy.deepcopy(t)
    assert prefix_exact_match([r["action"] for r in t],
                              [r["action"] for r in p], 4, "farmer") is True
    p[3]["action"] = {"farmer": ["SOUTH"], "hands": [], "market": []}
    assert prefix_exact_match([r["action"] for r in t],
                              [r["action"] for r in p], 4, "farmer") is False
    div = first_divergence(t, p)
    assert div["t_act_farmer"] == 3 and div["t_pos"] is None
    assert wash_order_correct([["BUY_PRODUCT", "WHEAT", 30],
                               ["SELL", "WHEAT", 30]]) is True
    assert wash_order_correct([["SELL", "WHEAT", 30],
                               ["BUY_PRODUCT", "WHEAT", 30]]) is False
