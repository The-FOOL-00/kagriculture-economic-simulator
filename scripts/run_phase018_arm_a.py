#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Phase 018 Arm A: funnel-reservation isolated pilot (preregistered).

Fresh cohort: seeds 249296..249305 (10 seeds, CRN mirror matches).
Comparisons (common control A0):
  - A1vA0: Phase015 treatment (reservation OFF) vs foundation control.
  - A2vA0: Phase015 treatment + funnel reservation vs foundation control.
Reservation effect within (seed, seat): delta_A2 - delta_A1.

Isolation: A2 differs from A1 ONLY by enable_funnel_reservation=True
(see test_arm_a2_differs_from_a1_only_by_reservation_flag).

Produces:
- results/PHASE018_ARM_A_MATCHES.csv
- results/PHASE018_ARM_A_LEDGER.csv
- results/PHASE018_ARM_A_SUMMARY.json
"""

from __future__ import annotations

import csv
import hashlib
import json
import os
import sys
import time
from collections import Counter
from typing import Any, Dict, List, Tuple

import numpy as np

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)
CPPSIM = os.path.join(REPO_ROOT, "external_repos", "kaggriculture-cppsim")
if CPPSIM not in sys.path:
    sys.path.insert(0, CPPSIM)

import kagsim
from aec.config import (
    build_phase015_treatment_config,
    build_phase018_arm_a2_config,
    build_robust_qualified_config,
)
from aec.integration.executor import AECExecutor

V3_TARBALL_PATH = os.path.join(REPO_ROOT, "submission_Vj_kc_v3.tar.gz")
V3_EXPECTED_SHA = "845e0d10981b11b06d272048ff5cee30d70a0403dd757651a556a78c8bf18943"
RESULTS_DIR = os.path.join(REPO_ROOT, "results")
MATCHES_CSV = os.path.join(RESULTS_DIR, "PHASE018_ARM_A_MATCHES.csv")
LEDGER_CSV = os.path.join(RESULTS_DIR, "PHASE018_ARM_A_LEDGER.csv")
SUMMARY_JSON = os.path.join(RESULTS_DIR, "PHASE018_ARM_A_SUMMARY.json")

ARM_A_SEEDS = list(range(249296, 249306))
FOUNDATION_MECHS = {
    "DEPENDENCY_AWARE_MARKET_TIMING", "TERMINAL_LIQUIDATION", "PHASE_SHUTDOWN",
}


def verify_v3_sha() -> None:
    with open(V3_TARBALL_PATH, "rb") as f:
        actual = hashlib.sha256(f.read()).hexdigest()
    if actual != V3_EXPECTED_SHA:
        raise RuntimeError(f"V3 SHA MISMATCH: {actual}")


def _summarize_side(history: List[Any]) -> Dict[str, Any]:
    commits_by_mech: Counter = Counter()
    sims_by_mech: Counter = Counter()
    cand_by_mech: Counter = Counter()
    pruned_foundation = 0
    sims_foundation = 0
    lat: List[float] = []
    res_saved = 0
    res_displaced = 0
    res_turns = 0
    res_sites: Counter = Counter()
    for t in history:
        lat.append(t.total_time_ms)
        if t.decision == "COMMIT" and t.committed_mechanism:
            commits_by_mech[t.committed_mechanism] += 1
        for c in t.candidates:
            cand_by_mech[c.mechanism_family] += 1
            if c.simulation_run:
                sims_by_mech[c.mechanism_family] += 1
                if c.mechanism_family in FOUNDATION_MECHS:
                    sims_foundation += 1
            elif c.patch_pruned and c.mechanism_family in FOUNDATION_MECHS:
                pruned_foundation += 1
        fr = getattr(t, "funnel_reservation", {}) or {}
        if fr:
            res_turns += 1
            for site, rec in fr.items():
                d = rec.to_dict() if hasattr(rec, "to_dict") else dict(rec)
                res_saved += len(d.get("saved", []))
                res_displaced += len(d.get("displaced", []))
                if d.get("saved"):
                    res_sites[site] += 1
    return {
        "commits": sum(commits_by_mech.values()),
        "commits_by_mech": dict(commits_by_mech),
        "sims": sum(sims_by_mech.values()),
        "sims_by_mech": dict(sims_by_mech),
        "candidates": sum(cand_by_mech.values()),
        "pruned_foundation": pruned_foundation,
        "sims_foundation": sims_foundation,
        "escalations": sum(t.macro_escalations_count for t in history),
        "safety_rejected": sum(t.patches_safety_rejected_count for t in history),
        "econ_rejected": sum(t.patches_economically_rejected_count for t in history),
        "res_saved": res_saved,
        "res_displaced": res_displaced,
        "res_turns": res_turns,
        "res_sites": dict(res_sites),
        "latencies": lat,
    }


def run_arm_match(seed: int, seat: int, arm: str) -> Dict[str, Any]:
    """One CRN mirror match: treatment arm (A1/A2) at `seat` vs A0 control."""
    game = kagsim.Game(seed)
    if arm == "A1":
        trt_cfg = build_phase015_treatment_config()
    elif arm == "A2":
        trt_cfg = build_phase018_arm_a2_config()
    else:
        raise ValueError(arm)
    ctrl_cfg = build_robust_qualified_config()
    trt = AECExecutor(config=trt_cfg)
    ctrl = AECExecutor(config=ctrl_cfg)
    t0 = time.time()
    while not game.done:
        o0, o1 = game.observe(0), game.observe(1)
        if seat == 0:
            a0, a1 = trt.act(o0), ctrl.act(o1)
        else:
            a0, a1 = ctrl.act(o0), trt.act(o1)
        game.step(a0, a1)
    r0, r1 = float(game.reward(0)), float(game.reward(1))
    margin = (r0 - r1) if seat == 0 else (r1 - r0)
    trt_hist = getattr(trt, "_telemetry_history", [])
    ctrl_hist = getattr(ctrl, "_telemetry_history", [])
    ledgers = []
    for t in trt_hist:
        for c in t.candidates:
            ledgers.append({
                "arm": arm, "seed": seed, "seat": seat, "step": t.step,
                "patch_id": c.patch_id, "mechanism": c.mechanism_family,
                "simulated": c.simulation_run, "committed": c.commit_decision,
                "pruned": c.patch_pruned, "final_delta": c.delta_margin,
                "local_delta": c.delta_money_realized,
                "macro_escalated": c.macro_escalated,
                "macro_regime": c.macro_regime_type,
                "safety_pass": c.safety_pass,
                "quantity": c.candidate_quantity,
            })
    return {
        "arm": arm, "seed": seed, "seat": seat,
        "trt_reward": r0 if seat == 0 else r1,
        "ctrl_reward": r1 if seat == 0 else r0,
        "margin": margin, "elapsed_s": time.time() - t0,
        "trt": _summarize_side(trt_hist),
        "ctrl": _summarize_side(ctrl_hist),
        "ledgers": ledgers,
    }


def run_task(args: Tuple[int, int, str]) -> Dict[str, Any]:
    return run_arm_match(*args)


def execute_arm_a(max_workers: int = 6) -> Dict[str, Any]:
    verify_v3_sha()
    os.makedirs(RESULTS_DIR, exist_ok=True)
    print("=" * 64)
    print("PHASE018 ARM A: funnel reservation isolated pilot")
    print(f"Seeds {ARM_A_SEEDS[0]}..{ARM_A_SEEDS[-1]} x seats x A1vA0,A2vA0 "
          f"({len(ARM_A_SEEDS) * 4} matches, {max_workers} workers)")
    print("=" * 64)
    tasks = [(s, seat, arm) for s in ARM_A_SEEDS for seat in (0, 1)
             for arm in ("A1", "A2")]
    from concurrent.futures import ProcessPoolExecutor, as_completed
    results: Dict[Tuple[str, int, int], Dict[str, Any]] = {}
    with ProcessPoolExecutor(max_workers=max_workers) as ex:
        futs = {ex.submit(run_task, t): t for t in tasks}
        for f in as_completed(futs):
            arm, seed, seat = futs[f][2], futs[f][0], futs[f][1]
            r = f.result()
            results[(arm, seed, seat)] = r
            print(f"  [{arm}vA0] seed {seed} seat {seat}: margin={r['margin']:+.0f} "
                  f"trt_commits={r['trt']['commits']} ctrl_commits={r['ctrl']['commits']} "
                  f"saved={r['trt']['res_saved']} ({r['elapsed_s']:.0f}s)")

    with open(LEDGER_CSV, "w", newline="") as f:
        fields = ["arm", "seed", "seat", "step", "patch_id", "mechanism",
                  "simulated", "committed", "pruned", "final_delta",
                  "local_delta", "macro_escalated", "macro_regime",
                  "safety_pass", "quantity"]
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for key in sorted(results):
            for row in results[key]["ledgers"]:
                w.writerow(row)

    with open(MATCHES_CSV, "w", newline="") as f:
        fields = ["arm", "seed", "seat", "trt_reward", "ctrl_reward", "margin",
                  "trt_commits", "ctrl_commits", "trt_sims", "trt_escalations",
                  "res_saved", "res_turns", "elapsed_s"]
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for key in sorted(results):
            r = results[key]
            w.writerow({
                "arm": r["arm"], "seed": r["seed"], "seat": r["seat"],
                "trt_reward": round(r["trt_reward"], 1),
                "ctrl_reward": round(r["ctrl_reward"], 1),
                "margin": round(r["margin"], 1),
                "trt_commits": r["trt"]["commits"],
                "ctrl_commits": r["ctrl"]["commits"],
                "trt_sims": r["trt"]["sims"],
                "trt_escalations": r["trt"]["escalations"],
                "res_saved": r["trt"]["res_saved"],
                "res_turns": r["trt"]["res_turns"],
                "elapsed_s": round(r["elapsed_s"], 1),
            })

    per_seed = []
    for seed in ARM_A_SEEDS:
        d1 = (results[("A1", seed, 0)]["margin"]
              + results[("A1", seed, 1)]["margin"]) / 2
        d2 = (results[("A2", seed, 0)]["margin"]
              + results[("A2", seed, 1)]["margin"]) / 2
        per_seed.append({"seed": seed, "A1": d1, "A2": d2, "effect": d2 - d1})

    def stats(xs: List[float]) -> Dict[str, float]:
        a = np.asarray(xs, dtype=float)
        se = float(a.std(ddof=1) / np.sqrt(len(a))) if len(a) > 1 else 0.0
        return {"mean": float(a.mean()), "std": float(a.std(ddof=1)) if len(a) > 1 else 0.0,
                "se": se, "ci95": [float(a.mean() - 1.96 * se), float(a.mean() + 1.96 * se)],
                "min": float(a.min()), "max": float(a.max())}

    def wlt(xs: List[float]) -> Dict[str, int]:
        return {"W": sum(1 for x in xs if x > 0), "L": sum(1 for x in xs if x < 0),
                "T": sum(1 for x in xs if x == 0)}

    a1 = [p["A1"] for p in per_seed]
    a2 = [p["A2"] for p in per_seed]
    eff = [p["effect"] for p in per_seed]
    summary = {
        "v3_sha256": V3_EXPECTED_SHA, "v3_verified": True,
        "seeds": ARM_A_SEEDS, "n_matches": len(tasks),
        "A1vA0": {**stats(a1), "wlt": wlt(a1)},
        "A2vA0": {**stats(a2), "wlt": wlt(a2)},
        "reservation_effect_A2_minus_A1": {**stats(eff), "wlt": wlt(eff)},
        "per_seed": per_seed,
        "totals": {
            arm: {
                "commits": sum(results[(arm, s, st)]["trt"]["commits"]
                               for s in ARM_A_SEEDS for st in (0, 1)),
                "sims": sum(results[(arm, s, st)]["trt"]["sims"]
                            for s in ARM_A_SEEDS for st in (0, 1)),
                "escalations": sum(results[(arm, s, st)]["trt"]["escalations"]
                                   for s in ARM_A_SEEDS for st in (0, 1)),
                "res_saved": sum(results[(arm, s, st)]["trt"]["res_saved"]
                                 for s in ARM_A_SEEDS for st in (0, 1)),
            } for arm in ("A1", "A2")
        },
    }
    with open(SUMMARY_JSON, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"A1vA0 mean={summary['A1vA0']['mean']:+.1f} {summary['A1vA0']['wlt']}")
    print(f"A2vA0 mean={summary['A2vA0']['mean']:+.1f} {summary['A2vA0']['wlt']}")
    print(f"effect mean={summary['reservation_effect_A2_minus_A1']['mean']:+.1f}")
    return summary


if __name__ == "__main__":
    execute_arm_a()
