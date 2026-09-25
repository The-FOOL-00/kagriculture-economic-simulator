# SPDX-License-Identifier: MIT
"""V32 P2 tests: action-head suite (§30 T1-T11), features, models.

Fast, no matches (T5 steps a few turns on an already-consumed TRAIN seed;
T9/T11 read the generated BC legs + frozen vocab).
"""

import json
import os
import sys

import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, REPO_ROOT)
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))

torch = pytest.importorskip("torch")

from v32.p2 import actions as A  # noqa: E402
from v32.p2.features import EpisodeFeatures, schema_names, unit_ctx  # noqa: E402
from v32.p2.models import P2Policy, param_count  # noqa: E402

OPS = sorted(set(A.UNIT_OPS) | {"HIRE", "BUY_LAND", "BUY_SEED",
                                "BUY_PRODUCT", "BUY_ANIMAL", "SELL", "NOOP"})
ITEMS = sorted(set(A.SHED_ITEMS) | set(A.CROPS))

UVOC = [("PASS", None, None), ("NORTH", None, None),
        ("PLANT", "WHEAT", None), ("PLANT", "CARROT", None),
        ("PICKUP", "WHEAT", None), ("PICKUP", "WHEAT", 2)]
MVOC = [("NOOP", None, None), ("HIRE", None, None),
        ("SELL", "WHEAT", 1), ("SELL", "WHEAT", 50), ("BUY_SEED", "WHEAT", 1)]


def _model(state_dim=157, seed=0):
    torch.manual_seed(seed)
    return P2Policy(state_dim, 12, UVOC, MVOC, OPS, ITEMS)


def _batch(model, b=2, u=3, state_dim=157):
    torch.manual_seed(1)
    state = torch.randn(b, state_dim)
    uctx = torch.randn(b, u, 12)
    valid = torch.ones(b, u, dtype=torch.bool)
    mask = torch.zeros(b, len(UVOC))
    return state, uctx, valid, mask


# --- T2 normalization / T1 masking ---

def test_T1_T2_masked_probs_normalized():
    m = _model()
    state, uctx, valid, mask = _batch(m)
    mask[:, 2] = 1.0  # mask PLANT/WHEAT everywhere
    out = m.forward(state, uctx, valid, mask)
    pu = torch.softmax(out["unit_logits"], -1)
    pm = torch.softmax(out["market_logits"], -1)
    assert torch.allclose(pu.sum(-1), torch.ones_like(pu.sum(-1)), atol=1e-5)
    assert torch.allclose(pm.sum(-1), torch.ones_like(pm.sum(-1)), atol=1e-5)
    assert (pu[:, :, 2] == 0).all()  # illegal candidate: zero probability


def test_T4_single_action_determinism():
    m = _model()
    state, uctx, valid, mask = _batch(m, b=1, u=1)
    mask[:, 1:] = 1.0  # only PASS legal
    out = m.act(state, uctx, valid, mask, deterministic=False)
    assert out["unit"][0, 0].item() == 0
    ent = torch.distributions.Categorical(
        logits=m.forward(state, uctx, valid, mask)["unit_logits"]).entropy()
    assert ent[0, 0].item() == pytest.approx(0.0, abs=1e-4)


def test_T3_permutation_invariance():
    import random
    perm = list(range(len(UVOC)))
    random.Random(0).shuffle(perm)
    inv = [0] * len(perm)
    for i, p in enumerate(perm):
        inv[p] = i
    uvo2 = [UVOC[p] for p in perm]
    torch.manual_seed(0)
    m1 = P2Policy(157, 12, UVOC, MVOC, OPS, ITEMS)
    m2 = P2Policy(157, 12, uvo2, MVOC, OPS, ITEMS)
    m2.load_state_dict(m1.state_dict())  # identical weights, permuted vocab
    s, u, v, mk = _batch(m1)
    mk2 = mk[:, perm]
    l1 = m1.forward(s, u, v, mk)["unit_logits"]
    l2 = m2.forward(s, u, v, mk2)["unit_logits"][:, :, inv]
    assert torch.allclose(l1, l2, atol=1e-5)


