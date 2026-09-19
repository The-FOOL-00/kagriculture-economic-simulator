#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""AEC Phase 014: Economic Headroom Audit Harness (§5, §6, §7, §8, §9, §10, §27).

Executes the formal diagnostic headroom probe and state profiler across certified fresh
development cohorts:
  - Diagnostic Block 1: Seeds 249241..249250 (N=10 seeds, 20 mirror matches)
  - Expanded Audit Block: Seeds 249251..249275 (N=25 seeds, 50 mirror matches)
  - Total Census: 35 pristine fresh seeds (70 mirror matches, 50,400 turns)

Protocol:
  - Common Random Numbers (CRN), Symmetric Mirror Seats (S0, S1)
  - Frozen V3 chassis verification (SHA256: 845e0d10981b11b06d272048ff5cee30d70a0403dd757651a556a78c8bf18943)
  - Empirical Live Foundation (V3 + DEPENDENCY_AWARE_MARKET_TIMING + TERMINAL_LIQUIDATION + PHASE_SHUTDOWN)
  - Quarantined: All Group 1, Group 2, Group 3 experimental mechanisms
  - State Profiler taxonomy & 16 diagnostic headroom indicators
  - Bounded Oracle Probe across 7 action families
  - Causal Attribution Engine & Candidate-Gap Matrix
