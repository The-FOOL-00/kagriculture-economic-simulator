import json
import glob
import pandas as pd
import datetime
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

files = sorted(glob.glob("replays/episode-*.json"))
rows = []

for f in files:
    with open(f, "r", encoding="utf-8") as fp:
        d = json.load(fp)
    
    eid = d.get("id")
    info = d.get("info", {})
    team_names = info.get("TeamNames", [])
    agents = info.get("Agents", [])
    ep_id_int = info.get("EpisodeId")
    
    user_idx = None
    if "Sundareswaran Rajaguru" in team_names:
        user_idx = team_names.index("Sundareswaran Rajaguru")
    elif len(team_names) >= 2:
        user_idx = 1 # default
        
    opp_name = team_names[1 - user_idx] if user_idx is not None and len(team_names) > (1 - user_idx) else "Unknown"
    
    rewards = d.get("rewards", [0, 0])
    user_reward = rewards[user_idx] if user_idx is not None and len(rewards) > user_idx else 0
    opp_reward = rewards[1 - user_idx] if user_idx is not None and len(rewards) > (1 - user_idx) else 0
    
    rows.append({
        "file": f,
        "episode_id": ep_id_int,
        "uuid": eid,
        "user_seat": user_idx,
        "user_name": team_names[user_idx] if user_idx is not None else "Unknown",
        "opp_name": opp_name,
        "user_reward": user_reward,
        "opp_reward": opp_reward,
        "won": 1 if user_reward > opp_reward else 0,
        "lost": 1 if user_reward < opp_reward else 0,
    })

df = pd.DataFrame(rows)
print(df.to_string())
df.to_csv("scratch/replays_27_complete_forensics.csv", index=False, encoding="utf-8")
print("\n=== SUMMARY RECONCILIATION ===")
print(f"Total files: {len(df)}")
print(f"Wins: {df['won'].sum()} ({df['won'].sum()/len(df)*100:.1f}%)")
print(f"Losses: {df['lost'].sum()} ({df['lost'].sum()/len(df)*100:.1f}%)")
print(f"Mean User Score: {df['user_reward'].mean():.1f}")
print(f"Mean Opponent Score: {df['opp_reward'].mean():.1f}")