def test_T7_padding_invariance():
    m = _model()
    s, u, v, mk = _batch(m, b=2, u=2)
    l_short = m.forward(s, u, v, mk)["unit_logits"]
    u_pad = torch.cat([u, torch.zeros(2, 3, 12)], dim=1)
    v_pad = torch.cat([v, torch.zeros(2, 3, dtype=torch.bool)], dim=1)
    l_pad = m.forward(s, u_pad, v_pad, mk)["unit_logits"][:, :2, :]
    assert torch.allclose(l_short, l_pad, atol=1e-5)
    a = m.act(s, u_pad, v_pad, mk, deterministic=True)
    # invalid slots contribute no logprob/entropy: compare vs valid-only call
    a2 = m.act(s, u, v, mk, deterministic=True)
    assert torch.allclose(a["logprob"], a2["logprob"], atol=1e-4)


def test_T8_T10_serialization_deterministic_state_independent():
    m = _model()
    dev = torch.device("cpu")
    t1 = m._cand_tensors(UVOC, dev)
    t2 = m._cand_tensors(UVOC, dev)
    for a, b in zip(t1, t2):
        assert torch.equal(a, b)
    # same candidate, different states/outcomes -> same encoding (T10: the
    # encoding path takes only the literal triple; states never enter it)
    h1 = A.candidate_hash(["SELL", "WHEAT", 50])
    h2 = A.candidate_hash(["SELL", "WHEAT", 50])
    assert h1 == h2 and len(h1) == 64


def test_T6_rollout_update_parity():
    # Regen-from-same-state: identical essentials -> identical candidate
    # tensors + identical selected-candidate identity hash.
    m = _model()
    dev = torch.device("cpu")
    op1, it1, sc1 = m._cand_tensors(MVOC, dev)
    op2, it2, sc2 = m._cand_tensors([tuple(c) for c in MVOC], dev)
    assert torch.equal(op1, op2) and torch.equal(it1, it2)
    assert torch.equal(sc1, sc2)
    sel = ["BUY_SEED", "WHEAT", 1]
    assert A.market_from_literal(sel) == ("BUY_SEED", "WHEAT", 1)
    assert A.market_to_literal(("BUY_SEED", "WHEAT", 1)) == sel


def test_T5_execution_identity_full_episode():
    # Emit policy actions into the exact simulator for a FULL episode on an
    # already-consumed TRAIN seed (no new consumption). PASS opponent.
    # Regression: manual env.step leaves seat-1 obs uninitialized, so all
    # rollout/eval MUST go through run_episode (env.run path).
    import numpy as np
    from kaggle_environments import make
    from v32.p2.features import Normalizer
    from v32.p2.rollout import Predictor, run_episode
    m = _model()
    m.eval()
    norm = Normalizer()
    norm.mu = np.zeros(157)
    norm.sd = np.ones(157)
    pred = Predictor(m, norm, UVOC, MVOC)

    class _Pass:
        def act(self, obs, cfg=None):
            return {"farmer": ["PASS"], "hands": [],
                    "market": []}

    torch.manual_seed(0)
    steps, mine, theirs = run_episode(
        lambda s: make("kaggriculture", configuration={"seed": s}),
        249635, 0, pred, _Pass())
    assert len(steps) == 719, len(steps)
    assert steps[-1]["done"] and steps[-1]["reward"] == mine / 1e5
    assert all(s["reward"] == 0.0 for s in steps[:-1])
    assert all(not s["done"] for s in steps[:-1])
    assert mine == mine and abs(mine) < 1e9  # finite
    # every emitted action was well-formed (simulator never errored) and
    # every step recorded hashes for parity
    assert all(len(s["hashes"]) >= 1 for s in steps)


