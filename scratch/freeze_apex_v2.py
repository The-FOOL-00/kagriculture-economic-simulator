import os
import sys
import hashlib
import subprocess

project_root = r"c:\Users\Sundareswaran\Kagriculture"
src_file = os.path.join(project_root, "candidates", "slot5_apex_synthesis_v2.py")
frozen_file = os.path.join(project_root, "agents", "apex_v2_frozen.py")

with open(src_file, "r", encoding="utf-8") as f:
    code = f.read()

with open(frozen_file, "w", encoding="utf-8") as f:
    f.write(code)

def sha256_file(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()

src_hash = sha256_file(src_file)
frozen_hash = sha256_file(frozen_file)
main_hash = sha256_file(os.path.join(project_root, "main.py"))

try:
    git_commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=project_root).decode().strip()
except Exception as e:
    git_commit = "N/A"

import kaggle_environments
env_ver = getattr(kaggle_environments, "__version__", "unknown")

print("=" * 80)
print("PART 1: APEX_V2_FROZEN ARTIFACT CREATED")
print("=" * 80)
print(f"Frozen File:        {frozen_file}")
print(f"Candidate Hash:     {src_hash}")
print(f"Frozen Hash:        {frozen_hash}")
print(f"Main Hash:          {main_hash}")
print(f"Hashes Match:       {src_hash == frozen_hash == main_hash}")
print(f"Git Commit:         {git_commit}")
print(f"Kaggle Env Version: {env_ver}")
print("Strategy Parameters:")
print("  - Target Cows: 8")
print("  - Target Sheep: 4")
print("  - Target Geese: 0")
print("  - Target Day-0 Melons: 15")
print("  - Cycle-2 Melons: 8 (Days 10-13)")
print("  - Sell Batch Size: 24 (Step % 4 == 0)")
print("  - Feed Buffer Days: 2 (24 wheat target)")
print("  - Emergency Liquidity: Enabled")
print("  - Care Animals: Enabled")
print("=" * 80)
