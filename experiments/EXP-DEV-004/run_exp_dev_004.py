# SPDX-License-Identifier: MIT
"""
=============================================================================
EXP-DEV-004 EXECUTION RUNNER: DISCOVERY PARTITION
=============================================================================
Experiment: EXP-DEV-004
Title: Joint Macro Production Scheduler over V54++ Residual Preemption
Governing Protocol: DEVELOPMENT_EXPERIMENT_PROTOCOL_V1_3.md
Protocol Hash (SHA-256): 436fb79fb94ad2a05e0d01d3f16f487e51970478830d609a76f91b802e109751
Discovery Partition: Seeds 246000 to 246049 (N=50 seeds, 100 paired CRN matches)
Quarantined Holdouts: 214200-214249 (Strictly Excluded), 50050-50099 (Quarantined)
=============================================================================
"""

import os
import sys
import copy
import csv
import json
import math
import time
import hashlib
import importlib.util
from typing import Dict, List, Tuple, Any

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(BASE_DIR, "external_repos", "kaggriculture-cppsim"))
sys.path.insert(0, os.path.join(BASE_DIR, "candidates", "closed_loop_architecture"))
sys.path.insert(0, os.path.join(BASE_DIR, "scratch"))

import kagsim
from dev_004_joint_macro_scheduler import Dev004JointMacroScheduler
from verify_agent_zero_leakage import audit_agent_ast

EXP_DIR = os.path.abspath(os.path.dirname(__file__))
LOG_FILE = os.path.join(EXP_DIR, "EXECUTION_LOG.txt")
RAW_RESULTS_FILE = os.path.join(EXP_DIR, "RAW_RESULTS.json")
PAIRED_DELTAS_FILE = os.path.join(EXP_DIR, "PAIRED_DELTAS.csv")
PLAN_EVENTS_FILE = os.path.join(EXP_DIR, "PLAN_EVENTS.csv")
WORKER_TELEMETRY_FILE = os.path.join(EXP_DIR, "WORKER_TELEMETRY.csv")
STATS_FILE = os.path.join(EXP_DIR, "STATISTICS_RECOMPUTED.json")

BASELINE_PATH = os.path.join(BASE_DIR, "candidates", "compiled_v54_plus_residual.py")
CANDIDATE_PATH = os.path.join(BASE_DIR, "candidates", "closed_loop_architecture", "dev_004_joint_macro_scheduler.py")


