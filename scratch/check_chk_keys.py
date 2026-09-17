import json

with open("experiments/EXP-AEC-001/CHECKPOINT.json", "r") as f:
    chk = json.load(f)

seed_0 = chk["completed_seeds"]["340000"]
print("Keys of seed in CHECKPOINT.json:", seed_0.keys())
