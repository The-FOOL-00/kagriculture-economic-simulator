#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Phase 017: Comprehensive Outcome Attribution and Overblocking Audit Harness (§6, §7, §8, §9, §10, §11, §12, §13, §14).

Executes CRN mirror matches on the Phase 016 pilot cohort (seeds 249286..249295),
intercepting full candidate-level decision trails for both Treatment and Control to:
1. Build the Candidate Outcome Attribution Ledger (local vs macro vs terminal).
2. Quantify Overblocking across Categories O1, O2, O3, O4.
3. Measure Macro Probe Escalation Precision and Recall.
4. Construct the Macro Divergence Taxonomy.
5. Deconstruct Seed-by-Seed Divergences (including control-commit crowding).
6. Build the Headroom Survival Funnel.

Produces:
- results/PHASE017_ATTRIBUTION_LEDGER.csv
- results/PHASE017_CONTROL_COMMITS.csv
- results/PHASE017_ATTRIBUTION_SUMMARY.json
"""

from __future__ import annotations

import copy
import csv
import hashlib
import json
import math
import os
import sys
import tarfile
import time
from collections import Counter, defaultdict
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

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
V3_EXPECTED_SHA = "845e0d10981b11b06d272048ff5cee30d70a0403dd757651a556a78c8bf18943"

RESULTS_DIR = os.path.join(REPO_ROOT, "results")
LEDGER_CSV = os.path.join(RESULTS_DIR, "PHASE017_ATTRIBUTION_LEDGER.csv")
CTRL_COMMITS_CSV = os.path.join(RESULTS_DIR, "PHASE017_CONTROL_COMMITS.csv")
SUMMARY_JSON = os.path.join(RESULTS_DIR, "PHASE017_ATTRIBUTION_SUMMARY.json")

PILOT_SEEDS = list(range(249286, 249296))


def verify_v3_sha() -> None:
    with open(V3_TARBALL_PATH, "rb") as f:
        actual_sha = hashlib.sha256(f.read()).hexdigest()
    if actual_sha != V3_EXPECTED_SHA:
        raise RuntimeError(f"V3 SHA MISMATCH: expected {V3_EXPECTED_SHA}, got {actual_sha}")


def run_attribution_match(
    seed: int,
    treatment_seat: int,
    treatment_config: AECConfig,
    control_config: AECConfig,
) -> Dict[str, Any]:
    """Runs a single paired mirror match and collects exhaustive telemetry."""
    game = kagsim.Game(seed)
    trt_executor = AECExecutor(config=treatment_config)
    ctrl_executor = AECExecutor(config=control_config)

    t_start = time.time()

    while not game.done:
        o0 = game.observe(0)
        o1 = game.observe(1)

        if treatment_seat == 0:
            a0 = trt_executor.act(o0)
            a1 = ctrl_executor.act(o1)
        else:
            a0 = ctrl_executor.act(o0)
            a1 = trt_executor.act(o1)

        game.step(a0, a1)

    r0 = float(game.reward(0))
    r1 = float(game.reward(1))
    trt_reward = r0 if treatment_seat == 0 else r1
    ctrl_reward = r1 if treatment_seat == 0 else r0
    margin = trt_reward - ctrl_reward

    trt_history = getattr(trt_executor, "_telemetry_history", [])
    ctrl_history = getattr(ctrl_executor, "_telemetry_history", [])

    # Extract Treatment Candidates
    candidate_records: List[Dict[str, Any]] = []
    for t in trt_history:
        step = t.step
        for c in t.candidates:
            # Reconstruct decomposition
            # direct_effect: cash delta at turn 0
            # macro_continuation_delta: downstream policy divergence delta
            # final_delta: delta_margin
            direct_effect = c.delta_money_realized
            final_delta = c.delta_margin
            macro_effect = final_delta - direct_effect

            # Overblocking classifications (§9):
            # O1: Escalated because of macro risk, but remained economically favorable (final_delta > 0)
            is_o1 = bool(c.macro_escalated and final_delta > 0.0)
            # O2: Escalated and rejected, but final_delta was actually > 0
            is_o2 = bool(c.macro_escalated and not c.commit_decision and final_delta > 0.0)
            # O3: Rejected solely due to macro boundary crossing even though harmless (final_delta >= 0)
            is_o3 = bool(c.macro_escalated and not c.commit_decision and final_delta >= 0.0 and c.safety_pass)
            # O4: Locally positive (delta_money_realized > 0 or short horizon positive) but rejected after long continuation
            is_o4 = bool(direct_effect > 0.0 and c.macro_escalated and not c.commit_decision)

            rec = {
                "seed": seed,
                "seat": treatment_seat,
                "step": step,
                "patch_id": c.patch_id,
                "mechanism": c.mechanism_family,
                "quantity": c.candidate_quantity,
                "reason": c.candidate_reason or "",
                "why_v3_omitted": c.why_v3_did_not_do_this or "",
                "simulated": c.simulation_run,
                "horizon": c.simulation_horizon,
                "local_delta": direct_effect,
                "macro_effect": macro_effect,
                "final_delta": final_delta,
                "macro_escalated": c.macro_escalated,
                "macro_regime": c.macro_regime_type,
                "escalation_reason": c.macro_escalation_reason or "",
                "first_div_turn": c.first_divergence_turn if c.first_divergence_turn is not None else -1,
                "safety_pass": c.safety_pass,
                "safety_rejection": c.safety_rejection_reason or "",
                "economic_rejection": c.economic_rejection_reason or "",
                "committed": c.commit_decision,
                "is_o1": is_o1,
                "is_o2": is_o2,
                "is_o3": is_o3,
                "is_o4": is_o4,
            }
            candidate_records.append(rec)

    # Extract Control Commits
    control_commits: List[Dict[str, Any]] = []
    for t in ctrl_history:
        if t.decision == "COMMIT":
            committed_cands = [c for c in t.candidates if c.commit_decision]
            c_delta = committed_cands[0].delta_margin if committed_cands else 0.0
            control_commits.append({
                "seed": seed,
                "seat": 1 - treatment_seat,
                "step": t.step,
                "mechanism": t.committed_mechanism,
                "patch_id": t.committed_patch_id,
                "delta_margin": c_delta,
            })

    return {
        "seed": seed,
        "seat": treatment_seat,
        "trt_reward": trt_reward,
        "ctrl_reward": ctrl_reward,
        "margin": margin,
        "elapsed_s": time.time() - t_start,
        "candidate_records": candidate_records,
        "control_commits": control_commits,
        "trt_commits": sum(1 for t in trt_history if t.decision == "COMMIT"),
        "trt_sims": sum(t.simulations_run for t in trt_history),
        "trt_escalations": sum(t.macro_escalations_count for t in trt_history),
    }


def run_match_task(args: Tuple[int, int]) -> Dict[str, Any]:
    seed, treatment_seat = args
    treatment_config = build_phase015_treatment_config()
    control_config = build_robust_qualified_config()
    return run_attribution_match(seed, treatment_seat, treatment_config, control_config)


def execute_attribution_audit(max_workers: int = 6) -> Dict[str, Any]:
    verify_v3_sha()
    os.makedirs(RESULTS_DIR, exist_ok=True)

    print(f"================================================================")
    print(f"PHASE 017: OUTCOME ATTRIBUTION & OVERBLOCKING AUDIT HARNESS")
    print(f"Seeds: {PILOT_SEEDS[0]}..{PILOT_SEEDS[-1]} (20 mirror matches under CRN, {max_workers} workers)")
    print(f"V3 Chassis SHA-256 Verified: {V3_EXPECTED_SHA}")
    print(f"================================================================")

    tasks = []
    for seed in PILOT_SEEDS:
        tasks.append((seed, 0))
        tasks.append((seed, 1))

    all_candidate_records: List[Dict[str, Any]] = []
    all_control_commits: List[Dict[str, Any]] = []
    match_results: Dict[Tuple[int, int], Dict[str, Any]] = {}

    t0_total = time.time()
    from concurrent.futures import ProcessPoolExecutor, as_completed

    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        future_map = {executor.submit(run_match_task, t): t for t in tasks}
        for future in as_completed(future_map):
            seed, seat = future_map[future]
            res = future.result()
            match_results[(seed, seat)] = res
            all_candidate_records.extend(res["candidate_records"])
            all_control_commits.extend(res["control_commits"])
            print(f"  [Match Done] Seed {seed} Seat {seat}: Margin=${res['margin']:+,.1f} | Commits: Trt={res['trt_commits']}, Ctrl={len(res['control_commits'])} | Esc={res['trt_escalations']} in {res['elapsed_s']:.1f}s")

    seed_summaries: List[Dict[str, Any]] = []
    for seed in PILOT_SEEDS:
        m0 = match_results[(seed, 0)]
        m1 = match_results[(seed, 1)]
        paired_margin = (m0["margin"] + m1["margin"]) / 2.0
        seed_summaries.append({
            "seed": seed,
            "s0_margin": m0["margin"],
            "s1_margin": m1["margin"],
            "paired_margin": paired_margin,
            "s0_trt_commits": m0["trt_commits"],
            "s1_trt_commits": m1["trt_commits"],
            "s0_ctrl_commits": len(m0["control_commits"]),
            "s1_ctrl_commits": len(m1["control_commits"]),
            "s0_escalations": m0["trt_escalations"],
            "s1_escalations": m1["trt_escalations"],
        })

    # Save Candidate Attribution Ledger CSV
    fieldnames = [
        "seed", "seat", "step", "patch_id", "mechanism", "quantity", "reason",
        "why_v3_omitted", "simulated", "horizon", "local_delta", "macro_effect",
        "final_delta", "macro_escalated", "macro_regime", "escalation_reason",
        "first_div_turn", "safety_pass", "safety_rejection", "economic_rejection",
        "committed", "is_o1", "is_o2", "is_o3", "is_o4"
    ]
    with open(LEDGER_CSV, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in all_candidate_records:
            writer.writerow(r)

    # Save Control Commits CSV
    ctrl_fields = ["seed", "seat", "step", "mechanism", "patch_id", "delta_margin"]
    with open(CTRL_COMMITS_CSV, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=ctrl_fields)
        writer.writeheader()
        for r in all_control_commits:
            writer.writerow(r)

    # Comprehensive Quantitative Aggregations (§8, §9, §10, §11, §12)
    total_candidates = len(all_candidate_records)
    simulated_cands = [r for r in all_candidate_records if r["simulated"]]
    escalated_cands = [r for r in simulated_cands if r["macro_escalated"]]
    committed_cands = [r for r in all_candidate_records if r["committed"]]

    # 1. Overblocking metrics
    o1_cands = [r for r in all_candidate_records if r["is_o1"]]
    o2_cands = [r for r in all_candidate_records if r["is_o2"]]
    o3_cands = [r for r in all_candidate_records if r["is_o3"]]
    o4_cands = [r for r in all_candidate_records if r["is_o4"]]

    # 2. Precision & Recall of Macro Probing (§10)
    # True Macro Divergence: candidate caused simulated policy divergence (first_div_turn >= 0)
    true_div_cands = [r for r in escalated_cands if r["first_div_turn"] >= 0]
    precision = (len(true_div_cands) / len(escalated_cands)) if escalated_cands else 0.0

    # 3. Macro Divergence Taxonomy (§11)
    regime_tax: Dict[str, Dict[str, Any]] = {}
    for r in escalated_cands:
        reg = r["macro_regime"]
        if reg not in regime_tax:
            regime_tax[reg] = {
                "count": 0,
                "local_deltas": [],
                "macro_effects": [],
                "final_deltas": [],
                "rejected_count": 0,
                "committed_count": 0,
                "divergence_turns": [],
                "horizons": [],
            }
        t_entry = regime_tax[reg]
        t_entry["count"] += 1
        t_entry["local_deltas"].append(r["local_delta"])
        t_entry["macro_effects"].append(r["macro_effect"])
        t_entry["final_deltas"].append(r["final_delta"])
        if r["committed"]:
            t_entry["committed_count"] += 1
        else:
            t_entry["rejected_count"] += 1
        if r["first_div_turn"] >= 0:
            t_entry["divergence_turns"].append(r["first_div_turn"] - r["step"])
        t_entry["horizons"].append(r["horizon"])

    taxonomy_summary = {}
    for reg, d in regime_tax.items():
        taxonomy_summary[reg] = {
            "count": d["count"],
            "pct": round(d["count"] / len(escalated_cands) * 100.0, 1),
            "mean_local_delta": float(np.mean(d["local_deltas"])) if d["local_deltas"] else 0.0,
            "mean_macro_effect": float(np.mean(d["macro_effects"])) if d["macro_effects"] else 0.0,
            "mean_final_delta": float(np.mean(d["final_deltas"])) if d["final_deltas"] else 0.0,
            "commit_rate": round(d["committed_count"] / d["count"], 3) if d["count"] else 0.0,
            "reject_rate": round(d["rejected_count"] / d["count"], 3) if d["count"] else 0.0,
            "mean_divergence_turn_offset": float(np.mean(d["divergence_turns"])) if d["divergence_turns"] else 0.0,
            "mean_horizon": float(np.mean(d["horizons"])) if d["horizons"] else 0.0,
        }

    # 4. Mechanism-Level Decomposition (§13)
    mechs: Dict[str, Dict[str, Any]] = {}
    for r in all_candidate_records:
        m = r["mechanism"]
        if m not in mechs:
            mechs[m] = {
                "candidates": 0,
                "commits": 0,
                "rejections": 0,
                "escalations": 0,
                "final_deltas": [],
                "local_deltas": [],
                "macro_effects": [],
            }
        mechs[m]["candidates"] += 1
        if r["committed"]:
            mechs[m]["commits"] += 1
        else:
            mechs[m]["rejections"] += 1
        if r["macro_escalated"]:
            mechs[m]["escalations"] += 1
        mechs[m]["final_deltas"].append(r["final_delta"])
        mechs[m]["local_deltas"].append(r["local_delta"])
        mechs[m]["macro_effects"].append(r["macro_effect"])

    mech_summary = {}
    for m, d in mechs.items():
        mech_summary[m] = {
            "candidates": d["candidates"],
            "commits": d["commits"],
            "rejections": d["rejections"],
            "escalations": d["escalations"],
            "mean_local_delta": float(np.mean(d["local_deltas"])),
            "mean_macro_effect": float(np.mean(d["macro_effects"])),
            "mean_final_delta": float(np.mean(d["final_deltas"])),
            "min_final_delta": float(np.min(d["final_deltas"])),
            "max_final_delta": float(np.max(d["final_deltas"])),
        }

    # 5. Candidate Outcome Matrix (§12)
    # (Local CF +/-) x (Macro Escalated Y/N) x (Long-Horizon Result +/-) -> Decision
    matrix_bins = defaultdict(int)
    for r in simulated_cands:
        local_sign = "+" if r["local_delta"] > 0 else "-"
        esc_str = "Yes" if r["macro_escalated"] else "No"
        long_sign = "+" if r["final_delta"] > 0 else "-"
        dec_str = "Commit" if r["committed"] else "Reject"
        matrix_bins[(local_sign, esc_str, long_sign, dec_str)] += 1

    outcome_matrix = [
        {"local_cf": k[0], "macro_escalated": k[1], "long_horizon": k[2], "decision": k[3], "count": v}
        for k, v in sorted(matrix_bins.items())
    ]

    # 6. Survival Funnel (§22)
    # Stages: Proposed -> Feasible -> Local Positive -> Macro-Safe -> Safety Pass -> Committed -> Positive Final
    stage_proposed = len(all_candidate_records)
    stage_simulated = len(simulated_cands)
    stage_local_pos = sum(1 for r in simulated_cands if r["local_delta"] > 0)
    stage_macro_safe = sum(1 for r in simulated_cands if (not r["macro_escalated"] or r["macro_effect"] >= 0))
    stage_safety_pass = sum(1 for r in simulated_cands if r["safety_pass"])
    stage_committed = len(committed_cands)
    stage_terminal_pos = sum(1 for r in committed_cands if r["final_delta"] > 0)

    funnel = {
        "1_proposed": stage_proposed,
        "2_simulated": stage_simulated,
        "3_locally_positive": stage_local_pos,
        "4_macro_safe": stage_macro_safe,
        "5_safety_passed": stage_safety_pass,
        "6_committed": stage_committed,
        "7_positive_terminal": stage_terminal_pos,
    }

    summary_data = {
        "v3_sha256": V3_EXPECTED_SHA,
        "v3_sha_verified": True,
        "seeds": PILOT_SEEDS,
        "total_matches": len(PILOT_SEEDS) * 2,
        "total_candidates": total_candidates,
        "simulated_candidates": len(simulated_cands),
        "escalated_candidates": len(escalated_cands),
        "committed_candidates": len(committed_cands),
        "overblocking": {
            "o1_escalated_and_favorable": len(o1_cands),
            "o2_escalated_rejected_but_positive": len(o2_cands),
            "o3_rejected_solely_on_macro_boundary": len(o3_cands),
            "o4_locally_positive_rejected_by_continuation": len(o4_cands),
        },
        "macro_probe_precision": {
            "escalated_count": len(escalated_cands),
            "true_divergence_count": len(true_div_cands),
            "precision": round(precision, 4),
        },
        "taxonomy": taxonomy_summary,
        "mechanisms": mech_summary,
        "outcome_matrix": outcome_matrix,
        "funnel": funnel,
        "seed_summaries": seed_summaries,
        "total_control_commits": len(all_control_commits),
    }

    with open(SUMMARY_JSON, "w") as f:
        json.dump(summary_data, f, indent=2)

    print("\n================================================================")
    print("ATTRIBUTION AUDIT COMPLETE")
    print(f"Total Candidates Screened: {total_candidates}")
    print(f"Simulations Executed: {len(simulated_cands)}")
    print(f"Macro Escalations: {len(escalated_cands)} ({len(escalated_cands)/len(simulated_cands):.1%})")
    print(f"True Divergence Precision: {precision:.1%}")
    print(f"Overblocking: O1={len(o1_cands)}, O2={len(o2_cands)}, O3={len(o3_cands)}, O4={len(o4_cands)}")
    print(f"Control Commits: {len(all_control_commits)}")
    print(f"Ledger written to: {LEDGER_CSV}")
    print(f"Summary written to: {SUMMARY_JSON}")
    print("================================================================")

    return summary_data


if __name__ == "__main__":
    execute_attribution_audit()
