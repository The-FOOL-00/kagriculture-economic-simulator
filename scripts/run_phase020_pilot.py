#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Phase 020: Isolated Fresh Pilot Trial for Multi-Worker Harvest Synchronization (§35).

Cohort: Fresh prospective seeds 249366..249375 (10 seeds, 20 CRN mirror matches).
Evaluates:
  - Treatment: Phase 020 Multi-Worker Harvest Synchronization + Foundation + Reservation
  - Control: Canonical AEC_ROBUST_QUALIFIED foundation control
Measures:
  - Within-seed paired treatment delta
  - Mean, Median, SD, SE, 95% CI
  - Win / Loss / Tie record
  - Mechanism commit attribution
  - Macro escalations, rejections, safety, and latency
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
    build_phase020_treatment_config,
    build_robust_qualified_config,
)
from aec.integration.executor import AECExecutor

V3_TARBALL_PATH = os.path.join(REPO_ROOT, "submission_Vj_kc_v3.tar.gz")
V3_EXPECTED_SHA = "845e0d10981b11b06d272048ff5cee30d70a0403dd757651a556a78c8bf18943"
RESULTS_DIR = os.path.join(REPO_ROOT, "results")

PILOT_SEEDS = list(range(249366, 249376))


def verify_v3_sha() -> None:
    with open(V3_TARBALL_PATH, "rb") as f:
        actual = hashlib.sha256(f.read()).hexdigest()
    if actual != V3_EXPECTED_SHA:
        raise RuntimeError(f"V3 SHA MISMATCH: {actual}")


def run_pilot_match(seed: int, seat: int) -> Dict[str, Any]:
    """Execute one CRN mirror match between Phase 020 treatment and foundation control."""
    game = kagsim.Game(seed)
    trt_cfg = build_phase020_treatment_config()
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
    elapsed = time.time() - t0

    trt_hist = getattr(trt, "_telemetry_history", [])
    commits_by_mech: Counter = Counter()
    candidates_count = 0
    macro_escalations = 0
    macro_rejections = 0
    safety_passes = 0
    ledgers = []

    for t in trt_hist:
        if t.decision == "COMMIT" and t.committed_mechanism:
            commits_by_mech[t.committed_mechanism] += 1

        for c in t.candidates:
            candidates_count += 1
            if c.macro_escalated:
                macro_escalations += 1
            if c.safety_pass:
                safety_passes += 1
            if "MACRO_INCOMPATIBLE" in (c.economic_rejection_reason or ""):
                macro_rejections += 1

            ledgers.append({
                "seed": seed,
                "seat": seat,
                "step": t.step,
                "patch_id": c.patch_id,
                "mechanism": c.mechanism_family,
                "simulated": c.simulation_run,
                "committed": c.commit_decision,
                "pruned": c.patch_pruned,
                "final_delta": c.delta_margin,
                "macro_escalated": c.macro_escalated,
                "safety_pass": c.safety_pass,
            })

    return {
        "seed": seed,
        "seat": seat,
        "trt_reward": r0 if seat == 0 else r1,
        "ctrl_reward": r1 if seat == 0 else r0,
        "margin": margin,
        "elapsed_s": elapsed,
        "trt_commits": sum(commits_by_mech.values()),
        "commits_by_mech": dict(commits_by_mech),
        "candidates_count": candidates_count,
        "macro_escalations": macro_escalations,
        "macro_rejections": macro_rejections,
        "safety_passes": safety_passes,
        "ledgers": ledgers,
    }


