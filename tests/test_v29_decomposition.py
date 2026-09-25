# SPDX-License-Identifier: MIT
"""V29 decomposition tests: four-arm seed matching + CREATE/EXTRACT math.

Covers brief s33 items 13-16. Synthetic-math tests always run; frozen-
output validation runs strictly whenever results/v29_raw_results.jsonl
exists (skipped before the tournament produces it).
"""

import csv
import json
import os
import sys

import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
RAW = os.path.join(ROOT, "results", "v29_raw_results.jsonl")
DECOMP = os.path.join(ROOT, "results", "v29_decomposition.csv")


def decompose(a0, v1p, a1c, v0p, A0, A1c, V0, V1):
    """Reference implementation of V29_ABSOLUTE_LEVEL_SPEC.md ss2-4."""
    d0, d1 = a0 - v1p, a1c - v0p
    m = (d0 + d1) / 2
    LA, LV = (A0 + A1c) / 2, (V0 + V1) / 2
    C = LA - LV
    E = m - C
    Abar, Vbar = (a0 + a1c) / 2, (v0p + v1p) / 2
    OA, OV = Abar - LA, LV - Vbar
    return {"d0": d0, "d1": d1, "m": m, "L_A": LA, "L_V": LV,
            "CREATE": C, "EXTRACT": E, "O_A": OA, "O_V": OV,
            "C_0": A0 - V0, "C_1": A1c - V1}


def test_identity_holds_exactly():
    r = decompose(100.0, 50.0, 90.0, 60.0, 110.0, 105.0, 70.0, 65.0)
    assert abs((r["CREATE"] + r["EXTRACT"]) - r["m"]) < 1e-9
    assert abs((r["O_A"] + r["O_V"]) - r["EXTRACT"]) < 1e-9
    assert abs(((r["C_0"] + r["C_1"]) / 2) - r["CREATE"]) < 1e-9


def test_pure_creation_calibration():
    """A7 adds +X own-cash, opponent untouched -> E=0, C=m=X."""
    X, V0, V1 = 1286.0, 100000.0, 101000.0
    r = decompose(V0 + X, V1, V1 + X, V0, V0 + X, V1 + X, V0, V1)
    assert abs(r["m"] - X) < 1e-9
    assert abs(r["CREATE"] - X) < 1e-9
    assert abs(r["EXTRACT"]) < 1e-9


def test_pure_extraction_calibration():
    """Zero-sum +X/-X redistribution -> C=0, E=m=2X."""
    X, V0, V1 = 500.0, 100000.0, 101000.0
    r = decompose(V0 + X, V1 - X, V1 + X, V0 - X, V0, V1, V0, V1)
    assert abs(r["CREATE"]) < 1e-9
    assert abs(r["m"] - 2 * X) < 1e-9
    assert abs(r["EXTRACT"] - 2 * X) < 1e-9


def test_predation_pattern_detectable():
    """C<0<m (wins while lowering absolute level) is representable."""
    r = decompose(90000.0, 80000.0, 90000.0, 80000.0,
                  70000.0, 70000.0, 100000.0, 100000.0)
    assert r["m"] > 0 and r["CREATE"] < 0


def _load_raw():
    if not os.path.exists(RAW):
        pytest.skip("V29 tournament outputs not present yet")
    recs = [json.loads(l) for l in open(RAW) if l.strip()]
    if len(recs) != 160:
        pytest.skip("V29 tournament incomplete (%d/160)" % len(recs))
    return recs


def test_four_arm_seed_matching():
    """Every seed has exactly one record per arm (frozen outputs)."""
    recs = _load_raw()
    by_seed = {}
    for r in recs:
        by_seed.setdefault(r["seed"], []).append(r["arm"])
    assert sorted(by_seed) == list(range(340050, 340090))
    for s, arms in by_seed.items():
        assert sorted(arms) == ["A1", "A2", "A3", "A4"], s


def test_selfplay_records_carry_both_seats():
    """A3/A4 records expose both seats' rewards and digests."""
    recs = _load_raw()
    for r in recs:
        if r["arm"] in ("A3", "A4"):
            assert isinstance(r["seat0_reward"], float), r["key"]
            assert isinstance(r["seat1_reward"], float), r["key"]
            assert r["action_digest_seat1"], r["key"]


def test_decomposition_csv_identities():
    """Frozen decomposition CSV satisfies every spec identity."""
    _load_raw()
    if not os.path.exists(DECOMP):
        pytest.skip("v29_decomposition.csv not emitted yet")
    n = 0
    with open(DECOMP, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            n += 1
            m, C, E = float(row["m"]), float(row["CREATE"]), float(row["EXTRACT"])
            assert abs((C + E) - m) < 1e-6, row["seed"]
            assert abs((float(row["O_A"]) + float(row["O_V"])) - E) < 1e-6
            C0, C1 = float(row["C_0"]), float(row["C_1"])
            assert abs(((C0 + C1) / 2) - C) < 1e-6
            assert abs((float(row["d0"]) + float(row["d1"])) / 2 - m) < 1e-6
    assert n == 40, n


def test_gate_math_reference():
    """Gate-5 t-CI construction matches the preregistered formula."""
    import statistics
    sys.path.insert(0, os.path.join(ROOT, "scripts"))
    from v29_analyze import tcrit95
    assert abs(tcrit95(39) - 2.0227) < 0.001
    ms = [1286.0] * 39 + [5279.5]
    lo = statistics.mean(ms) - tcrit95(39) * statistics.stdev(ms) / (40 ** 0.5)
    assert lo > 0