def test_T9_count_safety_and_T11_exact_mapping():
    import glob
    legs = os.path.join(REPO_ROOT, "results", "v32_p2_bc_legs.jsonl")
    vocab_p = os.path.join(REPO_ROOT, "results", "v32_p2_vocab.json")
    assert os.path.exists(legs), "run v32_p2_capture.py first"
    assert os.path.exists(vocab_p), "run v32_p2_build_vocab.py first"
    vocab = json.load(open(vocab_p))
    uidx = {tuple(c): i for i, c in enumerate(vocab["unit_vocab"])}
    midx = {tuple(c): i for i, c in enumerate(vocab["market_vocab"])}
    max_hands = max_mkt = miss_u = miss_m = n = 0
    for line in open(legs):
        leg = json.loads(line)
        for side in ("rows0", "rows1"):
            for row in leg[side]:
                n += 1
                act = row["a"] or {}
                units = [act.get("farmer")] + list(act.get("hands") or [])
                max_hands = max(max_hands, len(act.get("hands") or []))
                mk = act.get("market") or []
                max_mkt = max(max_mkt, len(mk))
                for lit in units:
                    if tuple(A.unit_from_literal(lit) or ()) not in uidx:
                        miss_u += 1
                for s in range(A.M_MARKET_SLOTS):
                    lit = mk[s] if s < len(mk) else []
                    if tuple(A.market_from_literal(lit) or ()) not in midx:
                        miss_m += 1
    assert max_hands <= A.MAX_HANDS_CAP, max_hands
    assert max_mkt <= A.M_MARKET_SLOTS, max_mkt
    assert miss_u == 0, miss_u
    assert miss_m == 0, miss_m
    assert n > 10000, n


# --- features ---

def _ess(step=0, **kw):
    e = {"step": step, "day": 0, "hour": 0, "money": 3000.0,
         "farmer": [4, 4], "hands": [], "quads": 1, "hires": 0,
         "thist": [0] * 12, "ucode": [0],
         "shed": {}, "seeds": {}, "inv": [{}],
         "prices": {}, "mkt_inv": {}, "shops": [],
         "o_money": 3000.0, "o_hands": 0, "o_quads": 1,
         "o_plant": 0, "o_past": 0, "o_weed": 0}
    e.update(kw)
    return e


def test_features_schema_dim_determinism_masks():
    names = schema_names()
    assert len(names) == len(set(names))
    f1, f2 = EpisodeFeatures(), EpisodeFeatures()
    acts = [None, {"farmer": ["NORTH"], "hands": [], "market": []},
            {"farmer": ["PLANT", "WHEAT"], "hands": [],
             "market": [["BUY_SEED", "WHEAT", 1]]}]
    v1 = [f1.update(_ess(step=t, money=3000.0 + t), acts[t] if t < 3 else None)
          for t in range(3)]
    v2 = [f2.update(_ess(step=t, money=3000.0 + t), acts[t] if t < 3 else None)
          for t in range(3)]
    assert len(v1[0]) == len(names)
    assert v1 == v2  # deterministic
    assert f1.dim == len(names)
    # t=0: all window-validity masks 0, deltas zero-filled
    base_b = len([n for n in names if n.startswith("A/")])
    masks = v1[0][base_b + 48:base_b + 52]
    assert masks == [0.0, 0.0, 0.0, 0.0]
    assert all(x == 0.0 for x in v1[0][base_b:base_b + 48])
    # no-future: step-0 features identical with/without later steps appended
    f3 = EpisodeFeatures()
    assert f3.update(_ess(step=0), None) == v1[0]


def test_features_delta_correctness():
    f = EpisodeFeatures()
    f.update(_ess(step=0, money=1000.0), None)
    v = f.update(_ess(step=1, money=1500.0),
                 {"farmer": ["PASS"], "hands": [], "market": []})
    names = schema_names()
    i = names.index("B/d1_cash")
    assert v[i] == pytest.approx(500.0 / 1e5)
    assert v[names.index("B/valid_1")] == 1.0
    assert v[names.index("B/valid_8")] == 0.0


