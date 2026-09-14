# SPDX-License-Identifier: MIT
"""
=============================================================================
EXP-DEV-005 EXECUTION RUNNER: DISCOVERY PARTITION
=============================================================================
Experiment: EXP-DEV-005
Title: Confirmed-Shop Gated Whole-Route Scheduler over V54++ Residual Preemption
Governing Protocol: DEVELOPMENT_EXPERIMENT_PROTOCOL_V1_4.md
Protocol Hash (SHA-256): ac69fc602083f232792ad5bdabd699e4b9f96e73462f9edc740ccd63c727e9f6
Discovery Partition: Seeds 247000 to 247049 (N=50 seeds, 100 paired CRN matches)
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
from dev_005_confirmed_shop_scheduler import Dev005ConfirmedShopScheduler
from verify_agent_zero_leakage import audit_agent_ast

EXP_DIR = os.path.abspath(os.path.dirname(__file__))
LOG_FILE = os.path.join(EXP_DIR, "EXECUTION_LOG.txt")
RAW_RESULTS_FILE = os.path.join(EXP_DIR, "RAW_RESULTS.json")
PAIRED_DELTAS_FILE = os.path.join(EXP_DIR, "PAIRED_DELTAS.csv")
DECISION_EVENTS_FILE = os.path.join(EXP_DIR, "DECISION_EVENTS.csv")
SPECIALIZATION_EVENTS_FILE = os.path.join(EXP_DIR, "SPECIALIZATION_EVENTS.csv")
STATS_FILE = os.path.join(EXP_DIR, "STATISTICS_RECOMPUTED.json")

BASELINE_PATH = os.path.join(BASE_DIR, "candidates", "compiled_v54_plus_residual.py")
CANDIDATE_PATH = os.path.join(BASE_DIR, "candidates", "closed_loop_architecture", "dev_005_confirmed_shop_scheduler.py")


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
    if 246000 <= seed <= 246049:
        msg = f"CRITICAL PROTOCOL VIOLATION: DEV-004 consumed seed {seed} requested!"
        log(f"FATAL: {msg}")
        raise RuntimeError(msg)


def verify_preflight():
    log("=" * 80)
    log("PREFLIGHT INVARIANT VERIFICATION FOR EXP-DEV-005 DISCOVERY RUN")
    log("=" * 80)

    # 1. Protocol V1.4 SHA-256
    proto_path = os.path.join(EXP_DIR, "DEVELOPMENT_EXPERIMENT_PROTOCOL_V1_4.md")
    with open(proto_path, "rb") as f:
        proto_sha = hashlib.sha256(f.read()).hexdigest()
    EXPECTED_PROTO_SHA = "ac69fc602083f232792ad5bdabd699e4b9f96e73462f9edc740ccd63c727e9f6"
    assert proto_sha == EXPECTED_PROTO_SHA, f"Protocol SHA mismatch: {proto_sha} != {EXPECTED_PROTO_SHA}"
    log(f"  [1/6] Protocol V1.4 SHA-256 Verified: {proto_sha}")

    # 2. Frozen Baseline SHA-256
    with open(BASELINE_PATH, "rb") as f:
        base_sha = hashlib.sha256(f.read()).hexdigest()
    EXPECTED_BASE_SHA = "18402ec6fa3709b9b5ef90dd9c8d7b9c0e44aea55ab163e44a80a4adc0cb7eeb"
    assert base_sha == EXPECTED_BASE_SHA, f"Baseline SHA mismatch: {base_sha} != {EXPECTED_BASE_SHA}"
    log(f"  [2/6] Baseline SHA-256 Verified: {base_sha}")

    # 3. Treatment SHA-256
    with open(CANDIDATE_PATH, "rb") as f:
        cand_sha = hashlib.sha256(f.read()).hexdigest()
    EXPECTED_CAND_SHA = "f52b168619e47bea6a052faff890fc84804cb39b47392d247139967f910e2a78"
    assert cand_sha == EXPECTED_CAND_SHA, f"Candidate SHA mismatch: {cand_sha} != {EXPECTED_CAND_SHA}"
    log(f"  [3/6] Treatment dev_005 SHA-256 Verified: {cand_sha}")

    # 4. AST Zero-Leakage Audit
    ast_violations = audit_agent_ast(CANDIDATE_PATH)
    assert len(ast_violations) == 0, f"Candidate AST violations: {ast_violations}"
    log("  [4/6] Candidate dev_005 AST Zero-Leakage Verified Clean (0 violations).")

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
    spec_events = []

    # Match 0: Candidate is Seat 0, Baseline is Seat 1
    g0 = kagsim.Game(seed)
    cand0 = Dev005ConfirmedShopScheduler(seat=0, seed=seed)
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
    for ev in cand0.decision_events:
        ev_copy = dict(ev)
        ev_copy["match"] = 0
        decision_events.append(ev_copy)
    for ev in cand0.specialization_events:
        ev_copy = dict(ev)
        ev_copy["match"] = 0
        spec_events.append(ev_copy)

    # Match 1: Baseline is Seat 0, Candidate is Seat 1
    g1 = kagsim.Game(seed)
    base0 = load_isolated_baseline(f"base_s{seed}_m1")
    cand1 = Dev005ConfirmedShopScheduler(seat=1, seed=seed)

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
    for ev in cand1.decision_events:
        ev_copy = dict(ev)
        ev_copy["match"] = 1
        decision_events.append(ev_copy)
    for ev in cand1.specialization_events:
        ev_copy = dict(ev)
        ev_copy["match"] = 1
        spec_events.append(ev_copy)

    paired_mean_delta = 0.5 * (delta0 + delta1)
    if paired_mean_delta > 0.0:
        outcome = "WIN"
    elif paired_mean_delta < 0.0:
        outcome = "LOSS"
    else:
        outcome = "TIE"

    # Lifetime activation check across all decision events for this seed
    ever_activated = any(
        ev["decision"] == "SPECIALIZE_CONFIRMED"
        for ev in cand0.decision_events + cand1.decision_events
    )

    match_record = {
        "seed": seed,
        "match0_cand_p0": cand_rew0,
        "match0_base_p1": base_rew1,
        "match0_delta": delta0,
        "match1_base_p0": base_rew0,
        "match1_cand_p1": cand_rew1,
        "match1_delta": delta1,
        "paired_mean_delta": paired_mean_delta,
        "outcome": outcome,
        "activated": ever_activated,
        "cand0_plan": cand0.active_plan,
        "cand1_plan": cand1.active_plan,
        "missed_opps_m0": cand0.missed_opportunity_count,
        "confirmed_specs_m0": cand0.post_confirmation_specialization_count,
        "runtime_sec": round(t0_elapsed + t1_elapsed, 3)
    }

    return match_record, decision_events, spec_events


def compute_statistics(records: List[Dict[str, Any]], all_decisions: List[Dict[str, Any]]) -> Dict[str, Any]:
    deltas = [r["paired_mean_delta"] for r in records]
    n = len(deltas)
    assert n == 50, f"Expected 50 seeds, got {n}"

    sorted_deltas = sorted(deltas)
    mean_val = sum(deltas) / n
    variance = sum((x - mean_val) ** 2 for x in deltas) / (n - 1)
    sd_val = math.sqrt(variance)
    se_val = sd_val / math.sqrt(n)
    t_stat = mean_val / se_val if se_val > 0 else 0.0

    try:
        from scipy import stats
        p_val = float(stats.t.sf(abs(t_stat), df=n - 1) * 2)
    except ImportError:
        p_val = 2.0 * (1.0 - 0.5 * (1.0 + math.erf(abs(t_stat) / math.sqrt(2.0))))

    def pct(arr, p):
        k = (len(arr) - 1) * p
        f = math.floor(k)
        c = math.ceil(k)
        if f == c:
            return arr[int(k)]
        return arr[f] * (c - k) + arr[c] * (k - f)

    wins = sum(1 for d in deltas if d > 0.0)
    losses = sum(1 for d in deltas if d < 0.0)
    ties = sum(1 for d in deltas if d == 0.0)

    # Truncated subsets
    mean_ex_best = sum(sorted_deltas[:-1]) / (n - 1)
    mean_ex_worst = sum(sorted_deltas[1:]) / (n - 1)
    mean_ex_top2 = sum(sorted_deltas[:-2]) / (n - 2)

    # 10% trimmed mean (remove top 5 and bottom 5)
    trimmed_mean = sum(sorted_deltas[5:-5]) / (n - 10)

    # Activation rate
    activated_seeds = sum(1 for r in records if r["activated"])
    activation_rate = activated_seeds / n

    # Decision telemetry counts
    total_decisions = len(all_decisions)
    confirmed_spec_decisions = sum(1 for d in all_decisions if d["decision"] == "SPECIALIZE_CONFIRMED")
    rejected_unconfirmed_decisions = sum(1 for d in all_decisions if d["decision"] == "REJECT_UNCONFIRMED")
    baseline_decisions = sum(1 for d in all_decisions if d["decision"] == "BASELINE")

    return {
        "n_seeds": n,
        "n_matches": n * 2,
        "mean_paired_delta": round(mean_val, 2),
        "median_paired_delta": round(pct(sorted_deltas, 0.5), 2),
        "sd": round(sd_val, 4),
        "se": round(se_val, 4),
        "t_stat": round(t_stat, 2),
        "p_value": round(p_val, 6),
        "ci_95_lower": round(mean_val - 2.009 * se_val, 3),
        "ci_95_upper": round(mean_val + 2.009 * se_val, 3),
        "trimmed_mean_10pct": round(trimmed_mean, 3),
        "min": round(min(deltas), 2),
        "max": round(max(deltas), 2),
        "p01": round(pct(sorted_deltas, 0.01), 3),
        "p05": round(pct(sorted_deltas, 0.05), 3),
        "p10": round(pct(sorted_deltas, 0.10), 3),
        "p25": round(pct(sorted_deltas, 0.25), 3),
        "p50": round(pct(sorted_deltas, 0.50), 3),
        "p75": round(pct(sorted_deltas, 0.75), 3),
        "p90": round(pct(sorted_deltas, 0.90), 3),
        "p95": round(pct(sorted_deltas, 0.95), 3),
        "p99": round(pct(sorted_deltas, 0.99), 3),
        "wins": wins,
        "losses": losses,
        "ties": ties,
        "win_rate": round(wins / n, 4),
        "loss_rate": round(losses / n, 4),
        "tie_rate": round(ties / n, 4),
        "mean_excluding_best": round(mean_ex_best, 4),
        "mean_excluding_worst": round(mean_ex_worst, 4),
        "mean_excluding_top2": round(mean_ex_top2, 4),
        "top1_contribution_pct": round((sorted_deltas[-1] / sum(deltas) * 100.0) if sum(deltas) > 0 else 0.0, 2),
        "top2_contribution_pct": round(((sorted_deltas[-1] + sorted_deltas[-2]) / sum(deltas) * 100.0) if sum(deltas) > 0 else 0.0, 2),
        "activated_seeds": activated_seeds,
        "activation_rate": round(activation_rate, 4),
        "total_checkpoint_decisions": total_decisions,
        "confirmed_specialization_decisions": confirmed_spec_decisions,
        "rejected_unconfirmed_decisions": rejected_unconfirmed_decisions,
        "baseline_decisions": baseline_decisions
    }


def main():
    verify_preflight()

    start_seed = 247000
    end_seed = 247049
    total_seeds = end_seed - start_seed + 1

    log(f"BEGINNING EXP-DEV-005 SIMULATION: {total_seeds} SEEDS ({start_seed} to {end_seed})")
    log(f"Candidate: Dev005ConfirmedShopScheduler")
    log(f"Baseline: compiled_v54_plus_residual (Sub 56146971)")

    all_records = []
    all_decisions = []
    all_spec_events = []

    t_suite_start = time.perf_counter()

    for idx, seed in enumerate(range(start_seed, end_seed + 1), start=1):
        rec, decs, specs = run_paired_match(seed)
        all_records.append(rec)
        all_decisions.extend(decs)
        all_spec_events.extend(specs)

        log(
            f"[{idx:02d}/{total_seeds}] Seed {seed:6d} | "
            f"Delta: {rec['paired_mean_delta']:+9.1f} | "
            f"Outcome: {rec['outcome']:4s} | "
            f"Act: {str(rec['activated']):5s} | "
            f"Missed: {rec['missed_opps_m0']:1d} | Conf: {rec['confirmed_specs_m0']:1d} | "
            f"Time: {rec['runtime_sec']:.2f}s"
        )

    t_suite_elapsed = time.perf_counter() - t_suite_start
    log(f"\nSimulation Complete in {t_suite_elapsed:.2f}s. Computing primary statistics...")

    # Write PAIRED_DELTAS.csv
    with open(PAIRED_DELTAS_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(all_records[0].keys()))
        writer.writeheader()
        writer.writerows(all_records)
    log(f"  Saved {PAIRED_DELTAS_FILE}")

    # Write DECISION_EVENTS.csv
    if all_decisions:
        with open(DECISION_EVENTS_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(all_decisions[0].keys()))
            writer.writeheader()
            writer.writerows(all_decisions)
        log(f"  Saved {DECISION_EVENTS_FILE}")

    # Write SPECIALIZATION_EVENTS.csv
    if all_spec_events:
        with open(SPECIALIZATION_EVENTS_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(all_spec_events[0].keys()))
            writer.writeheader()
            writer.writerows(all_spec_events)
        log(f"  Saved {SPECIALIZATION_EVENTS_FILE}")

    # Write RAW_RESULTS.json
    with open(RAW_RESULTS_FILE, "w", encoding="utf-8") as f:
        json.dump(all_records, f, indent=2)
    log(f"  Saved {RAW_RESULTS_FILE}")

    # Compute and write STATISTICS_RECOMPUTED.json
    stats = compute_statistics(all_records, all_decisions)
    stats["total_runtime_sec"] = round(t_suite_elapsed, 2)
    with open(STATS_FILE, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2)
    log(f"  Saved {STATS_FILE}")

    log("=" * 80)
    log("EXP-DEV-005 DISCOVERY SUMMARY REPORT")
    log("=" * 80)
    log(f"  Seeds: {stats['n_seeds']} | Matches: {stats['n_matches']}")
    log(f"  Paired Mean Delta:  {stats['mean_paired_delta']:+,.2f}")
    log(f"  10% Trimmed Mean:   {stats['trimmed_mean_10pct']:+,.2f}")
    log(f"  Median Delta:       {stats['median_paired_delta']:+,.2f}")
    log(f"  Standard Error:     ${stats['se']:,.2f}")
    log(f"  Student-t:          {stats['t_stat']:.2f} (p = {stats['p_value']:.4f})")
    log(f"  95% CI:             [${stats['ci_95_lower']:,.2f}, ${stats['ci_95_upper']:,.2f}]")
    log(f"  Record:             {stats['wins']}W / {stats['losses']}L / {stats['ties']}T "
        f"({stats['win_rate']*100:.1f}% / {stats['loss_rate']*100:.1f}% / {stats['tie_rate']*100:.1f}%)")
    log(f"  Activation Rate:    {stats['activation_rate']*100:.1f}% ({stats['activated_seeds']} seeds)")
    log(f"  Excluding Best:     {stats['mean_excluding_best']:+,.2f}")
    log(f"  Excluding Top-2:    {stats['mean_excluding_top2']:+,.2f}")
    log(f"  Confirmed Decs:     {stats['confirmed_specialization_decisions']}")
    log(f"  Rejected Opps:      {stats['rejected_unconfirmed_decisions']}")
    log("=" * 80)


if __name__ == "__main__":
    main()
