#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Phase 015: Fresh Natural-Game Pilot Evaluation Harness (§30, §31, §32, §33).

Executes the formal Stage C natural pilot across certified fresh seeds 249276..249285
(N=10 seeds, 20 mirror matches under CRN) to evaluate whether the upstream compiler
rescue primitives (Asset-Holding Valuation Trigger + Autonomous Tranche Synthesizer)
generate positive incremental economic value over the frozen live foundation.

Evaluates:
1. Baseline Control: Frozen Live Foundation (V3 + Market Timing + Terminal Liq + Phase Shutdown)
2. Treatment (Combined): Frozen Foundation + Phase 015 Capabilities
3. Causal Decomposition:
   - Trigger-only: Valuation Trigger active, Synthesizer disabled
   - Synthesizer-only: Valuation Trigger disabled, Synthesizer enabled on legacy opportunities

Metrics:
- Paired terminal margin delta (Treatment vs Control)
- W/L/T counts
- Activation, candidate, simulation, and commit rates
- Latency breakdown and safety invariants
"""

from __future__ import annotations

import copy
import csv
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
RESULTS_DIR = os.path.join(REPO_ROOT, "results")
PILOT_RESULTS_CSV = os.path.join(RESULTS_DIR, "PHASE015_PILOT_RESULTS.csv")
PILOT_SUMMARY_JSON = os.path.join(RESULTS_DIR, "PHASE015_PILOT_SUMMARY.json")
ATTRIBUTION_JSON = os.path.join(RESULTS_DIR, "PHASE015_ATTRIBUTION_DECOMPOSITION.json")

# Certified pristine fresh pilot cohort (§30, §31)
PILOT_SEEDS = list(range(249276, 249286))  # 10 fresh seeds


def assert_pilot_governance(seed: int) -> None:
    """Strict assertion guarding all holdout and previously consumed seed cohorts."""
    # Holdouts
    if 340050 <= seed <= 340199 or 214200 <= seed <= 214249 or 340300 <= seed <= 340349:
        raise RuntimeError(f"CRITICAL GOVERNANCE BREACH: Access to protected holdout seed {seed}")
    # Consumed Phase 010..014 seeds
    if 249000 <= seed <= 249275:
        raise RuntimeError(f"CRITICAL GOVERNANCE BREACH: Access to previously consumed seed {seed}")


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
    control_config: Optional[AECConfig] = None,
    v3_agent: Optional[Any] = None,
) -> Dict[str, Any]:
    """Runs a single Kaggle game mirror match between Treatment and Frozen Control."""
    assert_pilot_governance(seed)
    game = kagsim.Game(seed)
    # Always instantiate a fresh V3 agent for each match to ensure pure statelessness
    v3_agent = load_v3_agent()

    # Executor for Treatment
    trt_executor = AECExecutor(config=treatment_config)
    # Executor for Control (if None, raw V3 is used)
    ctrl_executor = AECExecutor(config=control_config) if control_config is not None else None

    t_start = time.time()

    while not game.done:
        o0 = game.observe(0)
        o1 = game.observe(1)

        if treatment_seat == 0:
            a0 = trt_executor.act(o0)
            a1 = ctrl_executor.act(o1) if ctrl_executor else v3_agent(o1)
        else:
            a0 = ctrl_executor.act(o0) if ctrl_executor else v3_agent(o0)
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
    triggers = sum(1 for t in history if any("E13_ASSET_HOLDING_STATE" in e for e in t.events_detected))
    candidates = sum(t.candidates_count for t in history)
    latencies = [t.total_time_ms for t in history]

    # Commit mechanism counts
    from collections import Counter
    comm_mechs = Counter(t.committed_mechanism for t in history if t.decision == "COMMIT")

    return {
        "seed": seed,
        "seat": treatment_seat,
        "trt_reward": trt_reward,
        "ctrl_reward": ctrl_reward,
        "margin": margin,
        "commits": commits,
        "simulations": sims,
        "asset_triggers": triggers,
        "candidates": candidates,
        "avg_latency_ms": round(float(np.mean(latencies)), 2) if latencies else 0.0,
        "max_latency_ms": round(float(np.max(latencies)), 2) if latencies else 0.0,
        "match_time_s": round(time.time() - t_start, 2),
        "committed_mechanisms": dict(comm_mechs),
    }


def run_paired_seed_evaluation(
    seed: int,
    treatment_config: AECConfig,
    control_config: AECConfig,
    v3_agent: Any,
) -> Dict[str, Any]:
    """Runs symmetric mirror matches (Seat 0 & Seat 1) for a single seed against Control."""
    # 1. Baseline Foundation Match (Control vs V3) to establish empirical control baseline
    ctrl_s0 = run_single_match(seed, 0, control_config, control_config=None, v3_agent=v3_agent)
    ctrl_s1 = run_single_match(seed, 1, control_config, control_config=None, v3_agent=v3_agent)
    ctrl_paired_margin = 0.5 * (ctrl_s0["margin"] + ctrl_s1["margin"])

    # 2. Treatment Match (Treatment vs V3)
    trt_s0 = run_single_match(seed, 0, treatment_config, control_config=None, v3_agent=v3_agent)
    trt_s1 = run_single_match(seed, 1, treatment_config, control_config=None, v3_agent=v3_agent)
    trt_paired_margin = 0.5 * (trt_s0["margin"] + trt_s1["margin"])

    # Incremental Paired Delta: Treatment paired margin minus Control paired margin
    incremental_paired_delta = trt_paired_margin - ctrl_paired_margin

    return {
        "seed": seed,
        "ctrl_s0_margin": ctrl_s0["margin"],
        "ctrl_s1_margin": ctrl_s1["margin"],
        "ctrl_paired_margin": ctrl_paired_margin,
        "trt_s0_margin": trt_s0["margin"],
        "trt_s1_margin": trt_s1["margin"],
        "trt_paired_margin": trt_paired_margin,
        "incremental_paired_delta": incremental_paired_delta,
        "trt_s0_commits": trt_s0["commits"],
        "trt_s1_commits": trt_s1["commits"],
        "total_commits": trt_s0["commits"] + trt_s1["commits"],
        "total_sims": trt_s0["simulations"] + trt_s1["simulations"],
        "total_triggers": trt_s0["asset_triggers"] + trt_s1["asset_triggers"],
        "total_candidates": trt_s0["candidates"] + trt_s1["candidates"],
        "avg_latency_ms": round(0.5 * (trt_s0["avg_latency_ms"] + trt_s1["avg_latency_ms"]), 2),
        "committed_mechanisms": {
            k: trt_s0["committed_mechanisms"].get(k, 0) + trt_s1["committed_mechanisms"].get(k, 0)
            for k in set(trt_s0["committed_mechanisms"]) | set(trt_s1["committed_mechanisms"])
        }
    }


def run_seed_worker(seed: int) -> Dict[str, Any]:
    assert_pilot_governance(seed)
    v3_agent = load_v3_agent()
    ctrl_cfg = build_robust_qualified_config()
    trt_cfg = build_phase015_treatment_config()
    return run_paired_seed_evaluation(seed, trt_cfg, ctrl_cfg, v3_agent)


def run_attribution_worker(seed: int) -> Dict[str, Any]:
    assert_pilot_governance(seed)
    v3_agent = load_v3_agent()
    ctrl_cfg = build_robust_qualified_config()

    trig_cfg = copy.deepcopy(ctrl_cfg)
    trig_cfg.enable_asset_holding_trigger = True
    trig_cfg.enable_tranche_synthesizer = False
    trig_cfg.enabled_mechanisms = list(ctrl_cfg.enabled_mechanisms) + ["ASSET_HOLDING_VALUATION_TRIGGER"]

    synth_cfg = copy.deepcopy(ctrl_cfg)
    synth_cfg.enable_asset_holding_trigger = False
    synth_cfg.enable_tranche_synthesizer = True
    synth_cfg.enabled_mechanisms = list(ctrl_cfg.enabled_mechanisms) + ["AUTONOMOUS_TRANCHE_ORDER_SYNTHESIZER"]

    res_trig = run_paired_seed_evaluation(seed, trig_cfg, ctrl_cfg, v3_agent)
    res_synth = run_paired_seed_evaluation(seed, synth_cfg, ctrl_cfg, v3_agent)
    return {
        "seed": seed,
        "trig_delta": res_trig["incremental_paired_delta"],
        "synth_delta": res_synth["incremental_paired_delta"],
    }


def execute_natural_pilot(seeds: List[int], max_workers: int = 6) -> Dict[str, Any]:
    print(f"\n{'='*75}")
    print("STARTING PHASE 015 FRESH NATURAL PILOT (STAGE C)")
    print(f"Cohort: Seeds {seeds[0]}..{seeds[-1]} (N={len(seeds)} seeds, {len(seeds)*2} mirror matches)")
    print(f"Parallel Workers: {max_workers} processes")
    print(f"{'='*75}\n", flush=True)

    import concurrent.futures
    seed_records: List[Dict[str, Any]] = []
    t_pilot_start = time.time()

    with concurrent.futures.ProcessPoolExecutor(max_workers=min(max_workers, len(seeds))) as pool:
        futures = {pool.submit(run_seed_worker, s): s for s in seeds}
        completed = 0
        for f in concurrent.futures.as_completed(futures):
            seed = futures[f]
            completed += 1
            res = f.result()
            seed_records.append(res)
            print(f"  [{completed:02d}/{len(seeds):02d}] Seed {seed}: "
                  f"Ctrl={res['ctrl_paired_margin']:+8.1f} | "
                  f"Trt={res['trt_paired_margin']:+8.1f} | "
                  f"Incr Paired Delta={res['incremental_paired_delta']:+8.1f} "
                  f"(Commits={res['total_commits']:2d}, Sims={res['total_sims']:3d})",
                  flush=True)
            # Incremental checkpointing
            try:
                os.makedirs(RESULTS_DIR, exist_ok=True)
                with open(PILOT_RESULTS_CSV, "w", newline="", encoding="utf-8") as out_f:
                    writer = csv.DictWriter(out_f, fieldnames=list(res.keys()))
                    writer.writeheader()
                    writer.writerows(seed_records)
            except Exception:
                pass

    seed_records.sort(key=lambda r: r["seed"])
    total_time = time.time() - t_pilot_start

    # Compute Statistics (§33)
    deltas = [r["incremental_paired_delta"] for r in seed_records]
    mean_delta = float(np.mean(deltas))
    std_delta = float(np.std(deltas, ddof=1)) if len(deltas) > 1 else 0.0
    se_delta = std_delta / math.sqrt(len(deltas)) if len(deltas) > 1 else 0.0
    median_delta = float(np.median(deltas))

    # 95% Confidence Interval
    ci95_low = mean_delta - 1.96 * se_delta
    ci95_high = mean_delta + 1.96 * se_delta

    # Paired t-test
    t_stat, p_val = stats.ttest_1samp(deltas, 0.0) if len(deltas) > 1 else (0.0, 1.0)

    # W/L/T
    wins = sum(1 for d in deltas if d > 10.0)
    losses = sum(1 for d in deltas if d < -10.0)
    ties = len(deltas) - wins - losses

    # Worst-case downside seed
    min_delta = float(np.min(deltas))
    worst_seed = seed_records[int(np.argmin(deltas))]["seed"]

    # Activity Metrics
    tot_commits = sum(r["total_commits"] for r in seed_records)
    tot_sims = sum(r["total_sims"] for r in seed_records)
    tot_triggers = sum(r["total_triggers"] for r in seed_records)
    tot_candidates = sum(r["total_candidates"] for r in seed_records)

    # Mechanism commits
    from collections import Counter
    overall_mechs = Counter()
    for r in seed_records:
        overall_mechs.update(r["committed_mechanisms"])

    print(f"\n{'='*75}")
    print("PHASE 015 NATURAL PILOT RESULTS SUMMARY")
    print(f"{'='*75}")
    print(f"Seeds Evaluated:         {len(seeds)} fresh seeds (20 mirror matches)")
    print(f"Mean Paired Delta:       {mean_delta:+8.2f}")
    print(f"Median Paired Delta:     {median_delta:+8.2f}")
    print(f"Std Dev (SD):            {std_delta:8.2f}")
    print(f"Std Error (SE):          {se_delta:8.2f}")
    print(f"95% CI:                  [{ci95_low:+8.2f}, {ci95_high:+8.2f}]")
    print(f"Paired t-stat:           {t_stat:8.3f} (p-value: {p_val:.4f})")
    print(f"Win / Loss / Tie:        {wins}W / {losses}L / {ties}T")
    print(f"Worst Downside Seed:     Seed {worst_seed} ({min_delta:+8.1f})")
    print(f"Total Triggers:          {tot_triggers}")
    print(f"Total Candidates:        {tot_candidates}")
    print(f"Total Simulations:       {tot_sims}")
    print(f"Total Commits:           {tot_commits}")
    print(f"Committed Mechanisms:    {dict(overall_mechs)}")
    print(f"Total Execution Time:    {total_time:.1f}s")
    print(f"{'='*75}\n", flush=True)

    # Save Results CSV
    os.makedirs(RESULTS_DIR, exist_ok=True)
    with open(PILOT_RESULTS_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(seed_records[0].keys()))
        writer.writeheader()
        writer.writerows(seed_records)

    # Save Summary JSON
    summary_data = {
        "cohort": "phase015_fresh_pilot",
        "seeds": [int(s) for s in seeds],
        "n_seeds": len(seeds),
        "mean_paired_delta": round(mean_delta, 2),
        "median_paired_delta": round(median_delta, 2),
        "std_delta": round(std_delta, 2),
        "se_delta": round(se_delta, 2),
        "ci95": [round(ci95_low, 2), round(ci95_high, 2)],
        "p_value": round(float(p_val), 4),
        "t_stat": round(float(t_stat), 3),
        "record": f"{wins}W / {losses}L / {ties}T",
        "worst_seed": worst_seed,
        "worst_delta": round(min_delta, 2),
        "total_triggers": tot_triggers,
        "total_candidates": tot_candidates,
        "total_simulations": tot_sims,
        "total_commits": tot_commits,
        "committed_mechanisms": dict(overall_mechs),
        "elapsed_seconds": round(total_time, 2),
    }
    with open(PILOT_SUMMARY_JSON, "w", encoding="utf-8") as f:
        json.dump(summary_data, f, indent=2)

    return summary_data


def execute_causal_attribution(seeds: List[int]) -> Dict[str, Any]:
    """Runs isolated attribution runs: Trigger-only vs Synthesizer-only (§30)."""
    print(f"\n{'='*75}")
    print("RUNNING ISOLATED ATTRIBUTION RUNS (TRIGGER-ONLY & SYNTHESIZER-ONLY)")
    print(f"{'='*75}\n", flush=True)

    v3_agent = load_v3_agent()
    ctrl_cfg = build_robust_qualified_config()

    # 1. Trigger-only config (Trigger ON, Synthesizer OFF)
    trig_cfg = copy.deepcopy(ctrl_cfg)
    trig_cfg.enable_asset_holding_trigger = True
    trig_cfg.enable_tranche_synthesizer = False
    trig_cfg.enabled_mechanisms = list(ctrl_cfg.enabled_mechanisms) + ["ASSET_HOLDING_VALUATION_TRIGGER"]

    # 2. Synthesizer-only config (Trigger OFF, Synthesizer ON)
    synth_cfg = copy.deepcopy(ctrl_cfg)
    synth_cfg.enable_asset_holding_trigger = False
    synth_cfg.enable_tranche_synthesizer = True
    synth_cfg.enabled_mechanisms = list(ctrl_cfg.enabled_mechanisms) + ["AUTONOMOUS_TRANCHE_ORDER_SYNTHESIZER"]

    import concurrent.futures
    sample_seeds = seeds[:5]
    trig_deltas = []
    synth_deltas = []

    with concurrent.futures.ProcessPoolExecutor(max_workers=min(5, len(sample_seeds))) as pool:
        futures = {pool.submit(run_attribution_worker, s): s for s in sample_seeds}
        for f in concurrent.futures.as_completed(futures):
            res = f.result()
            trig_deltas.append(res["trig_delta"])
            synth_deltas.append(res["synth_delta"])

    attribution_data = {
        "sample_seeds": [int(s) for s in seeds[:5]],
        "trigger_only_mean_delta": round(float(np.mean(trig_deltas)), 2),
        "synthesizer_only_mean_delta": round(float(np.mean(synth_deltas)), 2),
        "trigger_only_deltas": [round(d, 2) for d in trig_deltas],
        "synthesizer_only_deltas": [round(d, 2) for d in synth_deltas],
    }

    with open(ATTRIBUTION_JSON, "w", encoding="utf-8") as f:
        json.dump(attribution_data, f, indent=2)

    print(f"Trigger-only mean delta (5 seeds):     {attribution_data['trigger_only_mean_delta']:+8.2f}")
    print(f"Synthesizer-only mean delta (5 seeds): {attribution_data['synthesizer_only_mean_delta']:+8.2f}")
    print(f"{'='*75}\n", flush=True)

    return attribution_data


if __name__ == "__main__":
    summary = execute_natural_pilot(PILOT_SEEDS)
    attribution = execute_causal_attribution(PILOT_SEEDS)
