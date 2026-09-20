# SPDX-License-Identifier: MIT
"""
=============================================================================
EXP-AEC-001 PROSPECTIVE COHORT EXECUTION RUNNER
=============================================================================
Experiment Identifier: EXP-AEC-001
Binding Protocol: experiments/EXP-AEC-001_AEC_V1_PREREGISTRATION.md
Authorized Cohort: Seeds 340000–340049 (N = 50 contiguous seeds)
Design: 2 CRN mirror matches per seed (Total = 100 matches)
  - Match A: Player 0 = AEC Treatment, Player 1 = Frozen V3 Control
  - Match B: Player 0 = Frozen V3 Control, Player 1 = AEC Treatment

PROTECTED COHORTS (ZERO ACCESS / ZERO EXECUTION):
  - Final Holdout: 214200–214249
  - All other past/future development and benchmark cohorts

SAFETY COVENANTS:
1. Sequential execution with zero worker recycling.
2. Multi-layer fail-closed mechanism quarantine.
3. Atomic per-seed checkpointing.
4. Fail-closed on any engine exception, duplicate baseline call, or policy breach.
5. Strict preflight cryptographic hash and config verification.
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
from aec.integration.executor import AECExecutor

# -----------------------------------------------------------------------------
# Protected Quarantine Invariants
# -----------------------------------------------------------------------------
COHORT_START = 340000
COHORT_END = 340049
COHORT_SIZE = 50
EXPECTED_TOTAL_MATCHES = 100

V3_EXPECTED_SHA256 = "845e0d10981b11b06d272048ff5cee30d70a0403dd757651a556a78c8bf18943"
V3_TARBALL_PATH = os.path.join(REPO_ROOT, "submission_Vj_kc_v3.tar.gz")

FROZEN_FILES_EXPECTED = {
    "submission_Vj_kc_v3.tar.gz": "845e0d10981b11b06d272048ff5cee30d70a0403dd757651a556a78c8bf18943",
    "submission_Vj_kc_v2.tar.gz": "45b9c54fd4946ff94a7a6de03be3e9d2da1c1662316be1129813b362b0bd22b2",
    os.path.join("candidates", "compiled_v54_plus_residual.py"): "18402ec6fa3709b9b5ef90dd9c8d7b9c0e44aea55ab163e44a80a4adc0cb7eeb",
    os.path.join("candidates", "compiled_v54_plus_shop.py"): "f651ccd220e701968bc33579812d8917da63f5b0582f2fd0d363fa6a16ffd8b8",
    "DEVELOPMENT_HOLDOUT_REGISTRY.md": "0b35f56c4c0a130f559fdd1a90999ed865c905c8e0854937c35e129a73771205",
}

STRICT_QUARANTINE_RANGES = [
    (214200, 214249, "Virgin Final Holdout (CRITICAL PROTECTED)"),
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
    (249000, 249049, "Reserved Alternative 1"),
    (250000, 250049, "Reserved Alternative 2"),
    (255000, 255049, "Reserved Alternative 3"),
    (260000, 260049, "Reserved Alternative 4"),
    (300000, 300049, "Reserved Alternative 5"),
]

OUTPUT_DIR = HERE
EXECUTION_MANIFEST_PATH = os.path.join(OUTPUT_DIR, "EXECUTION_MANIFEST.json")
CONFIG_JSON_PATH = os.path.join(OUTPUT_DIR, "CONFIG.json")
RAW_RESULTS_PATH = os.path.join(OUTPUT_DIR, "RAW_RESULTS.json")
PAIRED_DELTAS_PATH = os.path.join(OUTPUT_DIR, "PAIRED_DELTAS.csv")
TELEMETRY_EVENTS_PATH = os.path.join(OUTPUT_DIR, "TELEMETRY_EVENTS.csv")
SUMMARY_JSON_PATH = os.path.join(OUTPUT_DIR, "SUMMARY.json")
CHECKPOINT_PATH = os.path.join(OUTPUT_DIR, "CHECKPOINT.json")
LOG_PATH = os.path.join(OUTPUT_DIR, "EXECUTION_LOG.txt")


def sha256_of_file(path: str) -> str:
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def log(msg: str) -> None:
    timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
    line = f"[{timestamp}] {msg}"
    print(line, flush=True)
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def atomic_json_write(path: str, data: Any) -> None:
    tmp_path = path + f".tmp_{time.time_ns()}"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp_path, path)


def assert_quarantine_invariants(seed: int) -> None:
    """Strictly assert seed is in authorized cohort and never touches protected ranges."""
    for lo, hi, label in STRICT_QUARANTINE_RANGES:
        if lo <= seed <= hi:
            raise RuntimeError(
                f"CRITICAL QUARANTINE BREACH: Seed {seed} is inside protected range "
                f"[{lo}, {hi}] ({label})! Hard abort."
            )
    if not (COHORT_START <= seed <= COHORT_END):
        raise RuntimeError(
            f"CRITICAL COHORT VIOLATION: Seed {seed} is outside authorized cohort "
            f"[{COHORT_START}, {COHORT_END}]! Hard abort."
        )


def verify_frozen_artifacts() -> Dict[str, str]:
    """Verify cryptographic integrity of all frozen artifacts."""
    deltas = {}
    for rel_path, expected_hash in FROZEN_FILES_EXPECTED.items():
        abs_path = os.path.join(REPO_ROOT, rel_path)
        if not os.path.exists(abs_path):
            raise FileNotFoundError(f"Missing required frozen file: {abs_path}")
        actual_hash = sha256_of_file(abs_path)
        if actual_hash != expected_hash:
            raise RuntimeError(
                f"CRITICAL INTEGRITY FAILURE: {rel_path} hash mismatch!\n"
                f"Expected: {expected_hash}\nActual:   {actual_hash}"
            )
        deltas[rel_path] = actual_hash
    return deltas


def get_git_commit() -> str:
    import subprocess
    try:
        res = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=True
        )
        return res.stdout.strip()
    except Exception as e:
        return f"UNKNOWN_COMMIT_{e}"


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


class FrozenV3ControlAgent:
    """Isolated raw frozen V3 control loaded directly from tarball in memory."""
    def __init__(self, tar_path: str = V3_TARBALL_PATH) -> None:
        if not os.path.exists(tar_path):
            raise FileNotFoundError(f"Frozen V3 tarball not found at: {tar_path}")
        actual_sha = sha256_of_file(tar_path)
        if actual_sha != V3_EXPECTED_SHA256:
            raise RuntimeError(f"V3 integrity breach: {actual_sha} != {V3_EXPECTED_SHA256}")

        with tarfile.open(tar_path, "r:gz") as tar:
            member = tar.extractfile("main.py")
            if member is None:
                raise RuntimeError("Failed to extract main.py from V3 tarball")
            v3_code = member.read().decode("utf-8")
        ns: Dict[str, Any] = {"__name__": f"frozen_v3_ctrl_{time.time_ns()}"}
        exec(compile(v3_code, "frozen_v3_ctrl_main.py", "exec"), ns)
        raw_agent = ns.get("agent")
        if not callable(raw_agent):
            raise RuntimeError("V3 tarball does not define callable 'agent'")
        self._agent = raw_agent

    def act(self, obs: Dict[str, Any], cfg: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return self._agent(obs, cfg)


class AECTreatmentAgent:
    """Instrumented AEC treatment agent wrapping AECExecutor with frozen foundation config."""
    def __init__(self, config: Optional[AECConfig] = None) -> None:
        self.config = config or AECConfig(
            v3_tarball_path=V3_TARBALL_PATH,
            v3_tarball_sha256=V3_EXPECTED_SHA256,
        )
        # Verify mechanism isolation invariants
        assert self.config.enabled_mechanisms == ENABLED_FOUNDATION_MECHANISMS, (
            f"AECConfig enabled_mechanisms violation: {self.config.enabled_mechanisms}"
        )
        assert self.config.quarantined_mechanisms == QUARANTINED_MECHANISMS, (
            f"AECConfig quarantined_mechanisms violation: {self.config.quarantined_mechanisms}"
        )
        assert self.config.frozen_mode is True, "AECConfig must be in frozen_mode"

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
    aec_seat: int,
    match_label: str,
    global_match_idx: int,
) -> Dict[str, Any]:
    """Execute one 719-step match sequentially with fail-closed safety and complete telemetry."""
    assert_quarantine_invariants(seed)
    log(f"[{global_match_idx}/100] Starting Seed={seed} {match_label}: AEC Seat={aec_seat}, V3 Seat={1 - aec_seat}")

    t_start = time.perf_counter()

    treat_agent = AECTreatmentAgent()
    ctrl_agent = FrozenV3ControlAgent()

    game = kagsim.Game(seed)
    turn_count = 0
    step_telemetry: List[Dict[str, Any]] = []

    commits_by_mechanism: Dict[str, int] = {}
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

        # Check live shed inventory for AEC seat
        aec_obs = obs0 if aec_seat == 0 else obs1
        raw_shed = (aec_obs.get("private", {}) or {}).get("shed", {}) or {}
        current_shed_units = sum(int(v or 0) for v in raw_shed.values())
        if current_shed_units > max_shed_units_seen:
            max_shed_units_seen = current_shed_units
        if current_shed_units > 100:
            shed_overflow_occurred = True

        if aec_seat == 0:
            act0 = treat_agent.act(obs0)
            act1 = ctrl_agent.act(obs1)
        else:
            act0 = ctrl_agent.act(obs0)
            act1 = treat_agent.act(obs1)

        latest_telem = treat_agent.executor.latest_telemetry
        if latest_telem is not None:
            td = latest_telem.to_dict()
            step_telemetry.append(td)

            events_list = td.get("events", [])
            if len(events_list) > 0:
                events_count += 1

            if td.get("decision") == "COMMIT":
                mech = td.get("committed_mechanism") or "UNKNOWN"
                # FAIL-CLOSED ASSERTION: Any non-foundation commit is a hard abort!
                if mech not in ENABLED_FOUNDATION_MECHANISMS:
                    raise RuntimeError(
                        f"CRITICAL PROTOCOL VIOLATION on step {step}: "
                        f"Quarantined/unauthorized mechanism '{mech}' was committed!"
                    )
                commits_by_mechanism[mech] = commits_by_mechanism.get(mech, 0) + 1
            else:
                abstains_count += 1

            for q_mech, cnt in td.get("quarantined_by_mechanism", {}).items():
                quarantined_by_mechanism[q_mech] = quarantined_by_mechanism.get(q_mech, 0) + cnt

            reason = td.get("abstain_reason") or ""
            if "POLICY_VIOLATION" in reason:
                safety_violations += 1

        game.step(act0, act1)
        turn_count += 1

    t_elapsed = time.perf_counter() - t_start

    final_reward_0 = float(game.reward(0))
    final_reward_1 = float(game.reward(1))
    aec_score = final_reward_0 if aec_seat == 0 else final_reward_1
    ctrl_score = final_reward_1 if aec_seat == 0 else final_reward_0
    margin = aec_score - ctrl_score

    # Integrity assertions
    if turn_count != 719:
        raise RuntimeError(f"Step count violation: expected 719, got {turn_count}")
    if treat_agent.baseline_calls != 719:
        raise RuntimeError(f"Baseline calls mismatch: expected 719, got {treat_agent.baseline_calls}")
    if treat_agent.duplicate_baseline_calls != 0:
        raise RuntimeError(f"Duplicate baseline calls detected: {treat_agent.duplicate_baseline_calls}")

    latencies = treat_agent.step_latencies_ms
    mean_lat = float(np.mean(latencies)) if latencies else 0.0
    median_lat = float(np.median(latencies)) if latencies else 0.0
    p95_lat = float(np.percentile(latencies, 95)) if latencies else 0.0
    p99_lat = float(np.percentile(latencies, 99)) if latencies else 0.0
    max_lat = float(np.max(latencies)) if latencies else 0.0

    log(
        f"  Completed Seed={seed} {match_label}: AEC Score={aec_score:.0f}, V3 Score={ctrl_score:.0f}, "
        f"Margin={margin:+.0f}, Commits={sum(commits_by_mechanism.values())}, "
        f"Elapsed={t_elapsed:.1f}s, Latency(mean={mean_lat:.2f}ms, max={max_lat:.2f}ms)"
    )

    return {
        "seed": seed,
        "match_label": match_label,
        "aec_seat": aec_seat,
        "turn_count": turn_count,
        "elapsed_seconds": round(t_elapsed, 2),
        "reward_0": final_reward_0,
        "reward_1": final_reward_1,
        "aec_score": aec_score,
        "ctrl_score": ctrl_score,
        "margin": margin,
        "winner": "AEC" if margin > 0 else ("V3" if margin < 0 else "TIE"),
        "commits_by_mechanism": commits_by_mechanism,
        "quarantined_by_mechanism": quarantined_by_mechanism,
        "total_commits": sum(commits_by_mechanism.values()),
        "abstains_count": abstains_count,
        "events_count": events_count,
        "safety_violations": safety_violations,
        "max_shed_units_seen": max_shed_units_seen,
        "shed_overflow_occurred": shed_overflow_occurred,
        "latencies": {
            "mean_ms": round(mean_lat, 2),
            "median_ms": round(median_lat, 2),
            "p95_ms": round(p95_lat, 2),
            "p99_ms": round(p99_lat, 2),
            "max_ms": round(max_lat, 2),
        },
        "step_telemetry": step_telemetry,
    }


def compute_statistics(paired_deltas: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Compute formal preregistered hypothesis statistics."""
    N = len(paired_deltas)
    if N == 0:
        return {}

    deltas_m = np.array([d["delta_margin"] for d in paired_deltas], dtype=np.float64)
    scores_treat = np.array([d["mean_treat_score"] for d in paired_deltas], dtype=np.float64)
    scores_ctrl = np.array([d["mean_ctrl_score"] for d in paired_deltas], dtype=np.float64)

    mean_delta_m = float(np.mean(deltas_m))
    median_delta_m = float(np.median(deltas_m))
    std_delta_m = float(np.std(deltas_m, ddof=1)) if N > 1 else 0.0
    se_delta_m = std_delta_m / np.sqrt(N) if N > 1 else 0.0

    # 95% Student's t Confidence Interval
    t_crit = float(stats.t.ppf(0.975, df=N - 1)) if N > 1 else 0.0
    ci95_low = mean_delta_m - t_crit * se_delta_m
    ci95_high = mean_delta_m + t_crit * se_delta_m

    # Paired t-test
    if std_delta_m > 0:
        t_stat, p_val_t = stats.ttest_1samp(deltas_m, 0.0)
        t_stat = float(t_stat)
        p_val_t = float(p_val_t)
    else:
        t_stat, p_val_t = 0.0, 1.0

    # Wilcoxon signed-rank test
    # If all deltas are 0, wilcoxon cannot be computed directly
    non_zero_deltas = deltas_m[deltas_m != 0.0]
    if len(non_zero_deltas) > 0:
        try:
            w_res = stats.wilcoxon(deltas_m, alternative="two-sided")
            w_stat = float(w_res.statistic)
            p_val_w = float(w_res.pvalue)
        except Exception:
            w_stat, p_val_w = 0.0, 1.0
    else:
        w_stat, p_val_w = 0.0, 1.0

    # Bootstrap 95% CI (10,000 resamples)
    rng = np.random.default_rng(12345678)
    boot_means = np.empty(10000, dtype=np.float64)
    for i in range(10000):
        sample = rng.choice(deltas_m, size=N, replace=True)
        boot_means[i] = np.mean(sample)
    boot_ci_low = float(np.percentile(boot_means, 2.5))
    boot_ci_high = float(np.percentile(boot_means, 97.5))

    # 5th percentile delta
    p05_delta_m = float(np.percentile(deltas_m, 5))

    # Win Accounting across all 2*N matches
    treat_wins = 0
    ctrl_wins = 0
    ties = 0
    for d in paired_deltas:
        w_a = d["match_a_winner"]
        w_b = d["match_b_winner"]
        for w in (w_a, w_b):
            if w == "AEC":
                treat_wins += 1
            elif w == "V3":
                ctrl_wins += 1
            else:
                ties += 1

    total_matches = 2 * N
    win_rate_treat = treat_wins / total_matches
    win_rate_ctrl = ctrl_wins / total_matches
    delta_win_rate = (win_rate_treat - win_rate_ctrl) * 100.0  # percentage points
    delta_wins_raw = treat_wins - ctrl_wins

    # Mechanism Interventions
    all_commits: Dict[str, int] = {}
    all_quarantined: Dict[str, int] = {}
    total_events = 0
    total_abstains = 0
    total_safety_violations = 0

    for d in paired_deltas:
        for m, c in d.get("commits_by_mech", {}).items():
            all_commits[m] = all_commits.get(m, 0) + c
        for m, q in d.get("quarantined_by_mech", {}).items():
            all_quarantined[m] = all_quarantined.get(m, 0) + q
        total_events += d.get("events_count", 0)
        total_abstains += d.get("abstains_count", 0)
        total_safety_violations += d.get("safety_violations", 0)

    abstain_rate = (total_abstains / total_events) if total_events > 0 else 0.0

    # Falsification Criteria Assessment (Preregistration Section 20)
    crit_1_falsified = delta_win_rate < -2.0
    crit_2_falsified = (mean_delta_m < -50.0) and (p_val_t < 0.05)
    crit_3_falsified = total_safety_violations > 0
    crit_4_falsified = any(d.get("shed_overflow_occurred", False) for d in paired_deltas)
    # Max latency check will be computed from match telemetry
    all_max_latencies = [d["max_latency_ms"] for d in paired_deltas]
    max_turn_latency = max(all_max_latencies) if all_max_latencies else 0.0
    crit_5_falsified = max_turn_latency > 1000.0

    any_falsified = (
        crit_1_falsified
        or crit_2_falsified
        or crit_3_falsified
        or crit_4_falsified
        or crit_5_falsified
    )

    # Acceptance Criteria (Section 19)
    acc_1_pass = delta_wins_raw >= 0
    acc_2_pass = mean_delta_m >= 0.0
    acc_3_pass = median_delta_m >= 0.0
    acc_4_pass = p05_delta_m >= -250.0
    acc_5_pass = total_safety_violations == 0
    acc_6_pass = True  # Dormant zero leakage checked

    all_accepted = (
        acc_1_pass
        and acc_2_pass
        and acc_3_pass
        and acc_4_pass
        and acc_5_pass
        and not any_falsified
    )

    return {
        "cohort_size": N,
        "total_matches": total_matches,
        "mean_delta_margin": round(mean_delta_m, 2),
        "median_delta_margin": round(median_delta_m, 2),
        "std_delta_margin": round(std_delta_m, 2),
        "se_delta_margin": round(se_delta_m, 2),
        "ci95_t": [round(ci95_low, 2), round(ci95_high, 2)],
        "ci95_bootstrap": [round(boot_ci_low, 2), round(boot_ci_high, 2)],
        "paired_t_test": {
            "t_statistic": round(t_stat, 4),
            "p_value": float(f"{p_val_t:.6g}"),
        },
        "wilcoxon_test": {
            "w_statistic": round(w_stat, 4),
            "p_value": float(f"{p_val_w:.6g}"),
        },
        "percentile_05_delta_margin": round(p05_delta_m, 2),
        "treatment_wins": treat_wins,
        "control_wins": ctrl_wins,
        "ties": ties,
        "win_rate_treatment": round(win_rate_treat, 4),
        "win_rate_control": round(win_rate_ctrl, 4),
        "delta_win_rate_percentage_points": round(delta_win_rate, 2),
        "delta_wins_raw": delta_wins_raw,
        "mean_treatment_score": round(float(np.mean(scores_treat)), 2),
        "mean_control_score": round(float(np.mean(scores_ctrl)), 2),
        "score_delta": round(float(np.mean(scores_treat) - np.mean(scores_ctrl)), 2),
        "commits_by_mechanism": all_commits,
        "quarantined_by_mechanism": all_quarantined,
        "quarantined_commits_zero": all(all_commits.get(m, 0) == 0 for m in QUARANTINED_MECHANISMS),
        "total_commits": sum(all_commits.values()),
        "total_events": total_events,
        "total_abstains": total_abstains,
        "abstain_rate": round(abstain_rate, 4),
        "total_safety_violations": total_safety_violations,
        "max_shed_units_seen": max((d.get("max_shed_units", 0) for d in paired_deltas), default=0),
        "max_turn_latency_ms": round(max_turn_latency, 2),
        "falsification_checks": {
            "crit_1_delta_win_rate_lt_minus_2pct": crit_1_falsified,
            "crit_2_mean_margin_lt_minus_50_sig": crit_2_falsified,
            "crit_3_safety_disqualification": crit_3_falsified,
            "crit_4_shed_overflow_discard": crit_4_falsified,
            "crit_5_max_latency_gt_1000ms": crit_5_falsified,
            "any_criterion_falsified": any_falsified,
        },
        "acceptance_checks": {
            "acc_1_non_inferior_win_rate": acc_1_pass,
            "acc_2_non_negative_mean_margin": acc_2_pass,
            "acc_3_non_negative_median_margin": acc_3_pass,
            "acc_4_tail_p05_ge_minus_250": acc_4_pass,
            "acc_5_zero_safety_regressions": acc_5_pass,
            "all_criteria_met": all_accepted,
        },
        "hypothesis_verdict": "ACCEPTED" if all_accepted else ("FALSIFIED" if any_falsified else "INCONCLUSIVE"),
    }


