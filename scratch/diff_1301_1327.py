import os, difflib, json
import kaggle_environments

installed_dir = os.path.join(os.path.dirname(kaggle_environments.__file__), 'envs', 'kaggriculture')
backup_dir = r"c:\Users\Sundareswaran\Kagriculture\env_backup_1_30_1"

installed_py = os.path.join(installed_dir, 'kaggriculture.py')
backup_py = os.path.join(backup_dir, 'kaggriculture.py')

with open(installed_py, 'r', encoding='utf-8') as f:
    inst_lines = f.readlines()
with open(backup_py, 'r', encoding='utf-8') as f:
    back_lines = f.readlines()

diff = list(difflib.unified_diff(back_lines, inst_lines, fromfile='1.30.1', tofile='1.32.7'))
print(f"Total diff lines: {len(diff)}")

print("\n=== UNIFIED DIFF (1.30.1 -> 1.32.7) ===")
for line in diff:
    if line.startswith(('---', '+++', '@@', '+', '-')):
        print(line.rstrip())
