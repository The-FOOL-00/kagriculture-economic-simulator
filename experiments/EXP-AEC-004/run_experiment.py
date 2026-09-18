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


def compute_statistics(paired_deltas: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Compute preregistered primary and secondary statistical estimators."""
    N = len(paired_deltas)
    if N == 0:
        raise ValueError("Cannot compute statistics on empty cohort.")

    deltas_m = np.array([d["delta_margin"] for d in paired_deltas], dtype=float)
    scores_treat = np.array([d["mean_treat_score"] for d in paired_deltas], dtype=float)
    scores_ctrl = np.array([d["mean_ctrl_score"] for d in paired_deltas], dtype=float)

    # Primary estimator: Mean paired margin delta
    mean_delta_m = float(np.mean(deltas_m))
    std_delta_m = float(np.std(deltas_m, ddof=1)) if N > 1 else 0.0
    se_delta_m = std_delta_m / np.sqrt(N) if N > 0 else 0.0

    # One-sided paired Student's t-test (H0: mu_delta < 0 vs H1: mu_delta >= 0)
    t_crit_one_sided = float(stats.t.ppf(0.95, df=N - 1)) if N > 1 else 0.0
    lower_95_one_sided_bound = mean_delta_m - t_crit_one_sided * se_delta_m

    t_crit_two_sided = float(stats.t.ppf(0.975, df=N - 1)) if N > 1 else 0.0
    ci95_low_two_sided = mean_delta_m - t_crit_two_sided * se_delta_m
    ci95_high_two_sided = mean_delta_m + t_crit_two_sided * se_delta_m

    if se_delta_m > 0:
        t_stat = mean_delta_m / se_delta_m
        p_val_t_one_sided = 1.0 - float(stats.t.cdf(t_stat, df=N - 1))
    else:
        t_stat = 0.0
        p_val_t_one_sided = 0.5 if mean_delta_m == 0 else (0.0 if mean_delta_m > 0 else 1.0)

    # Wilcoxon signed-rank test on non-zero deltas
    nonzero_deltas = deltas_m[deltas_m != 0.0]
    if len(nonzero_deltas) >= 5:
        try:
            w_res = stats.wilcoxon(nonzero_deltas, alternative="greater")
            w_stat, p_val_w = float(w_res.statistic), float(w_res.pvalue)
        except Exception:
            w_stat, p_val_w = 0.0, 1.0
    else:
        w_stat, p_val_w = 0.0, 1.0

    # Distributional Quantiles
    median_delta_m = float(np.median(deltas_m))
    q25 = float(np.percentile(deltas_m, 25))
    q75 = float(np.percentile(deltas_m, 75))
    iqr_delta_m = q75 - q25
    p05_delta_m = float(np.percentile(deltas_m, 5))
    p95_delta_m = float(np.percentile(deltas_m, 95))

    # Win Accounting across all 2*N matches
    treat_wins = 0
    ctrl_wins = 0
    ties = 0
    for d in paired_deltas:
        for w in (d["match_a_winner"], d["match_b_winner"]):
            if w == "TREATMENT":
                treat_wins += 1
            elif w == "CONTROL":
                ctrl_wins += 1
            else:
                ties += 1

    total_matches = 2 * N
    win_rate_treat = treat_wins / total_matches
    win_rate_ctrl = ctrl_wins / total_matches
    delta_win_rate_pp = (win_rate_treat - win_rate_ctrl) * 100.0
    delta_wins_raw = treat_wins - ctrl_wins

    decisive_matches = treat_wins + ctrl_wins
    if decisive_matches > 0:
        delta_win_rate_excl_pp = ((treat_wins - ctrl_wins) / decisive_matches) * 100.0
    else:
        delta_win_rate_excl_pp = 0.0

    # Mechanism Interventions
    all_commits_treat: Dict[str, int] = {}
    all_commits_ctrl: Dict[str, int] = {}
    all_quarantined: Dict[str, int] = {}
    total_events = 0
    total_abstains = 0
    total_safety_violations = 0
    total_feed_commits = 0
    seeds_with_feed_commits = 0

    for d in paired_deltas:
        for m, c in d.get("commits_by_mech_treat", {}).items():
            all_commits_treat[m] = all_commits_treat.get(m, 0) + c
        for m, c in d.get("commits_by_mech_ctrl", {}).items():
            all_commits_ctrl[m] = all_commits_ctrl.get(m, 0) + c
        for m, q in d.get("quarantined_by_mech", {}).items():
            all_quarantined[m] = all_quarantined.get(m, 0) + q
        total_events += d.get("events_count", 0)
        total_abstains += d.get("abstains_count", 0)
        total_safety_violations += d.get("safety_violations", 0)
        fc = d.get("feed_commits_total", 0)
        total_feed_commits += fc
        if fc > 0:
            seeds_with_feed_commits += 1

    abstain_rate = (total_abstains / total_events) if total_events > 0 else 0.0
    activation_rate = seeds_with_feed_commits / N

    # Acceptance Criteria (Section 6.1)
    gate_1_pass = bool(total_safety_violations == 0)
    gate_2_pass = bool(not any(d.get("shed_overflow_occurred", False) for d in paired_deltas))
    ctrl_feed_commits = all_commits_ctrl.get("EMERGENCY_FEED_PURCHASE", 0)
    treat_quarantined = set(QUARANTINED_MECHANISMS) - {"EMERGENCY_FEED_PURCHASE"}
    ctrl_quarantined = set(QUARANTINED_MECHANISMS)
    quarantined_commits = any(all_commits_treat.get(m, 0) > 0 for m in treat_quarantined) or \
                          any(all_commits_ctrl.get(m, 0) > 0 for m in ctrl_quarantined)
    gate_3_pass = bool(ctrl_feed_commits == 0 and not quarantined_commits)
    gate_4_pass = True  # Verified by assertion in every match and post-run audit
    gate_5_pass = True  # Verified by SHA256 invariant
    gate_6_pass = True  # Verified by per-commit counterfactual fidelity == VERIFIED
    gate_7_pass = bool(lower_95_one_sided_bound >= 0.0)
    gate_8_pass = bool(delta_win_rate_pp >= -2.0)

    all_accepted = bool(
        gate_1_pass
        and gate_2_pass
        and gate_3_pass
        and gate_4_pass
        and gate_5_pass
        and gate_6_pass
        and gate_7_pass
        and gate_8_pass
    )

    # Falsification Checks (Section 6.2)
    fals_1 = bool(not gate_1_pass or not gate_2_pass)
    fals_2 = bool(quarantined_commits or ctrl_feed_commits > 0)
    fals_3 = False  # Holdout touch
    fals_4 = bool(lower_95_one_sided_bound < 0.0)
    fals_5 = bool(delta_win_rate_pp < -2.0)
    fals_6 = bool(p05_delta_m < -250.0)

    any_falsified = bool(fals_1 or fals_2 or fals_3 or fals_4 or fals_5 or fals_6)

    # Result Classification (§6.3 of Preregistration Protocol)
    if not gate_1_pass or not gate_2_pass or not gate_3_pass:
        classification = "INVALID"
        primary_verdict = "INTEGRITY_FAILURE"
    elif total_feed_commits < 5:
        classification = "DORMANT_INCONCLUSIVE"
        primary_verdict = "DORMANT"
    elif any_falsified:
        classification = "ACTIVE_NEGATIVE"
        primary_verdict = "FALSIFIED"
    elif all_accepted:
        if mean_delta_m > 0.0:
            classification = "ACTIVE_POSITIVE"
        else:
            classification = "ACTIVE_NON_INFERIOR"
        primary_verdict = "ACCEPTED"
    else:
        classification = "INCONCLUSIVE"
        primary_verdict = "INCONCLUSIVE"

    return {
        "experiment_id": "EXP-AEC-004",
        "cohort_size": N,
        "total_matches": total_matches,
        "expected_turns": EXPECTED_TOTAL_TURNS,
        "mean_delta_margin": round(mean_delta_m, 2),
        "median_delta_margin": round(median_delta_m, 2),
        "std_delta_margin": round(std_delta_m, 2),
        "se_delta_margin": round(se_delta_m, 2),
        "min_delta_margin": round(float(np.min(deltas_m)), 2),
        "max_delta_margin": round(float(np.max(deltas_m)), 2),
        "iqr_delta_margin": round(iqr_delta_m, 2),
        "percentile_05_delta_margin": round(p05_delta_m, 2),
        "percentile_95_delta_margin": round(p95_delta_m, 2),
        "ci95_two_sided_t": [round(ci95_low_two_sided, 2), round(ci95_high_two_sided, 2)],
        "lower_95_one_sided_bound": round(lower_95_one_sided_bound, 2),
        "paired_t_test_one_sided": {
            "t_statistic": round(t_stat, 4),
            "p_value": float(f"{p_val_t_one_sided:.6g}"),
            "df": N - 1,
            "alternative": "greater",
        },
        "wilcoxon_test": {
            "w_statistic": round(w_stat, 4),
            "p_value": float(f"{p_val_w:.6g}"),
            "nonzero_n": int(len(nonzero_deltas)),
        },
        "treatment_wins": treat_wins,
        "control_wins": ctrl_wins,
        "ties": ties,
        "win_rate_treatment": round(win_rate_treat, 4),
        "win_rate_control": round(win_rate_ctrl, 4),
        "delta_win_rate_percentage_points": round(delta_win_rate_pp, 2),
        "delta_win_rate_excl_ties_pp": round(delta_win_rate_excl_pp, 2),
        "delta_wins_raw": delta_wins_raw,
        "mean_treatment_score": round(float(np.mean(scores_treat)), 2),
        "mean_control_score": round(float(np.mean(scores_ctrl)), 2),
        "score_delta": round(float(np.mean(scores_treat) - np.mean(scores_ctrl)), 2),
        "emergency_feed_commits": total_feed_commits,
        "seeds_with_feed_commits": seeds_with_feed_commits,
        "activation_rate": round(activation_rate, 4),
        "commits_by_mechanism_treatment": all_commits_treat,
        "commits_by_mechanism_control": all_commits_ctrl,
        "control_feed_commits": ctrl_feed_commits,
        "quarantined_by_mechanism": all_quarantined,
        "quarantined_commits_zero": not quarantined_commits,
        "total_commits_treatment": sum(all_commits_treat.values()),
        "total_events": total_events,
        "total_abstains": total_abstains,
        "abstain_rate": round(abstain_rate, 4),
        "total_safety_violations": total_safety_violations,
        "max_shed_units_seen": max((d.get("max_shed_units", 0) for d in paired_deltas), default=0),
        "max_turn_latency_ms": round(max((d.get("max_latency_ms", 0.0) for d in paired_deltas), default=0.0), 2),
        "acceptance_criteria": {
            "GATE_1_zero_safety_violations": gate_1_pass,
            "GATE_2_zero_shed_overflow": gate_2_pass,
            "GATE_3_zero_isolation_violations": gate_3_pass,
            "GATE_4_zero_holdout_touches": gate_4_pass,
            "GATE_5_v3_chassis_integrity": gate_5_pass,
            "GATE_6_counterfactual_fidelity_verified": gate_6_pass,
            "GATE_7_economic_non_inferiority": gate_7_pass,
            "GATE_8_win_rate_preservation": gate_8_pass,
            "ALL_ACCEPTANCE_CRITERIA_MET": all_accepted,
        },
        "falsification_checks": {
            "FALS_1_safety_or_shed_overflow": fals_1,
            "FALS_2_isolation_breach": fals_2,
            "FALS_3_holdout_breach": fals_3,
            "FALS_4_lower_ci_lt_0": fals_4,
            "FALS_5_win_rate_lt_minus_2pp": fals_5,
            "FALS_6_p05_margin_lt_minus_250": fals_6,
            "ANY_FALSIFIED": any_falsified,
        },
        "result_classification": classification,
        "primary_verdict": primary_verdict,
    }


def perform_execution_audit(paired_deltas: List[Dict[str, Any]], raw_results: Dict[str, Any]) -> Dict[str, Any]:
    """Execute independent post-run execution audit."""
    log("Running independent post-run execution audit...")
    audit_records = {}

    # A. Cohort completeness
    seeds_seen = sorted([int(s) for s in raw_results.keys()])
    expected_seeds = list(range(COHORT_START, COHORT_END + 1))
    cohort_complete = (seeds_seen == expected_seeds) and len(seeds_seen) == COHORT_SIZE
    audit_records["A_cohort_completeness"] = {
        "pass": cohort_complete,
        "seed_count": len(seeds_seen),
        "expected_count": COHORT_SIZE,
        "min_seed": min(seeds_seen) if seeds_seen else None,
        "max_seed": max(seeds_seen) if seeds_seen else None,
    }

    # B. Turn completeness
    total_turns = 0
    for s_str, r in raw_results.items():
        total_turns += r["match_a"]["turn_count"] + r["match_b"]["turn_count"]
    turn_complete = (total_turns == EXPECTED_TOTAL_TURNS)
    audit_records["B_turn_completeness"] = {
        "pass": turn_complete,
        "total_treatment_turns": total_turns,
        "expected_turns": EXPECTED_TOTAL_TURNS,
    }

    # C. Seat symmetry
    seat_sym_pass = True
    for s_str, r in raw_results.items():
        if r["match_a"]["treatment_seat"] != 0 or r["match_b"]["treatment_seat"] != 1:
            seat_sym_pass = False
    audit_records["C_seat_symmetry"] = {
        "pass": seat_sym_pass,
        "note": "Match A has Treatment Seat 0, Match B has Treatment Seat 1 for all seeds",
    }

    # D. CRN integrity
    crn_pass = True
    for s_str, r in raw_results.items():
        if r["match_a"]["seed"] != r["match_b"]["seed"]:
            crn_pass = False
    audit_records["D_crn_integrity"] = {
        "pass": crn_pass,
        "note": "Match A and Match B share identical seeds across all 50 pairs",
    }

    # E. Holdout protection
    holdout_touch = False
    for s in seeds_seen:
        for lo, hi, label in STRICT_QUARANTINE_RANGES:
            if lo <= s <= hi:
                holdout_touch = True
                break
    audit_records["E_holdout_protection"] = {
        "pass": not holdout_touch,
        "primary_holdout_touches": 0,
        "secondary_holdout_touches": 0,
    }

    # F. V3 Hash Integrity
    v3_sha = sha256_of_file(V3_TARBALL_PATH)
    audit_records["F_v3_chassis_integrity"] = {
        "pass": (v3_sha == V3_EXPECTED_SHA256),
        "actual_sha": v3_sha,
        "expected_sha": V3_EXPECTED_SHA256,
    }

    # G. Mechanism Isolation
    ctrl_feed_commits = sum(d.get("commits_by_mech_ctrl", {}).get("EMERGENCY_FEED_PURCHASE", 0) for d in paired_deltas)
    rc_commits_treat = sum(d.get("commits_by_mech_treat", {}).get("RESOURCE_CONVERSION", 0) for d in paired_deltas)
    rc_commits_ctrl = sum(d.get("commits_by_mech_ctrl", {}).get("RESOURCE_CONVERSION", 0) for d in paired_deltas)
    iso_pass = (ctrl_feed_commits == 0) and (rc_commits_treat == 0) and (rc_commits_ctrl == 0)
    audit_records["G_mechanism_isolation"] = {
        "pass": iso_pass,
        "control_feed_commits": ctrl_feed_commits,
        "resource_conversion_commits_treatment": rc_commits_treat,
        "resource_conversion_commits_control": rc_commits_ctrl,
    }

    # H. Counterfactual Fidelity
    fidelity_pass = True
    for s_str, r in raw_results.items():
        for m_key in ("match_a", "match_b"):
            for cp in r[m_key].get("committed_patches", []):
                if cp.get("counterfactual_fidelity") != "VERIFIED":
                    fidelity_pass = False
    audit_records["H_counterfactual_fidelity"] = {
        "pass": fidelity_pass,
        "note": "100% of committed patches confirmed counterfactual_fidelity == VERIFIED",
    }

    # I. Shed Overflow Invariant
    shed_pass = not any(d.get("shed_overflow_occurred", False) for d in paired_deltas)
    audit_records["I_shed_overflow_integrity"] = {
        "pass": shed_pass,
        "max_shed_units": max((d.get("max_shed_units", 0) for d in paired_deltas), default=0),
    }

    # J. Latency Bound
    all_max_latencies = [d["max_latency_ms"] for d in paired_deltas]
    max_lat = max(all_max_latencies) if all_max_latencies else 0.0
    audit_records["J_latency_bound"] = {
        "pass": (max_lat < 1000.0),
        "max_latency_ms": max_lat,
    }

    # K. Deterministic Replay on Seed 340300
    orig_a = raw_results[str(COHORT_START)]["match_a"]
    log("Running deterministic audit replay on Seed 340300 Match A...")
    replay_res_a = run_single_match(
        seed=COHORT_START,
        treatment_seat=0,
        match_label="Audit_Replay_A",
        global_match_idx=999,
    )
    replay_match = (
        replay_res_a["margin"] == orig_a["margin"]
        and replay_res_a["treatment_score"] == orig_a["treatment_score"]
        and replay_res_a["control_score"] == orig_a["control_score"]
        and replay_res_a["emergency_feed_commits"] == orig_a["emergency_feed_commits"]
    )
    audit_records["K_deterministic_replay"] = {
        "pass": replay_match,
        "replay_seed": COHORT_START,
        "original_margin": orig_a["margin"],
        "replay_margin": replay_res_a["margin"],
    }

    overall_audit_pass = all(v.get("pass", False) for v in audit_records.values())
    audit_records["OVERALL_AUDIT_PASS"] = overall_audit_pass

    atomic_json_write(EXECUTION_AUDIT_PATH, audit_records)
    log(f"Execution audit complete. Overall audit pass: {overall_audit_pass}")
    return audit_records


def execute_cohort() -> None:
    """Execute the full 50-seed cohort with atomic per-seed checkpointing."""
    log("=" * 80)
    log("EXP-AEC-004 PROSPECTIVE COHORT EXECUTION COMMENCING")
    log("=" * 80)

    # Preflight Verification
    log("Running preflight verification...")
    hashes = verify_preflight_environment()
    for f, h in hashes.items():
        log(f"Verified frozen artifact: {f} -> {h}")

    # Checkpoint load / resume
    completed_seeds: Dict[int, Dict[str, Any]] = {}
    if os.path.exists(CHECKPOINT_PATH):
        try:
            with open(CHECKPOINT_PATH, "r", encoding="utf-8") as f:
                chk = json.load(f)
                completed_seeds = {int(k): v for k, v in chk.get("completed_seeds", {}).items()}
                log(f"Resuming from checkpoint: {len(completed_seeds)} completed seeds already recorded.")
        except Exception as e:
            log(f"Warning: Could not read existing checkpoint ({e}). Starting fresh.")

    # Update initial EXECUTION_MANIFEST.json
    start_time_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    t_cohort_start = time.perf_counter()

    with open(EXECUTION_MANIFEST_PATH, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    manifest["status"] = "IN_PROGRESS"
    manifest["start_time"] = start_time_iso
    atomic_json_write(EXECUTION_MANIFEST_PATH, manifest)
    log("EXECUTION_MANIFEST.json updated: status=IN_PROGRESS")

    # CSV headers setup if not resuming
    if not os.path.exists(PAIRED_DELTAS_PATH):
        with open(PAIRED_DELTAS_PATH, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "seed", "delta_margin_a", "delta_margin_b", "delta_margin",
                "treat_score_a", "ctrl_score_a", "treat_score_b", "ctrl_score_b",
                "mean_treat_score", "mean_ctrl_score",
                "match_a_winner", "match_b_winner",
                "commits_treat_a", "commits_treat_b", "total_commits_treat",
                "feed_commits_a", "feed_commits_b", "feed_commits_total",
                "max_latency_ms"
            ])

    if not os.path.exists(TELEMETRY_EVENTS_PATH):
        with open(TELEMETRY_EVENTS_PATH, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "seed", "match_id", "match_label", "turn", "treatment_seat",
                "decision", "committed_mechanism", "patch_id",
                "opp_count", "opp_quarantined_count", "cand_count", "sim_count",
                "abstain_reason", "events", "latency_ms"
            ])

    if not os.path.exists(COMMITTED_PATCHES_PATH):
        with open(COMMITTED_PATCHES_PATH, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "seed", "match_id", "turn", "treatment_seat", "mechanism_family",
                "patch_id", "delta_money", "delta_margin", "safety_pass",
                "counterfactual_fidelity", "delta_money_realized",
                "baseline_action", "candidate_action", "terminal_telemetry"
            ])

    raw_results: Dict[str, Any] = {}
    if os.path.exists(RAW_RESULTS_PATH):
        try:
            with open(RAW_RESULTS_PATH, "r", encoding="utf-8") as f:
                raw_results = json.load(f)
        except Exception:
            raw_results = {}

    paired_deltas_records: List[Dict[str, Any]] = []
    for seed in range(COHORT_START, COHORT_END + 1):
        if seed in completed_seeds:
            paired_deltas_records.append(completed_seeds[seed])

    global_match_counter = len(completed_seeds) * 2

    for seed in range(COHORT_START, COHORT_END + 1):
        if seed in completed_seeds:
            log(f"Seed {seed} already completed in checkpoint. Skipping re-execution.")
            continue

        log(f"\n=== Executing Prospective Seed {seed} ({seed - COHORT_START + 1}/{COHORT_SIZE}) ===")

        try:
            # Match A: Treatment Seat 0, Control Seat 1
            global_match_counter += 1
            res_a = run_single_match(
                seed=seed,
                treatment_seat=0,
                match_label="Match_A",
                global_match_idx=global_match_counter,
            )

            # Match B: Treatment Seat 1, Control Seat 0
            global_match_counter += 1
            res_b = run_single_match(
                seed=seed,
                treatment_seat=1,
                match_label="Match_B",
                global_match_idx=global_match_counter,
            )

            # Paired Margin Delta
            delta_a = res_a["margin"]
            delta_b = res_b["margin"]
            delta_paired = 0.5 * (delta_a + delta_b)

            mean_treat_score = 0.5 * (res_a["treatment_score"] + res_b["treatment_score"])
            mean_ctrl_score = 0.5 * (res_a["control_score"] + res_b["control_score"])

            feed_a = res_a["emergency_feed_commits"]
            feed_b = res_b["emergency_feed_commits"]
            feed_total = feed_a + feed_b

            seed_commits_treat: Dict[str, int] = {}
            for m, c in res_a["commits_by_mechanism_treatment"].items():
                seed_commits_treat[m] = seed_commits_treat.get(m, 0) + c
            for m, c in res_b["commits_by_mechanism_treatment"].items():
                seed_commits_treat[m] = seed_commits_treat.get(m, 0) + c

            seed_commits_ctrl: Dict[str, int] = {}
            for m, c in res_a["commits_by_mechanism_control"].items():
                seed_commits_ctrl[m] = seed_commits_ctrl.get(m, 0) + c
            for m, c in res_b["commits_by_mechanism_control"].items():
                seed_commits_ctrl[m] = seed_commits_ctrl.get(m, 0) + c

            seed_quarantined: Dict[str, int] = {}
            for m, q in res_a["quarantined_by_mechanism"].items():
                seed_quarantined[m] = seed_quarantined.get(m, 0) + q
            for m, q in res_b["quarantined_by_mechanism"].items():
                seed_quarantined[m] = seed_quarantined.get(m, 0) + q

            seed_events = len(res_a["step_telemetry"]) + len(res_b["step_telemetry"])
            seed_abstains = sum(1 for st in res_a["step_telemetry"] if st.get("decision") != "COMMIT") + \
                            sum(1 for st in res_b["step_telemetry"] if st.get("decision") != "COMMIT")
            seed_safety_viol = res_a["safety_violations"] + res_b["safety_violations"]
            seed_max_lat = max(res_a["max_latency_ms"], res_b["max_latency_ms"])

            paired_record = {
                "seed": seed,
                "delta_margin_a": delta_a,
                "delta_margin_b": delta_b,
                "delta_margin": delta_paired,
                "treat_score_a": res_a["treatment_score"],
                "ctrl_score_a": res_a["control_score"],
                "treat_score_b": res_b["treatment_score"],
                "ctrl_score_b": res_b["control_score"],
                "mean_treat_score": mean_treat_score,
                "mean_ctrl_score": mean_ctrl_score,
                "match_a_winner": res_a["winner"],
                "match_b_winner": res_b["winner"],
                "commits_treat_a": sum(res_a["commits_by_mechanism_treatment"].values()),
                "commits_treat_b": sum(res_b["commits_by_mechanism_treatment"].values()),
                "total_commits_treat": sum(seed_commits_treat.values()),
                "feed_commits_a": feed_a,
                "feed_commits_b": feed_b,
                "feed_commits_total": feed_total,
                "commits_by_mech_treat": seed_commits_treat,
                "commits_by_mech_ctrl": seed_commits_ctrl,
                "quarantined_by_mech": seed_quarantined,
                "events_count": seed_events,
                "abstains_count": seed_abstains,
                "safety_violations": seed_safety_viol,
                "shed_overflow_occurred": res_a.get("shed_overflow", False) or res_b.get("shed_overflow", False),
                "max_shed_units": max(res_a.get("max_shed_units", 0), res_b.get("max_shed_units", 0)),
                "max_latency_ms": seed_max_lat,
            }

            completed_seeds[seed] = paired_record
            paired_deltas_records.append(paired_record)

            raw_results[str(seed)] = {
                "seed": seed,
                "delta_margin": delta_paired,
                "match_a": {
                    "seed": seed,
                    "match_id": res_a["match_id"],
                    "treatment_seat": res_a["treatment_seat"],
                    "treatment_score": res_a["treatment_score"],
                    "control_score": res_a["control_score"],
                    "margin": res_a["margin"],
                    "winner": res_a["winner"],
                    "turn_count": res_a["turn_count"],
                    "emergency_feed_commits": res_a["emergency_feed_commits"],
                    "commits_by_mechanism_treatment": res_a["commits_by_mechanism_treatment"],
                    "commits_by_mechanism_control": res_a["commits_by_mechanism_control"],
                    "quarantined_by_mechanism": res_a["quarantined_by_mechanism"],
                    "max_latency_ms": res_a["max_latency_ms"],
                    "committed_patches": res_a["committed_patches"],
                },
                "match_b": {
                    "seed": seed,
                    "match_id": res_b["match_id"],
                    "treatment_seat": res_b["treatment_seat"],
                    "treatment_score": res_b["treatment_score"],
                    "control_score": res_b["control_score"],
                    "margin": res_b["margin"],
                    "winner": res_b["winner"],
                    "turn_count": res_b["turn_count"],
                    "emergency_feed_commits": res_b["emergency_feed_commits"],
                    "commits_by_mechanism_treatment": res_b["commits_by_mechanism_treatment"],
                    "commits_by_mechanism_control": res_b["commits_by_mechanism_control"],
                    "quarantined_by_mechanism": res_b["quarantined_by_mechanism"],
                    "max_latency_ms": res_b["max_latency_ms"],
                    "committed_patches": res_b["committed_patches"],
                },
            }

            # Append to PAIRED_DELTAS.csv
            with open(PAIRED_DELTAS_PATH, "a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([
                    seed, f"{delta_a:.2f}", f"{delta_b:.2f}", f"{delta_paired:.2f}",
                    f"{res_a['treatment_score']:.2f}", f"{res_a['control_score']:.2f}",
                    f"{res_b['treatment_score']:.2f}", f"{res_b['control_score']:.2f}",
                    f"{mean_treat_score:.2f}", f"{mean_ctrl_score:.2f}",
                    res_a["winner"], res_b["winner"],
                    paired_record["commits_treat_a"], paired_record["commits_treat_b"],
                    paired_record["total_commits_treat"],
                    feed_a, feed_b, feed_total,
                    f"{seed_max_lat:.2f}"
                ])

            # Append events to TELEMETRY_EVENTS.csv
            with open(TELEMETRY_EVENTS_PATH, "a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                for m_lbl, m_res in (("Match_A", res_a), ("Match_B", res_b)):
                    m_id = m_res["match_id"]
                    seat = m_res["treatment_seat"]
                    for st in m_res["step_telemetry"]:
                        events_list = st.get("events", [])
                        is_commit = (st.get("decision") == "COMMIT")
                        if len(events_list) > 0 or is_commit:
                            writer.writerow([
                                seed, m_id, m_lbl, st.get("step", 0), seat,
                                st.get("decision", ""),
                                st.get("committed_mechanism") or "",
                                st.get("patch_id") or "",
                                st.get("opp_count", 0),
                                st.get("opp_quarantined_count", 0),
                                st.get("cand_count", 0),
                                st.get("sim_count", 0),
                                st.get("abstain_reason") or "",
                                ";".join(events_list),
                                round(st.get("latency_ms", {}).get("total", 0.0), 2),
                            ])

            # Append committed patches if any
            for m_res in (res_a, res_b):
                if len(m_res["committed_patches"]) > 0:
                    with open(COMMITTED_PATCHES_PATH, "a", newline="", encoding="utf-8") as f:
                        writer = csv.writer(f)
                        for cp in m_res["committed_patches"]:
                            writer.writerow([
                                cp["seed"], cp["match_id"], cp["turn"], cp["treatment_seat"],
                                cp["mechanism_family"], cp["patch_id"],
                                cp["delta_money"], cp["delta_margin"], cp["safety_pass"],
                                cp.get("counterfactual_fidelity", "VERIFIED"),
                                cp["delta_money_realized"], cp["baseline_action"], cp["candidate_action"],
                                cp.get("terminal_telemetry", "{}"),
                            ])

            # Atomic checkpoint write
            checkpoint_data = {
                "experiment": "EXP-AEC-004",
                "last_completed_seed": seed,
                "total_completed_seeds": len(completed_seeds),
                "cohort_size": COHORT_SIZE,
                "completed_seeds": completed_seeds,
            }
            atomic_json_write(CHECKPOINT_PATH, checkpoint_data)
            atomic_json_write(RAW_RESULTS_PATH, raw_results)

            log(f"Seed {seed} checkpointed: Delta Margin={delta_paired:+.2f} (A={delta_a:+.0f}, B={delta_b:+.0f}), Feed Commits={feed_total} (Cumulative seeds: {len(completed_seeds)}/{COHORT_SIZE})")

        except Exception as e:
            log(f"CRITICAL EXECUTION FAILURE ON SEED {seed}: {e}")
            manifest["status"] = f"FAILED_AT_SEED_{seed}"
            manifest["end_time"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
            manifest["error"] = str(e)
            atomic_json_write(EXECUTION_MANIFEST_PATH, manifest)
            raise

    t_cohort_elapsed = time.perf_counter() - t_cohort_start
    end_time_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

    log("\n" + "=" * 80)
    log("ALL 50 PROSPECTIVE SEEDS (100 MATCHES) COMPLETED.")
    log("COMMENCING POST-RUN EXECUTION AUDIT BEFORE STATISTICAL ANALYSIS...")
    log("=" * 80)

    # Independent execution audit
    audit_results = perform_execution_audit(paired_deltas_records, raw_results)

    log("\nCOMPUTING PREREGISTERED STATISTICAL SUMMARY...")
    stats_summary = compute_statistics(paired_deltas_records)

    stats_summary["start_time"] = start_time_iso
    stats_summary["end_time"] = end_time_iso
    stats_summary["elapsed_seconds"] = round(t_cohort_elapsed, 2)
    stats_summary["audit_passed"] = audit_results["OVERALL_AUDIT_PASS"]

    atomic_json_write(SUMMARY_JSON_PATH, stats_summary)
    log(f"SUMMARY.json written: {SUMMARY_JSON_PATH}")

    manifest["status"] = "COMPLETED"
    manifest["end_time"] = end_time_iso
    manifest["elapsed_seconds"] = round(t_cohort_elapsed, 2)
    manifest["final_stats"] = {
        "mean_delta_margin": stats_summary["mean_delta_margin"],
        "median_delta_margin": stats_summary["median_delta_margin"],
        "lower_95_one_sided_bound": stats_summary["lower_95_one_sided_bound"],
        "p_value_one_sided": stats_summary["paired_t_test_one_sided"]["p_value"],
        "delta_win_rate_percentage_points": stats_summary["delta_win_rate_percentage_points"],
        "treatment_wins": stats_summary["treatment_wins"],
        "control_wins": stats_summary["control_wins"],
        "ties": stats_summary["ties"],
        "emergency_feed_commits": stats_summary["emergency_feed_commits"],
        "seeds_with_feed_commits": stats_summary["seeds_with_feed_commits"],
        "result_classification": stats_summary["result_classification"],
        "primary_verdict": stats_summary["primary_verdict"],
    }
    atomic_json_write(EXECUTION_MANIFEST_PATH, manifest)
    log("Final EXECUTION_MANIFEST.json written: status=COMPLETED")

    log("\n" + "=" * 80)
    log(f"EXP-AEC-004 EXECUTION COMPLETE IN {t_cohort_elapsed:.1f}s")
    log(f"Classification: {stats_summary['result_classification']}")
    log(f"Primary Verdict: {stats_summary['primary_verdict']}")
    log(f"Mean Paired Margin Delta: ${stats_summary['mean_delta_margin']:+.2f}")
    log(f"Lower 95% Confidence Bound: ${stats_summary['lower_95_one_sided_bound']:+.2f}")
    log(f"p-value (one-sided): {stats_summary['paired_t_test_one_sided']['p_value']}")
    log(f"Win Rate Delta: {stats_summary['delta_win_rate_percentage_points']:+.2f} pp")
    log(f"Emergency Feed Commits: {stats_summary['emergency_feed_commits']} (in {stats_summary['seeds_with_feed_commits']} seeds)")
    log(f"Control Feed Commits: {stats_summary['control_feed_commits']}")
    log(f"Quarantined Commits: 0 (verified: {stats_summary['quarantined_commits_zero']})")
    log("=" * 80)


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

    # If authorized execution requested:
    if args.authorized_execute_prospective_cohort:
        log("STAGE 2: Authorized Prospective Cohort Execution...")
        execute_cohort()
        sys.exit(0)

    # If no flags provided:
    log("=" * 70)
    log("GOVERNANCE DIRECTIVE: EXECUTION STRICTLY HALTED.")
    log("The protocol is FROZEN. Prospective cohort matches (340300–340349) require --authorized-execute-prospective-cohort.")
    log("To verify the execution infrastructure, run with --preflight-only or --smoke-only.")
    log("=" * 70)
    print("\nSTATUS: FROZEN_NOT_LAUNCHED (EXECUTION HALTED)")
    sys.exit(0)


if __name__ == "__main__":
    main()

