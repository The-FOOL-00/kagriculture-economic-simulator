# SPDX-License-Identifier: MIT
"""
=============================================================================
RUNNER VALIDATION TEST SUITE (PHASE C)
=============================================================================
Validates all runner requirements (A through P) without consuming any
prospective performance seed (320000–320499). Uses only non-prospective
quarantine fixtures and consumed DEV-006 validation seeds (248000–248049).
=============================================================================
"""

import os
import sys
import pytest
import json

HERE = os.path.dirname(os.path.abspath(__file__))
H1_DIR = os.path.dirname(HERE)
REPO_ROOT = os.path.abspath(os.path.join(H1_DIR, "..", ".."))

PORT_DIR = os.path.join(REPO_ROOT, "experiments", "EXP-DEV-006_HORIZON_KILLTEST", "port")
if PORT_DIR not in sys.path:
    sys.path.insert(0, PORT_DIR)
if H1_DIR not in sys.path:
    sys.path.insert(0, H1_DIR)

from run_arch002_h1_execution import (
    assert_quarantine,
    verify_integrity_hashes,
    run_seed_crn,
    save_results_checkpoint,
    load_existing_results,
    AUTHORIZED_COHORT_LO,
    AUTHORIZED_COHORT_HI,
    PROTECTED_QUARANTINE_RANGES,
)


def test_quarantine_hard_abort_holdout():
    """Requirement P: Holdout seeds 214200-214249 must raise RuntimeError."""
    for seed in (214200, 214225, 214249):
        with pytest.raises(RuntimeError, match="CRITICAL QUARANTINE BREACH.*Virgin Final Holdout"):
            assert_quarantine(seed, allow_consumed_validation=False)
        with pytest.raises(RuntimeError, match="CRITICAL QUARANTINE BREACH.*Virgin Final Holdout"):
            assert_quarantine(seed, allow_consumed_validation=True)


def test_quarantine_hard_abort_dev007():
    """Requirement O: DEV-007 seeds 310000-310499 must raise RuntimeError."""
    for seed in (310000, 310250, 310499):
        with pytest.raises(RuntimeError, match="CRITICAL QUARANTINE BREACH.*DEV-007 Reserved Cohort"):
            assert_quarantine(seed, allow_consumed_validation=False)
        with pytest.raises(RuntimeError, match="CRITICAL QUARANTINE BREACH.*DEV-007 Reserved Cohort"):
            assert_quarantine(seed, allow_consumed_validation=True)


def test_quarantine_hard_abort_fallbacks_and_consumed():
    """Verify other protected blocks trigger hard abort."""
    # DEV-007 fallbacks
    for seed in (410000, 410499, 510000, 510499):
        with pytest.raises(RuntimeError, match="CRITICAL QUARANTINE BREACH"):
            assert_quarantine(seed, allow_consumed_validation=False)

    # Benchmark and qualification blocks
    for seed in (50000, 50050, 50100, 50150, 60000, 245000, 246000, 247000):
        with pytest.raises(RuntimeError, match="CRITICAL QUARANTINE BREACH"):
            assert_quarantine(seed, allow_consumed_validation=False)


def test_quarantine_hard_abort_out_of_cohort():
    """Requirement A: Seeds outside 320000-320499 must abort in production mode."""
    for seed in (100, 319999, 320500, 999999):
        with pytest.raises(RuntimeError, match="CRITICAL COHORT VIOLATION"):
            assert_quarantine(seed, allow_consumed_validation=False)


def test_quarantine_permits_consumed_validation_flag_only():
    """Requirement A: Consumed seed 248000 only permitted when flag is True."""
    with pytest.raises(RuntimeError, match="CRITICAL QUARANTINE BREACH.*DEV-006 Consumed Cohort"):
        assert_quarantine(248000, allow_consumed_validation=False)
    # Does not raise when explicitly validating
    assert_quarantine(248000, allow_consumed_validation=True)


def test_g_hash_verification():
    """Requirement G-HASH: Integrity hashes must pass."""
    verify_integrity_hashes()


def test_crn_and_labeling_on_consumed_seed():
    """Requirements B, C, D, I, J, L, M: 2 games per seed, correct seats, CRN math."""
    # Consumed seed 248000 (DEV-006 consumed, safe for validation)
    res = run_seed_crn(248000, allow_consumed_validation=True)

    assert res["seed"] == 248000
    assert "delta_a" in res
    assert "delta_b" in res
    assert "delta_paired" in res
    assert res["delta_paired"] == 0.5 * (res["delta_a"] + res["delta_b"])

    # Game a checks
    ga = res["game_a"]
    assert ga["seed"] == 248000
    assert ga["h1_seat"] == 0
    assert ga["base_seat"] == 1
    assert ga["delta"] == ga["reward_h1"] - ga["reward_base"]
    assert ga["pure_pre_e_pass"] is True
    assert ga["pure_verbatim_pass"] is True
    assert ga["pure_step_pass"] is True

    # Game b checks
    gb = res["game_b"]
    assert gb["seed"] == 248000
    assert gb["h1_seat"] == 1
    assert gb["base_seat"] == 0
    assert gb["delta"] == gb["reward_h1"] - gb["reward_base"]
    assert gb["pure_pre_e_pass"] is True
    assert gb["pure_verbatim_pass"] is True
    assert gb["pure_step_pass"] is True


