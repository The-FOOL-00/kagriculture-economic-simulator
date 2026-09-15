import os
import sys
import hashlib
import json
import subprocess
import glob
import re

BASE_DIR = r"c:\Users\Sundareswaran\Kagriculture"

def sha256_file(filepath):
    with open(filepath, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()

print("=== 1. HASH VERIFICATIONS ===")

# Protocol hash
proto_path = os.path.join(BASE_DIR, "DEVELOPMENT_EXPERIMENT_PROTOCOL_V1_1.md")
proto_sha = sha256_file(proto_path)
print(f"Protocol V1.1 path: {proto_path}")
print(f"Protocol V1.1 SHA256: {proto_sha}")
EXPECTED_PROTO_SHA = "735ad844b727a967058e4f817a72ae6bf3ea3f5a40182fa18f59f972da91f446"
assert proto_sha == EXPECTED_PROTO_SHA, f"Protocol hash mismatch: {proto_sha} != {EXPECTED_PROTO_SHA}"
print("Protocol V1.1 SHA256: MATCH (VERIFIED)")

# Treatment hash
treatment_path = os.path.join(BASE_DIR, "candidates", "closed_loop_architecture", "dev_002_hedged_portfolio.py")
treatment_sha = sha256_file(treatment_path)
print(f"Treatment path: {treatment_path}")
print(f"Treatment SHA256: {treatment_sha}")
EXPECTED_TREATMENT_SHA = "cdd19cc8d2b6a718ce6252223b9016ce76e5b08b88de10689ea5fce4ddb8f907"
assert treatment_sha == EXPECTED_TREATMENT_SHA, f"Treatment hash mismatch: {treatment_sha} != {EXPECTED_TREATMENT_SHA}"
print("Treatment SHA256: MATCH (VERIFIED)")

# Frozen submissions
res_path = os.path.join(BASE_DIR, "candidates", "compiled_v54_plus_residual.py")
res_sha = sha256_file(res_path)
EXPECTED_RES_SHA = "18402ec6fa3709b9b5ef90dd9c8d7b9c0e44aea55ab163e44a80a4adc0cb7eeb"
assert res_sha == EXPECTED_RES_SHA, f"Residual hash mismatch: {res_sha} != {EXPECTED_RES_SHA}"
print(f"Residual submission SHA256: {res_sha} MATCH (VERIFIED)")

shop_path = os.path.join(BASE_DIR, "candidates", "compiled_v54_plus_shop.py")
shop_sha = sha256_file(shop_path)
EXPECTED_SHOP_SHA = "f651ccd220e701968bc33579812d8917da63f5b0582f2fd0d363fa6a16ffd8b8"
assert shop_sha == EXPECTED_SHOP_SHA, f"Shop submission SHA256: {shop_sha} MATCH (VERIFIED)"
print(f"Shop submission SHA256: {shop_sha} MATCH (VERIFIED)")

print("\n=== 2. GIT STATE ===")
git_status = subprocess.check_output(["git", "status", "--short"], cwd=BASE_DIR, text=True)
git_head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=BASE_DIR, text=True).strip()
print(f"Current git commit: {git_head}")

# Check if any tracked files modified
modified_tracked = [line for line in git_status.splitlines() if not line.startswith("??")]
print(f"Modified tracked files count: {len(modified_tracked)}")
for line in modified_tracked:
    print(f"  {line}")

print("\n=== 3. AST ZERO-LEAKAGE AUDIT ===")
sys.path.insert(0, os.path.join(BASE_DIR, "scratch"))
from verify_agent_zero_leakage import audit_agent_ast
ast_violations = audit_agent_ast(treatment_path)
print(f"AST audit violations count: {len(ast_violations)}")
assert len(ast_violations) == 0, f"AST violations found: {ast_violations}"
print("AST Zero-Leakage Audit: PASSED (CLEAN)")

print("\n=== 4. QUALIFICATION SEEDS CONTAMINATION AUDIT (50050-50099) ===")
qual_seeds = set(range(50050, 50100))

# Search across repo text files for mentions of 50050..50099
qual_references = {}
for root, dirs, files in os.walk(BASE_DIR):
    if ".git" in root or "external_repos" in root or "__pycache__" in root:
        continue
    for file in files:
        filepath = os.path.join(root, file)
        # only check text files or json/csv/py/md
        ext = os.path.splitext(file)[1].lower()
        if ext not in [".py", ".md", ".json", ".csv", ".txt"]:
            continue
        try:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            # check for each seed
            for s in qual_seeds:
                s_str = str(s)
                if s_str in content:
                    rel_path = os.path.relpath(filepath, BASE_DIR)
                    if rel_path not in qual_references:
                        qual_references[rel_path] = set()
                    qual_references[rel_path].add(s)
        except Exception as e:
            pass

print(f"Found {len(qual_references)} files referencing qualification seed numbers:")
for rel_path, seeds in sorted(qual_references.items()):
    sample = sorted(list(seeds))[:5]
    print(f"  {rel_path}: {len(seeds)} seeds found (e.g. {sample}...)")

print("\n=== 5. VIRGIN HOLDOUT AUDIT (214200-214249) ===")
holdout_seeds = set(range(214200, 214250))
holdout_references = {}
for root, dirs, files in os.walk(BASE_DIR):
    if ".git" in root or "external_repos" in root or "__pycache__" in root:
        continue
    for file in files:
        filepath = os.path.join(root, file)
        ext = os.path.splitext(file)[1].lower()
        if ext not in [".py", ".md", ".json", ".csv", ".txt"]:
            continue
        try:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            for s in holdout_seeds:
                s_str = str(s)
                if s_str in content:
                    rel_path = os.path.relpath(filepath, BASE_DIR)
                    if rel_path not in holdout_references:
                        holdout_references[rel_path] = set()
                    holdout_references[rel_path].add(s)
        except Exception as e:
            pass

print(f"Found {len(holdout_references)} files referencing holdout seed numbers:")
for rel_path, seeds in sorted(holdout_references.items()):
    sample = sorted(list(seeds))[:5]
    print(f"  {rel_path}: {len(seeds)} seeds found (e.g. {sample}...)")
