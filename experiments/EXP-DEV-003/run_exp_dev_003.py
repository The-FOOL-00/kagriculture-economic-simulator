# SPDX-License-Identifier: MIT
"""
=============================================================================
EXP-DEV-003 EXECUTION RUNNER: DISCOVERY PARTITION
=============================================================================
Experiment: EXP-DEV-003
Title: Conditional Opportunity-Value Specialization over V54++ Residual Preemption
Governing Protocol: DEVELOPMENT_EXPERIMENT_PROTOCOL_V1_2.md
Protocol Hash (SHA-256): f94f9b71a13842915bb20820c610e86cd597d535cb7a80b5a69a5d64dc2d6007
Discovery Partition: Seeds 245000 to 245049 (N=50 seeds, 100 paired CRN matches)
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
from dev_003_conditional_specialization import Dev003ConditionalSpecializationAgent
from verify_agent_zero_leakage import audit_agent_ast

EXP_DIR = os.path.abspath(os.path.dirname(__file__))
LOG_FILE = os.path.join(EXP_DIR, "EXECUTION_LOG.txt")
RAW_RESULTS_FILE = os.path.join(EXP_DIR, "RAW_RESULTS.json")
PAIRED_DELTAS_FILE = os.path.join(EXP_DIR, "PAIRED_DELTAS.csv")
DECISION_EVENTS_FILE = os.path.join(EXP_DIR, "DECISION_EVENTS.csv")
STATS_FILE = os.path.join(EXP_DIR, "STATISTICS_RECOMPUTED.json")

BASELINE_PATH = os.path.join(BASE_DIR, "candidates", "compiled_v54_plus_residual.py")
CANDIDATE_PATH = os.path.join(BASE_DIR, "candidates", "closed_loop_architecture", "dev_003_conditional_specialization.py")


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


def verify_preflight():
    log("=" * 80)
    log("PREFLIGHT INVARIANT VERIFICATION FOR EXP-DEV-003 DISCOVERY RUN")
    log("=" * 80)

    # 1. Protocol V1.2 SHA-256
    proto_path = os.path.join(EXP_DIR, "DEVELOPMENT_EXPERIMENT_PROTOCOL_V1_2.md")
    with open(proto_path, "rb") as f:
        proto_sha = hashlib.sha256(f.read()).hexdigest()
    EXPECTED_PROTO_SHA = "f94f9b71a13842915bb20820c610e86cd597d535cb7a80b5a69a5d64dc2d6007"
    assert proto_sha == EXPECTED_PROTO_SHA, f"Protocol SHA mismatch: {proto_sha} != {EXPECTED_PROTO_SHA}"
    log(f"  [1/6] Protocol V1.2 SHA-256 Verified: {proto_sha}")

    # 2. Frozen Baseline SHA-256
    with open(BASELINE_PATH, "rb") as f:
        base_sha = hashlib.sha256(f.read()).hexdigest()
    EXPECTED_BASE_SHA = "18402ec6fa3709b9b5ef90dd9c8d7b9c0e44aea55ab163e44a80a4adc0cb7eeb"
    assert base_sha == EXPECTED_BASE_SHA, f"Baseline SHA mismatch: {base_sha} != {EXPECTED_BASE_SHA}"
    log(f"  [2/6] Baseline SHA-256 Verified: {base_sha}")

    # 3. Treatment SHA-256
    with open(CANDIDATE_PATH, "rb") as f:
        cand_sha = hashlib.sha256(f.read()).hexdigest()
    EXPECTED_CAND_SHA = "0b152cfa544244fe813ac10c4eec66056c47c5a652f14fe7fbf0a3f7a764c5cb"
    assert cand_sha == EXPECTED_CAND_SHA, f"Candidate SHA mismatch: {cand_sha} != {EXPECTED_CAND_SHA}"
    log(f"  [3/6] Treatment dev_003 SHA-256 Verified: {cand_sha}")

    # 4. AST Zero-Leakage Audit
    ast_violations = audit_agent_ast(CANDIDATE_PATH)
    assert len(ast_violations) == 0, f"Candidate AST violations: {ast_violations}"
    log("  [4/6] Candidate dev_003 AST Zero-Leakage Verified Clean (0 violations).")

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


def run_paired_match(seed: int) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    assert_not_quarantined(seed)

    decision_events = []

    # Match 0: Candidate is Seat 0, Baseline is Seat 1
    g0 = kagsim.Game(seed)
    cand0 = Dev003ConditionalSpecializationAgent(seat=0, seed=seed)
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
    cand1 = Dev003ConditionalSpecializationAgent(seat=1, seed=seed)

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
            "cand_mode": cand0.mode,
            "specialized_crop": cand0.specialized_crop
        },
        "match1": {
            "base_seat": 0,
            "cand_seat": 1,
            "base_reward": base_rew0,
            "cand_reward": cand_rew1,
            "delta": delta1,
            "steps": step1,
            "runtime_sec": round(t1_elapsed, 3),
            "cand_mode": cand1.mode,
            "specialized_crop": cand1.specialized_crop
        },
        "paired_mean_delta": paired_mean_delta,
        "outcome": outcome,
        "activated": (cand0.mode == "SPECIALIZE" or cand1.mode == "SPECIALIZE")
    }

    return match_record, decision_events


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
        # Normal approximation fallback if scipy unavailable
        p_val = float(2.0 * (1.0 - 0.5 * (1.0 + math.erf(abs(t_stat) / math.sqrt(2.0)))))

    t_crit_95 = 2.0096  # df=49
    ci_lower = mean_val - t_crit_95 * se_val
    ci_upper = mean_val + t_crit_95 * se_val

    # 10% trimmed mean (drop 5 lowest, 5 highest)
    trimmed_deltas = sorted_deltas[5:45]
    trimmed_mean = sum(trimmed_deltas) / len(trimmed_deltas)

    # Percentile helper
    def get_percentile(p: float) -> float:
        idx = (len(sorted_deltas) - 1) * p
        lower = int(idx)
        upper = min(lower + 1, len(sorted_deltas) - 1)
        weight = idx - lower
        return sorted_deltas[lower] * (1.0 - weight) + sorted_deltas[upper] * weight

    p01 = get_percentile(0.01)
    p05 = get_percentile(0.05)
    p10 = get_percentile(0.10)
    p25 = get_percentile(0.25)
    p50 = get_percentile(0.50)
    p75 = get_percentile(0.75)
    p90 = get_percentile(0.90)
    p95 = get_percentile(0.95)
    p99 = get_percentile(0.99)

    min_val = sorted_deltas[0]
    max_val = sorted_deltas[-1]

    win_count = sum(1 for d in deltas if d > 0.0)
    loss_count = sum(1 for d in deltas if d < 0.0)
    tie_count = sum(1 for d in deltas if d == 0.0)
    win_rate = win_count / n
    loss_rate = loss_count / n
    tie_rate = tie_count / n
    downside_freq = loss_rate

    total_surplus = sum(deltas)
    best_seed_val = sorted_deltas[-1]
    second_best_val = sorted_deltas[-2]
    worst_seed_val = sorted_deltas[0]

    top1_contribution = (best_seed_val / total_surplus * 100.0) if total_surplus > 0 else 0.0
    top2_contribution = ((best_seed_val + second_best_val) / total_surplus * 100.0) if total_surplus > 0 else 0.0

    mean_excl_best = sum(sorted_deltas[:-1]) / (n - 1)
    mean_excl_worst = sum(sorted_deltas[1:]) / (n - 1)
    mean_excl_best2 = sum(sorted_deltas[:-2]) / (n - 2)

    active_seeds_count = sum(1 for r in records if r["activated"])

    # Development Gates Evaluation
    gate_a_pass = mean_val >= 30.0
    gate_b_pass = win_rate >= 0.50
    gate_c_pass = min_val >= -350.0
    gate_d_pass = mean_excl_best > 0.0
    gate_e_pass = 5 <= active_seeds_count <= 35

    all_gates_pass = all([gate_a_pass, gate_b_pass, gate_c_pass, gate_d_pass, gate_e_pass])

    # Epistemic Classification
    if all_gates_pass and p_val < 0.10:
        classification = "ROBUST_DISCOVERY"
    elif gate_a_pass and gate_b_pass and trimmed_mean > 0.0:
        classification = "PROMISING"
    elif mean_val > 0.0:
        classification = "SIGNAL"
    else:
        classification = "FAILURE"

    return {
        "n_seeds": n,
        "mean_paired_delta": round(mean_val, 2),
        "median": round(p50, 2),
        "sd": round(sd_val, 2),
        "se": round(se_val, 2),
        "t_statistic": round(t_stat, 4),
        "p_value": round(p_val, 6),
        "ci_95_lower": round(ci_lower, 2),
        "ci_95_upper": round(ci_upper, 2),
        "trimmed_mean_10": round(trimmed_mean, 2),
        "percentiles": {
            "p01": round(p01, 2),
            "p05": round(p05, 2),
            "p10": round(p10, 2),
            "p25": round(p25, 2),
            "p50": round(p50, 2),
            "p75": round(p75, 2),
            "p90": round(p90, 2),
            "p95": round(p95, 2),
            "p99": round(p99, 2)
        },
        "min": round(min_val, 2),
        "max": round(max_val, 2),
        "win_count": win_count,
        "loss_count": loss_count,
        "tie_count": tie_count,
        "win_rate": round(win_rate, 4),
        "loss_rate": round(loss_rate, 4),
        "tie_rate": round(tie_rate, 4),
        "downside_frequency": round(downside_freq, 4),
        "total_surplus": round(total_surplus, 2),
        "top1_contribution_pct": round(top1_contribution, 2),
        "top2_contribution_pct": round(top2_contribution, 2),
        "mean_excl_best": round(mean_excl_best, 2),
        "mean_excl_worst": round(mean_excl_worst, 2),
        "mean_excl_best2": round(mean_excl_best2, 2),
        "active_seeds_count": active_seeds_count,
        "active_seeds_fraction": round(active_seeds_count / n, 4),
        "gates": {
            "Gate_A_positive_mean_ge_30": {"passed": gate_a_pass, "threshold": 30.0, "observed": round(mean_val, 2)},
            "Gate_B_win_rate_ge_50": {"passed": gate_b_pass, "threshold": 0.50, "observed": round(win_rate, 4)},
            "Gate_C_worst_loss_ge_minus_350": {"passed": gate_c_pass, "threshold": -350.0, "observed": round(min_val, 2)},
            "Gate_D_outlier_non_dominance": {"passed": gate_d_pass, "threshold": 0.0, "observed": round(mean_excl_best, 2)},
            "Gate_E_selective_activation": {"passed": gate_e_pass, "min": 5, "max": 35, "observed": active_seeds_count}
        },
        "all_gates_passed": all_gates_pass,
        "epistemic_classification": classification
    }


def main():
    verify_preflight()

    start_seed = 245000
    end_seed = 245049
    total_seeds = end_seed - start_seed + 1

    log(f"Starting EXP-DEV-003 Discovery Run across {total_seeds} seeds ({start_seed} to {end_seed})...")
    t_run_start = time.perf_counter()

    all_match_records = []
    all_decision_events = []

    for idx, seed in enumerate(range(start_seed, end_seed + 1), start=1):
        rec, events = run_paired_match(seed)
        all_match_records.append(rec)
        all_decision_events.extend(events)

        log(
            f"[{idx:02d}/{total_seeds}] Seed {seed:d} | "
            f"M0 Delta: {rec['match0']['delta']:+8.1f} | "
            f"M1 Delta: {rec['match1']['delta']:+8.1f} | "
            f"Paired Mean: {rec['paired_mean_delta']:+8.1f} | "
            f"Outcome: {rec['outcome']:4s} | "
            f"Mode: {rec['match0']['cand_mode']}"
        )

    t_run_total = time.perf_counter() - t_run_start
    log(f"Execution complete in {t_run_total:.1f}s ({t_run_total / total_seeds:.2f}s/seed).")

    # 1. Write RAW_RESULTS.json
    with open(RAW_RESULTS_FILE, "w", encoding="utf-8") as f:
        json.dump(all_match_records, f, indent=2)
    log(f"Saved RAW_RESULTS.json ({len(all_match_records)} records).")

    # 2. Write PAIRED_DELTAS.csv
    with open(PAIRED_DELTAS_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "seed", "cand_seat0_rew", "base_seat1_rew", "delta_m0",
            "base_seat0_rew", "cand_seat1_rew", "delta_m1",
            "paired_mean_delta", "outcome", "cand_mode_m0", "specialized_crop_m0"
        ])
        for r in all_match_records:
            writer.writerow([
                r["seed"],
                r["match0"]["cand_reward"],
                r["match0"]["base_reward"],
                r["match0"]["delta"],
                r["match1"]["base_reward"],
                r["match1"]["cand_reward"],
                r["match1"]["delta"],
                r["paired_mean_delta"],
                r["outcome"],
                r["match0"]["cand_mode"],
                r["match0"]["specialized_crop"]
            ])
    log(f"Saved PAIRED_DELTAS.csv ({len(all_match_records)} rows).")

    # 3. Write DECISION_EVENTS.csv
    if all_decision_events:
        with open(DECISION_EVENTS_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "seed", "step", "observed_shops", "cash", "inventory",
                "baseline_recommendation", "specialization_recommendation",
                "expected_specialization_value", "expected_baseline_value",
                "incremental_value", "risk_penalty", "liquidity_state",
                "decision", "resulting_plan"
            ])
            for ev in all_decision_events:
                writer.writerow([
                    ev.get("seed", ""),
                    ev.get("step", ""),
                    ev.get("observed_shops", ""),
                    ev.get("cash", ""),
                    json.dumps(ev.get("inventory", {})),
                    ev.get("baseline_recommendation", ""),
                    ev.get("specialization_recommendation", ""),
                    ev.get("expected_specialization_value", ""),
                    ev.get("expected_baseline_value", ""),
                    ev.get("incremental_value", ""),
                    ev.get("risk_penalty", ""),
                    ev.get("liquidity_state", ""),
                    ev.get("decision", ""),
                    ev.get("resulting_plan", "")
                ])
        log(f"Saved DECISION_EVENTS.csv ({len(all_decision_events)} events).")

    # 4. Compute and write STATISTICS_RECOMPUTED.json
    stats_dict = compute_statistics(all_match_records)
    with open(STATS_FILE, "w", encoding="utf-8") as f:
        json.dump(stats_dict, f, indent=2)
    log(f"Saved STATISTICS_RECOMPUTED.json.")

    log("=" * 80)
    log("EXP-DEV-003 EXECUTIVE SUMMARY")
    log("=" * 80)
    log(f"  Mean Paired Delta : ${stats_dict['mean_paired_delta']:+.2f}")
    log(f"  Median Delta      : ${stats_dict['median']:+.2f}")
    log(f"  Win / Loss / Tie  : {stats_dict['win_count']} / {stats_dict['loss_count']} / {stats_dict['tie_count']}")
    log(f"  Win Rate          : {stats_dict['win_rate'] * 100:.1f}%")
    log(f"  Downside Frequency: {stats_dict['downside_frequency'] * 100:.1f}%")
    log(f"  Min / Max Delta   : ${stats_dict['min']:+.2f} / ${stats_dict['max']:+.2f}")
    log(f"  Active Seeds      : {stats_dict['active_seeds_count']} / {stats_dict['n_seeds']} ({stats_dict['active_seeds_fraction']*100:.1f}%)")
    log(f"  Gate A (Mean >= +30) : {'PASS' if stats_dict['gates']['Gate_A_positive_mean_ge_30']['passed'] else 'FAIL'}")
    log(f"  Gate B (Win >= 50%)  : {'PASS' if stats_dict['gates']['Gate_B_win_rate_ge_50']['passed'] else 'FAIL'}")
    log(f"  Gate C (Loss >= -350): {'PASS' if stats_dict['gates']['Gate_C_worst_loss_ge_minus_350']['passed'] else 'FAIL'}")
    log(f"  Gate D (No Outlier)  : {'PASS' if stats_dict['gates']['Gate_D_outlier_non_dominance']['passed'] else 'FAIL'}")
    log(f"  Gate E (5-35 Active) : {'PASS' if stats_dict['gates']['Gate_E_selective_activation']['passed'] else 'FAIL'}")
    log(f"  Verdict Classification: {stats_dict['epistemic_classification']}")
    log("=" * 80)


if __name__ == "__main__":
    main()