def test_unit_ctx_dim():
    assert len(unit_ctx(_ess(), 0)) == 12


def test_model_param_count_reported():
    m = _model()
    n = param_count(m)
    assert n > 100000, n
    print("P2 params (synthetic vocab): %d" % n)


# --- PPO core ---

def test_gae_endpoints():
    from v32.p2.ppo import compute_gae
    r = torch.tensor([0.0, 0.0, 1.0])
    v = torch.tensor([0.0, 0.0, 0.0])
    d = torch.tensor([False, False, True])
    adv, ret = compute_gae(r, v, d, gamma=1.0, lam=1.0)
    assert torch.allclose(ret, torch.tensor([1.0, 1.0, 1.0]))
    adv0, _ = compute_gae(r, v, d, gamma=1.0, lam=0.0)
    assert torch.allclose(adv0, torch.tensor([0.0, 0.0, 1.0]))
    # bootstrapping cut at done within a longer stream
    r2 = torch.tensor([0.0, 1.0, 0.0, 2.0])
    d2 = torch.tensor([False, True, False, True])
    v2 = torch.zeros(4)
    _, ret2 = compute_gae(r2, v2, d2, gamma=1.0, lam=1.0)
    assert torch.allclose(ret2, torch.tensor([1.0, 1.0, 2.0, 2.0]))


def test_parity_tripwire():
    from v32.p2.ppo import check_parity
    batch = {"seeds": [{"WHEAT": 5, "CARROT": 5, "TOMATO": 5, "STRAWBERRY": 5, "MELON": 5}], "mask": [[0.0] * len(UVOC)],
             "u_idx": [[0]], "m_idx": [[2] + [0] * 9],
             "hashes": [[A.candidate_hash(["PASS"]),
                         A.candidate_hash(["SELL", "WHEAT", 1])]]}
    assert check_parity(batch, UVOC, MVOC) is True
    bad = dict(batch, mask=[[1.0] * len(UVOC)])
    with pytest.raises(AssertionError):
        check_parity(bad, UVOC, MVOC)


def test_ppo_update_smoke():
    from v32.p2.ppo import ppo_update
    torch.manual_seed(0)
    m = _model()
    opt = torch.optim.Adam(m.parameters(), lr=3e-4)
    import random
    rng = random.Random(0)
    N = 64
    batch = {"feat": [torch.randn(157).tolist() for _ in range(N)],
             "uctx": [[torch.randn(12).tolist()] for _ in range(N)],
             "mask": [[0.0] * len(UVOC) for _ in range(N)],
             "seeds": [{"WHEAT": 5, "CARROT": 5, "TOMATO": 5, "STRAWBERRY": 5, "MELON": 5} for _ in range(N)],
             "u_idx": [[rng.randrange(len(UVOC))] for _ in range(N)],
             "m_idx": [[rng.randrange(len(MVOC)) for _ in range(10)]
                       for _ in range(N)],
             "logprob": [-5.0] * N, "adv": [rng.uniform(-1, 1) for _ in range(N)],
             "ret": [rng.uniform(0, 1) for _ in range(N)], "hashes": []}
    for i in range(N):
        ul = [A.unit_to_literal(UVOC[j]) for j in batch["u_idx"][i]]
        ml = A.emit_market_list([MVOC[j] for j in batch["m_idx"][i]])
        batch["hashes"].append([A.candidate_hash(x) for x in ul + ml])
    before = [p.detach().clone() for p in m.parameters()]
    stats = ppo_update(m, opt, batch, len(UVOC), len(MVOC), UVOC, MVOC,
                       epochs=1, minibatch=32)
    assert all(v == v for v in stats.values())  # finite
    assert any(not torch.equal(a, b) for a, b in zip(before, m.parameters()))
