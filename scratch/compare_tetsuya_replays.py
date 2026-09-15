import json

replays = [
    ("ep1", "external_repos/lixingtao123-Kaggriculture/opponents/top1_tetsuya/replays/episode-104024965-replay.json", 1),
    ("ep2", "external_repos/lixingtao123-Kaggriculture/opponents/top1_tetsuya/replays/episode-104058487-replay.json", 0),
    ("ep3", "external_repos/lixingtao123-Kaggriculture/opponents/top1_tetsuya/replays/episode-104060611-replay.json", 0),
]

for name, path, seat in replays:
    with open(path, "r") as f:
        d = json.load(f)
    print(f"=== {name} (Seat {seat}, Seed {d['info']['seed']}, Reward {d['rewards'][seat]}) ===")
    step1_market = d["steps"][1][seat].get("action", {}).get("market", [])
    print("  Step 1 market:", step1_market)
    step2_market = d["steps"][2][seat].get("action", {}).get("market", [])
    print("  Step 2 market:", step2_market)
    total_ferts = sum(1 for step in d["steps"] for h in step[seat].get("action", {}).get("hands", []) if h and h[0] == "FERTILIZE")
    print(f"  Total hand FERTILIZE actions: {total_ferts}")
