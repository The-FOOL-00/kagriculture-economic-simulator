#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Phase 019: Fresh Prospective Diagnostic Pilot (Arm U1 vs A0 Control).

Cohort: Seeds 249336..249345 (10 seeds, CRN mirror matches, 20 matches total).
Evaluates:
  - U1 treatment: Phase015 treatment + reservation + discrimination + shadow robustness audit.
  - A0 control: live qualified foundation control.
Measures:
  - Within-seed paired treatment delta
  - Shadow robustness categorization (R0..R5)
  - Selection regret, abstention regret, foundation opportunity cost
  - Candidate-level perturbation sensitivity
"""

from __future__ import annotations

import csv
import hashlib
import json
import os
import sys
import time
from collections import Counter
from concurrent.futures import ProcessPoolExecutor, as_completed
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
    build_phase019_u0_config,
    build_phase019_u1_config,
    build_phase019_u2_config,
    build_phase019_u3_config,
    build_robust_qualified_config,
)
from aec.integration.executor import AECExecutor

V3_TARBALL_PATH = os.path.join(REPO_ROOT, "submission_Vj_kc_v3.tar.gz")
V3_EXPECTED_SHA = "845e0d10981b11b06d272048ff5cee30d70a0403dd757651a556a78c8bf18943"
RESULTS_DIR = os.path.join(REPO_ROOT, "results")

DIAGNOSTIC_SEEDS = list(range(249336, 249346))
REPAIR_SEEDS = list(range(249346, 249356))


def verify_v3_sha() -> None:
    with open(V3_TARBALL_PATH, "rb") as f:
        actual = hashlib.sha256(f.read()).hexdigest()
    if actual != V3_EXPECTED_SHA:
        raise RuntimeError(f"V3 SHA MISMATCH: {actual}")


def run_match(seed: int, seat: int, arm: str) -> Dict[str, Any]:
    """Execute one CRN mirror match between treatment arm and A0 foundation control."""
    game = kagsim.Game(seed)
    if arm == "U0":
        trt_cfg = build_phase019_u0_config()
    elif arm == "U1":
        trt_cfg = build_phase019_u1_config()
    elif arm == "U2":
        trt_cfg = build_phase019_u2_config()
    elif arm == "U3":
        trt_cfg = build_phase019_u3_config()
    else:
        raise ValueError(f"Unknown arm: {arm}")

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
    shadow_records = []
    commits_by_mech: Counter = Counter()

    for t in trt_hist:
        if t.decision == "COMMIT" and t.committed_mechanism:
            commits_by_mech[t.committed_mechanism] += 1

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

        for s in getattr(t, "shadow_records", []):
            shadow_records.append({
                "arm": arm, "seed": seed, "seat": seat,
                "step": s.get("step"),
                "patch_id": s.get("committed_patch_id"),
                "mechanism": s.get("committed_mechanism"),
                "committed_delta": s.get("committed_delta"),
                "best_alt_id": s.get("best_admissible_alt_id"),
                "best_alt_delta": s.get("best_admissible_alt_delta"),
                "selection_regret": s.get("selection_regret"),
                "abstention_regret": s.get("abstention_regret"),
                "foundation_patch_id": s.get("foundation_patch_id"),
                "foundation_delta": s.get("foundation_delta"),
                "foundation_opportunity_cost": s.get("foundation_opportunity_cost"),
                "category": s.get("category"),
                "would_abstain": s.get("would_abstain"),
                "min_neighbor_delta": s.get("vector", {}).get("min_neighbor_delta"),
                "max_neighbor_delta": s.get("vector", {}).get("max_neighbor_delta"),
                "sign_stability": s.get("vector", {}).get("sign_stability"),
                "quantity_sensitivity": s.get("vector", {}).get("quantity_sensitivity"),
                "safety_margin": s.get("vector", {}).get("safety_margin"),
                "notes": s.get("notes"),
            })

    return {
        "arm": arm, "seed": seed, "seat": seat,
        "trt_reward": r0 if seat == 0 else r1,
        "ctrl_reward": r1 if seat == 0 else r0,
        "margin": margin,
        "elapsed_s": time.time() - t0,
        "trt_commits": sum(commits_by_mech.values()),
        "commits_by_mech": dict(commits_by_mech),
        "ledgers": ledgers,
        "shadow_records": shadow_records,
    }


def run_cohort(seeds: List[int], arm: str, max_workers: int = 6) -> Dict[str, Any]:
    verify_v3_sha()
    os.makedirs(RESULTS_DIR, exist_ok=True)
    print("=" * 64)
    print(f"PHASE 019: Executing Arm {arm} on Seeds {seeds[0]}..{seeds[-1]}")
    print(f"{len(seeds)} seeds x 2 seats = {len(seeds) * 2} CRN mirror matches")
    print("=" * 64)

    tasks = [(s, seat, arm) for s in seeds for seat in (0, 1)]
    results: Dict[Tuple[int, int], Dict[str, Any]] = {}

    with ProcessPoolExecutor(max_workers=max_workers) as ex:
        futs = {ex.submit(run_match, s, seat, arm): (s, seat) for s, seat, _ in tasks}
        for f in as_completed(futs):
            s, seat = futs[f]
            r = f.result()
            results[(s, seat)] = r
            print(f"  [{arm}vA0] seed {s} seat {seat}: margin={r['margin']:+.0f} "
                  f"commits={r['trt_commits']} mechs={r['commits_by_mech']} ({r['elapsed_s']:.1f}s)")

    # Aggregate match records
    matches = []
    all_ledgers = []
    all_shadow = []
    seed_paired_margins = {}

    for (s, seat), r in sorted(results.items()):
        matches.append({
            "arm": arm, "seed": s, "seat": seat,
            "trt_reward": r["trt_reward"], "ctrl_reward": r["ctrl_reward"],
            "margin": r["margin"], "elapsed_s": round(r["elapsed_s"], 2),
            "commits": r["trt_commits"],
            "commits_by_mech": json.dumps(r["commits_by_mech"]),
        })
        all_ledgers.extend(r["ledgers"])
        all_shadow.extend(r["shadow_records"])
        seed_paired_margins.setdefault(s, []).append(r["margin"])

    paired_deltas = [float(np.mean(margins)) for s, margins in sorted(seed_paired_margins.items())]
    mean_delta = float(np.mean(paired_deltas))
    median_delta = float(np.median(paired_deltas))
    std_delta = float(np.std(paired_deltas, ddof=1)) if len(paired_deltas) > 1 else 0.0
    se = std_delta / (len(paired_deltas) ** 0.5) if len(paired_deltas) > 0 else 0.0
    ci95 = [float(mean_delta - 1.96 * se), float(mean_delta + 1.96 * se)]

    wins = sum(1 for d in paired_deltas if d > 0)
    losses = sum(1 for d in paired_deltas if d < 0)
    ties = sum(1 for d in paired_deltas if d == 0)

    # Save CSV outputs
    matches_csv = os.path.join(RESULTS_DIR, f"PHASE019_{arm}_MATCHES.csv")
    with open(matches_csv, "w", newline="") as f:
        if matches:
            w = csv.DictWriter(f, fieldnames=matches[0].keys())
            w.writeheader()
            w.writerows(matches)

    ledger_csv = os.path.join(RESULTS_DIR, f"PHASE019_{arm}_LEDGER.csv")
    with open(ledger_csv, "w", newline="") as f:
        if all_ledgers:
            w = csv.DictWriter(f, fieldnames=all_ledgers[0].keys())
            w.writeheader()
            w.writerows(all_ledgers)

    shadow_csv = os.path.join(RESULTS_DIR, f"PHASE019_{arm}_SHADOW_RECORDS.csv")
    with open(shadow_csv, "w", newline="") as f:
        if all_shadow:
            w = csv.DictWriter(f, fieldnames=all_shadow[0].keys())
            w.writeheader()
            w.writerows(all_shadow)

    summary = {
        "arm": arm,
        "seeds": seeds,
        "matches_count": len(matches),
        "mean_paired_delta": round(mean_delta, 2),
        "median_paired_delta": round(median_delta, 2),
        "std_delta": round(std_delta, 2),
        "ci95": [round(c, 2) for c in ci95],
        "win_loss_tie": [wins, losses, ties],
        "total_commits": sum(m["commits"] for m in matches),
        "paired_deltas_by_seed": {s: round(d, 2) for s, d in zip(sorted(seed_paired_margins.keys()), paired_deltas)},
        "shadow_records_count": len(all_shadow),
    }

    summary_json = os.path.join(RESULTS_DIR, f"PHASE019_{arm}_SUMMARY.json")
    with open(summary_json, "w") as f:
        json.dump(summary, f, indent=2)

    print("\n" + "=" * 64)
    print(f"ARM {arm} RESULTS:")
    print(f"  Mean Paired Delta:   {mean_delta:+.2f}")
    print(f"  Median Paired Delta: {median_delta:+.2f}")
    print(f"  95% CI:              [{ci95[0]:+.2f}, {ci95[1]:+.2f}]")
    print(f"  Win/Loss/Tie:        {wins}W / {losses}L / {ties}T")
    print(f"  Shadow Records:      {len(all_shadow)}")
    print("=" * 64)

    return summary


def main():
    arm = sys.argv[1] if len(sys.argv) > 1 else "U1"
    seeds = REPAIR_SEEDS if arm in ("U2", "U3", "U4") else DIAGNOSTIC_SEEDS
    run_cohort(seeds=seeds, arm=arm, max_workers=6)


if __name__ == "__main__":
    main()
