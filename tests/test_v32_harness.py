# SPDX-License-Identifier: MIT
"""V32 harness tests (§51 items 8, 14, 15). RUNS MATCHES on commissioning seeds.

Consumes ONLY 249673-249674 (V32-TRAIN commissioning pair, documented in
V32_BASELINE_FREEZE.md addendum A1 + V32_QUAL_MANIFEST.json). Never touches
protected holdouts, CONFIRM, or any other cohort. Slow (~60s): run with the
V32 gate, not in the fast pre-commit loop.
"""

import os
import sys
from concurrent.futures import ProcessPoolExecutor

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))
sys.path.insert(0, REPO_ROOT)

from v32_common import assert_frozen  # noqa: E402
from v32_exp1_benchmark import run_one  # noqa: E402

SEED_A, SEED_B = 249673, 249674


def test_deterministic_evaluation():
    """§51(8): same leg twice in-process -> identical action+money digests."""
    assert_frozen()
    spec = {"left": "E2_A7", "right": "E0_V3", "seed": SEED_A, "mode": "serial"}
    r1 = run_one(dict(spec))
    r2 = run_one(dict(spec))
    assert r1["action_digest"] == r2["action_digest"]
    assert r1["money_digest"] == r2["money_digest"]
    assert r1["delta"] == r2["delta"]


def test_serial_parallel_parity():
    """§51(14): serial vs fresh-process pool -> identical digests."""
    assert_frozen()
    specs = [{"left": "E2_A7", "right": "E6_W72", "seed": SEED_B, "mode": "serial"},
             {"left": "E6_W72", "right": "E2_A7", "seed": SEED_A, "mode": "serial"}]
    serial = [run_one(dict(s)) for s in specs]
    with ProcessPoolExecutor(max_workers=2, max_tasks_per_child=1) as ex:
        pool = list(ex.map(run_one, [dict(s, mode="pool") for s in specs]))
    for rs, rp in zip(sorted(serial, key=lambda r: r["key"]),
                      sorted(pool, key=lambda r: r["key"])):
        assert rs["key"] == rp["key"]
        assert rs["action_digest"] == rp["action_digest"], rs["key"]
        assert rs["money_digest"] == rp["money_digest"], rs["key"]


def test_packaged_candidate_parity():
    """§51(15) at V32 stage: packaged A7 (E9_AST file) ties adapter A7 exactly."""
    assert_frozen()
    r = run_one({"left": "E2_A7", "right": "E9_AST", "seed": SEED_B,
                 "mode": "serial"})
    assert r["delta"] == 0, r
    assert r["winner"] == "TIE"
