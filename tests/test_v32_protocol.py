# SPDX-License-Identifier: MIT
"""V32 protocol tests (§51 items 5, 6, 9, 10, 12, 13). Fast, no matches."""

import copy
import inspect
import os
import random
import sys

import numpy as np

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))
sys.path.insert(0, REPO_ROOT)

from v32_encoder import V32_OBS_DIM, encode_obs, mask_for, validate_action  # noqa: E402
from v32_gate import digests_equal, evaluate_gate  # noqa: E402
from v32_sample import (classify_leg, family_weights,  # noqa: E402
                        sample_opponent_sequence, sample_replay_batch)


def _obs():
    farm = {"money": 5000.0, "farmer": [4, 4], "hands": [[2, 3]],
            "hires_today": 3, "unlocked_quadrants": ["NW"],
            "tiles": [[None, {"kind": "PLANT", "crop": "WHEAT", "yield_units": 2,
                              "watered_today": True}]]}
    return {"step": 100, "day": 4, "hour": 4, "player": 0,
            "farms": [copy.deepcopy(farm), copy.deepcopy(farm)],
            "private": {"shed": {"WHEAT": 100, "COW": 2}, "seeds": {"WHEAT": 5},
                        "inventories": [{}, {"WHEAT": 1}]},
            "town": {"unlocked_shops": ["FARMERS_MARKET"]},
            "market": {"prices": {"WHEAT": 41}, "inventory": {"WHEAT": 9000}}}


def test_encoder_dim_and_determinism():
    v1 = encode_obs(_obs(), 0)
    v2 = encode_obs(_obs(), 0)
    assert len(v1) == V32_OBS_DIM == 90
    assert v1 == v2
    assert all(-8.0 <= x <= 8.0 for x in v1)


def test_encoder_no_seed_input():
    """§51(12): encoder signature cannot take seed/replay identity."""
    params = set(inspect.signature(encode_obs).parameters)
    assert params == {"observation", "player"}


def test_encoder_no_future_leakage():
    """§51(5): opponent-private/hidden perturbations are invisible; public visible."""
    base = encode_obs(_obs(), 0)
    # opponent private does not exist in the schema; simulate a rogue field
    o = _obs()
    o["opponent_private"] = {"shed": {"WHEAT": 999999}}
    o["seed"] = 12345
    o["future_reward"] = 1e9
    assert encode_obs(o, 0) == base
    # opponent PUBLIC farm change must register (observability, not leakage)
    o2 = _obs()
    o2["farms"][1]["money"] = 99999.0
    assert encode_obs(o2, 0) != base
    # own money change registers
    o3 = _obs()
    o3["farms"][0]["money"] = 1.0
    assert encode_obs(o3, 0) != base


def test_legal_mask():
    """§51(6): validator accepts expert-shaped actions, rejects bad ones."""
    good = {"farmer": ["NORTH"],
            "hands": [["PICKUP", "SHEEP"], ["PASS"]],
            "market": [["BUY_PRODUCT", "WHEAT", 30], ["SELL", "WHEAT", 30],
                       ["HIRE"]]}
    ok, reason = validate_action(good, 2)
    assert ok, reason
    bad_hands = dict(good, hands=[[ "PASS"]])
    assert not validate_action(bad_hands, 2)[0]
    bad_op = {"farmer": ["TELEPORT"], "hands": [], "market": []}
    assert not validate_action(bad_op, 0)[0]
    bad_mkt = {"farmer": ["PASS"], "hands": [],
               "market": [["MINT", "CASH", 10**9]]}
    assert not validate_action(bad_mkt, 0)[0]
    assert mask_for(5)["n_unit_ops"] >= 18


def test_sampling_reproducibility_and_floor():
    """§51(10): seeded sampler reproduces; every family floored over 10k draws."""
    a = sample_opponent_sequence(7, 10000)
    b = sample_opponent_sequence(7, 10000)
    assert a == b
    c = sample_opponent_sequence(8, 10000)
    assert a != c
    from v32_sample import FAMILIES
    fam_of = {e: f for f, ms in FAMILIES.items() for e in ms}
    counts = {}
    for x in a:
        if x in fam_of:
            counts[fam_of[x]] = counts.get(fam_of[x], 0) + 1
    for f in FAMILIES:
        assert counts.get(f, 0) / 10000 >= 0.04, (f, counts.get(f, 0))
    w = family_weights()
    assert abs(sum(w.values()) - 1.0) < 1e-9


def test_replay_priorities():
    assert classify_leg(5000) == "win"
    assert classify_leg(-5000) == "loss"
    assert classify_leg(500) == "close"
    assert classify_leg(-30000) == "catastrophe"
    assert classify_leg(5000, strong_opp=True) == "strong_opp"
    legs = [{"delta": 5000, "id": "w"}, {"delta": -5000, "id": "l"}]
    batch = sample_replay_batch(random.Random(3), legs, 2000)
    n_loss = sum(1 for x in batch if x["id"] == "l")
    assert 0.6 < n_loss / 2000 < 0.9  # 3:1 weighting


