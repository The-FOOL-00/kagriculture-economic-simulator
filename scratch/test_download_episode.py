import requests
import json
import pandas as pd

df = pd.read_csv("scratch/all_top_team_episodes_manifest.csv")
print("Top 10 sample rows in manifest:")
print(df.head(10))

sample_ep_id = df.iloc[0]['episode_id']
print(f"\nTesting episode download for ep_id: {sample_ep_id}")

urls_to_test = [
    f"https://www.kaggle.com/api/v1/episodes/{sample_ep_id}",
    f"https://www.kaggle.com/episodes/{sample_ep_id}.json",
    f"https://www.kaggle.com/api/i/episodes.EpisodeService/ShowEpisode?episodeId={sample_ep_id}",
    f"https://www.kaggle.com/api/i/tournaments.TournamentService/GetEpisodeDetails?episodeId={sample_ep_id}"
]

headers = {"User-Agent": "Mozilla/5.0"}

for u in urls_to_test:
    try:
        r = requests.get(u, headers=headers, timeout=5)
        print(f"GET {u} -> Status: {r.status_code}, Length: {len(r.text)}")
        if r.status_code == 200:
            data = r.json()
            print("  Keys:", list(data.keys())[:10])
    except Exception as e:
        print(f"Error {u}: {e}")
