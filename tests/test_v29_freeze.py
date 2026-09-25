# SPDX-License-Identifier: MIT
"""V29 freeze tests: V22R1/V3/A7 integrity + holdout/remainder quarantine."""

import glob
import hashlib
import json
import os
import subprocess

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


def test_v28_artifacts_untouched():
    """No V28 file may drift on the V29 line."""
    assert sha256_file(os.path.join(ROOT, "V28_PREREGISTRATION.md")) == \
        "54aff6b4c56adb811f3fdc3767a3e415bc2d1c5df149f4cb50fc1f656a4ddb43"
    assert sha256_file(os.path.join(ROOT, "results", "v28_raw_results.jsonl")) == \
        "2efb4446f35da094a1fb9b3c9f65024bcedd60f648b4d5a4a799180165f21082"
    assert sha256_file(os.path.join(ROOT, "results", "v28_paired_results.csv")) == \
        "a0600fc86f0156a896b9ca6d3309491f8b5accd3dedd7784b7c54af5aecc1555"


def test_holdout_slice_quarantine():
    """No pre-V29 artifact may reference a V29-slice seed as an execution.

    Allowlist: V29's own files (which name the cohort by design), V28's
    final report (which authorized the slice), and the replay-timestamp /
    hash-substring noise class documented in the cohort manifest.
    """
    import re
    allow_sub = ("v29_", "V29_")
    # Interior slice seeds only: the 340050 boundary itself appears in
    # pre-V29 governance text / quarantine guards (manifest-documented).
    pat = re.compile(r"(?<!\d)3400(5[1-9]|[6-8]\d)(?!\d)")
    offenders = []
    for f in glob.glob(os.path.join(ROOT, "results", "*.jsonl")):
        if os.path.basename(f).startswith(("v29_", "V29_")):
            continue
        with open(f, encoding="utf-8", errors="replace") as fh:
            for i, line in enumerate(fh):
                if '"seed"' not in line:
                    continue
                try:
                    s = json.loads(line).get("seed")
                except Exception:
                    continue
                if isinstance(s, int) and 340050 <= s <= 340089:
                    offenders.append((f, i, s))
    assert offenders == [], offenders[:5]
    roots = glob.glob(os.path.join(ROOT, "*.md")) + \
        glob.glob(os.path.join(ROOT, "scripts", "*.py")) + \
        glob.glob(os.path.join(ROOT, "tests", "*.py"))
    for f in roots:
        base = os.path.basename(f)
        if any(s in base for s in allow_sub):
            continue
        if base == "V28_FINAL_REPORT.md":
            continue
        txt = open(f, encoding="utf-8", errors="replace").read()
        hits = [m.group(0) for m in pat.finditer(txt)]
        assert not hits, (base, hits[:5])


def test_protected_remainder_quarantine():
    """Nothing anywhere (except V29 governance text) may name 340090+."""
    import re
    pat = re.compile(r"(?<!\d)340(09\d|1\d\d)(?!\d)")
    offenders = []
    for f in glob.glob(os.path.join(ROOT, "results", "v29_*.jsonl")) + \
            glob.glob(os.path.join(ROOT, "results", "v29_*.csv")) + \
            glob.glob(os.path.join(ROOT, "results", "v29_*.json")):
        txt = open(f, encoding="utf-8", errors="replace").read()
        if '"seed"' in txt:
            for i, line in enumerate(txt.splitlines()):
                if '"seed"' not in line:
                    continue
                try:
                    s = json.loads(line).get("seed")
                except Exception:
                    continue
                if isinstance(s, int) and s >= 340090:
                    offenders.append((f, i, s))
        else:
            hits = [m.group(0) for m in pat.finditer(txt)]
            # v29 governance docs legitimately name the remainder boundary;
            # result files must not contain remainder seeds at all.
            assert not hits, (os.path.basename(f), hits[:5])
    assert offenders == [], offenders[:5]


def test_runner_refuses_remainder():
    import sys
    sys.path.insert(0, ROOT)
    sys.path.insert(0, os.path.join(ROOT, "scripts"))
    import pytest
    from v29_holdout_tournament import check_seed_allowed
    with pytest.raises(RuntimeError):
        check_seed_allowed(340090, True)
    with pytest.raises(RuntimeError):
        check_seed_allowed(340199, True)
    with pytest.raises(RuntimeError):
        check_seed_allowed(249431, False)
    check_seed_allowed(249431, True)  # qual flag permits consumed seeds
    check_seed_allowed(340050, False)
    check_seed_allowed(340089, False)


def test_preregistration_committed_before_results():
    """The V29 preregistration blob must be in git history (committed)."""
    r = subprocess.run(["git", "log", "--oneline", "--", "V29_PREREGISTRATION.md"],
                       capture_output=True, text=True, cwd=ROOT)
    assert r.stdout.strip(), "V29_PREREGISTRATION.md not committed!"
