# SPDX-License-Identifier: MIT
"""V30 freeze/quarantine/integrity tests (no matches executed)."""

import hashlib
import json
import os
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, REPO_ROOT)
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))

V22R1_SHA = "6b879b3e499d2cf43b76884f6ef433479468b5c316f92cf4a8cc5119586fb3f5"
V3_SHA = "845e0d10981b11b06d272048ff5cee30d70a0403dd757651a556a78c8bf18943"
A7_FILE_SHA = "18d2c8ea2cf826b0bef71c96988dba0c93d7dbcc73936a0c99f07cb0539e7ae9"
AST_MAIN_SHA = "51c1d25245f68dd8de66b355f2ad6ca1d79de8af02efed521a5a82f7be69ce3f"


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def test_v22r1_frozen():
    assert sha256_file(os.path.join(REPO_ROOT, "submission_aec_v22r1.tar.gz")) == V22R1_SHA


def test_v3_frozen():
    assert sha256_file(os.path.join(REPO_ROOT, "submission_Vj_kc_v3.tar.gz")) == V3_SHA


def test_a7_adapter_frozen():
    assert sha256_file(os.path.join(REPO_ROOT, "aec", "backbone",
                                    "v27_ablation_adapters.py")) == A7_FILE_SHA


def test_ast_source_frozen():
    assert sha256_file(os.path.join(REPO_ROOT, "candidates",
                                    "v30_a7_standalone", "main.py")) == AST_MAIN_SHA


def test_harness_refuses_protected():
    from v30_gauntlet import check_seed_allowed
    for s in (340090, 340199, 340050, 340050 + 39, 214200, 214249, 340300, 340349):
        try:
            check_seed_allowed(s)
        except RuntimeError:
            continue
        raise AssertionError("seed %d not refused" % s)
    for s in (249570, 249590, 1547989980):
        check_seed_allowed(s)


def _v30_seeds():
    seeds = []
    for fn in ("v30_explore.jsonl", "v30_explore2.jsonl", "v30_fallback.jsonl",
               "v30_equivalence.jsonl", "v30_parity_serial.jsonl",
               "v30_parity_pool.jsonl", "v30_liveseed.jsonl",
               "v30_liveseed_passive.jsonl", "v30_smoke.jsonl"):
        p = os.path.join(REPO_ROOT, "results", fn)
        if not os.path.exists(p):
            continue
        with open(p) as f:
            for line in f:
                seeds.append(json.loads(line)["seed"])
    return seeds


def test_no_protected_seed_executed():
    for s in _v30_seeds():
        assert not (340090 <= s <= 340199), s
        assert not (214200 <= s <= 214249), s
        assert not (340300 <= s <= 340349), s
        assert not (340050 <= s <= 340050 + 39), s


def test_v30_ranges_declared():
    seeds = set(_v30_seeds())
    lo = [s for s in seeds if 249570 <= s <= 249590]
    assert lo, "no V30-range seeds found"
    assert min(lo) == 249570
    # live seeds are 9-10 digit, disjoint by construction
    live = [s for s in seeds if s > 10**8]
    assert len(live) >= 12


def test_equivalence_all_tied():
    p = os.path.join(REPO_ROOT, "results", "v30_equivalence.jsonl")
    n = 0
    with open(p) as f:
        for line in f:
            r = json.loads(line)
            assert r["delta"] == 0, r["key"]
            n += 1
    assert n == 24, n


def test_package_artifact():
    import tarfile
    p = os.path.join(REPO_ROOT, "submission_a7_v30.tar.gz")
    assert os.path.exists(p)
    with tarfile.open(p, "r:gz") as tar:
        assert tar.getnames() == ["main.py"]
