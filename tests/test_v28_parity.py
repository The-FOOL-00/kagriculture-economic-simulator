# SPDX-License-Identifier: MIT
"""V28 parity tests: serial/pool/subprocess equivalence + checkpoint resume.

All matches run on CONSUMED seeds (249434/249435, V25 cohort A).
"""

import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "scripts"))

from v28_confirmation_tournament import run_one, run_one_subprocess  # noqa: E402


def sig(r):
    return (r["cand_reward"], r["base_reward"], r["action_digest"],
            r["money_digest"])


def test_serial_pool_subprocess_parity():
    """Same consumed seed+seat across all three execution modes: identical."""
    from concurrent.futures import ProcessPoolExecutor
    seed, seat = 249434, 0
    serial = run_one({"seed": seed, "seat": seat, "mode": "serial"})
    with ProcessPoolExecutor(max_workers=1, max_tasks_per_child=1) as ex:
        pooled = ex.submit(run_one, {"seed": seed, "seat": seat,
                                     "mode": "pool"}).result()
    fresh = run_one_subprocess(seed, seat)
    assert sig(serial) == sig(pooled) == sig(fresh)
    assert serial["step0_rewritten"] is True
    assert fresh["step0_unexpected_shape"] is False


def test_deterministic_reward_and_digest():
    a = run_one({"seed": 249435, "seat": 1, "mode": "serial"})
    b = run_one({"seed": 249435, "seat": 1, "mode": "serial"})
    assert sig(a) == sig(b)


def test_checkpoint_resume_no_duplicates(tmp_path):
    """Runner resumes without duplicating completed matches."""
    import subprocess
    out = str(tmp_path / "v28_resume.jsonl")
    base = [sys.executable, os.path.join(ROOT, "scripts",
            "v28_confirmation_tournament.py"),
            "--seeds", "249434:249434", "--out", out, "--mode", "serial"]
    r1 = subprocess.run(base, capture_output=True, text=True, cwd=ROOT)
    assert r1.returncode == 0, r1.stderr[-1500:]
    n1 = len([l for l in open(out) if l.strip()])
    assert n1 == 2, n1
    r2 = subprocess.run(base, capture_output=True, text=True, cwd=ROOT)
    assert r2.returncode == 0, r2.stderr[-1500:]
    recs = [json.loads(l) for l in open(out) if l.strip()]
    assert len(recs) == 2, "resume duplicated matches!"
    assert len({r["key"] for r in recs}) == 2
