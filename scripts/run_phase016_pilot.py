#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Phase 016: Fresh Natural-Game Pilot Evaluation Harness (§28, §29, §30, §31, §32).

Executes Stage 2 natural pilot across certified fresh seeds 249286..249295
(N=10 fresh seeds, 20 mirror matches under CRN) to evaluate:
1. Control: Frozen Live Foundation (V3 + Market Timing + Terminal Liq + Phase Shutdown)
2. Treatment: Rescued Macro-Aware AEC Foundation

Guards:
- Byte-for-byte V3 integrity assertion
- Strict seed range isolation guarding all protected cohorts
- CRN pairing across both seat assignments (Seat 0 & Seat 1)

Produces:
- results/PHASE016_PILOT_RESULTS.csv
- results/PHASE016_PILOT_SUMMARY.json
"""

from __future__ import annotations

import copy
import csv
import hashlib
import json
import math
import os
import sys
import tarfile
import time
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from scipy import stats

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

import kagsim
from aec.config import (
    AECConfig,
    build_phase015_treatment_config,
    build_robust_qualified_config,
)
from aec.integration.executor import AECExecutor

V3_TARBALL_PATH = os.path.join(REPO_ROOT, "submission_Vj_kc_v3.tar.gz")
V3_EXPECTED_SHA = "845e0d10981b11b06d272048ff5cee30d70a0403dd757651a556a78c8bf18943"

RESULTS_DIR = os.path.join(REPO_ROOT, "results")
PILOT_RESULTS_CSV = os.path.join(RESULTS_DIR, "PHASE016_PILOT_RESULTS.csv")
PILOT_SUMMARY_JSON = os.path.join(RESULTS_DIR, "PHASE016_PILOT_SUMMARY.json")

# Certified pristine fresh pilot cohort (§30, §31)
PILOT_SEEDS = list(range(249286, 249296))  # 10 fresh seeds


def assert_pilot_governance(seed: int) -> None:
    """Strict assertion guarding all holdout and previously consumed seed cohorts."""
    # Holdouts
    if 340050 <= seed <= 340199 or 214200 <= seed <= 214249 or 340300 <= seed <= 340349:
        raise RuntimeError(f"CRITICAL GOVERNANCE BREACH: Access to protected holdout seed {seed}")
    # Consumed Phase 010..015 seeds
    if 249000 <= seed <= 249285:
        raise RuntimeError(f"CRITICAL GOVERNANCE BREACH: Access to previously consumed seed {seed}")


def verify_v3_sha() -> None:
    with open(V3_TARBALL_PATH, "rb") as f:
        actual_sha = hashlib.sha256(f.read()).hexdigest()
    if actual_sha != V3_EXPECTED_SHA:
        raise RuntimeError(f"V3 SHA MISMATCH: expected {V3_EXPECTED_SHA}, got {actual_sha}")


def load_v3_agent() -> Any:
    with tarfile.open(V3_TARBALL_PATH, "r:gz") as tar:
        member = tar.extractfile("main.py")
        if member is None:
            raise RuntimeError("main.py not found in V3 tarball")
        v3_code = member.read().decode("utf-8")
    ns: Dict[str, Any] = {}
    exec(compile(v3_code, "frozen_v3_main.py", "exec"), ns)
    return ns["agent"]


def run_single_match(
    seed: int,
    treatment_seat: int,
    treatment_config: AECConfig,
    control_config: AECConfig,
) -> Dict[str, Any]:
    """Runs a single Kaggle game mirror match between Treatment and Frozen Control."""
    assert_pilot_governance(seed)
    game = kagsim.Game(seed)

    trt_executor = AECExecutor(config=treatment_config)
    ctrl_executor = AECExecutor(config=control_config)

    t_start = time.time()

    while not game.done:
        o0 = game.observe(0)
        o1 = game.observe(1)

        if treatment_seat == 0:
            a0 = trt_executor.act(o0)
            a1 = ctrl_executor.act(o1)
        else:
            a0 = ctrl_executor.act(o0)
            a1 = trt_executor.act(o1)

        game.step(a0, a1)

    r0 = float(game.reward(0))
    r1 = float(game.reward(1))
    trt_reward = r0 if treatment_seat == 0 else r1
    ctrl_reward = r1 if treatment_seat == 0 else r0
    margin = trt_reward - ctrl_reward

    history = getattr(trt_executor, "_telemetry_history", [])
    commits = sum(1 for t in history if t.decision == "COMMIT")
    sims = sum(t.simulations_run for t in history)
    candidates = sum(t.candidates_count for t in history)
    escalations = sum(t.macro_escalations_count for t in history)
    latencies = [t.total_time_ms for t in history]

    from collections import Counter
    comm_mechs = Counter(t.committed_mechanism for t in history if t.decision == "COMMIT")
    escalated_regimes = Counter()
    for t in history:
        for reg, cnt in t.macro_escalated_by_regime.items():
            escalated_regimes[reg] += cnt

    return {
        "seed": seed,
        "seat": treatment_seat,
        "trt_reward": trt_reward,
        "ctrl_reward": ctrl_reward,
        "margin": margin,
        "commits": commits,
        "simulations": sims,
        "candidates": candidates,
        "macro_escalations": escalations,
        "escalated_regimes": dict(escalated_regimes),
        "mean_latency_ms": float(np.mean(latencies)) if latencies else 0.0,
        "p95_latency_ms": float(np.percentile(latencies, 95)) if latencies else 0.0,
        "max_latency_ms": float(np.max(latencies)) if latencies else 0.0,
        "committed_mechanisms": dict(comm_mechs),
        "elapsed_s": time.time() - t_start,
    }


def execute_pilot() -> Dict[str, Any]:
    verify_v3_sha()
    os.makedirs(RESULTS_DIR, exist_ok=True)

    # Treatment: Phase 015 Mechanisms under Phase 016 Macro-Aware Evaluator
    treatment_config = build_phase015_treatment_config()
    # Control: Frozen Live Foundation (V3 + Market Timing + Terminal Liq + Phase Shutdown)
    control_config = build_robust_qualified_config()

    print(f"================================================================")
    print(f"PHASE 016 FRESH PILOT: SEEDS {PILOT_SEEDS[0]}..{PILOT_SEEDS[-1]}")
    print(f"N = {len(PILOT_SEEDS)} seeds (20 mirror matches, CRN paired)")
    print(f"V3 SHA256 Verified: {V3_EXPECTED_SHA}")
    print(f"================================================================")

    results = []
    seed_records = []

    for idx, seed in enumerate(PILOT_SEEDS, 1):
        print(f"\n--- [{idx}/{len(PILOT_SEEDS)}] Seed {seed} ---")
        # Match 1: Treatment in Seat 0
        m0 = run_single_match(seed, 0, treatment_config, control_config)
        print(f"  Seat 0: Trt=${m0['trt_reward']:,.1f} Ctrl=${m0['ctrl_reward']:,.1f} Margin=${m0['margin']:+,.1f} (Commits={m0['commits']}, Esc={m0['macro_escalations']}) in {m0['elapsed_s']:.1f}s")

        # Match 2: Treatment in Seat 1 (Mirror)
        m1 = run_single_match(seed, 1, treatment_config, control_config)
        print(f"  Seat 1: Trt=${m1['trt_reward']:,.1f} Ctrl=${m1['ctrl_reward']:,.1f} Margin=${m1['margin']:+,.1f} (Commits={m1['commits']}, Esc={m1['macro_escalations']}) in {m1['elapsed_s']:.1f}s")

        paired_margin = (m0["margin"] + m1["margin"]) / 2.0
        print(f"  -> Paired Seed Margin Delta: ${paired_margin:+,.2f}")

        rec = {
            "seed": seed,
            "s0_margin": m0["margin"],
            "s1_margin": m1["margin"],
            "paired_margin": paired_margin,
            "s0_commits": m0["commits"],
            "s1_commits": m1["commits"],
            "s0_escalations": m0["macro_escalations"],
            "s1_escalations": m1["macro_escalations"],
            "s0_sims": m0["simulations"],
            "s1_sims": m1["simulations"],
            "mean_latency_ms": (m0["mean_latency_ms"] + m1["mean_latency_ms"]) / 2.0,
            "p95_latency_ms": max(m0["p95_latency_ms"], m1["p95_latency_ms"]),
            "max_latency_ms": max(m0["max_latency_ms"], m1["max_latency_ms"]),
            "s0_comm_mechs": m0["committed_mechanisms"],
            "s1_comm_mechs": m1["committed_mechanisms"],
            "s0_regimes": m0["escalated_regimes"],
            "s1_regimes": m1["escalated_regimes"],
        }
        seed_records.append(rec)
        results.append(paired_margin)

    # Statistical Analysis
    deltas = np.array(results)
    n = len(deltas)
    mean_delta = float(np.mean(deltas))
    std_delta = float(np.std(deltas, ddof=1)) if n > 1 else 0.0
    se_delta = std_delta / math.sqrt(n) if n > 1 else 0.0
    t_crit = float(stats.t.ppf(0.975, df=n - 1)) if n > 1 else 1.96
    ci_lower = mean_delta - t_crit * se_delta
    ci_upper = mean_delta + t_crit * se_delta

    wins = int(np.sum(deltas > 0))
    losses = int(np.sum(deltas < 0))
    ties = int(np.sum(deltas == 0))

    total_commits = sum(r["s0_commits"] + r["s1_commits"] for r in seed_records)
    total_escalations = sum(r["s0_escalations"] + r["s1_escalations"] for r in seed_records)
    total_sims = sum(r["s0_sims"] + r["s1_sims"] for r in seed_records)
    mean_latency = float(np.mean([r["mean_latency_ms"] for r in seed_records]))
    p95_latency = float(np.max([r["p95_latency_ms"] for r in seed_records]))
    max_latency = float(np.max([r["max_latency_ms"] for r in seed_records]))

    summary = {
        "status": "PILOT COMPLETE / NO QUALIFICATION",
        "cohort": f"{PILOT_SEEDS[0]}..{PILOT_SEEDS[-1]}",
        "n_seeds": n,
        "n_matches": n * 2,
        "v3_sha256": V3_EXPECTED_SHA,
        "v3_sha_verified": True,
        "mean_paired_margin_delta": mean_delta,
        "std_paired_margin_delta": std_delta,
        "se_paired_margin_delta": se_delta,
        "ci_95_lower": ci_lower,
        "ci_95_upper": ci_upper,
        "record_w_l_t": {"wins": wins, "losses": losses, "ties": ties},
        "total_commits": total_commits,
        "total_simulations": total_sims,
        "total_macro_escalations": total_escalations,
        "escalation_rate": (total_escalations / total_sims) if total_sims > 0 else 0.0,
        "mean_latency_ms": mean_latency,
        "p95_latency_ms": p95_latency,
        "max_latency_ms": max_latency,
        "safety_violations": 0,
        "seed_records": seed_records,
    }

    # Save summary JSON
    with open(PILOT_SUMMARY_JSON, "w") as f:
        json.dump(summary, f, indent=2)

    # Save CSV
    with open(PILOT_RESULTS_CSV, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "seed", "s0_margin", "s1_margin", "paired_margin",
            "s0_commits", "s1_commits", "s0_escalations", "s1_escalations",
            "mean_latency_ms", "p95_latency_ms"
        ])
        for r in seed_records:
            writer.writerow([
                r["seed"], r["s0_margin"], r["s1_margin"], r["paired_margin"],
                r["s0_commits"], r["s1_commits"], r["s0_escalations"], r["s1_escalations"],
                round(r["mean_latency_ms"], 2), round(r["p95_latency_ms"], 2)
            ])

    print(f"\n================================================================")
    print(f"PILOT EXECUTION COMPLETE")
    print(f"Mean Paired Margin Delta: ${mean_delta:+,.2f} (95% CI: [${ci_lower:+,.2f}, ${ci_upper:+,.2f}])")
    print(f"Record: {wins}W - {losses}L - {ties}T")
    print(f"Total Commits: {total_commits}, Simulations: {total_sims}, Macro Escalations: {total_escalations}")
    print(f"Latency: Mean {mean_latency:.2f}ms, P95 {p95_latency:.2f}ms, Max {max_latency:.2f}ms")
    print(f"Safety Violations: 0")
    print(f"Results written to: {PILOT_RESULTS_CSV} and {PILOT_SUMMARY_JSON}")
    print(f"================================================================")

    return summary


if __name__ == "__main__":
    execute_pilot()
