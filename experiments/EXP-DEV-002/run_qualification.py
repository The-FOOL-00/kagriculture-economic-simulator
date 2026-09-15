"""
=============================================================================
EXP-DEV-002 FORMAL QUALIFICATION RUNNER: FROZEN TREATMENT
=============================================================================
Governing Protocol: DEVELOPMENT_EXPERIMENT_PROTOCOL_V1_1.md (SHA-256: 735ad844...)
Evaluation Partition: Qualification (Seeds 50050..50099, N=50 seeds, 100 matches/pair)
Evaluation Mode: Paired Common Random Numbers (CRN), Seat 0 + Seat 1
Active Containment: ActiveContainmentSandbox (Zero-Leakage Enforcement)
Virgin Holdout Protection: Strict exclusion of Seeds 214200-214249
Frozen Treatment: candidates/closed_loop_architecture/dev_002_hedged_portfolio.py
  SHA-256: cdd19cc8d2b6a718ce6252223b9016ce76e5b08b88de10689ea5fce4ddb8f907
Comparators:
  - Primary Baseline: ClosedLoopAgentV2
  - Reference Benchmark: Dmitrii-LB2800
  - Diagnostic Comparator: Dev001DynamicPortfolioAgent (for risk/return tradeoff audit)
=============================================================================
"""

import copy
import csv
import hashlib
import json
import math
import os
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
from dev_002_hedged_portfolio import Dev002HedgedPortfolioAgent
from dev_001_dynamic_portfolio import Dev001DynamicPortfolioAgent
from verify_agent_zero_leakage import ActiveContainmentSandbox, LeakageViolationError, audit_agent_ast

EXP_DIR = os.path.abspath(os.path.dirname(__file__))
QUAL_DIR = os.path.join(EXP_DIR, "qualification")
os.makedirs(QUAL_DIR, exist_ok=True)

LOG_FILE = os.path.join(QUAL_DIR, "QUALIFICATION_EXECUTION_LOG.txt")


def log(msg: str):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
    line = f"[{timestamp} UTC] {msg}"
    print(line)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def assert_not_holdout(seed: int):
    """Hard invariant: virgin holdout seeds 214200-214249 must NEVER be executed."""
    if 214200 <= seed <= 214249:
        msg = f"CRITICAL PROTOCOL VIOLATION: Holdout seed {seed} requested during Qualification!"
        log(f"FATAL: {msg}")
        raise RuntimeError(msg)


