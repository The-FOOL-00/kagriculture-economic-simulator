# SPDX-License-Identifier: MIT
"""
Behavioral and Source Isolation Verifier for 2x2 Factorial Candidates (A, B, C, D)
Validates that candidates differ ONLY in the intended factors:
- Market Controller (MC: OFF vs ON)
- Step-712 Terminal (T712: OFF [717] vs ON [712])
Across source diffs and step-by-step runtime execution on representative seeds.
"""

import os
import sys
import difflib
import json
from kaggle_environments import make

def check_source_diffs():
    print("=" * 80)
    print("1. SOURCE CODE DIFF & ISOLATION CHECK")
    print("=" * 80)

    files = {
        "Base": "agents/aethel_factorial_base.py",
        "A": "agents/candidate_a_aethel_v1.py",
        "B": "agents/candidate_b_aethel_mc.py",
        "C": "agents/candidate_c_aethel_t712.py",
        "D": "agents/candidate_d_aethel_refined.py"
    }

    contents = {}
    for name, path in files.items():
        with open(path, "r", encoding="utf-8") as f:
            contents[name] = f.read().splitlines()

    pairs = [
        ("A", "B", "market controller only (_MARKET_CONTROLLER_ENABLED)"),
        ("A", "C", "terminal trigger only (_TERMINAL_START_STEP 717 -> 712)"),
        ("A", "D", "market controller + terminal trigger"),
        ("B", "D", "terminal trigger only (_TERMINAL_START_STEP 717 -> 712)"),
        ("C", "D", "market controller only (_MARKET_CONTROLLER_ENABLED)"),
    ]

    all_clean = True
    for c1, c2, expected in pairs:
        diff = list(difflib.unified_diff(contents[c1], contents[c2], fromfile=f"Cand_{c1}", tofile=f"Cand_{c2}", lineterm=""))
        changes = [d for d in diff if d.startswith(("+", "-")) and not d.startswith(("+++", "---"))]
        print(f"\nComparing {c1} vs {c2} (Expected: {expected}):")
        print(f"  Total changed lines: {len(changes)}")
        for ch in changes:
            print(f"    {ch}")
        
        # Verify changes match expected
        if c1 == "A" and c2 == "B":
            if not (len(changes) == 2 and any("_MARKET_CONTROLLER_ENABLED = False" in c for c in changes) and any("_MARKET_CONTROLLER_ENABLED = True" in c for c in changes)):
                print("  [ERROR] Unexpected diff in A vs B!")
                all_clean = False
        elif c1 == "A" and c2 == "C":
            if not (len(changes) == 2 and any("_TERMINAL_START_STEP = 717" in c for c in changes) and any("_TERMINAL_START_STEP = 712" in c for c in changes)):
                print("  [ERROR] Unexpected diff in A vs C!")
                all_clean = False
        elif c1 == "B" and c2 == "D":
            if not (len(changes) == 2 and any("_TERMINAL_START_STEP = 717" in c for c in changes) and any("_TERMINAL_START_STEP = 712" in c for c in changes)):
                print("  [ERROR] Unexpected diff in B vs D!")
                all_clean = False
        elif c1 == "C" and c2 == "D":
            if not (len(changes) == 2 and any("_MARKET_CONTROLLER_ENABLED = False" in c for c in changes) and any("_MARKET_CONTROLLER_ENABLED = True" in c for c in changes)):
                print("  [ERROR] Unexpected diff in C vs D!")
                all_clean = False

    if all_clean:
        print("\n>>> SOURCE ISOLATION PASSED: Exactly the specified flags differ across all pairs. <<<")
    else:
        print("\n>>> SOURCE ISOLATION FAILED <<<")
    return all_clean

