import pandas as pd
import glob
import os
import json

sub_id = 55893176

print(f"=== Searching for submission {sub_id} in georgymamarin dataset ===")

if os.path.exists("replays/raw/georgymamarin/agents.csv"):
    df_agents = pd.read_csv("replays/raw/georgymamarin/agents.csv")
    matches = df_agents[df_agents["submission_id"] == sub_id]
    print(f"Found in agents.csv: {len(matches)} rows")
    if len(matches) > 0:
        print(matches.head(10))
        
if os.path.exists("replays/raw/georgymamarin/episodes.csv"):
    df_ep = pd.read_csv("replays/raw/georgymamarin/episodes.csv")
    m0 = df_ep[df_ep["sub_0"] == sub_id]
    m1 = df_ep[df_ep["sub_1"] == sub_id]
    print(f"Found in episodes.csv: sub_0={len(m0)}, sub_1={len(m1)}, total={len(m0)+len(m1)}")
    if len(m0) + len(m1) > 0:
        comb = pd.concat([m0, m1])
        print(comb.head(10))

if os.path.exists("replays/raw/georgymamarin/per_submission_coverage.csv"):
    df_cov = pd.read_csv("replays/raw/georgymamarin/per_submission_coverage.csv")
    m_cov = df_cov[df_cov["submission_id"] == sub_id]
    print(f"Found in per_submission_coverage.csv:\n{m_cov}")

# Also check teams.csv
if os.path.exists("replays/raw/georgymamarin/teams.csv"):
    df_teams = pd.read_csv("replays/raw/georgymamarin/teams.csv")
    t_match = df_teams[df_teams["team_name"].str.contains("Eldritch|Sundar|thefool", case=False, na=False)]
    print(f"Found in teams.csv:\n{t_match}")
