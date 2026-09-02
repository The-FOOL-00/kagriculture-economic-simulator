import os
import sys
import json
import kaggle
from datetime import datetime

kaggle.api.authenticate()
now_utc = datetime.utcnow().isoformat() + "Z"
print(f"Retrieval timestamp: {now_utc}")

os.makedirs("scratch", exist_ok=True)

# 1. Leaderboard
print("\n--- Fetching Leaderboard ---")
try:
    lb = kaggle.api.competition_leaderboard_view('kaggriculture')
    lb_list = []
    for row in lb:
        if hasattr(row, 'to_dict'):
            lb_list.append(row.to_dict())
        elif hasattr(row, '__dict__'):
            lb_list.append(row.__dict__)
        else:
            lb_list.append(str(row))
    with open("scratch/leaderboard.json", "w") as f:
        json.dump(lb_list, f, indent=2, default=str)
    print(f"Saved {len(lb_list)} leaderboard entries to scratch/leaderboard.json")
    # Print top 20
    print("\nTop 20 on Leaderboard:")
    for i, r in enumerate(lb_list[:20]):
        print(f"#{i+1}: {r.get('teamName', r.get('team_name', r))} | Score: {r.get('score', r.get('publicScore', 'N/A'))}")
except Exception as e:
    print(f"Error fetching leaderboard: {e}")

# 2. Submissions
print("\n--- Fetching Submissions ---")
try:
    subs = kaggle.api.competition_submissions('kaggriculture')
    sub_list = []
    for s in subs:
        if hasattr(s, 'to_dict'):
            sub_list.append(s.to_dict())
        elif hasattr(s, '__dict__'):
            sub_list.append(s.__dict__)
        else:
            sub_list.append(str(s))
    with open("scratch/submissions.json", "w") as f:
        json.dump(sub_list, f, indent=2, default=str)
    print(f"Saved {len(sub_list)} submissions to scratch/submissions.json")
    for s in sub_list[:5]:
        print(f"Ref: {s.get('ref')}, Name: {s.get('fileName')}, Date: {s.get('date')}, Status: {s.get('status')}, Score: {s.get('publicScore')}")
except Exception as e:
    print(f"Error fetching submissions: {e}")

# 3. Episodes for Slot 1 and Slot 2
for name, sub_id in [("Slot 1 (Aethel-Prime V1)", 55944418), ("Slot 2 (Aethel-Refined V2)", 55958978)]:
    print(f"\n--- Fetching Episodes for {name} [Ref: {sub_id}] ---")
    try:
        eps = kaggle.api.competition_list_episodes(sub_id)
        eps_list = []
        if hasattr(eps, 'episodes'):
            raw_eps = eps.episodes
        elif isinstance(eps, (list, tuple)):
            raw_eps = eps
        else:
            raw_eps = [eps]
            
        for ep in raw_eps:
            if hasattr(ep, 'to_dict'):
                eps_list.append(ep.to_dict())
            elif hasattr(ep, '__dict__'):
                eps_list.append(ep.__dict__)
            else:
                eps_list.append(str(ep))
                
        out_file = f"scratch/episodes_{sub_id}.json"
        with open(out_file, "w") as f:
            json.dump(eps_list, f, indent=2, default=str)
        print(f"Saved {len(eps_list)} episodes to {out_file}")
    except Exception as e:
        print(f"Error fetching episodes for {sub_id}: {e}")
