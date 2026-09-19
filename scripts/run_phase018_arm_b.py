#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Phase 018 Arm B: boundary-safe quantity isolated pilot (preregistered).

Fresh cohort: seeds 249306..249315 (10 seeds, CRN mirror matches).
(Consumes the freeze-doc reserve block per §27 fresh-cohort-per-arm rule;
contingency reserve moves to 249336+. Arm A cohort 249296..249305 not reused.)
Comparisons (common control A0):
  - B0vA0: Phase015 treatment, legacy quantities (within-phase control).
  - B1vA0: treatment + boundary-safe quantity menu.
Isolation: B1 differs from B0 ONLY by enable_boundary_safe_quantities=True;
reservation OFF, trigger unmodified, evaluator unchanged.

Produces:
- results/PHASE018_ARM_B_MATCHES.csv
- results/PHASE018_ARM_B_LEDGER.csv (adds candidate `reason` for §31 analysis)
- results/PHASE018_ARM_B_SUMMARY.json (adds per-turn latency percentiles)
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
    build_phase018_arm_b1_config,
    build_robust_qualified_config,
)
from aec.integration.executor import AECExecutor

V3_TARBALL_PATH = os.path.join(REPO_ROOT, "submission_Vj_kc_v3.tar.gz")
V3_EXPECTED_SHA = "845e0d10981b11b06d272048ff5cee30d70a0403dd757651a556a78c8bf18943"
RESULTS_DIR = os.path.join(REPO_ROOT, "results")
MATCHES_CSV = os.path.join(RESULTS_DIR, "PHASE018_ARM_B_MATCHES.csv")
LEDGER_CSV = os.path.join(RESULTS_DIR, "PHASE018_ARM_B_LEDGER.csv")
SUMMARY_JSON = os.path.join(RESULTS_DIR, "PHASE018_ARM_B_SUMMARY.json")

ARM_B_SEEDS = list(range(249306, 249316))


def verify_v3_sha() -> None:
    with open(V3_TARBALL_PATH, "rb") as f:
        actual = hashlib.sha256(f.read()).hexdigest()
    if actual != V3_EXPECTED_SHA:
        raise RuntimeError(f"V3 SHA MISMATCH: {actual}")


def _summarize_side(history: List[Any]) -> Dict[str, Any]:
    commits_by_mech: Counter = Counter()
    sims = 0
    lat: List[float] = []
    for t in history:
        lat.append(float(t.total_time_ms))
        if t.decision == "COMMIT" and t.committed_mechanism:
            commits_by_mech[t.committed_mechanism] += 1
        sims += t.simulations_run
    return {
        "commits": sum(commits_by_mech.values()),
        "commits_by_mech": dict(commits_by_mech),
        "sims": sims,
        "escalations": sum(t.macro_escalations_count for t in history),
        "latencies": lat,
    }


