# SPDX-License-Identifier: MIT
"""
Behavioral Equivalence and Action Diff Verification Tool:
Verifying Zero Uncontrolled Divergence across Candidates A, B, C, D.
"""

import os
import sys
import json
from kaggle_environments import make

def run_diff_audit(seed=42):
    print("=" * 90)
    print(f"BEHAVIORAL EQUIVALENCE & ZERO UNCONTROLLED DIVERGENCE AUDIT (Seed {seed})")
    print("=" * 90)

    opp_path = os.path.abspath("replays/raw/reference_agents/closer_cleo.py")
    candidates = {
        "A": os.path.abspath("agents/candidate_a_aethel_v1.py"),
        "B": os.path.abspath("agents/candidate_b_aethel_mc.py"),
        "C": os.path.abspath("agents/candidate_c_aethel_t712.py"),
        "D": os.path.abspath("agents/candidate_d_aethel_refined.py"),
    }

    env_runs = {}
    for cand_name, cand_path in candidates.items():
        env = make("kaggriculture", configuration={"seed": seed})
        env.run([cand_path, opp_path])
        env_runs[cand_name] = env

    # 1. Compare A vs B: Worker Actions must be 100% IDENTICAL for ALL 720 TURNS
    print("\n--- 1. Auditing Candidate A vs Candidate B (Worker Action Invariance) ---")
    worker_diffs_ab = []
    for step in range(720):
        act_a = env_runs["A"].steps[step][0].get("action") or {}
        act_b = env_runs["B"].steps[step][0].get("action") or {}

        farmer_a = act_a.get("farmer")
        farmer_b = act_b.get("farmer")
        hands_a = act_a.get("hands")
        hands_b = act_b.get("hands")

        if farmer_a != farmer_b or hands_a != hands_b:
            worker_diffs_ab.append({
                "step": step,
                "farmer_a": farmer_a,
                "farmer_b": farmer_b,
                "hands_a": hands_a,
                "hands_b": hands_b
            })

    print(f"Total Worker/Spatial Action Divergences (A vs B across 720 turns): {len(worker_diffs_ab)}")
    assert len(worker_diffs_ab) == 0, f"UNCONTROLLED WORKER DIVERGENCE DETECTED IN A vs B: {worker_diffs_ab[:3]}"
    print("[VERIFIED PASS] A and B execute 100% identical worker movements across all 720 turns.")

    # 2. Compare A vs C: Worker Actions must be 100% IDENTICAL for steps 0..711
    print("\n--- 2. Auditing Candidate A vs Candidate C (Pre-Terminal Spatial Invariance) ---")
    worker_diffs_ac = []
    for step in range(712):
        act_a = env_runs["A"].steps[step][0].get("action") or {}
        act_c = env_runs["C"].steps[step][0].get("action") or {}

        farmer_a = act_a.get("farmer")
        farmer_c = act_c.get("farmer")
        hands_a = act_a.get("hands")
        hands_c = act_c.get("hands")

        if farmer_a != farmer_c or hands_a != hands_c:
            worker_diffs_ac.append({
                "step": step,
                "farmer_a": farmer_a,
                "farmer_c": farmer_c,
                "hands_a": hands_a,
                "hands_c": hands_c
            })

    print(f"Total Pre-Terminal Spatial Divergences (A vs C across turns 0-711): {len(worker_diffs_ac)}")
    assert len(worker_diffs_ac) == 0, f"UNCONTROLLED WORKER DIVERGENCE DETECTED IN A vs C: {worker_diffs_ac[:3]}"
    print("[VERIFIED PASS] A and C execute 100% identical spatial route up to Turn 711.")

    # 3. Compare A vs D: Worker Actions must be 100% IDENTICAL for steps 0..711
    print("\n--- 3. Auditing Candidate A vs Candidate D (Pre-Terminal Spatial Invariance) ---")
    worker_diffs_ad = []
    for step in range(712):
        act_a = env_runs["A"].steps[step][0].get("action") or {}
        act_d = env_runs["D"].steps[step][0].get("action") or {}

        farmer_a = act_a.get("farmer")
        farmer_d = act_d.get("farmer")
        hands_a = act_a.get("hands")
        hands_d = act_d.get("hands")

        if farmer_a != farmer_d or hands_a != hands_d:
            worker_diffs_ad.append({
                "step": step,
                "farmer_a": farmer_a,
                "farmer_d": farmer_d,
                "hands_a": hands_a,
                "hands_d": hands_d
            })

    print(f"Total Pre-Terminal Spatial Divergences (A vs D across turns 0-711): {len(worker_diffs_ad)}")
    assert len(worker_diffs_ad) == 0, f"UNCONTROLLED WORKER DIVERGENCE DETECTED IN A vs D: {worker_diffs_ad[:3]}"
    print("[VERIFIED PASS] A and D execute 100% identical spatial route up to Turn 711.")

    # 4. Check Terminal Divergence Timing (A vs D)
    print("\n--- 4. Auditing Terminal Controller Transition Turn ---")
    divergence_turn = -1
    for step in range(720):
        act_a = env_runs["A"].steps[step][0].get("action") or {}
        act_d = env_runs["D"].steps[step][0].get("action") or {}
        if act_a.get("farmer") != act_d.get("farmer") or act_a.get("hands") != act_d.get("hands"):
            divergence_turn = step
            break

    print(f"First Spatial Divergence between A and D: Turn {divergence_turn}")
    assert divergence_turn >= 712, f"Unexpected early divergence at step {divergence_turn} (must be >= 712)"
    print("[VERIFIED PASS] Exact spatial divergence occurs strictly in terminal phase (Step >= 712).")

    print("\n" + "=" * 90)
    print("ALL BEHAVIORAL EQUIVALENCE & ZERO UNCONTROLLED DIVERGENCE INVARIANTS PASS.")
    print("=" * 90)

if __name__ == "__main__":
    run_diff_audit(seed=42)
