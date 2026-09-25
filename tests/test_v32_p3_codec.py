# SPDX-License-Identifier: MIT
"""V32 P3 codec tests: schema, edge cases, full round-trip (G1), execution identity.

G1 gate: round-trip over all 172,560 recorded BC steps with 0 unexplained
semantic mismatches. Execution identity replays native vs decoded actions
through the live simulator on consumed seed 249635 (no new consumption).
"""

import json
import os
import sys

import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, REPO_ROOT)

from v32.p3 import codec as C  # noqa: E402

LEGS = os.path.join(REPO_ROOT, "results", "v32_p2_bc_legs.jsonl")


def test_schema_json_matches_codec():
    s = C.load_schema()
    assert s["heads"]["U_OP"]["n"] == len(C.U_OP) == 18
    assert s["heads"]["U_ARG"]["n"] == len(C.U_ARG) == 12
    assert s["heads"]["U_QTY"]["n"] == len(C.U_QTY) == 17
    assert s["heads"]["M_OP"]["n"] == len(C.M_OP) == 7
    assert s["heads"]["M_ITEM"]["n"] == len(C.M_ITEM) == 12
    assert s["heads"]["M_QTY"]["n"] == len(C.M_QTY) == 77
    assert s["heads"]["U_OP"]["classes"] == C.U_OP
    assert s["heads"]["M_OP"]["classes"] == C.M_OP
    assert s["heads"]["M_QTY"]["classes"] == C.M_QTY
    assert s["max_dims"]["market_slots_M"] == C.M_MARKET_SLOTS == 10
    assert s["provenance"]["vocab_source"].startswith(
        "results/v32_p2_vocab.json")


def test_unit_edge_cases():
    # exact round-trips (no flags)
    for lit in (["PASS"], ["NORTH"], ["PLANT", "WHEAT"],
                ["PICKUP", "WHEAT"], ["PICKUP", "WHEAT", 2],
                ["PLACE", "COW"], ["PLACE", "WHEAT", 5], ["DROP"],
                ["DIG"], ["CARE"], ["COLLECT_FERTILIZER"]):
        o, a, q, fl = C.encode_unit(lit)
        assert fl == [], (lit, fl)
        assert C.decode_unit(o, a, q) == lit, lit
    # N1: unknown opcode -> PASS
    for lit in (["WEED"], ["FOO"], ["", "X"], [None]):
        o, a, q, fl = C.encode_unit(lit)
        assert fl == ["N1"] and C.decode_unit(o, a, q) == ["PASS"], lit
    # missing/empty -> PASS (simulator-identical no-op), no flag
    for lit in (None, [], "PASS", {"op": "PASS"}):
        o, a, q, fl = C.encode_unit(lit)
        assert (o, a, q, fl) == (0, 0, 0, []), lit
    # N3: trailing args dropped
    o, a, q, fl = C.encode_unit(["PASS", "X"])
    assert fl == ["N3"] and C.decode_unit(o, a, q) == ["PASS"]
    # malformed PLANT/PICKUP/PLACE -> PASS + N3 (simulator silent no-op)
    for lit in (["PLANT"], ["PLANT", "COOP"], ["PICKUP"], ["PICKUP", "COOP"],
                ["PLACE"], ["PLACE", "COOP"]):
        o, a, q, fl = C.encode_unit(lit)
        assert fl == ["N3"] and C.decode_unit(o, a, q) == ["PASS"], lit
    # unexecutable qty (simulator would RAISE) -> PASS + N3
    o, a, q, fl = C.encode_unit(["PICKUP", "WHEAT", "abc"])
    assert fl == ["N3"] and C.decode_unit(o, a, q) == ["PASS"]
    # N2: OOV qty -> nearest
    o, a, q, fl = C.encode_unit(["PICKUP", "WHEAT", 11])
    assert fl == ["N2"] and C.decode_unit(o, a, q) == ["PICKUP", "WHEAT", 10]
    o, a, q, fl = C.encode_unit(["PLACE", "WHEAT", 999])
    assert fl == ["N2"] and C.decode_unit(o, a, q) == ["PLACE", "WHEAT", 1000]