def main() -> None:
    verify_v3_sha()
    os.makedirs(RESULTS_DIR, exist_ok=True)

    print("=" * 72)
    print("PHASE 020: ISOLATED FRESH PILOT TRIAL (MULTI-WORKER SYNCHRONIZATION)")
    print(f"Cohort: Seeds {PILOT_SEEDS[0]}..{PILOT_SEEDS[-1]} (10 seeds, 20 CRN mirror matches)")
    print("Treatment: Foundation + MULTIWORKER_HARVEST_SYNCHRONIZATION + Funnel Reservation")
    print("Control: Canonical AEC_ROBUST_QUALIFIED foundation control")
    print("=" * 72)

    tasks = [(s, seat) for s in PILOT_SEEDS for seat in (0, 1)]
    results: Dict[Tuple[int, int], Dict[str, Any]] = {}
    t_start = time.time()

    with ProcessPoolExecutor(max_workers=6) as executor:
        futs = {executor.submit(run_pilot_match, s, seat): (s, seat) for s, seat in tasks}
        for f in as_completed(futs):
            s, seat = futs[f]
            r = f.result()
            results[(s, seat)] = r
            print(f"  [PILOT] seed {s} seat {seat}: margin={r['margin']:+.0f} "
                  f"commits={r['trt_commits']} mechs={r['commits_by_mech']} ({r['elapsed_s']:.1f}s)")

    # Aggregate match records
    matches = []
    all_ledgers = []
    seed_paired_margins = {}

    for (s, seat), r in sorted(results.items()):
        matches.append({
            "seed": s, "seat": seat,
            "trt_reward": r["trt_reward"],
            "ctrl_reward": r["ctrl_reward"],
            "margin": r["margin"],
            "trt_commits": r["trt_commits"],
            "commits_by_mech": json.dumps(r["commits_by_mech"]),
            "elapsed_s": round(r["elapsed_s"], 2),
        })
        all_ledgers.extend(r["ledgers"])

    # Compute within-seed CRN paired differences
    paired_deltas = []
    w_cnt = 0
    l_cnt = 0
    t_cnt = 0

    for s in PILOT_SEEDS:
        m0 = results[(s, 0)]["margin"]
        m1 = results[(s, 1)]["margin"]
        paired_d = 0.5 * (m0 + m1)
        paired_deltas.append(paired_d)
        seed_paired_margins[s] = paired_d
        if paired_d > 0:
            w_cnt += 1
        elif paired_d < 0:
            l_cnt += 1
        else:
            t_cnt += 1

    mean_paired = float(np.mean(paired_deltas))
    median_paired = float(np.median(paired_deltas))
    sd_paired = float(np.std(paired_deltas, ddof=1)) if len(paired_deltas) > 1 else 0.0
    se_paired = sd_paired / np.sqrt(len(paired_deltas))
    ci95 = [float(mean_paired - 1.96 * se_paired), float(mean_paired + 1.96 * se_paired)]

    total_commits = Counter()
    for r in results.values():
        for m, c in r["commits_by_mech"].items():
            total_commits[m] += c

    print("=" * 72)
    print(f"PILOT RESULTS SUMMARY (Cohort {PILOT_SEEDS[0]}..{PILOT_SEEDS[-1]}):")
    print(f"  Mean Paired Delta   : ${mean_paired:+7.2f}")
    print(f"  Median Paired Delta : ${median_paired:+7.2f}")
    print(f"  Standard Error (SE) : ${se_paired:7.2f}")
    print(f"  95% Conf Interval   : [${ci95[0]:.2f}, ${ci95[1]:.2f}]")
    print(f"  Win / Loss / Tie    : {w_cnt}W / {l_cnt}L / {t_cnt}T")
    print(f"  Commits by Mechanism: {dict(total_commits)}")
    print(f"  Total Runtime       : {time.time() - t_start:.1f}s")
    print("=" * 72)

    # Save CSVs
    matches_csv = os.path.join(RESULTS_DIR, "PHASE020_PILOT_MATCHES.csv")
    with open(matches_csv, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(matches[0].keys()))
        writer.writeheader()
        writer.writerows(matches)

    ledger_csv = os.path.join(RESULTS_DIR, "PHASE020_PILOT_LEDGER.csv")
    if all_ledgers:
        with open(ledger_csv, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(all_ledgers[0].keys()))
            writer.writeheader()
            writer.writerows(all_ledgers)

    # Save JSON summary
    summary = {
        "phase": "PHASE020",
        "cohort": [PILOT_SEEDS[0], PILOT_SEEDS[-1]],
        "mean_paired_delta": round(mean_paired, 2),
        "median_paired_delta": round(median_paired, 2),
        "sd_paired_delta": round(sd_paired, 2),
        "se_paired_delta": round(se_paired, 2),
        "ci95": [round(ci95[0], 2), round(ci95[1], 2)],
        "win_loss_tie": [w_cnt, l_cnt, t_cnt],
        "total_commits": dict(total_commits),
        "seed_paired_margins": {str(k): round(v, 2) for k, v in seed_paired_margins.items()},
    }
    summary_json = os.path.join(RESULTS_DIR, "PHASE020_PILOT_SUMMARY.json")
    with open(summary_json, "w") as f:
        json.dump(summary, f, indent=2)


if __name__ == "__main__":
    main()
