# SPDX-License-Identifier: MIT
"""
EXP-AEC-004 Mechanism Isolation and Preflight Verification Test Suite.

Verifies:
1. Exact single-mechanism difference between Control and Treatment (EMERGENCY_FEED_PURCHASE).
2. Strict quarantine of RESOURCE_CONVERSION in both arms.
3. Absolute holdout protection and seed cohort disjointness.
4. Cryptographic integrity of V3 tarball and experiment configs.
5. Fail-closed runner quarantine guards.
"""

import importlib.util
import json
import os
import sys
import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

runner_path = os.path.join(REPO_ROOT, "experiments", "EXP-AEC-004", "run_experiment.py")
spec = importlib.util.spec_from_file_location("exp_004_runner", runner_path)
exp_004 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(exp_004)

COHORT_START = exp_004.COHORT_START
COHORT_END = exp_004.COHORT_END
COHORT_SIZE = exp_004.COHORT_SIZE
V3_EXPECTED_SHA256 = exp_004.V3_EXPECTED_SHA256
V3_TARBALL_PATH = exp_004.V3_TARBALL_PATH
CONFIG_CONTROL_PATH = exp_004.CONFIG_CONTROL_PATH
CONFIG_TREATMENT_PATH = exp_004.CONFIG_TREATMENT_PATH
EXECUTION_MANIFEST_PATH = exp_004.EXECUTION_MANIFEST_PATH
assert_quarantine_invariants = exp_004.assert_quarantine_invariants
sha256_of_file = exp_004.sha256_of_file
verify_preflight_environment = exp_004.verify_preflight_environment


def test_exp_004_mechanism_isolation():
    """Verify that Treatment differs from Control by EXACTLY EMERGENCY_FEED_PURCHASE."""
    assert os.path.exists(CONFIG_CONTROL_PATH), f"Missing {CONFIG_CONTROL_PATH}"
    assert os.path.exists(CONFIG_TREATMENT_PATH), f"Missing {CONFIG_TREATMENT_PATH}"

    with open(CONFIG_CONTROL_PATH, "r", encoding="utf-8") as f:
        ctrl = json.load(f)
    with open(CONFIG_TREATMENT_PATH, "r", encoding="utf-8") as f:
        treat = json.load(f)

    ctrl_enabled = set(ctrl["enabled_mechanisms"])
    treat_enabled = set(treat["enabled_mechanisms"])

    # Difference must be exactly EMERGENCY_FEED_PURCHASE
    diff = treat_enabled - ctrl_enabled
    assert diff == {"EMERGENCY_FEED_PURCHASE"}, f"Unexpected enabled diff: {diff}"

    # Control must not have any mechanism that treatment lacks
    reverse_diff = ctrl_enabled - treat_enabled
    assert len(reverse_diff) == 0, f"Control has mechanisms Treatment lacks: {reverse_diff}"

    # Foundation mechanisms must match exactly
    assert "DEPENDENCY_AWARE_MARKET_TIMING" in ctrl_enabled
    assert "DEPENDENCY_AWARE_MARKET_TIMING" in treat_enabled
    assert "TERMINAL_LIQUIDATION" in ctrl_enabled
    assert "TERMINAL_LIQUIDATION" in treat_enabled
    assert "PHASE_SHUTDOWN" in ctrl_enabled
    assert "PHASE_SHUTDOWN" in treat_enabled


def test_exp_004_resource_conversion_quarantine():
    """Verify that RESOURCE_CONVERSION is strictly quarantined in both arms."""
    with open(CONFIG_CONTROL_PATH, "r", encoding="utf-8") as f:
        ctrl = json.load(f)
    with open(CONFIG_TREATMENT_PATH, "r", encoding="utf-8") as f:
        treat = json.load(f)

    assert "RESOURCE_CONVERSION" not in ctrl["enabled_mechanisms"]
    assert "RESOURCE_CONVERSION" not in treat["enabled_mechanisms"]
    assert "RESOURCE_CONVERSION" in ctrl["quarantined_mechanisms"]
    assert "RESOURCE_CONVERSION" in treat["quarantined_mechanisms"]


