import os
import kaggle_environments

core_py = os.path.join(os.path.dirname(kaggle_environments.__file__), 'core.py')
with open(core_py, 'r', encoding='utf-8') as f:
    lines = f.readlines()

print("=== ACT_AGENT (170-200) ===")
for i in range(169, min(200, len(lines))):
    print(f"{i+1}: {lines[i].rstrip()}")

print("\n=== STEP (255-305) ===")
for i in range(255, min(305, len(lines))):
    print(f"{i+1}: {lines[i].rstrip()}")

print("\n=== RUN (306-335) ===")
for i in range(306, min(335, len(lines))):
    print(f"{i+1}: {lines[i].rstrip()}")
