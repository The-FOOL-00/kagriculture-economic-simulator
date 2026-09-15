import os
import json
import re

BASE_DIR = r"c:\Users\Sundareswaran\Kagriculture"
qual_seeds = set(range(50050, 50100))

print("=== DEEP INVESTIGATION OF 50050-50099 REFERENCES ===")

# 1. Check EXP-DEV-001 and EXP-DEV-002
print("\n--- Checking EXP-DEV-001 and EXP-DEV-002 directories ---")
for exp in ["EXP-DEV-001", "EXP-DEV-002"]:
    exp_dir = os.path.join(BASE_DIR, "experiments", exp)
    for f in os.listdir(exp_dir):
        fp = os.path.join(exp_dir, f)
        if os.path.isfile(fp):
            with open(fp, "r", encoding="utf-8", errors="ignore") as file:
                content = file.read()
            found = [s for s in qual_seeds if str(s) in content]
            if found:
                print(f"  [{exp}] {f}: {len(found)} seeds found: {found[:5]}...")

# 2. Check candidate code
print("\n--- Checking candidate code ---")
cand_dir = os.path.join(BASE_DIR, "candidates")
for root, _, files in os.walk(cand_dir):
    for f in files:
        fp = os.path.join(root, f)
        with open(fp, "r", encoding="utf-8", errors="ignore") as file:
            content = file.read()
        found = [s for s in qual_seeds if str(s) in content]
        if found:
            print(f"  [candidate] {f}: {len(found)} seeds found: {found[:5]}...")

# 3. Check v2_dmitrii_margin_scan.json
scan_fp = os.path.join(BASE_DIR, "scratch", "v2_dmitrii_margin_scan.json")
if os.path.exists(scan_fp):
    with open(scan_fp, "r", encoding="utf-8") as file:
        data = json.load(file)
    print(f"\n--- Checking {scan_fp} ---")
    print(f"Type: {type(data)}, length/keys: {len(data) if isinstance(data, list) else list(data.keys())[:5]}")
    if isinstance(data, list) and len(data) > 0:
        print(f"Sample item 0: {data[0]}")
    elif isinstance(data, dict):
        sample_k = list(data.keys())[0]
        print(f"Sample key {sample_k}: {data[sample_k]}")

# 4. Check whether dev_002 was EVER executed on any seed in 50050-50099
print("\n--- Checking if dev_002 was ever executed on 50050-50099 ---")
dev002_executions = []
for root, _, files in os.walk(BASE_DIR):
    if ".git" in root or "external_repos" in root or "__pycache__" in root:
        continue
    for f in files:
        if f.endswith((".json", ".csv", ".txt", ".log")):
            fp = os.path.join(root, f)
            try:
                with open(fp, "r", encoding="utf-8", errors="ignore") as file:
                    text = file.read()
                if "dev_002" in text or "Dev002" in text or "hedged_portfolio" in text:
                    for s in qual_seeds:
                        if str(s) in text:
                            dev002_executions.append((os.path.relpath(fp, BASE_DIR), s))
            except Exception:
                pass

print(f"Found {len(dev002_executions)} occurrences of dev_002 + qual_seed:")
for fp, s in dev002_executions[:20]:
    print(f"  {fp}: seed {s}")
