# SPDX-License-Identifier: MIT
"""V33 Freeze Test: Verifies cryptographic integrity of protected incumbents."""

import hashlib
import json
import os
import sys
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

A7_PROTECTED_PATH = os.path.join(REPO_ROOT, "candidates", "v30_a7_standalone", "main.py")
A7_PROTECTED_SHA256 = "51c1d25245f68dd8de66b355f2ad6ca1d79de8af02efed521a5a82f7be69ce3f"

V22R1_ARCHIVE_PATH = os.path.join(REPO_ROOT, "submission_aec_v22r1.tar.gz")
V22R1_ARCHIVE_SHA256 = "6b879b3e499d2cf43b76884f6ef433479468b5c316f92cf4a8cc5119586fb3f5"


def test_a7_standalone_hash():
    assert os.path.exists(A7_PROTECTED_PATH), f"A7 file missing at {A7_PROTECTED_PATH}"
    with open(A7_PROTECTED_PATH, "rb") as f:
        actual_hash = hashlib.sha256(f.read()).hexdigest()
    assert actual_hash == A7_PROTECTED_SHA256, (
        f"A7 SHA-256 mismatch! Expected {A7_PROTECTED_SHA256}, got {actual_hash}"
    )


def test_v22r1_archive_hash():
    assert os.path.exists(V22R1_ARCHIVE_PATH), f"V22R1 archive missing at {V22R1_ARCHIVE_PATH}"
    with open(V22R1_ARCHIVE_PATH, "rb") as f:
        actual_hash = hashlib.sha256(f.read()).hexdigest()
    assert actual_hash == V22R1_ARCHIVE_SHA256, (
        f"V22R1 SHA-256 mismatch! Expected {V22R1_ARCHIVE_SHA256}, got {actual_hash}"
    )


def test_virgin_holdout_protection():
    """Verifies that no test or training file accesses protected virgin holdout ranges."""
    protected_ranges = [(214200, 214249), (249695, 249734), (340090, 340199)]
    v33_dir = os.path.join(REPO_ROOT, "candidates", "v33_meta_strategy")
    for fname in os.listdir(v33_dir):
        if fname.endswith(".py") and fname != "replay_leakage_audit.py":
            fpath = os.path.join(v33_dir, fname)
            with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            for start, end in protected_ranges:
                for seed in range(start, end + 1):
                    assert str(seed) not in content, (
                        f"Leakage hazard: virgin holdout seed {seed} found hardcoded in {fname}"
                    )
