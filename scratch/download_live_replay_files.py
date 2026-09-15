import json
import os
import requests
import time

manifest_path = "scratch/live_episodes_manifest.json"
manifest = json.load(open(manifest_path, encoding="utf-8"))

save_dir = "replays/live_tournament"
os.makedirs(save_dir, exist_ok=True)

all_episodes = []
for sid, eps in manifest.items():
    for ep in eps:
        ep_id = ep["id"]
        all_episodes.append((ep_id, sid))

print(f"Total live episodes to verify/download: {len(all_episodes)}")

downloaded = 0
skipped = 0
failed = 0

for ep_id, sid in all_episodes:
    out_file = os.path.join(save_dir, f"episode_{ep_id}.json")
    if os.path.exists(out_file) and os.path.getsize(out_file) > 1000:
        skipped += 1
        continue
        
    url = f"https://www.kaggleusercontent.com/episodes/{ep_id}.json"
    try:
        r = requests.get(url, timeout=20)
        if r.status_code == 200:
            with open(out_file, "wb") as f:
                f.write(r.content)
            downloaded += 1
            if downloaded % 10 == 0:
                print(f"  Downloaded {downloaded} episodes...")
        else:
            print(f"  Failed {ep_id}: HTTP {r.status_code}")
            failed += 1
    except Exception as e:
        print(f"  Error {ep_id}: {e}")
        failed += 1
    time.sleep(0.1)

print(f"\nFinished: Downloaded {downloaded}, Skipped {skipped}, Failed {failed}")
print(f"Total files in {save_dir}: {len(os.listdir(save_dir))}")
