# SPDX-License-Identifier: MIT
"""
=============================================================================
EXP-AEC-004 PROSPECTIVE COHORT EXECUTION RUNNER & PREFLIGHT HARNESS
=============================================================================
Experiment Identifier: EXP-AEC-004
Target Mechanism: EMERGENCY_FEED_PURCHASE (Isolated)
Binding Protocol: reports/EXP_AEC_004_EMERGENCY_FEED_PREREGISTRATION.md
Cohort Audit: reports/EXP_AEC_004_COHORT_AUDIT.md
Prelaunch Audit: reports/EXP_AEC_004_PRELAUNCH_AUDIT.md
Execution Manifest: experiments/EXP-AEC-004/EXECUTION_MANIFEST.json
Authorized Cohort: Seeds 340300–340349 (N = 50 contiguous seeds)
Design: 2 CRN mirror matches per seed (Total = 100 matches)
  - Match A: Player 0 = Treatment (EMERGENCY_FEED_PURCHASE Active), Player 1 = Control (Validated AEC Baseline)
  - Match B: Player 0 = Control (Validated AEC Baseline), Player 1 = Treatment (EMERGENCY_FEED_PURCHASE Active)

PROTECTED COHORTS (STRICT ZERO ACCESS / ZERO EXECUTION):
  - Primary Locked Holdout: 340050–340199 (150 seeds - CRITICAL TOUCHLESS)
  - Secondary Locked Holdout: 214200–214249 (50 seeds - CRITICAL TOUCHLESS)
  - EXP-AEC-001 Cohort: 340000–340049 (Permanently consumed)
  - EXP-AEC-002 Cohort: 340200–340249 (Permanently consumed)
  - EXP-AEC-003 Cohort: 340250–340299 (Permanently consumed)

SAFETY & EXECUTION INTEGRITY COVENANTS:
1. Robust single-process sequential execution with zero worker recycling hazards.
2. Multi-layer fail-closed mechanism quarantine.
3. Target mechanism isolation: Treatment differs from Control by exactly EMERGENCY_FEED_PURCHASE.
4. RESOURCE_CONVERSION strictly quarantined in both arms pending Phase 003.
5. Exact obligation-derived terminal safety; zero arbitrary economic thresholds.
6. Atomic per-seed checkpointing with recovery integrity.
7. Fail-closed on any engine exception, duplicate baseline call, or policy breach.
=============================================================================
"""

from __future__ import annotations

import argparse
import copy
import csv
import datetime
import hashlib
import json
import os
import sys
import tarfile
import time
from typing import Any, Callable, Dict, List, Optional, Tuple

import numpy as np
import scipy.stats as stats

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

import kagsim
from aec.config import (
    AECConfig,
    ENABLED_FOUNDATION_MECHANISMS,
    QUARANTINED_MECHANISMS,
)
from aec.integration.backbone_adapter import BackboneAdapter
from aec.integration.executor import AECExecutor, CandidateTelemetry

# -----------------------------------------------------------------------------
# Protected Quarantine Invariants & Cohort Bounds
# -----------------------------------------------------------------------------
COHORT_START = 340300
COHORT_END = 340349
COHORT_SIZE = 50
EXPECTED_TOTAL_MATCHES = 100
EXPECTED_TURNS_PER_MATCH = 719
EXPECTED_TOTAL_TURNS = COHORT_SIZE * 2 * EXPECTED_TURNS_PER_MATCH  # 71,900

V3_EXPECTED_SHA256 = "845e0d10981b11b06d272048ff5cee30d70a0403dd757651a556a78c8bf18943"
V3_TARBALL_PATH = os.path.join(REPO_ROOT, "submission_Vj_kc_v3.tar.gz")

