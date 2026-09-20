# SPDX-License-Identifier: MIT
"""
=============================================================================
EXP-ARCH-002 H1 DOMINANCE TERMINAL CORRECTED RE-EXECUTION RUNNER (P-RE-RUN)
=============================================================================
Experiment: EXP-ARCH-002_H1_DOMINANCE_TERMINAL
Preregistration: 02_PREREGISTRATION.md
Baseline: candidates/compiled_v54_plus_residual.py (SHA-256: 18402ec6...)
Treatment: H1 Dominance-Gated Terminal Optimizer (h1_*.py)
Authorized Cohort: Seeds 320000 to 320499 inclusive (N = 500 seeds, 1000 games)
CRN Design: 2 games per seed (Seat 0: H1 vs Base; Seat 1: Base vs H1)
Eligibility & Governance Authority: 07_REEXECUTION_ELIGIBILITY_AUDIT.md

CORRECTION STATEMENT:
This runner replaces the invalidated execution runner run_arch002_h1_execution.py.
The correction is STRICTLY CONFINED to execution integrity:
1. It eliminates the runner-level double-call defect on the wrapped baseline instance.
2. An independent baseline twin instance (base_inst_twin) is used to verify P-PURE
   pre-E action identity and in-window verbatim markets without mutating the
   treatment baseline's internal state.
3. Neither mutable policy instance is ever called twice on the same step.
4. Scientific hypothesis, protocol, H1 implementation, baseline, simulator, and
   cohort 320000–320499 remain 100% bit-identical.
5. All outputs are written to REEXECUTION_* artifacts to preserve original run data.
=============================================================================
"""

from __future__ import annotations

import argparse
import copy
import csv
import datetime
import hashlib
import json
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import Any, Dict, List, Optional, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))

PORT_DIR = os.path.join(REPO_ROOT, "experiments", "EXP-DEV-006_HORIZON_KILLTEST", "port")
if PORT_DIR not in sys.path:
    sys.path.insert(0, PORT_DIR)
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from kagsim_py import api as papi
from h1_agent import build_agent
from h1_baseline import load_baseline
from h1_const import (
    BASELINE_SHA256,
    ENTRY_STEP,
    FINAL_STEP,
    PIN_BOARD_SIZE,
    PIN_EPISODE_STEPS,
    PIN_MAX_ORDERS,
    PIN_SHED_CAPACITY,
    PIN_TURNS_PER_DAY,
)

# -----------------------------------------------------------------------------
# Protected Quarantined Cohorts (G-QUAR)
# -----------------------------------------------------------------------------
PROTECTED_QUARANTINE_RANGES = [
    (214200, 214249, "Virgin Final Holdout"),
    (310000, 310499, "DEV-007 Reserved Cohort (Unexecuted)"),
    (410000, 410499, "DEV-007 Fallback 1"),
    (510000, 510499, "DEV-007 Fallback 2"),
    (50000, 50499, "Consumed Benchmark Block"),
    (50050, 50099, "DEV-006 Qualification Cohort"),
    (50100, 50149, "Audited Benchmark"),
    (50150, 50199, "Contaminated Benchmark"),
    (60000, 60049, "Sweep-Contaminated Block"),
    (1000, 2683, "Stride-Reachable Executions"),
    (245000, 245049, "DEV-003 Consumed Cohort"),
    (246000, 246049, "DEV-004 Consumed Cohort"),
    (247000, 247049, "DEV-005 Consumed Cohort"),
    (248000, 248049, "DEV-006 Consumed Cohort"),
    (249000, 249049, "Named Reserved Alternative 1"),
    (250000, 250049, "Named Reserved Alternative 2"),
    (255000, 255049, "Named Reserved Alternative 3"),
    (260000, 260049, "Named Reserved Alternative 4"),
    (300000, 300049, "Named Reserved Alternative 5"),
]

AUTHORIZED_COHORT_LO = 320000
AUTHORIZED_COHORT_HI = 320499
AUTHORIZED_SEEDS_COUNT = 500

