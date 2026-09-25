# SPDX-License-Identifier: MIT
"""Kagriculture V35 Test Suite: A7 & V22R1 Protected Incumbent Integrity."""

import hashlib
import os
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

A7_PATH = os.path.join(REPO_ROOT, "candidates", "v30_a7_standalone", "main.py")
V22R1_PATH = os.path.join(REPO_ROOT, "submission_aec_v22r1.tar.gz")

EXPECTED_A7_SHA256 = "51c1d25245f68dd8de66b355f2ad6ca1d79de8af02efed521a5a82f7be69ce3f"
EXPECTED_V22R1_SHA256 = "6b879b3e499d2cf43b76884f6ef433479468b5c316f92cf4a8cc5119586fb3f5"


def test_a7_standalone_hash():
    assert os.path.exists(A7_PATH), f"Protected A7 file missing at {A7_PATH}"
    with open(A7_PATH, "rb") as f:
        content = f.read()
    digest = hashlib.sha256(content).hexdigest()
    assert digest == EXPECTED_A7_SHA256, (
        f"A7 standalone SHA256 mismatch!\nExpected: {EXPECTED_A7_SHA256}\nObserved: {digest}"
    )


def test_v22r1_archive_hash():
    assert os.path.exists(V22R1_PATH), f"Protected V22R1 archive missing at {V22R1_PATH}"
    with open(V22R1_PATH, "rb") as f:
        content = f.read()
    digest = hashlib.sha256(content).hexdigest()
    assert digest == EXPECTED_V22R1_SHA256, (
        f"V22R1 archive SHA256 mismatch!\nExpected: {EXPECTED_V22R1_SHA256}\nObserved: {digest}"
    )


def test_no_forbidden_modifications():
    assert os.path.getsize(A7_PATH) > 10000
    assert os.path.getsize(V22R1_PATH) > 10000
