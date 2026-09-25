# SPDX-License-Identifier: MIT
"""V28 freeze tests: V22R1/V3/A7 integrity + cohort quarantine."""

import glob
import hashlib
import json
import os
import subprocess

import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def test_v22r1_tag_and_commit_frozen():
    commit = subprocess.run(["git", "rev-parse", "v22r1^{commit}"],
                            capture_output=True, text=True, cwd=ROOT)
    assert commit.stdout.strip() == "33763a8f58b17bc3a32735c2a322883b78ed3778"


def test_v22r1_archive_frozen():
    assert sha256_file(os.path.join(ROOT, "submission_aec_v22r1.tar.gz")) == \
        "6b879b3e499d2cf43b76884f6ef433479468b5c316f92cf4a8cc5119586fb3f5"


def test_v3_and_p3_frozen():
    assert sha256_file(os.path.join(ROOT, "submission_Vj_kc_v3.tar.gz")) == \
        "845e0d10981b11b06d272048ff5cee30d70a0403dd757651a556a78c8bf18943"
    assert sha256_file(os.path.join(ROOT, "candidates", "v25_p3_unified.py")) == \
        "13292582c8cc796bc11ccebff9684fbec45cfb97d936fb9e85e4e9bb4dbea179"


def test_a7_source_frozen():
    base = os.path.join(ROOT, "aec", "backbone")
    assert sha256_file(os.path.join(base, "v27_ablation_adapters.py")) == \
        "18d2c8ea2cf826b0bef71c96988dba0c93d7dbcc73936a0c99f07cb0539e7ae9"
    assert sha256_file(os.path.join(base, "v25_p3_adapter.py")) == \
        "ce8169e95e86bd338b32dada48ba3fa0216bdeea4cebdd34a0264fe18a9f5195"
    assert sha256_file(os.path.join(base, "v3_adapter.py")) == \
        "a0a9fd2c2ce1abe2de7e871e7fd9deec647df9863179c19cf1b94fc5ed2e3135"
    assert sha256_file(os.path.join(base, "interface.py")) == \
        "1a1c5ec7cbc097c13d60eeed98ed98749f11cad7456c368366513dc7eeda4091"
    assert sha256_file(os.path.join(base, "utils.py")) == \
        "53f9277406162cf1789d5dceb944f147ead85d65d52647350533a1c1c7684404"
    assert sha256_file(os.path.join(ROOT, "aec", "config.py")) == \
        "14c3a22c0141b770efe43244afe77f7ed27064e0256bdb9f8b40750e3b2eabae"


def test_engine_version():
    import kaggle_environments
    assert kaggle_environments.__version__ == "1.32.7"


def test_a7_flags_exact():
    from aec.backbone.v27_ablation_adapters import V27AblationAdapter
    a7 = V27AblationAdapter(variant="V27-ABL-A7")
    assert a7.call_v3_at_step0 is True
    assert a7.open_units == 30
    assert a7.dispatch is False
    assert a7.rewrite_step0_wash is True
    assert a7.identity() == "V27-ABL-A7"


def test_cohort_quarantine():
    """No pre-V28 artifact may reference a virgin-cohort seed.

    Allowlist: V28's own files (which name the cohort by design) and the
    V27 reservation pointers (which never ran matches there).
    """
    import re
    # V29 maintenance (2026-09-21): the successor campaign's own files name
    # V28's cohort (replication references) and use post-V28 seeds (340050+);
    # they are definitionally not "pre-V28 artifacts" (see docstring), so
    # they join the own-file allowlist. Protection over all pre-V29 files is
    # unchanged. See V29_FINAL_REPORT.md s15 (stale-test note).
    # V30 maintenance (2026-09-21): same stale-test situation — V30's
    # authorized outputs (249570+, v30_*) tripped the unbounded forward
    # scan; offender list verified to contain ONLY post-V28 V30 rows.
    # V30 own-files join the allowlist by the same definitional argument.
    # Protection over all pre-V30 files is unchanged. See V30_FINAL_REPORT.md
    # s8 (stale-test note). Verified by planted-violation mutation probe.
    # V31R2 maintenance (2026-09-22): same — V31R2's authorized E1/E2/E3
    # outputs (249591+, v31r2_*) tripped the scan; non-v31r2 offender
    # count verified 0. V31R2 own-files join by the same argument.
    # Protection over all pre-V31R2 files unchanged. Verified by
    # planted-violation mutation probe (below, kept passing).
    # V32 maintenance (2026-09-22): same — V32's authorized EXP-1 output
    # (249635+, v32_*) tripped the scan; non-v32 offender count verified 0
    # (replicated scan). V32 own-files join by the same definitional
    # argument. Protection over all pre-V32 files unchanged. See
    # V32_FINAL_REPORT.md s7 (stale-test note).
    allow = {"V28_", "v28_", "V29_", "v29_", "V30_", "v30_",
             "V31R2_", "v31r2_", "V32_", "v32_",
             "V27_COHORT_MANIFEST",
             "V27_QUAL_MANIFEST", "V27_FINAL_REPORT",
             "V27_CONFIRMATION_REPORT", "v27_prospective_tournament"}
    pat = re.compile(r"(?<!\d)249(5[3-9]\d|[6-9]\d\d)(?!\d)")
    offenders = []
    for f in glob.glob(os.path.join(ROOT, "results", "*.jsonl")):
        # V29 maintenance: successor-campaign outputs are post-V28 by
        # construction (see allow-note above); V28's own exclusion kept.
        # V30 maintenance: same for v30_* (see allow-note above).
        if "v28_" in os.path.basename(f) or "v29_" in os.path.basename(f) \
                or "v30_" in os.path.basename(f) \
                or "v31r2_" in os.path.basename(f) \
                or "v32_" in os.path.basename(f):
            continue
        with open(f, encoding="utf-8", errors="replace") as fh:
            for i, line in enumerate(fh):
                if '"seed"' not in line:
                    continue
                try:
                    s = json.loads(line).get("seed")
                except Exception:
                    continue
                if isinstance(s, int) and s >= 249530:
                    offenders.append((f, i, s))
    assert offenders == [], offenders[:5]
    for f in glob.glob(os.path.join(ROOT, "*.md")) + \
            glob.glob(os.path.join(ROOT, "scripts", "*.py")):
        base = os.path.basename(f)
        if any(a in base for a in allow):
            continue
        txt = open(f, encoding="utf-8", errors="replace").read()
        hits = [m.group(0) for m in pat.finditer(txt)]
        # v27 runner's exclusive bound is fine (max actual seed 249529)
        assert not hits, (base, hits[:5])


def test_preregistration_committed_before_results():
    """The preregistration blob must be in git history (committed)."""
    r = subprocess.run(["git", "log", "--oneline", "--", "V28_PREREGISTRATION.md"],
                       capture_output=True, text=True, cwd=ROOT)
    assert r.stdout.strip(), "V28_PREREGISTRATION.md not committed!"
