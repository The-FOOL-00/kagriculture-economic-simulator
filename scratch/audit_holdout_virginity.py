import os
import subprocess
import re

BASE_DIR = r"c:\Users\Sundareswaran\Kagriculture"
holdout_seeds = list(range(214200, 214250))

print("=== VIRGIN HOLDOUT ISOLATION AUDIT (SEEDS 214200..214249) ===")

# 1. Check for any simulation execution in python files
print("\n--- 1. Checking for range overlaps in Python simulation scripts ---")
overlap_scripts = []
for root, dirs, files in os.walk(BASE_DIR):
    if any(x in root for x in [".git", "__pycache__", "external_repos"]):
        continue
    for f in files:
        if f.endswith(".py"):
            fp = os.path.join(root, f)
            with open(fp, "r", encoding="utf-8", errors="ignore") as fh:
                for lno, line in enumerate(fh, 1):
                    # Check for explicit holdout seed constants
                    for s in holdout_seeds:
                        if re.search(r"\b" + str(s) + r"\b", line):
                            # Is this a quarantine check (assert / if / comment / docstring)?
                            is_quarantine = any(k in line for k in ["assert", "raise", "VIOLATION", "holdout", "Holdout", "HOLDOUT", "PROHIBITED", "quarantine", "exclude", "EXPECTED", "range("])
                            rel = os.path.relpath(fp, BASE_DIR)
                            print(f"  Explicit seed mention: {rel}:{lno} -> {line.strip()[:80]} (quarantine={is_quarantine})")
                    # Check for range(start, stop)
                    for m in re.finditer(r'range\s*\(\s*(\d+)\s*,\s*(\d+)', line):
                        sr, er = int(m.group(1)), int(m.group(2))
                        if max(214200, sr) <= min(214249, er - 1):
                            rel = os.path.relpath(fp, BASE_DIR)
                            print(f"  Range execution overlap: {rel}:{lno} -> range({sr}, {er})")
                            overlap_scripts.append((rel, lno, sr, er))

print(f"Total range execution overlaps: {len(overlap_scripts)}")

# 2. Check for simulation result files (json/csv) containing holdout seeds
print("\n--- 2. Checking simulation result outputs (json/csv) ---")
result_files_with_holdout = []
for root, dirs, files in os.walk(BASE_DIR):
    if any(x in root for x in [".git", "__pycache__", "external_repos"]):
        continue
    for f in files:
        if f.endswith((".json", ".csv")):
            fp = os.path.join(root, f)
            rel = os.path.relpath(fp, BASE_DIR)
            # Skip replay files or public datasets
            with open(fp, "r", encoding="utf-8", errors="ignore") as fh:
                txt = fh.read()
            found = [s for s in holdout_seeds if str(s) in txt]
            if found:
                print(f"  File with holdout seed: {rel} ({len(found)} seeds found: {found[:5]}...)")
                result_files_with_holdout.append((rel, len(found)))

print(f"Total result files with holdout seeds: {len(result_files_with_holdout)}")
