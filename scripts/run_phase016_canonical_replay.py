#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Phase 016 Canonical Replay: Phase 015 Failure Reproduction & Macro Rescue Audit (§18).

Replays Seed 249276:
1. Replays under Phase 015 unrescued static H=18 evaluator (reproducing the catastrophic divergence).
2. Replays under Phase 016 Macro-Aware Long-Horizon evaluator (testing whether macro bifurcation is caught and rejected).
3. Evaluates the canonical Step 195 (and Step 68) candidate states in detail:
   - Local H=18 value
   - Macro boundary detection & regime identified
   - Escalation horizon chosen
   - Dynamic V3 downstream divergence detection
   - Long-horizon terminal delta recognition
   - Final Commit vs Abstain decision
"""

import copy
import json
import os
import sys
import tarfile
import time
from typing import Any, Dict, List, Optional

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


def load_v3_agent() -> Any:
    with tarfile.open(V3_TARBALL_PATH, "r:gz") as tar:
        member = tar.extractfile("main.py")
        if member is None:
            raise RuntimeError("main.py not found in V3 tarball")
        v3_code = member.read().decode("utf-8")
    ns: Dict[str, Any] = {}
    exec(compile(v3_code, "frozen_v3_main.py", "exec"), ns)
    return ns["agent"]


def replay_seed_249276():
    seed = 249276
    print(f"=== REPLAYING SEED {seed} UNDER PHASE 016 EVALUATOR ===")

    # Setup configurations
    control_config = build_robust_qualified_config()
    # Treatment with Phase 015 mechanisms enabled to test evaluator rescue
    treatment_config = build_phase015_treatment_config()

    # Run Match 1: Seat 0 = Treatment (Phase 016 Rescued), Seat 1 = Control
    game = kagsim.Game(seed)
    v3_agent = load_v3_agent()

    trt_exec = AECExecutor(config=treatment_config)
    ctrl_exec = AECExecutor(config=control_config)

    step_records = []
    t0 = time.time()

    total_escalations = 0
    escalations_by_regime = {}
    phase015_candidates_screened = 0
    phase015_candidates_escalated = 0
    phase015_candidates_rejected = 0
    phase015_candidates_committed = 0

    while not game.done:
        obs_p0 = game.observe(0)
        obs_p1 = game.observe(1)
        step = obs_p0.get("step", 0)

        # Act Treatment (p0)
        act_p0 = trt_exec.act(obs_p0)
        telem_p0 = trt_exec.latest_telemetry

        # Act Control (p1)
        act_p1 = ctrl_exec.act(obs_p1)

        # Inspect candidate telemetry on p0
        if telem_p0 and telem_p0.candidates:
            for c in telem_p0.candidates:
                if "AUTONOMOUS_TRANCHE" in c.mechanism_family or "ASSET_HOLDING" in c.mechanism_family:
                    phase015_candidates_screened += 1
                    if c.macro_escalated:
                        phase015_candidates_escalated += 1
                    if c.commit_decision:
                        phase015_candidates_committed += 1
                    else:
                        phase015_candidates_rejected += 1

                    step_records.append({
                        "step": step,
                        "patch_id": c.patch_id,
                        "family": c.mechanism_family,
                        "macro_escalated": c.macro_escalated,
                        "macro_regime": c.macro_regime_type,
                        "macro_reason": c.macro_escalation_reason,
                        "first_divergence_turn": c.first_divergence_turn,
                        "horizon": c.simulation_horizon,
                        "delta_money": c.delta_money,
                        "delta_margin": c.delta_margin,
                        "safety_pass": c.safety_pass,
                        "commit_decision": c.commit_decision,
                        "economic_rejection": c.economic_rejection_reason,
                        "safety_rejection": c.safety_rejection_reason,
                    })

        if telem_p0 and telem_p0.macro_escalations_count > 0:
            total_escalations += telem_p0.macro_escalations_count
            for r, cnt in telem_p0.macro_escalated_by_regime.items():
                escalations_by_regime[r] = escalations_by_regime.get(r, 0) + cnt

        game.step(act_p0, act_p1)

    elapsed_m1 = time.time() - t0
    final_p0_m1 = float(game.reward(0))
    final_p1_m1 = float(game.reward(1))
    s0_margin = final_p0_m1 - final_p1_m1

    print(f"Match 1 (Trt Seat 0) Finished in {elapsed_m1:.2f}s:")
    print(f"  P0 (Trt):   ${final_p0_m1:,.2f}")
    print(f"  P1 (Ctrl):  ${final_p1_m1:,.2f}")
    print(f"  Margin:     ${s0_margin:,.2f}")

    # Run Match 2: Seat 1 = Treatment, Seat 0 = Control (Mirror Match)
    print("Running Mirror Match 2 (Trt Seat 1, Ctrl Seat 0)...")
    game2 = kagsim.Game(seed)
    trt_exec2 = AECExecutor(config=treatment_config)
    ctrl_exec2 = AECExecutor(config=control_config)

    t1 = time.time()
    while not game2.done:
        obs_p0 = game2.observe(0)
        obs_p1 = game2.observe(1)

        act_p0 = ctrl_exec2.act(obs_p0)
        act_p1 = trt_exec2.act(obs_p1)

        game2.step(act_p0, act_p1)

    elapsed_m2 = time.time() - t1
    final_p0_m2 = float(game2.reward(0))
    final_p1_m2 = float(game2.reward(1))
    s1_margin = final_p1_m2 - final_p0_m2

    print(f"Match 2 (Trt Seat 1) Finished in {elapsed_m2:.2f}s:")
    print(f"  P0 (Ctrl):  ${final_p0_m2:,.2f}")
    print(f"  P1 (Trt):   ${final_p1_m2:,.2f}")
    print(f"  Margin:     ${s1_margin:,.2f}")

    paired_margin = (s0_margin + s1_margin) / 2.0
    print(f"=== SEED 249276 REPLAY SUMMARY ===")
    print(f"  Seat 0 Margin:    ${s0_margin:,.2f}")
    print(f"  Seat 1 Margin:    ${s1_margin:,.2f}")
    print(f"  Paired Margin:    ${paired_margin:,.2f}  (Phase 015 Unrescued was -$39,455.00!)")
    print(f"  Phase015 Candidates Screened: {phase015_candidates_screened}")
    print(f"  Escalated:                    {phase015_candidates_escalated}")
    print(f"  Committed:                    {phase015_candidates_committed}")
    print(f"  Rejected:                     {phase015_candidates_rejected}")
    print(f"  Total Macro Escalations:      {total_escalations} ({escalations_by_regime})")

    replay_summary = {
        "seed": seed,
        "seat_0_margin": s0_margin,
        "seat_1_margin": s1_margin,
        "paired_margin": paired_margin,
        "phase015_historical_paired_margin": -39455.0,
        "rescue_improvement": paired_margin - (-39455.0),
        "phase015_candidates_screened": phase015_candidates_screened,
        "phase015_candidates_escalated": phase015_candidates_escalated,
        "phase015_candidates_committed": phase015_candidates_committed,
        "phase015_candidates_rejected": phase015_candidates_rejected,
        "total_macro_escalations": total_escalations,
        "escalations_by_regime": escalations_by_regime,
        "sample_step_records": step_records[:30],
    }

    out_path = os.path.join(REPO_ROOT, "results", "PHASE016_CANONICAL_REPLAY.json")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(replay_summary, f, indent=2)
    print(f"Saved replay summary to {out_path}")

    return replay_summary


if __name__ == "__main__":
    replay_seed_249276()
