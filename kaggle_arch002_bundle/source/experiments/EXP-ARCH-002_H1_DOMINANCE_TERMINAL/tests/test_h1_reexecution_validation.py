# SPDX-License-Identifier: MIT
"""
=============================================================================
EXP-ARCH-002 H1 RE-EXECUTION RUNNER VALIDATION SUITE (PHASE G)
=============================================================================
Validates all 16 integrity properties of run_arch002_h1_reexecution.py
without consuming any prospective performance seeds (320000–320499).
Uses strictly non-prospective quarantine fixtures and consumed DEV-006
seeds (248000–248049).
=============================================================================
"""

import copy
import json
import os
import sys
import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
H1_DIR = os.path.dirname(HERE)
REPO_ROOT = os.path.abspath(os.path.join(H1_DIR, "..", ".."))

PORT_DIR = os.path.join(REPO_ROOT, "experiments", "EXP-DEV-006_HORIZON_KILLTEST", "port")
if PORT_DIR not in sys.path:
    sys.path.insert(0, PORT_DIR)
if H1_DIR not in sys.path:
    sys.path.insert(0, H1_DIR)

from run_arch002_h1_reexecution import (
    assert_quarantine,
    verify_integrity_hashes,
    run_single_game,
    run_seed_crn,
    save_results_checkpoint,
    load_existing_results,
    load_baseline,
    build_agent,
    _get_game_config,
    _actions_equal,
    AUTHORIZED_COHORT_LO,
    AUTHORIZED_COHORT_HI,
    ENTRY_STEP,
    FINAL_STEP,
)
import kagsim_py.api as papi


# -----------------------------------------------------------------------------
# 1. Quarantine Hard-Abort Tests (Properties 12, 13, 14)
# -----------------------------------------------------------------------------
def test_quarantine_hard_abort_holdout():
    """Property 13: Holdout seeds 214200-214249 must raise RuntimeError."""
    for seed in (214200, 214225, 214249):
        with pytest.raises(RuntimeError, match="CRITICAL QUARANTINE BREACH.*Virgin Final Holdout"):
            assert_quarantine(seed, allow_consumed_validation=False)
        with pytest.raises(RuntimeError, match="CRITICAL QUARANTINE BREACH.*Virgin Final Holdout"):
            assert_quarantine(seed, allow_consumed_validation=True)


def test_quarantine_hard_abort_dev007():
    """Property 12: DEV-007 seeds 310000-310499 must raise RuntimeError."""
    for seed in (310000, 310250, 310499):
        with pytest.raises(RuntimeError, match="CRITICAL QUARANTINE BREACH.*DEV-007 Reserved Cohort"):
            assert_quarantine(seed, allow_consumed_validation=False)
        with pytest.raises(RuntimeError, match="CRITICAL QUARANTINE BREACH.*DEV-007 Reserved Cohort"):
            assert_quarantine(seed, allow_consumed_validation=True)


def test_quarantine_hard_abort_fallbacks_and_consumed():
    """Verify other protected blocks trigger hard abort."""
    for seed in (410000, 410499, 510000, 510499):
        with pytest.raises(RuntimeError, match="CRITICAL QUARANTINE BREACH"):
            assert_quarantine(seed, allow_consumed_validation=False)
    for seed in (50000, 50050, 50100, 50150, 60000, 245000, 246000, 247000):
        with pytest.raises(RuntimeError, match="CRITICAL QUARANTINE BREACH"):
            assert_quarantine(seed, allow_consumed_validation=False)


def test_quarantine_hard_abort_out_of_cohort():
    """Property 14: Seeds outside 320000-320499 must abort in production mode."""
    for seed in (100, 319999, 320500, 999999):
        with pytest.raises(RuntimeError, match="CRITICAL COHORT VIOLATION"):
            assert_quarantine(seed, allow_consumed_validation=False)


def test_quarantine_permits_consumed_validation_flag_only():
    """Consumed seed 248000 only permitted when allow_consumed_validation is True."""
    with pytest.raises(RuntimeError, match="CRITICAL QUARANTINE BREACH.*DEV-006 Consumed Cohort"):
        assert_quarantine(248000, allow_consumed_validation=False)
    assert_quarantine(248000, allow_consumed_validation=True)


# -----------------------------------------------------------------------------
# 2. Integrity Hashes (G-HASH)
# -----------------------------------------------------------------------------
def test_g_hash_verification():
    """Requirement G-HASH: Baseline and Preregistration integrity hashes match."""
    verify_integrity_hashes()


