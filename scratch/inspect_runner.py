import os
import kaggle_environments

core_py = os.path.join(os.path.dirname(kaggle_environments.__file__), 'core.py')
with open(core_py, 'r', encoding='utf-8') as f:
    lines = f.readlines()

print("=== AGENT_RUNNER (700-760) ===")
for i in range(700, min(760, len(lines))):
    print(f"{i+1}: {lines[i].rstrip()}")
