#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Phase 018 Arm B2: S7 discrimination + boundary-menu retest (preregistered).

Fresh cohort: seeds 249316..249325 (10 seeds, CRN mirror matches).
Legs (matched funnels per leg, common-control structure):
  - S0 : treatment-A1 vs control-A0, legacy funnel (replicates B0vA0; sanity).
  - S1 : treatment-S1 vs control-B2ctrl, discrimination ON, legacy quantities.
  - S1B: treatment-S1B vs control-B2ctrl, discrimination ON + boundary menu.
Effects: S1-S0 (joint discrimination), S1B-S1 (true menu effect).
Reservation OFF in all legs. 60 matches total.

Produces results/PHASE018_ARM_B2_{MATCHES,LEDGER,SUMMARY}.{csv,csv,json}.
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
    build_phase018_arm_b2_control_config,
    build_phase018_arm_b2_s1_config,
    build_phase018_arm_b2_s1b_config,
    build_robust_qualified_config,
)
from aec.integration.executor import AECExecutor

V3_TARBALL_PATH = os.path.join(REPO_ROOT, "submission_Vj_kc_v3.tar.gz")
V3_EXPECTED_SHA = "845e0d10981b11b06d272048ff5cee30d70a0403dd757651a556a78c8bf18943"
RESULTS_DIR = os.path.join(REPO_ROOT, "results")
MATCHES_CSV = os.path.join(RESULTS_DIR, "PHASE018_ARM_B2_MATCHES.csv")
LEDGER_CSV = os.path.join(RESULTS_DIR, "PHASE018_ARM_B2_LEDGER.csv")
SUMMARY_JSON = os.path.join(RESULTS_DIR, "PHASE018_ARM_B2_SUMMARY.json")

ARM_B2_SEEDS = list(range(249316, 249326))
LEGS = ("S0", "S1", "S1B")


def verify_v3_sha() -> None:
    with open(V3_TARBALL_PATH, "rb") as f:
        actual = hashlib.sha256(f.read()).hexdigest()
    if actual != V3_EXPECTED_SHA:
        raise RuntimeError(f"V3 SHA MISMATCH: {actual}")


def _configs(leg: str):
    if leg == "S0":
        return build_phase015_treatment_config(), build_robust_qualified_config()
    if leg == "S1":
        return build_phase018_arm_b2_s1_config(), build_phase018_arm_b2_control_config()
    if leg == "S1B":
        return build_phase018_arm_b2_s1b_config(), build_phase018_arm_b2_control_config()
    raise ValueError(leg)


def run_arm_match(seed: int, seat: int, leg: str) -> Dict[str, Any]:
    game = kagsim.Game(seed)
    trt_cfg, ctrl_cfg = _configs(leg)
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
                "leg": leg, "seed": seed, "seat": seat, "step": t.step,
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
        "sims_per_turn": [t.simulations_run for t in trt_hist],
        "latencies": [float(t.total_time_ms) for t in trt_hist],
        "ctrl_commits": sum(1 for t in getattr(ctrl, "_telemetry_history", [])
                            if t.decision == "COMMIT"),
        "ledgers": ledgers,
    }


def run_task(args: Tuple[int, int, str]) -> Dict[str, Any]:
    return run_arm_match(*args)


