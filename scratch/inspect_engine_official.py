import kaggle_environments, os

p1 = os.path.join(os.path.dirname(kaggle_environments.__file__), 'envs', 'kaggriculture', 'kaggriculture.py')
print("Installed engine path:", p1)
with open(p1, 'r', encoding='utf-8') as f:
    lines = f.readlines()

print(f"Total lines: {len(lines)}")

keywords = ["def ", "class ", "HIRE", "BUY_ANIMAL", "PASTURE", "PICKUP", "PLACE", "market", "shed", "hands", "worker"]
for idx, line in enumerate(lines):
    stripped = line.strip()
    if any(stripped.startswith(f"def {kw}") for kw in ["hire", "buy", "step", "pickup", "place", "order", "market", "reset"]):
        print(f"Line {idx+1}: {stripped}")
    elif stripped.startswith("class "):
        print(f"Line {idx+1}: {stripped}")