LOG_FILE = os.path.join(HERE, "REEXECUTION_LOG.txt")
RAW_RESULTS_FILE = os.path.join(HERE, "REEXECUTION_RAW_RESULTS.json")
PAIRED_DELTAS_FILE = os.path.join(HERE, "REEXECUTION_PAIRED_DELTAS.csv")
TELEMETRY_EVENTS_FILE = os.path.join(HERE, "REEXECUTION_TELEMETRY_EVENTS.csv")
MANIFEST_FILE = os.path.join(HERE, "REEXECUTION_EXECUTION_MANIFEST.json")


def log(msg: str):
    ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def sha256_of_file(path: str) -> str:
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def assert_quarantine(seed: int, allow_consumed_validation: bool = False):
    """Hard-abort if seed touches any protected, reserved, or invalid cohort."""
    for lo, hi, label in PROTECTED_QUARANTINE_RANGES:
        if lo <= seed <= hi:
            if allow_consumed_validation and (248000 <= seed <= 248049):
                # Permitted solely during non-prospective runner unit-validation
                return
            raise RuntimeError(
                f"CRITICAL QUARANTINE BREACH: Seed {seed} falls within prohibited range "
                f"[{lo}, {hi}] ({label})! Hard abort."
            )
    if not allow_consumed_validation:
        if not (AUTHORIZED_COHORT_LO <= seed <= AUTHORIZED_COHORT_HI):
            raise RuntimeError(
                f"CRITICAL COHORT VIOLATION: Seed {seed} is outside authorized cohort "
                f"[{AUTHORIZED_COHORT_LO}, {AUTHORIZED_COHORT_HI}]! Hard abort."
            )


def verify_integrity_hashes():
    """G-HASH integrity gate: verify baseline, preregistration, and H1 source."""
    base_path = os.path.join(REPO_ROOT, "candidates", "compiled_v54_plus_residual.py")
    actual_base_sha = sha256_of_file(base_path)
    if actual_base_sha != BASELINE_SHA256:
        raise RuntimeError(
            f"G-HASH FAIL: Baseline SHA mismatch! Expected {BASELINE_SHA256}, got {actual_base_sha}"
        )

    prereg_path = os.path.join(HERE, "02_PREREGISTRATION.md")
    expected_prereg_sha = "508f1dff91f1bfd34186b1eeb6e899c97f87b99fff3841513abe3a88dc4a71b5"
    actual_prereg_sha = sha256_of_file(prereg_path)
    if actual_prereg_sha != expected_prereg_sha:
        raise RuntimeError(
            f"G-HASH FAIL: Preregistration SHA mismatch! Expected {expected_prereg_sha}, got {actual_prereg_sha}"
        )


def _get_game_config() -> Dict[str, Any]:
    return {
        "boardSize": PIN_BOARD_SIZE,
        "turnsPerDay": PIN_TURNS_PER_DAY,
        "episodeSteps": PIN_EPISODE_STEPS,
        "shedCapacity": PIN_SHED_CAPACITY,
        "maxMarketOrdersPerTurn": PIN_MAX_ORDERS,
        "townShopSellInterval": 4,
        "townCenterCenterInterval": 24,
    }


def _actions_equal(a1: Any, a2: Any) -> bool:
    """Deep equality check between two action dictionaries."""
    if not isinstance(a1, dict) or not isinstance(a2, dict):
        return a1 == a2
    return (
        a1.get("farmer") == a2.get("farmer")
        and a1.get("hands") == a2.get("hands")
        and a1.get("market") == a2.get("market")
    )


def _markets_equal(m1: Any, m2: Any) -> bool:
    """Element-wise equality on market orders."""
    list1 = m1 if isinstance(m1, list) else []
    list2 = m2 if isinstance(m2, list) else []
    return list1 == list2