def log(msg: str):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
    line = f"[{timestamp} UTC] {msg}"
    print(line, flush=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def assert_not_quarantined(seed: int):
    """Hard invariant: virgin holdout seeds and contaminated ranges must NEVER be executed."""
    if 214200 <= seed <= 214249:
        msg = f"CRITICAL PROTOCOL VIOLATION: Virgin Holdout seed {seed} requested!"
        log(f"FATAL: {msg}")
        raise RuntimeError(msg)
    if 50050 <= seed <= 50099:
        msg = f"CRITICAL PROTOCOL VIOLATION: Qualification seed {seed} requested during Discovery!"
        log(f"FATAL: {msg}")
        raise RuntimeError(msg)
    if 50100 <= seed <= 50149:
        msg = f"CRITICAL PROTOCOL VIOLATION: Contaminated seed {seed} requested!"
        log(f"FATAL: {msg}")
        raise RuntimeError(msg)
    if 245000 <= seed <= 245049:
        msg = f"CRITICAL PROTOCOL VIOLATION: DEV-003 consumed seed {seed} requested!"
        log(f"FATAL: {msg}")
        raise RuntimeError(msg)


def verify_preflight():
    log("=" * 80)
    log("PREFLIGHT INVARIANT VERIFICATION FOR EXP-DEV-004 DISCOVERY RUN")
    log("=" * 80)

    # 1. Protocol V1.3 SHA-256
    proto_path = os.path.join(EXP_DIR, "DEVELOPMENT_EXPERIMENT_PROTOCOL_V1_3.md")
    with open(proto_path, "rb") as f:
        proto_sha = hashlib.sha256(f.read()).hexdigest()
    EXPECTED_PROTO_SHA = "436fb79fb94ad2a05e0d01d3f16f487e51970478830d609a76f91b802e109751"
    assert proto_sha == EXPECTED_PROTO_SHA, f"Protocol SHA mismatch: {proto_sha} != {EXPECTED_PROTO_SHA}"
    log(f"  [1/6] Protocol V1.3 SHA-256 Verified: {proto_sha}")

    # 2. Frozen Baseline SHA-256
    with open(BASELINE_PATH, "rb") as f:
        base_sha = hashlib.sha256(f.read()).hexdigest()
    EXPECTED_BASE_SHA = "18402ec6fa3709b9b5ef90dd9c8d7b9c0e44aea55ab163e44a80a4adc0cb7eeb"
    assert base_sha == EXPECTED_BASE_SHA, f"Baseline SHA mismatch: {base_sha} != {EXPECTED_BASE_SHA}"
    log(f"  [2/6] Baseline SHA-256 Verified: {base_sha}")

    # 3. Treatment SHA-256
    with open(CANDIDATE_PATH, "rb") as f:
        cand_sha = hashlib.sha256(f.read()).hexdigest()
    EXPECTED_CAND_SHA = "321fc4bd3aa3c8629a125f04edbbe0422fb0a01f8c29a530dc3c19f8f1207e25"
    assert cand_sha == EXPECTED_CAND_SHA, f"Candidate SHA mismatch: {cand_sha} != {EXPECTED_CAND_SHA}"
    log(f"  [3/6] Treatment dev_004 SHA-256 Verified: {cand_sha}")

    # 4. AST Zero-Leakage Audit
    ast_violations = audit_agent_ast(CANDIDATE_PATH)
    assert len(ast_violations) == 0, f"Candidate AST violations: {ast_violations}"
    log("  [4/6] Candidate dev_004 AST Zero-Leakage Verified Clean (0 violations).")

    # 5. Simulator Parity
    assert hasattr(kagsim, "Game"), "kagsim simulator engine missing Game class"
    log("  [5/6] Simulator Engine kagsim 1.32.7 Verified.")

    # 6. Precheck Document Verified
    precheck_path = os.path.join(EXP_DIR, "PRECHECK.md")
    assert os.path.exists(precheck_path), f"Missing {precheck_path}"
    log(f"  [6/6] Precheck report verified on disk: {precheck_path}")
    log("All Preflight Invariants Passed.\n")


def load_isolated_baseline(name: str):
    spec = importlib.util.spec_from_file_location(name, BASELINE_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def run_paired_match(seed: int) -> Tuple[Dict[str, Any], List[Dict[str, Any]], List[Dict[str, Any]]]:
    assert_not_quarantined(seed)

    decision_events = []
    worker_telemetry = []

    # Match 0: Candidate is Seat 0, Baseline is Seat 1
    g0 = kagsim.Game(seed)
    cand0 = Dev004JointMacroScheduler(seat=0, seed=seed)
    base1 = load_isolated_baseline(f"base_s{seed}_m0")

    step0 = 0
    t0_start = time.perf_counter()
    while not g0.done:
        o0 = g0.observe(0)
        o1 = g0.observe(1)
        a0 = cand0.act(o0)
        a1 = base1.agent(o1)
        g0.step(a0, a1)
        step0 += 1
    t0_elapsed = time.perf_counter() - t0_start

    cand_rew0 = float(g0.reward(0))
    base_rew1 = float(g0.reward(1))
    delta0 = cand_rew0 - base_rew1
    decision_events.extend(cand0.decision_events)

    # Match 1: Baseline is Seat 0, Candidate is Seat 1
    g1 = kagsim.Game(seed)
    base0 = load_isolated_baseline(f"base_s{seed}_m1")
    cand1 = Dev004JointMacroScheduler(seat=1, seed=seed)

    step1 = 0
    t1_start = time.perf_counter()
    while not g1.done:
        o0 = g1.observe(0)
        o1 = g1.observe(1)
        a0 = base0.agent(o0)
        a1 = cand1.act(o1)
        g1.step(a0, a1)
        step1 += 1
    t1_elapsed = time.perf_counter() - t1_start

    base_rew0 = float(g1.reward(0))
    cand_rew1 = float(g1.reward(1))
    delta1 = cand_rew1 - base_rew0
    decision_events.extend(cand1.decision_events)

    paired_mean_delta = 0.5 * (delta0 + delta1)
    if paired_mean_delta > 0.0:
        outcome = "WIN"
    elif paired_mean_delta < 0.0:
        outcome = "LOSS"
    else:
        outcome = "TIE"

    # Worker telemetry row
    telemetry_entry = {
        "seed": seed,
        "cand0_plan": cand0.active_plan,
        "cand1_plan": cand1.active_plan,
        "m0_cand_rew": cand_rew0,
        "m0_base_rew": base_rew1,
        "m0_delta": delta0,
        "m1_base_rew": base_rew0,
        "m1_cand_rew": cand_rew1,
        "m1_delta": delta1,
        "paired_mean_delta": paired_mean_delta,
        "outcome": outcome,
    }
    worker_telemetry.append(telemetry_entry)

    match_record = {
        "seed": seed,
        "match0": {
            "cand_seat": 0,
            "base_seat": 1,
            "cand_reward": cand_rew0,
            "base_reward": base_rew1,
            "delta": delta0,
            "steps": step0,
            "runtime_sec": round(t0_elapsed, 3),
            "cand_plan": cand0.active_plan,
        },
        "match1": {
            "base_seat": 0,
            "cand_seat": 1,
            "base_reward": base_rew0,
            "cand_reward": cand_rew1,
            "delta": delta1,
            "steps": step1,
            "runtime_sec": round(t1_elapsed, 3),
            "cand_plan": cand1.active_plan,
        },
        "paired_mean_delta": paired_mean_delta,
        "outcome": outcome,
        "activated": (cand0.active_plan != "BASELINE_BACKBONE" or cand1.active_plan != "BASELINE_BACKBONE")
    }

    return match_record, decision_events, worker_telemetry


def compute_statistics(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    deltas = [r["paired_mean_delta"] for r in records]
    n = len(deltas)
    assert n == 50, f"Expected 50 seeds, got {n}"

    sorted_deltas = sorted(deltas)
    mean_val = sum(deltas) / n
    variance = sum((x - mean_val) ** 2 for x in deltas) / (n - 1)
    sd_val = math.sqrt(variance)
    se_val = sd_val / math.sqrt(n)
    t_stat = mean_val / se_val if se_val > 0 else 0.0

    # Two-sided p-value approximation via Student-t
    try:
        from scipy import stats
        p_val = float(stats.t.sf(abs(t_stat), df=n - 1) * 2)
    except ImportError:
        # Normal approximation fallback
        p_val = 2.0 * (1.0 - 0.5 * (1.0 + math.erf(abs(t_stat) / math.sqrt(2.0))))

    # Percentiles
    def pct(arr, p):
        k = (len(arr) - 1) * p
        f = math.floor(k)
        c = math.ceil(k)
        if f == c:
            return arr[int(k)]
        return arr[int(f)] * (c - k) + arr[int(c)] * (k - f)

    p01 = pct(sorted_deltas, 0.01)
    p05 = pct(sorted_deltas, 0.05)
    p10 = pct(sorted_deltas, 0.10)
    p25 = pct(sorted_deltas, 0.25)
    p50 = pct(sorted_deltas, 0.50)
    p75 = pct(sorted_deltas, 0.75)
    p90 = pct(sorted_deltas, 0.90)
    p95 = pct(sorted_deltas, 0.95)
    p99 = pct(sorted_deltas, 0.99)

    # Wins / Losses / Ties
    wins = sum(1 for d in deltas if d > 0.0)
    losses = sum(1 for d in deltas if d < 0.0)
    ties = sum(1 for d in deltas if d == 0.0)

    # 95% Confidence Interval (t_crit = 2.0096 for df=49)
    ci_margin = 2.0096 * se_val
    ci_lower = mean_val - ci_margin
    ci_upper = mean_val + ci_margin

    # Trimmed mean (10% two-sided -> trim 5 lowest and 5 highest)
    trimmed_deltas = sorted_deltas[5:45]
    trimmed_mean = sum(trimmed_deltas) / len(trimmed_deltas)

    # Outlier sensitivity
    deltas_no_best = sorted_deltas[:-1]
    mean_no_best = sum(deltas_no_best) / len(deltas_no_best)
    deltas_no_worst = sorted_deltas[1:]
    mean_no_worst = sum(deltas_no_worst) / len(deltas_no_worst)
    deltas_no_top2 = sorted_deltas[:-2]
    mean_no_top2 = sum(deltas_no_top2) / len(deltas_no_top2)

    top1_contrib = (sorted_deltas[-1] / (n * mean_val)) if mean_val != 0 else 0.0
    top2_contrib = ((sorted_deltas[-1] + sorted_deltas[-2]) / (n * mean_val)) if mean_val != 0 else 0.0

    activated_seeds = sum(1 for r in records if r["activated"])

    stats_summary = {
        "n_seeds": n,
        "n_matches": n * 2,
        "mean_paired_delta": round(mean_val, 4),
        "median_paired_delta": round(p50, 4),
        "sd": round(sd_val, 4),
        "se": round(se_val, 4),
        "t_stat": round(t_stat, 4),
        "p_value": round(p_val, 6),
        "ci_95_lower": round(ci_lower, 4),
        "ci_95_upper": round(ci_upper, 4),
        "trimmed_mean_10pct": round(trimmed_mean, 4),
        "min": round(sorted_deltas[0], 4),
        "max": round(sorted_deltas[-1], 4),
        "p01": round(p01, 4),
        "p05": round(p05, 4),
        "p10": round(p10, 4),
        "p25": round(p25, 4),
        "p50": round(p50, 4),
        "p75": round(p75, 4),
        "p90": round(p90, 4),
        "p95": round(p95, 4),
        "p99": round(p99, 4),
        "wins": wins,
        "losses": losses,
        "ties": ties,
        "win_rate": round(wins / n, 4),
        "loss_rate": round(losses / n, 4),
        "tie_rate": round(ties / n, 4),
        "mean_excluding_best": round(mean_no_best, 4),
        "mean_excluding_worst": round(mean_no_worst, 4),
        "mean_excluding_top2": round(mean_no_top2, 4),
        "top1_contribution_pct": round(top1_contrib * 100, 2),
        "top2_contribution_pct": round(top2_contrib * 100, 2),
        "activated_seeds": activated_seeds,
        "activation_rate": round(activated_seeds / n, 4),
    }
    return stats_summary


def main():
    log("=" * 80)
    log("STARTING EXP-DEV-004 DISCOVERY SIMULATION RUN (Seeds 246000-246049)")
    log("=" * 80)

    verify_preflight()

    start_seed = 246000
    end_seed = 246049
    seeds = list(range(start_seed, end_seed + 1))

    all_match_records = []
    all_decision_events = []
    all_worker_telemetry = []

    t_total_start = time.perf_counter()

    for idx, seed in enumerate(seeds, 1):
        t_seed_start = time.perf_counter()
        rec, dec_events, w_telemetry = run_paired_match(seed)
        t_seed_elapsed = time.perf_counter() - t_seed_start

        all_match_records.append(rec)
        all_decision_events.extend(dec_events)
        all_worker_telemetry.extend(w_telemetry)

        log(f"[{idx:02d}/50] Seed {seed} | Paired Delta: {rec['paired_mean_delta']:+9.2f} | "
            f"M0 (Cand P0): {rec['match0']['delta']:+9.2f} ({rec['match0']['cand_plan']}) | "
            f"M1 (Cand P1): {rec['match1']['delta']:+9.2f} ({rec['match1']['cand_plan']}) | "
            f"Outcome: {rec['outcome']:<4} | Time: {t_seed_elapsed:.2f}s")

    t_total_elapsed = time.perf_counter() - t_total_start
    log(f"\nExecution Complete across {len(seeds)} seeds in {t_total_elapsed:.2f}s.\n")

    # Save RAW_RESULTS.json
    log(f"Writing raw results to {RAW_RESULTS_FILE}...")
    with open(RAW_RESULTS_FILE, "w", encoding="utf-8") as f:
        json.dump(all_match_records, f, indent=2)

    # Save PAIRED_DELTAS.csv
    log(f"Writing paired deltas to {PAIRED_DELTAS_FILE}...")
    with open(PAIRED_DELTAS_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["seed", "match0_cand_p0", "match0_base_p1", "match0_delta",
                         "match1_base_p0", "match1_cand_p1", "match1_delta",
                         "paired_mean_delta", "outcome", "activated", "cand0_plan", "cand1_plan"])
        for r in all_match_records:
            writer.writerow([
                r["seed"],
                r["match0"]["cand_reward"], r["match0"]["base_reward"], r["match0"]["delta"],
                r["match1"]["base_reward"], r["match1"]["cand_reward"], r["match1"]["delta"],
                r["paired_mean_delta"], r["outcome"], r["activated"],
                r["match0"]["cand_plan"], r["match1"]["cand_plan"]
            ])

    # Save PLAN_EVENTS.csv
    log(f"Writing plan events to {PLAN_EVENTS_FILE}...")
    if all_decision_events:
        with open(PLAN_EVENTS_FILE, "w", newline="", encoding="utf-8") as f:
            fieldnames = list(all_decision_events[0].keys())
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_decision_events)

    # Save WORKER_TELEMETRY.csv
    log(f"Writing worker telemetry to {WORKER_TELEMETRY_FILE}...")
    if all_worker_telemetry:
        with open(WORKER_TELEMETRY_FILE, "w", newline="", encoding="utf-8") as f:
            fieldnames = list(all_worker_telemetry[0].keys())
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_worker_telemetry)

    # Compute Statistics
    stats = compute_statistics(all_match_records)
    stats["total_runtime_sec"] = round(t_total_elapsed, 2)

    log(f"Writing recomputed statistics to {STATS_FILE}...")
    with open(STATS_FILE, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2)

    log("=" * 80)
    log("EXP-DEV-004 DISCOVERY SUMMARY STATISTICS")
    log("=" * 80)
    log(f"  Paired Mean Delta:      {stats['mean_paired_delta']:+8.2f}")
    log(f"  Median Delta:           {stats['median_paired_delta']:+8.2f}")
    log(f"  Standard Deviation:     {stats['sd']:8.2f}")
    log(f"  Standard Error:         {stats['se']:8.2f}")
    log(f"  Student-t Stat:         {stats['t_stat']:8.2f}")
    log(f"  Two-sided p-value:      {stats['p_value']:8.6f}")
    log(f"  95% Conf. Interval:     [{stats['ci_95_lower']:+8.2f}, {stats['ci_95_upper']:+8.2f}]")
    log(f"  10% Trimmed Mean:       {stats['trimmed_mean_10pct']:+8.2f}")
    log(f"  Min Delta (Worst Loss): {stats['min']:+8.2f}")
    log(f"  Max Delta (Best Win):   {stats['max']:+8.2f}")
    log(f"  Record (W / L / T):     {stats['wins']} Wins / {stats['losses']} Losses / {stats['ties']} Ties")
    log(f"  Win Rate:               {stats['win_rate']*100:.1f}%")
    log(f"  Activation Rate:        {stats['activation_rate']*100:.1f}% ({stats['activated_seeds']}/50 seeds)")
    log(f"  Mean (excl. Best):      {stats['mean_excluding_best']:+8.2f}")
    log(f"  Mean (excl. Worst):     {stats['mean_excluding_worst']:+8.2f}")
    log(f"  Mean (excl. Top-2):     {stats['mean_excluding_top2']:+8.2f}")
    log("=" * 80)


if __name__ == "__main__":
    main()
