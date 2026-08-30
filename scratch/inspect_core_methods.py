import os
import kaggle_environments

core_py = os.path.join(os.path.dirname(kaggle_environments.__file__), 'core.py')
with open(core_py, 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if 'def act(' in line or 'def step(' in line or 'def run(' in line or 'def __step(' in line or 'agent(' in line:
        print(f"{i+1}: {line.strip()}")
