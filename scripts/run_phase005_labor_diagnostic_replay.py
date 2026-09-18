# SPDX-License-Identifier: MIT
"""AEC Phase 005: Generic Labor Opportunity-Cost Diagnostic Replay Runner (§29).

Executes development-only passive diagnostic evaluation on development cohort (seeds 50000-50024).
Answers:
    "For previously observed labor-dependent opportunities, what would the generic
     labor engine have estimated as the worker opportunity cost?"

Strict Governance:
- Zero prospective matches (340300-340349 untouched).
- Zero holdout touches (340050-340199 and 214200-214249 untouched).
- Byte-identical frozen V3 chassis verification.
- Passive/diagnostic evaluation: RESOURCE_CONVERSION remains quarantined.
"""

from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import json
import os
import sys
import time
from typing import Any, Dict, List, Optional, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(HERE, ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

import kagsim
from aec.config import BOARD_SIZE, FINAL_STEP, TURNS_PER_DAY
from aec.coordination.worker_model import extract_farm_workers
from aec.ir.economic_state import build_economic_state
from aec.resource.labor_engine import (
    LaborOpportunityAssessment,
    LaborOpportunityCostEngine,
    LaborOpportunityRequest,
    ValuationLevel,
)

V3_TARBALL_PATH = os.path.join(REPO_ROOT, "submission_Vj_kc_v3.tar.gz")
V3_EXPECTED_SHA256 = "845e0d10981b11b06d272048ff5cee30d70a0403dd757651a556a78c8bf18943"
RESULTS_DIR = os.path.join(REPO_ROOT, "results")
os.makedirs(RESULTS_DIR, exist_ok=True)


def sha256_of_file(filepath: str) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def assert_governance_invariants(seed: int) -> None:
    if 340050 <= seed <= 340199:
        raise RuntimeError(f"FATAL GOVERNANCE BREACH: Attempted access to protected holdout seed {seed}!")
    if 214200 <= seed <= 214249:
        raise RuntimeError(f"FATAL GOVERNANCE BREACH: Attempted access to Gate 0.3 holdout seed {seed}!")
    if 340300 <= seed <= 340349:
        raise RuntimeError(f"FATAL GOVERNANCE BREACH: Attempted access to EXP-AEC-004 prospective cohort seed {seed}!")
    actual_sha = sha256_of_file(V3_TARBALL_PATH)
    if actual_sha != V3_EXPECTED_SHA256:
        raise RuntimeError(f"FATAL CHASSIS BREACH: V3 sha {actual_sha} != expected {V3_EXPECTED_SHA256}")


def run_diagnostic_replay(seeds: List[int]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    engine = LaborOpportunityCostEngine()
    records: List[Dict[str, Any]] = []

    # Check for existing Phase 004B patches to evaluate historical opportunities
    patches_csv = os.path.join(RESULTS_DIR, "PHASE004B_PATCHES.csv")
    historical_patches: List[Dict[str, Any]] = []
    if os.path.exists(patches_csv):
        with open(patches_csv, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if int(row["seed"]) in seeds:
                    historical_patches.append(row)

    print(f"Loaded {len(historical_patches)} historical patch records from development cohort.")

    # Group patches by seed and step
    patches_by_seed_step: Dict[Tuple[int, int], List[Dict[str, Any]]] = {}
    for p in historical_patches:
        s = int(p["seed"])
        st = int(p["step"])
        patches_by_seed_step.setdefault((s, st), []).append(p)

    total_evaluated = 0
    total_rejected_high_oc = 0
    total_approved = 0
    latencies: List[float] = []

    for seed in seeds:
        assert_governance_invariants(seed)
        print(f"Processing development seed {seed}...")

        # Run a simulated replay to get exact state at steps where patches occurred
        game = kagsim.Game(seed)

        # Extract agent from frozen V3 tarball
        import tarfile
        with tarfile.open(V3_TARBALL_PATH, "r:gz") as tar:
            member = tar.extractfile("main.py")
            if member is None:
                raise RuntimeError("Failed to extract main.py from V3 tarball")
            v3_code = member.read().decode("utf-8")
        ns: Dict[str, Any] = {"__name__": f"frozen_v3_{seed}"}
        exec(compile(v3_code, "frozen_v3_main.py", "exec"), ns)
        v3_agent = ns["agent"]

        while not game.done:
            step = game.step_count
            obs0 = game.observe(0)
            obs1 = game.observe(1)
            act0 = v3_agent(obs0)
            act1 = v3_agent(obs1)

            # Check if this step had candidate labor opportunities in historical records
            key = (seed, step)
            if key in patches_by_seed_step:
                econ = build_economic_state(obs0)
                workers_dict = extract_farm_workers(econ, current_turn=step)

                for patch_row in patches_by_seed_step[key]:
                    # Target worker
                    assigned_workers_str = patch_row.get("assigned_workers", "[1]")
                    wid = 1 if "1" in assigned_workers_str else 0

                    if wid in workers_dict and workers_dict[wid].is_active:
                        mech_name = patch_row.get("mechanism_name", "UNKNOWN")
                        cand_cmd = "FEED" if "CONVERSION" in mech_name else "HARVEST"

                        req = LaborOpportunityRequest(
                            worker_id=wid,
                            candidate_action_cmd=cand_cmd,
                            econ_state=econ,
                            baseline_action=act0,
                            baseline_continuation=[copy.deepcopy(act0) for _ in range(6)],
                            current_step=step
                        )

                        t0 = time.perf_counter()
                        assessment = engine.assess_opportunity(req)
                        t1 = time.perf_counter()
                        latencies.append((t1 - t0) * 1000.0)

                        rec = {
                            "seed": seed,
                            "step": step,
                            "candidate_id": patch_row.get("opportunity_id", f"CAND_{seed}_{step}"),
                            "mechanism_name": mech_name,
                            "worker_id": wid,
                            "baseline_task": assessment.tasks_displaced[0] if assessment.tasks_displaced else "PASS",
                            "candidate_task": cand_cmd,
                            "opportunity_cost": assessment.opportunity_cost,
                            "candidate_value": assessment.candidate_incremental_value,
                            "net_value": assessment.net_incremental_value,
                            "commit_recommendation": assessment.commit_recommendation,
                            "abstention_reason": assessment.abstention_reason or "NONE",
                            "valuation_level": int(assessment.valuation_level),
                            "safe_to_use": assessment.safe_to_use,
                        }
                        records.append(rec)
                        total_evaluated += 1

                        if not assessment.commit_recommendation:
                            total_rejected_high_oc += 1
                        else:
                            total_approved += 1

            # Step environment
            game.step(act0, act1)

    # Latency statistics
    latencies_sorted = sorted(latencies) if latencies else [0.0]
    p50_lat = latencies_sorted[len(latencies_sorted) // 2]
    p95_lat = latencies_sorted[int(len(latencies_sorted) * 0.95)]
    worst_lat = max(latencies_sorted)

    summary = {
        "cohort": {"start": seeds[0], "end": seeds[-1], "count": len(seeds)},
        "total_opportunities_evaluated": total_evaluated,
        "total_rejected_due_to_opportunity_cost": total_rejected_high_oc,
        "total_approved": total_approved,
        "rejection_rate": (total_rejected_high_oc / total_evaluated) if total_evaluated > 0 else 0.0,
        "latency_ms": {
            "p50": round(p50_lat, 2),
            "p95": round(p95_lat, 2),
            "worst": round(worst_lat, 2)
        },
        "v3_sha256": sha256_of_file(V3_TARBALL_PATH),
        "holdout_protection": "VERIFIED_UNTOUCHED",
        "prospective_cohort": "VERIFIED_UNTOUCHED"
    }

    return records, summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Phase 005 Labor Opportunity Diagnostic Replay")
    parser.add_argument("--count", type=int, default=5, help="Number of development seeds to replay (1-25)")
    args = parser.parse_args()

    count = max(1, min(25, args.count))
    seeds = [50000 + i for i in range(count)]
    print(f"Starting Phase 005 Labor Diagnostic Replay across {count} seeds: {seeds[0]}..{seeds[-1]}")

    records, summary = run_diagnostic_replay(seeds)

    # Write CSV
    out_csv = os.path.join(RESULTS_DIR, "PHASE005_LABOR_DIAGNOSTIC.csv")
    if records:
        with open(out_csv, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(records[0].keys()))
            writer.writeheader()
            writer.writerows(records)
        print(f"Wrote {len(records)} evaluation records to {out_csv}")

    # Write JSON Summary
    out_json = os.path.join(RESULTS_DIR, "PHASE005_LABOR_DIAGNOSTIC_SUMMARY.json")
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print(f"Wrote summary to {out_json}")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
