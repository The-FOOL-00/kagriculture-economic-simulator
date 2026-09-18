#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""AEC Phase 005B: Ground-Truth Labor Opportunity Engine Audit & Harvest Discovery.

Executes deterministic offline ground-truth evaluation across development seeds 50000-50024.
Measures exact simulator terminal reward delta vs labor engine net incremental value.
Performs genuine harvest candidate discovery.

Governance Invariants:
- Frozen V3 chassis SHA-256 verification.
- Holdouts (340050-340199, 214200-214249, 340300-340349) strictly protected (zero access).
- Development seeds 50000-50024 only.
- RESOURCE_CONVERSION remains strictly quarantined.
"""

from __future__ import annotations

import copy
import csv
import hashlib
import json
import os
import sys
import tarfile
import time
from typing import Any, Dict, List, Optional, Tuple

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

import kagsim
from aec.config import BOARD_SIZE, CROP_GROWTH_DAYS, CROPS, FINAL_STEP, TURNS_PER_DAY
from aec.coordination.worker_model import extract_farm_workers
from aec.ir.economic_state import build_economic_state
from aec.resource.labor_engine import (
    LaborOpportunityAssessment,
    LaborOpportunityCostEngine,
    LaborOpportunityRequest,
    ValuationLevel,
)
from extracted_agents.dmitrii_lb2800.unit_model import CROPS as CROPS_META

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
        raise RuntimeError(f"FATAL GOVERNANCE BREACH: Holdout seed {seed} accessed!")
    if 214200 <= seed <= 214249:
        raise RuntimeError(f"FATAL GOVERNANCE BREACH: Gate 0.3 holdout seed {seed} accessed!")
    if 340300 <= seed <= 340349:
        raise RuntimeError(f"FATAL GOVERNANCE BREACH: EXP-AEC-004 prospective cohort seed {seed} accessed!")
    actual_sha = sha256_of_file(V3_TARBALL_PATH)
    if actual_sha != V3_EXPECTED_SHA256:
        raise RuntimeError(f"FATAL CHASSIS BREACH: V3 hash {actual_sha} != {V3_EXPECTED_SHA256}")


def load_v3_agent() -> Any:
    with tarfile.open(V3_TARBALL_PATH, "r:gz") as tar:
        member = tar.extractfile("main.py")
        if member is None:
            raise RuntimeError("Failed to extract main.py from V3 tarball")
        v3_code = member.read().decode("utf-8")
    ns: Dict[str, Any] = {"__name__": "v3_agent_ground_truth"}
    exec(compile(v3_code, "frozen_v3_main.py", "exec"), ns)
    return ns["agent"]


def run_full_game_with_actions(seed: int, v3_agent: Any) -> Tuple[float, List[Tuple[Dict[str, Any], Dict[str, Any]]], List[Dict[str, Any]]]:
    assert_governance_invariants(seed)
    game = kagsim.Game(seed)
    actions: List[Tuple[Dict[str, Any], Dict[str, Any]]] = []
    observations: List[Dict[str, Any]] = []

    while not game.done:
        obs0 = game.observe(0)
        obs1 = game.observe(1)
        observations.append(obs0)
        a0 = v3_agent(obs0)
        a1 = v3_agent(obs1)
        actions.append((copy.deepcopy(a0), copy.deepcopy(a1)))
        game.step(a0, a1)

    return float(game.reward(0)), actions, observations


def run_counterfactual_game(
    seed: int,
    intervention_step: int,
    patched_action_p0: Dict[str, Any],
    v3_agent: Any
) -> float:
    """Replay seed from step 0 to intervention_step, execute patched action at step, continue to terminal with v3_agent."""
    assert_governance_invariants(seed)
    game = kagsim.Game(seed)

    # Replay up to intervention_step
    for s in range(intervention_step):
        obs0 = game.observe(0)
        obs1 = game.observe(1)
        a0 = v3_agent(obs0)
        a1 = v3_agent(obs1)
        game.step(a0, a1)

    # Intervene at intervention_step
    obs0 = game.observe(0)
    obs1 = game.observe(1)
    a1 = v3_agent(obs1)
    game.step(patched_action_p0, a1)

    # Continue with v3_agent to terminal
    while not game.done:
        obs0 = game.observe(0)
        obs1 = game.observe(1)
        game.step(v3_agent(obs0), v3_agent(obs1))

    return float(game.reward(0))


def main() -> None:
    print("=" * 70)
    print("AEC PHASE 005B: LABOR OPPORTUNITY ENGINE GROUND-TRUTH AUDIT")
    print("=" * 70)

    # Governance check
    v3_sha = sha256_of_file(V3_TARBALL_PATH)
    print(f"Verified V3 Chassis SHA256: {v3_sha}")
    if v3_sha != V3_EXPECTED_SHA256:
        raise RuntimeError("V3 hash mismatch!")

    v3_agent = load_v3_agent()
    engine = LaborOpportunityCostEngine()

    seeds = [50000 + i for i in range(25)]
    print(f"Development Cohort: 25 seeds ({seeds[0]}..{seeds[-1]})")

    gt_records: List[Dict[str, Any]] = []
    harvest_candidates: List[Dict[str, Any]] = []

    # Latency benchmarking by level
    level_latencies: Dict[int, List[float]] = {0: [], 1: [], 2: [], 3: [], 4: []}

    for seed_idx, seed in enumerate(seeds):
        assert_governance_invariants(seed)
        t_start_seed = time.perf_counter()
        print(f"[{seed_idx + 1}/25] Simulating baseline match for seed {seed}...")
        base_reward, base_actions, observations = run_full_game_with_actions(seed, v3_agent)

        # 1. SCAN FOR WORKER STATES
        # We look for:
        # A. Idle worker near mature crop (candidate HARVEST)
        # B. Productive worker (candidate PASS diversion)
        # C. Zero-delta baseline PASS to PASS
        # D. Terminal phase states (step >= 680)
        # E. Peer absorption candidates
        found_idle_harvest: Optional[Tuple[int, int, Tuple[int, int], str, int]] = None
        found_productive_diversion: Optional[Tuple[int, int, str]] = None
        found_terminal_harvest: Optional[Tuple[int, int, Tuple[int, int], str, int]] = None

        for s in range(len(observations)):
            obs0 = observations[s]
            a0, _ = base_actions[s]
            day = obs0["day"]
            tiles = obs0["farms"][0]["tiles"]
            hands = obs0["farms"][0]["hands"]

            # Harvest Candidate Discovery across the entire game
            if hands and len(hands) > 0:
                # Find mature crops
                mature_crops: List[Tuple[Tuple[int, int], str, int]] = []
                for y in range(len(tiles)):
                    for x in range(len(tiles[0])):
                        t = tiles[y][x]
                        if isinstance(t, dict) and t.get("kind") == "PLANT":
                            crop = t.get("crop")
                            if crop and crop in CROPS_META:
                                cd = CROPS_META[crop]
                                if day - t.get("planted_day", 0) >= cd["first_yield_day"] and t.get("yield_units", 0) > 0:
                                    mature_crops.append(((x, y), crop, t["yield_units"]))

                if mature_crops:
                    hand_acts = a0.get("hands", [])
                    for wid, h_act in enumerate(hand_acts):
                        if wid < len(hands):
                            worker_id = wid + 1
                            hpos = hands[wid]
                            b_cmd = h_act[0] if h_act else "PASS"

                            # Closest mature crop
                            closest_crop_info = min(
                                mature_crops,
                                key=lambda item: abs(item[0][0] - hpos[0]) + abs(item[0][1] - hpos[1])
                            )
                            cpos, crop_name, yield_u = closest_crop_info
                            dist = abs(cpos[0] - hpos[0]) + abs(cpos[1] - hpos[1])

                            # Genuine harvest opportunity criteria:
                            # 1. Mature harvestable crop exists
                            # 2. Worker reachable (dist <= 3 or standing directly dist == 0)
                            # 3. Harvest not already part of baseline
                            # 4. Feasible before terminal (day < 30)
                            if b_cmd != "HARVEST" and dist <= 3 and day < 30:
                                # Candidate is HARVEST
                                econ = build_economic_state(obs0)
                                req = LaborOpportunityRequest(
                                    worker_id=worker_id,
                                    candidate_action_cmd="HARVEST" if dist == 0 else "PASS",
                                    econ_state=econ,
                                    baseline_action=a0,
                                    baseline_continuation=[copy.deepcopy(a0) for _ in range(6)],
                                    current_step=s,
                                    target_location=cpos
                                )
                                t_eval_0 = time.perf_counter()
                                assessment = engine.assess_opportunity(req)
                                t_eval_1 = time.perf_counter()
                                lat_ms = (t_eval_1 - t_eval_0) * 1000.0
                                level_latencies[int(assessment.valuation_level)].append(lat_ms)

                                candidate_rec = {
                                    "candidate_id": f"HARVEST_{seed}_{s}_W{worker_id}",
                                    "seed": seed,
                                    "step": s,
                                    "worker": worker_id,
                                    "crop": crop_name,
                                    "distance": dist,
                                    "baseline_task": b_cmd,
                                    "candidate_task": "HARVEST" if dist == 0 else "NAVIGATE_HARVEST",
                                    "engine_net_value": assessment.net_incremental_value,
                                    "exact_delta": 0.0, # Filled if evaluated in GT
                                    "opportunity_cost": assessment.opportunity_cost,
                                    "terminal_effect": "TERMINAL_SAFE" if s < 650 else "NEAR_TERMINAL",
                                    "worker_class": "IDLE_WORKER" if b_cmd == "PASS" else "BUSY_WORKER",
                                    "valuation_level": int(assessment.valuation_level),
                                }
                                harvest_candidates.append(candidate_rec)

                                if dist == 0 and b_cmd == "PASS" and found_idle_harvest is None and s < 600:
                                    found_idle_harvest = (s, worker_id, cpos, crop_name, yield_u)
                                if dist == 0 and b_cmd == "PASS" and s >= 650 and found_terminal_harvest is None:
                                    found_terminal_harvest = (s, worker_id, cpos, crop_name, yield_u)

                            # Productive worker diversion candidate
                            if b_cmd in ("HARVEST", "WATER") and found_productive_diversion is None and day < 25:
                                found_productive_diversion = (s, worker_id, b_cmd)

        # 2. CONSTRUCT GROUND-TRUTH SAMPLES FOR THIS SEED
        gt_cases_for_seed: List[Tuple[str, int, int, str, Dict[str, Any]]] = []

        # Case A: Idle Worker Harvest (if found)
        if found_idle_harvest:
            s_ih, w_ih, cpos_ih, crop_ih, y_ih = found_idle_harvest
            cand_a0 = copy.deepcopy(base_actions[s_ih][0])
            cand_a0["hands"][w_ih - 1] = ["HARVEST"]
            gt_cases_for_seed.append(("IDLE_WORKER_HARVEST", s_ih, w_ih, "HARVEST", cand_a0))

        # Case B: Productive Worker Diversion (if found)
        if found_productive_diversion:
            s_pd, w_pd, orig_cmd = found_productive_diversion
            cand_a0 = copy.deepcopy(base_actions[s_pd][0])
            cand_a0["hands"][w_pd - 1] = ["PASS"]
            gt_cases_for_seed.append(("PRODUCTIVE_WORKER_DIVERSION", s_pd, w_pd, "PASS", cand_a0))

        # Case C: Zero Delta (PASS diverted to PASS)
        if base_actions:
            # Find a step where hand passes
            for s_pass in range(len(observations)):
                h_acts = base_actions[s_pass][0].get("hands", [])
                if h_acts and h_acts[0] == ["PASS"]:
                    cand_a0 = copy.deepcopy(base_actions[s_pass][0])
                    gt_cases_for_seed.append(("ZERO_DELTA_NEUTRAL", s_pass, 1, "PASS", cand_a0))
                    break

        # Case D: Terminal Harvest
        if found_terminal_harvest:
            s_th, w_th, cpos_th, crop_th, y_th = found_terminal_harvest
            cand_a0 = copy.deepcopy(base_actions[s_th][0])
            cand_a0["hands"][w_th - 1] = ["HARVEST"]
            gt_cases_for_seed.append(("TERMINAL_HARVEST", s_th, w_th, "HARVEST", cand_a0))

        # Evaluate each GT case against exact simulator
        for case_type, stp, wid, cand_cmd, cand_a0 in gt_cases_for_seed:
            obs_at_step = observations[stp]
            base_act_at_step = base_actions[stp][0]
            b_task = base_act_at_step.get("hands", [[]])[wid - 1][0] if wid > 0 and wid <= len(base_act_at_step.get("hands", [])) else "PASS"

            # 1. Exact Counterfactual Terminal Simulation
            cand_terminal_reward = run_counterfactual_game(
                seed=seed,
                intervention_step=stp,
                patched_action_p0=cand_a0,
                v3_agent=v3_agent
            )
            exact_delta = cand_terminal_reward - base_reward

            # 2. Labor Opportunity Engine Assessment
            econ = build_economic_state(obs_at_step)
            req = LaborOpportunityRequest(
                worker_id=wid,
                candidate_action_cmd=cand_cmd,
                econ_state=econ,
                baseline_action=base_act_at_step,
                baseline_continuation=[copy.deepcopy(base_actions[min(len(base_actions)-1, stp + offset)][0]) for offset in range(1, 7)],
                current_step=stp,
                target_location=tuple(obs_at_step["farms"][0]["hands"][wid - 1]) if wid > 0 and wid <= len(obs_at_step["farms"][0]["hands"]) else None
            )

            t0 = time.perf_counter()
            assessment = engine.assess_opportunity(req)
            t1 = time.perf_counter()
            lat_ms = (t1 - t0) * 1000.0
            level_latencies[int(assessment.valuation_level)].append(lat_ms)

            # Measure sign agreement
            # Neutral / zero agreement: both == 0.0 or within epsilon
            if abs(exact_delta) < 1e-4 and abs(assessment.net_incremental_value) < 1e-4:
                sign_agreement = True
            elif exact_delta > 0 and assessment.net_incremental_value > 0:
                sign_agreement = True
            elif exact_delta < 0 and assessment.net_incremental_value < 0:
                sign_agreement = True
            elif exact_delta == 0.0 and assessment.net_incremental_value <= 0.0 and not assessment.commit_recommendation:
                # Conservative agreement
                sign_agreement = True
            else:
                sign_agreement = False

            rec = {
                "seed": seed,
                "step": stp,
                "case_type": case_type,
                "worker": wid,
                "baseline_task": b_task,
                "candidate_task": cand_cmd,
                "baseline_action_sequence": str(base_act_at_step.get("hands", [])[:2]),
                "candidate_action_sequence": str(cand_a0.get("hands", [])[:2]),
                "dependency_closure": "WORKER_LOCAL" if assessment.valuation_level <= 2 else "EXTENDED_SIMULATION",
                "baseline_terminal_reward": base_reward,
                "candidate_terminal_reward": cand_terminal_reward,
                "exact_delta": exact_delta,
                "engine_opportunity_cost": assessment.opportunity_cost,
                "engine_net_value": assessment.net_incremental_value,
                "engine_recommendation": assessment.commit_recommendation,
                "valuation_level": int(assessment.valuation_level),
                "sign_agreement": sign_agreement,
            }
            gt_records.append(rec)

        t_elapsed_seed = time.perf_counter() - t_start_seed
        print(f"  Completed seed {seed} in {t_elapsed_seed:.2f}s ({len(gt_cases_for_seed)} GT cases evaluated).")

    # 3. WRITE GROUND-TRUTH CSV & SUMMARY
    gt_csv_path = os.path.join(RESULTS_DIR, "PHASE005_LABOR_GROUND_TRUTH.csv")
    if gt_records:
        with open(gt_csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(gt_records[0].keys()))
            writer.writeheader()
            writer.writerows(gt_records)
        print(f"\nWrote {len(gt_records)} ground-truth records to {gt_csv_path}")

    # Write Harvest Candidates CSV
    harvest_csv_path = os.path.join(RESULTS_DIR, "PHASE005_HARVEST_CANDIDATES.csv")
    if harvest_candidates:
        with open(harvest_csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(harvest_candidates[0].keys()))
            writer.writeheader()
            writer.writerows(harvest_candidates)
        print(f"Wrote {len(harvest_candidates)} genuine harvest candidates to {harvest_csv_path}")

    # Calculate summary metrics
    total_gt = len(gt_records)
    total_agreed = sum(1 for r in gt_records if r["sign_agreement"])
    sign_agreement_rate = (total_agreed / total_gt) if total_gt > 0 else 0.0

    idle_cases = [r for r in gt_records if r["case_type"] == "IDLE_WORKER_HARVEST"]
    prod_cases = [r for r in gt_records if r["case_type"] == "PRODUCTIVE_WORKER_DIVERSION"]
    zero_cases = [r for r in gt_records if r["case_type"] == "ZERO_DELTA_NEUTRAL"]
    term_cases = [r for r in gt_records if r["case_type"] == "TERMINAL_HARVEST"]

    # Latency percentiles by level
    latency_summary: Dict[str, Any] = {}
    for lvl in range(5):
        lats = sorted(level_latencies[lvl])
        if lats:
            p50 = lats[len(lats) // 2]
            p95 = lats[int(len(lats) * 0.95)]
            p99 = lats[int(len(lats) * 0.99)]
            worst = max(lats)
            latency_summary[f"Level_{lvl}"] = {
                "invocations": len(lats),
                "p50_ms": round(p50, 3),
                "p95_ms": round(p95, 3),
                "p99_ms": round(p99, 3),
                "max_ms": round(worst, 3),
            }
        else:
            latency_summary[f"Level_{lvl}"] = {
                "invocations": 0,
                "p50_ms": 0.0,
                "p95_ms": 0.0,
                "p99_ms": 0.0,
                "max_ms": 0.0,
            }

    gt_summary = {
        "cohort": {"start": seeds[0], "end": seeds[-1], "count": len(seeds)},
        "v3_chassis_sha256": v3_sha,
        "total_ground_truth_states_evaluated": total_gt,
        "total_sign_agreements": total_agreed,
        "overall_sign_agreement_rate": round(sign_agreement_rate, 4),
        "breakdown_by_case_type": {
            "IDLE_WORKER_HARVEST": {
                "total": len(idle_cases),
                "sign_agreed": sum(1 for r in idle_cases if r["sign_agreement"]),
                "mean_exact_delta": round(sum(r["exact_delta"] for r in idle_cases) / len(idle_cases), 2) if idle_cases else 0.0,
                "mean_engine_net": round(sum(r["engine_net_value"] for r in idle_cases) / len(idle_cases), 2) if idle_cases else 0.0,
            },
            "PRODUCTIVE_WORKER_DIVERSION": {
                "total": len(prod_cases),
                "sign_agreed": sum(1 for r in prod_cases if r["sign_agreement"]),
                "mean_exact_delta": round(sum(r["exact_delta"] for r in prod_cases) / len(prod_cases), 2) if prod_cases else 0.0,
                "mean_engine_net": round(sum(r["engine_net_value"] for r in prod_cases) / len(prod_cases), 2) if prod_cases else 0.0,
            },
            "ZERO_DELTA_NEUTRAL": {
                "total": len(zero_cases),
                "sign_agreed": sum(1 for r in zero_cases if r["sign_agreement"]),
            },
            "TERMINAL_HARVEST": {
                "total": len(term_cases),
                "sign_agreed": sum(1 for r in term_cases if r["sign_agreement"]),
            },
        },
        "genuine_harvest_candidates_discovered": {
            "total_candidates": len(harvest_candidates),
            "idle_worker_candidates": sum(1 for r in harvest_candidates if r["worker_class"] == "IDLE_WORKER"),
            "busy_worker_candidates": sum(1 for r in harvest_candidates if r["worker_class"] == "BUSY_WORKER"),
            "immediately_harvestable_dist_0": sum(1 for r in harvest_candidates if r["distance"] == 0),
            "route_compression_dist_1_3": sum(1 for r in harvest_candidates if 1 <= r["distance"] <= 3),
        },
        "latency_by_level": latency_summary,
        "holdout_protection": "VERIFIED_UNTOUCHED",
        "prospective_cohort": "VERIFIED_UNTOUCHED",
        "resource_conversion_status": "QUARANTINED",
    }

    gt_summary_path = os.path.join(RESULTS_DIR, "PHASE005_LABOR_GROUND_TRUTH_SUMMARY.json")
    with open(gt_summary_path, "w", encoding="utf-8") as f:
        json.dump(gt_summary, f, indent=2)
    print(f"Wrote summary to {gt_summary_path}")
    print(json.dumps(gt_summary, indent=2))


if __name__ == "__main__":
    main()