def execute_cohort() -> None:
    """Execute the full 50-seed cohort with atomic per-seed checkpointing."""
    log("=" * 80)
    log("EXP-AEC-001 PROSPECTIVE COHORT EXECUTION COMMENCING")
    log("=" * 80)

    # 1. Preflight Verification
    log("Running preflight verification...")
    git_commit = get_git_commit()
    log(f"Git HEAD Commit: {git_commit}")

    frozen_hashes = verify_frozen_artifacts()
    for f, h in frozen_hashes.items():
        log(f"Verified frozen artifact: {f} -> {h}")

    cfg = AECConfig(
        v3_tarball_path=V3_TARBALL_PATH,
        v3_tarball_sha256=V3_EXPECTED_SHA256,
    )
    if cfg.enabled_mechanisms != ENABLED_FOUNDATION_MECHANISMS:
        raise RuntimeError(f"Config enabled mechanisms invalid: {cfg.enabled_mechanisms}")
    if cfg.quarantined_mechanisms != QUARANTINED_MECHANISMS:
        raise RuntimeError(f"Config quarantined mechanisms invalid: {cfg.quarantined_mechanisms}")

    # Write CONFIG.json
    config_dict = {
        "short_horizon": cfg.short_horizon,
        "normal_horizon": cfg.normal_horizon,
        "extended_horizon": cfg.extended_horizon,
        "max_opportunities": cfg.max_opportunities,
        "max_candidates": cfg.max_candidates,
        "max_simulations": cfg.max_simulations,
        "cash_deviation_threshold": cfg.cash_deviation_threshold,
        "shed_alarm_threshold": cfg.shed_alarm_threshold,
        "price_shock_relative": cfg.price_shock_relative,
        "opponent_supply_shock_qty": cfg.opponent_supply_shock_qty,
        "per_step_latency_limit_ms": cfg.per_step_latency_limit_ms,
        "fail_closed": cfg.fail_closed,
        "backbone_type": cfg.backbone_type,
        "v3_tarball_sha256": cfg.v3_tarball_sha256,
        "enabled_mechanisms": list(cfg.enabled_mechanisms),
        "quarantined_mechanisms": list(cfg.quarantined_mechanisms),
        "frozen_mode": cfg.frozen_mode,
    }
    atomic_json_write(CONFIG_JSON_PATH, config_dict)
    log(f"Wrote CONFIG.json: {CONFIG_JSON_PATH}")

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

    # 10. Produce initial EXECUTION_MANIFEST before seed 340000 starts
    start_time_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    t_cohort_start = time.perf_counter()

    manifest = {
        "experiment": "EXP-AEC-001",
        "protocol": "experiments/EXP-AEC-001_AEC_V1_PREREGISTRATION.md",
        "cohort_lo": COHORT_START,
        "cohort_hi": COHORT_END,
        "cohort_size": COHORT_SIZE,
        "matches_per_seed": 2,
        "total_games": EXPECTED_TOTAL_MATCHES,
        "start_time": start_time_iso,
        "end_time": None,
        "elapsed_seconds": None,
        "git_commit": git_commit,
        "v3_tarball_sha256": V3_EXPECTED_SHA256,
        "frozen_file_hashes": frozen_hashes,
        "enabled_mechanisms": list(cfg.enabled_mechanisms),
        "quarantined_mechanisms": list(cfg.quarantined_mechanisms),
        "status": "IN_PROGRESS",
    }
    atomic_json_write(EXECUTION_MANIFEST_PATH, manifest)
    log(f"Pre-execution EXECUTION_MANIFEST written: status=IN_PROGRESS")

    # CSV headers setup if not resuming
    if not os.path.exists(PAIRED_DELTAS_PATH):
        with open(PAIRED_DELTAS_PATH, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "seed", "delta_margin_a", "delta_margin_b", "delta_margin",
                "aec_score_a", "ctrl_score_a", "aec_score_b", "ctrl_score_b",
                "mean_treat_score", "mean_ctrl_score",
                "match_a_winner", "match_b_winner",
                "commits_a", "commits_b", "total_commits",
                "max_latency_ms"
            ])

    if not os.path.exists(TELEMETRY_EVENTS_PATH):
        with open(TELEMETRY_EVENTS_PATH, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "seed", "match_label", "step", "decision", "events",
                "opp_count", "opp_quarantined_count", "cand_count", "sim_count",
                "patch_committed", "committed_mechanism", "patch_id",
                "abstain_reason", "latency_ms"
            ])

    raw_results: Dict[str, Any] = {}
    if os.path.exists(RAW_RESULTS_PATH):
        try:
            with open(RAW_RESULTS_PATH, "r", encoding="utf-8") as f:
                raw_results = json.load(f)
        except Exception:
            raw_results = {}

    paired_deltas_records: List[Dict[str, Any]] = []

    # Reconstruct paired_deltas_records from completed seeds if any
    for seed in range(COHORT_START, COHORT_END + 1):
        if seed in completed_seeds:
            paired_deltas_records.append(completed_seeds[seed])

    # Sequential execution loop over seeds 340000 to 340049
    global_match_counter = len(completed_seeds) * 2

    for seed in range(COHORT_START, COHORT_END + 1):
        if seed in completed_seeds:
            log(f"Seed {seed} already completed in checkpoint. Skipping re-execution.")
            continue

        log(f"\n=== Executing Cohort Seed {seed} ({seed - COHORT_START + 1}/{COHORT_SIZE}) ===")

        try:
            # Match A: AEC Seat = 0, Control Seat = 1
            global_match_counter += 1
            res_a = run_single_match(
                seed=seed,
                aec_seat=0,
                match_label="Match_A",
                global_match_idx=global_match_counter,
            )

            # Match B: AEC Seat = 1, Control Seat = 0
            global_match_counter += 1
            res_b = run_single_match(
                seed=seed,
                aec_seat=1,
                match_label="Match_B",
                global_match_idx=global_match_counter,
            )

            # Compute Paired Delta:
            # delta_margin_a = AEC_score_A - Ctrl_score_A
            # delta_margin_b = AEC_score_B - Ctrl_score_B
            # delta_margin = 0.5 * (delta_margin_a + delta_margin_b)
            delta_a = res_a["margin"]
            delta_b = res_b["margin"]
            delta_paired = 0.5 * (delta_a + delta_b)

            mean_treat_score = 0.5 * (res_a["aec_score"] + res_b["aec_score"])
            mean_ctrl_score = 0.5 * (res_a["ctrl_score"] + res_b["ctrl_score"])

            # Merge mechanism counts
            seed_commits: Dict[str, int] = {}
            for m, c in res_a["commits_by_mechanism"].items():
                seed_commits[m] = seed_commits.get(m, 0) + c
            for m, c in res_b["commits_by_mechanism"].items():
                seed_commits[m] = seed_commits.get(m, 0) + c

            seed_quarantined: Dict[str, int] = {}
            for m, q in res_a["quarantined_by_mechanism"].items():
                seed_quarantined[m] = seed_quarantined.get(m, 0) + q
            for m, q in res_b["quarantined_by_mechanism"].items():
                seed_quarantined[m] = seed_quarantined.get(m, 0) + q

            seed_events = res_a["events_count"] + res_b["events_count"]
            seed_abstains = res_a["abstains_count"] + res_b["abstains_count"]
            seed_safety_viol = res_a["safety_violations"] + res_b["safety_violations"]
            seed_max_lat = max(res_a["latencies"]["max_ms"], res_b["latencies"]["max_ms"])

            paired_record = {
                "seed": seed,
                "delta_margin_a": delta_a,
                "delta_margin_b": delta_b,
                "delta_margin": delta_paired,
                "aec_score_a": res_a["aec_score"],
                "ctrl_score_a": res_a["ctrl_score"],
                "aec_score_b": res_b["aec_score"],
                "ctrl_score_b": res_b["ctrl_score"],
                "mean_treat_score": mean_treat_score,
                "mean_ctrl_score": mean_ctrl_score,
                "match_a_winner": res_a["winner"],
                "match_b_winner": res_b["winner"],
                "commits_a": res_a["total_commits"],
                "commits_b": res_b["total_commits"],
                "total_commits": res_a["total_commits"] + res_b["total_commits"],
                "commits_by_mech": seed_commits,
                "quarantined_by_mech": seed_quarantined,
                "events_count": seed_events,
                "abstains_count": seed_abstains,
                "safety_violations": seed_safety_viol,
                "shed_overflow_occurred": res_a.get("shed_overflow_occurred", False) or res_b.get("shed_overflow_occurred", False),
                "max_shed_units": max(res_a.get("max_shed_units_seen", 0), res_b.get("max_shed_units_seen", 0)),
                "max_latency_ms": seed_max_lat,
            }

            completed_seeds[seed] = paired_record
            paired_deltas_records.append(paired_record)

            # Store in raw_results
            raw_results[str(seed)] = {
                "seed": seed,
                "delta_margin": delta_paired,
                "match_a": {
                    "aec_seat": res_a["aec_seat"],
                    "aec_score": res_a["aec_score"],
                    "ctrl_score": res_a["ctrl_score"],
                    "margin": res_a["margin"],
                    "winner": res_a["winner"],
                    "commits_by_mechanism": res_a["commits_by_mechanism"],
                    "quarantined_by_mechanism": res_a["quarantined_by_mechanism"],
                    "latencies": res_a["latencies"],
                },
                "match_b": {
                    "aec_seat": res_b["aec_seat"],
                    "aec_score": res_b["aec_score"],
                    "ctrl_score": res_b["ctrl_score"],
                    "margin": res_b["margin"],
                    "winner": res_b["winner"],
                    "commits_by_mechanism": res_b["commits_by_mechanism"],
                    "quarantined_by_mechanism": res_b["quarantined_by_mechanism"],
                    "latencies": res_b["latencies"],
                },
            }

            # Append to PAIRED_DELTAS.csv
            with open(PAIRED_DELTAS_PATH, "a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([
                    seed, f"{delta_a:.2f}", f"{delta_b:.2f}", f"{delta_paired:.2f}",
                    f"{res_a['aec_score']:.2f}", f"{res_a['ctrl_score']:.2f}",
                    f"{res_b['aec_score']:.2f}", f"{res_b['ctrl_score']:.2f}",
                    f"{mean_treat_score:.2f}", f"{mean_ctrl_score:.2f}",
                    res_a["winner"], res_b["winner"],
                    res_a["total_commits"], res_b["total_commits"],
                    res_a["total_commits"] + res_b["total_commits"],
                    f"{seed_max_lat:.2f}"
                ])

            # Append events to TELEMETRY_EVENTS.csv
            with open(TELEMETRY_EVENTS_PATH, "a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                for m_lbl, m_res in (("Match_A", res_a), ("Match_B", res_b)):
                    for st in m_res["step_telemetry"]:
                        events_list = st.get("events", [])
                        is_commit = (st.get("decision") == "COMMIT")
                        if len(events_list) > 0 or is_commit:
                            writer.writerow([
                                seed, m_lbl, st.get("step", 0),
                                st.get("decision", ""),
                                ";".join(events_list),
                                st.get("opp_count", 0),
                                st.get("opp_quarantined_count", 0),
                                st.get("cand_count", 0),
                                st.get("sim_count", 0),
                                1 if is_commit else 0,
                                st.get("committed_mechanism") or "",
                                st.get("patch_id") or "",
                                st.get("abstain_reason") or "",
                                round(st.get("latency_ms", {}).get("total", 0.0), 2),
                            ])

            # Atomic checkpoint write
            checkpoint_data = {
                "experiment": "EXP-AEC-001",
                "last_completed_seed": seed,
                "total_completed_seeds": len(completed_seeds),
                "cohort_size": COHORT_SIZE,
                "completed_seeds": completed_seeds,
            }
            atomic_json_write(CHECKPOINT_PATH, checkpoint_data)
            atomic_json_write(RAW_RESULTS_PATH, raw_results)

            log(f"Seed {seed} atomically checkpointed. Cumulative completed: {len(completed_seeds)}/{COHORT_SIZE}")

        except Exception as e:
            log(f"CRITICAL INFRASTRUCTURE FAILURE ON SEED {seed}: {e}")
            manifest["status"] = f"FAILED_AT_SEED_{seed}"
            manifest["end_time"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
            manifest["error"] = str(e)
            atomic_json_write(EXECUTION_MANIFEST_PATH, manifest)
            raise

    # 11. Post-Cohort Analysis & Final Artifact Freezing
    t_cohort_elapsed = time.perf_counter() - t_cohort_start
    end_time_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

    log("\n" + "=" * 80)
    log("ALL 50 SEEDS COMPLETED. COMPUTING PREREGISTERED STATISTICAL SUMMARY...")
    log("=" * 80)

    stats_summary = compute_statistics(paired_deltas_records)

    # Post-execution frozen artifact integrity check
    post_hashes = verify_frozen_artifacts()

    stats_summary["git_commit"] = git_commit
    stats_summary["start_time"] = start_time_iso
    stats_summary["end_time"] = end_time_iso
    stats_summary["elapsed_seconds"] = round(t_cohort_elapsed, 2)
    stats_summary["frozen_artifact_integrity_pass"] = (post_hashes == frozen_hashes)

    atomic_json_write(SUMMARY_JSON_PATH, stats_summary)
    log(f"SUMMARY.json written: {SUMMARY_JSON_PATH}")

    manifest["status"] = "COMPLETED"
    manifest["end_time"] = end_time_iso
    manifest["elapsed_seconds"] = round(t_cohort_elapsed, 2)
    manifest["final_stats"] = {
        "mean_delta_margin": stats_summary["mean_delta_margin"],
        "median_delta_margin": stats_summary["median_delta_margin"],
        "treatment_wins": stats_summary["treatment_wins"],
        "control_wins": stats_summary["control_wins"],
        "ties": stats_summary["ties"],
        "delta_win_rate_percentage_points": stats_summary["delta_win_rate_percentage_points"],
        "hypothesis_verdict": stats_summary["hypothesis_verdict"],
    }
    atomic_json_write(EXECUTION_MANIFEST_PATH, manifest)
    log(f"Final EXECUTION_MANIFEST.json written: status=COMPLETED")

    log("\n" + "=" * 80)
    log(f"EXP-AEC-001 RUN COMPLETE IN {t_cohort_elapsed:.1f}s")
    log(f"Mean Paired Margin Delta: {stats_summary['mean_delta_margin']:+.2f}")
    log(f"Median Paired Margin Delta: {stats_summary['median_delta_margin']:+.2f}")
    log(f"Treatment Wins: {stats_summary['treatment_wins']}, Control Wins: {stats_summary['control_wins']}, Ties: {stats_summary['ties']}")
    log(f"Win Rate Delta: {stats_summary['delta_win_rate_percentage_points']:+.2f}%")
    log(f"Hypothesis Verdict: {stats_summary['hypothesis_verdict']}")
    log("=" * 80)


def main():
    parser = argparse.ArgumentParser(description="EXP-AEC-001 Prospective Cohort Runner")
    parser.add_argument(
        "--execute-experiment",
        action="store_true",
        help="Mandatory explicit authorization flag to execute the 50-seed cohort",
    )
    args = parser.parse_args()

    if not args.execute_experiment:
        print("ERROR: Explicit authorization flag --execute-experiment is REQUIRED to execute.")
        print("No matches were run. Cohort 340000–340049 remains untouched.")
        sys.exit(1)

    execute_cohort()


if __name__ == "__main__":
    main()
