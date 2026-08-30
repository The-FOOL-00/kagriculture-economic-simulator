"""
=============================================================================
KAGGRICULTURE CHAMPIONSHIP RELEASE & STAGING PIPELINE (CANONICAL)
=============================================================================
Compiles, verifies, and packages 5 genuinely distinct competitive candidates:
- Slot 1: Titan Control Baseline (Legacy reference main.py)
- Slot 2: Hybrid 6C / 3S / 10M Champion (Production Deployable Deliverable 1)
- Slot 3: Hybrid Dynamic Economic (Deliverable 2)
- Slot 4: Hybrid Lookahead Planner (Deliverable 3)
- Slot 5: Hybrid 8C / 4S High-Capacity Scaler
Guarantees 5 unique SHA256 hashes, zero staging collisions, and tarball integrity.
=============================================================================
"""

import os
import sys
import shutil
import hashlib
import tarfile
import tempfile
from kaggle_environments import make

project_root = r"c:\Users\Sundareswaran\Kagriculture"
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import compiler


def get_sha256(filepath):
    with open(filepath, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def generate_candidate_files():
    os.makedirs("candidates", exist_ok=True)

    # 0. Canonical Compilation of modular source into main.py
    print("Compiling canonical main.py from modular source...")
    compiler.compile_main("main.py")

    # 1. Slot 1: Titan Control Baseline (Legacy Pure Crop from backup)
    if os.path.exists("baseline_backup/candidates/slot1_titan_control.py"):
        shutil.copy("baseline_backup/candidates/slot1_titan_control.py", "candidates/slot1_titan_control.py")
    else:
        # Fallback to compiled main with zero animals
        with open("main.py", "r", encoding="utf-8") as f:
            t_code = f.read().replace("target_cows=6, target_sheep=3", "target_cows=0, target_sheep=0")
        with open("candidates/slot1_titan_control.py", "w", encoding="utf-8") as f:
            f.write(t_code)

    # 2. Slot 2: Hybrid 6C3S 10M Production Champion
    shutil.copy("agents/hybrid_6c3s_10m.py", "candidates/slot2_hybrid_6c3s_10m.py")

    # 3. Slot 3: Hybrid Dynamic Economic Allocator
    shutil.copy("agents/hybrid_dynamic_economic.py", "candidates/slot3_hybrid_dynamic.py")

    # 4. Slot 4: Hybrid Lookahead Planner
    shutil.copy("agents/hybrid_lookahead.py", "candidates/slot4_hybrid_lookahead.py")

    # 5. Slot 5: Hybrid 8C / 4S High-Capacity Scaler
    with open("agents/hybrid_6c3s_10m.py", "r", encoding="utf-8") as f:
        code_8c = f.read()
    code_8c = code_8c.replace("target_cows=6, target_sheep=3, target_geese=0, target_melons=10",
                              "target_cows=8, target_sheep=4, target_geese=0, target_melons=15")
    code_8c = code_8c.replace("KAGGRICULTURE CHAMPION DELIVERABLE 1: HYBRID 6C / 3S / 10M",
                              "KAGGRICULTURE CANDIDATE 5: HYBRID 8C / 4S / 15M HIGH-CAPACITY SCALER")
    with open("candidates/slot5_hybrid_8c4s.py", "w", encoding="utf-8") as f:
        f.write(code_8c)

    # Clean legacy duplicate files if present
    for legacy in [
        "candidates/slot2_loss_fix_challenger.py",
        "candidates/slot3_opponent_adaptive.py",
        "candidates/slot4_market_planner.py",
        "candidates/slot5_local_champion.py"
    ]:
        if os.path.exists(legacy):
            os.remove(legacy)

    # Package Primary Champion (Hybrid 6C3S 10M) into submission.tar.gz
    # Kaggle requires main.py at root of tarball
    temp_main = "temp_tarball_main.py"
    shutil.copy("candidates/slot2_hybrid_6c3s_10m.py", temp_main)
    with tarfile.open("submission.tar.gz", "w:gz") as tar:
        tar.add(temp_main, arcname="main.py")
    if os.path.exists(temp_main):
        os.remove(temp_main)

    print("Staging and packaging complete.")


def verify_candidates_and_tarball():
    print("\n" + "=" * 90)
    print("VERIFYING CANDIDATE INTEGRITY & UNIQUE HASHES (PART 10 & PART 11)")
    print("=" * 90)

    candidates = [
        ("Slot 1 (Titan Control)", "candidates/slot1_titan_control.py"),
        ("Slot 2 (Hybrid 6C3S 10M)", "candidates/slot2_hybrid_6c3s_10m.py"),
        ("Slot 3 (Hybrid Dynamic)", "candidates/slot3_hybrid_dynamic.py"),
        ("Slot 4 (Hybrid Lookahead)", "candidates/slot4_hybrid_lookahead.py"),
        ("Slot 5 (Hybrid 8C4S Scaler)", "candidates/slot5_hybrid_8c4s.py"),
    ]

    hashes = {}
    passed_all = True

    for label, path in candidates:
        if not os.path.exists(path):
            print(f"  [FAIL] Missing candidate file: {path}")
            passed_all = False
            continue

        h = get_sha256(path)
        if h in hashes:
            print(f"  [FAIL] HASH COLLISION DETECTED! {label} shares hash with {hashes[h]}")
            passed_all = False
        else:
            hashes[h] = label

        # Execution validation (720 steps)
        try:
            env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": 10001}, debug=False)
            env.run([path, "starter"])
            r = float(env.steps[-1][0].reward or 0.0)
            status = env.state[0].status
            if status != "DONE" or r < 0:
                print(f"  [FAIL] {label:28s} failed 720-step execution (Status: {status}, Reward: ${r:,.2f})")
                passed_all = False
            else:
                print(f"  [PASS] {label:28s} -> Hash: {h[:16]}... | 720-Step Reward: ${r:,.2f} | Status: {status}")
        except Exception as e:
            print(f"  [FAIL] {label:28s} exception: {e}")
            passed_all = False

    # PART 11: Tarball Extraction & Clean Verification
    print("\n" + "-" * 90)
    print("PART 11: CLEAN ISOLATED TARBALL EXTRACTION & EXECUTION TEST")
    print("-" * 90)
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            shutil.copy("submission.tar.gz", os.path.join(tmpdir, "submission.tar.gz"))
            with tarfile.open(os.path.join(tmpdir, "submission.tar.gz"), "r:gz") as tar:
                tar.extractall(path=tmpdir)

            extracted_main = os.path.join(tmpdir, "main.py")
            if not os.path.exists(extracted_main):
                print(f"  [FAIL] main.py missing from extracted tarball in {tmpdir}")
                passed_all = False
            else:
                extracted_hash = hashlib.sha256(open(extracted_main, "rb").read()).hexdigest()
                print(f"  [PASS] Extracted main.py from tarball -> SHA256: {extracted_hash[:16]}...")
                
                # Execute extracted artifact in clean environment
                env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": 10001}, debug=False)
                env.run([extracted_main, "starter"])
                r_tar = float(env.steps[-1][0].reward or 0.0)
                status_tar = env.state[0].status
                if status_tar == "DONE" and r_tar > 50000:
                    print(f"  [PASS] Extracted tarball completed 720 steps cleanly -> Reward: ${r_tar:,.2f} | Status: {status_tar}")
                else:
                    print(f"  [FAIL] Extracted tarball execution failure -> Reward: ${r_tar:,.2f} | Status: {status_tar}")
                    passed_all = False
    except Exception as e:
        print(f"  [FAIL] Tarball verification error: {e}")
        passed_all = False

    print("=" * 90)
    return passed_all


if __name__ == "__main__":
    generate_candidate_files()
    ok = verify_candidates_and_tarball()
    if ok:
        print("ALL 5 CANDIDATES VALIDATED WITH 100% UNIQUE HASHES & TARBALL VERIFIED!")
    else:
        print("CANDIDATE STAGING VERIFICATION FAILED!")
        sys.exit(1)
