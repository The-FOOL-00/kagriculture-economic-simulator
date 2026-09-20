#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""AEC Phase 010: Scientific Mechanism Qualification & Replication Harness.

Executes paired Common Random Numbers (CRN) mirror matches to rigorously isolate
and qualify transformational mechanisms against the frozen AEC foundation.

Adheres strictly to:
1. Phase 009 Architecture Freeze (no architectural additions).
2. Touchless Holdout Protection Covenant (zero touches of protected cohorts).
3. Bit-identical V3 chassis preservation.
4. Single-mechanism isolation protocol.
"""

from __future__ import annotations

import argparse
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

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

import kagsim
from aec.config import (
    AECConfig,
    ENABLED_FOUNDATION_MECHANISMS,
    QUARANTINED_MECHANISMS,
    ScientificStatus,
)
from aec.integration.executor import AECExecutor

V3_TARBALL_PATH = os.path.join(REPO_ROOT, "submission_Vj_kc_v3.tar.gz")
V3_EXPECTED_SHA256 = "845e0d10981b11b06d272048ff5cee30d70a0403dd757651a556a78c8bf18943"

# Official Preregistered Seed Partitions
PARTITIONS: Dict[str, List[int]] = {
    "pilot": list(range(249050, 249060)),        # N=10 seeds (Stage A Pilot)
    "formal_q1": list(range(249060, 249085)),    # N=25 seeds (Stage B Formal Group A)
    "replicate_q2": list(range(249085, 249110)), # N=25 seeds (Replication / Formal Group B)
    "formal_q3": list(range(249110, 249135)),    # N=25 seeds (Group C Formal)
    "formal_q4": list(range(249135, 249160)),    # N=25 seeds (Group D Formal)
    "formal_q5": list(range(249160, 249185)),    # N=25 seeds (Group E Formal)
    "integrated_r1": list(range(249185, 249210)),# N=25 seeds (Integrated Regression)
}


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
    # 4. Retired Development Cohorts
    if 50000 <= seed <= 50024 or 249000 <= seed <= 249049:
        raise RuntimeError(f"FATAL GOVERNANCE BREACH: Retired cohort seed {seed} re-used!")

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


def build_configs_for_mechanism(mechanism: str) -> Tuple[AECConfig, AECConfig]:
    """Returns (control_config, treatment_config)."""
    # Baseline control configuration
    ctrl_cfg = AECConfig(
        enabled_mechanisms=ENABLED_FOUNDATION_MECHANISMS,
        quarantined_mechanisms=QUARANTINED_MECHANISMS,
        frozen_mode=True
    )

    if mechanism == "NONE":
        # Pure baseline identity test
        return ctrl_cfg, ctrl_cfg

    if mechanism == "META":
        trt_cfg = AECConfig(
            operational_mode="META_MODE",
            enabled_mechanisms=ENABLED_FOUNDATION_MECHANISMS,
            quarantined_mechanisms=QUARANTINED_MECHANISMS,
            frozen_mode=True
        )
        return ctrl_cfg, trt_cfg

    # Single mechanism treatment arm
    new_enabled = tuple(list(ENABLED_FOUNDATION_MECHANISMS) + [mechanism])
    new_quarantined = tuple(m for m in QUARANTINED_MECHANISMS if m != mechanism)

    trt_cfg = AECConfig(
        enabled_mechanisms=new_enabled,
        quarantined_mechanisms=new_quarantined,
        frozen_mode=True
    )
    return ctrl_cfg, trt_cfg


def run_mirror_match(
    seed: int,
    treatment_seat: int,
    treatment_executor: AECExecutor,
    control_agent: Any,
    target_mechanism: str
) -> Dict[str, Any]:
    """Runs one match of treatment vs control."""
    assert_governance(seed)
    game = kagsim.Game(seed)
    latencies: List[float] = []

    while not game.done:
        obs0 = game.observe(0)
        obs1 = game.observe(1)

        t0 = time.perf_counter()
        if treatment_seat == 0:
            act0 = treatment_executor.act(obs0)
            lat_ms = (time.perf_counter() - t0) * 1000.0
            act1 = control_agent.act(obs1)
        else:
            act0 = control_agent.act(obs0)
            t0 = time.perf_counter()
            act1 = treatment_executor.act(obs1)
            lat_ms = (time.perf_counter() - t0) * 1000.0

        latencies.append(lat_ms)
        game.step(act0, act1)

    r0 = float(game.reward(0))
    r1 = float(game.reward(1))

    treatment_reward = r0 if treatment_seat == 0 else r1
    control_reward = r1 if treatment_seat == 0 else r0
    margin = treatment_reward - control_reward

    telemetry_history = getattr(treatment_executor, "_telemetry_history", [])
    total_opportunities = sum(t.opportunities_count for t in telemetry_history)
    total_candidates = sum(len(t.candidates) for t in telemetry_history)
    total_simulations = sum(t.simulations_run for t in telemetry_history)
    committed = sum(1 for t in telemetry_history if t.decision == "COMMIT")
    abstained = sum(1 for t in telemetry_history if t.decision == "ABSTAIN")
    fallback_count = getattr(treatment_executor, "fallback_policy", None).fallback_count if hasattr(treatment_executor, "fallback_policy") else 0

    # Specific target mechanism tracking
    target_opps = 0
    target_candidates = 0
    target_sims = 0
    target_commits = 0
    foundation_commits = 0

    commits_by_mech: Dict[str, int] = {}
    quarantined_by_mech: Dict[str, int] = {}

    predicted_deltas: List[float] = []

    for t in telemetry_history:
        for c in t.candidates:
            if getattr(c, "mechanism_family", "") == target_mechanism:
                target_candidates += 1
                pred_delta = getattr(c, "delta_margin", getattr(c, "delta_money", 0.0))
                predicted_deltas.append(pred_delta)

        if t.decision == "COMMIT":
            mech = t.committed_mechanism or ""
            commits_by_mech[mech] = commits_by_mech.get(mech, 0) + 1
            if mech == target_mechanism:
                target_commits += 1
            elif mech in ENABLED_FOUNDATION_MECHANISMS:
                foundation_commits += 1

        for fam, cnt in getattr(t, "quarantined_by_mechanism", {}).items():
            quarantined_by_mech[fam] = quarantined_by_mech.get(fam, 0) + cnt

    return {
        "seed": seed,
        "seat": treatment_seat,
        "treatment_reward": treatment_reward,
        "control_reward": control_reward,
        "margin": margin,
        "win": margin > 0,
        "loss": margin < 0,
        "tie": margin == 0,
        "latency_p50": float(np.percentile(latencies, 50)) if latencies else 0.0,
        "latency_p95": float(np.percentile(latencies, 95)) if latencies else 0.0,
        "worst_turn_ms": float(np.max(latencies)) if latencies else 0.0,
        "total_opportunities": total_opportunities,
        "total_candidates": total_candidates,
        "total_simulations": total_simulations,
        "committed": committed,
        "abstained": abstained,
        "fallback_count": fallback_count,
        "target_mechanism": target_mechanism,
        "target_candidates": target_candidates,
        "target_commits": target_commits,
        "foundation_commits": foundation_commits,
        "commits_by_mech": commits_by_mech,
        "quarantined_by_mech": quarantined_by_mech,
        "mean_predicted_delta": float(np.mean(predicted_deltas)) if predicted_deltas else 0.0,
    }


def execute_qualification(
    mechanism: str,
    seeds: List[int],
    stage_name: str,
    output_csv: Optional[str] = None,
    output_json: Optional[str] = None
) -> Dict[str, Any]:
    """Executes mirror matches across seeds and compiles statistical summary."""
    print("=" * 70, flush=True)
    print(f"AEC PHASE 010: MECHANISM QUALIFICATION EXPERIMENT", flush=True)
    print("=" * 70, flush=True)
    print(f"Mechanism Under Evaluation : {mechanism}", flush=True)
    print(f"Testing Stage              : {stage_name.upper()}", flush=True)
    print(f"Seed Cohort                : {seeds[0]}..{seeds[-1]} (N={len(seeds)} seeds, {len(seeds)*2} matches)", flush=True)
    print("=" * 70, flush=True)

    # Pre-flight governance checks
    for s in seeds:
        assert_governance(s)
    print("  [OK] Pre-flight Governance: All seeds verified clean, zero protected overlap.", flush=True)
    print(f"  [OK] Chassis Hash Verified: {V3_EXPECTED_SHA256[:16]}...", flush=True)

    ctrl_cfg, trt_cfg = build_configs_for_mechanism(mechanism)
    print(f"  [OK] Active Foundation: {list(trt_cfg.enabled_mechanisms)}", flush=True)
    print(f"  [OK] Quarantined Set  : {len(trt_cfg.quarantined_mechanisms)} mechanisms quarantined", flush=True)

    matches_data: List[Dict[str, Any]] = []
    seed_deltas: List[float] = []

    t_start = time.time()

    for idx, seed in enumerate(seeds):
        t_seed = time.time()

        # Match A: Treatment as Seat 0, Control as Seat 1
        exec_t0 = AECExecutor(config=trt_cfg)
        ctrl_1 = FrozenV3ControlAgent()
        res_m1 = run_mirror_match(seed, treatment_seat=0, treatment_executor=exec_t0, control_agent=ctrl_1, target_mechanism=mechanism)
        matches_data.append(res_m1)

        # Match B: Control as Seat 0, Treatment as Seat 1
        exec_t1 = AECExecutor(config=trt_cfg)
        ctrl_0 = FrozenV3ControlAgent()
        res_m2 = run_mirror_match(seed, treatment_seat=1, treatment_executor=exec_t1, control_agent=ctrl_0, target_mechanism=mechanism)
        matches_data.append(res_m2)

        net_delta = (res_m1["margin"] + res_m2["margin"]) / 2.0
        seed_deltas.append(net_delta)

        tot_target_commits = res_m1["target_commits"] + res_m2["target_commits"]
        tot_all_commits = res_m1["committed"] + res_m2["committed"]

        print(f"[{idx+1:02d}/{len(seeds)}] Seed {seed}: S0={res_m1['margin']:+.0f}, S1={res_m2['margin']:+.0f} | NetDelta={net_delta:+.1f} | MechCommits={tot_target_commits} (Tot={tot_all_commits}) | ({time.time()-t_seed:.1f}s)", flush=True)

    elapsed = time.time() - t_start

    # Statistical Analysis
    arr = np.array(seed_deltas)
    mean_delta = float(np.mean(arr))
    median_delta = float(np.median(arr))
    std_delta = float(np.std(arr, ddof=1)) if len(arr) > 1 else 0.0
    se_delta = std_delta / np.sqrt(len(arr)) if len(arr) > 1 else 0.0
    t_stat = (mean_delta / se_delta) if se_delta > 0 else 0.0
    p_val = 2.0 * (1.0 - 0.5 * (1.0 + math.erf(abs(t_stat) / math.sqrt(2.0))))

    ci_95_lower = mean_delta - 1.96 * se_delta
    ci_95_upper = mean_delta + 1.96 * se_delta

    wins = sum(1 for d in seed_deltas if d > 0)
    losses = sum(1 for d in seed_deltas if d < 0)
    ties = sum(1 for d in seed_deltas if d == 0)
    win_rate = (wins / len(seed_deltas)) if seed_deltas else 0.0
    decided_matches = wins + losses
    tie_excluded_win_rate = (wins / decided_matches) if decided_matches > 0 else 0.5

    # Telemetry Totals
    total_target_candidates = sum(m["target_candidates"] for m in matches_data)
    total_target_commits = sum(m["target_commits"] for m in matches_data)
    total_foundation_commits = sum(m["foundation_commits"] for m in matches_data)
    total_commits = sum(m["committed"] for m in matches_data)
    total_sims = sum(m["total_simulations"] for m in matches_data)
    total_fallbacks = sum(m["fallback_count"] for m in matches_data)

    all_commits_by_mech: Dict[str, int] = {}
    for m in matches_data:
        for k, v in m["commits_by_mech"].items():
            all_commits_by_mech[k] = all_commits_by_mech.get(k, 0) + v

    lat_p50 = float(np.median([m["latency_p50"] for m in matches_data]))
    lat_p95 = float(np.percentile([m["latency_p95"] for m in matches_data], 95))
    max_turn_latency = float(np.max([m["worst_turn_ms"] for m in matches_data]))

    commit_rate_exposure = (total_target_commits / total_target_candidates) if total_target_candidates > 0 else 0.0
    commit_purity = (total_target_commits / total_commits) if total_commits > 0 else 1.0

    summary = {
        "mechanism": mechanism,
        "stage": stage_name,
        "sample_seeds": len(seeds),
        "total_matches": len(matches_data),
        "elapsed_seconds": round(elapsed, 2),
        "mean_net_delta": round(mean_delta, 2),
        "median_net_delta": round(median_delta, 2),
        "std_delta": round(std_delta, 2),
        "se_delta": round(se_delta, 2),
        "t_statistic": round(t_stat, 2),
        "p_value": round(p_val, 4),
        "ci_95_lower": round(ci_95_lower, 2),
        "ci_95_upper": round(ci_95_upper, 2),
        "wins": wins,
        "losses": losses,
        "ties": ties,
        "win_rate": round(win_rate, 4),
        "tie_excluded_win_rate": round(tie_excluded_win_rate, 4),
        "worst_seed_delta": round(float(np.min(arr)), 2) if len(arr) else 0.0,
        "best_seed_delta": round(float(np.max(arr)), 2) if len(arr) else 0.0,
        "p95_downside_delta": round(float(np.percentile(arr, 5)), 2) if len(arr) else 0.0,
        "target_candidates": total_target_candidates,
        "target_commits": total_target_commits,
        "foundation_commits": total_foundation_commits,
        "total_commits": total_commits,
        "total_simulations": total_sims,
        "total_fallbacks": total_fallbacks,
        "commit_rate_given_exposure": round(commit_rate_exposure, 4),
        "commit_purity": round(commit_purity, 4),
        "commits_by_mechanism": all_commits_by_mech,
        "latency_p50_ms": round(lat_p50, 2),
        "latency_p95_ms": round(lat_p95, 2),
        "max_turn_latency_ms": round(max_turn_latency, 2),
    }

    # Save to CSV
    if output_csv:
        os.makedirs(os.path.dirname(output_csv), exist_ok=True)
        with open(output_csv, "w", newline="", encoding="utf-8") as f:
            fieldnames = [
                "seed", "seat", "treatment_reward", "control_reward", "margin",
                "win", "loss", "tie", "target_candidates", "target_commits",
                "committed", "abstained", "fallback_count", "latency_p50", "latency_p95"
            ]
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            for m in matches_data:
                writer.writerow(m)

    # Save to JSON
    if output_json:
        os.makedirs(os.path.dirname(output_json), exist_ok=True)
        with open(output_json, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)

    print("\n" + "=" * 70)
    print(f"QUALIFICATION SUMMARY: {mechanism} ({stage_name.upper()})")
    print("=" * 70)
    print(f"Matches Evaluated     : {len(matches_data)} ({len(seeds)} seeds x 2 seats)")
    print(f"Net Mean Delta        : ${mean_delta:+.2f} +/- ${se_delta:.2f} (t={t_stat:.2f}, p={p_val:.4f})")
    print(f"95% CI                : [${ci_95_lower:+.2f}, ${ci_95_upper:+.2f}]")
    print(f"Mirror Record         : {wins}W / {losses}L / {ties}T (WinRate: {win_rate*100:.1f}%)")
    print(f"Target Candidates     : {total_target_candidates}")
    print(f"Target Commits        : {total_target_commits}")
    print(f"Commits by Mechanism  : {all_commits_by_mech}")
    print(f"P95 Downside Delta    : ${summary['p95_downside_delta']:+.2f}")
    print(f"Latency P50 / P95     : {lat_p50:.1f}ms / {lat_p95:.1f}ms (Max: {max_turn_latency:.1f}ms)")
    print("=" * 70)

    return summary


def main():
    parser = argparse.ArgumentParser(description="AEC Phase 010 Mechanism Qualification Runner")
    parser.add_argument("--mechanism", type=str, required=True, help="Target mechanism name (e.g. DYNAMIC_SHADOW_HARVEST)")
    parser.add_argument("--stage", type=str, default="pilot", choices=list(PARTITIONS.keys()) + ["custom"], help="Evaluation stage")
    parser.add_argument("--start-seed", type=int, default=None, help="Custom start seed")
    parser.add_argument("--end-seed", type=int, default=None, help="Custom end seed (inclusive)")
    parser.add_argument("--output-csv", type=str, default=None, help="Output CSV path")
    parser.add_argument("--output-json", type=str, default=None, help="Output JSON path")

    args = parser.parse_args()

    if args.stage == "custom":
        if args.start_seed is None or args.end_seed is None:
            parser.error("--start-seed and --end-seed required when stage is custom")
        seeds = list(range(args.start_seed, args.end_seed + 1))
    else:
        seeds = PARTITIONS[args.stage]

    csv_path = args.output_csv or os.path.join(REPO_ROOT, "results", f"PHASE010_{args.mechanism}_{args.stage.upper()}_RESULTS.csv")
    json_path = args.output_json or os.path.join(REPO_ROOT, "results", f"PHASE010_{args.mechanism}_{args.stage.upper()}_TELEMETRY.json")

    execute_qualification(
        mechanism=args.mechanism,
        seeds=seeds,
        stage_name=args.stage,
        output_csv=csv_path,
        output_json=json_path
    )


if __name__ == "__main__":
    main()
