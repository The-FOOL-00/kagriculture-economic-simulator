"""
=============================================================================
KAGGLE COMPETITIONS SUBMISSION RUNNER
=============================================================================
Submits selected candidate slots to Kaggle and logs submission IDs.
=============================================================================
"""

import json
import os
import subprocess
import time


def submit_candidate(file_path, message):
    cred_path = os.path.expanduser("~/.kaggle/credentials.json")
    with open(cred_path, "r") as f:
        creds = json.load(f)

    tok = creds.get("access_token")
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
    # Submit Slot 1
    print("=" * 75)
    print("SUBMITTING SLOT 1 & SLOT 2 ONLY")
    print("=" * 75)
    
    ok1 = submit_candidate(
        "candidates/slot1_titan_control.py",
        "Slot 1: Titan Control Baseline (Live Reference)"
    )
    
    time.sleep(3)
    
    ok2 = submit_candidate(
        "candidates/slot2_loss_fix_challenger.py",
        "Slot 2: High-Throughput Liquidation Challenger (12-14 Batch Sell)"
    )
    
    time.sleep(3)
    
    # Query current submissions list
    cred_path = os.path.expanduser("~/.kaggle/credentials.json")
    with open(cred_path, "r") as f:
        creds = json.load(f)
    env = os.environ.copy()
    env["KAGGLE_API_TOKEN"] = creds.get("access_token")
    
    print("\n" + "=" * 75)
    print("RECENT KAGGLE SUBMISSIONS LIST:")
    print("=" * 75)
    res = subprocess.run(["kaggle", "competitions", "submissions", "-c", "kaggriculture"], env=env, capture_output=True, text=True)
    print(res.stdout)
