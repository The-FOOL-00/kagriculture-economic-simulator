import requests
import json
import time
import os
import glob

sub_id = 55893176
LIST_URL = "https://www.kaggle.com/api/i/competitions.EpisodeService/ListEpisodes"
REPLAY_URL = "https://www.kaggleusercontent.com/episodes/{id}.json"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Content-Type": "application/json",
    "Accept": "application/json"
}

session = requests.Session()
session.headers.update(headers)

print(f"Calling {LIST_URL} for submission {sub_id}...")
r = session.post(LIST_URL, json={"submissionId": sub_id}, timeout=30)
print(f"Status: {r.status_code}, Length: {len(r.text)}")

if r.status_code != 200:
    print("Response text:", r.text[:500])
    exit(1)

data = r.json()
episodes = data.get("episodes", [])
print(f"Total episodes returned for submission {sub_id}: {len(episodes)}")

with open("scratch/apex_v4_raw_episodes_list.json", "w", encoding="utf-8") as f:
    json.dump(episodes, f, indent=2)

print("Saved raw episode list to scratch/apex_v4_raw_episodes_list.json")
