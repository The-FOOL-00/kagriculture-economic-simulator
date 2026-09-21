# SPDX-License-Identifier: MIT
"""V27: freeze integrity, cohort registry, dataset, and firewall tests.

Fast (no matches). Guards V22R1, the frozen P3/V3 bytes, the vendored
evidence, the virgin-cohort firewall, and the normalized dataset.
"""

import hashlib
import json
import os
import re
import subprocess

import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
RESULTS = os.path.join(REPO_ROOT, "results")

P3_SHA = "13292582c8cc796bc11ccebff9684fbec45cfb97d936fb9e85e4e9bb4dbea179"
V3_SHA = "845e0d10981b11b06d272048ff5cee30d70a0403dd757651a556a78c8bf18943"
V22R1_SHA = "6b879b3e499d2cf43b76884f6ef433479468b5c316f92cf4a8cc5119586fb3f5"
V22R1_COMMIT = "33763a8f58b17bc3a32735c2a322883b78ed3778"
V25_E4 = "e4eb8a421562ba9e0a2627375d385fdfe011e32f"

VENDORED = {
    "v25_backbone_matches.jsonl": (
        "aebf1372552c8d16f255b5c548769357f61c41945d21823d47ea5c506e2d1484", 120),
    "v25_confirmation_matches.jsonl": (
        "112194cd3d63bd1cf08f6c02c2d66140e22b34f760660fa90752c23f161738bd", 40),
    "v25_aec_transfer_matches.jsonl": (
        "40e96e15cf6d91d7c092fb8f358ce4b4658a70685afd1a2b4971c52590aa834a", 80),
    "v26_aec_transfer_matches.jsonl": (
        "7aef81965152dea4a5f88eddb7cf53ec83b4954bd802eb1a7177f94f5eb90c2e", 160),
}


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def git(*args):
    return subprocess.run(["git"] + list(args), cwd=REPO_ROOT,
                          capture_output=True, text=True, check=True).stdout.strip()


class TestV27FreezeIntegrity:
    def test_v22r1_tag_commit(self):
        assert git("rev-parse", "v22r1^{commit}") == V22R1_COMMIT

    def test_v22r1_archive(self):
        assert sha256_file(os.path.join(REPO_ROOT, "submission_aec_v22r1.tar.gz")) == V22R1_SHA

    def test_v3_frozen(self):
        assert sha256_file(os.path.join(REPO_ROOT, "submission_Vj_kc_v3.tar.gz")) == V3_SHA

    def test_p3_frozen_and_matches_v25_tip(self):
        assert sha256_file(os.path.join(REPO_ROOT, "candidates", "v25_p3_unified.py")) == P3_SHA
        blob = subprocess.run(
            ["git", "show", "%s:candidates/v25_p3_unified.py" % V25_E4],
            cwd=REPO_ROOT, capture_output=True, check=True).stdout
        assert hashlib.sha256(blob).hexdigest() == P3_SHA

    def test_vendored_evidence_intact(self):
        for name, (digest, n_lines) in VENDORED.items():
            path = os.path.join(RESULTS, name)
            assert sha256_file(path) == digest, name
            with open(path, "r", encoding="utf-8") as f:
                assert sum(1 for line in f if line.strip()) == n_lines, name


class TestV27CohortRegistry:
    def test_manifest_ranges_virgin_and_disjoint(self):
        man = json.load(open(os.path.join(REPO_ROOT, "V27_COHORT_MANIFEST.json")))
        stages = man["stages"]
        assert [s["seeds"] for s in stages] == [[249490, 249509], [249510, 249529]]
        assert man["disjointness_audit"]["max_consumed_seed_anywhere"] == 249489
        assert man["disjointness_audit"]["overlap_count"] == 0
        # protected holdouts untouched by reservations
        for lo, hi in [(214200, 214249), (340050, 340199), (340300, 340349)]:
            for s in stages:
                assert s["seeds"][1] < lo or s["seeds"][0] > hi

    def test_no_virgin_seed_use_outside_allowlist(self):
        # Results JSONL must not reference seeds >= 249490, except the future
        # prospective result files (allowlisted by name once created).
        allow = {"v27_discovery_matches.jsonl", "v27_confirmation_matches.jsonl"}
        pat = re.compile(r'"seed"\s*:\s*(24\d{4}|25\d{4}|3\d{5})')
        bad = []
        for fname in sorted(os.listdir(RESULTS)):
            if not (fname.endswith(".jsonl") or fname.endswith(".json")):
                continue
            if fname in allow:
                continue
            path = os.path.join(RESULTS, fname)
            if os.path.getsize(path) > 300_000_000:
                continue  # trajectory stores carry only consumed seeds by construction
            try:
                text = open(path, "r", encoding="utf-8", errors="replace").read()
            except OSError:
                continue
            for m in pat.finditer(text):
                s = int(m.group(1))
                if 249490 <= s <= 249529:
                    bad.append((fname, s))
                    break
        assert bad == [], bad


class TestV27HistoricalDataset:
    @pytest.fixture()
    def recs(self):
        path = os.path.join(RESULTS, "v27_historical_matches.jsonl")
        assert os.path.exists(path), "run scripts/v27_build_historical_dataset.py"
        with open(path, "r", encoding="utf-8") as f:
            return [json.loads(line) for line in f if line.strip()]

    def test_counts_and_ranges(self, recs):
        assert len(recs) == 120
        by_c = {}
        for r in recs:
            by_c.setdefault(r["cohort"], []).append(r)
        assert {k: len(v) for k, v in by_c.items()} == {"A": 40, "B": 40, "C": 40}
        for cohort, (lo, hi) in {"A": (249430, 249449), "B": (249450, 249469),
                                 "C": (249470, 249489)}.items():
            seeds = sorted({r["seed"] for r in by_c[cohort]})
            assert seeds == list(range(lo, hi + 1))

    def test_means_reproduce(self, recs):
        import statistics
        by_c = {}
        for r in recs:
            by_c.setdefault(r["cohort"], []).append(r["paired_delta"])
        assert abs(statistics.mean(by_c["A"]) - 1300.70) < 0.005
        assert abs(statistics.mean(by_c["B"]) - 453.77) < 0.005
        assert abs(statistics.mean(by_c["C"]) - (-218.75)) < 0.005

    def test_exact_zero_wlt(self, recs):
        by_c = {}
        for r in recs:
            by_c.setdefault(r["cohort"], []).append(r["paired_delta"])
        assert (sum(1 for d in by_c["A"] if d > 0), sum(1 for d in by_c["A"] if d < 0)) == (40, 0)
        assert (sum(1 for d in by_c["B"] if d > 0), sum(1 for d in by_c["B"] if d < 0)) == (27, 13)
        assert (sum(1 for d in by_c["C"] if d > 0), sum(1 for d in by_c["C"] if d < 0)) == (18, 22)
