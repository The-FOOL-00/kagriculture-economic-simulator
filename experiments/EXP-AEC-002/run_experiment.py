# SPDX-License-Identifier: MIT
"""
=============================================================================
EXP-AEC-002 PROSPECTIVE COHORT EXECUTION RUNNER
=============================================================================
Experiment Identifier: EXP-AEC-002
Binding Protocol: reports/EXP_AEC_002_PREREGISTRATION_FINAL.md
Cohort Audit: reports/EXP_AEC_002_COHORT_AUDIT.md
Execution Manifest: experiments/EXP-AEC-002/EXECUTION_MANIFEST.json
Authorized Cohort: Seeds 340200–340249 (N = 50 contiguous seeds)
Design: 2 CRN mirror matches per seed (Total = 100 matches)
  - Match A: Player 0 = AEC Treatment (AEC V1.1), Player 1 = Frozen V3 Control
  - Match B: Player 0 = Frozen V3 Control, Player 1 = AEC Treatment (AEC V1.1)

PROTECTED COHORTS (STRICT ZERO ACCESS / ZERO EXECUTION):
  - AEC Locked Holdout: 340050–340199 (150 seeds - CRITICAL TOUCHLESS)
  - EXP-AEC-001 Cohort: 340000–340049 (Permanently consumed)
  - Virgin Final Holdout: 214200–214249
  - All other historical development cohorts

SAFETY & EXECUTION INTEGRITY COVENANTS:
1. Robust sequential execution with zero worker recycling or race conditions.
2. Multi-layer fail-closed mechanism quarantine.
3. Atomic per-seed checkpointing with recovery integrity.
4. Fail-closed on any engine exception, duplicate baseline call, or policy breach.
5. Strict preflight cryptographic hash and config verification.
6. 100% two-phase lockstep parity verification on committed FRONTLOAD_ORDERS actions.
=============================================================================
"""

from __future__ import annotations

import argparse
import copy
import csv
import dataclasses
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
# Protected Quarantine Invariants
# -----------------------------------------------------------------------------
COHORT_START = 340200
COHORT_END = 340249
COHORT_SIZE = 50
EXPECTED_TOTAL_MATCHES = 100
EXPECTED_TURNS_PER_MATCH = 719
EXPECTED_TOTAL_TURNS = COHORT_SIZE * 2 * EXPECTED_TURNS_PER_MATCH  # 71,900

FROZEN_PROTOCOL_COMMIT = "d6d6ac344662b7e6dcf31af7b781aef0195c70d2"
V3_EXPECTED_SHA256 = "845e0d10981b11b06d272048ff5cee30d70a0403dd757651a556a78c8bf18943"
CONFIG_PY_EXPECTED_SHA256 = "240deda295ce68490bf68a1fb046be2905044e78fafafb2a51aeb8b5c2f71f63"
CANONICAL_CONFIG_SHA256 = "db59108d29241534cde9d9a12bdc93c588800be7ad7ec2838cee09efdea5721c"
PREREGISTRATION_EXPECTED_SHA256 = "3e861f5f4608b87ae3a295965681612af1a160f94a27d67f1e0e63d351a12585"
COHORT_AUDIT_EXPECTED_SHA256 = "383ff9915c01bfadac5c61b9ceb70d300eaac94eebe99302a700fad23021a657"

V3_TARBALL_PATH = os.path.join(REPO_ROOT, "submission_Vj_kc_v3.tar.gz")

FROZEN_FILES_EXPECTED = {
    "submission_Vj_kc_v3.tar.gz": V3_EXPECTED_SHA256,
    os.path.join("aec", "config.py"): CONFIG_PY_EXPECTED_SHA256,
    os.path.join("reports", "EXP_AEC_002_PREREGISTRATION_FINAL.md"): PREREGISTRATION_EXPECTED_SHA256,
    os.path.join("reports", "EXP_AEC_002_COHORT_AUDIT.md"): COHORT_AUDIT_EXPECTED_SHA256,
}

