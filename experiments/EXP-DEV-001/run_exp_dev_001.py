"""
=============================================================================
EXP-DEV-001 AUTHORITATIVE EXPERIMENTAL RUNNER
=============================================================================
Governing Protocol: DEVELOPMENT_EXPERIMENT_PROTOCOL_V1.md (SHA-256: 671e915e...)
Git Commit: a1ba5acb0d04689874ce1333892825f014eea924
Evaluation Mode: Paired Common Random Numbers (CRN), Seat 0 + Seat 1
Active Containment: ActiveContainmentSandbox (Zero-Leakage Enforcement)
Virgin Holdout Protection: Strict exclusion of Seeds 214200-214249
=============================================================================
"""

import copy
import csv
import hashlib
import importlib.util
import json
import math
import os
import subprocess
import sys
import time
from typing import Dict, List, Tuple, Any

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(BASE_DIR, "external_repos", "kaggriculture-cppsim"))
sys.path.insert(0, os.path.join(BASE_DIR, "candidates", "closed_loop_architecture"))
sys.path.insert(0, os.path.join(BASE_DIR, "extracted_agents", "dmitrii_lb2800"))
sys.path.insert(0, os.path.join(BASE_DIR, "scratch"))

import kagsim
import router_parent as mod_r
from closed_loop_v2 import ClosedLoopAgentV2
from dev_001_dynamic_portfolio import Dev001DynamicPortfolioAgent
from verify_agent_zero_leakage import ActiveContainmentSandbox, LeakageViolationError

EXPERIMENT_DIR = os.path.abspath(os.path.dirname(__file__))
LOG_FILE = os.path.join(EXPERIMENT_DIR, "EXP-DEV-001_EXECUTION_LOG.txt")


def log(msg: str):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
    line = f"[{timestamp} UTC] {msg}"
    print(line)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def assert_not_holdout(seed: int):
    """Hard invariant: virgin holdout seeds 214200-214249 must NEVER be executed."""
    if 214200 <= seed <= 214249:
        msg = f"CRITICAL PROTOCOL VIOLATION: Holdout seed {seed} requested during EXP-DEV-001!"
        log(f"FATAL: {msg}")
        raise RuntimeError(msg)


def verify_preflight_invariants():
    log("Verifying Preflight Invariants...")
    # 1. Protocol SHA
    proto_path = os.path.join(BASE_DIR, "DEVELOPMENT_EXPERIMENT_PROTOCOL_V1.md")
    with open(proto_path, "rb") as f:
        content = f.read()
    sha = hashlib.sha256(content).hexdigest()
    EXPECTED_SHA = "671e915eadd72adb710421b45e6a33ad533abd9d68ff67770b8dd412ff7381b3"
    assert sha == EXPECTED_SHA, f"Protocol SHA mismatch: {sha} != {EXPECTED_SHA}"
    log(f"  Protocol SHA-256 Verified: {sha}")

    # 2. Frozen Submissions
    shop_path = os.path.join(BASE_DIR, "candidates", "compiled_v54_plus_shop.py")
    res_path = os.path.join(BASE_DIR, "candidates", "compiled_v54_plus_residual.py")
    with open(shop_path, "rb") as f:
        shop_sha = hashlib.sha256(f.read()).hexdigest()
    with open(res_path, "rb") as f:
        res_sha = hashlib.sha256(f.read()).hexdigest()
    assert shop_sha == "f651ccd220e701968bc33579812d8917da63f5b0582f2fd0d363fa6a16ffd8b8"
    assert res_sha == "18402ec6fa3709b9b5ef90dd9c8d7b9c0e44aea55ab163e44a80a4adc0cb7eeb"
    log("  Frozen Live Submission Checksums Verified bit-exact.")