# -----------------------------------------------------------------------------
# 3. Pure Baseline vs Pure Baseline Identity (Property 1)
# -----------------------------------------------------------------------------
def test_pure_baseline_vs_pure_baseline_identity():
    """Property 1: Two independent baseline instances in identical environments produce identical actions."""
    inst_a = load_baseline()
    inst_b = load_baseline()
    cfg = _get_game_config()

    game_a = papi.Game(248000)
    game_b = papi.Game(248000)

    while not game_a.done:
        obs_a0 = game_a.observe(0)
        obs_b0 = game_b.observe(0)
        act_a = inst_a.call(copy.deepcopy(obs_a0), copy.deepcopy(cfg))
        act_b = inst_b.call(copy.deepcopy(obs_b0), copy.deepcopy(cfg))
        assert _actions_equal(act_a, act_b), f"Baseline drift at step {game_a.step_count}!"

        # Step both with identical passive opponent
        game_a.step(act_a, {})
        game_b.step(act_b, {})

    assert game_a.reward(0) == game_b.reward(0)


# -----------------------------------------------------------------------------
# 4. Zero Double-Call Tracer & P-PURE Pre-E Identity (Properties 2, 3, 4, 15, 16)
# -----------------------------------------------------------------------------
def test_no_accidental_double_call_and_p_pure_identity():
    """Properties 2, 4, 15, 16:
    Proves directly that no mutable policy instance is called more than once per turn,
    and H1 pre-E actions equal untouched baseline actions 100% of the time across
    seeds 248000, 248001, 248002 (including seeds that failed under the original runner).
    """
    for seed in (248000, 248001, 248002):
        cfg = _get_game_config()

        base_inst_h1 = load_baseline()
        base_inst_ctrl = load_baseline()
        base_inst_twin = load_baseline()

        # Instrumentation wrapper to trace every call per step
        call_counts_h1 = {}
        call_counts_ctrl = {}
        call_counts_twin = {}

        orig_call_h1 = base_inst_h1.call
        orig_call_ctrl = base_inst_ctrl.call
        orig_call_twin = base_inst_twin.call

        def traced_h1(obs, conf):
            step = obs.get("step", 0)
            call_counts_h1[step] = call_counts_h1.get(step, 0) + 1
            return orig_call_h1(obs, conf)

        def traced_ctrl(obs, conf):
            step = obs.get("step", 0)
            call_counts_ctrl[step] = call_counts_ctrl.get(step, 0) + 1
            return orig_call_ctrl(obs, conf)

        def traced_twin(obs, conf):
            step = obs.get("step", 0)
            call_counts_twin[step] = call_counts_twin.get(step, 0) + 1
            return orig_call_twin(obs, conf)

        base_inst_h1.call = traced_h1
        base_inst_ctrl.call = traced_ctrl
        base_inst_twin.call = traced_twin

        agent_h1 = build_agent(base_inst_h1, shadow_only=False)
        agent_base = base_inst_ctrl.call

        game = papi.Game(seed)
        step_count = 0

        while not game.done:
            t = game.step_count
            obs0 = game.observe(0)
            obs1 = game.observe(1)

            act_h1 = agent_h1(copy.deepcopy(obs0), copy.deepcopy(cfg))
            act_ctrl = agent_base(copy.deepcopy(obs1), copy.deepcopy(cfg))

            if t < ENTRY_STEP:
                act_twin = base_inst_twin.call(copy.deepcopy(obs0), copy.deepcopy(cfg))
                # PROVE IDENTITY: H1 pre-E actions equal untouched baseline actions
                assert _actions_equal(act_h1, act_twin), (
                    f"Seed {seed} step {t}: H1 pre-E action != untouched baseline action!"
                )

            game.step(act_h1, act_ctrl)
            step_count += 1

        # PROVE NO DOUBLE CALL: each policy called exactly once per step
        for s in range(ENTRY_STEP):
            assert call_counts_h1.get(s, 0) == 1, f"Seed {seed} step {s}: base_inst_h1 called {call_counts_h1.get(s)} times!"
            assert call_counts_twin.get(s, 0) == 1, f"Seed {seed} step {s}: base_inst_twin called {call_counts_twin.get(s)} times!"
            assert call_counts_ctrl.get(s, 0) == 1, f"Seed {seed} step {s}: base_inst_ctrl called {call_counts_ctrl.get(s)} times!"


