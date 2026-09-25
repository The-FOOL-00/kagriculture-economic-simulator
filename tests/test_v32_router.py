# SPDX-License-Identifier: MIT
"""V32 R1 router tests: splits, leakage, boundary, labels, metrics, determinism.

Fast, no matches. Torch-only tests skip when torch is unavailable (they run
under system python3); everything else runs in .venv.
"""

import json
import os
import sys

import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, REPO_ROOT)
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))

from v32.router import baselines as B  # noqa: E402
from v32.router import labels as L  # noqa: E402
from v32.router import leakage_checks as LC  # noqa: E402
from v32.router import metrics as M  # noqa: E402
from v32.router import oracle as O  # noqa: E402
from v32.router.features import build_a_id, build_b, dim_of  # noqa: E402
from v32.router.split import (OPP_PANEL, ROUTER_CLASSES, SPLIT_OF,  # noqa: E402
                              load_splits)


def _row(seed=249635, opp="E0_V3", split="train", cash=None, mode="full"):
    cash = cash or [100000.0, 101000.0, 99000.0, 92000.0, 102000.0]
    win = [1.0 if c == max(cash) else 0.0 for c in cash]
    return {"seed": seed, "opp": opp, "split": split, "mode": mode,
            "cash": list(cash), "win": win,
            "margin": [c - cash[1] for c in cash],
            "prefix": {"frames": {"0": [0.0] * 90, "12": [0.0] * 90,
                                  "24": [0.1] * 90},
                       "wheat": {"0": 25, "24": 28},
                       "inv_wheat": {"0": 9000, "24": 8900},
                       "cash": {"0": [3000.0, 3000.0],
                                "24": [5000.0, 5100.0]},
                       "canonical": True}}


# --- splits ---

def test_split_registry_matches_json():
    sp = load_splits()
    assert len(sp["train"]) == 10 and len(sp["val"]) == 5
    assert len(sp["test"]) == 32 and len(sp["locked"]) == 8
    assert len(sp["test"]) + len(sp["locked"]) == 40
    for name in ("train", "val", "test", "locked", "spare"):
        for s in sp[name]:
            assert SPLIT_OF[s] == name, s
    assert 249673 not in SPLIT_OF and 249674 not in SPLIT_OF


def test_split_disjoint_and_ordered():
    sp = load_splits()
    seen = set()
    for name in ("train", "val", "test", "locked", "spare"):
        for s in sp[name]:
            assert s not in seen, s
            seen.add(s)


def test_audit_rows_accepts_clean_rejects_dirty():
    rows = [_row(249635, "E0_V3", "train"), _row(249650, "E2_A7", "test")]
    assert LC.audit_rows(rows) == {"train": 1, "test": 1}
    with pytest.raises(AssertionError):
        LC.audit_rows([_row(249695, "E0_V3", "locked")])  # CONFIRM
    with pytest.raises(AssertionError):
        LC.audit_rows([_row(214200, "E0_V3", "train")])  # protected
    with pytest.raises(AssertionError):
        LC.audit_rows([_row(249673, "E0_V3", "train")])  # commissioning
    with pytest.raises(AssertionError):
        LC.audit_rows([_row(249635, "E0_V3", "train"),
                       _row(249635, "E2_A7", "test")])  # seed in 2 splits
    bad = _row()
    bad["prefix"] = dict(bad["prefix"], canonical=False)
    with pytest.raises(AssertionError):
        LC.audit_rows([bad])  # mirror prefix
    bad2 = _row()
    bad2["prefix"]["frames"]["36"] = [0.0] * 90
    with pytest.raises(AssertionError):
        LC.audit_rows([bad2])  # future frame


# --- features / leakage ---

def test_feature_dims_and_no_seed_leak():
    r = _row()
    assert len(build_a_id(r)) == dim_of("a_id") == 7
    assert len(build_b(r, "none")) == dim_of("b", "none") == 113
    assert len(build_b(r, "short")) == dim_of("b", "short") == 203
    assert len(build_b(r, "longer")) == dim_of("b", "longer") == 293
    # identical rows except seed id -> identical features (no seed leak)
    r2 = _row(seed=249650)
    assert build_b(r) == build_b(r2)
    assert build_a_id(r) == build_a_id(r2)
    assert LC.audit_features([build_b(r)]) == 293


def test_step0_obs_constant_across_seeds():
    """P1-F10: step-0 state carries zero bits (Regime A provably constant)."""
    pytest.importorskip("kaggle_environments")
    from kaggle_environments import make
    from v32_encoder import encode_obs
    vecs = []
    for s in (249635, 249636):
        env = make("kaggriculture", configuration={"seed": s})
        vecs.append(encode_obs(env.state[0]["observation"], 0))
    assert vecs[0] == vecs[1]