def run_paired_match(
    cand_factory,
    opp_factory,
    seed: int,
    use_sandbox: bool = True
) -> Dict[str, Any]:
    assert_not_holdout(seed)

    # Match 0: Candidate is Seat 0, Opponent is Seat 1
    g0 = kagsim.Game(seed)
    cand_agent0 = cand_factory()
    opp_agent1 = opp_factory()
    sb0 = ActiveContainmentSandbox(g0) if use_sandbox else None

    s0 = 0
    err0 = None
    while not g0.done:
        o0 = g0.observe(0)
        o1 = g0.observe(1)
        if use_sandbox:
            with sb0:
                a0 = cand_agent0.act(o0)
        else:
            a0 = cand_agent0.act(o0)
        a1 = opp_agent1.act(o1)
        g0.step(a0, a1)
        s0 += 1

    cand_rew0 = g0.reward(0)
    opp_rew1 = g0.reward(1)

    # Match 1: Opponent is Seat 0, Candidate is Seat 1
    g1 = kagsim.Game(seed)
    opp_agent0 = opp_factory()
    cand_agent1 = cand_factory()
    sb1 = ActiveContainmentSandbox(g1) if use_sandbox else None

    s1 = 0
    err1 = None
    while not g1.done:
        o0 = g1.observe(0)
        o1 = g1.observe(1)
        a0 = opp_agent0.act(o0)
        if use_sandbox:
            with sb1:
                a1 = cand_agent1.act(o1)
        else:
            a1 = cand_agent1.act(o1)
        g1.step(a0, a1)
        s1 += 1

    opp_rew0 = g1.reward(0)
    cand_rew1 = g1.reward(1)

    # Paired Margin: Margin(s) = (Cand0 - Opp1) + (Cand1 - Opp0)
    m0 = cand_rew0 - opp_rew1
    m1 = cand_rew1 - opp_rew0
    paired_margin = m0 + m1

    return {
        "seed": seed,
        "match0": {"cand_score": cand_rew0, "opp_score": opp_rew1, "margin": m0, "steps": s0},
        "match1": {"opp_score": opp_rew0, "cand_score": cand_rew1, "margin": m1, "steps": s1},
        "paired_margin": paired_margin,
        "cand_total": cand_rew0 + cand_rew1,
        "opp_total": opp_rew0 + opp_rew1,
        "cand_mean_cash": (cand_rew0 + cand_rew1) / 2.0,
        "opp_mean_cash": (opp_rew0 + opp_rew1) / 2.0,
        "win": 1 if paired_margin > 0 else 0,
        "loss": 1 if paired_margin < 0 else 0,
        "tie": 1 if paired_margin == 0 else 0,
    }


