# SPDX-License-Identifier: MIT
"""AEC Phase 004: Offline Replay Evaluation Runner (§5, §6, §7, §8, §9, §14, §15, §20).

Executes deterministic offline development replays across seeds 50000-50024
(25 seeds x 2 seats x 4 arms = 200 matches).

Evaluates:
- Arm A: CONTROL (frozen baseline)
- Arm B: RESOURCE_CONVERSION_ONLY (+ Multi-Worker Coordination)
- Arm C: EMERGENCY_FEED_ONLY (+ Multi-Worker Coordination)
- Arm D: COMBINED_RESOURCE (+ Multi-Worker Coordination, exploratory)

Measures:
- Labor cannibalization (primary displacement rate, auxiliary absorption rate)
- High-value harvest preservation
- Terminal margin deltas (all-seed ITT and triggered subsets)
- Invariant preservation, zero holdout touches, and counterfactual fidelity.
"""

from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import json
import os
import sys
import tarfile
import time
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(HERE, ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

import kagsim
from aec.config import (
    AECConfig,
    ENABLED_FOUNDATION_MECHANISMS,
    QUARANTINED_MECHANISMS,
    PRODUCTS,
    SHED_CAPACITY,
)
from aec.integration.backbone_adapter import BackboneAdapter
from aec.integration.executor import AECExecutor
from aec.coordination.assignment import DisplacementOutcome

COHORT_START = 50000
DEFAULT_COHORT_SIZE = 25
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


class FrozenV3ControlAgent:
    """Isolated raw frozen V3 control loaded directly from tarball in memory."""
    def __init__(self, tar_path: str = V3_TARBALL_PATH) -> None:
        assert_governance_invariants(50000)
        with tarfile.open(tar_path, "r:gz") as tar:
            member = tar.extractfile("main.py")
            if member is None:
                raise RuntimeError("Failed to extract main.py from V3 tarball")
            v3_code = member.read().decode("utf-8")
        ns: Dict[str, Any] = {"__name__": f"frozen_v3_{time.time_ns()}"}
        exec(compile(v3_code, "frozen_v3_main.py", "exec"), ns)
        self._agent = ns["agent"]

    def act(self, obs: Dict[str, Any], cfg: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return self._agent(obs, cfg)


class Phase004TreatmentAgent:
    """Isolated AEC treatment agent configured for a specific Phase 004 arm."""
    def __init__(self, arm_name: str) -> None:
        self.arm_name = arm_name

        if arm_name == "CONTROL":
            enabled = ENABLED_FOUNDATION_MECHANISMS
            quarantined = QUARANTINED_MECHANISMS
        elif arm_name == "RESOURCE_CONVERSION_ONLY":
            enabled = ENABLED_FOUNDATION_MECHANISMS + ("RESOURCE_CONVERSION",)
            quarantined = tuple(m for m in QUARANTINED_MECHANISMS if m != "RESOURCE_CONVERSION")
        elif arm_name == "EMERGENCY_FEED_ONLY":
            enabled = ENABLED_FOUNDATION_MECHANISMS + ("EMERGENCY_FEED_PURCHASE",)
            quarantined = tuple(m for m in QUARANTINED_MECHANISMS if m != "EMERGENCY_FEED_PURCHASE")
        elif arm_name == "COMBINED_RESOURCE":
            enabled = ENABLED_FOUNDATION_MECHANISMS + ("RESOURCE_CONVERSION", "EMERGENCY_FEED_PURCHASE")
            quarantined = tuple(m for m in QUARANTINED_MECHANISMS if m not in ("RESOURCE_CONVERSION", "EMERGENCY_FEED_PURCHASE"))
        else:
            raise ValueError(f"Unknown arm name: {arm_name}")

        self.config = AECConfig(
            enabled_mechanisms=enabled,
            quarantined_mechanisms=quarantined,
            frozen_mode=True,
            fail_closed=True
        )
        self.adapter = BackboneAdapter(config=self.config)
        self.executor = AECExecutor(backbone_adapter=self.adapter, config=self.config)
        self.step_latencies_ms: List[float] = []

    def act(self, obs: Dict[str, Any], cfg: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        t0 = time.perf_counter()
        action = self.executor.act(obs, cfg)
        self.step_latencies_ms.append((time.perf_counter() - t0) * 1000.0)
        return action


def run_single_match(
    seed: int,
    aec_seat: int,
    arm_name: str
) -> Dict[str, Any]:
    assert_governance_invariants(seed)

    treat_agent = Phase004TreatmentAgent(arm_name=arm_name)
    ctrl_agent = FrozenV3ControlAgent()

    game = kagsim.Game(seed)
    step_telemetries: List[Dict[str, Any]] = []
    committed_patches: List[Dict[str, Any]] = []

    candidate_counts: Dict[str, int] = {}
    commit_counts: Dict[str, int] = {}
    abstain_counts: Dict[str, int] = {}
    safety_pass_count = 0
    safety_fail_count = 0
    simulations_count = 0

    max_shed_units = 0
    shed_overflow_detected = False

    farmer_displaced_count = 0
    auxiliary_absorbed_count = 0
    high_value_harvests_displaced = 0

    while not game.done:
        step = game.step_count
        obs0 = game.observe(0)
        obs1 = game.observe(1)

        aec_obs = obs0 if aec_seat == 0 else obs1
        raw_shed = (aec_obs.get("private", {}) or {}).get("shed", {}) or {}
        shed_qty = sum(int(v or 0) for v in raw_shed.values())
        if shed_qty > max_shed_units:
            max_shed_units = shed_qty
        if shed_qty > 100:
            shed_overflow_detected = True

        if aec_seat == 0:
            act0 = treat_agent.act(obs0)
            act1 = ctrl_agent.act(obs1)
        else:
            act0 = ctrl_agent.act(obs0)
            act1 = treat_agent.act(obs1)

        telem = treat_agent.executor.latest_telemetry
        if telem is not None:
            td = telem.to_dict()
            step_telemetries.append(td)

            for c in td.get("candidates", []):
                fam = c.get("mechanism_family") or "UNKNOWN"
                candidate_counts[fam] = candidate_counts.get(fam, 0) + 1
                if c.get("simulation_run"):
                    simulations_count += 1
                if c.get("safety_pass"):
                    safety_pass_count += 1
                else:
                    safety_fail_count += 1

            if td.get("decision") == "COMMIT":
                mech = td.get("committed_mechanism") or "UNKNOWN"
                commit_counts[mech] = commit_counts.get(mech, 0) + 1

                # Locate committed candidate and patch
                committed_cand = next((c for c in td.get("candidates", []) if c.get("patch_id") == td.get("patch_id")), None)
                committed_patch = treat_agent.executor.latest_committed_patch
                coord_plan = getattr(committed_patch, "coordination_plan", None) if committed_patch else None

                # Inspect worker mutations
                cand_act = committed_cand.get("candidate_action") or {} if committed_cand else {}
                base_act = committed_cand.get("baseline_action") or {} if committed_cand else {}
                farmer_moved = (cand_act.get("farmer") != base_act.get("farmer"))
                hands_moved = (cand_act.get("hands") != base_act.get("hands"))

                assigned_workers: List[int] = []
                tasks_preserved = 0
                tasks_absorbed = 0
                tasks_delayed = 0
                tasks_cancelled = 0
                lost_mandatory = 0
                high_val_disp = 0

                if coord_plan is not None:
                    assigned_workers = [a.worker_id for a in coord_plan.assignments]
                    loc = coord_plan.labor_opportunity_cost
                    tasks_absorbed = len(loc.absorbed_tasks)
                    tasks_delayed = len(loc.delayed_tasks)
                    lost_mandatory = loc.lost_mandatory_count
                    for tid, outcome in loc.displaced_tasks.items():
                        if outcome == DisplacementOutcome.PRESERVED_BY_SELF:
                            tasks_preserved += 1
                        elif outcome in (DisplacementOutcome.CANCELLED, DisplacementOutcome.INFEASIBLE):
                            tasks_cancelled += 1
                            if "HARVEST" in tid:
                                high_val_disp += 1
                else:
                    if farmer_moved:
                        assigned_workers.append(0)
                    if hands_moved:
                        assigned_workers.extend([i + 1 for i in range(len(cand_act.get("hands", [])))])

                is_farmer_disp = (0 in assigned_workers or farmer_moved)
                is_aux_abs = (any(w >= 1 for w in assigned_workers) or hands_moved)

                if is_farmer_disp:
                    farmer_displaced_count += 1
                if is_aux_abs:
                    auxiliary_absorbed_count += 1
                high_value_harvests_displaced += high_val_disp

                # Benefit classification (§16)
                if not is_farmer_disp and not is_aux_abs:
                    benefit_class = "NO_MULTIWORKER_NEEDED"
                elif not is_farmer_disp and is_aux_abs:
                    benefit_class = "MULTIWORKER_FEASIBLE"
                elif is_farmer_disp and is_aux_abs:
                    benefit_class = "MULTIWORKER_REQUIRED"
                else:
                    benefit_class = "NO_MULTIWORKER_NEEDED"

                record = {
                    "seed": seed,
                    "seat": aec_seat,
                    "step": step,
                    "arm": arm_name,
                    "mechanism_name": mech,
                    "opportunity_id": td.get("patch_id"),
                    "patch_type": getattr(committed_patch, "patch_type", mech) if committed_patch else mech,
                    "assigned_workers": str(assigned_workers),
                    "farmer_displaced": is_farmer_disp,
                    "auxiliary_absorbed": is_aux_abs,
                    "benefit_classification": benefit_class,
                    "baseline_tasks_preserved": tasks_preserved,
                    "baseline_tasks_absorbed": tasks_absorbed,
                    "baseline_tasks_delayed": tasks_delayed,
                    "baseline_tasks_cancelled": tasks_cancelled,
                    "high_value_harvests_displaced": high_val_disp,
                    "lost_mandatory_count": lost_mandatory,
                    "simulation_result": "SUCCESS",
                    "safety_result": "PASS",
                    "commit_decision": "COMMIT",
                    "predicted_delta_money": committed_cand.get("delta_money") if committed_cand else 0.0,
                    "predicted_delta_margin": committed_cand.get("delta_margin") if committed_cand else 0.0,
                    "realized_delta_money": committed_cand.get("delta_money_realized") if committed_cand else 0.0,
                    "realized_delta_margin": committed_cand.get("delta_margin_realized") if committed_cand else 0.0,
                }
                committed_patches.append(record)
            else:
                reason = td.get("abstain_reason") or "UNKNOWN_ABSTAIN"
                abstain_counts[reason] = abstain_counts.get(reason, 0) + 1

        game.step(act0, act1)

    r0 = game.reward(0)
    r1 = game.reward(1)
    treat_reward = r0 if aec_seat == 0 else r1
    ctrl_reward = r1 if aec_seat == 0 else r0
    margin = treat_reward - ctrl_reward

    return {
        "seed": seed,
        "seat": aec_seat,
        "arm": arm_name,
        "treatment_reward": treat_reward,
        "control_reward": ctrl_reward,
        "terminal_margin": margin,
        "total_steps": game.step_count,
        "max_shed_units": max_shed_units,
        "shed_overflow_detected": shed_overflow_detected,
        "candidate_counts": candidate_counts,
        "commit_counts": commit_counts,
        "abstain_counts": abstain_counts,
        "safety_pass_count": safety_pass_count,
        "safety_fail_count": safety_fail_count,
        "simulations_count": simulations_count,
        "farmer_displaced_count": farmer_displaced_count,
        "auxiliary_absorbed_count": auxiliary_absorbed_count,
        "high_value_harvests_displaced": high_value_harvests_displaced,
        "committed_patches": committed_patches,
        "mean_latency_ms": float(np.mean(treat_agent.step_latencies_ms)) if treat_agent.step_latencies_ms else 0.0,
        "median_latency_ms": float(np.median(treat_agent.step_latencies_ms)) if treat_agent.step_latencies_ms else 0.0,
        "p95_latency_ms": float(np.percentile(treat_agent.step_latencies_ms, 95)) if treat_agent.step_latencies_ms else 0.0,
    }


def run_phase004_cohort(seeds: List[int], arms: List[str]) -> Dict[str, Any]:
    print(f"\n================================================================================")
    print(f"STARTING AEC PHASE 004 DETERMINISTIC OFFLINE REPLAY EVALUATION BATCH")
    print(f"Seeds: {len(seeds)} ({seeds[0]}..{seeds[-1]}), Seats: 2, Arms: {len(arms)}")
    print(f"Total Matches: {len(seeds) * 2 * len(arms)}")
    print(f"================================================================================\n")

    arm_summaries: Dict[str, Any] = {}
    all_committed_patches: List[Dict[str, Any]] = []
    all_match_records: List[Dict[str, Any]] = []

    for arm in arms:
        print(f"--- Executing Arm: {arm} ({len(seeds)*2} matches) ---", flush=True)
        t_arm0 = time.perf_counter()
        arm_matches: List[Dict[str, Any]] = []

        for s_idx, seed in enumerate(seeds):
            for seat in (0, 1):
                m_res = run_single_match(seed=seed, aec_seat=seat, arm_name=arm)
                arm_matches.append(m_res)
                all_match_records.append({
                    "arm": arm,
                    "seed": seed,
                    "seat": seat,
                    "treatment_reward": m_res["treatment_reward"],
                    "control_reward": m_res["control_reward"],
                    "margin": m_res["terminal_margin"],
                    "commits": len(m_res["committed_patches"]),
                    "farmer_displaced": m_res["farmer_displaced_count"],
                    "auxiliary_absorbed": m_res["auxiliary_absorbed_count"],
                    "overflow": m_res["shed_overflow_detected"],
                    "mean_latency_ms": round(m_res["mean_latency_ms"], 3),
                })
                all_committed_patches.extend(m_res["committed_patches"])

            if (s_idx + 1) % 5 == 0 or (s_idx + 1) == len(seeds):
                print(f"  Processed {s_idx + 1}/{len(seeds)} seeds...", flush=True)

        arm_time = time.perf_counter() - t_arm0
        margins = [m["terminal_margin"] for m in arm_matches]
        commits = sum(len(m["committed_patches"]) for m in arm_matches)
        seeds_with_commits = len(set(p["seed"] for p in all_committed_patches if p["arm"] == arm))

        farmer_disp = sum(m["farmer_displaced_count"] for m in arm_matches)
        aux_abs = sum(m["auxiliary_absorbed_count"] for m in arm_matches)

        arm_summaries[arm] = {
            "total_matches": len(arm_matches),
            "mean_margin": float(np.mean(margins)),
            "median_margin": float(np.median(margins)),
            "std_margin": float(np.std(margins)),
            "p05_margin": float(np.percentile(margins, 5)),
            "p95_margin": float(np.percentile(margins, 95)),
            "total_commits": commits,
            "seeds_with_commits": seeds_with_commits,
            "farmer_displaced_total": farmer_disp,
            "auxiliary_absorbed_total": aux_abs,
            "shed_overflow_any": any(m["shed_overflow_detected"] for m in arm_matches),
            "arm_elapsed_sec": round(arm_time, 2),
        }
        print(f"  Done {arm}: Mean Margin=${arm_summaries[arm]['mean_margin']:.2f}, Commits={commits} across {seeds_with_commits} seeds ({arm_time:.1f}s)\n")

    # Compute Paired Deltas relative to Arm A (CONTROL)
    paired_deltas: Dict[str, Any] = {}
    control_margins = {
        (m["seed"], m["seat"]): m["margin"]
        for m in all_match_records if m["arm"] == "CONTROL"
    }

    for arm in arms:
        if arm == "CONTROL":
            continue
        deltas = []
        triggered_deltas = []
        for m in all_match_records:
            if m["arm"] == arm:
                ctrl_m = control_margins.get((m["seed"], m["seat"]), 0.0)
                delta = m["margin"] - ctrl_m
                deltas.append(delta)
                if m["commits"] > 0:
                    triggered_deltas.append(delta)

        paired_deltas[arm] = {
            "itt_mean_delta": float(np.mean(deltas)) if deltas else 0.0,
            "itt_median_delta": float(np.median(deltas)) if deltas else 0.0,
            "itt_std": float(np.std(deltas)) if deltas else 0.0,
            "triggered_count": len(triggered_deltas),
            "triggered_mean_delta": float(np.mean(triggered_deltas)) if triggered_deltas else 0.0,
        }

    # Save CSV outputs
    matches_csv = os.path.join(RESULTS_DIR, "PHASE004_MATCHES.csv")
    with open(matches_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "arm", "seed", "seat", "treatment_reward", "control_reward",
            "margin", "commits", "farmer_displaced", "auxiliary_absorbed",
            "overflow", "mean_latency_ms"
        ])
        writer.writeheader()
        writer.writerows(all_match_records)

    patches_csv = os.path.join(RESULTS_DIR, "PHASE004_PATCHES.csv")
    with open(patches_csv, "w", newline="", encoding="utf-8") as f:
        if all_committed_patches:
            writer = csv.DictWriter(f, fieldnames=list(all_committed_patches[0].keys()))
            writer.writeheader()
            writer.writerows(all_committed_patches)

    summary_json = os.path.join(RESULTS_DIR, "PHASE004_SUMMARY.json")
    full_summary = {
        "cohort": {"start": seeds[0], "end": seeds[-1], "count": len(seeds)},
        "arms": arm_summaries,
        "paired_deltas": paired_deltas,
        "v3_sha256": V3_EXPECTED_SHA256,
        "holdout_protection": "VERIFIED_UNTOUCHED",
    }
    with open(summary_json, "w", encoding="utf-8") as f:
        json.dump(full_summary, f, indent=2)

    print("================================================================================")
    print("PHASE 004 EVALUATION COMPLETE")
    print(f"Summary saved to: {summary_json}")
    print(f"Matches saved to: {matches_csv}")
    print(f"Patches saved to: {patches_csv}")
    print("================================================================================\n")
    return full_summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AEC Phase 004 Replay Runner")
    parser.add_argument("--smoke-only", action="store_true", help="Run 1 seed smoke test")
    args = parser.parse_args()

    assert_governance_invariants(50000)

    if args.smoke_only:
        seeds = [50000]
        arms = ["CONTROL", "RESOURCE_CONVERSION_ONLY"]
    else:
        seeds = list(range(COHORT_START, COHORT_START + DEFAULT_COHORT_SIZE))
        arms = ["CONTROL", "RESOURCE_CONVERSION_ONLY", "EMERGENCY_FEED_ONLY", "COMBINED_RESOURCE"]

    run_phase004_cohort(seeds, arms)
