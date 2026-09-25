# SPDX-License-Identifier: MIT
"""V34 Freeze & Governance Test Suite.

Verifies:
1. Protected incumbent A7 SHA-256 integrity.
2. Protected Slot A V22R1 SHA-256 integrity.
3. Strict virgin holdout quarantine refusal (214200-214249, 340090-340199, 249695-249734).
"""

from __future__ import annotations
import hashlib
import os
import sys
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

A7_PATH = os.path.join(REPO_ROOT, "candidates", "v30_a7_standalone", "main.py")
A7_SHA256 = "51c1d25245f68dd8de66b355f2ad6ca1d79de8af02efed521a5a82f7be69ce3f"

V22R1_PATH = os.path.join(REPO_ROOT, "submission_aec_v22r1.tar.gz")
V22R1_SHA256 = "6b879b3e499d2cf43b76884f6ef433479468b5c316f92cf4a8cc5119586fb3f5"

VIRGIN_HOLDOUTS = [
    (214200, 214249),  # GATE0 virgin holdout
    (340090, 340199),  # Remainder
    (249695, 249734),  # V32_CONFIRM single-touch holdout
]


def _sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest().lower()


def test_a7_standalone_integrity():
    assert os.path.exists(A7_PATH), f"A7 standalone file missing at {A7_PATH}"
    actual = _sha256(A7_PATH)
    assert actual == A7_SHA256, f"A7 SHA-256 mismatch! Expected {A7_SHA256}, got {actual}"


def test_v22r1_archive_integrity():
    assert os.path.exists(V22R1_PATH), f"V22R1 archive missing at {V22R1_PATH}"
    actual = _sha256(V22R1_PATH)
    assert actual == V22R1_SHA256, f"V22R1 SHA-256 mismatch! Expected {V22R1_SHA256}, got {actual}"


def test_virgin_holdout_quarantine():
    from scripts.v32_common import check_seed_allowed
    for lo, hi in VIRGIN_HOLDOUTS:
        for test_s in (lo, (lo + hi) // 2, hi):
            with pytest.raises(RuntimeError, match="GOVERNANCE REFUSAL"):
                check_seed_allowed(test_s, allow_confirm=False)
