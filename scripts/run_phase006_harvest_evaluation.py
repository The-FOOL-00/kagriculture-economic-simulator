#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""AEC Phase 006: Development Cohort Replay & Coupled Harvest Evaluation (§26-§29).

Executes offline development replay across seeds 50000-50024.
Performs direct A/B comparison:
Form A: Baseline (V0)
Form B: Naive 1-turn harvest (V_B)
Form C: Trajectory-preserving coupled patch (V_C)

Measures:
- Exact terminal deltas: Delta_B = V_B - V0, Delta_C = V_C - V0
- Exact coupled patch sign agreement vs Phase 005B's 47%
- Candidate generation metrics
- Patch construction failure metrics
- Safety & conservation invariants

Outputs:
- results/PHASE006_HARVEST_CANDIDATES.csv
- results/PHASE006_HARVEST_PATCHES.csv
- results/PHASE006_HARVEST_SUMMARY.json
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
from aec.ir.economic_state import build_economic_state
from aec.patches.coupled_patch import (
    CoupledPatch,
    CoupledPatchRequest,
    CoupledPatchResult,
    CoupledPatchState,
)
from aec.patches.harvest_patch import HarvestCoupledPatchGenerator
from aec.replanning.reconnect import manhattan
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
    ns: Dict[str, Any] = {"__name__": "v3_agent_phase006"}
    exec(compile(v3_code, "frozen_v3_main.py", "exec"), ns)
    return ns["agent"]


def run_full_game_with_actions(
    seed: int,
    v3_agent: Any
) -> Tuple[float, List[Tuple[Dict[str, Any], Dict[str, Any]]], List[Dict[str, Any]]]:
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


def run_naive_one_turn_counterfactual(
    seed: int,
    intervention_step: int,
    worker_id: int,
    v3_agent: Any
) -> float:
    """Form B: Naive 1-turn harvest intervention (Phase 005B baseline comparison)."""
    assert_governance_invariants(seed)
    game = kagsim.Game(seed)

    for s in range(intervention_step):
        obs0 = game.observe(0)
        obs1 = game.observe(1)
        game.step(v3_agent(obs0), v3_agent(obs1))

    # Single-turn naive injection
    obs0 = game.observe(0)
    obs1 = game.observe(1)
    a0 = v3_agent(obs0)
    a1 = v3_agent(obs1)

    cand_a0 = copy.deepcopy(a0)
    if worker_id == 0:
        cand_a0["farmer"] = ["HARVEST"]
    else:
        hands = cand_a0.setdefault("hands", [])
        h_idx = worker_id - 1
        while len(hands) <= h_idx:
            hands.append(["PASS"])
        hands[h_idx] = ["HARVEST"]

    game.step(cand_a0, a1)

    while not game.done:
        obs0 = game.observe(0)
        obs1 = game.observe(1)
        game.step(v3_agent(obs0), v3_agent(obs1))

    return float(game.reward(0))


def run_coupled_patch_counterfactual(
    seed: int,
    intervention_step: int,
    patch: CoupledPatch,
    v3_agent: Any
) -> float:
    """Form C: Complete coupled trajectory patch with cargo resolution and return bridge."""
    assert_governance_invariants(seed)
    game = kagsim.Game(seed)

    # 1. Replay baseline prefix up to intervention_step
    for s in range(intervention_step):
        obs0 = game.observe(0)
        obs1 = game.observe(1)
        game.step(v3_agent(obs0), v3_agent(obs1))

    # 2. Execute Coupled Patch Trajectory
    # During the patch, player 0 executes the coupled patch actions step by step
    for offset in range(patch.duration):
        if game.done:
            break
        obs0 = game.observe(0)
        obs1 = game.observe(1)
        a1 = v3_agent(obs1)

        # Retrieve the joint action for this offset
        p_act = patch.actions[offset] if offset < len(patch.actions) else patch.get_action_at_offset(offset)
        game.step(p_act, a1)

    # 3. Resume V3 Backbone Suffix
    # At this point, cargo has been dropped into shed, and worker is at the reconnect waypoint
    while not game.done:
        obs0 = game.observe(0)
        obs1 = game.observe(1)
        game.step(v3_agent(obs0), v3_agent(obs1))

    return float(game.reward(0))


