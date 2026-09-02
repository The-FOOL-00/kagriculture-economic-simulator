import os
import sys
import json
import kaggle
import pandas as pd
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')
kaggle.api.authenticate()

os.makedirs("scratch/replays", exist_ok=True)

# 1. Identify key episodes from V2 to download
v2_df = pd.read_csv("scratch/analyzed_episodes_55958978.csv")
print(f"Total V2 episodes: {len(v2_df)}")

# Find losses and notable wins
v2_losses = v2_df[v2_df['win'] == 0.0]
v2_wins = v2_df[v2_df['win'] == 1.0]

print("\nV2 Top Losses (by negative margin):")
top_losses = v2_losses.sort_values(by='margin').head(8)
print(top_losses[['ep_id', 'opp_team_name', 'opp_rank', 'opp_score', 'our_reward', 'opp_reward', 'margin']].to_string(index=False))

# 2. Get top teams submission episodes
top_subs = {
    "MtN (Rank 1)": 55947871,
    "Crop Dusta (Rank 2)": 55929317,
    "Yuan800 (Rank 3)": 55959086,
    "3정훈 (Rank 4)": 55944801,
    "Whyme Labs (Rank 5)": 55957002,
}

top_episodes_map = {}
for name, sub_id in top_subs.items():
    print(f"\nFetching episodes for {name} (Sub ID: {sub_id})...")
    try:
        eps = kaggle.api.competition_list_episodes(sub_id)
        eps_list = []
        raw_eps = eps.episodes if hasattr(eps, 'episodes') else (eps if isinstance(eps, (list, tuple)) else [eps])
        for ep in raw_eps:
            if hasattr(ep, 'to_dict'):
                eps_list.append(ep.to_dict())
            elif hasattr(ep, '__dict__'):
                eps_list.append(ep.__dict__)
            else:
                eps_list.append(str(ep))
        top_episodes_map[name] = eps_list
        print(f"Found {len(eps_list)} episodes for {name}")
        with open(f"scratch/episodes_top_{sub_id}.json", "w", encoding="utf-8") as f:
            json.dump(eps_list, f, indent=2, default=str)
    except Exception as e:
        print(f"Error fetching episodes for {name}: {e}")

# 3. Select a curated list of episodes to download replays for:
# - 5 V2 losses (KawattaTaido, GAYATHRI SALINI, Yuyajk, qihuaz, Emre Kurubaş)
# - 3 V2 wins (Chaitanya Sonaje, dk07dk, Wei_Chance)
# - 2 MtN episodes
# - 2 Crop Dusta episodes
# - 2 Yuan800 episodes
# - 2 3정훈 episodes
# - 2 Whyme Labs episodes

episodes_to_download = []

for _, row in top_losses.head(5).iterrows():
    episodes_to_download.append((row['ep_id'], f"V2_Loss_vs_{row['opp_team_name']}"))

for _, row in v2_wins.sort_values(by='margin', ascending=False).head(3).iterrows():
    episodes_to_download.append((row['ep_id'], f"V2_Win_vs_{row['opp_team_name']}"))

for name, eps_list in top_episodes_map.items():
    clean_name = name.split()[0]
    for ep in eps_list[:2]:
        ep_id = ep.get('id')
        if ep_id:
            episodes_to_download.append((ep_id, f"Top_{clean_name}_{ep_id}"))

print(f"\nTotal curated replays to download: {len(episodes_to_download)}")

for ep_id, tag in episodes_to_download:
    dest_path = f"scratch/replays/{tag}_{ep_id}.json"
    if os.path.exists(dest_path) and os.path.getsize(dest_path) > 1000:
        print(f"Already downloaded: {tag} ({ep_id})")
        continue
    print(f"Downloading replay {ep_id} ({tag})...")
    try:
        kaggle.api.competition_episode_replay(ep_id, path="scratch/replays")
        # kaggle saves as episode-{ep_id}-replay.json in scratch/replays
        def_name = f"scratch/replays/episode-{ep_id}-replay.json"
        if os.path.exists(def_name):
            os.replace(def_name, dest_path)
            print(f"Saved to {dest_path} (Size: {os.path.getsize(dest_path):,} bytes)")
        else:
            print(f"Warning: default file {def_name} not found")
    except Exception as e:
        print(f"Error downloading replay {ep_id}: {e}")

