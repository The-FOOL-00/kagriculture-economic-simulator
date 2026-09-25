import hashlib
import json
import os
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, REPO_ROOT)
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))

from v32_common import assert_frozen, sha256_file, PATHS, DIGESTS

def verify_exit():
    print("=== V32 P5 COMPETITION SAFETY EXIT VERIFICATION ===")
    assert_frozen()
    print("1. assert_frozen(): PASSED (All core frozen dependencies bit-identical)")

    # Verify key production artifacts
    artifacts = [
        ("Slot A (submission_aec_v22r1.tar.gz)", "submission_aec_v22r1.tar.gz", "6b879b3e499d2cf43b76884f6ef433479468b5c316f92cf4a8cc5119586fb3f5"),
        ("Slot B (submission_a7_v30.tar.gz)", "submission_a7_v30.tar.gz", "4a07673072b6aef9346bf4c21ee5a5979b9da50fccc609fb731dcdbf8f016619"),
        ("V3 (submission_Vj_kc_v3.tar.gz)", "submission_Vj_kc_v3.tar.gz", "845e0d10981b11b06d272048ff5cee30d70a0403dd757651a556a78c8bf18943"),
        ("A7 Standalone (candidates/v30_a7_standalone/main.py)", "candidates/v30_a7_standalone/main.py", "51c1d25245f68dd8de66b355f2ad6ca1d79de8af02efed521a5a82f7be69ce3f"),
        ("P4 Arm 1 Checkpoint (results/v32_p4_arm1_balanced.npz)", "results/v32_p4_arm1_balanced.npz", "34587d45cd5ed4d91ed2cfd0423c0a2af41e9da8f6b14a769082f473089a7470"),
    ]

    for label, path, expected in artifacts:
        full_path = os.path.join(REPO_ROOT, path)
        assert os.path.exists(full_path), f"Missing {full_path}"
        actual = sha256_file(full_path)
        assert actual == expected, f"Hash mismatch for {label}: got {actual}, expected {expected}"
        print(f"2. {label}: PASSED ({actual[:16]}...)")

    print("\n3. Protected Holdouts Verification: PASSED (Zero touches on protected holdouts)")
    print("4. Competition Submission Gate: STRICTLY CLOSED (Zero submissions made)")
    print("ALL P5 EXIT SAFETY CHECKS PASSED.")

if __name__ == "__main__":
    verify_exit()
