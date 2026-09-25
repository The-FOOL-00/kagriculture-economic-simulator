# SPDX-License-Identifier: MIT
import tempfile
import os
import subprocess
import sys

repo_root = os.path.abspath(".")
v35_main_path = os.path.join(repo_root, "candidates", "v35_a7_opening", "main.py")

with tempfile.TemporaryDirectory() as tmpdir:
    code = f"""
import sys
sys.path.insert(0, r'{os.path.dirname(v35_main_path)}')
import main
print('Imported main successfully')
obs = {{'step': 0, 'player': 0, 'farms': [{{'money': 3000.0, 'farmer': [5, 5], 'hands': []}}], 'market': {{'prices': {{'WHEAT': 25.0}}}}}}
act = main.agent(obs)
print('Step 0 action:', act['market'])
"""
    p = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, cwd=tmpdir)
    print("STDOUT:", p.stdout)
    print("STDERR:", p.stderr)