def test_market_edge_cases():
    for lit in (["SELL", "WHEAT", 50], ["BUY_SEED", "MELON", 7],
                ["BUY_PRODUCT", "WHEAT", 983], ["BUY_ANIMAL", "COW", 1],
                ["HIRE"], ["BUY_LAND"], [], ["SELL", "WHEAT", 0]):
        o, i, q, fl = C.encode_market(lit)
        assert fl == [], (lit, fl)
        assert C.decode_market(o, i, q) == lit, lit
    assert C.encode_market(None)[:3] == (0, 0, 0)
    # N1 / N3
    o, i, q, fl = C.encode_market(["WEED", "X", 1])
    assert fl == ["N1"] and C.decode_market(o, i, q) == []
    o, i, q, fl = C.encode_market(["SELL", "WHEAT"])  # len<3: sim parses None
    assert fl == ["N3"] and C.decode_market(o, i, q) == []
    o, i, q, fl = C.encode_market(["HIRE", "x"])
    assert fl == ["N3"] and C.decode_market(o, i, q) == ["HIRE"]
    o, i, q, fl = C.encode_market(["SELL", "WHEAT", "abc"])
    assert fl == ["N3"] and C.decode_market(o, i, q) == []
    # N2: OOV qty -> nearest (26 -> 25)
    o, i, q, fl = C.encode_market(["SELL", "WHEAT", 26])
    assert fl == ["N2"] and C.decode_market(o, i, q) == ["SELL", "WHEAT", 25]


def test_action_level_truncation_and_caps():
    act = {"farmer": ["PASS"], "hands": [["PASS"]] * 3,
           "market": [["HIRE"]] * 12}
    enc = C.encode_action(act, 3)
    assert len(enc["u"]) == 4 and len(enc["m"]) == 10
    assert "M:TRUNC" in enc["flags"]
    dec = C.decode_action(enc["u"], enc["m"])
    assert len(dec["market"]) == 10  # simulator truncates identically
    enc2 = C.encode_action(act, 1)
    assert "U:TRUNC" in enc2["flags"]
    with pytest.raises(AssertionError):
        C.encode_action(act, 17)
    # missing hands default to PASS; trailing market [] stripped
    enc3 = C.encode_action({"farmer": ["NORTH"]}, 2)
    dec3 = C.decode_action(enc3["u"], enc3["m"])
    assert dec3 == {"farmer": ["NORTH"], "hands": [["PASS"], ["PASS"]],
                    "market": []}


def test_codec_determinism_and_fixpoint():
    act = {"farmer": ["PLANT", "WHEAT"], "hands": [["PICKUP", "EGG", 3]],
           "market": [["BUY_SEED", "WHEAT", 30], ["SELL", "WHEAT", 30]]}
    e1 = C.encode_action(act, 1)
    e2 = C.encode_action(act, 1)
    assert e1 == e2
    dec = C.decode_action(e1["u"], e1["m"])
    assert dec == act
    e3 = C.encode_action(dec, 1)
    assert e3 == e1  # target-level fixpoint


def test_plant_crop_masked_helper():
    assert C.plant_crop_masked({}, "WHEAT") is True
    assert C.plant_crop_masked({"WHEAT": 0}, "WHEAT") is True
    assert C.plant_crop_masked({"WHEAT": 5}, "WHEAT") is False


def _norm_diff_unit(orig, dec):
    """Classify unit literal difference; None = unexplained mismatch."""
    if dec == orig:
        return None
    if not isinstance(orig, list) or not orig:
        return None if dec != ["PASS"] else "ok-empty"
    if orig[0] not in C._U_OP_ID:
        return "N1" if dec == ["PASS"] else None
    if orig[0] in C.U_NOPARAM:
        return "N3" if dec == [orig[0]] else None
    if orig[0] == "PLANT":
        if len(orig) < 2 or orig[1] not in C.CROPS:
            return "N3" if dec == ["PASS"] else None
        return "N3" if dec == orig[:2] else None
    if len(orig) < 2 or orig[1] not in C._U_ARG_ID:
        return "N3" if dec == ["PASS"] else None
    if len(orig) < 3:
        return "N3" if dec == orig else None
    try:
        q = C._coerce_int(orig[2])
    except (ValueError, TypeError):
        return "N3" if dec == ["PASS"] else None
    if q not in C._U_QTY_ID:
        return "N2" if dec == [orig[0], orig[1], C._nearest(
            C._U_QTY_INTS, q)] else None
    return "N3" if dec == orig[:3] else None


def _norm_diff_market(orig, dec):
    if dec == orig:
        return None
    if not isinstance(orig, list) or not orig:
        return None if dec != [] else "ok-empty"
    if orig[0] not in C._M_OP_ID:
        return "N1" if dec == [] else None
    if orig[0] in ("HIRE", "BUY_LAND"):
        return "N3" if dec == [orig[0]] else None
    if len(orig) < 3 or orig[1] not in C._M_ITEM_ID:
        return "N3" if dec == [] else None
    try:
        q = C._coerce_int(orig[2])
    except (ValueError, TypeError):
        return "N3" if dec == [] else None
    if q not in C._M_QTY_ID:
        return "N2" if dec == [orig[0], orig[1], C._nearest(
            C.M_QTY, q)] else None
    return "N3" if dec == orig[:3] else None


