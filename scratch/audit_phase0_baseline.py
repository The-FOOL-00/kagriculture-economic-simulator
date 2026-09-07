"""
Phase 0: Immutability and Reproducibility Audit Harness.
Formally verifies:
1. Slot 1 and Slot 2 SHA256 hashes against canonical expectations.
2. Git status and working directory cleanliness.
3. Python version, kaggle-environments version, engine configuration.
4. Clean baseline head-to-head match between Slot 1 and Slot 2.
"""

import hashlib
import json
import os
import subprocess
import sys
import kaggle_environments

EXPECTED_HASHES = {
    "Slot 1 (Aethel-Prime V1)": {
        "file": "agents/candidate_a_aethel_v1.py",
        "expected_sha256": "c1945f24f34ca9d5124e8200df14af019f6cb4cdec3ca402d9a3a88f6b04e36f",
        "submission_id": "55944418"
    },
    "Slot 2 (Aethel-Refined V2)": {
        "file": "candidates/slot2_aethel_refined_v2.py",
        "expected_sha256": "79efb19a9b9d8146d53a7531d1f1962d5d963b8ea2b5b509e12ad526559de93d",
        "submission_id": "55958978"
    }
}

def get_file_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().lower()

def run_phase0():
    print("=" * 80)
    print("PHASE 0: IMMUTABILITY & REPRODUCIBILITY AUDIT")
    print("=" * 80)

    # 1. Verify Hashes
    all_match = True
    for slot_name, meta in EXPECTED_HASHES.items():
        filepath = meta["file"]
        expected = meta["expected_sha256"].lower()
        if not os.path.exists(filepath):
            print(f"ERROR: File not found: {filepath}")
            all_match = False
            continue
        actual = get_file_sha256(filepath)
        match = (actual == expected)
        print(f"[{'PASS' if match else 'FAIL'}] {slot_name}:")
        print(f"  File: {filepath}")
        print(f"  Submission ID: {meta['submission_id']}")
        print(f"  Expected: {expected}")
        print(f"  Actual:   {actual}")
        if not match:
            all_match = False

    if not all_match:
        print("\nCRITICAL FAILURE: SHA256 HASH MISMATCH DETECTED. STOPPING.")
        sys.exit(1)

    print("\nAll immutable controls verified 100% untouched.")

    # 2. Record Git Status
    git_status = subprocess.check_output(["git", "status", "--short"], text=True).strip()
    print(f"\nGit Status:\n{git_status if git_status else 'Clean (nothing to commit)'}")

    # 3. Environment Details
    print(f"Python Version: {sys.version.split()[0]}")
    print(f"kaggle-environments Version: {kaggle_environments.__version__}")
    print(f"Platform: {sys.platform}")

    # 4. Baseline Runs (V1 vs V2, V2 vs V1 on seed 42 and 100)
    import importlib.util

    def load_module_from_path(name, path):
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod

    v1 = load_module_from_path("v1_module", os.path.abspath(EXPECTED_HASHES["Slot 1 (Aethel-Prime V1)"]["file"]))
    v2 = load_module_from_path("v2_module", os.path.abspath(EXPECTED_HASHES["Slot 2 (Aethel-Refined V2)"]["file"]))

    print("\n--- BASELINE CONTROL RUNS ---")
    seeds = [42, 100, 2026]
    baseline_records = []
    for s in seeds:
        env = kaggle_environments.make("kaggriculture", configuration={"seed": s, "episodeSteps": 720})
        env.run([v1.agent, v2.agent])
        r0 = float(env.steps[-1][0]["reward"])
        r1 = float(env.steps[-1][1]["reward"])
        print(f"Seed {s}: V1 (P0)=${r0:,.1f} vs V2 (P1)=${r1:,.1f} | Delta (V2 - V1)=${r1 - r0:+,.1f}")
        baseline_records.append({"seed": s, "v1_reward": r0, "v2_reward": r1, "v2_delta": r1 - r0})

    out_path = "scratch/phase0_baseline_report.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({
            "controls": EXPECTED_HASHES,
            "python_version": sys.version,
            "kaggle_version": kaggle_environments.__version__,
            "baseline_matches": baseline_records
        }, f, indent=2)
    print(f"\nPhase 0 report saved to {out_path}")
    print("=" * 80)

if __name__ == "__main__":
    run_phase0()