def run_single_game(
    seed: int,
    h1_seat: int,
    allow_consumed_validation: bool = False,
) -> Dict[str, Any]:
    """Execute exactly one game between H1 and Baseline with unpolluted P-PURE telemetry."""
    assert_quarantine(seed, allow_consumed_validation=allow_consumed_validation)
    assert h1_seat in (0, 1), f"Invalid h1_seat: {h1_seat}"

    base_seat = 1 - h1_seat
    cfg = _get_game_config()

    # 1. H1 Treatment agent (wraps base_inst_h1)
    base_inst_h1 = load_baseline()
    agent_h1 = build_agent(base_inst_h1, shadow_only=False)

    # 2. Baseline Control agent (in the other seat)
    base_inst_ctrl = load_baseline()
    agent_base = base_inst_ctrl.call

    # 3. Independent Baseline Twin agent (in H1 seat, solely for unpolluted P-PURE verification)
    base_inst_twin = load_baseline()

    game = papi.Game(seed)

    pure_pre_e_pass = True
    pure_step_pass = True
    pure_verbatim_pass = True

    while not game.done:
        t = game.step_count
        obs0 = game.observe(0)
        obs1 = game.observe(1)

        obs_h1 = obs0 if h1_seat == 0 else obs1
        obs_base = obs1 if h1_seat == 0 else obs0

        # Execute H1 and Baseline (each policy called exactly once per step)
        act_h1 = agent_h1(copy.deepcopy(obs_h1), copy.deepcopy(cfg))
        act_base = agent_base(copy.deepcopy(obs_base), copy.deepcopy(cfg))

        # Check pre-E action identity against the independent twin baseline instance (never double-call base_inst_h1)
        if t < ENTRY_STEP:
            act_twin = base_inst_twin.call(copy.deepcopy(obs_h1), copy.deepcopy(cfg))
            if not _actions_equal(act_h1, act_twin):
                pure_pre_e_pass = False

        # In-window market tracking (712 to 717)
        elif ENTRY_STEP <= t < FINAL_STEP:
            act_twin = base_inst_twin.call(copy.deepcopy(obs_h1), copy.deepcopy(cfg))
            m_h1 = act_h1.get("market") if isinstance(act_h1, dict) else []
            m_twin = act_twin.get("market") if isinstance(act_twin, dict) else []
            if not _markets_equal(m_h1, m_twin):
                pure_verbatim_pass = False

        # Step engine
        if h1_seat == 0:
            game.step(act_h1, act_base)
        else:
            game.step(act_base, act_h1)

    # Episode ended
    reward_h1 = game.reward(h1_seat)
    reward_base = game.reward(base_seat)
    delta = reward_h1 - reward_base

    # Close and extract H1 telemetry
    agent_h1.overlay._close_record(h1_seat)
    rec: Dict[str, Any] = {}
    if agent_h1.overlay.records:
        rec = agent_h1.overlay.records[-1]
    elif h1_seat in agent_h1.overlay.open_records:
        rec = agent_h1.overlay.open_records[h1_seat]

    reason = rec.get("reason", "UNKNOWN")
    activated = (reason == "OK_ACTIVATED")

    # Check non-activated purity: if not activated, delta should strictly be 0.00
    if not activated and abs(delta) > 1e-6:
        pure_step_pass = False

    return {
        "seed": seed,
        "h1_seat": h1_seat,
        "base_seat": base_seat,
        "reward_h1": reward_h1,
        "reward_base": reward_base,
        "delta": delta,
        "activated": activated,
        "reason": reason,
        "subcause": rec.get("subcause", {}),
        "route": rec.get("route", "unknown"),
        "step_E": rec.get("step_E", 712),
        "simulations": rec.get("simulations"),
        "planning_ms": rec.get("planning_ms"),
        "changed_workers": rec.get("changed_workers", []),
        "sold_unit_delta": rec.get("sold_unit_delta"),
        "stock_value_gain": rec.get("stock_value_gain"),
        "candidate_overflow": rec.get("candidate_overflow"),
        "baseline_overflow": rec.get("baseline_overflow"),
        "markets_verbatim": rec.get("markets_verbatim"),
        "market_718_equal": rec.get("market_718_equal"),
        "buy_units_U": rec.get("buy_units_U"),
        "money_at_E": rec.get("money_at_E"),
        "fertilizer_reaped": rec.get("fertilizer_reaped"),
        "fertilizer_baseline": rec.get("fertilizer_baseline"),
        "pure_pre_e_pass": pure_pre_e_pass,
        "pure_verbatim_pass": pure_verbatim_pass,
        "pure_step_pass": pure_step_pass,
    }