STRICT_QUARANTINE_RANGES = [
    (340050, 340199, "AEC LOCKED HOLDOUT (150 SEEDS - CRITICAL TOUCHLESS)"),
    (214200, 214249, "GATE 0.3 VIRGIN HOLDOUT (50 SEEDS - CRITICAL TOUCHLESS)"),
    (340000, 340049, "EXP-AEC-001 Consumed Cohort"),
    (340200, 340249, "EXP-AEC-002 Consumed Cohort"),
    (340250, 340299, "EXP-AEC-003 Consumed Cohort"),
    (310000, 310499, "DEV-007 Reserved Cohort"),
    (410000, 410499, "DEV-007 Fallback 1"),
    (510000, 510499, "DEV-007 Fallback 2"),
    (320000, 320499, "ARCH-002 Consumed Cohort"),
    (330000, 330499, "ARCH-003 Consumed Cohort"),
    (50000, 50499, "Consumed Benchmark Block"),
    (50050, 50099, "DEV-006 Qualification Cohort"),
    (50100, 50149, "Audited Benchmark"),
    (50150, 50199, "Contaminated Benchmark"),
    (60000, 60049, "Sweep-Contaminated Block"),
    (245000, 245049, "DEV-003 Consumed Cohort"),
    (246000, 246049, "DEV-004 Consumed Cohort"),
    (247000, 247049, "DEV-005 Consumed Cohort"),
    (248000, 248049, "DEV-006 Consumed Cohort"),
]

OUTPUT_DIR = HERE
EXECUTION_MANIFEST_PATH = os.path.join(OUTPUT_DIR, "EXECUTION_MANIFEST.json")
CONFIG_CONTROL_PATH = os.path.join(OUTPUT_DIR, "CONFIG_CONTROL.json")
CONFIG_TREATMENT_PATH = os.path.join(OUTPUT_DIR, "CONFIG_TREATMENT.json")
RAW_RESULTS_PATH = os.path.join(OUTPUT_DIR, "RAW_RESULTS.json")
PAIRED_DELTAS_PATH = os.path.join(OUTPUT_DIR, "PAIRED_DELTAS.csv")
TELEMETRY_EVENTS_PATH = os.path.join(OUTPUT_DIR, "TELEMETRY_EVENTS.csv")
COMMITTED_PATCHES_PATH = os.path.join(OUTPUT_DIR, "COMMITTED_PATCHES.csv")
SUMMARY_JSON_PATH = os.path.join(OUTPUT_DIR, "SUMMARY.json")
CHECKPOINT_PATH = os.path.join(OUTPUT_DIR, "CHECKPOINT.json")
EXECUTION_AUDIT_PATH = os.path.join(OUTPUT_DIR, "EXECUTION_AUDIT.json")
LOG_PATH = os.path.join(OUTPUT_DIR, "EXECUTION_LOG.txt")


def sha256_of_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def log(msg: str) -> None:
    timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
    line = f"[{timestamp}] {msg}"
    print(line, flush=True)
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def json_default(obj: Any) -> Any:
    if isinstance(obj, (np.bool_, bool)):
        return bool(obj)
    if isinstance(obj, (np.integer, int)):
        return int(obj)
    if isinstance(obj, (np.floating, float)):
        return float(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


def atomic_json_write(path: str, data: Any) -> None:
    tmp_path = path + f".tmp_{time.time_ns()}"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=json_default)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp_path, path)


def assert_quarantine_invariants(seed: int, allow_dev_seed: bool = False) -> None:
    """Strictly assert seed never touches protected holdout or contaminated historical ranges."""
    for lo, hi, label in STRICT_QUARANTINE_RANGES:
        if lo <= seed <= hi:
            if allow_dev_seed and 50000 <= seed <= 50499:
                # Allowed only for explicit non-holdout development smoke tests
                return
            raise RuntimeError(
                f"CRITICAL QUARANTINE BREACH: Seed {seed} is inside protected range "
                f"[{lo}, {hi}] ({label})! Hard abort."
            )
    if not allow_dev_seed:
        if not (COHORT_START <= seed <= COHORT_END):
            raise RuntimeError(
                f"CRITICAL COHORT VIOLATION: Seed {seed} is outside authorized prospective cohort "
                f"[{COHORT_START}, {COHORT_END}]! Hard abort."
            )


