import kaggle_environments.envs.kaggriculture.kaggriculture as kg

with open(kg.__file__, 'r', encoding='utf-8') as f:
    lines = f.readlines()

for idx in range(893, min(966, len(lines))):
    print(f"{idx+1}: {lines[idx]}", end="")