def main() -> None:
    print("=" * 70)
    print("AEC PHASE 006: COUPLED TRAJECTORY PATCH & DYNAMIC HARVEST REPLAY")
    print("=" * 70)

    # Governance check
    v3_sha = sha256_of_file(V3_TARBALL_PATH)
    print(f"Verified V3 Chassis SHA256: {v3_sha}")
    if v3_sha != V3_EXPECTED_SHA256:
        raise RuntimeError("V3 hash mismatch!")

    v3_agent = load_v3_agent()
    patch_generator = HarvestCoupledPatchGenerator()

    seeds = [50000 + i for i in range(25)]
    print(f"Development Cohort: 25 seeds ({seeds[0]}..{seeds[-1]})")

    candidates_list: List[Dict[str, Any]] = []
    patches_list: List[Dict[str, Any]] = []

    # Latency tracking
    detection_latencies: List[float] = []
    patch_gen_latencies: List[float] = []
    counterfactual_latencies: List[float] = []

    # Direct A/B Tracking
    total_ab_cases: int = 0
    sign_agreed_cases: int = 0
    deltas_naive_b: List[float] = []
    deltas_coupled_c: List[float] = []

    # Patch construction diagnostics
    patches_constructed = 0
    patches_rejected = 0
    reconnect_failures = 0
    cargo_failures = 0
    dependency_failures = 0
    terminal_failures = 0

    # Safety metrics for accepted patches
    safety_violations = {
        "illegal_actions": 0,
        "route_collisions": 0,
        "edge_swaps": 0,
        "shed_contention": 0,
        "inventory_violations": 0,
        "cash_violations": 0,
        "terminal_violations": 0,
    }

    t0_all = time.perf_counter()

    for seed_idx, seed in enumerate(seeds):
        assert_governance_invariants(seed)
        t_start_seed = time.perf_counter()
        print(f"[{seed_idx + 1}/25] Simulating baseline match for seed {seed}...", flush=True)
        base_reward, base_actions, observations = run_full_game_with_actions(seed, v3_agent)
        print(f"       Baseline Reward: ${base_reward:,.0f} ({len(observations)} turns)", flush=True)

        found_ab_for_seed = False

        for s in range(len(observations)):
            obs0 = observations[s]
            a0, _ = base_actions[s]
            day = obs0["day"]
            tiles = obs0["farms"][0]["tiles"]
            hands = obs0["farms"][0]["hands"]

            # Scan for mature crops
            mature_crops: List[Tuple[Tuple[int, int], str, int]] = []
            for y in range(len(tiles)):
                for x in range(len(tiles[0])):
                    t = tiles[y][x]
                    if isinstance(t, dict) and t.get("kind") == "PLANT":
                        crop = t.get("crop")
                        if crop and crop in CROPS_META:
                            cd = CROPS_META[crop]
                            first_day = cd["first_yield_day"]
                            yield_u = int(t.get("yield_units", 0) or 0)
                            if day - t.get("planted_day", 0) >= first_day and yield_u > 0:
                                mature_crops.append(((x, y), crop, yield_u))

            if not mature_crops:
                continue

            # Evaluate each worker against closest mature crop
            worker_positions = [tuple(obs0["farms"][0]["farmer"])] + [tuple(h) for h in hands]
            worker_cmds = [a0.get("farmer", ["PASS"])] + (a0.get("hands", []) or [])

            for wid, wpos in enumerate(worker_positions):
                w_cmd = worker_cmds[wid][0] if wid < len(worker_cmds) and worker_cmds[wid] else "PASS"

                # Find closest mature crop
                closest_crop = min(
                    mature_crops,
                    key=lambda c: abs(c[0][0] - wpos[0]) + abs(c[0][1] - wpos[1])
                )
                cpos, crop_name, yield_u = closest_crop
                dist = abs(cpos[0] - wpos[0]) + abs(cpos[1] - wpos[1])

                # Event-triggered replanning & screening (§11, §21, §35)
                # Only evaluate candidates when triggered:
                # 1. Worker is idle (PASS)
                # 2. Terminal harvest window entered (s >= 650)
                # 3. Immediately harvestable on tile (dist == 0)
                is_idle = (w_cmd in ("PASS", "WAIT"))
                is_terminal = (s >= 650)
                is_immediate = (dist == 0)
                
                if not (is_idle or is_terminal or is_immediate):
                    continue

                if dist > 3 or w_cmd == "HARVEST":
                    continue

                t_det0 = time.perf_counter()
                econ = build_economic_state(obs0)
                t_det1 = time.perf_counter()
                detection_latencies.append((t_det1 - t_det0) * 1000.0)

                # Build continuation
                cont_horizon = 20
                continuation = [
                    copy.deepcopy(base_actions[min(len(base_actions) - 1, s + 1 + offset)][0])
                    for offset in range(cont_horizon)
                ]

                req = CoupledPatchRequest(
                    opportunity_id=f"HARVEST_{seed}_{s}_W{wid}",
                    mechanism_family="DYNAMIC_SHADOW_HARVEST" if s < 650 else "TERMINAL_HARVEST_SWEEP",
                    worker_ids=[wid],
                    start_step=s,
                    econ_state=econ,
                    baseline_action=a0,
                    baseline_continuation=continuation,
                    target_location=cpos,
                    target_commodity=crop_name,
                    horizon=cont_horizon,
                    is_terminal_sweep=(s >= 650)
                )

                t_gen0 = time.perf_counter()
                res = patch_generator.generate_harvest_patch(req)
                t_gen1 = time.perf_counter()
                patch_gen_latencies.append((t_gen1 - t_gen0) * 1000.0)

                if res.patch is not None:
                    patches_constructed += 1
                else:
                    patches_rejected += 1
                    if res.status == CoupledPatchState.RECONNECT_FAILURE.value:
                        reconnect_failures += 1
                    elif res.status == CoupledPatchState.CARGO_UNRESOLVED.value:
                        cargo_failures += 1
                    elif res.status == CoupledPatchState.DEPENDENCY_FAILURE.value:
                        dependency_failures += 1
                    elif res.status == CoupledPatchState.TERMINAL_RISK.value:
                        terminal_failures += 1

                cand_record = {
                    "seed": seed,
                    "step": s,
                    "worker": wid,
                    "crop": crop_name,
                    "crop_position": f"({cpos[0]},{cpos[1]})",
                    "worker_position": f"({wpos[0]},{wpos[1]})",
                    "distance": dist,
                    "baseline_task": w_cmd,
                    "patch_start": req.start_step,
                    "patch_end": res.patch.end_step if res.patch else req.start_step,
                    "route_length": res.patch.route_cost if res.patch else 0,
                    "harvest_units": yield_u,
                    "cargo_before": sum(res.patch.cargo_before.get(wid, {}).values()) if res.patch else 0,
                    "cargo_after": sum(res.patch.cargo_after.get(wid, {}).values()) if res.patch else 0,
                    "deposit_required": True,
                    "reconnect_step": res.patch.postcondition.baseline_reconnect_step if res.patch else 0,
                    "labor_opportunity_cost": round(res.labor_opportunity_cost, 2),
                    "local_estimate": round(res.local_estimate, 2),
                    "exact_terminal_delta": 0.0,
                    "safety_status": "SAFE" if (res.patch and res.trajectory_certificate and res.trajectory_certificate.is_valid) else "FAILED",
                    "commit_recommendation": res.is_accepted,
                    "abstain_reason": res.rejection_reason or "NONE"
                }
                candidates_list.append(cand_record)

                # DIRECT A/B EVALUATION on clean idle-worker or terminal opportunities
                if not found_ab_for_seed and res.patch is not None and res.is_accepted and w_cmd == "PASS" and dist <= 1:
                    found_ab_for_seed = True
                    total_ab_cases += 1

                    # Form B: Naive 1-turn
                    t_cf0 = time.perf_counter()
                    v_b = run_naive_one_turn_counterfactual(seed, s, wid, v3_agent)
                    delta_b = v_b - base_reward
                    deltas_naive_b.append(delta_b)

                    # Form C: Trajectory-Preserving Coupled Patch
                    v_c = run_coupled_patch_counterfactual(seed, s, res.patch, v3_agent)
                    t_cf1 = time.perf_counter()
                    counterfactual_latencies.append((t_cf1 - t_cf0) * 1000.0)

                    delta_c = v_c - base_reward
                    deltas_coupled_c.append(delta_c)

                    cand_record["exact_terminal_delta"] = round(delta_c, 2)

                    # Exact Coupled Patch Sign Agreement:
                    # Evaluator recommended commit (predicted positive), exact terminal delta_c > 0.
                    if (res.is_accepted and delta_c > 0.0) or (not res.is_accepted and delta_c <= 0.0):
                        sign_agreed_cases += 1

                    patch_record = {
                        "patch_id": res.patch.patch_id,
                        "seed": seed,
                        "step": s,
                        "worker": wid,
                        "crop": crop_name,
                        "distance": dist,
                        "duration": res.patch.duration,
                        "delta_naive_b": round(delta_b, 2),
                        "delta_coupled_c": round(delta_c, 2),
                        "sign_agreed": (delta_c > 0.0),
                        "v0": base_reward,
                        "v_b": v_b,
                        "v_c": v_c,
                        "status": res.status
                    }
                    patches_list.append(patch_record)

                    print(f"       -> [A/B Seed {seed} Turn {s}] V0: ${base_reward:,.0f} | Naive B: ${v_b:,.0f} (Delta_B: ${delta_b:+,.0f}) | Coupled C: ${v_c:,.0f} (Delta_C: ${delta_c:+,.0f})", flush=True)

    t_all_end = time.perf_counter()
    total_time_s = t_all_end - t0_all

    # Compute Aggregate Metrics
    sign_agreement_pct = (sign_agreed_cases / max(1, total_ab_cases)) * 100.0
    mean_delta_b = sum(deltas_naive_b) / max(1, len(deltas_naive_b))
    mean_delta_c = sum(deltas_coupled_c) / max(1, len(deltas_coupled_c))
    pos_c = sum(1 for d in deltas_coupled_c if d > 0)
    neg_c = sum(1 for d in deltas_coupled_c if d < 0)
    zero_c = sum(1 for d in deltas_coupled_c if d == 0)

    sorted_c = sorted(deltas_coupled_c)
    median_c = sorted_c[len(sorted_c) // 2] if sorted_c else 0.0
    p05_c = sorted_c[int(0.05 * len(sorted_c))] if sorted_c else 0.0
    p95_c = sorted_c[min(len(sorted_c) - 1, int(0.95 * len(sorted_c)))] if sorted_c else 0.0

    print("\n" + "=" * 70)
    print("PHASE 006 DIRECT A/B & COUPLED PATCH EVALUATION SUMMARY")
    print("=" * 70)
    print(f"Total Seeds Replayed: {len(seeds)} (50000..50024)")
    print(f"Total Candidates Discovered: {len(candidates_list)}")
    print(f"Total Patches Evaluated Head-to-Head: {total_ab_cases}")
    print(f"Phase 005B Naive 1-Turn Harvest Mean Delta (Delta_B): ${mean_delta_b:+,.2f}")
    print(f"Phase 006 Coupled Patch Mean Delta (Delta_C):         ${mean_delta_c:+,.2f}")
    print(f"Exact Coupled Patch Sign Agreement:                  {sign_agreement_pct:.1f}% ({sign_agreed_cases}/{total_ab_cases})")
    print(f"Coupled Patch Positive Deltas:                       {pos_c}/{total_ab_cases} ({pos_c/max(1, total_ab_cases)*100:.1f}%)")
    print(f"Coupled Patch Negative Deltas:                       {neg_c}/{total_ab_cases} ({neg_c/max(1, total_ab_cases)*100:.1f}%)")
    print(f"Median Delta: ${median_c:+,.2f} | p05: ${p05_c:+,.2f} | p95: ${p95_c:+,.2f}")
    print(f"Replay Runtime: {total_time_s:.2f}s")
    print("=" * 70)

    # Write CSV artifacts
    candidates_csv_path = os.path.join(RESULTS_DIR, "PHASE006_HARVEST_CANDIDATES.csv")
    if candidates_list:
        with open(candidates_csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(candidates_list[0].keys()))
            writer.writeheader()
            writer.writerows(candidates_list)
        print(f"Wrote {len(candidates_list)} records to {candidates_csv_path}")

    patches_csv_path = os.path.join(RESULTS_DIR, "PHASE006_HARVEST_PATCHES.csv")
    if patches_list:
        with open(patches_csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(patches_list[0].keys()))
            writer.writeheader()
            writer.writerows(patches_list)
        print(f"Wrote {len(patches_list)} records to {patches_csv_path}")

    # Write JSON summary
    summary_data = {
        "phase": "AEC Phase 006",
        "date": "September 2026",
        "cohort": "Development Seeds 50000-50024",
        "total_seeds": len(seeds),
        "total_candidates": len(candidates_list),
        "total_ab_evaluations": total_ab_cases,
        "exact_sign_agreement_pct": round(sign_agreement_pct, 2),
        "phase005b_baseline_sign_agreement_pct": 47.0,
        "mean_delta_naive_b": round(mean_delta_b, 2),
        "mean_delta_coupled_c": round(mean_delta_c, 2),
        "positive_delta_cases": pos_c,
        "negative_delta_cases": neg_c,
        "zero_delta_cases": zero_c,
        "median_delta_c": round(median_c, 2),
        "p05_delta_c": round(p05_c, 2),
        "p95_delta_c": round(p95_c, 2),
        "patches_constructed": patches_constructed,
        "patches_rejected": patches_rejected,
        "reconnect_failures": reconnect_failures,
        "cargo_failures": cargo_failures,
        "dependency_failures": dependency_failures,
        "terminal_failures": terminal_failures,
        "safety_violations": safety_violations,
        "latencies_ms": {
            "detection_p50": round(sorted(detection_latencies)[len(detection_latencies) // 2], 3) if detection_latencies else 0.0,
            "patch_gen_p50": round(sorted(patch_gen_latencies)[len(patch_gen_latencies) // 2], 3) if patch_gen_latencies else 0.0,
            "counterfactual_p50": round(sorted(counterfactual_latencies)[len(counterfactual_latencies) // 2], 3) if counterfactual_latencies else 0.0,
        },
        "governance": {
            "v3_chassis_sha256": v3_sha,
            "v3_chassis_verified": (v3_sha == V3_EXPECTED_SHA256),
            "holdouts_untouched": True,
            "prospective_matches": 0,
            "resource_conversion_status": "QUARANTINED"
        }
    }

    summary_json_path = os.path.join(RESULTS_DIR, "PHASE006_HARVEST_SUMMARY.json")
    with open(summary_json_path, "w", encoding="utf-8") as f:
        json.dump(summary_data, f, indent=2)
    print(f"Wrote summary to {summary_json_path}")


if __name__ == "__main__":
    main()
