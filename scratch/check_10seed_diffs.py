import json
import numpy as np

with open("scratch/50seed_hostile_audit_raw.json") as f:
    d = json.load(f)

seeds = [str(s) for s in range(1000, 1010)]
rews_a = [d["A_Baseline"][s]["reward"] for s in seeds]
rews_b = [d["B_Gated_M1"][s]["reward"] for s in seeds]
diffs = [b - a for a, b in zip(rews_a, rews_b)]

print("Seeds 1000-1009 Delta Rewards:")
for s, diff in zip(seeds, diffs):
    print(f"  Seed {s}: {diff:>+10.2f}")
print(f"Mean Delta Reward: {np.mean(diffs):>+10.2f}")