"""

from __future__ import annotations

import argparse
import concurrent.futures
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
)
from aec.integration.executor import AECExecutor
from aec.audit.state_profiler import StateProfiler, StateClassification
from aec.audit.oracle_probe import BoundedOracleProbe, OracleProbeResult, OracleCategory
from aec.audit.attribution_engine import AttributionEngine, CandidateGapRecord, CausalFailureLayer, ScorecardRow
from aec.ir.economic_state import build_economic_state

V3_TARBALL_PATH = os.path.join(REPO_ROOT, "submission_Vj_kc_v3.tar.gz")
V3_EXPECTED_SHA256 = "845e0d10981b11b06d272048ff5cee30d70a0403dd757651a556a78c8bf18943"

# Certified Fresh Development Cohorts for Phase 014 (§27)
PHASE014_COHORTS: Dict[str, List[int]] = {
    "diagnostic_block_1": list(range(249241, 249251)),  # N=10 seeds (20 mirror matches)
    "expanded_audit_block": list(range(249251, 249276)), # N=25 seeds (50 mirror matches)
    "full_census": list(range(249241, 249276)),          # N=35 seeds (70 mirror matches)
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
    # 5. Consumed Phase 010/010B Cohorts
    if 249050 <= seed <= 249110:
        raise RuntimeError(f"FATAL REPLICATION BREACH: Consumed seed {seed} re-used!")
    # 6. Consumed Phase 011 Group 1 Cohorts
    if 249111 <= seed <= 249170:
        raise RuntimeError(f"FATAL REPLICATION BREACH: Consumed Phase 011 seed {seed} re-used!")
    # 7. Consumed Phase 012 Group 2 Cohorts
    if 249171 <= seed <= 249230:
        raise RuntimeError(f"FATAL REPLICATION BREACH: Consumed Phase 012 seed {seed} re-used!")
    # 8. Consumed Phase 013 Group 3 Pilot Cohort
    if 249231 <= seed <= 249240:
        raise RuntimeError(f"FATAL REPLICATION BREACH: Consumed Phase 013 seed {seed} re-used!")

    # Verify bit-identical V3 tarball chassis
    actual_sha = sha256_of_file(V3_TARBALL_PATH)
    if actual_sha != V3_EXPECTED_SHA256:
        raise RuntimeError(f"FATAL CHASSIS BREACH: V3 hash {actual_sha} != {V3_EXPECTED_SHA256}")


def load_v3_agent() -> Any:
    with tarfile.open(V3_TARBALL_PATH, "r:gz") as tar:
        member = tar.extractfile("main.py")
        if member is None:
            raise RuntimeError("main.py not found in V3 tarball")
        v3_code = member.read().decode("utf-8")
    ns: Dict[str, Any] = {}
    exec(compile(v3_code, "frozen_v3_main.py", "exec"), ns)
    return ns["agent"]


class FrozenV3ControlAgent:
    """Isolated raw frozen V3 control loaded in memory."""
    def __init__(self) -> None:
        self._agent = load_v3_agent()

    def act(self, obs: Dict[str, Any], cfg: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return self._agent(obs, cfg)


def run_audit_match(
    seed: int,
    treatment_seat: int,
    treatment_executor: AECExecutor,
    control_agent: Any,
    sample_every_n: int = 12,
) -> Dict[str, Any]:
    """Runs one mirror match instrumented with state profiler and oracle probe."""
    assert_governance(seed)
    game = kagsim.Game(seed)
    profiler = StateProfiler()
    oracle_probe = BoundedOracleProbe()
    attributor = AttributionEngine()

    state_records: List[Dict[str, Any]] = []
    probe_records: List[Dict[str, Any]] = []
    gap_records: List[Dict[str, Any]] = []

    step_idx = 0
    t_start = time.time()

    while not game.done:
        obs0 = game.observe(0)
        obs1 = game.observe(1)

        treatment_obs = obs0 if treatment_seat == 0 else obs1
        control_obs = obs1 if treatment_seat == 0 else obs0

        # Execute actions
        if treatment_seat == 0:
            act0 = treatment_executor.act(obs0)
            act1 = control_agent.act(obs1)
            treatment_action = act0
        else:
            act0 = control_agent.act(obs0)
            act1 = treatment_executor.act(obs1)
            treatment_action = act1

        # Profile state on treatment agent
        econ_state = build_economic_state(treatment_obs)
        pressure_state = getattr(treatment_executor, "_prev_econ_state", None)
        classification = profiler.classify_turn(econ_state, treatment_action)
        state_dict = classification.to_dict()
        state_dict["seed"] = seed
        state_dict["seat"] = treatment_seat
        state_records.append(state_dict)

        # Sampling rule for Oracle Probe:
        # Sample interesting states (gated at step % 4 == 0 to avoid identical consecutive ticks),
        # periodic turns (step % sample_every_n == 0), and endgame liquidation (step >= 700 and step % 2 == 0)
        should_probe = (
            (classification.is_interesting and step_idx % 4 == 0)
            or (step_idx % sample_every_n == 0)
            or (step_idx >= 700 and step_idx % 2 == 0)
        )

        if should_probe:
            latest_telem = treatment_executor.latest_telemetry
            future_traj = treatment_executor.backbone.get_future_trajectory(
                step=step_idx,
                horizon=24,
                player=econ_state.player,
                n_hands=max(0, len(econ_state.workers.workers) - 1),
            )
            p_res = oracle_probe.probe_state(
                econ_state=econ_state,
                baseline_action=treatment_action,
                continuation_trajectory=future_traj,
                aec_telemetry=latest_telem,
                horizon=18,
            )
            p_dict = p_res.to_dict()
            p_dict["seed"] = seed
            p_dict["seat"] = treatment_seat
            p_dict["is_interesting"] = classification.is_interesting
            p_dict["worker_state"] = classification.worker_state
            p_dict["farm_state"] = classification.farm_state
            p_dict["market_state"] = classification.market_state
            p_dict["production_state"] = classification.production_state
            p_dict["terminal_state"] = classification.terminal_state
            probe_records.append(p_dict)

            # Causal attribution for positive headroom
            if p_res.local_headroom > 0.5:
                layer, reason, gap_rec = attributor.attribute_state(p_res, latest_telem, seed)
                if gap_rec is not None:
                    g_dict = gap_rec.to_dict()
                    g_dict["seat"] = treatment_seat
                    g_dict["layer"] = layer.value
                    g_dict["reason"] = reason
                    gap_records.append(g_dict)

        game.step(act0, act1)
        step_idx += 1

    r0 = float(game.reward(0))
    r1 = float(game.reward(1))
    treatment_reward = r0 if treatment_seat == 0 else r1
    control_reward = r1 if treatment_seat == 0 else r0
    margin = treatment_reward - control_reward

    telemetry_history = getattr(treatment_executor, "_telemetry_history", [])
    total_commits = sum(1 for t in telemetry_history if t.decision == "COMMIT")

    return {
        "seed": seed,
        "treatment_seat": treatment_seat,
        "treatment_reward": treatment_reward,
        "control_reward": control_reward,
        "margin": margin,
        "total_commits": total_commits,
        "match_elapsed_s": round(time.time() - t_start, 2),
        "state_records": state_records,
        "probe_records": probe_records,
        "gap_records": gap_records,
    }


def run_seed_paired_audit(seed: int) -> Dict[str, Any]:
    """Runs mirror matches (Seat 0 and Seat 1) for a single fresh seed."""
    assert_governance(seed)
    ctrl_cfg = AECConfig(
        enabled_mechanisms=ENABLED_FOUNDATION_MECHANISMS,
        quarantined_mechanisms=QUARANTINED_MECHANISMS,
        frozen_mode=True,
    )

    t_seed = time.time()
    # Match 1: Treatment at Seat 0
    exec0 = AECExecutor(config=ctrl_cfg)
    v3_ctrl0 = FrozenV3ControlAgent()
    m1 = run_audit_match(seed, 0, exec0, v3_ctrl0)

    # Match 2: Treatment at Seat 1
    exec1 = AECExecutor(config=ctrl_cfg)
    v3_ctrl1 = FrozenV3ControlAgent()
    m2 = run_audit_match(seed, 1, exec1, v3_ctrl1)

    paired_delta = 0.5 * (m1["margin"] + m2["margin"])
    elapsed = time.time() - t_seed

    return {
        "seed": seed,
        "m1_margin": m1["margin"],
        "m2_margin": m2["margin"],
        "paired_delta": paired_delta,
        "elapsed_s": round(elapsed, 2),
        "m1": m1,
        "m2": m2,
    }


def execute_cohort_audit(
    cohort_name: str,
    seeds: List[int],
    max_workers: int = 6,
) -> Dict[str, Any]:
    """Executes headroom audit across an entire seed cohort with process pooling."""
    print(f"\n{'='*75}")
    print(f"STARTING PHASE 014 HEADROOM AUDIT — COHORT: {cohort_name}")
    print(f"Seeds: {seeds[0]}..{seeds[-1]} (N={len(seeds)} seeds, {len(seeds)*2} mirror matches)")
    print(f"Workers: {max_workers} processes")
    print(f"{'='*75}\n", flush=True)

    t_start = time.time()
    seed_results: List[Dict[str, Any]] = []

    with concurrent.futures.ProcessPoolExecutor(max_workers=min(max_workers, len(seeds))) as pool:
        futures = {pool.submit(run_seed_paired_audit, s): s for s in seeds}
        completed = 0
        for f in concurrent.futures.as_completed(futures):
            seed = futures[f]
            completed += 1
            try:
                res = f.result()
                seed_results.append(res)
                print(f"  [{completed:02d}/{len(seeds):02d}] Seed {seed:d}: "
                      f"M1={res['m1_margin']:+8.1f}, M2={res['m2_margin']:+8.1f} | "
                      f"Paired Delta={res['paired_delta']:+8.1f} ({res['elapsed_s']:.1f}s)", flush=True)
            except Exception as e:
                print(f"  [ERROR] Seed {seed} failed: {e}", flush=True)
                raise e

    seed_results.sort(key=lambda r: r["seed"])
    total_elapsed = time.time() - t_start

    # Flatten match and probe records
    all_match_rows: List[Dict[str, Any]] = []
    all_state_rows: List[Dict[str, Any]] = []
    all_probe_rows: List[Dict[str, Any]] = []
    all_gap_rows: List[Dict[str, Any]] = []

    for sr in seed_results:
        for m_key in ("m1", "m2"):
            m = sr[m_key]
            all_match_rows.append({
                "seed": m["seed"],
                "seat": m["treatment_seat"],
                "treatment_reward": m["treatment_reward"],
                "control_reward": m["control_reward"],
                "margin": m["margin"],
                "commits": m["total_commits"],
                "elapsed_s": m["match_elapsed_s"],
            })
            all_state_rows.extend(m["state_records"])
            all_probe_rows.extend(m["probe_records"])
            all_gap_rows.extend(m["gap_records"])

    # Aggregate Statistics
    paired_deltas = [r["paired_delta"] for r in seed_results]
    mean_delta = float(np.mean(paired_deltas))
    std_delta = float(np.std(paired_deltas, ddof=1)) if len(paired_deltas) > 1 else 0.0
    median_delta = float(np.median(paired_deltas))

    # State Frequencies
    total_turns = len(all_state_rows)
    worker_freq: Dict[str, int] = {}
    farm_freq: Dict[str, int] = {}
    market_freq: Dict[str, int] = {}
    prod_freq: Dict[str, int] = {}
    term_freq: Dict[str, int] = {}
    opp_freq: Dict[str, int] = {}
    indicator_freq: Dict[str, int] = {}

    interesting_count = 0
    for s in all_state_rows:
        worker_freq[s["worker_state"]] = worker_freq.get(s["worker_state"], 0) + 1
        farm_freq[s["farm_state"]] = farm_freq.get(s["farm_state"], 0) + 1
        market_freq[s["market_state"]] = market_freq.get(s["market_state"], 0) + 1
        prod_freq[s["production_state"]] = prod_freq.get(s["production_state"], 0) + 1
        term_freq[s["terminal_state"]] = term_freq.get(s["terminal_state"], 0) + 1
        opp_freq[s["opponent_state"]] = opp_freq.get(s["opponent_state"], 0) + 1
        if s["is_interesting"]:
            interesting_count += 1
        for ind in s.get("indicators", []):
            indicator_freq[ind] = indicator_freq.get(ind, 0) + 1

    # Oracle Headroom Statistics
    total_probed = len(all_probe_rows)
    positive_probes = [p for p in all_probe_rows if p["local_headroom"] > 0.5]
    positive_deltas = [p["local_headroom"] for p in positive_probes]

    category_counts: Dict[str, int] = {}
    family_headroom: Dict[str, List[float]] = {}

    for p in all_probe_rows:
        cat = p["category"]
        category_counts[cat] = category_counts.get(cat, 0) + 1
        if p["local_headroom"] > 0.5 and p["best_family"]:
            fam = p["best_family"]
            family_headroom.setdefault(fam, []).append(p["local_headroom"])

    hr_mean = float(np.mean(positive_deltas)) if positive_deltas else 0.0
    hr_median = float(np.median(positive_deltas)) if positive_deltas else 0.0
    hr_p75 = float(np.percentile(positive_deltas, 75)) if positive_deltas else 0.0
    hr_p90 = float(np.percentile(positive_deltas, 90)) if positive_deltas else 0.0
    hr_p95 = float(np.percentile(positive_deltas, 95)) if positive_deltas else 0.0
    hr_max = float(np.max(positive_deltas)) if positive_deltas else 0.0

    # Causal Gap Summary
    gap_layer_counts: Dict[str, int] = {}
    for g in all_gap_rows:
        lay = g["layer"]
        gap_layer_counts[lay] = gap_layer_counts.get(lay, 0) + 1

    summary = {
        "cohort_name": cohort_name,
        "n_seeds": len(seeds),
        "n_matches": len(seeds) * 2,
        "total_turns": total_turns,
        "total_elapsed_s": round(total_elapsed, 2),
        "foundation_performance": {
            "mean_paired_delta": round(mean_delta, 2),
            "median_delta": round(median_delta, 2),
            "std_delta": round(std_delta, 2),
        },
        "state_frequencies": {
            "worker_state": {k: round(v / total_turns, 4) for k, v in worker_freq.items()},
            "farm_state": {k: round(v / total_turns, 4) for k, v in farm_freq.items()},
            "market_state": {k: round(v / total_turns, 4) for k, v in market_freq.items()},
            "production_state": {k: round(v / total_turns, 4) for k, v in prod_freq.items()},
            "terminal_state": {k: round(v / total_turns, 4) for k, v in term_freq.items()},
            "opponent_state": {k: round(v / total_turns, 4) for k, v in opp_freq.items()},
            "interesting_state_rate": round(interesting_count / total_turns, 4),
            "indicator_counts": indicator_freq,
        },
        "oracle_headroom": {
            "total_states_probed": total_probed,
            "positive_headroom_states": len(positive_probes),
            "positive_rate": round(len(positive_probes) / max(1, total_probed), 4),
            "mean_headroom": round(hr_mean, 2),
            "median_headroom": round(hr_median, 2),
            "p75": round(hr_p75, 2),
            "p90": round(hr_p90, 2),
            "p95": round(hr_p95, 2),
            "max_headroom": round(hr_max, 2),
            "category_distribution": category_counts,
            "headroom_by_family": {
                fam: {
                    "count": len(vals),
                    "mean": round(float(np.mean(vals)), 2),
                    "max": round(float(np.max(vals)), 2)
                }
                for fam, vals in family_headroom.items()
            },
        },
        "causal_gaps": {
            "total_gaps_recorded": len(all_gap_rows),
            "counts_by_layer": gap_layer_counts,
        }
    }

    return {
        "summary": summary,
        "seed_results": seed_results,
        "matches": all_match_rows,
        "states": all_state_rows,
        "probes": all_probe_rows,
        "gaps": all_gap_rows,
    }


def save_results(audit_output: Dict[str, Any], results_dir: str = "results") -> None:
    os.makedirs(results_dir, exist_ok=True)

    # 1. Matches CSV
    m_path = os.path.join(results_dir, "PHASE014_AUDIT_MATCHES.csv")
    with open(m_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["seed", "seat", "treatment_reward", "control_reward", "margin", "commits", "elapsed_s"])
        writer.writeheader()
        writer.writerows(audit_output["matches"])
    print(f"Saved match records to {m_path}")

    # 2. State Classification sample (first 5,000 for size management)
    s_path = os.path.join(results_dir, "PHASE014_STATE_CLASSIFICATION.csv")
    with open(s_path, "w", newline="", encoding="utf-8") as f:
        keys = ["seed", "seat", "step", "worker_state", "farm_state", "market_state", "production_state", "terminal_state", "opponent_state", "is_interesting", "indicators"]
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(audit_output["states"][:5000])
    print(f"Saved state classification records to {s_path}")

    # 3. Oracle Probes CSV
    p_path = os.path.join(results_dir, "PHASE014_ORACLE_PROBES.csv")
    with open(p_path, "w", newline="", encoding="utf-8") as f:
        keys = ["seed", "seat", "step", "is_interesting", "worker_state", "farm_state", "market_state", "production_state", "terminal_state", "alternatives_evaluated", "local_headroom", "category", "category_rationale", "best_family", "best_description", "aec_committed", "aec_committed_mechanism", "positive_alternatives_count"]
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(audit_output["probes"])
    print(f"Saved oracle probe records to {p_path}")

    # 4. Candidate Gap Matrix CSV
    g_path = os.path.join(results_dir, "PHASE014_CANDIDATE_GAP_MATRIX.csv")
    with open(g_path, "w", newline="", encoding="utf-8") as f:
        keys = ["seed", "seat", "step", "oracle_opportunity", "current_mechanism", "detected", "represented", "patchable", "exact_sim", "safety_pass", "final_decision", "missing_layer", "layer", "reason", "oracle_delta"]
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(audit_output["gaps"])
    print(f"Saved candidate gap matrix to {g_path}")

    # 5. Summary JSON
    j_path = os.path.join(results_dir, "PHASE014_AUDIT_SUMMARY.json")
    with open(j_path, "w", encoding="utf-8") as f:
        json.dump(audit_output["summary"], f, indent=2)
    print(f"Saved summary metrics to {j_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Phase 014 Economic Headroom Audit")
    parser.add_argument("--cohort", choices=["diagnostic_block_1", "expanded_audit_block", "full_census"], default="full_census")
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument("--sample_every", type=int, default=12)
    args = parser.parse_args()

    seeds = PHASE014_COHORTS[args.cohort]
    results = execute_cohort_audit(args.cohort, seeds, max_workers=args.workers)
    save_results(results)
    print("\nPhase 014 Economic Headroom Audit complete!")
