import requests
import json
import time
import os

sub_ids = [56146971, 56146947]
LIST_URL = "https://www.kaggle.com/api/i/competitions.EpisodeService/ListEpisodes"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Content-Type": "application/json",
    "Accept": "application/json"
}

session = requests.Session()
session.headers.update(headers)

all_episodes = {}

for sub_id in sub_ids:
    print(f"\nQuerying ListEpisodes for submission {sub_id}...")
    try:
        r = session.post(LIST_URL, json={"submissionId": sub_id}, timeout=30)
        print(f"Status: {r.status_code}, Length: {len(r.text)}")
        if r.status_code == 200:
            data = r.json()
            episodes = data.get("episodes", [])
            print(f"Total episodes for {sub_id}: {len(episodes)}")
            all_episodes[sub_id] = episodes
        else:
            print("Response:", r.text[:300])
    except Exception as e:
        print(f"Error querying {sub_id}: {e}")

output_path = "scratch/live_submissions_episodes_index.json"
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(all_episodes, f, indent=2)

print(f"\nSaved all episodes to {output_path}")
