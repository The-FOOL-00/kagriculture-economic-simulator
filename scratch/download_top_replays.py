import os
import sys
import json
import kaggle
import glob

sys.stdout.reconfigure(encoding='utf-8')
kaggle.api.authenticate()

ep_files = glob.glob("scratch/episodes_top_*.json")
print(f"Found top episode files: {ep_files}")

for fpath in ep_files:
    with open(fpath, "r", encoding="utf-8") as f:
        eps = json.load(f)
    if not eps:
        continue
    # Pick the most recent completed episode
    top_ep = eps[0]
    ep_id = top_ep.get('id')
    print(f"\nProcessing {fpath} -> Episode {ep_id}")
    dest_path = f"scratch/replays/top_{os.path.basename(fpath).replace('.json', '')}_{ep_id}.json"
    if os.path.exists(dest_path) and os.path.getsize(dest_path) > 100000:
        print(f"Already exists: {dest_path}")
        continue
    print(f"Downloading episode {ep_id} to scratch/replays...")
    try:
        kaggle.api.competition_episode_replay(ep_id, path="scratch/replays")
        def_name = f"scratch/replays/episode-{ep_id}-replay.json"
        if os.path.exists(def_name):
            os.replace(def_name, dest_path)
            print(f"Successfully saved {dest_path} ({os.path.getsize(dest_path):,} bytes)")
        else:
            print(f"Default file {def_name} not found")
    except Exception as e:
        print(f"Error downloading {ep_id}: {e}")