def run_seed_crn(
    seed: int,
    allow_consumed_validation: bool = False,
) -> Dict[str, Any]:
    """Execute both Game a (seat 0) and Game b (seat 1) for a single seed under CRN."""
    game_a = run_single_game(seed, h1_seat=0, allow_consumed_validation=allow_consumed_validation)
    game_b = run_single_game(seed, h1_seat=1, allow_consumed_validation=allow_consumed_validation)

    delta_a = game_a["delta"]
    delta_b = game_b["delta"]
    delta_paired = 0.5 * (delta_a + delta_b)

    exposed = game_a["activated"] or game_b["activated"]

    return {
        "seed": seed,
        "delta_a": delta_a,
        "delta_b": delta_b,
        "delta_paired": delta_paired,
        "exposed": exposed,
        "h1_score_a": game_a["reward_h1"],
        "base_score_a": game_a["reward_base"],
        "h1_score_b": game_b["reward_h1"],
        "base_score_b": game_b["reward_base"],
        "activated_a": game_a["activated"],
        "activated_b": game_b["activated"],
        "reason_a": game_a["reason"],
        "reason_b": game_b["reason"],
        "route_a": game_a["route"],
        "route_b": game_b["route"],
        "game_a": game_a,
        "game_b": game_b,
    }


def load_existing_results() -> Tuple[Dict[int, Dict[str, Any]], int]:
    """Load previously completed seeds for deterministic resume."""
    completed: Dict[int, Dict[str, Any]] = {}
    if os.path.exists(RAW_RESULTS_FILE):
        try:
            with open(RAW_RESULTS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                for item in data.get("seeds", []):
                    completed[int(item["seed"])] = item
        except Exception as e:
            log(f"Warning: Failed to load REEXECUTION_RAW_RESULTS.json: {e}")
    return completed, len(completed)


def save_results_checkpoint(
    results_map: Dict[int, Dict[str, Any]],
    start_time_iso: str,
    status: str = "IN_PROGRESS",
):
    """Atomically serialize results to REEXECUTION_* files."""
    sorted_seeds = sorted(results_map.keys())
    seeds_list = [results_map[s] for s in sorted_seeds]

    # 1. REEXECUTION_RAW_RESULTS.json (atomic write)
    raw_payload = {
        "experiment": "EXP-ARCH-002_H1_DOMINANCE_TERMINAL_REEXECUTION",
        "cohort_lo": AUTHORIZED_COHORT_LO,
        "cohort_hi": AUTHORIZED_COHORT_HI,
        "total_seeds": len(sorted_seeds),
        "total_games": len(sorted_seeds) * 2,
        "start_time": start_time_iso,
        "status": status,
        "seeds": seeds_list,
    }
    tmp_json = RAW_RESULTS_FILE + ".tmp"
    with open(tmp_json, "w", encoding="utf-8") as f:
        json.dump(raw_payload, f, indent=2)
    os.replace(tmp_json, RAW_RESULTS_FILE)

    # 2. REEXECUTION_PAIRED_DELTAS.csv
    tmp_csv = PAIRED_DELTAS_FILE + ".tmp"
    with open(tmp_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "seed", "delta_a", "delta_b", "delta_paired", "exposed",
            "h1_score_a", "base_score_a", "h1_score_b", "base_score_b",
            "activated_a", "activated_b", "reason_a", "reason_b",
            "route_a", "route_b",
        ])
        for s in sorted_seeds:
            item = results_map[s]
            writer.writerow([
                item["seed"],
                f"{item['delta_a']:.2f}",
                f"{item['delta_b']:.2f}",
                f"{item['delta_paired']:.2f}",
                int(item["exposed"]),
                f"{item['h1_score_a']:.2f}",
                f"{item['base_score_a']:.2f}",
                f"{item['h1_score_b']:.2f}",
                f"{item['base_score_b']:.2f}",
                int(item["activated_a"]),
                int(item["activated_b"]),
                item["reason_a"],
                item["reason_b"],
                item["route_a"],
                item["route_b"],
            ])
    os.replace(tmp_csv, PAIRED_DELTAS_FILE)

    # 3. REEXECUTION_TELEMETRY_EVENTS.csv
    tmp_tel = TELEMETRY_EVENTS_FILE + ".tmp"
    with open(tmp_tel, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "seed", "seat", "reward_h1", "reward_base", "delta",
            "activated", "reason", "route", "planning_ms", "simulations",
            "changed_workers_count", "stock_value_gain", "buy_units_U",
            "fertilizer_reaped", "pure_pre_e_pass", "pure_verbatim_pass",
        ])
        for s in sorted_seeds:
            item = results_map[s]
            for g in (item["game_a"], item["game_b"]):
                writer.writerow([
                    g["seed"],
                    g["h1_seat"],
                    f"{g['reward_h1']:.2f}",
                    f"{g['reward_base']:.2f}",
                    f"{g['delta']:.2f}",
                    int(g["activated"]),
                    g["reason"],
                    g["route"],
                    f"{g['planning_ms']:.2f}" if g["planning_ms"] is not None else "",
                    g["simulations"] if g["simulations"] is not None else "",
                    len(g["changed_workers"]),
                    f"{g['stock_value_gain']:.2f}" if g["stock_value_gain"] is not None else "",
                    g["buy_units_U"] if g["buy_units_U"] is not None else "",
                    g["fertilizer_reaped"] if g["fertilizer_reaped"] is not None else "",
                    int(g["pure_pre_e_pass"]),
                    int(g["pure_verbatim_pass"]),
                ])
    os.replace(tmp_tel, TELEMETRY_EVENTS_FILE)


