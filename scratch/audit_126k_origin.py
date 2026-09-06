import os
import json
import glob

print("=== SEARCHING FOR 126k AND 81.4% IN JSON AND REPORT DATA ===")
for root, dirs, files in os.walk("."):
    if ".git" in root or "__pycache__" in root:
        continue
    for f in files:
        if f.endswith(".json") or f.endswith(".csv"):
            p = os.path.join(root, f)
            try:
                with open(p, "r", encoding="utf-8", errors="ignore") as file:
                    content = file.read()
                    if "126840" in content or "126,840" in content or "81.4%" in content:
                        print(f"Found in {p}")
            except Exception as e:
                pass
