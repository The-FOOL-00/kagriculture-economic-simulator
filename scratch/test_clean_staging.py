# SPDX-License-Identifier: MIT
import tempfile
import os
import shutil
import subprocess
import sys

repo_root = os.path.abspath(".")
v35_src = os.path.join(repo_root, "candidates", "v35_a7_opening", "main.py")

with tempfile.TemporaryDirectory() as tmpdir:
    # Copy main.py alone into tmpdir
    staged_main = os.path.join(tmpdir, "main.py")
    shutil.copy2(v35_src, staged_main)
    
    code = """
import sys
import main
print('Imported main successfully')
"""
    p = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, cwd=tmpdir)
    print("STDOUT:", p.stdout)
    print("STDERR:", p.stderr)