def test_expert_digests_immutable_in_records():
    """Every recorded leg resolves experts to frozen digests (immutability)."""
    sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))
    from v32_common import DIGESTS, expert_digest
    n = 0
    with open(os.path.join(REPO_ROOT, "results", "v32_exp1.jsonl")) as f:
        for line in f:
            r = json.loads(line)
            for side, key in (("left", "left_digest"), ("right", "right_digest")):
                eid = r[side]
                if eid in ("E9_AST", "E10_PASS"):
                    continue
                assert r[key] == expert_digest(eid), (r["key"], side)
                n += 1
            if n > 60:
                break
    assert n > 60
    assert DIGESTS["v22r1_tarball"].startswith("6b879b3e")


# --- labels / oracle ---

def test_admissible_band_and_soft_target():
    assert L.admissible_set([100.0, 200.0, 250.0, 800.0, 801.0]) == [3, 4]
    t = L.soft_target([100.0, 200.0, 250.0, 800.0, 801.0])
    assert t == [0.0, 0.0, 0.0, 0.5, 0.5]
    assert abs(sum(t) - 1.0) < 1e-12
    assert L.hard_target([1.0, 5.0, 5.0, 2.0, 0.0]) == 1  # fixed tie-break
    p = L.preference_target([100000.0, 102000.0, 99000.0, 92000.0, 101000.0])
    assert abs(sum(p) - 1.0) < 1e-12 and max(p) == p[1]
    assert L.wl_target([1.0, 1.0, 0.0, 0.0, 0.5],
                       [100.0, 200.0, 0.0, 0.0, 150.0]) == 1  # cash tie-break


def test_oracle_picks_best():
    r = _row(cash=[100000.0, 101000.0, 99000.0, 92000.0, 102000.0])
    assert O.oracle_cash(r) == 4
    assert O.oracle_cash_value(r) == 102000.0
    assert O.oracle_wl(r) == 4


# --- baselines / metrics ---

def test_baselines_deterministic():
    rows = [_row(249635 + i, o, "train") for i, o in enumerate(OPP_PANEL)]
    assert B.FixedExpert("E2_A7").predict(rows) == [1] * len(rows)
    assert B.RandomExpert(0).predict(rows) == B.RandomExpert(0).predict(rows)
    m1a, m1b = B.PerOpponentLookup(), B.PerOpponentLookup()
    m1a.fit(rows)
    m1b.fit(rows)
    assert m1a.predict(rows) == m1b.predict(rows)
    assert set(m1a.predict(rows)) <= set(range(5))


def test_metrics_regret_math():
    rows = [_row(249635, "E0_V3", "test",
                 cash=[100000.0, 101000.0, 99000.0, 92000.0, 102000.0]),
            _row(249636, "E2_A7", "test",
                 cash=[103000.0, 101500.0, 99000.0, 92000.0, 102000.0])]
    m, per = M.evaluate(rows, [1, 1], tag="t")
    assert m["n"] == 2 and m["mean_cash"] == 101250.0
    assert m["mean_regret"] == ((102000 - 101000) + (103000 - 101500)) / 2
    assert m["catastrophic"] == 0
    assert m["seed_positive_frac"] == 0.0  # A7 vs itself
    ci = M.seed_bootstrap_ci(rows, [4, 0], [1, 1], n_boot=200, seed=0)
    assert ci["lo"] <= ci["est"] <= ci["hi"]
    ci2 = M.seed_bootstrap_ci(rows, [4, 0], [1, 1], n_boot=200, seed=0)
    assert ci == ci2  # deterministic


def test_drop_one_seed_sensitivity():
    rows = [_row(249635 + i, "E0_V3", "test") for i in range(3)]
    d = M.drop_one_seed(rows, [4, 4, 4], [1, 1, 1])
    assert set(d) == {249635, 249636, 249637}
    assert all(v == 1000.0 for v in d.values())


# --- torch router determinism ---

def _need_torch():
    return pytest.importorskip("torch")


def test_router_models_deterministic_init():
    torch = _need_torch()
    from v32.router.models import build, param_count
    torch.manual_seed(0)
    a = build("small", 293)
    torch.manual_seed(0)
    b = build("small", 293)
    for pa, pb in zip(a.parameters(), b.parameters()):
        assert torch.equal(pa, pb)
    assert param_count(a) == (293 + 1) * 64 + 65 * 32 + 33 * 5 == 21061
    assert param_count(build("medium", 293)) == 48133
    assert param_count(build("logistic", 7)) == 8 * 5 == 40


def test_train_loop_reproducible(tmp_path):
    torch = _need_torch()
    import numpy as np
    from v32.router.train import train_model
    rng = np.random.RandomState(0)
    X = rng.randn(12, 7)
    Y = np.eye(5)[rng.randint(0, 5, 12)]
    kw = dict(model_name="logistic", seed=3, epochs=20, patience=20)
    s1, _, v1, _ = train_model(X, Y, X, Y, **kw)
    s2, _, v2, _ = train_model(X, Y, X, Y, **kw)
    assert v1 == v2
    for k in s1:
        assert torch.equal(s1[k], s2[k])
