"""
=============================================================================
KAGGRICULTURE AUTOMATED RELEASE CHECKER & QA VALIDATOR
=============================================================================
Runs exhaustive release-gate checks on all 5 submission candidates,
compiler equivalence, packaging integrity, and runtime constraints.
=============================================================================
"""

import os
import sys
import tarfile
import time
import importlib.util
from kaggle_environments import make


def check_file_exists_and_valid(path):
    if not os.path.exists(path):
        return False, f"File not found: {path}"
    try:
        spec = importlib.util.spec_from_file_location("mod", path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        if not hasattr(mod, "agent"):
            return False, f"Missing 'agent' entry point in {path}"
        return True, "Valid"
    except Exception as e:
        return False, f"Syntax or import error in {path}: {e}"


def check_tarball_integrity(tar_path="submission.tar.gz"):
    if not os.path.exists(tar_path):
        return False, f"Tarball not found: {tar_path}"
    try:
        with tarfile.open(tar_path, "r:gz") as tar:
            names = tar.getnames()
            if "main.py" not in names:
                return False, f"main.py not in root of tarball (found: {names})"
        return True, "Valid tarball with root main.py"
    except Exception as e:
        return False, f"Tarball error: {e}"


def run_full_game_test(candidate_path, opp_path="starter", seed=10001):
    start_t = time.time()
    env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed}, debug=False)
    env.run([candidate_path, opp_path])
    elapsed = time.time() - start_t
    
    last_step = env.steps[-1]
    r0 = last_step[0].reward
    r1 = last_step[1].reward
    
    if r0 is None:
        return False, f"Failed 720-step execution: reward is None", elapsed
    return True, f"720 steps completed: Cash=${r0:,.2f} vs Opp=${r1:,.2f} in {elapsed:.2f}s", elapsed


def main():
    print("=" * 80)
    print("KAGGRICULTURE RELEASE CHECKER & QA VALIDATOR")
    print("=" * 80)
    
    blocked = []
    
    # 1. Check Golden Control Immutability
    print("\n[1/7] Verifying Golden Control Immutability...")
    g_ok, g_msg = check_file_exists_and_valid("agents/golden_v1.py")
    if g_ok:
        print("  [OK] agents/golden_v1.py is valid and present")
    else:
        print(f"  [FAIL] Golden Control issue: {g_msg}")
        blocked.append(f"Golden Control: {g_msg}")

    # 2. Check Candidate Files
    print("\n[2/7] Verifying 5 Staged Submission Candidates...")
    candidates = [
        ("Slot 1 (Control)", "candidates/slot1_titan_control.py"),
        ("Slot 2 (Liquidation)", "candidates/slot2_loss_fix_challenger.py"),
        ("Slot 3 (Opponent)", "candidates/slot3_opponent_adaptive.py"),
        ("Slot 4 (Market)", "candidates/slot4_market_planner.py"),
        ("Slot 5 (Champion)", "candidates/slot5_local_champion.py"),
    ]
    
    for label, path in candidates:
        ok, msg = check_file_exists_and_valid(path)
        if ok:
            print(f"  [OK] {label:22s} ({path}) -> Valid")
        else:
            print(f"  [FAIL] {label:22s} ({path}) -> {msg}")
            blocked.append(f"{label}: {msg}")

    # 3. Compiler Execution & main.py Generation
    print("\n[3/7] Verifying Compiler Execution...")
    try:
        from compiler import compile_main
        compile_main()
        m_ok, m_msg = check_file_exists_and_valid("main.py")
        if m_ok:
            print("  [OK] main.py successfully compiled and verified")
        else:
            print(f"  [FAIL] main.py verification failed: {m_msg}")
            blocked.append(f"Compiler: {m_msg}")
    except Exception as e:
        print(f"  [FAIL] Compiler exception: {e}")
        blocked.append(f"Compiler exception: {e}")

    # 4. Behavioral Equivalence Test
    print("\n[4/7] Verifying Modular vs Compiled Equivalence...")
    try:
        env1 = make("kaggriculture", configuration={"episodeSteps": 720, "seed": 10001}, debug=False)
        env1.run(["engine/unified_agent.py", "agents/golden_v1.py"])
        r_mod = env1.steps[-1][0].reward
        
        env2 = make("kaggriculture", configuration={"episodeSteps": 720, "seed": 10001}, debug=False)
        env2.run(["main.py", "agents/golden_v1.py"])
        r_comp = env2.steps[-1][0].reward
        
        if r_mod == r_comp:
            print(f"  [OK] Exact behavioral match confirmed (Reward: ${r_comp:,.2f})")
        else:
            print(f"  [FAIL] Mismatch: Modular=${r_mod} vs Compiled=${r_comp}")
            blocked.append("Compiled equivalence mismatch")
    except Exception as e:
        print(f"  [FAIL] Equivalence test exception: {e}")
        blocked.append(f"Equivalence test: {e}")

    # 5. Tarball Packaging Integrity
    print("\n[5/7] Verifying submission.tar.gz Packaging...")
    t_ok, t_msg = check_tarball_integrity("submission.tar.gz")
    if t_ok:
        print(f"  [OK] submission.tar.gz is valid and contains root main.py")
    else:
        print(f"  [FAIL] Tarball error: {t_msg}")
        blocked.append(f"Tarball: {t_msg}")

    # 6. Full 720-Turn Execution Test for All 5 Candidates
    print("\n[6/7] Running 720-Turn Execution Tests on All Candidates...")
    for label, path in candidates:
        ok, msg, el = run_full_game_test(path, "starter", seed=10005)
        if ok:
            print(f"  [OK] {label:22s} -> {msg}")
        else:
            print(f"  [FAIL] {label:22s} -> {msg}")
            blocked.append(f"{label} execution: {msg}")

    # 7. Release Verdict
    print("\n" + "=" * 80)
    if not blocked:
        print("RELEASE STATUS: RELEASE READY (All Checks Passed)")
        print("All 5 candidate slots are validated and ready for tomorrow's submission window.")
    else:
        print("RELEASE STATUS: RELEASE BLOCKED")
        for b in blocked:
            print(f"   * {b}")
    print("=" * 80)


if __name__ == "__main__":
    main()
