# SPDX-License-Identifier: MIT
"""
=============================================================================
EXP-ARCH-003 H1 TERMINAL REPAIR EXECUTION RUNNER
=============================================================================
Experiment: EXP-ARCH-003_H1_TERMINAL_REPAIR
Preregistration: 02_PREREGISTRATION.md
Baseline: candidates/compiled_v54_plus_residual.py (SHA-256: 18402ec6...)
Treatment: H1 Terminal Repair Optimizer (h1_*.py)
Authorized Cohort: Seeds 330000 to 330499 inclusive (N = 500 seeds, 1000 CRN games)
CRN Design: 2 games per seed (Seat 0: H1 vs Base; Seat 1: Base vs H1)

EXECUTION SAFETY LOCK:
Prospective execution of cohort 330000–330499 is strictly locked until all
pre-freeze audits, micro-validations, and freeze records are complete.
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
    COHORT_END,
    COHORT_SIZE,
    COHORT_START,
    ENTRY_STEP,
    EXPERIMENT_ID,
    FINAL_STEP,
    PIN_BOARD_SIZE,
    PIN_EPISODE_STEPS,
    PIN_MAX_ORDERS,
    PIN_SHED_CAPACITY,
    PIN_TURNS_PER_DAY,
)
from h1_dominance import compute_terminal_liquidation_market

# -----------------------------------------------------------------------------
# Protected Quarantined Cohorts (G-QUAR)
# -----------------------------------------------------------------------------
PROTECTED_QUARANTINE_RANGES = [
    (214200, 214249, "Virgin Final Holdout"),
    (310000, 310499, "DEV-007 Reserved Cohort (Unexecuted)"),
    (410000, 410499, "DEV-007 Fallback 1"),
    (510000, 510499, "DEV-007 Fallback 2"),
    (320000, 320499, "ARCH-002 Consumed Cohort"),
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

AUTHORIZED_COHORT_LO = COHORT_START  # 330000
AUTHORIZED_COHORT_HI = COHORT_END    # 330499
AUTHORIZED_SEEDS_COUNT = COHORT_SIZE  # 500

LOG_FILE = os.path.join(HERE, "EXECUTION_LOG.txt")
RAW_RESULTS_FILE = os.path.join(HERE, "RAW_RESULTS.json")
PAIRED_DELTAS_FILE = os.path.join(HERE, "PAIRED_DELTAS.csv")
TELEMETRY_EVENTS_FILE = os.path.join(HERE, "TELEMETRY_EVENTS.csv")
MANIFEST_FILE = os.path.join(HERE, "EXECUTION_MANIFEST.json")


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
    """G-HASH integrity gate: verify baseline and engine extracts."""
    base_path = os.path.join(REPO_ROOT, "candidates", "compiled_v54_plus_residual.py")
    actual_base_sha = sha256_of_file(base_path)
    if actual_base_sha != BASELINE_SHA256:
        raise RuntimeError(
            f"G-HASH FAIL: Baseline SHA mismatch! Expected {BASELINE_SHA256}, got {actual_base_sha}"
        )


def _actions_equal(a1: Dict[str, Any], a2: Dict[str, Any]) -> bool:
    """Check action equality for farmer, hands, and market."""
    if a1.get("farmer") != a2.get("farmer"):
        return False
    if a1.get("hands") != a2.get("hands"):
        return False
    if a1.get("market") != a2.get("market"):
        return False
    return True


def run_single_game(
    seed: int,
    h1_seat: int,
    allow_consumed_validation: bool = False,
) -> Dict[str, Any]:
    """Execute one 2-player CRN game under pure runner isolation."""
    assert_quarantine(seed, allow_consumed_validation=allow_consumed_validation)

    base_inst_treatment = load_baseline()
    base_inst_opponent = load_baseline()
    base_inst_twin = load_baseline()

    h1_agent = build_agent(base_inst_treatment, shadow_only=False)
    opp_agent = base_inst_opponent.agent
    twin_agent = base_inst_twin.agent

    game = papi.Game(seed)

    config = {
        "boardSize": PIN_BOARD_SIZE,
        "turnsPerDay": PIN_TURNS_PER_DAY,
        "episodeSteps": PIN_EPISODE_STEPS,
        "shedCapacity": PIN_SHED_CAPACITY,
        "maxMarketOrdersPerTurn": PIN_MAX_ORDERS,
    }

    pure_pre_e_pass = True
    pure_712_717_market_pass = True
    pure_step_pass = True

    while not game.done:
        t = game.step_count
        obs_h1 = game.observe(h1_seat)
        obs_opp = game.observe(1 - h1_seat)

        act_twin = twin_agent(copy.deepcopy(obs_h1), copy.deepcopy(config))
        act_h1 = h1_agent(copy.deepcopy(obs_h1), copy.deepcopy(config))
        act_opp = opp_agent(copy.deepcopy(obs_opp), copy.deepcopy(config))

        # 1. P-PURE: steps 0–711 action bit-identity
        if t < ENTRY_STEP:
            if not _actions_equal(act_h1, act_twin):
                pure_pre_e_pass = False

        # 2. P-PURE: steps 712–717 market orders verbatim match
        if ENTRY_STEP <= t < FINAL_STEP:
            if act_h1.get("market", []) != act_twin.get("market", []):
                pure_712_717_market_pass = False

        # 3. Non-activated step purity
        plan = h1_agent.overlay.plans.get(h1_seat)
        if plan is None and t >= ENTRY_STEP:
            if not _actions_equal(act_h1, act_twin):
                pure_step_pass = False

        actions = [None, None]
        actions[h1_seat] = act_h1
        actions[1 - h1_seat] = act_opp
        game.step(actions[0], actions[1])

    h1_score = float(game.reward(h1_seat))
    opp_score = float(game.reward(1 - h1_seat))

    h1_agent.overlay._close_record(h1_seat)
    telemetry_records = copy.deepcopy(h1_agent.overlay.records)
    if not telemetry_records and h1_seat in h1_agent.overlay.open_records:
        rec = h1_agent.overlay.open_records[h1_seat]
        if rec.get("reason") is not None:
            telemetry_records.append(copy.deepcopy(rec))

    primary_reason = telemetry_records[0].get("reason") if telemetry_records else "NO_RECORD"
    activated = (primary_reason == "OK_ACTIVATED")

    return {
        "seed": seed,
        "h1_seat": h1_seat,
        "h1_score": h1_score,
        "opp_score": opp_score,
        "activated": activated,
        "reason": primary_reason,
        "pure_pre_e_pass": pure_pre_e_pass,
        "pure_712_717_market_pass": pure_712_717_market_pass,
        "pure_step_pass": pure_step_pass,
        "telemetry": telemetry_records,
    }


def run_paired_seed(
    seed: int,
    allow_consumed_validation: bool = False,
) -> Dict[str, Any]:
    """Execute CRN pair for one seed (Game A: Seat 0, Game B: Seat 1)."""
    assert_quarantine(seed, allow_consumed_validation=allow_consumed_validation)

    game_a = run_single_game(seed, 0, allow_consumed_validation=allow_consumed_validation)
    game_b = run_single_game(seed, 1, allow_consumed_validation=allow_consumed_validation)

    h1_score_a = game_a["h1_score"]
    base_score_a = game_a["opp_score"]
    h1_score_b = game_b["h1_score"]
    base_score_b = game_b["opp_score"]

    delta_a = h1_score_a - base_score_a
    delta_b = h1_score_b - base_score_b
    delta_paired = 0.5 * (delta_a + delta_b)

    return {
        "seed": seed,
        "h1_score_a": h1_score_a,
        "base_score_a": base_score_a,
        "delta_a": delta_a,
        "h1_score_b": h1_score_b,
        "base_score_b": base_score_b,
        "delta_b": delta_b,
        "delta_paired": delta_paired,
        "activated_a": game_a["activated"],
        "activated_b": game_b["activated"],
        "reason_a": game_a["reason"],
        "reason_b": game_b["reason"],
        "game_a": game_a,
        "game_b": game_b,
    }


def save_results_checkpoint(
    results_map: Dict[int, Any],
    start_time_iso: str,
    status: str = "IN_PROGRESS",
    elapsed_seconds: float = 0.0,
):
    sorted_seeds = sorted(results_map.keys())

    # 1. RAW_RESULTS.json
    tmp_raw = RAW_RESULTS_FILE + ".tmp"
    with open(tmp_raw, "w", encoding="utf-8") as f:
        json.dump({str(s): results_map[s] for s in sorted_seeds}, f, indent=2)
    os.replace(tmp_raw, RAW_RESULTS_FILE)

    # 2. PAIRED_DELTAS.csv
    tmp_csv = PAIRED_DELTAS_FILE + ".tmp"
    with open(tmp_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "seed", "delta_a", "delta_b", "delta_paired", "exposed",
            "h1_score_a", "base_score_a", "h1_score_b", "base_score_b",
            "activated_a", "activated_b", "reason_a", "reason_b",
        ])
        for s in sorted_seeds:
            item = results_map[s]
            exposed = int(bool(item["activated_a"] or item["activated_b"]))
            writer.writerow([
                item["seed"],
                f"{item['delta_a']:.2f}",
                f"{item['delta_b']:.2f}",
                f"{item['delta_paired']:.2f}",
                exposed,
                f"{item['h1_score_a']:.2f}",
                f"{item['base_score_a']:.2f}",
                f"{item['h1_score_b']:.2f}",
                f"{item['base_score_b']:.2f}",
                int(item["activated_a"]),
                int(item["activated_b"]),
                item["reason_a"],
                item["reason_b"],
            ])
    os.replace(tmp_csv, PAIRED_DELTAS_FILE)

    # 3. TELEMETRY_EVENTS.csv
    tmp_tel = TELEMETRY_EVENTS_FILE + ".tmp"
    with open(tmp_tel, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "seed", "h1_seat", "h1_score", "opp_score", "delta", "activated",
            "reason", "pure_pre_e_pass", "pure_712_717_market_pass", "pure_step_pass",
            "route", "simulations", "planning_ms", "changed_workers_count",
            "money_delta", "stock_value_gain", "candidate_overflow", "baseline_overflow",
            "markets_verbatim", "buy_units_U", "fertilizer_reaped", "fertilizer_baseline",
        ])
        for s in sorted_seeds:
            item = results_map[s]
            for g, seat, delta in (
                (item["game_a"], 0, item["delta_a"]),
                (item["game_b"], 1, item["delta_b"]),
            ):
                rec = g.get("telemetry", [{}])[0] if g.get("telemetry") else {}
                writer.writerow([
                    g["seed"],
                    seat,
                    f"{g['h1_score']:.2f}",
                    f"{g['opp_score']:.2f}",
                    f"{delta:.2f}",
                    int(g["activated"]),
                    g["reason"],
                    int(g["pure_pre_e_pass"]),
                    int(g["pure_712_717_market_pass"]),
                    int(g["pure_step_pass"]),
                    rec.get("route", "") or "",
                    rec.get("simulations", "") if rec.get("simulations") is not None else "",
                    f"{rec['planning_ms']:.2f}" if rec.get("planning_ms") is not None else "",
                    len(rec.get("changed_workers", []) or []),
                    f"{rec['money_delta']:.2f}" if rec.get("money_delta") is not None else "",
                    f"{rec['stock_value_gain']:.2f}" if rec.get("stock_value_gain") is not None else "",
                    rec.get("candidate_overflow", "") if rec.get("candidate_overflow") is not None else "",
                    rec.get("baseline_overflow", "") if rec.get("baseline_overflow") is not None else "",
                    rec.get("markets_verbatim", "") if rec.get("markets_verbatim") is not None else "",
                    rec.get("buy_units_U", "") if rec.get("buy_units_U") is not None else "",
                    rec.get("fertilizer_reaped", "") if rec.get("fertilizer_reaped") is not None else "",
                    rec.get("fertilizer_baseline", "") if rec.get("fertilizer_baseline") is not None else "",
                ])
    os.replace(tmp_tel, TELEMETRY_EVENTS_FILE)

    # 4. EXECUTION_MANIFEST.json
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    manifest = {
        "experiment": EXPERIMENT_ID,
        "cohort_lo": AUTHORIZED_COHORT_LO,
        "cohort_hi": AUTHORIZED_COHORT_HI,
        "authorized_seeds": AUTHORIZED_SEEDS_COUNT,
        "executed_seeds": len(results_map),
        "total_games": len(results_map) * 2,
        "start_time": start_time_iso,
        "end_time": now_iso,
        "elapsed_seconds": elapsed_seconds,
        "baseline_sha256": BASELINE_SHA256,
        "runner_sha256": sha256_of_file(__file__),
        "status": status,
    }
    tmp_man = MANIFEST_FILE + ".tmp"
    with open(tmp_man, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    os.replace(tmp_man, MANIFEST_FILE)


def execute_production_cohort(workers: int = 4):
    """Execute the preregistered prospective cohort 330000-330499 under CRN."""
    log("=" * 70)
    log(f"STARTING {EXPERIMENT_ID} AUTHORIZED PRODUCTION EXECUTION")
    log("=" * 70)
    log(f"Authorized Cohort: [{AUTHORIZED_COHORT_LO}, {AUTHORIZED_COHORT_HI}] (N={AUTHORIZED_SEEDS_COUNT} seeds)")
    log(f"Total Games Scheduled: {AUTHORIZED_SEEDS_COUNT * 2}")
    log(f"Parallel Workers: {workers}")

    log("Verifying pre-execution integrity hashes (G-HASH)...")
    verify_integrity_hashes()
    log("G-HASH passed: Baseline verified bit-identical.")

    start_time_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    t0 = time.perf_counter()

    seeds_to_run = list(range(AUTHORIZED_COHORT_LO, AUTHORIZED_COHORT_HI + 1))
    results_map = {}
    completed_count = 0

    if workers <= 1:
        for seed in seeds_to_run:
            seed_res = run_paired_seed(seed, allow_consumed_validation=False)
            results_map[seed] = seed_res
            completed_count += 1
            if completed_count % 25 == 0 or completed_count == AUTHORIZED_SEEDS_COUNT:
                elapsed = time.perf_counter() - t0
                rate = completed_count / max(elapsed, 0.001)
                log(f"Progress: {completed_count}/{AUTHORIZED_SEEDS_COUNT} seeds "
                    f"({completed_count * 2}/{AUTHORIZED_SEEDS_COUNT * 2} games) "
                    f"[{rate:.2f} seeds/s] - Latest seed {seed}: delta_paired={seed_res['delta_paired']:.2f}")
                save_results_checkpoint(results_map, start_time_iso, status="IN_PROGRESS", elapsed_seconds=elapsed)
    else:
        with ProcessPoolExecutor(max_workers=workers, max_tasks_per_child=10) as pool:
            future_to_seed = {
                pool.submit(run_paired_seed, s, False): s for s in seeds_to_run
            }
            for future in as_completed(future_to_seed):
                seed = future_to_seed[future]
                try:
                    seed_res = future.result()
                    results_map[seed] = seed_res
                    completed_count += 1
                except Exception as exc:
                    elapsed = time.perf_counter() - t0
                    log(f"FATAL ERROR on seed {seed}: {exc}")
                    save_results_checkpoint(results_map, start_time_iso, status="FAILED_EXCEPTION", elapsed_seconds=elapsed)
                    raise

                if completed_count % 25 == 0 or completed_count == AUTHORIZED_SEEDS_COUNT:
                    elapsed = time.perf_counter() - t0
                    rate = completed_count / max(elapsed, 0.001)
                    log(f"Progress: {completed_count}/{AUTHORIZED_SEEDS_COUNT} seeds "
                        f"({completed_count * 2}/{AUTHORIZED_SEEDS_COUNT * 2} games) "
                        f"[{rate:.2f} seeds/s] - Latest seed {seed}: delta_paired={seed_res['delta_paired']:.2f}")
                    save_results_checkpoint(results_map, start_time_iso, status="IN_PROGRESS", elapsed_seconds=elapsed)

    t_end = time.perf_counter()
    total_elapsed = t_end - t0
    log(f"Execution complete: {len(results_map)} seeds ({len(results_map)*2} games) finished in {total_elapsed:.1f}s.")
    save_results_checkpoint(results_map, start_time_iso, status="COMPLETED", elapsed_seconds=total_elapsed)


def main():
    parser = argparse.ArgumentParser(description="EXP-ARCH-003 Execution Runner")
    parser.add_argument("--execute-authorized-cohort", action="store_true",
                        help="Authorization flag required to execute fresh cohort 330000–330499")
    parser.add_argument("--validation-seed", type=int, default=None,
                        help="Run single consumed validation seed for testing")
    parser.add_argument("--workers", type=int, default=4,
                        help="Parallel worker count")
    args = parser.parse_args()

    verify_integrity_hashes()

    if args.validation_seed is not None:
        log(f"Running unit-validation on consumed seed {args.validation_seed}")
        res = run_paired_seed(args.validation_seed, allow_consumed_validation=True)
        log(f"Validation seed {args.validation_seed} finished. delta_paired={res['delta_paired']:.2f}")
        return

    if not args.execute_authorized_cohort:
        log("SAFETY HALT: Prospective execution flag --execute-authorized-cohort not set.")
        log("Cohort 330000–330499 remains 100% untouched and protected. Exiting.")
        sys.exit(0)

    execute_production_cohort(workers=args.workers)


if __name__ == "__main__":
    main()