def _legs(wins, losses, per_fam_delta, fams=("f1", "f2", "f3"), opp="E0_V3"):
    legs = []
    for i in range(wins):
        legs.append({"key": "w%d" % i, "seed": i, "seat": 0, "opponent": opp,
                     "learner_cash": 100000 + per_fam_delta,
                     "champion_cash": 100000, "family": fams[i % len(fams)],
                     "action_digest": "a"})
    for i in range(losses):
        legs.append({"key": "l%d" % i, "seed": 100 + i, "seat": 1, "opponent": opp,
                     "learner_cash": 100000 + per_fam_delta,
                     "champion_cash": 100000 + abs(per_fam_delta),
                     "family": fams[i % len(fams)], "action_digest": "b"})
    return legs


def _fam_of(opp):
    return {"E0_V3": "f1", "E1_V22R1": "f2", "E2_A7": "f3"}[opp]


def _make_pass_legs():
    legs = []
    k = 0
    for opp in ("E0_V3", "E1_V22R1", "E2_A7"):
        for i in range(8):  # 6-2 per family
            win = i < 6
            legs.append({"key": "k%d" % k, "seed": k, "seat": 0, "opponent": opp,
                         "learner_cash": 101000 if win else 99500,
                         "champion_cash": 100000, "family": _fam_of(opp),
                         "action_digest": "d%d" % k})
            k += 1
    return legs


def test_gate_pass_and_clause_failures():
    """§51(13): gate passes a clean promotion; each clause can fail it."""
    ok, rep = evaluate_gate(_make_pass_legs(), "L", "C", _fam_of)
    assert ok, rep
    assert rep["wins"] == 18 and rep["losses"] == 6
    # c5 tail: one -$30k leg fails
    legs = _make_pass_legs()
    legs[0] = dict(legs[0], learner_cash=70000)
    ok, rep = evaluate_gate(legs, "L", "C", _fam_of)
    assert not ok and not rep["clauses"]["c5_no_tail"]
    # c6 family collapse: lose a whole family 0-8
    legs = _make_pass_legs()
    for i, l in enumerate(legs):
        if l["opponent"] == "E2_A7":
            legs[i] = dict(l, learner_cash=99000)
    ok, rep = evaluate_gate(legs, "L", "C", _fam_of)
    assert not ok and not rep["clauses"]["c6_no_family_collapse"]
    # c7 breadth: positive in only 2 families
    legs = []
    k = 0
    for opp, nwin in (("E0_V3", 8), ("E1_V22R1", 8), ("E2_A7", 3)):
        for i in range(8):
            win = i < nwin
            legs.append({"key": "k%d" % k, "seed": k, "seat": 0, "opponent": opp,
                         "learner_cash": 100100 if win else 99900,
                         "champion_cash": 100000, "family": _fam_of(opp),
                         "action_digest": "x"})
            k += 1
    ok, rep = evaluate_gate(legs, "L", "C", _fam_of)
    assert not ok and not rep["clauses"]["c7_breadth"]
    # c3/c4: more losses than wins
    legs = _make_pass_legs()
    for i in range(14):
        legs[i] = dict(legs[i], learner_cash=99000)
    ok, rep = evaluate_gate(legs, "L", "C", _fam_of)
    assert not ok and not rep["clauses"]["c3_wr_gt_half"]
    # clause 8 comparator
    run = [{"key": "k1", "action_digest": "aa"}]
    assert digests_equal(run, copy.deepcopy(run))
    assert not digests_equal(run, [{"key": "k1", "action_digest": "bb"}])
    assert not digests_equal(run, [{"key": "k2", "action_digest": "aa"}])


def test_checkpoint_restore_numpy_probe(tmp_path):
    """§51(9) at R0 rung: save/restore a linear probe -> bitwise-identical eval."""
    rng = np.random.RandomState(0)
    W = rng.randn(90, 4)
    ckpt = str(tmp_path / "r0.npz")
    meta = {"encoder": "v32enc-v1.1", "step": 100, "rng": 0}
    np.savez(ckpt, W=W, meta=json_dumps(meta))
    d = np.load(ckpt, allow_pickle=True)
    W2 = d["W"]
    x = rng.randn(7, 90)
    assert np.array_equal(x @ W, x @ W2)
    assert json_loads(str(d["meta"]))["encoder"] == "v32enc-v1.1"


def json_dumps(o):
    import json as _j
    return _j.dumps(o, sort_keys=True)


def json_loads(s):
    import json as _j
    return _j.loads(s)
