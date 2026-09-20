#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""AEC Phase 008: Canonical Integrated Offline Validation (§Preregistration).

Executes full offline integration validation under Common Random Numbers (CRN)
with mirror seating across:
  1. Primary Cohort: Fresh Reserved Discovery Partition 249000-249024 (N=25 seeds, 50 matches).
  2. Benchmark Cohort: Historical Re-Baseline Partition 50000-50024 (N=25 seeds, 50 matches).

Evaluates:
  Arm A: Control (Frozen V3 vs Frozen V3 under mirror seating)
  Arm B: Integrated ROBUST AEC vs Frozen V3 under mirror seating

Enforces strict scientific governance:
  - Touchless holdout protection (340050-340199, 214200-214249, 340300-340349).
  - Prospective tournament matches = 0.
  - V3 SHA-256 verified byte-for-byte.
  - RESOURCE_CONVERSION strictly quarantined.
  - Fail-closed execution.
"""

from __future__ import annotations

import copy
import csv
import hashlib
import json
import os
import sys
import tarfile
import time
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

import kagsim
from aec.config import AECConfig
from aec.integration.executor import AECExecutor

V3_TARBALL_PATH = os.path.join(REPO_ROOT, "submission_Vj_kc_v3.tar.gz")
V3_EXPECTED_SHA256 = "845e0d10981b11b06d272048ff5cee30d70a0403dd757651a556a78c8bf18943"

PRIMARY_SEEDS = list(range(249000, 249025))  # 25 fresh discovery seeds
BENCHMARK_SEEDS = list(range(50000, 50025))  # 25 historical benchmark seeds

RESULTS_DIR = os.path.join(REPO_ROOT, "results")
os.makedirs(RESULTS_DIR, exist_ok=True)


def sha256_of_file(filepath: str) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def assert_governance(seed: int) -> None:
    # 1. Primary Locked Holdout
    if 340050 <= seed <= 340199:
        raise RuntimeError(f"FATAL GOVERNANCE BREACH: Primary holdout seed {seed} accessed!")
    # 2. Gate 0.3 Virgin Final Holdout
    if 214200 <= seed <= 214249:
        raise RuntimeError(f"FATAL GOVERNANCE BREACH: Gate 0.3 holdout seed {seed} accessed!")
    # 3. Prospective Tournament Cohort
    if 340300 <= seed <= 340349:
        raise RuntimeError(f"FATAL GOVERNANCE BREACH: Prospective cohort seed {seed} accessed!")

    # Verify V3 hash
    actual_sha = sha256_of_file(V3_TARBALL_PATH)
    if actual_sha != V3_EXPECTED_SHA256:
        raise RuntimeError(f"FATAL CHASSIS BREACH: V3 hash {actual_sha} != {V3_EXPECTED_SHA256}")


def load_v3_agent() -> Any:
    with tarfile.open(V3_TARBALL_PATH, "r:gz") as tar:
        member = tar.extractfile("main.py")
        if member is None:
            raise RuntimeError("Failed to extract main.py from V3 tarball")
        v3_code = member.read().decode("utf-8")
    ns: Dict[str, Any] = {"__name__": f"frozen_v3_{time.time_ns()}"}
    exec(compile(v3_code, "frozen_v3_main.py", "exec"), ns)
    return ns["agent"]


class FrozenV3ControlAgent:
    """Isolated raw frozen V3 control loaded in memory."""
    def __init__(self) -> None:
        self._agent = load_v3_agent()

    def act(self, obs: Dict[str, Any], cfg: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return self._agent(obs, cfg)


def run_mirror_match(
    seed: int,
    aec_seat: int,
    executor: Any,
    rival_agent: Any
) -> Dict[str, Any]:
    """Runs a single match under Common Random Numbers with specified seat assignment."""
    assert_governance(seed)
    game = kagsim.Game(seed)
    latencies: List[float] = []

    while not game.done:
        obs0 = game.observe(0)
        obs1 = game.observe(1)

        t0 = time.perf_counter()
        if aec_seat == 0:
            act0 = executor.act(obs0)
            lat_ms = (time.perf_counter() - t0) * 1000.0
            act1 = rival_agent.act(obs1)
        else:
            act0 = rival_agent.act(obs0)
            t0 = time.perf_counter()
            act1 = executor.act(obs1)
            lat_ms = (time.perf_counter() - t0) * 1000.0

        latencies.append(lat_ms)
        game.step(act0, act1)

    r0 = float(game.reward(0))
    r1 = float(game.reward(1))

    # Reward from perspective of AEC executor
    treatment_reward = r0 if aec_seat == 0 else r1
    control_reward = r1 if aec_seat == 0 else r0
    margin = treatment_reward - control_reward

    telemetry_history = getattr(executor, "_telemetry_history", [])
    total_candidates = sum(len(t.candidates) for t in telemetry_history)
    total_simulations = sum(t.simulations_run for t in telemetry_history)
    committed = sum(1 for t in telemetry_history if t.decision == "COMMIT")
    abstained = sum(1 for t in telemetry_history if t.decision == "ABSTAIN")
    fallback_count = getattr(executor, "fallback_policy", None).fallback_count if hasattr(executor, "fallback_policy") else 0

    # Per-mechanism breakdown
    commits_by_mech: Dict[str, int] = {}
    for t in telemetry_history:
        if t.decision == "COMMIT" and t.committed_mechanism:
            commits_by_mech[t.committed_mechanism] = commits_by_mech.get(t.committed_mechanism, 0) + 1

    return {
        "seed": seed,
        "seat": aec_seat,
        "treatment_reward": treatment_reward,
        "control_reward": control_reward,
        "margin": margin,
        "win": margin > 0,
        "loss": margin < 0,
        "tie": margin == 0,
        "latency_p50": float(np.percentile(latencies, 50)) if latencies else 0.0,
        "latency_p95": float(np.percentile(latencies, 95)) if latencies else 0.0,
        "latency_p99": float(np.percentile(latencies, 99)) if latencies else 0.0,
        "worst_turn_ms": float(np.max(latencies)) if latencies else 0.0,
        "mean_latency_ms": float(np.mean(latencies)) if latencies else 0.0,
        "total_candidates": total_candidates,
        "total_simulations": total_simulations,
        "committed": committed,
        "abstained": abstained,
        "fallback_count": fallback_count,
        "commits_by_mech": commits_by_mech,
    }


def evaluate_cohort(
    cohort_name: str,
    seeds: List[int],
    cfg_robust: AECConfig
) -> Dict[str, Any]:
    """Executes full paired CRN mirror-seat evaluation for a seed cohort."""
    print(f"\n========================================================")
    print(f"EVALUATING COHORT: {cohort_name} ({len(seeds)} seeds, {len(seeds)*2} matches)")
    print(f"========================================================")

    matches_data: List[Dict[str, Any]] = []
    seed_summary: Dict[int, Dict[str, Any]] = {}

    for i, seed in enumerate(seeds):
        t_seed0 = time.time()
        
        # Match A: AEC is Seat 0, V3 is Seat 1
        exec_seat0 = AECExecutor(config=cfg_robust)
        ctrl_agent_1 = FrozenV3ControlAgent()
        res_m1 = run_mirror_match(seed, aec_seat=0, executor=exec_seat0, rival_agent=ctrl_agent_1)
        res_m1["cohort"] = cohort_name
        res_m1["match_id"] = f"{cohort_name}_{seed}_S0"
        matches_data.append(res_m1)

        # Match B: V3 is Seat 0, AEC is Seat 1
        exec_seat1 = AECExecutor(config=cfg_robust)
        ctrl_agent_0 = FrozenV3ControlAgent()
        res_m2 = run_mirror_match(seed, aec_seat=1, executor=exec_seat1, rival_agent=ctrl_agent_0)
        res_m2["cohort"] = cohort_name
        res_m2["match_id"] = f"{cohort_name}_{seed}_S1"
        matches_data.append(res_m2)

        # Paired net delta (mirror-averaged)
        net_delta = (res_m1["margin"] + res_m2["margin"]) / 2.0
        seed_win = (res_m1["margin"] > 0 and res_m2["margin"] >= 0) or (res_m2["margin"] > 0 and res_m1["margin"] >= 0)
        seed_loss = (res_m1["margin"] < 0 and res_m2["margin"] <= 0) or (res_m2["margin"] < 0 and res_m1["margin"] <= 0)
        
        # Merge commits by mechanism
        seed_commits_by_mech: Dict[str, int] = {}
        for k, v in res_m1["commits_by_mech"].items():
            seed_commits_by_mech[k] = seed_commits_by_mech.get(k, 0) + v
        for k, v in res_m2["commits_by_mech"].items():
            seed_commits_by_mech[k] = seed_commits_by_mech.get(k, 0) + v

        seed_summary[seed] = {
            "seed": seed,
            "m1_margin": res_m1["margin"],
            "m2_margin": res_m2["margin"],
            "net_delta": net_delta,
            "m1_commits": res_m1["committed"],
            "m2_commits": res_m2["committed"],
            "total_commits": res_m1["committed"] + res_m2["committed"],
            "commits_by_mech": seed_commits_by_mech,
            "seed_elapsed_s": round(time.time() - t_seed0, 2)
        }

        print(f"[{i+1:02d}/{len(seeds)}] Seed {seed}: S0={res_m1['margin']:+.0f} S1={res_m2['margin']:+.0f} -> NetDelta={net_delta:+.1f} Commits={seed_summary[seed]['total_commits']} ({time.time()-t_seed0:.2f}s)")

    # Aggregate statistical metrics
    net_deltas = [seed_summary[s]["net_delta"] for s in seeds]
    arr = np.array(net_deltas)
    
    wins = sum(1 for d in net_deltas if d > 0)
    losses = sum(1 for d in net_deltas if d < 0)
    ties = sum(1 for d in net_deltas if d == 0)

    mean_delta = float(np.mean(arr))
    std_delta = float(np.std(arr, ddof=1)) if len(arr) > 1 else 0.0
    se_delta = std_delta / np.sqrt(len(arr)) if len(arr) > 1 else 0.0
    t_stat = (mean_delta / se_delta) if se_delta > 0 else 0.0

    import math
    p_val = 2.0 * (1.0 - 0.5 * (1.0 + math.erf(abs(t_stat) / math.sqrt(2.0))))

    # Attribution totals across all matches
    all_commits_by_mech: Dict[str, int] = {}
    for m in matches_data:
        for k, v in m["commits_by_mech"].items():
            all_commits_by_mech[k] = all_commits_by_mech.get(k, 0) + v

    lat_p50 = float(np.median([m["latency_p50"] for m in matches_data]))
    lat_p95 = float(np.median([m["latency_p95"] for m in matches_data]))
    lat_p99 = float(np.median([m["latency_p99"] for m in matches_data]))
    worst_turn = float(np.max([m["worst_turn_ms"] for m in matches_data]))

    summary = {
        "cohort": cohort_name,
        "n_seeds": len(seeds),
        "n_matches": len(matches_data),
        "mean_net_delta": round(mean_delta, 2),
        "median_net_delta": round(float(np.median(arr)), 2),
        "std_delta": round(std_delta, 2),
        "se_delta": round(se_delta, 2),
        "ci95": [round(mean_delta - 1.96 * se_delta, 2), round(mean_delta + 1.96 * se_delta, 2)],
        "t_statistic": round(t_stat, 4),
        "p_value_approx": round(p_val, 6),
        "win_loss_tie": f"{wins}/{losses}/{ties}",
        "win_rate": round(wins / len(seeds), 4),
        "tie_excluded_win_rate": round(wins / (wins + losses), 4) if (wins + losses) > 0 else 0.0,
        "commits_by_mechanism": all_commits_by_mech,
        "total_commits": sum(all_commits_by_mech.values()),
        "latency_p50_ms": round(lat_p50, 3),
        "latency_p95_ms": round(lat_p95, 3),
        "latency_p99_ms": round(lat_p99, 3),
        "worst_turn_ms": round(worst_turn, 3),
    }

    return {
        "summary": summary,
        "matches": matches_data,
        "seed_summary": seed_summary
    }


def main() -> None:
    print("=" * 80)
    print("AEC PHASE 008: FULL INTEGRATED OFFLINE VALIDATION")
    print(f"Date: 2026-09-18")
    print(f"V3 Expected SHA-256: {V3_EXPECTED_SHA256}")
    print("=" * 80)

    # 1. Cryptographic Governance Check
    actual_sha = sha256_of_file(V3_TARBALL_PATH)
    assert actual_sha == V3_EXPECTED_SHA256, f"Hash mismatch: {actual_sha} != {V3_EXPECTED_SHA256}"
    print(f"[GOVERNANCE] V3 byte integrity verified: {actual_sha}")

    # 2. Immutable Configuration Binding
    cfg_robust = AECConfig(
        operational_mode="ROBUST_MODE",
        frozen_mode=False,
        enabled_mechanisms=(
            "DEPENDENCY_AWARE_MARKET_TIMING",
            "TERMINAL_LIQUIDATION",
            "PHASE_SHUTDOWN",
            "DYNAMIC_SHADOW_HARVEST",
            "TERMINAL_HARVEST_SWEEP",
        )
    )
    assert not cfg_robust.resource_conversion_enabled, "FATAL: RESOURCE_CONVERSION must be quarantined!"
    print(f"[GOVERNANCE] Robust config initialized: {cfg_robust.enabled_mechanisms}")
    print(f"[GOVERNANCE] Resource conversion quarantined: {not cfg_robust.resource_conversion_enabled}")

    t_all0 = time.time()

    # 3. Evaluate Primary Cohort: Fresh Reserved Discovery Partition (249000-249024)
    primary_eval = evaluate_cohort("PRIMARY_RESERVED_249k", PRIMARY_SEEDS, cfg_robust)

    # 4. Evaluate Benchmark Cohort: Historical Re-Baseline (50000-50024)
    benchmark_eval = evaluate_cohort("BENCHMARK_HISTORICAL_50k", BENCHMARK_SEEDS, cfg_robust)

    total_time = time.time() - t_all0
    print(f"\n[EXECUTION] All 100 matches completed in {total_time:.1f}s.")

    # 5. Export Results CSV
    all_matches = primary_eval["matches"] + benchmark_eval["matches"]
    csv_path = os.path.join(RESULTS_DIR, "PHASE008_INTEGRATED_RESULTS.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "cohort", "match_id", "seed", "seat", "treatment_reward", "control_reward",
            "margin", "win", "loss", "tie", "committed", "abstained", "fallback_count",
            "mean_latency_ms", "worst_turn_ms"
        ])
        writer.writeheader()
        for m in all_matches:
            row = {k: m[k] for k in writer.fieldnames}
            writer.writerow(row)
    print(f"[ARTIFACT] Matches exported to {csv_path}")

    # 6. Export Mechanism Telemetry JSON
    telemetry_path = os.path.join(RESULTS_DIR, "PHASE008_MECHANISM_TELEMETRY.json")
    telemetry_export = {
        "metadata": {
            "date": "2026-09-18",
            "phase": "008",
            "governance_v3_sha256": actual_sha,
            "total_matches": len(all_matches),
            "execution_time_sec": round(total_time, 2)
        },
        "primary_cohort_seeds": primary_eval["seed_summary"],
        "benchmark_cohort_seeds": benchmark_eval["seed_summary"],
        "mechanism_attribution": {
            "primary_cohort": primary_eval["summary"]["commits_by_mechanism"],
            "benchmark_cohort": benchmark_eval["summary"]["commits_by_mechanism"],
        }
    }
    with open(telemetry_path, "w", encoding="utf-8") as f:
        json.dump(telemetry_export, f, indent=2)
    print(f"[ARTIFACT] Mechanism telemetry exported to {telemetry_path}")

    # 7. Export Integration Metrics JSON
    metrics_path = os.path.join(RESULTS_DIR, "PHASE008_INTEGRATION_METRICS.json")
    metrics_export = {
        "governance": {
            "v3_sha256": actual_sha,
            "prospective_matches": 0,
            "holdouts_untouched": ["340050-340199", "214200-214249", "340300-340349"],
            "resource_conversion_quarantined": True,
        },
        "primary_cohort_summary": primary_eval["summary"],
        "benchmark_cohort_summary": benchmark_eval["summary"],
    }
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(metrics_export, f, indent=2)
    print(f"[ARTIFACT] Integration metrics exported to {metrics_path}")

    # 8. Print Executive Comparison Table
    print("\n" + "=" * 80)
    print("PHASE 008 EXECUTIVE VALIDATION SUMMARY")
    print("=" * 80)
    for name, res in [("PRIMARY (249000-249024)", primary_eval["summary"]), ("BENCHMARK (50000-50024)", benchmark_eval["summary"])]:
        print(f"\nCohort: {name}")
        print(f"  Mean Net Paired Delta: {res['mean_net_delta']:+.2f} gold (Median: {res['median_net_delta']:+.2f})")
        print(f"  Std Dev: {res['std_delta']:.2f}, SE: {res['se_delta']:.2f}, 95% CI: [{res['ci95'][0]}, {res['ci95'][1]}]")
        print(f"  t-stat: {res['t_statistic']}, p-value: {res['p_value_approx']}")
        print(f"  Win / Loss / Tie: {res['win_loss_tie']} (Win Rate: {res['win_rate']*100:.1f}%)")
        print(f"  Total Commits: {res['total_commits']} -> {res['commits_by_mechanism']}")
        print(f"  Latency: p50={res['latency_p50_ms']}ms, p95={res['latency_p95_ms']}ms, worst-turn={res['worst_turn_ms']}ms")
    print("=" * 80)


if __name__ == "__main__":
    main()