def test_G1_full_roundtrip_zero_unexplained_mismatches():
    assert os.path.exists(LEGS), "P2 BC legs missing"
    n_steps = n_n1 = n_n2 = n_n3 = 0
    mismatches = []
    for line in open(LEGS):
        leg = json.loads(line)
        for side in ("rows0", "rows1"):
            for row in leg[side]:
                n_steps += 1
                ess, act = row["e"], row["a"] or {}
                n_h = len(ess.get("hands", []) or [])
                enc = C.encode_action(act, n_h)
                dec = C.decode_action(enc["u"], enc["m"])
                units_o = [act.get("farmer")] + list(act.get("hands") or [])
                units_d = [dec["farmer"]] + dec["hands"]
                # hands beyond live count are simulator-ignored; align first
                for j in range(1 + n_h):
                    o = units_o[j] if j < len(units_o) else ["PASS"]
                    cls = _norm_diff_unit(o, units_d[j])
                    if cls is None and units_d[j] != o:
                        mismatches.append(("U", leg["seed"], ess.get("step"),
                                           side, o, units_d[j]))
                    elif cls in ("N1",):
                        n_n1 += 1
                    elif cls == "N2":
                        n_n2 += 1
                    elif cls == "N3":
                        n_n3 += 1
                mkt_o = act.get("market") or []
                mkt_d = dec["market"]
                for s in range(C.M_MARKET_SLOTS):
                    o = mkt_o[s] if s < len(mkt_o) else []
                    d = mkt_d[s] if s < len(mkt_d) else []
                    cls = _norm_diff_market(o, d)
                    if cls is None and d != o:
                        mismatches.append(("M", leg["seed"], ess.get("step"),
                                           side, o, d))
                    elif cls == "N1":
                        n_n1 += 1
                    elif cls == "N2":
                        n_n2 += 1
                    elif cls == "N3":
                        n_n3 += 1
                # target-level fixpoint: re-encode(decoded) == targets
                re = C.encode_action(dec, n_h)
                assert re["u"] == enc["u"] and re["m"] == enc["m"], \
                    (leg["seed"], ess.get("step"), side)
    assert n_steps == 172560, n_steps
    assert n_n1 == 0, ("N1 occurrences", n_n1)
    assert n_n2 == 0, ("N2 occurrences", n_n2)
    print("G1: %d steps, N3=%d, mismatches=%d" % (n_steps, n_n3,
                                                  len(mismatches)))
    assert mismatches == [], mismatches[:5]


def test_execution_identity_native_vs_decoded():
    """Replay recorded seat-0 actions for seed 249635 natively vs decoded.

    Two live envs, PASS opponent, same seed: per-step money and tile hash
    must match exactly. Seed 249635 is consumed P2-TRAIN (T5 precedent).
    """
    from kaggle_environments import make
    wants = []
    for line in open(LEGS):
        leg = json.loads(line)
        if leg["seed"] == 249635:
            wants = [dict(r["a"]) for r in leg["rows0"]]
            break
    assert len(wants) == 719, len(wants)

    def run(mutate):
        env = make("kaggriculture", configuration={"seed": 249635})
        it = iter(wants)
        trace = []

        def learner(obs, cfg=None):
            a = next(it)
            if mutate:
                farms = (obs.get("farms", []) if isinstance(obs, dict)
                         else getattr(obs, "farms", [])) or []
                f0 = farms[0] if farms else {}
                hands = (f0.get("hands", []) if isinstance(f0, dict)
                         else getattr(f0, "hands", [])) or []
                n_h = len(hands)
                enc = C.encode_action(
                    {"farmer": a.get("farmer"), "hands": a.get("hands"),
                     "market": a.get("market")}, n_h)
                a = C.decode_action(enc["u"], enc["m"])
            return {"farmer": a.get("farmer"), "hands": a.get("hands"),
                    "market": a.get("market")}

        def opp(obs, cfg=None):
            return {"farmer": ["PASS"], "hands": [], "market": []}

        env.run([learner, opp])
        for st in env.steps:
            f = st[0]["observation"]["farms"][0]
            trace.append((round(float(f["money"]), 6),
                          json.dumps(f["tiles"], sort_keys=True)))
        return trace, float(env.steps[-1][0]["reward"])

    t_nat, r_nat = run(False)
    t_dec, r_dec = run(True)
    assert r_nat == r_dec
    assert t_nat == t_dec
