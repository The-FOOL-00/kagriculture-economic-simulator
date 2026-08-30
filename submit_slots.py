"""
=============================================================================
KAGGLE COMPETITIONS SUBMISSION RUNNER (CORRECTED & VALIDATED)
=============================================================================
Submits verified candidates to Kaggle slots using authenticated credentials.
Guarantees candidate file existence and logs submission responses.
=============================================================================
"""

import os
import sys
import subprocess
import time

CANDIDATES_MAP = {
    "slot1": ("candidates/slot1_titan_control.py", "Slot 1: Titan Pure Crop Control Baseline"),
    "slot2": ("candidates/slot2_hybrid_6c3s_10m.py", "Slot 2: Hybrid 6C/3S/10M Production Champion"),
    "slot3": ("candidates/slot3_hybrid_dynamic.py", "Slot 3: Hybrid Dynamic Economic Allocator"),
    "slot4": ("candidates/slot4_hybrid_lookahead.py", "Slot 4: Hybrid Lookahead Capital Planner"),
    "slot5": ("candidates/slot5_hybrid_8c4s.py", "Slot 5: Hybrid 8C/4S High-Capacity Scaler"),
}


def submit_candidate(file_path, message):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Cannot submit non-existent candidate: {file_path}")

    tok = subprocess.check_output(["kaggle", "auth", "print-access-token"], text=True).strip()
    env = os.environ.copy()
    env["KAGGLE_API_TOKEN"] = tok

    print(f"\nSubmitting {file_path}...")
    print(f"Message: {message}")
    
    cmd = [
        "kaggle", "competitions", "submit",
        "-c", "kaggriculture",
        "-f", file_path,
        "-m", message
    ]
    
    res = subprocess.run(cmd, env=env, capture_output=True, text=True)
    print("Return code:", res.returncode)
    print("STDOUT:", res.stdout)
    if res.stderr:
        print("STDERR:", res.stderr)

    return res.returncode == 0


if __name__ == "__main__":
    print("=" * 75)
    print("KAGGLE SUBMISSION RUNNER - VERIFIED CANDIDATE TARGETS")
    print("=" * 75)
    
    # Verify all targets exist before submitting
    for slot, (path, msg) in CANDIDATES_MAP.items():
        assert os.path.exists(path), f"Candidate {path} missing!"
        print(f"  * {slot}: {path} [FOUND]")

    print("\nTo submit specific slots, call submit_candidate(path, message).")