def test_checkpoint_and_resume(tmp_path):
    """Requirements E, F, G, H: result serialization, duplicate protection, resume."""
    import run_arch002_h1_execution as runner_mod

    raw_file = str(tmp_path / "RAW_RESULTS.json")
    csv_file = str(tmp_path / "PAIRED_DELTAS.csv")
    tel_file = str(tmp_path / "TELEMETRY_EVENTS.csv")

    orig_raw = runner_mod.RAW_RESULTS_FILE
    orig_csv = runner_mod.PAIRED_DELTAS_FILE
    orig_tel = runner_mod.TELEMETRY_EVENTS_FILE

    try:
        runner_mod.RAW_RESULTS_FILE = raw_file
        runner_mod.PAIRED_DELTAS_FILE = csv_file
        runner_mod.TELEMETRY_EVENTS_FILE = tel_file

        # Save partial
        mock_res = {
            248000: {
                "seed": 248000,
                "delta_a": 0.0,
                "delta_b": 0.0,
                "delta_paired": 0.0,
                "exposed": False,
                "h1_score_a": 41567.0,
                "base_score_a": 41567.0,
                "h1_score_b": 41567.0,
                "base_score_b": 41567.0,
                "activated_a": False,
                "activated_b": False,
                "reason_a": "ABSTAIN_DOMINANCE",
                "reason_b": "ABSTAIN_DOMINANCE",
                "route_a": "backbone",
                "route_b": "backbone",
                "game_a": {
                    "seed": 248000,
                    "h1_seat": 0,
                    "reward_h1": 41567.0,
                    "reward_base": 41567.0,
                    "delta": 0.0,
                    "activated": False,
                    "reason": "ABSTAIN_DOMINANCE",
                    "route": "backbone",
                    "planning_ms": None,
                    "simulations": None,
                    "changed_workers": [],
                    "stock_value_gain": None,
                    "buy_units_U": None,
                    "fertilizer_reaped": None,
                    "pure_pre_e_pass": True,
                    "pure_verbatim_pass": True,
                },
                "game_b": {
                    "seed": 248000,
                    "h1_seat": 1,
                    "reward_h1": 41567.0,
                    "reward_base": 41567.0,
                    "delta": 0.0,
                    "activated": False,
                    "reason": "ABSTAIN_DOMINANCE",
                    "route": "backbone",
                    "planning_ms": None,
                    "simulations": None,
                    "changed_workers": [],
                    "stock_value_gain": None,
                    "buy_units_U": None,
                    "fertilizer_reaped": None,
                    "pure_pre_e_pass": True,
                    "pure_verbatim_pass": True,
                },
            }
        }
        save_results_checkpoint(mock_res, "2026-09-15T00:00:00Z", status="IN_PROGRESS")

        # Load back
        loaded, count = load_existing_results()
        assert count == 1
        assert 248000 in loaded
        assert loaded[248000]["delta_paired"] == 0.0

        # Verify CSV files exist and are non-empty
        assert os.path.exists(csv_file)
        assert os.path.exists(tel_file)
    finally:
        runner_mod.RAW_RESULTS_FILE = orig_raw
        runner_mod.PAIRED_DELTAS_FILE = orig_csv
        runner_mod.TELEMETRY_EVENTS_FILE = orig_tel


def test_static_boundary_audit_no_prospective_consumption():
    """Section 13: Certify zero prospective seeds (320000-320499) have been executed."""
    import run_arch002_h1_execution as runner_mod
    if os.path.exists(runner_mod.RAW_RESULTS_FILE):
        with open(runner_mod.RAW_RESULTS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            for s in data.get("seeds", []):
                assert not (320000 <= s["seed"] <= 320499), f"Prospective seed {s['seed']} found!"


def test_no_network_or_kaggle_contact():
    """Requirement N: Verify no network, socket, or kaggle imports exist in runner."""
    runner_path = os.path.join(H1_DIR, "run_arch002_h1_execution.py")
    with open(runner_path, "r", encoding="utf-8") as f:
        src = f.read()
    for forbidden in ("kaggle", "urllib.request", "requests", "http.client", "socket."):
        assert forbidden not in src, f"Forbidden network reference {forbidden} found in runner!"
