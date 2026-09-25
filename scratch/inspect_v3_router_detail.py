"""
Inspect V3 routes details and router
"""
import tarfile, os, ast

with tarfile.open("submission_Vj_kc_v3.tar.gz", "r:gz") as tar:
    m = tar.extractfile("main.py")
    src = m.read().decode("utf-8")

# Let's inspect where router is defined and routes keys
import re
lines = src.splitlines()
for i, line in enumerate(lines):
    if "def router(" in line or "class Router" in line or "router =" in line or "routes =" in line:
        print(f"Line {i}: {line[:120]}")
        for j in range(max(0, i-5), min(len(lines), i+25)):
            print(f"  {j:3d}: {lines[j][:120]}")
        print("="*60)
