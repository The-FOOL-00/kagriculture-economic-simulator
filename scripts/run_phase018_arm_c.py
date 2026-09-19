#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Phase 018 Arm C: trigger-timing variant pilot (preregistered).

Fresh cohort: seeds 249326..249335 (10 seeds, CRN mirror matches).
Legs (legacy funnel all legs, per preregistration; common A0 control):
  - C0: treatment-A1 (current trigger).
  - C1: + Class-A persistence (2 consecutive favorable turns).
  - C2: + Class-A $15 premium floor.
  - C3: + Class-A 2-turn V3-tape separation.
Variants independent, never stacked. 80 matches total.

Produces results/PHASE018_ARM_C_{MATCHES,LEDGER,FIRING,SUMMARY}.{csv,csv,csv,json}.
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
    build_phase018_arm_c1_config,
    build_phase018_arm_c2_config,
    build_phase018_arm_c3_config,
    build_robust_qualified_config,
)
from aec.integration.executor import AECExecutor

V3_TARBALL_PATH = os.path.join(REPO_ROOT, "submission_Vj_kc_v3.tar.gz")
V3_EXPECTED_SHA = "845e0d10981b11b06d272048ff5cee30d70a0403dd757651a556a78c8bf18943"
RESULTS_DIR = os.path.join(REPO_ROOT, "results")
MATCHES_CSV = os.path.join(RESULTS_DIR, "PHASE018_ARM_C_MATCHES.csv")
LEDGER_CSV = os.path.join(RESULTS_DIR, "PHASE018_ARM_C_LEDGER.csv")
FIRING_CSV = os.path.join(RESULTS_DIR, "PHASE018_ARM_C_FIRING.csv")
SUMMARY_JSON = os.path.join(RESULTS_DIR, "PHASE018_ARM_C_SUMMARY.json")

ARM_C_SEEDS = list(range(249326, 249336))
LEGS = ("C0", "C1", "C2", "C3")


def verify_v3_sha() -> None:
    with open(V3_TARBALL_PATH, "rb") as f:
        actual = hashlib.sha256(f.read()).hexdigest()
    if actual != V3_EXPECTED_SHA:
        raise RuntimeError(f"V3 SHA MISMATCH: {actual}")


def _trt_config(leg: str):
    return {
        "C0": build_phase015_treatment_config,
        "C1": build_phase018_arm_c1_config,
        "C2": build_phase018_arm_c2_config,
        "C3": build_phase018_arm_c3_config,
    }[leg]()


def run_arm_match(seed: int, seat: int, leg: str) -> Dict[str, Any]:
    game = kagsim.Game(seed)
    trt = AECExecutor(config=_trt_config(leg))
    ctrl = AECExecutor(config=build_robust_qualified_config())
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
    ledgers, firings = [], []
    for t in trt_hist:
        for c in t.candidates:
            ledgers.append({
                "leg": leg, "seed": seed, "seat": seat, "step": t.step,
                "patch_id": c.patch_id, "mechanism": c.mechanism_family,
                "reason": c.candidate_reason or "",
                "simulated": c.simulation_run, "committed": c.commit_decision,
                "final_delta": c.delta_margin, "local_delta": c.delta_money_realized,
                "macro_escalated": c.macro_escalated,
                "macro_regime": c.macro_regime_type,
                "safety_pass": c.safety_pass, "quantity": c.candidate_quantity,
            })
        for fr in (t.trigger_firings or []):
            firings.append({"leg": leg, "seed": seed, "seat": seat, **fr})
    commits_by_mech: Counter = Counter()
    for t in trt_hist:
        if t.decision == "COMMIT" and t.committed_mechanism:
            commits_by_mech[t.committed_mechanism] += 1
    return {
        "leg": leg, "seed": seed, "seat": seat,
        "trt_reward": r0 if seat == 0 else r1,
        "ctrl_reward": r1 if seat == 0 else r0,
        "margin": margin, "elapsed_s": time.time() - t0,
        "trt_commits": sum(commits_by_mech.values()),
        "trt_commits_by_mech": dict(commits_by_mech),
        "trt_sims": sum(t.simulations_run for t in trt_hist),
        "trt_escalations": sum(t.macro_escalations_count for t in trt_hist),
        "n_firings": len(firings),
        "latencies": [float(t.total_time_ms) for t in trt_hist],
        "ctrl_commits": sum(1 for t in getattr(ctrl, "_telemetry_history", [])
                            if t.decision == "COMMIT"),
        "ledgers": ledgers, "firings": firings,
    }


def run_task(args: Tuple[int, int, str]) -> Dict[str, Any]:
    return run_arm_match(*args)


