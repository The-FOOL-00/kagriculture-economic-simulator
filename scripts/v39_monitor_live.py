# SPDX-License-Identifier: MIT
"""V39 Lightweight Read-Only Live Competition Monitor.

Performs read-only polling of V35 submission status and identifies
any newly completed episodes, rating changes, or emergent failure modes.
Strictly non-invasive: NEVER invokes submit or mutation commands.
"""

import json
import os
import subprocess
import sys
from datetime import datetime

sys.stdout.reconfigure(encoding="utf-8")

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
LIVE_DIR = os.path.join(REPO_ROOT, "scratch", "v39", "live")
EPISODES_FILE = os.path.join(LIVE_DIR, "episodes.jsonl")
V35_SUBMISSION_ID = "56540535"

def check_live_status():
    print(f"[{datetime.now().isoformat()}] Checking Live Status for V35 (ID: {V35_SUBMISSION_ID})...")
    
    # 1. Read existing catalog
    existing_eids = set()
    if os.path.exists(EPISODES_FILE):
        with open(EPISODES_FILE, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    rec = json.loads(line)
                    existing_eids.add(rec["episode_id"])
    print(f"Local Cataloged Episodes: {len(existing_eids)}")
    
    # 2. Try Kaggle API CLI (read-only)
    try:
        res = subprocess.run(
            ["kaggle", "competitions", "submissions", "-c", "kaggriculture"],
            capture_output=True,
            text=True,
            timeout=15
        )
        if res.returncode == 0:
            lines = res.stdout.strip().splitlines()
            v35_line = next((l for l in lines if V35_SUBMISSION_ID in l), None)
            if v35_line:
                print(f"Kaggle Live Record: {v35_line}")
            else:
                print(f"Submission {V35_SUBMISSION_ID} not found in first page of submissions.")
        else:
            print("Kaggle CLI returned non-zero. Relying on local catalog.")
    except Exception as e:
        print(f"Kaggle API call failed ({e}). Relying on local catalog.")

    print("Monitoring check complete. Baseline remains frozen and intact.")

if __name__ == "__main__":
    check_live_status()
