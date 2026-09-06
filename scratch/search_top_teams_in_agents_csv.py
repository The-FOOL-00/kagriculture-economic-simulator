import pandas as pd
import json

df_agents = pd.read_csv("replays/raw/georgymamarin/agents.csv")

with open("scratch/top50_leaderboard_snapshot.json", "r", encoding="utf-8") as f:
    top50 = json.load(f)

print(f"Total records in agents.csv: {len(df_agents)}")
print("Searching for Top 20 teams in historical/daily match records...")

top_team_coverage = []

for t in top50[:20]:
    team_id = t['TeamId']
    team_name = t['TeamName'].encode('ascii', 'replace').decode('ascii')
    score = t['Score']
    rank = t['Rank']
    
    matches = df_agents[df_agents['team_id'] == team_id]
    num_matches = len(matches)
    
    if num_matches > 0:
        subs = matches['submission_id'].unique().tolist()
        mean_bank = round(float(matches['final_bank'].mean()), 1)
        max_bank = int(matches['final_bank'].max())
        min_bank = int(matches['final_bank'].min())
        latest_rating = round(float(matches['rating_after'].iloc[-1]), 1)
        episodes = matches['episode_id'].tolist()
    else:
        subs = []
        mean_bank = 0
        max_bank = 0
        min_bank = 0
        latest_rating = 0
        episodes = []
        
    top_team_coverage.append({
        "rank": rank,
        "team_id": team_id,
        "team_name": team_name,
        "leaderboard_score": score,
        "dataset_matches": num_matches,
        "submissions": subs,
        "mean_bank": mean_bank,
        "max_bank": max_bank,
        "min_bank": min_bank,
        "latest_rating_in_ds": latest_rating,
        "sample_episodes": episodes[:5]
    })
    
    print(f"Rank {rank:2d} | {team_name[:25]:<25} (TeamId: {team_id}) | In Dataset: {num_matches:4d} matches | Mean Bank: ${mean_bank:8.1f} | Max: ${max_bank:7d} | Subs: {subs}")

with open("scratch/top20_coverage_in_dataset.json", "w", encoding="utf-8") as f:
    json.dump(top_team_coverage, f, indent=2)