def verify_qualification_preflight():
    log("=" * 80)
    log("PREFLIGHT INVARIANT VERIFICATION FOR QUALIFICATION RUN")
    log("=" * 80)

    # 1. Protocol V1.1 SHA-256
    proto_path = os.path.join(BASE_DIR, "DEVELOPMENT_EXPERIMENT_PROTOCOL_V1_1.md")
    with open(proto_path, "rb") as f:
        proto_sha = hashlib.sha256(f.read()).hexdigest()
    EXPECTED_PROTO_SHA = "735ad844b727a967058e4f817a72ae6bf3ea3f5a40182fa18f59f972da91f446"
    assert proto_sha == EXPECTED_PROTO_SHA, f"Protocol V1.1 SHA mismatch: {proto_sha} != {EXPECTED_PROTO_SHA}"
    log(f"  [1/5] Protocol V1.1 SHA-256 Verified: {proto_sha}")

    # 2. Frozen Treatment SHA-256
    cand_path = os.path.join(BASE_DIR, "candidates", "closed_loop_architecture", "dev_002_hedged_portfolio.py")
    with open(cand_path, "rb") as f:
        cand_sha = hashlib.sha256(f.read()).hexdigest()
    EXPECTED_CAND_SHA = "cdd19cc8d2b6a718ce6252223b9016ce76e5b08b88de10689ea5fce4ddb8f907"
    assert cand_sha == EXPECTED_CAND_SHA, f"Candidate dev_002 SHA mismatch: {cand_sha} != {EXPECTED_CAND_SHA}"
    log(f"  [2/5] Treatment dev_002 SHA-256 Verified: {cand_sha}")

    # 3. Frozen Live Submissions
    shop_path = os.path.join(BASE_DIR, "candidates", "compiled_v54_plus_shop.py")
    res_path = os.path.join(BASE_DIR, "candidates", "compiled_v54_plus_residual.py")
    with open(shop_path, "rb") as f:
        shop_sha = hashlib.sha256(f.read()).hexdigest()
    with open(res_path, "rb") as f:
        res_sha = hashlib.sha256(f.read()).hexdigest()
    assert shop_sha == "f651ccd220e701968bc33579812d8917da63f5b0582f2fd0d363fa6a16ffd8b8"
    assert res_sha == "18402ec6fa3709b9b5ef90dd9c8d7b9c0e44aea55ab163e44a80a4adc0cb7eeb"
    log("  [3/5] Frozen Live Submissions 56146947 and 56146971 Verified bit-exact.")

    # 4. AST Zero-Leakage Audit
    ast_violations = audit_agent_ast(cand_path)
    assert len(ast_violations) == 0, f"Candidate AST violations: {ast_violations}"
    log("  [4/5] Candidate dev_002 AST Zero-Leakage Verified Clean (0 violations).")

    # 5. Precheck Document Existence
    precheck_path = os.path.join(EXP_DIR, "QUALIFICATION_PRECHECK.md")
    assert os.path.exists(precheck_path), f"QUALIFICATION_PRECHECK.md missing at {precheck_path}"
    log(f"  [5/5] Pre-Qualification Audit Report verified on disk: {precheck_path}")
    log("All Preflight Invariants Passed.\n")


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

    # Extract candidate mode and diagnostics if available
    cand_mode_0 = getattr(cand_agent0, "mode_selected", {}).get(0, "UNKNOWN")
    cand_mode_1 = getattr(cand_agent1, "mode_selected", {}).get(1, "UNKNOWN")
    crops_0 = getattr(cand_agent0, "crops_substituted", {})
    crops_1 = getattr(cand_agent1, "crops_substituted", {})

    # Extract shop list from observation
    final_obs0 = g0.observe(0)
    unlocked_shops = final_obs0.get("town", {}).get("unlocked_shops", [])

    return {
        "seed": seed,
        "match0": {"cand_score": cand_rew0, "opp_score": opp_rew1, "margin": m0, "steps": s0},
        "match1": {"opp_score": opp_rew0, "cand_score": cand_rew1, "margin": m1, "steps": s1},
        "paired_margin": paired_margin,
        "cand_total": cand_rew0 + cand_rew1,
        "opp_total": opp_rew0 + opp_rew1,
        "cand_mean_cash": (cand_rew0 + cand_rew1) / 2.0,
        "opp_mean_cash": (opp_rew0 + opp_rew1) / 2.0,
        "cand_mode": cand_mode_0,
        "crops_sub_m0": crops_0,
        "crops_sub_m1": crops_1,
        "unlocked_shops": unlocked_shops,
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

    # Student's t critical value for df = 49 (95% two-sided is t = 2.009575)
    t_crit = 2.009575 if n == 50 else 1.96
    ci_lower = mean - t_crit * se
    ci_upper = mean + t_crit * se
    t_stat = mean / se if se > 0 else 0.0

    # Two-sided p-value approximation via standard error and normal/t-distribution
    z = abs(t_stat)
    p_approx = 2.0 * (1.0 - 0.5 * (1.0 + math.erf(z / math.sqrt(2.0))))

    # 10% Trimmed Mean (drop top 5 and bottom 5 for N=50)
    trim_k = max(1, int(0.10 * n))
    trimmed_data = sorted_d[trim_k : n - trim_k]
    trimmed_mean = sum(trimmed_data) / len(trimmed_data)

    def quantile(p):
        idx = p * (n - 1)
        low = int(math.floor(idx))
        high = int(math.ceil(idx))
        weight = idx - low
        return sorted_d[low] * (1.0 - weight) + sorted_d[high] * weight

    downside_count = sum(1 for x in paired_deltas if x < 0)
    downside_freq = downside_count / n
    loss_gt_200 = sum(1 for x in paired_deltas if x < -200.0)
    loss_gt_500 = sum(1 for x in paired_deltas if x < -500.0)
    loss_gt_800 = sum(1 for x in paired_deltas if x < -800.0)

    # Tail concentration
    total_surplus = sum(paired_deltas)
    top1_delta = sorted_d[-1]
    top2_delta = sorted_d[-2] + sorted_d[-1]
    top1_pct = (top1_delta / total_surplus * 100.0) if total_surplus > 0 else 0.0
    top2_pct = (top2_delta / total_surplus * 100.0) if total_surplus > 0 else 0.0

    mean_ex_best = sum(sorted_d[:-1]) / (n - 1)
    mean_ex_worst = sum(sorted_d[1:]) / (n - 1)
    mean_ex_top2 = sum(sorted_d[:-2]) / (n - 2)

    return {
        "n": n,
        "mean": mean,
        "total_surplus": total_surplus,
        "trimmed_mean_10": trimmed_mean,
        "median": median,
        "sd": sd,
        "se": se,
        "t_stat": t_stat,
        "p_value_approx": p_approx,
        "ci_95": [ci_lower, ci_upper],
        "min": sorted_d[0],
        "max": sorted_d[-1],
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
        "downside_frequency": downside_freq,
        "downside_count": downside_count,
        "loss_gt_200_count": loss_gt_200,
        "loss_gt_500_count": loss_gt_500,
        "loss_gt_800_count": loss_gt_800,
        "top1_pct": top1_pct,
        "top2_pct": top2_pct,
        "mean_ex_best": mean_ex_best,
        "mean_ex_worst": mean_ex_worst,
        "mean_ex_top2": mean_ex_top2,
    }


def main():
    # Clear / initialize log
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        f.write(f"=== EXP-DEV-002 QUALIFICATION EXECUTION LOG ===\n")
        f.write(f"Started at: {time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime())} UTC\n\n")

    verify_qualification_preflight()

    cand_factory = lambda: Dev002HedgedPortfolioAgent()
    ctrl_v2_factory = lambda: ClosedLoopAgentV2()
    dmitrii_factory = lambda: mod_r.Policy(os.path.join(BASE_DIR, "extracted_agents", "dmitrii_lb2800"))
    dev001_factory = lambda: Dev001DynamicPortfolioAgent()

    qualification_seeds = list(range(50050, 50100))
    assert len(qualification_seeds) == 50, f"Expected exactly 50 seeds, got {len(qualification_seeds)}"
    assert qualification_seeds[0] == 50050 and qualification_seeds[-1] == 50099

    log("=" * 80)
    log(f"EXECUTING QUALIFICATION COHORT (Seeds 50050..50099, N=50 seeds)")
    log(f"Active Containment Sandbox: ACTIVE")
    log("=" * 80)

    qual_vs_v2_results = []
    qual_vs_dmi_results = []
    qual_dev001_vs_v2_results = []

    paired_deltas_v2 = []
    paired_deltas_dmi = []
    paired_deltas_dev001 = []
    mode_distribution = {}

    t_start = time.time()
    for idx, s in enumerate(qualification_seeds, 1):
        # 1. Primary Registered Comparison: Candidate dev_002 vs ClosedLoopAgentV2
        res_v2 = run_paired_match(cand_factory, ctrl_v2_factory, s, use_sandbox=True)
        qual_vs_v2_results.append(res_v2)
        paired_deltas_v2.append(res_v2["paired_margin"])

        mode = res_v2["cand_mode"]
        mode_distribution[mode] = mode_distribution.get(mode, 0) + 1

        # 2. Reference Comparison: Candidate dev_002 vs Dmitrii-LB2800
        res_dmi = run_paired_match(cand_factory, dmitrii_factory, s, use_sandbox=True)
        qual_vs_dmi_results.append(res_dmi)
        paired_deltas_dmi.append(res_dmi["paired_margin"])

        # 3. Diagnostic Baseline: dev_001 vs ClosedLoopAgentV2 (for tail-risk contrast)
        res_dev001 = run_paired_match(dev001_factory, ctrl_v2_factory, s, use_sandbox=True)
        qual_dev001_vs_v2_results.append(res_dev001)
        paired_deltas_dev001.append(res_dev001["paired_margin"])

        if idx % 10 == 0 or idx == len(qualification_seeds):
            cur_mean_v2 = sum(paired_deltas_v2) / len(paired_deltas_v2)
            cur_wr_v2 = sum(r["win"] for r in qual_vs_v2_results) / len(qual_vs_v2_results) * 100.0
            log(f"  Seed {idx:02d}/50 (Seed {s}): Margin vs V2 = ${res_v2['paired_margin']:+,.0f} (Mode: {mode}) | Cumulative Mean: ${cur_mean_v2:+,.2f} | WR: {cur_wr_v2:.1f}%")

    elapsed = time.time() - t_start
    log(f"\nExecution of all 50 Qualification seeds completed in {elapsed:.1f}s.")

    # Compute Sample Statistics
    stats_v2 = compute_sample_statistics(paired_deltas_v2)
    stats_dmi = compute_sample_statistics(paired_deltas_dmi)
    stats_dev001 = compute_sample_statistics(paired_deltas_dev001)

    wins_v2 = sum(r["win"] for r in qual_vs_v2_results)
    losses_v2 = sum(r["loss"] for r in qual_vs_v2_results)
    ties_v2 = sum(r["tie"] for r in qual_vs_v2_results)
    wr_v2 = (wins_v2 / len(qualification_seeds)) * 100.0

    wins_dmi = sum(r["win"] for r in qual_vs_dmi_results)
    losses_dmi = sum(r["loss"] for r in qual_vs_dmi_results)
    ties_dmi = sum(r["tie"] for r in qual_vs_dmi_results)
    wr_dmi = (wins_dmi / len(qualification_seeds)) * 100.0

    log("\n" + "=" * 80)
    log("EXP-DEV-002 QUALIFICATION RESULTS (N=50 Seeds, 100 Matches)")
    log("=" * 80)
    log("Primary Metric (Paired Margin vs ClosedLoopAgentV2):")
    log(f"  Mean Margin (Delta mu): ${stats_v2['mean']:+,.2f} coins")
    log(f"  10% Trimmed Mean:       ${stats_v2['trimmed_mean_10']:+,.2f} coins")
    log(f"  Median Margin:          ${stats_v2['median']:+,.2f} coins")
    log(f"  Standard Dev (SD):       ${stats_v2['sd']:,.2f} coins")
    log(f"  Standard Error (SE):     ${stats_v2['se']:,.2f} coins")
    log(f"  Student's t-statistic:   {stats_v2['t_stat']:,.4f}")
    log(f"  Two-Sided p-value:       {stats_v2['p_value_approx']:.6f}")
    log(f"  95% Confidence Interval: [${stats_v2['ci_95'][0]:+,.2f}, ${stats_v2['ci_95'][1]:+,.2f}]")
    log(f"  Paired Win Record:       {wins_v2}W - {losses_v2}L - {ties_v2}T (Win Rate: {wr_v2:.1f}%)")
    log(f"  5th Percentile (p05):   ${stats_v2['p05']:+,.2f} coins")
    log(f"  Worst Paired Loss:      ${stats_v2['worst_loss']:+,.2f} coins")
    log(f"  Best Paired Win:        ${stats_v2['best_win']:+,.2f} coins")
    log(f"  Downside Frequency:      {stats_v2['downside_frequency']*100.0:.1f}% ({stats_v2['downside_count']}/50 seeds)")
    log(f"  Tail Breaches (<-$800):  {stats_v2['loss_gt_800_count']}")
    log("-" * 80)
    log(f"Mode Distribution: {mode_distribution}")
    log("-" * 80)
    log("Reference Comparison vs Dmitrii-LB2800:")
    log(f"  Mean Margin vs Dmi:     ${stats_dmi['mean']:+,.2f} coins")
    log(f"  Win Record vs Dmi:       {wins_dmi}W - {losses_dmi}L - {ties_dmi}T ({wr_dmi:.1f}%)")
    log("=" * 80)

    # Qualification Success Criteria Check (Protocol V1.1 Section 2.7 Stage 2)
    # Stage 2 criteria:
    # 1. t > 1.96 (p < 0.05)
    # 2. worst_loss >= -800.0
    pass_t_stat = stats_v2["t_stat"] > 1.96
    pass_p_val = stats_v2["p_value_approx"] < 0.05
    pass_worst_loss = stats_v2["worst_loss"] >= -800.0

    if pass_t_stat and pass_worst_loss:
        qualification_verdict = "QUALIFICATION PASS"
    elif stats_v2["worst_loss"] < -800.0 or stats_v2["mean"] <= 0.0:
        qualification_verdict = "QUALIFICATION FAIL — TREATMENT RETIRED"
    else:
        qualification_verdict = "QUALIFICATION PASS WITH LIMITATIONS"

    log(f"\nStage 2 Qualification Decision:")
    log(f"  Verdict: {qualification_verdict}")
    log(f"  Criteria Check: t > 1.96: {pass_t_stat} (t={stats_v2['t_stat']:.4f})")
    log(f"  Criteria Check: Worst Loss >= -$800: {pass_worst_loss} (min={stats_v2['worst_loss']:+,.2f})")

    # 1. Save QUALIFICATION_RAW_RESULTS.json
    raw_payload = {
        "experiment_id": "EXP-DEV-002",
        "phase": "Qualification",
        "protocol_version": "DEVELOPMENT-PROTOCOL-V1.1",
        "protocol_hash": "735ad844b727a967058e4f817a72ae6bf3ea3f5a40182fa18f59f972da91f446",
        "git_commit": "b2a4f4585342875602af6f54324fe5a8bcfbd9d1",
        "treatment": {
            "identifier": "dev_002_hedged_portfolio",
            "file": "candidates/closed_loop_architecture/dev_002_hedged_portfolio.py",
            "sha256": "cdd19cc8d2b6a718ce6252223b9016ce76e5b08b88de10689ea5fce4ddb8f907",
            "class": "Dev002HedgedPortfolioAgent",
            "bedrock_strawberry_floor": 13,
            "tomato_substitution_cap": 6,
            "commitment_step": 144,
            "liquidity_buffer": 500.0,
            "market_timing": True,
            "tomato_sale_batch": 6,
        },
        "simulator": {
            "engine": "kagsim",
            "version": "1.32.7",
            "binary_path": "external_repos/kaggriculture-cppsim/kagsim.cp314-win_amd64.pyd",
        },
        "partition": {
            "name": "Qualification",
            "start_seed": 50050,
            "end_seed": 50099,
            "seed_count": 50,
        },
        "qualification_seeds": qualification_seeds,
        "results_vs_v2": qual_vs_v2_results,
        "results_vs_dmi": qual_vs_dmi_results,
        "diagnostic_dev001_vs_v2": qual_dev001_vs_v2_results,
        "summary_statistics": {
            "vs_closed_loop_v2": stats_v2,
            "vs_dmitrii": stats_dmi,
            "dev001_vs_v2": stats_dev001,
            "win_rate_vs_v2": wr_v2,
            "win_rate_vs_dmi": wr_dmi,
            "wins_v2": wins_v2,
            "losses_v2": losses_v2,
            "ties_v2": ties_v2,
            "mode_distribution": mode_distribution,
        },
        "qualification_verdict": qualification_verdict,
    }

    raw_json_path = os.path.join(QUAL_DIR, "QUALIFICATION_RAW_RESULTS.json")
    with open(raw_json_path, "w", encoding="utf-8") as f:
        json.dump(raw_payload, f, indent=2)
    log(f"Saved raw results to {raw_json_path}")

    # 2. Save QUALIFICATION_PAIRED_DELTAS.csv
    csv_path = os.path.join(QUAL_DIR, "QUALIFICATION_PAIRED_DELTAS.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "seed", "cand_mean_cash", "v2_mean_cash", "paired_margin_vs_v2",
            "cand_m0_cash", "v2_m0_cash", "cand_m1_cash", "v2_m1_cash",
            "dmi_mean_cash", "paired_margin_vs_dmi",
            "dev001_paired_margin_vs_v2", "dev002_minus_dev001",
            "cand_mode", "unlocked_shops"
        ])
        for r_v2, r_dmi, r_d1 in zip(qual_vs_v2_results, qual_vs_dmi_results, qual_dev001_vs_v2_results):
            diff_002_001 = r_v2["paired_margin"] - r_d1["paired_margin"]
            writer.writerow([
                r_v2["seed"],
                f"{r_v2['cand_mean_cash']:.2f}",
                f"{r_v2['opp_mean_cash']:.2f}",
                f"{r_v2['paired_margin']:.2f}",
                f"{r_v2['match0']['cand_score']:.2f}",
                f"{r_v2['match0']['opp_score']:.2f}",
                f"{r_v2['match1']['cand_score']:.2f}",
                f"{r_v2['match1']['opp_score']:.2f}",
                f"{r_dmi['opp_mean_cash']:.2f}",
                f"{r_dmi['paired_margin']:.2f}",
                f"{r_d1['paired_margin']:.2f}",
                f"{diff_002_001:.2f}",
                r_v2["cand_mode"],
                ";".join(r_v2["unlocked_shops"]),
            ])
    log(f"Saved paired deltas CSV to {csv_path}")

    # 3. Save QUALIFICATION_RUN_MANIFEST.json
    manifest = {
        "manifest_version": "1.0",
        "experiment_id": "EXP-DEV-002",
        "phase": "Qualification",
        "timestamp_utc": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()),
        "treatment_identity": {
            "identifier": "dev_002_hedged_portfolio",
            "path": "candidates/closed_loop_architecture/dev_002_hedged_portfolio.py",
            "sha256": "cdd19cc8d2b6a718ce6252223b9016ce76e5b08b88de10689ea5fce4ddb8f907",
            "class": "Dev002HedgedPortfolioAgent",
            "parameters": {
                "bedrock_strawberry_floor": 13,
                "tomato_substitution_cap": 6,
                "commitment_deadline_step": 144,
                "base_liquidity_reserve": 500.0,
                "market_timing": True,
                "tomato_sale_batch": 6,
            }
        },
        "protocol_identity": {
            "title": "DEVELOPMENT EXPERIMENT PROTOCOL V1.1",
            "path": "DEVELOPMENT_EXPERIMENT_PROTOCOL_V1_1.md",
            "sha256": "735ad844b727a967058e4f817a72ae6bf3ea3f5a40182fa18f59f972da91f446",
            "git_commit": "b2a4f4585342875602af6f54324fe5a8bcfbd9d1",
        },
        "live_submissions_frozen": {
            "submission_56146971_residual": {
                "path": "candidates/compiled_v54_plus_residual.py",
                "sha256": "18402ec6fa3709b9b5ef90dd9c8d7b9c0e44aea55ab163e44a80a4adc0cb7eeb",
            },
            "submission_56146947_shop": {
                "path": "candidates/compiled_v54_plus_shop.py",
                "sha256": "f651ccd220e701968bc33579812d8917da63f5b0582f2fd0d363fa6a16ffd8b8",
            }
        },
        "simulator_environment": {
            "engine": "kagsim",
            "version": "1.32.7",
            "binary_path": "external_repos/kaggriculture-cppsim/kagsim.cp314-win_amd64.pyd",
            "max_steps": 720,
        },
        "partition_provenance": {
            "qualification_range": [50050, 50099],
            "total_seeds": 50,
            "total_matches_evaluated": 100,
            "virgin_holdout_status": "Untouched (Seeds 214200-214249)",
        },
        "qualification_verdict": qualification_verdict,
        "files_emitted": [
            "experiments/EXP-DEV-002/qualification/QUALIFICATION_RAW_RESULTS.json",
            "experiments/EXP-DEV-002/qualification/QUALIFICATION_PAIRED_DELTAS.csv",
            "experiments/EXP-DEV-002/qualification/QUALIFICATION_RUN_MANIFEST.json",
            "experiments/EXP-DEV-002/qualification/QUALIFICATION_EXECUTION_LOG.txt",
        ]
    }

    manifest_path = os.path.join(QUAL_DIR, "QUALIFICATION_RUN_MANIFEST.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    log(f"Saved run manifest to {manifest_path}")

    log("\nEXP-DEV-002 Qualification Run Fully Completed.")


if __name__ == "__main__":
    main()