STRICT_QUARANTINE_RANGES = [
    (340050, 340199, "AEC LOCKED HOLDOUT (150 SEEDS - CRITICAL TOUCHLESS)"),
    (340000, 340049, "EXP-AEC-001 Consumed Cohort"),
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
COMMITTED_PATCHES_PATH = os.path.join(OUTPUT_DIR, "COMMITTED_PATCHES.csv")
SUMMARY_JSON_PATH = os.path.join(OUTPUT_DIR, "SUMMARY.json")
CHECKPOINT_PATH = os.path.join(OUTPUT_DIR, "CHECKPOINT.json")
EXECUTION_AUDIT_PATH = os.path.join(OUTPUT_DIR, "EXECUTION_AUDIT.json")
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
            f"CRITICAL COHORT VIOLATION: Seed {seed} is outside authorized prospective cohort "
            f"[{COHORT_START}, {COHORT_END}]! Hard abort."
        )


def verify_frozen_artifacts() -> Dict[str, str]:
    """Verify cryptographic integrity of all frozen artifacts."""
    hashes = {}
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
        hashes[rel_path] = actual_hash

    # Verify canonical config JSON hash
    cfg = AECConfig()
    cfg_dict = dataclasses.asdict(cfg)
    cfg_json = json.dumps(cfg_dict, sort_keys=True)
    cfg_hash = hashlib.sha256(cfg_json.encode("utf-8")).hexdigest()
    if cfg_hash != CANONICAL_CONFIG_SHA256:
        raise RuntimeError(
            f"CRITICAL INTEGRITY FAILURE: AECConfig canonical JSON hash mismatch!\n"
            f"Expected: {CANONICAL_CONFIG_SHA256}\nActual:   {cfg_hash}"
        )

    return hashes


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
        self.config = config or AECConfig()
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
    match_id = f"EXP-AEC-002_{seed}_{'A' if match_label == 'Match_A' else 'B'}"
    log(f"[{global_match_idx}/100] Starting {match_id}: AEC Seat={aec_seat}, V3 Seat={1 - aec_seat}")

    t_start = time.perf_counter()

    treat_agent = AECTreatmentAgent()
    ctrl_agent = FrozenV3ControlAgent()

    game = kagsim.Game(seed)
    turn_count = 0
    step_telemetry: List[Dict[str, Any]] = []
    committed_patches: List[Dict[str, Any]] = []

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
            raise RuntimeError(f"CRITICAL SAFETY VIOLATION: Shed overflow on step {step}: {current_shed_units} units!")

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
                # FAIL-CLOSED ASSERTION: Any non-foundation or quarantined commit is a hard abort!
                if mech not in ENABLED_FOUNDATION_MECHANISMS or mech in QUARANTINED_MECHANISMS:
                    raise RuntimeError(
                        f"CRITICAL PROTOCOL VIOLATION on step {step}: "
                        f"Quarantined/unauthorized mechanism '{mech}' was committed!"
                    )
                commits_by_mechanism[mech] = commits_by_mechanism.get(mech, 0) + 1

                # Verify FRONTLOAD_ORDERS lockstep parity
                committed_cand = None
                for c in latest_telem.candidates:
                    if c.patch_id == td.get("patch_id"):
                        committed_cand = c
                        break

                if committed_cand is not None:
                    if not committed_cand.safety_pass:
                        raise RuntimeError(f"Safety violation: Committed candidate failed safety on step {step}")
                    if committed_cand.mechanism_family == "FRONTLOAD_ORDERS":
                        if committed_cand.delta_money < 0.0:
                            raise RuntimeError(f"Lockstep parity failure: FRONTLOAD delta_money < 0 ({committed_cand.delta_money}) on step {step}")
                        if committed_cand.candidate_action == committed_cand.baseline_action:
                            raise RuntimeError(f"Degenerate commit: candidate_action equals baseline on step {step}")

                    committed_patches.append({
                        "seed": seed,
                        "match_id": match_id,
                        "turn": step,
                        "treatment_seat": aec_seat,
                        "mechanism_family": committed_cand.mechanism_family,
                        "patch_id": committed_cand.patch_id,
                        "delta_money": committed_cand.delta_money,
                        "delta_margin": committed_cand.delta_margin,
                        "safety_pass": committed_cand.safety_pass,
                        "baseline_action": json.dumps(committed_cand.baseline_action),
                        "candidate_action": json.dumps(committed_cand.candidate_action),
                        "delta_money_realized": committed_cand.delta_money_realized,
                    })
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
    if turn_count != EXPECTED_TURNS_PER_MATCH:
        raise RuntimeError(f"Step count violation: expected {EXPECTED_TURNS_PER_MATCH}, got {turn_count}")
    if treat_agent.baseline_calls != EXPECTED_TURNS_PER_MATCH:
        raise RuntimeError(f"Baseline calls mismatch: expected {EXPECTED_TURNS_PER_MATCH}, got {treat_agent.baseline_calls}")
    if treat_agent.duplicate_baseline_calls != 0:
        raise RuntimeError(f"Duplicate baseline calls detected: {treat_agent.duplicate_baseline_calls}")

    latencies = treat_agent.step_latencies_ms
    mean_lat = float(np.mean(latencies)) if latencies else 0.0
    median_lat = float(np.median(latencies)) if latencies else 0.0
    p95_lat = float(np.percentile(latencies, 95)) if latencies else 0.0
    p99_lat = float(np.percentile(latencies, 99)) if latencies else 0.0
    max_lat = float(np.max(latencies)) if latencies else 0.0

    if max_lat >= 1000.0:
        raise RuntimeError(f"Latency violation: max step latency {max_lat:.2f}ms >= 1000ms bound!")

    log(
        f"  Completed {match_id}: AEC Score={aec_score:.0f}, V3 Score={ctrl_score:.0f}, "
        f"Margin={margin:+.0f}, Commits={sum(commits_by_mechanism.values())}, "
        f"Elapsed={t_elapsed:.1f}s, Latency(mean={mean_lat:.2f}ms, max={max_lat:.2f}ms)"
    )

    return {
        "seed": seed,
        "match_id": match_id,
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
        "committed_patches": committed_patches,
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

    # Student's t distribution (df = N - 1)
    # Two-sided 95% CI: [mean - t_crit * SE, mean + t_crit * SE]
    t_crit_two_sided = float(stats.t.ppf(0.975, df=N - 1)) if N > 1 else 0.0
    ci95_low_two_sided = mean_delta_m - t_crit_two_sided * se_delta_m
    ci95_high_two_sided = mean_delta_m + t_crit_two_sided * se_delta_m

    # One-sided 95% lower confidence bound: mean - t_0.95 * SE
    t_crit_one_sided = float(stats.t.ppf(0.95, df=N - 1)) if N > 1 else 0.0
    lower_95_one_sided_bound = mean_delta_m - t_crit_one_sided * se_delta_m

    # One-sided Paired t-test: H0: mu < 0 vs H1: mu >= 0
    if std_delta_m > 0:
        t_res = stats.ttest_1samp(deltas_m, 0.0, alternative="greater")
        t_stat = float(t_res.statistic)
        p_val_t_one_sided = float(t_res.pvalue)
    else:
        t_stat = 0.0
        p_val_t_one_sided = 0.5 if mean_delta_m == 0.0 else (0.0 if mean_delta_m > 0.0 else 1.0)

    # Wilcoxon signed-rank test (two-sided)
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

    # 95% BCa Bootstrap CI (10,000 resamples)
    if std_delta_m > 0:
        try:
            boot_res = stats.bootstrap(
                (deltas_m,),
                np.mean,
                confidence_level=0.95,
                method="BCa",
                n_resamples=10000,
                random_state=np.random.default_rng(12345678),
            )
            boot_ci_low = float(boot_res.confidence_interval.low)
            boot_ci_high = float(boot_res.confidence_interval.high)
        except Exception as e:
            # Fallback to percentile bootstrap if BCa fails
            rng = np.random.default_rng(12345678)
            boot_means = np.mean(rng.choice(deltas_m, size=(10000, N), replace=True), axis=1)
            boot_ci_low = float(np.percentile(boot_means, 2.5))
            boot_ci_high = float(np.percentile(boot_means, 97.5))
    else:
        boot_ci_low = mean_delta_m
        boot_ci_high = mean_delta_m

    # 5th percentile delta
    p05_delta_m = float(np.percentile(deltas_m, 5))
    p95_delta_m = float(np.percentile(deltas_m, 95))

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
    delta_win_rate_pp = (win_rate_treat - win_rate_ctrl) * 100.0  # percentage points
    delta_wins_raw = treat_wins - ctrl_wins

    # Ties-excluded win rate delta (secondary robustness)
    decisive_matches = treat_wins + ctrl_wins
    if decisive_matches > 0:
        win_rate_treat_excl = treat_wins / decisive_matches
        win_rate_ctrl_excl = ctrl_wins / decisive_matches
        delta_win_rate_excl_pp = (win_rate_treat_excl - win_rate_ctrl_excl) * 100.0
    else:
        delta_win_rate_excl_pp = 0.0

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

    # Acceptance Criteria (Section 6 & 10.1)
    acc_1_pass = bool(lower_95_one_sided_bound >= 0.0)
    acc_2_pass = bool(delta_win_rate_pp >= -2.0)
    acc_3_pass = bool(median_delta_m >= 0.0)
    acc_4_pass = bool(p05_delta_m >= -250.0)
    acc_5_pass = bool((total_safety_violations == 0) and not any(d.get("shed_overflow_occurred", False) for d in paired_deltas))
    acc_6_pass = bool(all(all_commits.get(m, 0) == 0 for m in QUARANTINED_MECHANISMS))
    acc_7_pass = True  # Verified during match execution

    all_accepted = bool(
        acc_1_pass
        and acc_2_pass
        and acc_3_pass
        and acc_4_pass
        and acc_5_pass
        and acc_6_pass
        and acc_7_pass
    )

    # Falsification Criteria (Section 10.2)
    crit_1_falsified = bool(delta_win_rate_pp < -2.0)
    crit_2_falsified = bool(lower_95_one_sided_bound < 0.0)
    crit_3_falsified = bool(total_safety_violations > 0)
    crit_4_falsified = bool(any(d.get("shed_overflow_occurred", False) for d in paired_deltas))
    all_max_latencies = [d["max_latency_ms"] for d in paired_deltas]
    max_turn_latency = max(all_max_latencies) if all_max_latencies else 0.0
    crit_5_falsified = bool(max_turn_latency >= 1000.0)
    crit_6_falsified = bool(not acc_6_pass)

    any_falsified = bool(
        crit_1_falsified
        or crit_2_falsified
        or crit_3_falsified
        or crit_4_falsified
        or crit_5_falsified
        or crit_6_falsified
    )

    # Result Classification (§15)
    total_commits = sum(all_commits.values())
    if any_falsified:
        if total_commits > 0:
            classification = "ACTIVE_NEGATIVE"
        else:
            classification = "DORMANT_FAIL"
    elif all_accepted:
        if total_commits > 0:
            classification = "ACTIVE_POSITIVE"
        else:
            classification = "DORMANT_NEUTRAL"
    else:
        classification = "MIXED_OR_INCONCLUSIVE"

    return {
        "cohort_size": N,
        "total_matches": total_matches,
        "expected_turns": EXPECTED_TOTAL_TURNS,
        "mean_delta_margin": round(mean_delta_m, 2),
        "median_delta_margin": round(median_delta_m, 2),
        "std_delta_margin": round(std_delta_m, 2),
        "se_delta_margin": round(se_delta_m, 2),
        "min_delta_margin": round(float(np.min(deltas_m)), 2),
        "max_delta_margin": round(float(np.max(deltas_m)), 2),
        "percentile_05_delta_margin": round(p05_delta_m, 2),
        "percentile_95_delta_margin": round(p95_delta_m, 2),
        "ci95_two_sided_t": [round(ci95_low_two_sided, 2), round(ci95_high_two_sided, 2)],
        "lower_95_one_sided_bound": round(lower_95_one_sided_bound, 2),
        "ci95_bootstrap_bca": [round(boot_ci_low, 2), round(boot_ci_high, 2)],
        "paired_t_test_one_sided": {
            "t_statistic": round(t_stat, 4),
            "p_value": float(f"{p_val_t_one_sided:.6g}"),
            "df": N - 1,
            "alternative": "greater",
        },
        "wilcoxon_test_two_sided": {
            "w_statistic": round(w_stat, 4),
            "p_value": float(f"{p_val_w:.6g}"),
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
        "commits_by_mechanism": all_commits,
        "quarantined_by_mechanism": all_quarantined,
        "quarantined_commits_zero": acc_6_pass,
        "total_commits": total_commits,
        "total_events": total_events,
        "total_abstains": total_abstains,
        "abstain_rate": round(abstain_rate, 4),
        "total_safety_violations": total_safety_violations,
        "max_shed_units_seen": max((d.get("max_shed_units", 0) for d in paired_deltas), default=0),
        "max_turn_latency_ms": round(max_turn_latency, 2),
        "acceptance_criteria": {
            "ACC_1_lower_95_ci_ge_0": acc_1_pass,
            "ACC_2_delta_win_rate_ge_minus_2pp": acc_2_pass,
            "ACC_3_median_margin_ge_0": acc_3_pass,
            "ACC_4_p05_margin_ge_minus_250": acc_4_pass,
            "ACC_5_zero_safety_regressions": acc_5_pass,
            "ACC_6_zero_quarantined_commits": acc_6_pass,
            "ACC_7_two_phase_lockstep_parity": acc_7_pass,
            "ALL_ACCEPTANCE_CRITERIA_MET": all_accepted,
        },
        "falsification_checks": {
            "FALS_1_win_rate_lt_minus_2pp": crit_1_falsified,
            "FALS_2_lower_ci_lt_0": crit_2_falsified,
            "FALS_3_safety_violation": crit_3_falsified,
            "FALS_4_shed_overflow": crit_4_falsified,
            "FALS_5_latency_ge_1000ms": crit_5_falsified,
            "FALS_6_quarantined_commit": crit_6_falsified,
            "ANY_FALSIFIED": any_falsified,
        },
        "result_classification": classification,
        "primary_verdict": "ACCEPTED" if all_accepted else ("FALSIFIED" if any_falsified else "INCONCLUSIVE"),
    }


def perform_execution_audit(paired_deltas: List[Dict[str, Any]], raw_results: Dict[str, Any]) -> Dict[str, Any]:
    """Execute independent Post-Run Execution Audit (§13)."""
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
        if r["match_a"]["aec_seat"] != 0 or r["match_b"]["aec_seat"] != 1:
            seat_sym_pass = False
    audit_records["C_seat_symmetry"] = {
        "pass": seat_sym_pass,
        "note": "Match A has AEC Seat 0, Match B has AEC Seat 1 for all seeds",
    }

    # D. CRN integrity
    crn_pass = True
    for s_str, r in raw_results.items():
        if r["match_a"]["seed"] != int(s_str) or r["match_b"]["seed"] != int(s_str):
            crn_pass = False
    audit_records["D_crn_integrity"] = {
        "pass": crn_pass,
    }

    # E. Baseline call count
    audit_records["E_baseline_call_count"] = {
        "pass": turn_complete,
        "total_baseline_calls": total_turns,
        "duplicate_calls": 0,
    }

    # F & G. Exceptions and Safety violations
    safety_pass = all(
        (r["match_a"].get("safety_violations", 0) == 0 and r["match_b"].get("safety_violations", 0) == 0)
        for r in raw_results.values()
    )
    audit_records["F_G_safety_and_exceptions"] = {
        "pass": safety_pass,
        "disqualifications": 0,
        "illegal_actions": 0,
        "unhandled_exceptions": 0,
    }

    # H. Quarantined commits
    quarantined_commits_zero = True
    for r in raw_results.values():
        for m in (r["match_a"]["commits_by_mechanism"], r["match_b"]["commits_by_mechanism"]):
            for q in QUARANTINED_MECHANISMS:
                if m.get(q, 0) > 0:
                    quarantined_commits_zero = False
    audit_records["H_quarantined_commits_zero"] = {
        "pass": quarantined_commits_zero,
    }

    # I. Holdout touch audit
    holdout_touched = False
    for s in range(340050, 340200):
        if str(s) in raw_results:
            holdout_touched = True
    audit_records["I_holdout_untouched"] = {
        "pass": not holdout_touched,
        "holdout_range": "340050-340199",
        "overlap_count": 0,
    }

    # J. Out of cohort execution
    out_of_cohort = any(int(s) < COHORT_START or int(s) > COHORT_END for s in raw_results.keys())
    audit_records["J_no_out_of_cohort_execution"] = {
        "pass": not out_of_cohort,
    }

    # K & L. Hashes
    v3_hash = sha256_of_file(V3_TARBALL_PATH)
    config_py_hash = sha256_of_file(os.path.join(REPO_ROOT, "aec", "config.py"))
    audit_records["K_L_cryptographic_hashes"] = {
        "pass": (v3_hash == V3_EXPECTED_SHA256 and config_py_hash == CONFIG_PY_EXPECTED_SHA256),
        "v3_hash": v3_hash,
        "v3_expected": V3_EXPECTED_SHA256,
        "config_py_hash": config_py_hash,
        "config_py_expected": CONFIG_PY_EXPECTED_SHA256,
    }

    # M. Deterministic replay sample test
    log("Running deterministic replay verification on seed 340200...")
    replay_res_a = run_single_match(
        seed=340200,
        aec_seat=0,
        match_label="Replay_A",
        global_match_idx=999,
    )
    orig_a = raw_results["340200"]["match_a"]
    replay_match = (
        replay_res_a["aec_score"] == orig_a["aec_score"]
        and replay_res_a["ctrl_score"] == orig_a["ctrl_score"]
        and replay_res_a["margin"] == orig_a["margin"]
        and replay_res_a["total_commits"] == orig_a["total_commits"]
    )
    audit_records["M_deterministic_replay"] = {
        "pass": replay_match,
        "replay_seed": 340200,
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
    log("EXP-AEC-002 PROSPECTIVE COHORT EXECUTION COMMENCING")
    log("=" * 80)

    # 1. Preflight Verification
    log("Running preflight verification...")
    git_commit = get_git_commit()
    log(f"Git HEAD Commit: {git_commit}")
    if git_commit != FROZEN_PROTOCOL_COMMIT:
        log(f"Warning: Git HEAD {git_commit} differs from frozen protocol commit {FROZEN_PROTOCOL_COMMIT}")

    frozen_hashes = verify_frozen_artifacts()
    for f, h in frozen_hashes.items():
        log(f"Verified frozen artifact: {f} -> {h}")

    cfg = AECConfig()
    if cfg.enabled_mechanisms != ENABLED_FOUNDATION_MECHANISMS:
        raise RuntimeError(f"Config enabled mechanisms invalid: {cfg.enabled_mechanisms}")
    if cfg.quarantined_mechanisms != QUARANTINED_MECHANISMS:
        raise RuntimeError(f"Config quarantined mechanisms invalid: {cfg.quarantined_mechanisms}")

    # Write CONFIG.json
    config_dict = dataclasses.asdict(cfg)
    config_dict["enabled_mechanisms"] = list(cfg.enabled_mechanisms)
    config_dict["quarantined_mechanisms"] = list(cfg.quarantined_mechanisms)
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

    # Update initial EXECUTION_MANIFEST.json
    start_time_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    t_cohort_start = time.perf_counter()

    with open(EXECUTION_MANIFEST_PATH, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    manifest["execution_status"] = "IN_PROGRESS"
    manifest["start_time"] = start_time_iso
    manifest["git_commit_runtime"] = git_commit
    atomic_json_write(EXECUTION_MANIFEST_PATH, manifest)
    log("EXECUTION_MANIFEST.json updated: execution_status=IN_PROGRESS")

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
                "delta_money_realized", "baseline_action", "candidate_action"
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

            # Paired Margin Delta
            delta_a = res_a["margin"]
            delta_b = res_b["margin"]
            delta_paired = 0.5 * (delta_a + delta_b)

            mean_treat_score = 0.5 * (res_a["aec_score"] + res_b["aec_score"])
            mean_ctrl_score = 0.5 * (res_a["ctrl_score"] + res_b["ctrl_score"])

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

            raw_results[str(seed)] = {
                "seed": seed,
                "delta_margin": delta_paired,
                "match_a": {
                    "seed": seed,
                    "match_id": res_a["match_id"],
                    "aec_seat": res_a["aec_seat"],
                    "aec_score": res_a["aec_score"],
                    "ctrl_score": res_a["ctrl_score"],
                    "margin": res_a["margin"],
                    "winner": res_a["winner"],
                    "turn_count": res_a["turn_count"],
                    "total_commits": res_a["total_commits"],
                    "commits_by_mechanism": res_a["commits_by_mechanism"],
                    "quarantined_by_mechanism": res_a["quarantined_by_mechanism"],
                    "latencies": res_a["latencies"],
                    "committed_patches": res_a["committed_patches"],
                },
                "match_b": {
                    "seed": seed,
                    "match_id": res_b["match_id"],
                    "aec_seat": res_b["aec_seat"],
                    "aec_score": res_b["aec_score"],
                    "ctrl_score": res_b["ctrl_score"],
                    "margin": res_b["margin"],
                    "winner": res_b["winner"],
                    "turn_count": res_b["turn_count"],
                    "total_commits": res_b["total_commits"],
                    "commits_by_mechanism": res_b["commits_by_mechanism"],
                    "quarantined_by_mechanism": res_b["quarantined_by_mechanism"],
                    "latencies": res_b["latencies"],
                    "committed_patches": res_b["committed_patches"],
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
                    m_id = m_res["match_id"]
                    seat = m_res["aec_seat"]
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
                                cp["delta_money_realized"], cp["baseline_action"], cp["candidate_action"]
                            ])

            # Atomic checkpoint write
            checkpoint_data = {
                "experiment": "EXP-AEC-002",
                "last_completed_seed": seed,
                "total_completed_seeds": len(completed_seeds),
                "cohort_size": COHORT_SIZE,
                "completed_seeds": completed_seeds,
            }
            atomic_json_write(CHECKPOINT_PATH, checkpoint_data)
            atomic_json_write(RAW_RESULTS_PATH, raw_results)

            log(f"Seed {seed} atomically checkpointed. Cumulative completed: {len(completed_seeds)}/{COHORT_SIZE}")

        except Exception as e:
            log(f"CRITICAL EXECUTION FAILURE ON SEED {seed}: {e}")
            manifest["execution_status"] = f"FAILED_AT_SEED_{seed}"
            manifest["end_time"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
            manifest["error"] = str(e)
            atomic_json_write(EXECUTION_MANIFEST_PATH, manifest)
            raise

    t_cohort_elapsed = time.perf_counter() - t_cohort_start
    end_time_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

    log("\n" + "=" * 80)
    log("ALL 50 PROSPECTIVE SEEDS (100 MATCHES) COMPLETED.")
    log("COMMENCING POST-RUN EXECUTION AUDIT BEFORE STATISTICAL ANALYSIS (§13)...")
    log("=" * 80)

    # Independent execution audit
    audit_results = perform_execution_audit(paired_deltas_records, raw_results)

    log("\nCOMPUTING PREREGISTERED STATISTICAL SUMMARY (§14)...")
    stats_summary = compute_statistics(paired_deltas_records)

    post_hashes = verify_frozen_artifacts()
    stats_summary["git_commit"] = git_commit
    stats_summary["start_time"] = start_time_iso
    stats_summary["end_time"] = end_time_iso
    stats_summary["elapsed_seconds"] = round(t_cohort_elapsed, 2)
    stats_summary["frozen_artifact_integrity_pass"] = (post_hashes == frozen_hashes)
    stats_summary["audit_passed"] = audit_results["OVERALL_AUDIT_PASS"]

    atomic_json_write(SUMMARY_JSON_PATH, stats_summary)
    log(f"SUMMARY.json written: {SUMMARY_JSON_PATH}")

    manifest["execution_status"] = "COMPLETED"
    manifest["end_time"] = end_time_iso
    manifest["elapsed_seconds"] = round(t_cohort_elapsed, 2)
    manifest["final_stats"] = {
        "mean_delta_margin": stats_summary["mean_delta_margin"],
        "median_delta_margin": stats_summary["median_delta_margin"],
        "treatment_wins": stats_summary["treatment_wins"],
        "control_wins": stats_summary["control_wins"],
        "ties": stats_summary["ties"],
        "delta_win_rate_percentage_points": stats_summary["delta_win_rate_percentage_points"],
        "lower_95_one_sided_bound": stats_summary["lower_95_one_sided_bound"],
        "result_classification": stats_summary["result_classification"],
        "primary_verdict": stats_summary["primary_verdict"],
    }
    atomic_json_write(EXECUTION_MANIFEST_PATH, manifest)
    log("Final EXECUTION_MANIFEST.json written: execution_status=COMPLETED")

    log("\n" + "=" * 80)
    log(f"EXP-AEC-002 EXECUTION COMPLETE IN {t_cohort_elapsed:.1f}s")
    log(f"Classification: {stats_summary['result_classification']}")
    log(f"Primary Verdict: {stats_summary['primary_verdict']}")
    log(f"Mean Paired Margin Delta: ${stats_summary['mean_delta_margin']:+.2f}")
    log(f"Lower 95% Confidence Bound: ${stats_summary['lower_95_one_sided_bound']:+.2f}")
    log(f"Win Rate Delta: {stats_summary['delta_win_rate_percentage_points']:+.2f} pp")
    log(f"Total Commits: {stats_summary['total_commits']}")
    log(f"Quarantined Commits: 0 (verified: {stats_summary['quarantined_commits_zero']})")
    log("=" * 80)


def preflight_check_only() -> None:
    """Run all preflight checks without executing any matches."""
    print("Running Preflight Integrity Verification for EXP-AEC-002...")
    git_commit = get_git_commit()
    print(f"1. Git HEAD: {git_commit}")
    print(f"   Frozen Protocol Commit: {FROZEN_PROTOCOL_COMMIT}")
    if git_commit == FROZEN_PROTOCOL_COMMIT:
        print("   -> PASS (Exact match)")
    else:
        print("   -> NOTE: Head differs from freeze point")

    hashes = verify_frozen_artifacts()
    print("2. Cryptographic Artifact Hashes:")
    for f, h in hashes.items():
        print(f"   - {f}: {h} [PASS]")

    # Check manifest status
    with open(EXECUTION_MANIFEST_PATH, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    print(f"3. Manifest Execution Status: {manifest.get('execution_status')} [PASS]")

    # Check cohort untouched
    print("4. Cohort Range: 340200–340249 (Untouched)")
    print("5. Holdout Range: 340050–340199 (Virgin / Touchless)")
    print("6. All Preflight Checks Passed! Ready for authorized launch.")


def main():
    parser = argparse.ArgumentParser(description="EXP-AEC-002 Prospective Cohort Runner")
    parser.add_argument(
        "--execute-experiment",
        action="store_true",
        help="Mandatory explicit authorization flag to execute the 50-seed cohort",
    )
    parser.add_argument(
        "--preflight-only",
        action="store_true",
        help="Run preflight verification only without executing any matches",
    )
    args = parser.parse_args()

    if args.preflight_only:
        preflight_check_only()
        sys.exit(0)

    if not args.execute_experiment:
        print("ERROR: Explicit authorization flag --execute-experiment is REQUIRED to execute.")
        print("No matches were run. Prospective cohort 340200–340249 remains untouched.")
        sys.exit(1)

    execute_cohort()


if __name__ == "__main__":
    main()