def execute_arm_b2(max_workers: int = 6) -> Dict[str, Any]:
    verify_v3_sha()
    os.makedirs(RESULTS_DIR, exist_ok=True)
    print("=" * 64)
    print("PHASE018 ARM B2: discrimination + menu retest (60 matches)")
    print(f"Seeds {ARM_B2_SEEDS[0]}..{ARM_B2_SEEDS[-1]} x seats x S0,S1,S1B")
    print("=" * 64)
    tasks = [(s, seat, leg) for s in ARM_B2_SEEDS for seat in (0, 1) for leg in LEGS]
    from concurrent.futures import ProcessPoolExecutor, as_completed
    results: Dict[Tuple[str, int, int], Dict[str, Any]] = {}
    with ProcessPoolExecutor(max_workers=max_workers) as ex:
        futs = {ex.submit(run_task, t): t for t in tasks}
        for f in as_completed(futs):
            r = f.result()
            results[(r["leg"], r["seed"], r["seat"])] = r
            print(f"  [{r['leg']}] seed {r['seed']} seat {r['seat']}: "
                  f"margin={r['margin']:+.0f} commits={r['trt_commits']} "
                  f"sims={r['trt_sims']} ({r['elapsed_s']:.0f}s)")

    with open(LEDGER_CSV, "w", newline="") as f:
        fields = ["leg", "seed", "seat", "step", "patch_id", "mechanism", "reason",
                  "simulated", "committed", "pruned", "final_delta",
                  "local_delta", "macro_escalated", "macro_regime",
                  "safety_pass", "quantity"]
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for key in sorted(results):
            for row in results[key]["ledgers"]:
                w.writerow(row)

    with open(MATCHES_CSV, "w", newline="") as f:
        fields = ["leg", "seed", "seat", "trt_reward", "ctrl_reward", "margin",
                  "trt_commits", "ctrl_commits", "trt_sims", "trt_escalations",
                  "elapsed_s"]
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for key in sorted(results):
            r = results[key]
            w.writerow({
                "leg": r["leg"], "seed": r["seed"], "seat": r["seat"],
                "trt_reward": round(r["trt_reward"], 1),
                "ctrl_reward": round(r["ctrl_reward"], 1),
                "margin": round(r["margin"], 1),
                "trt_commits": r["trt_commits"],
                "ctrl_commits": r["ctrl_commits"],
                "trt_sims": r["trt_sims"],
                "trt_escalations": r["trt_escalations"],
                "elapsed_s": round(r["elapsed_s"], 1),
            })

    per_seed = []
    for seed in ARM_B2_SEEDS:
        row = {"seed": seed}
        for leg in LEGS:
            row[leg] = (results[(leg, seed, 0)]["margin"]
                        + results[(leg, seed, 1)]["margin"]) / 2
        row["discr_effect"] = row["S1"] - row["S0"]
        row["menu_effect"] = row["S1B"] - row["S1"]
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

    legs = {leg: [p[leg] for p in per_seed] for leg in LEGS}
    deff = [p["discr_effect"] for p in per_seed]
    meff = [p["menu_effect"] for p in per_seed]

    def lat(xs: List[float]) -> Dict[str, float]:
        a = np.asarray(xs, dtype=float)
        return {"mean": float(a.mean()), "median": float(np.median(a)),
                "p95": float(np.percentile(a, 95)), "max": float(a.max())}

    summary = {
        "v3_sha256": V3_EXPECTED_SHA, "v3_verified": True,
        "seeds": ARM_B2_SEEDS, "n_matches": len(tasks),
        **{leg: {**stats(legs[leg]), "wlt": wlt(legs[leg])} for leg in LEGS},
        "discrimination_effect_S1_minus_S0": {**stats(deff), "wlt": wlt(deff)},
        "menu_effect_S1B_minus_S1": {**stats(meff), "wlt": wlt(meff)},
        "per_seed": per_seed,
        "latency_ms": {
            leg: lat([t for key, r in results.items() if key[0] == leg
                      for t in r["latencies"]]) for leg in LEGS
        },
        "sims_per_turn_hist": {
            leg: {str(k): v for k, v in sorted(Counter(
                t for key, r in results.items() if key[0] == leg
                for t in r["sims_per_turn"]).items())} for leg in LEGS
        },
        "totals": {
            leg: {
                "commits": sum(results[(leg, s, st)]["trt_commits"]
                               for s in ARM_B2_SEEDS for st in (0, 1)),
                "sims": sum(results[(leg, s, st)]["trt_sims"]
                            for s in ARM_B2_SEEDS for st in (0, 1)),
                "escalations": sum(results[(leg, s, st)]["trt_escalations"]
                                   for s in ARM_B2_SEEDS for st in (0, 1)),
            } for leg in LEGS
        },
    }
    with open(SUMMARY_JSON, "w") as f:
        json.dump(summary, f, indent=2)
    for leg in LEGS:
        print(f"{leg} mean={summary[leg]['mean']:+.1f} {summary[leg]['wlt']}")
    print(f"discr effect={summary['discrimination_effect_S1_minus_S0']['mean']:+.1f}")
    print(f"menu effect={summary['menu_effect_S1B_minus_S1']['mean']:+.1f}")
    return summary


if __name__ == "__main__":
    execute_arm_b2()