def test_exp_004_cohort_disjointness_and_holdout_protection():
    """Verify cohort bounds and complete separation from holdouts and historical cohorts."""
    assert COHORT_START == 340300
    assert COHORT_END == 340349
    assert COHORT_SIZE == 50
    cohort_set = set(range(COHORT_START, COHORT_END + 1))

    # Primary Locked Holdout: 340050-340199
    primary_holdout = set(range(340050, 340199 + 1))
    assert cohort_set.isdisjoint(primary_holdout)
    assert min(cohort_set) - max(primary_holdout) == 101

    # Secondary Locked Holdout: 214200-214249
    secondary_holdout = set(range(214200, 214249 + 1))
    assert cohort_set.isdisjoint(secondary_holdout)

    # Historical Cohorts
    exp_001 = set(range(340000, 340049 + 1))
    exp_002 = set(range(340200, 340249 + 1))
    exp_003 = set(range(340250, 340299 + 1))
    assert cohort_set.isdisjoint(exp_001)
    assert cohort_set.isdisjoint(exp_002)
    assert cohort_set.isdisjoint(exp_003)


def test_exp_004_v3_tarball_hash():
    """Verify cryptographic integrity of frozen V3 submission archive."""
    assert os.path.exists(V3_TARBALL_PATH)
    actual_sha = sha256_of_file(V3_TARBALL_PATH)
    assert actual_sha == V3_EXPECTED_SHA256, f"V3 SHA mismatch: {actual_sha}"


def test_exp_004_execution_manifest_integrity():
    """Verify execution manifest status, schema, and directive."""
    assert os.path.exists(EXECUTION_MANIFEST_PATH)
    with open(EXECUTION_MANIFEST_PATH, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    assert manifest["experiment_id"] == "EXP-AEC-004"
    assert manifest["status"] == "FROZEN_NOT_LAUNCHED"
    assert manifest["directive"] == "DO_NOT_EXECUTE_WITHOUT_USER_APPROVAL"
    assert manifest["cohort"]["seed_start"] == 340300
    assert manifest["cohort"]["seed_end"] == 340349
    assert manifest["cohort"]["seed_count"] == 50
    assert manifest["cohort"]["matches_per_seed"] == 2
    assert manifest["cohort"]["total_matches"] == 100


def test_exp_004_runner_holdout_guards():
    """Verify that runner fail-closed logic aborts on protected or invalid seeds."""
    # Primary holdout breach must raise RuntimeError
    with pytest.raises(RuntimeError, match="CRITICAL QUARANTINE BREACH"):
        assert_quarantine_invariants(340050)
    with pytest.raises(RuntimeError, match="CRITICAL QUARANTINE BREACH"):
        assert_quarantine_invariants(340199)

    # Secondary holdout breach must raise RuntimeError
    with pytest.raises(RuntimeError, match="CRITICAL QUARANTINE BREACH"):
        assert_quarantine_invariants(214200)

    # Historical cohort breach must raise RuntimeError
    with pytest.raises(RuntimeError, match="CRITICAL QUARANTINE BREACH"):
        assert_quarantine_invariants(340250)

    # Out of cohort seed must raise RuntimeError
    with pytest.raises(RuntimeError, match="CRITICAL COHORT VIOLATION"):
        assert_quarantine_invariants(340350)

    # Valid cohort seeds must pass without error
    for s in range(COHORT_START, COHORT_END + 1):
        assert_quarantine_invariants(s)


def test_exp_004_preflight_environment():
    """Verify full preflight environment check executes cleanly."""
    hashes = verify_preflight_environment()
    assert "v3_tarball" in hashes
    assert "config_control_sha" in hashes
    assert "config_treatment_sha" in hashes
    assert "manifest_sha" in hashes
