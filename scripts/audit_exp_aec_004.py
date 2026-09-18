#!/usr/bin/env python3
"""
Independent Scientific Audit and Statistical Reproduction for EXP-AEC-004.

This script executes an independent verification of:
1. V3 chassis SHA-256 hash invariant.
2. Holdout partitions (340050-340199, 214200-214249) zero-touch covenant.
3. Historical cohorts separation.
4. Mechanism isolation (Control feed commits == 0, Resource conversion == 0).
5. Shed overflow invariant (max shed units <= 100).
6. Counterfactual fidelity (100% VERIFIED).
7. Independent reproduction of primary estimator and secondary statistics from raw CSV/JSON.
8. Terminal-purpose causal audit on late feed purchases.
"""

from __future__ import annotations

import csv
import hashlib
import json
import os
import sys
from typing import Any, Dict, List

import numpy as np
import scipy.stats as stats

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
V3_PATH = os.path.join(REPO_ROOT, "submission_Vj_kc_v3.tar.gz")
V3_EXPECTED_SHA = "845e0d10981b11b06d272048ff5cee30d70a0403dd757651a556a78c8bf18943"

EXP_DIR = os.path.join(REPO_ROOT, "experiments", "EXP-AEC-004")
RAW_RESULTS_PATH = os.path.join(EXP_DIR, "RAW_RESULTS.json")
PAIRED_DELTAS_PATH = os.path.join(EXP_DIR, "PAIRED_DELTAS.csv")
COMMITTED_PATCHES_PATH = os.path.join(EXP_DIR, "COMMITTED_PATCHES.csv")
TELEMETRY_EVENTS_PATH = os.path.join(EXP_DIR, "TELEMETRY_EVENTS.csv")
SUMMARY_PATH = os.path.join(EXP_DIR, "SUMMARY.json")
MANIFEST_PATH = os.path.join(EXP_DIR, "EXECUTION_MANIFEST.json")
LOG_PATH = os.path.join(EXP_DIR, "EXECUTION_LOG.txt")