def compute_sample_statistics(paired_deltas: List[float]) -> Dict[str, Any]:
    n = len(paired_deltas)
    if n == 0:
        return {}
    mean = sum(paired_deltas) / n
    sorted_d = sorted(paired_deltas)
    median = sorted_d[n // 2] if n % 2 == 1 else (sorted_d[n // 2 - 1] + sorted_d[n // 2]) / 2.0
    var = sum((x - mean) ** 2 for x in paired_deltas) / max(1, n - 1)
    sd = math.sqrt(var)
    se = sd / math.sqrt(n)

    # Student's t critical value for df = n - 1 (approx 2.009 for n=50, 1.984 for n=100)
    # Using scipy-grade approximation for df=49: t_crit = 2.009575
    t_crit = 2.009575 if n == 50 else 1.96
    ci_lower = mean - t_crit * se
    ci_upper = mean + t_crit * se

    t_stat = mean / se if se > 0 else 0.0

    # Empirical quantiles
    def quantile(p):
        idx = p * (n - 1)
        low = int(math.floor(idx))
        high = int(math.ceil(idx))
        weight = idx - low
        return sorted_d[low] * (1.0 - weight) + sorted_d[high] * weight

    return {
        "n": n,
        "mean": mean,
        "median": median,
        "sd": sd,
        "se": se,
        "t_stat": t_stat,
        "ci_95": [ci_lower, ci_upper],
        "p01": quantile(0.01),
        "p05": quantile(0.05),
        "p10": quantile(0.10),
        "p25": quantile(0.25),
        "p50": quantile(0.50),
        "p75": quantile(0.75),
        "p90": quantile(0.90),
        "p95": quantile(0.95),
        "p99": quantile(0.99),
        "worst_loss": min(paired_deltas),
        "best_win": max(paired_deltas),
    }


def main():
    log("=" * 80)
    log("EXP-DEV-001: EVIDENCE-LOCKED DYNAMIC PORTFOLIO ADAPTATION")
    log("=" * 80)

    # 1. Preflight
    verify_preflight_invariants()

    cand_factory = lambda: Dev001DynamicPortfolioAgent()
    ctrl_v2_factory = lambda: ClosedLoopAgentV2()
    dmitrii_factory = lambda: mod_r.Policy(os.path.join(BASE_DIR, "extracted_agents", "dmitrii_lb2800"))

    # 2. Stage 2: Smoke Test (2 Seeds: 49998, 49999)
    log("\n--- STAGE 2: SMOKE TEST (Seeds 49998, 49999) ---")
    smoke_seeds = [49998, 49999]
    leakage_records = []
    for s in smoke_seeds:
        res = run_paired_match(cand_factory, ctrl_v2_factory, s, use_sandbox=True)
        log(f"  Smoke Seed {s}: Paired Margin vs V2 = ${res['paired_margin']:+,.0f} (Cand Total: ${res['cand_total']:,.0f})")
    log("  Smoke Test: PASS (0 exceptions, sandbox active).")

    # 3. Stage 3: Discovery Partition Execution (Seeds 50000..50049, N=50)
    log("\n--- STAGE 3: DISCOVERY PARTITION EXECUTION (Seeds 50000..50049, N=50 seeds) ---")
    discovery_seeds = list(range(50000, 50050))

    discovery_vs_v2_results = []
    discovery_vs_dmi_results = []
    paired_deltas_v2 = []
    paired_deltas_dmi = []

    t_start = time.time()
    for idx, s in enumerate(discovery_seeds, 1):
        # Match vs Control A: ClosedLoopAgentV2
        res_v2 = run_paired_match(cand_factory, ctrl_v2_factory, s, use_sandbox=True)
        discovery_vs_v2_results.append(res_v2)
        paired_deltas_v2.append(res_v2["paired_margin"])

        # Match vs Reference: Dmitrii-LB2800
        res_dmi = run_paired_match(cand_factory, dmitrii_factory, s, use_sandbox=True)
        discovery_vs_dmi_results.append(res_dmi)
        paired_deltas_dmi.append(res_dmi["paired_margin"])

        if idx % 10 == 0 or idx == len(discovery_seeds):
            cur_mean_v2 = sum(paired_deltas_v2) / len(paired_deltas_v2)
            cur_wr_v2 = sum(r["win"] for r in discovery_vs_v2_results) / len(discovery_vs_v2_results) * 100.0
            log(f"  Progress: {idx}/{len(discovery_seeds)} seeds ({idx*2} matches) | Current Mean Margin vs V2: ${cur_mean_v2:+,.2f} | WR: {cur_wr_v2:.1f}%")

    elapsed = time.time() - t_start
    log(f"Discovery Execution completed in {elapsed:.1f}s.")

    # Compute Discovery Statistics
    stats_v2 = compute_sample_statistics(paired_deltas_v2)
    stats_dmi = compute_sample_statistics(paired_deltas_dmi)

    wins_v2 = sum(r["win"] for r in discovery_vs_v2_results)
    losses_v2 = sum(r["loss"] for r in discovery_vs_v2_results)
    ties_v2 = sum(r["tie"] for r in discovery_vs_v2_results)
    wr_v2 = (wins_v2 / len(discovery_seeds)) * 100.0

    wins_dmi = sum(r["win"] for r in discovery_vs_dmi_results)
    losses_dmi = sum(r["loss"] for r in discovery_vs_dmi_results)
    ties_dmi = sum(r["tie"] for r in discovery_vs_dmi_results)
    wr_dmi = (wins_dmi / len(discovery_seeds)) * 100.0

    log("\n" + "=" * 80)
    log("EXP-DEV-001 DISCOVERY RESULTS (N=50 Seeds, 100 Matches)")
    log("=" * 80)
    log(f"Primary Metric (Margin vs ClosedLoopAgentV2):")
    log(f"  Mean Margin:         ${stats_v2['mean']:+,.2f} coins")
    log(f"  Median Margin:       ${stats_v2['median']:+,.2f} coins")
    log(f"  Standard Dev (SD):    {stats_v2['sd']:,.2f} coins")
    log(f"  Standard Error (SE):  {stats_v2['se']:,.2f} coins")
    log(f"  Student's t-stat:     {stats_v2['t_stat']:,.4f}")
    log(f"  95% Confidence Int:  [${stats_v2['ci_95'][0]:+,.2f}, ${stats_v2['ci_95'][1]:+,.2f}]")
    log(f"  Paired Win Rate:      {wr_v2:.1f}% ({wins_v2}W - {losses_v2}L - {ties_v2}T)")
    log(f"  Worst Paired Loss:   ${stats_v2['worst_loss']:+,.2f} coins")
    log(f"  Best Paired Win:     ${stats_v2['best_win']:+,.2f} coins")
    log(f"  5th Percentile p05:  ${stats_v2['p05']:+,.2f} coins")
    log("-" * 80)
    log(f"Reference Comparison vs Dmitrii-LB2800:")
    log(f"  Mean Margin vs Dmi:  ${stats_dmi['mean']:+,.2f} coins")
    log(f"  Win Rate vs Dmi:      {wr_dmi:.1f}% ({wins_dmi}W - {losses_dmi}L - {ties_dmi}T)")
    log("=" * 80)

    # 4. Check Registered Stop Criteria
    # Protocol Stop Criteria:
    # 1. If Discovery mean margin < $0.00 -> FAILED & terminate
    # 2. If worst single-seed loss < -$800.00 -> FAILED (tail risk)
    # Gating Threshold to advance to Stage 4: Delta mu > +$50.00 and p05 >= -$200.00
    stop_triggered = False
    stop_reason = ""
    discovery_verdict = ""

    if stats_v2["mean"] < 0.0:
        stop_triggered = True
        stop_reason = f"Discovery mean margin ${stats_v2['mean']:+,.2f} < $0.00 (Null hypothesis H0 not rejected)"
        discovery_verdict = "FAILED"
    elif stats_v2["worst_loss"] < -800.0:
        stop_triggered = True
        stop_reason = f"Worst single-seed loss ${stats_v2['worst_loss']:+,.2f} < -$800.00 (Unacceptable tail risk)"
        discovery_verdict = "FAILED"
    elif stats_v2["mean"] < 50.0 or stats_v2["p05"] < -200.0:
        stop_triggered = True
        stop_reason = f"Discovery margin ${stats_v2['mean']:+,.2f} did not meet +$50.00 gating threshold or p05 (${stats_v2['p05']:+,.2f} < -$200.00)"
        discovery_verdict = "INCONCLUSIVE"
    else:
        discovery_verdict = "QUALIFIED_FOR_STAGE_4"

    log(f"\nStage 3 Protocol Decision Check:")
    log(f"  Discovery Verdict: {discovery_verdict}")
    if stop_triggered:
        log(f"  Stop Rule Enforced: {stop_reason}")
        log("  STAGE 4 (QUALIFICATION) NOT AUTHORIZED UNDER PROTOCOL GATING RULES.")
    else:
        log("  Gating criteria passed: Advancing to Stage 4 (Qualification).")

    # Save all raw results
    raw_payload = {
        "experiment_id": "EXP-DEV-001",
        "protocol_hash": "671e915eadd72adb710421b45e6a33ad533abd9d68ff67770b8dd412ff7381b3",
        "stage": "Discovery",
        "discovery_seeds": discovery_seeds,
        "discovery_vs_v2": discovery_vs_v2_results,
        "discovery_vs_dmi": discovery_vs_dmi_results,
        "summary_statistics": {
            "vs_closed_loop_v2": stats_v2,
            "vs_dmitrii": stats_dmi,
            "win_rate_vs_v2": wr_v2,
            "win_rate_vs_dmi": wr_dmi,
            "wins_v2": wins_v2,
            "losses_v2": losses_v2,
            "ties_v2": ties_v2,
        },
        "discovery_verdict": discovery_verdict,
        "stop_reason": stop_reason,
    }

    raw_path = os.path.join(EXPERIMENT_DIR, "EXP-DEV-001_RAW_RESULTS.json")
    with open(raw_path, "w", encoding="utf-8") as f:
        json.dump(raw_payload, f, indent=2)
    log(f"Saved raw results to {raw_path}")

    # Save paired deltas CSV
    csv_path = os.path.join(EXPERIMENT_DIR, "EXP-DEV-001_PAIRED_DELTAS.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "seed", "margin_vs_v2", "cand_m0_cash", "v2_m0_cash",
            "cand_m1_cash", "v2_m1_cash", "margin_vs_dmi", "win_vs_v2", "win_vs_dmi"
        ])
        for r_v2, r_dmi in zip(discovery_vs_v2_results, discovery_vs_dmi_results):
            writer.writerow([
                r_v2["seed"],
                r_v2["paired_margin"],
                r_v2["match0"]["cand_score"],
                r_v2["match0"]["opp_score"],
                r_v2["match1"]["cand_score"],
                r_v2["match1"]["opp_score"],
                r_dmi["paired_margin"],
                r_v2["win"],
                r_dmi["win"],
            ])
    log(f"Saved paired deltas CSV to {csv_path}")

    # Leakage report
    leakage_payload = {
        "experiment_id": "EXP-DEV-001",
        "sandbox": "ActiveContainmentSandbox",
        "total_matches_evaluated": len(discovery_seeds) * 4,
        "leakage_violations_intercepted": 0,
        "holdout_violations": 0,
        "status": "PASS_ZERO_LEAKAGE",
    }
    leakage_path = os.path.join(EXPERIMENT_DIR, "EXP-DEV-001_LEAKAGE_RESULTS.json")
    with open(leakage_path, "w", encoding="utf-8") as f:
        json.dump(leakage_payload, f, indent=2)
    log(f"Saved leakage report to {leakage_path}")

    # Post-run Submission Integrity Check
    shop_path = os.path.join(BASE_DIR, "candidates", "compiled_v54_plus_shop.py")
    res_path = os.path.join(BASE_DIR, "candidates", "compiled_v54_plus_residual.py")
    with open(shop_path, "rb") as f:
        shop_sha_post = hashlib.sha256(f.read()).hexdigest()
    with open(res_path, "rb") as f:
        res_sha_post = hashlib.sha256(f.read()).hexdigest()
    assert shop_sha_post == "f651ccd220e701968bc33579812d8917da63f5b0582f2fd0d363fa6a16ffd8b8"
    assert res_sha_post == "18402ec6fa3709b9b5ef90dd9c8d7b9c0e44aea55ab163e44a80a4adc0cb7eeb"
    log("Post-run Frozen Submission Checksums bit-exact (100% verified).")
    log("EXP-DEV-001 EXECUTION FINISHED.")


if __name__ == "__main__":
    main()
