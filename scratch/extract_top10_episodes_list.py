import pandas as pd
import json
import glob
import os

df_agents = pd.read_csv("replays/raw/georgymamarin/agents.csv")

with open("scratch/top20_coverage_in_dataset.json", "r", encoding="utf-8") as f:
    coverage = json.load(f)

# Find which episodes exist locally in our repository
local_json_files = glob.glob("replays/**/*.json", recursive=True) + glob.glob("scratch/**/*.json", recursive=True) + glob.glob("*.json")
local_ep_ids = {}
for f in local_json_files:
    fname = os.path.basename(f)
    # Check if number in fname
    for part in fname.replace("-", "_").replace(".", "_").split("_"):
        if part.isdigit() and len(part) >= 7:
            local_ep_ids[int(part)] = f

print(f"Total local episode files mapped by ID: {len(local_ep_ids)}")

top_episodes_manifest = []

for item in coverage:
    team_id = item['team_id']
    team_name = item['team_name']
    rank = item['rank']
    
    matches = df_agents[df_agents['team_id'] == team_id]
    for idx, row in matches.iterrows():
        ep_id = int(row['episode_id'])
        sub_id = int(row['submission_id'])
        bank = int(row['final_bank'])
        rating = float(row['rating_after'])
        
        # Check opponent in that episode
        opp_row = df_agents[(df_agents['episode_id'] == ep_id) & (df_agents['team_id'] != team_id)]
        opp_team_id = int(opp_row['team_id'].iloc[0]) if len(opp_row) > 0 else None
        opp_bank = int(opp_row['final_bank'].iloc[0]) if len(opp_row) > 0 else None
        
        local_path = local_ep_ids.get(ep_id, None)
        
        top_episodes_manifest.append({
            "rank": rank,
            "team_name": team_name,
            "team_id": team_id,
            "episode_id": ep_id,
            "submission_id": sub_id,
            "final_bank": bank,
            "rating_after": rating,
            "opp_team_id": opp_team_id,
            "opp_bank": opp_bank,
            "has_local_replay": local_path is not None,
            "local_path": local_path
        })

df_top_episodes = pd.DataFrame(top_episodes_manifest)
print(f"Total top-team match entries in manifest: {len(df_top_episodes)}")
print(f"Top-team matches with local full replay files: {df_top_episodes['has_local_replay'].sum()}")

df_top_episodes.to_csv("scratch/all_top_team_episodes_manifest.csv", index=False)
