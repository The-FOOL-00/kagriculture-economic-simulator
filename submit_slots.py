"""
=============================================================================
KAGGLE COMPETITIONS SUBMISSION RUNNER (SLOTS 3 & 4)
=============================================================================
Submits Slot 3 and Slot 4 to Kaggle using refreshed OAuth credentials.
=============================================================================
"""

import json
import os
import subprocess
import time


def submit_candidate(file_path, message):
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
    print("SUBMITTING SLOT 3 & SLOT 4")
    print("=" * 75)
    
    ok3 = submit_candidate(
        "candidates/slot3_opponent_adaptive.py",
        "Slot 3: Opponent-Adaptive Challenger (Anti-Glut Radar)"
    )
    
    time.sleep(3)
    
    ok4 = submit_candidate(
        "candidates/slot4_market_planner.py",
        "Slot 4: Market Planner Challenger (Scarcity Arbitrage Engine)"
    )
    
    time.sleep(3)
    
    # Query current submissions list
    tok = subprocess.check_output(["kaggle", "auth", "print-access-token"], text=True).strip()
    env = os.environ.copy()
    env["KAGGLE_API_TOKEN"] = tok
    
    print("\n" + "=" * 75)
    print("RECENT KAGGLE SUBMISSIONS LIST:")
    print("=" * 75)
    res = subprocess.run(["kaggle", "competitions", "submissions", "-c", "kaggriculture"], env=env, capture_output=True, text=True)
    print(res.stdout)
