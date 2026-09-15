#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""
scratch/submit_agent.py
=======================
Submits an approved standalone agent to Kaggle with pre-submission verification.
"""

from __future__ import annotations

import argparse
import hashlib
import time
from pathlib import Path
from kaggle.api.kaggle_api_extended import KaggleApi


def submit(file_path_str: str, expected_hash: str, identity: str, message: str):
    p = Path(file_path_str)
    assert p.exists(), f"File does not exist: {p}"
    
    print("=" * 80)
    print(f"PRE-SUBMISSION VERIFICATION: {identity}")
    print("=" * 80)
    print(f"File:          {p.resolve()}")
    calc_hash = hashlib.sha256(p.read_bytes()).hexdigest()
    print(f"Calculated:    {calc_hash}")
    print(f"Expected:      {expected_hash}")
    assert calc_hash == expected_hash, f"FATAL: Cryptographic hash mismatch for {p}!"
    print("Cryptographic integrity: 100% MATCH")
    print(f"Competition:   kaggriculture")
    print(f"Identity:      {identity}")
    print(f"Message:       {message}")
    print("-" * 80)

    api = KaggleApi()
    api.authenticate()

    print("Uploading file to Kaggle...")
    api.competition_submit(str(p), message, "kaggriculture")
    print("Upload complete. Waiting 10 seconds for initial status...")

    time.sleep(10)
    subs = api.competition_submissions("kaggriculture")
    latest = subs[0]
    print(f"\nImmediate Submission Record:")
    print(f"  Ref ID:      {latest.ref}")
    print(f"  File Name:   {latest.file_name}")
    print(f"  Date (UTC):  {latest.date}")
    print(f"  Status:      {latest.status}")
    print(f"  Score:       {latest.public_score}")
    print(f"  Error Desc:  {latest.error_description}")
    print("=" * 80)

    return latest


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", required=True)
    parser.add_argument("--hash", required=True)
    parser.add_argument("--identity", required=True)
    parser.add_argument("--message", required=True)
    args = parser.parse_args()

    submit(args.file, args.hash, args.identity, args.message)