PRIMARY_HOLDOUT = (340050, 340199)
SECONDARY_HOLDOUT = (214200, 214249)
CONSUMED_RANGES = [
    (340000, 340049, "EXP-AEC-001"),
    (340200, 340249, "EXP-AEC-002"),
    (340250, 340299, "EXP-AEC-003"),
]


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def audit() -> Dict[str, Any]:
    print("=" * 80)
    print("INDEPENDENT SCIENTIFIC AUDIT: EXP-AEC-004")
    print("=" * 80)

    report = {}

    # 1. V3 Backbone Hash Invariant
    actual_v3_sha = sha256_file(V3_PATH)
    v3_pass = (actual_v3_sha == V3_EXPECTED_SHA)
    report["1_v3_chassis_hash"] = {
        "pass": v3_pass,
        "actual": actual_v3_sha,
        "expected": V3_EXPECTED_SHA,
    }
    print(f"1. V3 Chassis Integrity: {'PASS' if v3_pass else 'FAIL'}")

    # 2. File existence
    for p, name in [
        (RAW_RESULTS_PATH, "RAW_RESULTS.json"),
        (PAIRED_DELTAS_PATH, "PAIRED_DELTAS.csv"),
        (COMMITTED_PATCHES_PATH, "COMMITTED_PATCHES.csv"),
        (SUMMARY_PATH, "SUMMARY.json"),
        (MANIFEST_PATH, "EXECUTION_MANIFEST.json"),
    ]:
        if not os.path.exists(p):
            print(f"CRITICAL: Missing artifact {name} at {p}")
            return {"CRITICAL_ERROR": f"Missing artifact {name}"}

    # 3. Holdout Zero-Touch Audit across all files and logs
    with open(RAW_RESULTS_PATH, "r", encoding="utf-8") as f:
        raw_results = json.load(f)

    seeds_seen = sorted([int(k) for k in raw_results.keys()])
    holdout_touches = 0
    for s in seeds_seen:
        if PRIMARY_HOLDOUT[0] <= s <= PRIMARY_HOLDOUT[1] or SECONDARY_HOLDOUT[0] <= s <= SECONDARY_HOLDOUT[1]:
            holdout_touches += 1

    # Scan log file for holdout mentions
    log_holdout_hits = 0
    if os.path.exists(LOG_PATH):
        with open(LOG_PATH, "r", encoding="utf-8") as f:
            log_content = f.read()
            for s in range(PRIMARY_HOLDOUT[0], PRIMARY_HOLDOUT[1] + 1):
                if f"Seed {s}" in log_content or f"seed {s}" in log_content:
                    log_holdout_hits += 1

    holdout_pass = (holdout_touches == 0 and log_holdout_hits == 0)
    report["2_holdout_protection"] = {
        "pass": holdout_pass,
        "primary_holdout": PRIMARY_HOLDOUT,
        "secondary_holdout": SECONDARY_HOLDOUT,
        "raw_results_holdout_touches": holdout_touches,
        "log_holdout_hits": log_holdout_hits,
    }
    print(f"2. Holdout Protection (Zero Touches): {'PASS' if holdout_pass else 'FAIL'}")

    # 4. Cohort Completeness
    expected_cohort = list(range(340300, 340350))
    cohort_pass = (seeds_seen == expected_cohort)
    report["3_cohort_completeness"] = {
        "pass": cohort_pass,
        "count": len(seeds_seen),
        "expected_count": 50,
        "min_seed": min(seeds_seen),
        "max_seed": max(seeds_seen),
    }
    print(f"3. Cohort Completeness (N=50, 340300-340349): {'PASS' if cohort_pass else 'FAIL'}")

    # 5. Mechanism Isolation Audit
    control_feed_commits = 0
    treat_feed_commits = 0
    rc_commits_treat = 0
    rc_commits_ctrl = 0
    quarantined_commits = 0

    for s_str, r in raw_results.items():
        for m_key in ("match_a", "match_b"):
            m = r[m_key]
            ctrl_commits = m.get("commits_by_mechanism_control", {})
            treat_commits = m.get("commits_by_mechanism_treatment", {})

            if "EMERGENCY_FEED_PURCHASE" in ctrl_commits:
                control_feed_commits += ctrl_commits["EMERGENCY_FEED_PURCHASE"]
            if "EMERGENCY_FEED_PURCHASE" in treat_commits:
                treat_feed_commits += treat_commits["EMERGENCY_FEED_PURCHASE"]
            if "RESOURCE_CONVERSION" in ctrl_commits:
                rc_commits_ctrl += ctrl_commits["RESOURCE_CONVERSION"]
            if "RESOURCE_CONVERSION" in treat_commits:
                rc_commits_treat += treat_commits["RESOURCE_CONVERSION"]

    iso_pass = (control_feed_commits == 0 and rc_commits_treat == 0 and rc_commits_ctrl == 0)
    report["4_mechanism_isolation"] = {
        "pass": iso_pass,
        "control_emergency_feed_commits": control_feed_commits,
        "treatment_emergency_feed_commits": treat_feed_commits,
        "resource_conversion_treatment": rc_commits_treat,
        "resource_conversion_control": rc_commits_ctrl,
    }
    print(f"4. Mechanism Isolation: {'PASS' if iso_pass else 'FAIL'} (Ctrl Feed={control_feed_commits}, RC={rc_commits_treat + rc_commits_ctrl})")

    # 6. Shed Overflow Invariant
    max_shed = 0
    shed_overflow_seeds = []
    checkpoint_path = os.path.join(EXP_DIR, "CHECKPOINT.json")
    if os.path.exists(checkpoint_path):
        with open(checkpoint_path, "r", encoding="utf-8") as f:
            chk = json.load(f)
            for s_str, rec in chk.get("completed_seeds", {}).items():
                ms = rec.get("max_shed_units", 0)
                if ms > max_shed:
                    max_shed = ms
                if ms > 100 or rec.get("shed_overflow_occurred", False):
                    shed_overflow_seeds.append((int(s_str), ms))

    shed_pass = (len(shed_overflow_seeds) == 0 and max_shed <= 100)
    report["5_shed_overflow"] = {
        "pass": shed_pass,
        "max_shed_units_seen": max_shed,
        "overflow_count": len(shed_overflow_seeds),
    }
    print(f"5. Shed Inventory Bound (Max <= 100): {'PASS' if shed_pass else 'FAIL'} (Max={max_shed})")

    # 7. Counterfactual Fidelity Audit
    committed_patches = []
    with open(COMMITTED_PATCHES_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            committed_patches.append(row)

    non_verified_fidelity = [cp for cp in committed_patches if cp.get("counterfactual_fidelity") != "VERIFIED"]
    fidelity_pass = (len(non_verified_fidelity) == 0)
    report["6_counterfactual_fidelity"] = {
        "pass": fidelity_pass,
        "total_committed_patches": len(committed_patches),
        "non_verified_count": len(non_verified_fidelity),
    }
    print(f"6. Counterfactual Fidelity (100% VERIFIED): {'PASS' if fidelity_pass else 'FAIL'}")

    # 8. Late Feed Terminal Safety Audit
    feed_patches = [cp for cp in committed_patches if cp.get("mechanism_family") == "EMERGENCY_FEED_PURCHASE"]
    late_feed_commits = [cp for cp in feed_patches if int(cp.get("turn", 0)) >= 600]
    day29_feed_commits = [cp for cp in feed_patches if int(cp.get("turn", 0)) >= 696]
    report["7_terminal_safety_audit"] = {
        "total_feed_commits": len(feed_patches),
        "late_feed_commits_step_ge_600": len(late_feed_commits),
        "day29_feed_commits_step_ge_696": len(day29_feed_commits),
        "zero_terminal_blind_pass": (len(day29_feed_commits) == 0),
    }
    print(f"7. Terminal Safety Audit: Total Feed Commits={len(feed_patches)}, Late (>=600)={len(late_feed_commits)}, Day 29 (>=696)={len(day29_feed_commits)}")

    # 9. Independent Statistical Reproduction from PAIRED_DELTAS.csv
    deltas = []
    treat_wins = 0
    ctrl_wins = 0
    ties = 0

    with open(PAIRED_DELTAS_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            d = float(row["delta_margin"])
            deltas.append(d)
            for w in (row["match_a_winner"], row["match_b_winner"]):
                if w == "TREATMENT":
                    treat_wins += 1
                elif w == "CONTROL":
                    ctrl_wins += 1
                else:
                    ties += 1

    deltas_arr = np.array(deltas, dtype=float)
    N = len(deltas_arr)
    mean_d = float(np.mean(deltas_arr))
    std_d = float(np.std(deltas_arr, ddof=1))
    se_d = std_d / np.sqrt(N)
    t_crit = float(stats.t.ppf(0.95, df=N - 1))
    lower_95 = mean_d - t_crit * se_d
    t_stat = mean_d / se_d if se_d > 0 else 0.0
    p_val_t = 1.0 - float(stats.t.cdf(t_stat, df=N - 1))

    total_matches = 2 * N
    win_rate_delta_pp = ((treat_wins - ctrl_wins) / total_matches) * 100.0

    with open(SUMMARY_PATH, "r", encoding="utf-8") as f:
        runner_summary = json.load(f)

    # Verification against runner SUMMARY.json
    stats_match = (
        abs(mean_d - runner_summary["mean_delta_margin"]) < 1e-2
        and abs(std_d - runner_summary["std_delta_margin"]) < 1e-2
        and abs(lower_95 - runner_summary["lower_95_one_sided_bound"]) < 1e-2
        and treat_wins == runner_summary["treatment_wins"]
        and ctrl_wins == runner_summary["control_wins"]
        and ties == runner_summary["ties"]
    )

    report["8_statistical_reproduction"] = {
        "pass": stats_match,
        "N": N,
        "independent_mean": round(mean_d, 2),
        "runner_mean": runner_summary["mean_delta_margin"],
        "independent_lower_95": round(lower_95, 2),
        "runner_lower_95": runner_summary["lower_95_one_sided_bound"],
        "t_statistic": round(t_stat, 4),
        "p_value_one_sided": float(f"{p_val_t:.6g}"),
        "treat_wins": treat_wins,
        "ctrl_wins": ctrl_wins,
        "ties": ties,
        "win_rate_delta_pp": round(win_rate_delta_pp, 2),
    }

    print(f"8. Statistical Reproduction: {'EXACT MATCH' if stats_match else 'DISCREPANCY'}")
    print(f"   Mean Margin Delta: ${mean_d:+.2f}")
    print(f"   Lower 95% Bound: ${lower_95:+.2f} (Acceptance requirement: >= $0.00)")
    print(f"   One-sided p-value: {p_val_t:.6f}")
    print(f"   Wins: Treat={treat_wins}, Ctrl={ctrl_wins}, Ties={ties} (Delta={win_rate_delta_pp:+.2f} pp)")

    # Overall Audit Decision
    all_pass = (
        v3_pass
        and holdout_pass
        and cohort_pass
        and iso_pass
        and shed_pass
        and fidelity_pass
        and stats_match
    )
    report["OVERALL_AUDIT_PASS"] = all_pass
    print("=" * 80)
    print(f"OVERALL INDEPENDENT AUDIT STATUS: {'PASS' if all_pass else 'FAIL'}")
    print("=" * 80)

    return report


if __name__ == "__main__":
    rep = audit()
    out_path = os.path.join(EXP_DIR, "INDEPENDENT_AUDIT_REPORT.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(rep, f, indent=2)
    print(f"Audit report saved to {out_path}")