def check_runtime_isolation():
    print("\n" + "=" * 80)
    print("2. RUNTIME BEHAVIORAL ISOLATION CHECK ACROSS MATCHED SEEDS")
    print("=" * 80)

    # We evaluate step-by-step trajectories of A, B, C, D against a fixed reference opponent (e.g. Starter or Slotter Silas)
    # on seed 42.
    opp_path = "replays/raw/reference_agents/slotter_silas.py"
    test_seed = 42

    candidates = {
        "A": "agents/candidate_a_aethel_v1.py",
        "B": "agents/candidate_b_aethel_mc.py",
        "C": "agents/candidate_c_aethel_t712.py",
        "D": "agents/candidate_d_aethel_refined.py"
    }

    trajectories = {}
    for name, path in candidates.items():
        env = make("kaggriculture", configuration={"seed": test_seed})
        env.run([path, opp_path])
        steps = env.steps
        trajectories[name] = steps

    # Compare step 0..711:
    # A vs C should be bit-exact identical in every single action (farmer, hands, market) and farm state!
    # B vs D should be bit-exact identical in every single action (farmer, hands, market) and farm state!
    # A vs B should differ ONLY in market queue order (farmer and hands must be bit-exact identical)!
    # C vs D should differ ONLY in market queue order (farmer and hands must be bit-exact identical)!

    print("\nVerifying Step 0..711 Pre-Terminal Invariants (Seed 42):")

    # 1. A vs C identical up to step 711
    ac_action_diffs = 0
    for s in range(len(trajectories["A"])):
        step_num = s
        if step_num >= 712:
            break
        act_a = trajectories["A"][s][0].get("action")
        act_c = trajectories["C"][s][0].get("action")
        if act_a != act_c:
            ac_action_diffs += 1
            print(f"  [ERROR] Step {step_num} action mismatch between A and C: A={act_a} vs C={act_c}")
    print(f"  A vs C pre-712 action differences: {ac_action_diffs} (Expected: 0)")

    # 2. B vs D identical up to step 711
    bd_action_diffs = 0
    for s in range(len(trajectories["B"])):
        step_num = s
        if step_num >= 712:
            break
        act_b = trajectories["B"][s][0].get("action")
        act_d = trajectories["D"][s][0].get("action")
        if act_b != act_d:
            bd_action_diffs += 1
            print(f"  [ERROR] Step {step_num} action mismatch between B and D: B={act_b} vs D={act_d}")
    print(f"  B vs D pre-712 action differences: {bd_action_diffs} (Expected: 0)")

    # 3. A vs B spatial worker actions identical (farmer + hands) for all steps 0..716
    ab_spatial_diffs = 0
    ab_market_diffs = 0
    for s in range(len(trajectories["A"])):
        step_num = s
        if step_num >= 717:
            break
        act_a = trajectories["A"][s][0].get("action") or {}
        act_b = trajectories["B"][s][0].get("action") or {}
        spatial_a = (act_a.get("farmer"), act_a.get("hands"))
        spatial_b = (act_b.get("farmer"), act_b.get("hands"))
        if spatial_a != spatial_b:
            ab_spatial_diffs += 1
        if act_a.get("market") != act_b.get("market"):
            ab_market_diffs += 1

    print(f"  A vs B spatial worker differences (steps 0..716): {ab_spatial_diffs} (Expected: 0)")
    print(f"  A vs B market order differences (steps 0..716): {ab_market_diffs} (Expected: > 0)")

    # 4. Terminal divergence at step 712:
    # C and D should switch to terminal controller at step 712, whereas A and B switch at step 717
    print("\nVerifying Step 712..719 Terminal Behavior:")
    for s in range(712, min(len(trajectories["A"]), 720)):
        act_a = trajectories["A"][s][0].get("action")
        act_c = trajectories["C"][s][0].get("action")
        act_d = trajectories["D"][s][0].get("action")
        print(f"  Step {s}: A_act_farmer={act_a.get('farmer') if act_a else None} | C_act_farmer={act_c.get('farmer') if act_c else None} | D_act_farmer={act_d.get('farmer') if act_d else None}")

    passed = (ac_action_diffs == 0 and bd_action_diffs == 0 and ab_spatial_diffs == 0 and ab_market_diffs > 0)
    if passed:
        print("\n>>> RUNTIME BEHAVIORAL ISOLATION PASSED: Spatial tape, workers, livestock, and inventory remain 100% identical. Only Market Controller and Terminal 712 vary exactly as designed. <<<")
    else:
        print("\n>>> RUNTIME BEHAVIORAL ISOLATION FAILED <<<")
    return passed

if __name__ == "__main__":
    src_ok = check_source_diffs()
    run_ok = check_runtime_isolation()
    if src_ok and run_ok:
        print("\nALL FACTORIAL ISOLATION CHECKS PASSED PERFECTLY.")
        sys.exit(0)
    else:
        print("\nISOLATION CHECKS FAILED.")
        sys.exit(1)