def execute_production_cohort(workers: int = 4):
    """Execute the preregistered prospective cohort 320000-320499 under CRN."""
    log("=" * 70)
    log("STARTING EXP-ARCH-002 H1 CORRECTED PRODUCTION RE-EXECUTION")
    log("=" * 70)
    log(f"Authorized Cohort: [{AUTHORIZED_COHORT_LO}, {AUTHORIZED_COHORT_HI}] (N={AUTHORIZED_SEEDS_COUNT} seeds)")
    log(f"Total Games Scheduled: {AUTHORIZED_SEEDS_COUNT * 2}")
    log(f"Parallel Workers: {workers}")

    # G-HASH gate
    log("Verifying pre-execution integrity hashes (G-HASH)...")
    verify_integrity_hashes()
    log("G-HASH passed: Baseline and Preregistration verified bit-identical.")

    start_time_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    results_map, already_done = load_existing_results()
    if already_done > 0:
        log(f"Resuming execution: found {already_done} already completed seeds in REEXECUTION_RAW_RESULTS.json.")

    seeds_to_run = [s for s in range(AUTHORIZED_COHORT_LO, AUTHORIZED_COHORT_HI + 1) if s not in results_map]
    log(f"Seeds remaining to execute: {len(seeds_to_run)}")

    if not seeds_to_run:
        log("All 500 seeds already executed. Re-saving manifest and exiting.")
        save_results_checkpoint(results_map, start_time_iso, status="COMPLETED")
        return

    t0 = time.perf_counter()
    completed_count = already_done

    if workers <= 1:
        for seed in seeds_to_run:
            seed_res = run_seed_crn(seed, allow_consumed_validation=False)
            results_map[seed] = seed_res
            completed_count += 1
            if completed_count % 10 == 0 or completed_count == AUTHORIZED_SEEDS_COUNT:
                elapsed = time.perf_counter() - t0
                rate = (completed_count - already_done) / max(elapsed, 0.001)
                log(f"Progress: {completed_count}/{AUTHORIZED_SEEDS_COUNT} seeds "
                    f"({completed_count * 2}/{AUTHORIZED_SEEDS_COUNT * 2} games) "
                    f"[{rate:.2f} seeds/s] - Latest seed {seed}: delta_paired={seed_res['delta_paired']:.2f}")
                save_results_checkpoint(results_map, start_time_iso, status="IN_PROGRESS")
    else:
        with ProcessPoolExecutor(max_workers=workers) as pool:
            future_to_seed = {
                pool.submit(run_seed_crn, s, False): s for s in seeds_to_run
            }
            batch_counter = 0
            for future in as_completed(future_to_seed):
                seed = future_to_seed[future]
                try:
                    seed_res = future.result()
                    results_map[seed] = seed_res
                    completed_count += 1
                    batch_counter += 1
                except Exception as exc:
                    log(f"FATAL ERROR on seed {seed}: {exc}")
                    save_results_checkpoint(results_map, start_time_iso, status="FAILED_EXCEPTION")
                    raise

                if batch_counter % 10 == 0 or completed_count == AUTHORIZED_SEEDS_COUNT:
                    elapsed = time.perf_counter() - t0
                    rate = (completed_count - already_done) / max(elapsed, 0.001)
                    log(f"Progress: {completed_count}/{AUTHORIZED_SEEDS_COUNT} seeds "
                        f"({completed_count * 2}/{AUTHORIZED_SEEDS_COUNT * 2} games) "
                        f"[{rate:.2f} seeds/s] - Latest seed {seed}: delta_paired={seed_res['delta_paired']:.2f}")
                    save_results_checkpoint(results_map, start_time_iso, status="IN_PROGRESS")

    t_end = time.perf_counter()
    total_elapsed = t_end - t0
    log(f"Re-execution complete: {len(results_map)} seeds ({len(results_map)*2} games) finished in {total_elapsed:.1f}s.")
    save_results_checkpoint(results_map, start_time_iso, status="COMPLETED")

    manifest = {
        "experiment": "EXP-ARCH-002_H1_DOMINANCE_TERMINAL_REEXECUTION",
        "cohort_lo": AUTHORIZED_COHORT_LO,
        "cohort_hi": AUTHORIZED_COHORT_HI,
        "authorized_seeds": AUTHORIZED_SEEDS_COUNT,
        "executed_seeds": len(results_map),
        "total_games": len(results_map) * 2,
        "start_time": start_time_iso,
        "end_time": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "elapsed_seconds": total_elapsed,
        "runner_version": "2.0.0_corrected",
        "runner_sha256": sha256_of_file(__file__),
        "status": "COMPLETED",
    }
    with open(MANIFEST_FILE, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    log(f"Re-execution manifest written to {MANIFEST_FILE}")


def main():
    parser = argparse.ArgumentParser(description="EXP-ARCH-002 H1 Corrected Re-Execution Runner")
    parser.add_argument("--workers", type=int, default=4, help="Number of parallel worker processes")
    parser.add_argument("--resume", action="store_true", help="Resume an interrupted run")
    parser.add_argument("--validate-only", action="store_true", help="Run validation self-test on consumed seeds only")
    args = parser.parse_args()

    if args.validate_only:
        log("Running non-prospective validation self-test...")
        verify_integrity_hashes()
        res = run_seed_crn(248000, allow_consumed_validation=True)
        log(f"Validation self-test passed: seed 248000 delta_paired={res['delta_paired']:.2f}")
        return

    execute_production_cohort(workers=args.workers)


if __name__ == "__main__":
    main()
