import json

with open("scratch/replays/Crop_Dusta_104824599.json", "r", encoding="utf-8") as f:
    data = json.load(f)

print("Keys in replay:", list(data.keys()))
steps = data.get("steps")
print("Total steps:", len(steps))

for s_idx in [0, 1, 2, 24, 122, 198, 200, 264, 719]:
    step = steps[s_idx]
    print(f"\n--- STEP {s_idx} ---")
    for p_idx in [0, 1]:
        p = step[p_idx]
        action = p.get("action")
        reward = p.get("reward")
        obs_keys = list(p.get("observation", {}).keys()) if isinstance(p.get("observation"), dict) else type(p.get("observation"))
        print(f"P{p_idx} reward: {reward} | action: {str(action)[:120]}... | obs_keys: {obs_keys}")
