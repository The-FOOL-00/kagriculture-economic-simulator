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

print(f"Total live episodes: {len(all_episodes)}")

downloaded = 0
skipped = 0
failed = 0

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
})

# Let's download a sample of 25 episodes (prioritizing major wins and major losses)
# Sort episodes: biggest losses and biggest wins
sorted_eps = []
for ep_id, sid in all_episodes:
    # find ep in manifest
    ep_obj = next((e for e in manifest[sid] if e["id"] == ep_id), None)
    if not ep_obj: continue
    us = next((a for a in ep_obj["agents"] if a.get("submissionId") == int(sid)), None)
    them = next((a for a in ep_obj["agents"] if a.get("submissionId") != int(sid)), None)
    if us and them:
        margin = (us.get("reward") or 0) - (them.get("reward") or 0)
        sorted_eps.append((abs(margin), ep_id, sid, margin))

sorted_eps.sort(reverse=True)

for _, ep_id, sid, margin in sorted_eps[:40]:
    out_file = os.path.join(save_dir, f"episode_{ep_id}.json")
    if os.path.exists(out_file) and os.path.getsize(out_file) > 1000:
        skipped += 1
        continue
        
    url = f"https://www.kaggleusercontent.com/episodes/{ep_id}.json"
    success = False
    for attempt in range(3):
        try:
            r = session.get(url, timeout=15)
            if r.status_code == 200:
                with open(out_file, "wb") as f:
                    f.write(r.content)
                downloaded += 1
                success = True
                print(f"  Downloaded Ep {ep_id} (Margin ${margin:+d})")
                break
            time.sleep(1)
        except Exception as e:
            time.sleep(1)
            
    if not success:
        failed += 1

print(f"Finished batch: Downloaded {downloaded}, Skipped {skipped}, Failed {failed}")
print(f"Total available in {save_dir}: {len(os.listdir(save_dir))}")
