import glob
import json
import os
import pandas as pd

sub_id = 55893176
team_id = 16657198

def search_episodes(directory):
    files = glob.glob(os.path.join(directory, "*.json"))
    print(f"Scanning {len(files)} files in {directory}...")
    
    matches = []
    for f in files:
        try:
            with open(f, "r", encoding="utf-8") as fp:
                data = json.load(fp)
                
            # Check agents field
            agents = data.get("agents", [])
            found = False
            user_seat = None
            opp_sub = None
            opp_team = None
            
            for ag in agents:
                if ag.get("submissionId") == sub_id or ag.get("teamId") == team_id:
                    found = True
                    user_seat = ag.get("index", 0)
                else:
                    opp_sub = ag.get("submissionId")
                    opp_team = ag.get("teamId")
                    
            # If not in agents, check steps or description
            if not found:
                desc = str(data.get("description", "")) + str(data.get("title", ""))
                if str(sub_id) in desc or str(team_id) in desc or "Sundareswaran" in desc:
                    found = True
                    
            if found:
                eid = data.get("id", os.path.splitext(os.path.basename(f))[0])
                rewards = data.get("rewards", [0, 0])
                statuses = data.get("statuses", ["", ""])
                steps = data.get("steps", [])
                
                # If user_seat not found from agents, try to determine
                if user_seat is None:
                    user_seat = 0
                    
                user_score = rewards[user_seat] if rewards and len(rewards) > user_seat else None
                opp_score = rewards[1 - user_seat] if rewards and len(rewards) > (1 - user_seat) else None
                
                matches.append({
                    "file": f,
                    "episode_id": eid,
                    "user_seat": user_seat,
                    "user_score": user_score,
                    "opp_score": opp_score,
                    "opp_sub": opp_sub,
                    "opp_team": opp_team,
                    "user_status": statuses[user_seat] if statuses and len(statuses) > user_seat else "",
                    "opp_status": statuses[1 - user_seat] if statuses and len(statuses) > (1 - user_seat) else "",
                    "steps": len(steps)
                })
        except Exception as e:
            print(f"Error parsing {f}: {e}")
            
    return matches

if __name__ == "__main__":
    all_matches = []
    for d in ["replays", "replays/raw/kaggle_daily_aug30", "replays/raw/kaggle_daily_aug31"]:
        if os.path.exists(d):
            m = search_episodes(d)
            print(f"Found {len(m)} matches in {d}")
            all_matches.extend(m)
            
    df = pd.DataFrame(all_matches)
    print(f"\nTotal matches found across all sources: {len(df)}")
    if len(df) > 0:
        df = df.drop_duplicates(subset=["episode_id"])
        print(f"Total unique episodes: {len(df)}")
        print(df[["episode_id", "user_seat", "user_score", "opp_score", "steps"]].to_string())
        df.to_csv("scratch/all_reconciled_apex_episodes.csv", index=False)