def verify_preflight_environment() -> Dict[str, Any]:
    """Verify cryptographic integrity of chassis, configs, manifests, and quarantine boundaries."""
    # 1. Verify V3 tarball
    if not os.path.exists(V3_TARBALL_PATH):
        raise FileNotFoundError(f"V3 tarball missing: {V3_TARBALL_PATH}")
    actual_v3_sha = sha256_of_file(V3_TARBALL_PATH)
    if actual_v3_sha != V3_EXPECTED_SHA256:
        raise RuntimeError(f"V3 SHA mismatch: {actual_v3_sha} != {V3_EXPECTED_SHA256}")

    # 2. Verify Configs exist
    if not os.path.exists(CONFIG_CONTROL_PATH):
        raise FileNotFoundError(f"Control config missing: {CONFIG_CONTROL_PATH}")
    if not os.path.exists(CONFIG_TREATMENT_PATH):
        raise FileNotFoundError(f"Treatment config missing: {CONFIG_TREATMENT_PATH}")
    if not os.path.exists(EXECUTION_MANIFEST_PATH):
        raise FileNotFoundError(f"Execution manifest missing: {EXECUTION_MANIFEST_PATH}")

    with open(CONFIG_CONTROL_PATH, "r", encoding="utf-8") as f:
        ctrl_cfg = json.load(f)
    with open(CONFIG_TREATMENT_PATH, "r", encoding="utf-8") as f:
        treat_cfg = json.load(f)

    # 3. Isolation Verification: Diff must be exactly EMERGENCY_FEED_PURCHASE
    ctrl_enabled = set(ctrl_cfg["enabled_mechanisms"])
    treat_enabled = set(treat_cfg["enabled_mechanisms"])
    diff = treat_enabled - ctrl_enabled
    if diff != {"EMERGENCY_FEED_PURCHASE"}:
        raise RuntimeError(f"Mechanism isolation violation: treatment diff is {diff}, expected exactly {{'EMERGENCY_FEED_PURCHASE'}}")

    # 4. Resource Conversion must be quarantined in both
    if "RESOURCE_CONVERSION" in ctrl_enabled or "RESOURCE_CONVERSION" in treat_enabled:
        raise RuntimeError("Quarantine breach: RESOURCE_CONVERSION is enabled! Must remain quarantined.")
    if "RESOURCE_CONVERSION" not in ctrl_cfg["quarantined_mechanisms"]:
        raise RuntimeError("Quarantine breach: RESOURCE_CONVERSION not in control quarantine list!")
    if "RESOURCE_CONVERSION" not in treat_cfg["quarantined_mechanisms"]:
        raise RuntimeError("Quarantine breach: RESOURCE_CONVERSION not in treatment quarantine list!")

    # 5. Holdout boundary check on cohort
    for s in range(COHORT_START, COHORT_END + 1):
        assert_quarantine_invariants(s)

    hashes = {
        "v3_tarball": actual_v3_sha,
        "config_control_sha": sha256_of_file(CONFIG_CONTROL_PATH),
        "config_treatment_sha": sha256_of_file(CONFIG_TREATMENT_PATH),
        "manifest_sha": sha256_of_file(EXECUTION_MANIFEST_PATH),
    }
    return hashes