def run_arm_match(seed: int, seat: int, arm: str) -> Dict[str, Any]:
    game = kagsim.Game(seed)
    if arm == "B0":
        trt_cfg = build_phase015_treatment_config()
    elif arm == "B1":
        trt_cfg = build_phase018_arm_b1_config()
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
    ledgers = []
    for t in trt_hist:
        for c in t.candidates:
            ledgers.append({
                "arm": arm, "seed": seed, "seat": seat, "step": t.step,
                "patch_id": c.patch_id, "mechanism": c.mechanism_family,
                "reason": c.candidate_reason or "",
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
        "ctrl_commits": sum(1 for t in getattr(ctrl, "_telemetry_history", [])
                            if t.decision == "COMMIT"),
        "ledgers": ledgers,
    }


def run_task(args: Tuple[int, int, str]) -> Dict[str, Any]:
    return run_arm_match(*args)


def _lat_stats(xs: List[float]) -> Dict[str, float]:
    a = np.asarray(xs, dtype=float)
    return {"mean": float(a.mean()), "median": float(np.median(a)),
            "p95": float(np.percentile(a, 95)), "max": float(a.max()),
            "n": int(len(a))}


def execute_arm_b(max_workers: int = 6) -> Dict[str, Any]:
    verify_v3_sha()
    os.makedirs(RESULTS_DIR, exist_ok=True)
    print("=" * 64)
    print("PHASE018 ARM B: boundary-safe quantity isolated pilot")
    print(f"Seeds {ARM_B_SEEDS[0]}..{ARM_B_SEEDS[-1]} x seats x B0vA0,B1vA0 "
          f"({len(ARM_B_SEEDS) * 4} matches, {max_workers} workers)")
    print("=" * 64)
    tasks = [(s, seat, arm) for s in ARM_B_SEEDS for seat in (0, 1)
             for arm in ("B0", "B1")]
    from concurrent.futures import ProcessPoolExecutor, as_completed
    results: Dict[Tuple[str, int, int], Dict[str, Any]] = {}
    with ProcessPoolExecutor(max_workers=max_workers) as ex:
        futs = {ex.submit(run_task, t): t for t in tasks}
        for f in as_completed(futs):
            args = futs[f]
            r = f.result()
            results[(r["arm"], r["seed"], r["seat"])] = r
            print(f"  [{r['arm']}vA0] seed {r['seed']} seat {r['seat']}: "
                  f"margin={r['margin']:+.0f} trt_commits={r['trt']['commits']} "
                  f"({r['elapsed_s']:.0f}s)")

    with open(LEDGER_CSV, "w", newline="") as f:
        fields = ["arm", "seed", "seat", "step", "patch_id", "mechanism", "reason",
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
                  "elapsed_s"]
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
                "ctrl_commits": r["ctrl_commits"],
                "trt_sims": r["trt"]["sims"],
                "trt_escalations": r["trt"]["escalations"],
                "elapsed_s": round(r["elapsed_s"], 1),
            })

    per_seed = []
    for seed in ARM_B_SEEDS:
        d0 = (results[("B0", seed, 0)]["margin"]
              + results[("B0", seed, 1)]["margin"]) / 2
        d1 = (results[("B1", seed, 0)]["margin"]
              + results[("B1", seed, 1)]["margin"]) / 2
        per_seed.append({"seed": seed, "B0": d0, "B1": d1, "effect": d1 - d0})

    def stats(xs: List[float]) -> Dict[str, float]:
        a = np.asarray(xs, dtype=float)
        se = float(a.std(ddof=1) / np.sqrt(len(a))) if len(a) > 1 else 0.0
        return {"mean": float(a.mean()), "std": float(a.std(ddof=1)) if len(a) > 1 else 0.0,
                "se": se, "ci95": [float(a.mean() - 1.96 * se), float(a.mean() + 1.96 * se)],
                "min": float(a.min()), "max": float(a.max())}

    def wlt(xs: List[float]) -> Dict[str, int]:
        return {"W": sum(1 for x in xs if x > 0), "L": sum(1 for x in xs if x < 0),
                "T": sum(1 for x in xs if x == 0)}

    b0 = [p["B0"] for p in per_seed]
    b1 = [p["B1"] for p in per_seed]
    eff = [p["effect"] for p in per_seed]
    lat: Dict[str, List[float]] = {"B0": [], "B1": []}
    for key, r in results.items():
        lat[key[0]].extend(r["trt"]["latencies"])
    summary = {
        "v3_sha256": V3_EXPECTED_SHA, "v3_verified": True,
        "seeds": ARM_B_SEEDS, "n_matches": len(tasks),
        "B0vA0": {**stats(b0), "wlt": wlt(b0)},
        "B1vA0": {**stats(b1), "wlt": wlt(b1)},
        "quantity_effect_B1_minus_B0": {**stats(eff), "wlt": wlt(eff)},
        "per_seed": per_seed,
        "latency_ms": {arm: _lat_stats(lat[arm]) for arm in ("B0", "B1")},
        "totals": {
            arm: {
                "commits": sum(results[(arm, s, st)]["trt"]["commits"]
                               for s in ARM_B_SEEDS for st in (0, 1)),
                "sims": sum(results[(arm, s, st)]["trt"]["sims"]
                            for s in ARM_B_SEEDS for st in (0, 1)),
                "escalations": sum(results[(arm, s, st)]["trt"]["escalations"]
                                   for s in ARM_B_SEEDS for st in (0, 1)),
            } for arm in ("B0", "B1")
        },
    }
    with open(SUMMARY_JSON, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"B0vA0 mean={summary['B0vA0']['mean']:+.1f} {summary['B0vA0']['wlt']}")
    print(f"B1vA0 mean={summary['B1vA0']['mean']:+.1f} {summary['B1vA0']['wlt']}")
    print(f"effect mean={summary['quantity_effect_B1_minus_B0']['mean']:+.1f}")
    return summary


if __name__ == "__main__":
    execute_arm_b()
