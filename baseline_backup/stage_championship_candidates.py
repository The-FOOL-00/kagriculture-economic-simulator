"""
=============================================================================
KAGGRICULTURE CHAMPIONSHIP RELEASE & STAGING PIPELINE
=============================================================================
Compiles, verifies, and packages 5 genuinely distinct competitive candidates:
- Slot 1: Titan Control Baseline (Legacy reference)
- Slot 2: Hybrid 6C / 3S / 10M Champion (Deliverable 1)
- Slot 3: Hybrid Dynamic Economic (Deliverable 2)
- Slot 4: Hybrid Lookahead Planner (Deliverable 3)
- Slot 5: Hybrid 8C / 4S High-Capacity Scaler
Guarantees unique SHA256 hashes, zero staging collisions, and tarball integrity.
=============================================================================
"""

import os
import sys
import shutil
import hashlib
import tarfile
import importlib.util
from kaggle_environments import make

project_root = r"c:\Users\Sundareswaran\Kagriculture"
if project_root not in sys.path:
    sys.path.insert(0, project_root)


def get_sha256(filepath):
    with open(filepath, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def generate_candidate_files():
    os.makedirs("candidates", exist_ok=True)

    # 1. Slot 1: Titan Control (Legacy Pure Crop main.py)
    shutil.copy("main.py", "candidates/slot1_titan_control.py")

    # 2. Slot 2: Hybrid 6C3S 10M Champion
    shutil.copy("agents/hybrid_6c3s_10m.py", "candidates/slot2_hybrid_6c3s_10m.py")

    # 3. Slot 3: Hybrid Dynamic Economic
    shutil.copy("agents/hybrid_dynamic_economic.py", "candidates/slot3_hybrid_dynamic.py")

    # 4. Slot 4: Hybrid Lookahead Planner
    shutil.copy("agents/hybrid_lookahead.py", "candidates/slot4_hybrid_lookahead.py")

    # 5. Slot 5: Hybrid 8C / 4S High Capacity Scaler
    with open("agents/hybrid_6c3s_10m.py", "r") as f:
        code_8c = f.read()
    code_8c = code_8c.replace("target_cows=6, target_sheep=3, target_geese=0, target_melons=10",
                              "target_cows=8, target_sheep=4, target_geese=0, target_melons=15")
    code_8c = code_8c.replace("DELIVERABLE 1: HYBRID 6C / 3S / 10M",
                              "CANDIDATE 5: HYBRID 8C / 4S / 15M HIGH-CAPACITY SCALER")
    with open("candidates/slot5_hybrid_8c4s.py", "w") as f:
        f.write(code_8c)

    # Package Primary Champion (Hybrid 6C3S 10M) into submission.tar.gz
    # Note: Kaggle requires main.py at the root of submission.tar.gz
    temp_main = "temp_main.py"
    shutil.copy("agents/hybrid_6c3s_10m.py", temp_main)
    with tarfile.open("submission.tar.gz", "w:gz") as tar:
        tar.add(temp_main, arcname="main.py")
    if os.path.exists(temp_main):
        os.remove(temp_main)

    print("Staging and compilation complete.")


def verify_candidates_and_hashes():
    print("\n" + "=" * 80)
    print("VERIFYING CANDIDATE INTEGRITY & UNIQUE HASHES")
    print("=" * 80)

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
            r = env.steps[-1][0].reward
            if r is None or r < 0:
                print(f"  [FAIL] {label:28s} failed 720-step execution (Reward: {r})")
                passed_all = False
            else:
                print(f"  [PASS] {label:28s} -> Hash: {h[:16]}... | 720-Step Reward: ${r:,.2f}")
        except Exception as e:
            print(f"  [FAIL] {label:28s} exception: {e}")
            passed_all = False

    # Tarball integrity
    print("\nVerifying submission.tar.gz integrity...")
    try:
        with tarfile.open("submission.tar.gz", "r:gz") as tar:
            names = tar.getnames()
            if "main.py" in names:
                print("  [PASS] submission.tar.gz contains root main.py")
            else:
                print(f"  [FAIL] main.py missing from tarball: {names}")
                passed_all = False
    except Exception as e:
        print(f"  [FAIL] Tarball error: {e}")
        passed_all = False

    print("=" * 80)
    return passed_all


if __name__ == "__main__":
    generate_candidate_files()
    ok = verify_candidates_and_hashes()
    if ok:
        print("ALL 5 CANDIDATES VALIDATED WITH 100% UNIQUE HASHES & PACKAGED SUCCESSFULLY!")
    else:
        print("CANDIDATE STAGING VERIFICATION FAILED!")
        sys.exit(1)