class InstrumentedBaselineCallable:
    """Wraps baseline callable to audit baseline calls with zero distortion."""
    def __init__(self, raw_callable: Callable) -> None:
        self.raw_callable = raw_callable
        self.call_count: int = 0
        self.step_calls: Dict[int, int] = {}
        self.duplicate_calls: int = 0

    def __call__(self, obs: Dict[str, Any], cfg: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        step = int(obs.get("step", 0) or 0)
        self.call_count += 1
        prior = self.step_calls.get(step, 0)
        if prior > 0:
            self.duplicate_calls += 1
        self.step_calls[step] = prior + 1
        return self.raw_callable(obs, cfg)


class ExperimentArmAgent:
    """Isolated AEC agent configured for either CONTROL or TREATMENT arm."""
    def __init__(self, arm: str) -> None:
        self.arm = arm.upper()
        if self.arm == "CONTROL":
            cfg_path = CONFIG_CONTROL_PATH
        elif self.arm == "TREATMENT":
            cfg_path = CONFIG_TREATMENT_PATH
        else:
            raise ValueError(f"Unknown arm: {arm}")

        with open(cfg_path, "r", encoding="utf-8") as f:
            cfg_dict = json.load(f)

        self.config = AECConfig(
            enabled_mechanisms=tuple(cfg_dict["enabled_mechanisms"]),
            quarantined_mechanisms=tuple(cfg_dict["quarantined_mechanisms"]),
            frozen_mode=cfg_dict.get("frozen_mode", True),
            short_horizon=cfg_dict.get("short_horizon", 6),
            normal_horizon=cfg_dict.get("normal_horizon", 18),
            extended_horizon=cfg_dict.get("extended_horizon", 36),
            max_opportunities=cfg_dict.get("max_opportunities", 16),
            max_candidates=cfg_dict.get("max_candidates", 8),
            max_simulations=cfg_dict.get("max_simulations", 8),
            fail_closed=cfg_dict.get("fail_closed", True),
            backbone_type=cfg_dict.get("backbone_type", "v3"),
            v3_tarball_path=cfg_dict.get("v3_tarball_path", "submission_Vj_kc_v3.tar.gz"),
            v3_tarball_sha256=cfg_dict.get("v3_tarball_sha256", V3_EXPECTED_SHA256),
        )

        raw_adapter = BackboneAdapter(config=self.config)
        assert raw_adapter._agent_fn is not None
        self.instrumented_baseline = InstrumentedBaselineCallable(raw_adapter._agent_fn)
        raw_adapter._agent_fn = self.instrumented_baseline
        self.executor = AECExecutor(backbone_adapter=raw_adapter, config=self.config)
        self.step_latencies_ms: List[float] = []

    def act(self, obs: Dict[str, Any], cfg: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        t0 = time.perf_counter()
        action = self.executor.act(obs, cfg)
        latency = (time.perf_counter() - t0) * 1000.0
        self.step_latencies_ms.append(latency)
        return action

    @property
    def baseline_calls(self) -> int:
        return self.instrumented_baseline.call_count

    @property
    def duplicate_baseline_calls(self) -> int:
        return self.instrumented_baseline.duplicate_calls


def run_single_match(
    seed: int,
    treatment_seat: int,
    match_label: str,
    global_match_idx: int,
    allow_dev_seed: bool = False,
) -> Dict[str, Any]:
    """Execute one 719-step match sequentially with fail-closed safety and complete telemetry."""
    assert_quarantine_invariants(seed, allow_dev_seed=allow_dev_seed)
    match_id = f"EXP-AEC-004_{seed}_{'A' if match_label == 'Match_A' else 'B'}"
    log(f"[{global_match_idx}/{EXPECTED_TOTAL_MATCHES}] Starting {match_id}: Treatment Seat={treatment_seat}, Control Seat={1 - treatment_seat}")

    t_start = time.perf_counter()

    treat_agent = ExperimentArmAgent("TREATMENT")
    ctrl_agent = ExperimentArmAgent("CONTROL")

    game = kagsim.Game(seed)
    turn_count = 0
    step_telemetry: List[Dict[str, Any]] = []
    committed_patches: List[Dict[str, Any]] = []

    commits_by_mechanism_treat: Dict[str, int] = {}
    commits_by_mechanism_ctrl: Dict[str, int] = {}
    quarantined_by_mechanism: Dict[str, int] = {}
    abstains_count = 0
    events_count = 0
    safety_violations = 0

    max_shed_units_seen = 0
    shed_overflow_occurred = False

    while not game.done:
        step = game.step_count
        obs0 = game.observe(0)
        obs1 = game.observe(1)

        # Check live shed inventory for Treatment seat
        treat_obs = obs0 if treatment_seat == 0 else obs1
        raw_shed = (treat_obs.get("private", {}) or {}).get("shed", {}) or {}
        current_shed_units = sum(int(v or 0) for v in raw_shed.values())
        if current_shed_units > max_shed_units_seen:
            max_shed_units_seen = current_shed_units
        if current_shed_units > 100:
            shed_overflow_occurred = True
            raise RuntimeError(f"CRITICAL SAFETY VIOLATION: Shed overflow on step {step}: {current_shed_units} units!")

        if treatment_seat == 0:
            act0 = treat_agent.act(obs0)
            act1 = ctrl_agent.act(obs1)
        else:
            act0 = ctrl_agent.act(obs0)
            act1 = treat_agent.act(obs1)

        # Inspect Treatment telemetry
        latest_telem_treat = treat_agent.executor.latest_telemetry
        if latest_telem_treat is not None:
            td = latest_telem_treat.to_dict()
            step_telemetry.append(td)

            events_list = td.get("events", [])
            if len(events_list) > 0:
                events_count += 1

            if td.get("decision") == "COMMIT":
                mech = td.get("committed_mechanism") or "UNKNOWN"
                # FAIL-CLOSED ASSERTION: Any non-authorized mechanism is a hard abort!
                if mech not in treat_agent.config.enabled_mechanisms or mech in treat_agent.config.quarantined_mechanisms:
                    raise RuntimeError(
                        f"CRITICAL PROTOCOL VIOLATION on step {step}: "
                        f"Quarantined/unauthorized mechanism '{mech}' was committed by Treatment!"
                    )
                if mech == "RESOURCE_CONVERSION":
                    raise RuntimeError(
                        f"CRITICAL PROTOCOL VIOLATION on step {step}: "
                        f"Quarantined 'RESOURCE_CONVERSION' was committed!"
                    )
                commits_by_mechanism_treat[mech] = commits_by_mechanism_treat.get(mech, 0) + 1

                # Verify committed candidate preconditions
                committed_cand = None
                for c in latest_telem_treat.candidates:
                    if c.patch_id == td.get("patch_id"):
                        committed_cand = c
                        break

                if committed_cand is not None:
                    if not committed_cand.safety_pass:
                        raise RuntimeError(f"Safety violation: Committed candidate failed safety on step {step}")
                    # Precondition: fidelity MUST be VERIFIED
                    committed_cert = None
                    for cert in reversed(treat_agent.executor._certificates):
                        if cert.patch_id == committed_cand.patch_id and cert.baseline_summary.startswith(f"step={step}"):
                            committed_cert = cert
                            break
                    if committed_cert is None:
                        for cert in reversed(treat_agent.executor._certificates):
                            if cert.patch_id == committed_cand.patch_id:
                                committed_cert = cert
                                break
                    fid = committed_cert.counterfactual_fidelity if committed_cert is not None else "UNKNOWN"
                    if fid != "VERIFIED":
                        raise RuntimeError(f"Fidelity violation: Committed candidate has fidelity '{fid}' (not VERIFIED) on step {step}")
                    if committed_cand.candidate_action == committed_cand.baseline_action:
                        raise RuntimeError(f"Degenerate commit: candidate_action equals baseline on step {step}")

                    committed_patches.append({
                        "seed": seed,
                        "match_id": match_id,
                        "turn": step,
                        "treatment_seat": treatment_seat,
                        "mechanism_family": committed_cand.mechanism_family,
                        "patch_id": committed_cand.patch_id,
                        "delta_money": committed_cand.delta_money,
                        "delta_margin": committed_cand.delta_margin,
                        "safety_pass": committed_cand.safety_pass,
                        "counterfactual_fidelity": fid,
                        "baseline_action": json.dumps(committed_cand.baseline_action),
                        "candidate_action": json.dumps(committed_cand.candidate_action),
                        "delta_money_realized": committed_cand.delta_money_realized,
                        "terminal_telemetry": json.dumps(committed_cand.terminal_telemetry) if committed_cand.terminal_telemetry else "{}",
                    })
            else:
                abstains_count += 1

            for q_mech, cnt in td.get("quarantined_by_mechanism", {}).items():
                quarantined_by_mechanism[q_mech] = quarantined_by_mechanism.get(q_mech, 0) + cnt

            reason = td.get("abstain_reason") or ""
            if "POLICY_VIOLATION" in reason:
                safety_violations += 1

        # Inspect Control telemetry (Control must NEVER commit EMERGENCY_FEED_PURCHASE)
        latest_telem_ctrl = ctrl_agent.executor.latest_telemetry
        if latest_telem_ctrl is not None:
            if latest_telem_ctrl.decision == "COMMIT":
                c_mech = latest_telem_ctrl.committed_mechanism or "UNKNOWN"
                if c_mech == "EMERGENCY_FEED_PURCHASE":
                    raise RuntimeError(f"ISOLATION VIOLATION: Control committed EMERGENCY_FEED_PURCHASE on step {step}!")
                commits_by_mechanism_ctrl[c_mech] = commits_by_mechanism_ctrl.get(c_mech, 0) + 1

        game.step(act0, act1)
        turn_count += 1

    t_elapsed = time.perf_counter() - t_start

    final_reward_0 = float(game.reward(0))
    final_reward_1 = float(game.reward(1))
    treat_score = final_reward_0 if treatment_seat == 0 else final_reward_1
    ctrl_score = final_reward_1 if treatment_seat == 0 else final_reward_0
    margin = treat_score - ctrl_score

    # Integrity assertions
    if turn_count != EXPECTED_TURNS_PER_MATCH:
        raise RuntimeError(f"Step count violation: expected {EXPECTED_TURNS_PER_MATCH}, got {turn_count}")
    if treat_agent.baseline_calls != EXPECTED_TURNS_PER_MATCH:
        raise RuntimeError(f"Treatment baseline calls mismatch: expected {EXPECTED_TURNS_PER_MATCH}, got {treat_agent.baseline_calls}")
    if treat_agent.duplicate_baseline_calls != 0:
        raise RuntimeError(f"Duplicate treatment baseline calls detected: {treat_agent.duplicate_baseline_calls}")
    if ctrl_agent.baseline_calls != EXPECTED_TURNS_PER_MATCH:
        raise RuntimeError(f"Control baseline calls mismatch: expected {EXPECTED_TURNS_PER_MATCH}, got {ctrl_agent.baseline_calls}")

    latencies = treat_agent.step_latencies_ms
    mean_lat = float(np.mean(latencies)) if latencies else 0.0
    max_lat = float(np.max(latencies)) if latencies else 0.0

    if max_lat >= 1000.0:
        raise RuntimeError(f"Latency violation: max step latency {max_lat:.2f}ms >= 1000ms bound!")

    feed_commits = commits_by_mechanism_treat.get("EMERGENCY_FEED_PURCHASE", 0)

    log(
        f"  Completed {match_id}: Treatment Score={treat_score:.0f}, Control Score={ctrl_score:.0f}, "
        f"Margin={margin:+.0f}, Feed Commits={feed_commits}, Total Treat Commits={sum(commits_by_mechanism_treat.values())}, "
        f"Control Feed Commits=0, Elapsed={t_elapsed:.1f}s, Latency(mean={mean_lat:.2f}ms, max={max_lat:.2f}ms)"
    )

    return {
        "seed": seed,
        "match_id": match_id,
        "match_label": match_label,
        "treatment_seat": treatment_seat,
        "turn_count": turn_count,
        "treatment_score": treat_score,
        "control_score": ctrl_score,
        "margin": margin,
        "winner": "TREATMENT" if margin > 0 else ("CONTROL" if margin < 0 else "TIE"),
        "commits_by_mechanism_treatment": commits_by_mechanism_treat,
        "commits_by_mechanism_control": commits_by_mechanism_ctrl,
        "emergency_feed_commits": feed_commits,
        "quarantined_by_mechanism": quarantined_by_mechanism,
        "safety_violations": safety_violations,
        "shed_overflow": shed_overflow_occurred,
        "max_shed_units": max_shed_units_seen,
        "mean_latency_ms": mean_lat,
        "max_latency_ms": max_lat,
        "elapsed_seconds": t_elapsed,
        "step_telemetry": step_telemetry,
        "committed_patches": committed_patches,
    }


def run_smoke_test(smoke_seed: int = 50015) -> bool:
    """Execute exactly one paired match on a non-cohort, non-holdout development seed to verify harness health."""
    log(f"=== RUNNING DEVELOPMENT SMOKE TEST ON SEED {smoke_seed} ===")
    assert 50000 <= smoke_seed <= 50024, f"Smoke seed {smoke_seed} must be in development block 50000-50024"
    assert_quarantine_invariants(smoke_seed, allow_dev_seed=True)

    hashes = verify_preflight_environment()
    log(f"Preflight hashes verified: {hashes}")

    # Match A: Treatment Seat 0, Control Seat 1
    res_a = run_single_match(smoke_seed, 0, "Match_A", 1, allow_dev_seed=True)
    # Match B: Treatment Seat 1, Control Seat 0
    res_b = run_single_match(smoke_seed, 1, "Match_B", 2, allow_dev_seed=True)

    paired_delta = 0.5 * (res_a["margin"] + res_b["margin"])
    feed_commits_total = res_a["emergency_feed_commits"] + res_b["emergency_feed_commits"]

    log(f"Smoke Test Results: Match A Margin={res_a['margin']:+.0f}, Match B Margin={res_b['margin']:+.0f}")
    log(f"Smoke Test Paired Delta: {paired_delta:+.2f}, Emergency Feed Commits: {feed_commits_total}")
    log(f"Control Feed Commits: Match A={res_a['commits_by_mechanism_control'].get('EMERGENCY_FEED_PURCHASE', 0)}, Match B={res_b['commits_by_mechanism_control'].get('EMERGENCY_FEED_PURCHASE', 0)}")
    log("=== SMOKE TEST PASSED: HARNESS, AGENTS, AND ISOLATION VERIFIED ===")
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description="EXP-AEC-004 Prospective Runner & Preflight Harness")
    parser.add_argument("--preflight-only", action="store_true", help="Run cryptographic and configuration preflight and exit")
    parser.add_argument("--smoke-only", action="store_true", help="Run development-only smoke test on a non-cohort seed and exit")
    parser.add_argument("--smoke-seed", type=int, default=50015, help="Development seed for smoke test (default: 50015)")
    parser.add_argument("--authorized-execute-prospective-cohort", action="store_true", help="Explicit directive to execute the prospective cohort")
    args = parser.parse_args()

    log("=" * 70)
    log("EXP-AEC-004 RUNNER INITIALIZATION")
    log("=" * 70)

    # Stage 1: Preflight Verification
    log("STAGE 1: Preflight Verification...")
    hashes = verify_preflight_environment()
    log(f"Preflight verified successfully: {hashes}")

    if args.preflight_only:
        log("PREFLIGHT CHECK COMPLETED SUCCESSFULLY. (Preflight-only requested)")
        print("\nPREFLIGHT_PASS: TRUE")
        sys.exit(0)

    if args.smoke_only:
        log(f"STAGE 2: Development Smoke Test on Seed {args.smoke_seed}...")
        run_smoke_test(args.smoke_seed)
        log("SMOKE TEST COMPLETED SUCCESSFULLY.")
        print("\nSMOKE_TEST_PASS: TRUE")
        sys.exit(0)

    # If neither preflight nor smoke nor authorized execution:
    if not args.authorized_execute_prospective_cohort:
        log("=" * 70)
        log("GOVERNANCE DIRECTIVE: EXECUTION STRICTLY HALTED.")
        log("The protocol is FROZEN. Prospective cohort matches (340300–340349) are NOT authorized in this task.")
        log("To verify the execution infrastructure, run with --preflight-only or --smoke-only.")
        log("=" * 70)
        print("\nSTATUS: FROZEN_NOT_LAUNCHED (EXECUTION HALTED)")
        sys.exit(0)

    # SAFETY STOP: Prospective cohort execution is blocked in this task by statute
    raise RuntimeError(
        "FATAL GOVERNANCE BREACH: Prospective cohort execution was invoked! "
        "Per statutory mandate, this task is PREREGISTRATION + TRIAL INFRASTRUCTURE ONLY. "
        "Prospective execution must occur under a separate, independently authorized task."
    )


if __name__ == "__main__":
    main()
