#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Phase 020: Prospective Headroom Reorientation & Opportunity Census Script (§9, §14-§18).

Executes CRN mirror matches across fresh cohort 249356..249365 (10 seeds, 20 matches).
At each turn, generates bounded diagnostic transformations across orthogonal families,
runs Stage 1 local probe and Stage 2 Phase 016 exact macro-aware counterfactual simulation,
and records complete telemetry into results/PHASE020_CENSUS_LEDGER.csv.
"""

from __future__ import annotations

import copy
import csv
import hashlib
import json
import os
import sys
import time
from collections import Counter, defaultdict
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
from aec.config import build_robust_qualified_config
from aec.integration.executor import AECExecutor
from aec.opportunities.diagnostic_transformations import (
    DiagnosticEvaluator,
    DiagnosticTransformationGenerator,
    OpportunityFamily,
    TransformationPrimitive,
)

V3_TARBALL_PATH = os.path.join(REPO_ROOT, "submission_Vj_kc_v3.tar.gz")
V3_EXPECTED_SHA = "845e0d10981b11b06d272048ff5cee30d70a0403dd757651a556a78c8bf18943"
RESULTS_DIR = os.path.join(REPO_ROOT, "results")

DISCOVERY_SEEDS = list(range(249356, 249366))


def verify_v3_sha() -> None:
    with open(V3_TARBALL_PATH, "rb") as f:
        actual = hashlib.sha256(f.read()).hexdigest()
    if actual != V3_EXPECTED_SHA:
        raise RuntimeError(f"V3 SHA MISMATCH: {actual}")


def run_census_match(seed: int, seat: int, sample_interval: int = 2) -> Dict[str, Any]:
    """Execute one CRN mirror match with fine-grained prospective opportunity census."""
    game = kagsim.Game(seed)
    
    agent_cfg = build_robust_qualified_config()
    opp_cfg = build_robust_qualified_config()
    
    player_agent = AECExecutor(config=agent_cfg)
    opp_agent = AECExecutor(config=opp_cfg)
    
    gen = DiagnosticTransformationGenerator()
    evaluator = DiagnosticEvaluator()
    
    records: List[Dict[str, Any]] = []
    step_count = 0
    t0 = time.time()
    
    while not game.done:
        o0, o1 = game.observe(0), game.observe(1)
        if seat == 0:
            a0 = player_agent.act(o0)
            a1 = opp_agent.act(o1)
        else:
            a0 = opp_agent.act(o0)
            a1 = player_agent.act(o1)
        
        current_action = a0 if seat == 0 else a1
        econ_state = getattr(player_agent, "_prev_econ_state", None)
        
        # Diagnostic census probe on sampled steps
        if econ_state is not None and (step_count % sample_interval == 0 or step_count >= 672):
            continuation = getattr(player_agent, "_in_flight_patch", None)
            cont_actions = continuation.actions[1:] if continuation and len(continuation.actions) > 1 else None
            
            candidates = gen.generate_candidates(
                econ_state=econ_state,
                baseline_action=current_action,
                continuation_trajectory=cont_actions,
            )
            
            for cand in candidates:
                # Stage 1: Cheap local probe
                local_sig = evaluator.evaluate_stage1_local(econ_state, cand, current_action)
                
                # Stage 2: Phase 016 exact long-horizon simulation
                v3_fn = getattr(player_agent.backbone, "_agent_fn", None)
                sim_res = evaluator.evaluate_stage2_long_horizon(
                    econ_state=econ_state,
                    candidate=cand,
                    baseline_action=current_action,
                    continuation_trajectory=cont_actions,
                    v3_agent_callable=v3_fn,
                    horizon=24,
                )
                
                cand_act = cand.patch.apply(current_action)
                
                # Causal source attribution
                causal_source = "TIMING_MISMATCH"
                if cand.family == OpportunityFamily.WORKER_ALLOCATION:
                    causal_source = "LABOR_TRAVEL_INEFFICIENCY"
                elif cand.family == OpportunityFamily.ROUTE_SPATIAL:
                    causal_source = "SPATIAL_DETOUR_CONGESTION"
                elif cand.family == OpportunityFamily.MULTI_WORKER:
                    causal_source = "WORKER_TIMING_DESYNCHRONIZATION"
                elif cand.family == OpportunityFamily.LIQUIDITY_CAPITAL_TIMING:
                    causal_source = "CAPITAL_BOTTLENECK"
                elif cand.family == OpportunityFamily.PRODUCTION_TIMING:
                    causal_source = "PRODUCTION_SYNCHRONIZATION"
                elif cand.family == OpportunityFamily.TERMINAL:
                    causal_source = "TERMINAL_RUNWAY_EXHAUSTION"
                elif cand.is_tranche_related:
                    causal_source = "TRANCHE_INVENTORY_LIQUIDATION"

                records.append({
                    "seed": seed,
                    "seat": seat,
                    "turn": step_count,
                    "candidate_id": cand.candidate_id,
                    "primitive": cand.primitive.value,
                    "family": cand.family.value,
                    "divergence_class": cand.divergence_class.value,
                    "baseline_action": json.dumps(current_action),
                    "candidate_action": json.dumps(cand_act),
                    "local_delta": round(float(cand.estimated_local_signal), 2),
                    "long_horizon_delta": round(float(cand.long_horizon_delta), 2),
                    "direct_intervention_effect": round(float(cand.direct_intervention_effect), 2),
                    "macro_continuation_delta": round(float(cand.macro_induced_continuation_delta), 2),
                    "macro_escalated": cand.macro_escalated,
                    "macro_regime": cand.macro_regime,
                    "divergence_turn": cand.divergence_turn if cand.divergence_turn is not None else -1,
                    "is_safe": cand.is_safe,
                    "survival_category": cand.survival_category,
                    "is_tranche_related": cand.is_tranche_related,
                    "is_representable": cand.is_representable,
                    "likely_causal_source": causal_source,
                    "rationale": cand.rationale,
                })

        game.step(a0, a1)
        step_count += 1

    r0, r1 = float(game.reward(0)), float(game.reward(1))
    margin = (r0 - r1) if seat == 0 else (r1 - r0)
    elapsed = time.time() - t0

    return {
        "seed": seed,
        "seat": seat,
        "margin": margin,
        "elapsed_s": elapsed,
        "records_count": len(records),
        "records": records,
    }


def main() -> None:
    verify_v3_sha()
    os.makedirs(RESULTS_DIR, exist_ok=True)
    
    print("=" * 72)
    print("PHASE 020: PROSPECTIVE OPPORTUNITY CENSUS DISCOVERY TRIAL")
    print(f"Cohort: Seeds {DISCOVERY_SEEDS[0]}..{DISCOVERY_SEEDS[-1]} (10 seeds, 20 mirror matches)")
    print("Evaluator: Phase 016 exact macro-aware continuation")
    print("Chassis: Frozen V3 (Verified)")
    print("=" * 72)

    tasks = [(s, seat) for s in DISCOVERY_SEEDS for seat in (0, 1)]
    all_records: List[Dict[str, Any]] = []
    
    t_start = time.time()
    with ProcessPoolExecutor(max_workers=6) as executor:
        futures = {executor.submit(run_census_match, s, seat): (s, seat) for s, seat in tasks}
        for fut in as_completed(futures):
            s, seat = futures[fut]
            res = fut.result()
            all_records.extend(res["records"])
            print(f"  [CENSUS] seed {s} seat {seat}: {res['records_count']} candidate probes evaluated ({res['elapsed_s']:.1f}s)")

    elapsed_total = time.time() - t_start
    print("=" * 72)
    print(f"CENSUS COMPLETE: {len(all_records)} total candidate evaluations across 20 matches in {elapsed_total:.1f}s")
    print("=" * 72)

    # Write CSV ledger
    csv_path = os.path.join(RESULTS_DIR, "PHASE020_CENSUS_LEDGER.csv")
    if all_records:
        fieldnames = list(all_records[0].keys())
        with open(csv_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_records)
        print(f"Saved census ledger to {csv_path}")

    # Summary statistics
    tranche_count = sum(1 for r in all_records if r["is_tranche_related"])
    non_tranche_count = len(all_records) - tranche_count

    print(f"Tranche-related probes: {tranche_count}")
    print(f"Non-tranche candidate probes: {non_tranche_count}")
    
    # Family breakdown
    family_counts = Counter(r["family"] for r in all_records if not r["is_tranche_related"])
    print("\nNon-Tranche Candidate Breakdown by Family:")
    for fam, cnt in family_counts.most_common():
        sub_recs = [r for r in all_records if r["family"] == fam and not r["is_tranche_related"]]
        mean_lh = np.mean([r["long_horizon_delta"] for r in sub_recs])
        h3_cnt = sum(1 for r in sub_recs if r["survival_category"] in ("H3", "H4", "H5"))
        print(f"  - {fam:25s}: {cnt:4d} probes | Mean LH Delta: ${mean_lh:+7.2f} | H3+ positive: {h3_cnt}")

    # Save summary JSON
    summary_path = os.path.join(RESULTS_DIR, "PHASE020_CENSUS_SUMMARY.json")
    summary_data = {
        "cohort": [DISCOVERY_SEEDS[0], DISCOVERY_SEEDS[-1]],
        "total_probes": len(all_records),
        "tranche_probes": tranche_count,
        "non_tranche_probes": non_tranche_count,
        "elapsed_seconds": elapsed_total,
    }
    with open(summary_path, "w") as f:
        json.dump(summary_data, f, indent=2)
    print(f"Saved census summary to {summary_path}")


if __name__ == "__main__":
    main()
