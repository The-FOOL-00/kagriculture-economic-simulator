import json
from collections import Counter

replay_path = "external_repos/lixingtao123-Kaggriculture/opponents/top1_tetsuya/replays/episode-104060611-replay.json"
with open(replay_path, "r") as f:
    d = json.load(f)

# Analyze actions by hand index across the game
hand_action_counts = {}
for s, step in enumerate(d["steps"]):
    a0 = step[0].get("action") or {}
    h_acts = a0.get("hands", [])
    for idx, act in enumerate(h_acts):
        if idx not in hand_action_counts:
            hand_action_counts[idx] = Counter()
        act_str = act[0] if act else "NONE"
        if len(act) > 1:
            act_str += f":{act[1]}"
        hand_action_counts[idx][act_str] += 1

print(f"Total hands ever active: {len(hand_action_counts)}")
for idx in sorted(hand_action_counts.keys()):
    counts = hand_action_counts[idx]
    top_acts = counts.most_common(5)
    top_str = ", ".join(f"{k}: {v}" for k, v in top_acts)
    total = sum(counts.values())
    print(f"Hand {idx:2d} ({total:3d} turns) -> {top_str}")
