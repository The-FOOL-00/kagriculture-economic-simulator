import os
import json

replays = []
for root, dirs, files in os.walk(r"external_repos\lixingtao123-Kaggriculture"):
    for f in files:
        if f.endswith("-replay.json"):
            replays.append(os.path.join(root, f))

print(f"Total replay files found: {len(replays)}")

unique_episodes = {}
player_counts = {}

for r in replays:
    fname = os.path.basename(r)
    ep_id = fname.split("-")[1]
    if ep_id in unique_episodes:
        continue
    unique_episodes[ep_id] = r
    
    # Read the first chunk of JSON to get player info without loading 30MB
    try:
        with open(r, "r", encoding="utf-8") as f:
            header = f.read(4096)
            # Find players or info
            # In Kaggle replays, info or configuration is near top
            # Or load just 'info' / 'configuration'
    except Exception as e:
        pass

print(f"Unique episode IDs: {len(unique_episodes)}")

# Let's check results/top1_tetsuya_replay_analysis.json, top3_islet_replay_analysis.json, top8_zhyphirus_replay_analysis.json
result_files = [
    r"external_repos\lixingtao123-Kaggriculture\results\top1_tetsuya_replay_analysis.json",
    r"external_repos\lixingtao123-Kaggriculture\results\top3_islet_replay_analysis.json",
    r"external_repos\lixingtao123-Kaggriculture\results\top8_zhyphirus_replay_analysis.json",
]

for rf in result_files:
    if os.path.exists(rf):
        with open(rf, "r", encoding="utf-8") as f:
            d = json.load(f)
            print(f"\nFile: {os.path.basename(rf)}")
            if isinstance(d, dict):
                print(f"  Keys: {list(d.keys())[:8]}")
                print(f"  Sample data: {str(d)[:200]}...")
            elif isinstance(d, list):
                print(f"  List length: {len(d)}")
                print(f"  Sample item: {d[0] if d else None}")
