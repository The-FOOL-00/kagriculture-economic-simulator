import json
import os
import glob
import pandas as pd
import numpy as np

def analyze_user_replays():
    files = glob.glob("replays/episode-*.json")
    print(f"Found {len(files)} user episode replay files.")
    
    records = []
    
    for fpath in sorted(files):
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            ep_id = data.get("id")
            num_ep_id = data.get("info", {}).get("EpisodeId")
            version = data.get("version")
            module_version = data.get("module_version")
            team_names = data.get("info", {}).get("TeamNames", ["Unknown", "Unknown"])
            seed = data.get("info", {}).get("seed")
            rewards = data.get("rewards", [0, 0])
            statuses = data.get("statuses", ["", ""])
            steps_count = len(data.get("steps", []))
            
            # Identify user index (Sundareswaran Rajaguru)
            user_idx = -1
            opp_idx = -1
            user_name = "Sundareswaran Rajaguru"
            
            for idx, name in enumerate(team_names):
                if user_name.lower() in name.lower():
                    user_idx = idx
                else:
                    opp_idx = idx
            
            if user_idx == -1:
                # If neither is explicit, maybe team 1
                user_idx = 1
                opp_idx = 0
            
            user_score = rewards[user_idx] if user_idx < len(rewards) else None
            opp_score = rewards[opp_idx] if opp_idx < len(rewards) else None
            opp_name = team_names[opp_idx] if opp_idx < len(team_names) else "Opponent"
            
            won = user_score > opp_score if (user_score is not None and opp_score is not None) else False
            draw = user_score == opp_score
            margin = (user_score - opp_score) if (user_score is not None and opp_score is not None) else 0
            
            # Analyze trajectories
            steps = data.get("steps", [])
            
            # Track progression at Day 0 (step 0-23), Day 1 (24), Day 2 (48), Day 3 (72), Day 5 (120), Day 10 (240), Day 20 (480), Day 30 (719)
            checkpoints = [24, 48, 72, 120, 240, 480, 719]
            user_cash_prog = {}
            opp_cash_prog = {}
            
            # Opening actions (Step 1)
            user_opening = steps[1][user_idx].get("action") if len(steps) > 1 else None
            opp_opening = steps[1][opp_idx].get("action") if len(steps) > 1 else None
            
            # Count livestock, crops, land, workers at end
            final_step = steps[-1] if len(steps) > 0 else None
            
            records.append({
                "file": os.path.basename(fpath),
                "ep_id": num_ep_id or ep_id,
                "module_version": module_version,
                "seed": seed,
                "user_seat": f"P{user_idx}",
                "opp_name": opp_name,
                "user_score": user_score,
                "opp_score": opp_score,
                "won": won,
                "draw": draw,
                "margin": margin,
                "user_opening": str(user_opening),
                "opp_opening": str(opp_opening),
                "steps": steps_count
            })
        except Exception as e:
            print(f"Error reading {fpath}: {e}")
            
    df = pd.DataFrame(records)
    print("\n=== USER LIVE REPLAYS SUMMARY ===")
    print(f"Total Matches: {len(df)}")
    print(f"Wins: {df['won'].sum()} | Losses: {(~df['won'] & ~df['draw']).sum()} | Draws: {df['draw'].sum()}")
    print(f"Win Rate: {df['won'].mean()*100:.1f}%")
    print(f"Average User Score: {df['user_score'].mean():.1f} | Average Opp Score: {df['opp_score'].mean():.1f}")
    print(f"Average Margin: {df['margin'].mean():.1f}")
    
    print("\n--- By Module/Engine Version ---")
    print(df.groupby("module_version")[["won", "margin", "user_score", "opp_score"]].agg(["count", "mean"]))
    
    print("\n--- By Player Seat (P0 vs P1) ---")
    print(df.groupby("user_seat")[["won", "margin", "user_score", "opp_score"]].agg(["count", "mean"]))
    
    print("\n--- Match Details Table ---")
    print(df[["file", "module_version", "user_seat", "opp_name", "user_score", "opp_score", "margin", "won"]].to_string())
    
    df.to_csv("scratch/user_live_matches.csv", index=False)
    with open("scratch/user_live_matches.json", "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2)

if __name__ == "__main__":
    analyze_user_replays()
