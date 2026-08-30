import os, difflib, json
import kaggle_environments

installed_dir = os.path.join(os.path.dirname(kaggle_environments.__file__), 'envs', 'kaggriculture')
backup_dir = r"c:\Users\Sundareswaran\Kagriculture\env_backup_1_30_1"

inst_json = os.path.join(installed_dir, 'kaggriculture.json')
back_json = os.path.join(backup_dir, 'kaggriculture.json')

with open(inst_json, 'r') as f:
    ij = json.load(f)
with open(back_json, 'r') as f:
    bj = json.load(f)

print("=== CONFIGURATION DIFF ===")
for k in set(ij.get("configuration", {})).union(bj.get("configuration", {})):
    iv = ij.get("configuration", {}).get(k)
    bv = bj.get("configuration", {}).get(k)
    if iv != bv:
        print(f"Config {k}: 1.30.1={bv} vs 1.32.7={iv}")

print("\n=== SPECIFICATION DIFF ===")
for k in set(ij).union(bj):
    if k != "configuration":
        if ij.get(k) != bj.get(k):
            print(f"Top-level {k} differs")