def execute_arm_c(max_workers: int = 6) -> Dict[str, Any]:
    verify_v3_sha()
    os.makedirs(RESULTS_DIR, exist_ok=True)
    print("=" * 64)
    print("PHASE018 ARM C: trigger-timing variants (80 matches)")
    print(f"Seeds {ARM_C_SEEDS[0]}..{ARM_C_SEEDS[-1]} x seats x C0,C1,C2,C3")
    print("=" * 64)
    tasks = [(s, seat, leg) for s in ARM_C_SEEDS for seat in (0, 1) for leg in LEGS]
    from concurrent.futures import ProcessPoolExecutor, as_completed
    results: Dict[Tuple[str, int, int], Dict[str, Any]] = {}
    with ProcessPoolExecutor(max_workers=max_workers) as ex:
        futs = {ex.submit(run_task, t): t for t in tasks}
        for f in as_completed(futs):
            r = f.result()
            results[(r["leg"], r["seed"], r["seat"])] = r
            print(f"  [{r['leg']}] seed {r['seed']} seat {r['seat']}: "
                  f"margin={r['margin']:+.0f} commits={r['trt_commits']} "
                  f"firings={r['n_firings']} ({r['elapsed_s']:.0f}s)")

    with open(LEDGER_CSV, "w", newline="") as f:
        fields = ["leg", "seed", "seat", "step", "patch_id", "mechanism", "reason",
                  "simulated", "committed", "final_delta", "local_delta",
                  "macro_escalated", "macro_regime", "safety_pass", "quantity"]
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for key in sorted(results):
            for row in results[key]["ledgers"]:
                w.writerow(row)

    with open(FIRING_CSV, "w", newline="") as f:
        fields = ["leg", "seed", "seat", "step", "commodity", "quantity_held",
                  "uncommitted_quantity", "current_price", "price_ratio",
                  "price_trajectory", "emitted", "suppressed_by"]
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for key in sorted(results):
            for row in results[key]["firings"]:
                w.writerow({k: row.get(k, "") for k in fields})

    with open(MATCHES_CSV, "w", newline="") as f:
        fields = ["leg", "seed", "seat", "trt_reward", "ctrl_reward", "margin",
                  "trt_commits", "ctrl_commits", "trt_sims", "trt_escalations",
                  "n_firings", "elapsed_s"]
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for key in sorted(results):
            r = results[key]
            w.writerow({
                "leg": r["leg"], "seed": r["seed"], "seat": r["seat"],
                "trt_reward": round(r["trt_reward"], 1),
                "ctrl_reward": round(r["ctrl_reward"], 1),
                "margin": round(r["margin"], 1),
                "trt_commits": r["trt_commits"], "ctrl_commits": r["ctrl_commits"],
                "trt_sims": r["trt_sims"], "trt_escalations": r["trt_escalations"],
                "n_firings": r["n_firings"], "elapsed_s": round(r["elapsed_s"], 1),
            })

    per_seed = []
    for seed in ARM_C_SEEDS:
        row = {"seed": seed}
        for leg in LEGS:
            row[leg] = (results[(leg, seed, 0)]["margin"]
                        + results[(leg, seed, 1)]["margin"]) / 2
        for v in ("C1", "C2", "C3"):
            row[f"{v}_effect"] = row[v] - row["C0"]
        per_seed.append(row)

    def stats(xs: List[float]) -> Dict[str, float]:
        a = np.asarray(xs, dtype=float)
        se = float(a.std(ddof=1) / np.sqrt(len(a))) if len(a) > 1 else 0.0
        return {"mean": float(a.mean()), "std": float(a.std(ddof=1)) if len(a) > 1 else 0.0,
                "se": se, "ci95": [float(a.mean() - 1.96 * se), float(a.mean() + 1.96 * se)],
                "min": float(a.min()), "max": float(a.max())}

    def wlt(xs: List[float]) -> Dict[str, int]:
        return {"W": sum(1 for x in xs if x > 0), "L": sum(1 for x in xs if x < 0),
                "T": sum(1 for x in xs if x == 0)}

    summary = {
        "v3_sha256": V3_EXPECTED_SHA, "v3_verified": True,
        "seeds": ARM_C_SEEDS, "n_matches": len(tasks),
        **{leg: {**stats([p[leg] for p in per_seed]),
                   "wlt": wlt([p[leg] for p in per_seed])} for leg in LEGS},
        **{f"{v}_minus_C0": {**stats([p[f"{v}_effect"] for p in per_seed]),
                             "wlt": wlt([p[f"{v}_effect"] for p in per_seed])}
           for v in ("C1", "C2", "C3")},
        "per_seed": per_seed,
        "totals": {
            leg: {
                "commits": sum(results[(leg, s, st)]["trt_commits"]
                               for s in ARM_C_SEEDS for st in (0, 1)),
                "sims": sum(results[(leg, s, st)]["trt_sims"]
                            for s in ARM_C_SEEDS for st in (0, 1)),
                "firings": sum(results[(leg, s, st)]["n_firings"]
                               for s in ARM_C_SEEDS for st in (0, 1)),
            } for leg in LEGS
        },
    }
    with open(SUMMARY_JSON, "w") as f:
        json.dump(summary, f, indent=2)
    for leg in LEGS:
        print(f"{leg} mean={summary[leg]['mean']:+.1f} {summary[leg]['wlt']}")
    return summary


if __name__ == "__main__":
    execute_arm_c()
