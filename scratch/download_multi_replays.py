import os
import sys
import json
import kaggle
import glob

sys.stdout.reconfigure(encoding='utf-8')
kaggle.api.authenticate()

os.makedirs("scratch/replays", exist_ok=True)

targets = [
    ("MtN", "scratch/episodes_top_55947871.json", 3),
    ("Crop_Dusta", "scratch/episodes_top_55929317.json", 3),
    ("Yuan800", "scratch/episodes_top_55959086.json", 3),
    ("Whyme_Labs", "scratch/episodes_top_55957002.json", 3),
    ("3JungHoon", "scratch/episodes_top_55944801.json", 3),
    ("Aethel_V2", "scratch/episodes_55958978.json", 5),
]

for name, fpath, count in targets:
    if not os.path.exists(fpath):
        print(f"File not found: {fpath}")
        continue
    with open(fpath, "r", encoding="utf-8") as f:
        try:
            eps = json.load(f)
        except Exception as e:
            print(f"Error loading {fpath}: {e}")
            continue
            
    print(f"\n--- Downloading up to {count} replays for {name} ---")
    downloaded = 0
    for ep in eps:
        if downloaded >= count:
            break
        ep_id = ep.get("id")
        if not ep_id:
            continue
        dest_path = f"scratch/replays/{name}_{ep_id}.json"
        if os.path.exists(dest_path) and os.path.getsize(dest_path) > 100000:
            print(f"Already exists: {dest_path}")
            downloaded += 1
            continue
            
        print(f"Downloading {name} Episode {ep_id}...")
        try:
            kaggle.api.competition_episode_replay(ep_id, path="scratch/replays")
            # Check possible filenames created by kaggle CLI
            candidates = [
                f"scratch/replays/episode-{ep_id}-replay.json",
                f"scratch/replays/{ep_id}.json",
                f"scratch/replays/episode-{ep_id}.json"
            ]
            found = False
            for c in candidates:
                if os.path.exists(c) and os.path.getsize(c) > 1000:
                    os.replace(c, dest_path)
                    print(f"Saved: {dest_path} ({os.path.getsize(dest_path):,} bytes)")
                    found = True
                    downloaded += 1
                    break
            if not found:
                print(f"Could not find downloaded replay for {ep_id}")
        except Exception as e:
            print(f"Error downloading {ep_id}: {e}")

print("\nReplay fetch complete.")