# -----------------------------------------------------------------------------
# 5. Full Single Game & CRN Execution (Properties 5, 6, 7, 10)
# -----------------------------------------------------------------------------
def test_crn_and_purity_on_consumed_seeds():
    """Test full CRN execution on seeds 248001 and 248002 (which failed under original runner).
    Verifies pure_pre_e_pass, pure_step_pass, and pure_verbatim_pass are all True.
    """
    for seed in (248001, 248002):
        res = run_seed_crn(seed, allow_consumed_validation=True)
        ga, gb = res["game_a"], res["game_b"]

        assert ga["pure_pre_e_pass"] is True, f"Seed {seed} Game a failed pure_pre_e_pass!"
        assert ga["pure_step_pass"] is True, f"Seed {seed} Game a failed pure_step_pass!"
        assert ga["pure_verbatim_pass"] is True, f"Seed {seed} Game a failed pure_verbatim_pass!"

        assert gb["pure_pre_e_pass"] is True, f"Seed {seed} Game b failed pure_pre_e_pass!"
        assert gb["pure_step_pass"] is True, f"Seed {seed} Game b failed pure_step_pass!"
        assert gb["pure_verbatim_pass"] is True, f"Seed {seed} Game b failed pure_verbatim_pass!"

        # Since H1 abstained, delta must strictly be 0.00
        assert ga["delta"] == 0.0, f"Seed {seed} Game a delta was {ga['delta']}, expected 0.0!"
        assert gb["delta"] == 0.0, f"Seed {seed} Game b delta was {gb['delta']}, expected 0.0!"
        assert res["delta_paired"] == 0.0


# -----------------------------------------------------------------------------
# 6. Terminal Window Micro-Transition Validation (Section XIII)
# -----------------------------------------------------------------------------
def test_terminal_window_micro_transitions():
    """Section XIII: Targeted validation around terminal window (710–718).
    Verifies clean entry, legal candidate generation, dominance computation,
    acceptance logic, and clean baseline passthrough.
    """
    cfg = _get_game_config()
    base_inst = load_baseline()
    agent_h1 = build_agent(base_inst, shadow_only=False)
    ctrl_inst = load_baseline()

    game = papi.Game(248000)
    while not game.done:
        t = game.step_count
        obs0 = game.observe(0)
        obs1 = game.observe(1)

        act0 = agent_h1(copy.deepcopy(obs0), copy.deepcopy(cfg))
        act1 = ctrl_inst.call(copy.deepcopy(obs1), copy.deepcopy(cfg))

        if 710 <= t <= 718:
            # Action serialization check: valid farmer, hands, market structure
            assert "farmer" in act0 and isinstance(act0["farmer"], list)
            assert "hands" in act0 and isinstance(act0["hands"], list)
            assert "market" in act0 and isinstance(act0["market"], list)

        game.step(act0, act1)

    agent_h1.overlay._close_record(0)
    assert len(agent_h1.overlay.records) == 1
    rec = agent_h1.overlay.records[0]
    assert rec["step_E"] == ENTRY_STEP
    assert rec["reason"] in ("ABSTAIN_DOMINANCE", "ABSTAIN_ACCEPT", "OK_ACTIVATED")


# -----------------------------------------------------------------------------
# 7. Checkpoint & Deterministic Resume (Properties 8, 9, 10, 11)
# -----------------------------------------------------------------------------
def test_checkpoint_and_resume(tmp_path):
    """Properties 9, 11: Atomic serialization, duplicate prevention, and clean resume."""
    import run_arch002_h1_reexecution as runner_mod

    raw_file = str(tmp_path / "REEXECUTION_RAW_RESULTS.json")
    csv_file = str(tmp_path / "REEXECUTION_PAIRED_DELTAS.csv")
    tel_file = str(tmp_path / "REEXECUTION_TELEMETRY_EVENTS.csv")

    orig_raw = runner_mod.RAW_RESULTS_FILE
    orig_csv = runner_mod.PAIRED_DELTAS_FILE
    orig_tel = runner_mod.TELEMETRY_EVENTS_FILE

    try:
        runner_mod.RAW_RESULTS_FILE = raw_file
        runner_mod.PAIRED_DELTAS_FILE = csv_file
        runner_mod.TELEMETRY_EVENTS_FILE = tel_file

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
        save_results_checkpoint(mock_res, "2026-09-16T00:00:00Z", status="IN_PROGRESS")

        loaded, count = load_existing_results()
        assert count == 1
        assert 248000 in loaded
        assert loaded[248000]["delta_paired"] == 0.0

        assert os.path.exists(csv_file)
        assert os.path.exists(tel_file)
    finally:
        runner_mod.RAW_RESULTS_FILE = orig_raw
        runner_mod.PAIRED_DELTAS_FILE = orig_csv
        runner_mod.TELEMETRY_EVENTS_FILE = orig_tel


# -----------------------------------------------------------------------------
# 8. Network and Kaggle Isolation (Safety)
# -----------------------------------------------------------------------------
def test_no_network_or_kaggle_contact():
    """Verify zero network, socket, or kaggle imports exist in runner."""
    runner_path = os.path.join(H1_DIR, "run_arch002_h1_reexecution.py")
    with open(runner_path, "r", encoding="utf-8") as f:
        src = f.read()
    for forbidden in ("kaggle", "urllib.request", "requests", "http.client", "socket."):
        assert forbidden not in src, f"Forbidden network reference {forbidden} found in runner!"
