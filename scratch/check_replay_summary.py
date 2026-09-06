import json
import os

if os.path.exists("scratch/all_parsed_replays_summary.json"):
    with open("scratch/all_parsed_replays_summary.json", "r", encoding="utf-8") as f:
        replays = json.load(f)
    print(f"Total replays parsed in summary: {len(replays)}")
    
    # Check teams
    teams = {}
    for r in replays:
        for t in r.get("team_names", []):
            teams[t] = teams.get(t, 0) + 1
            
    print("\nTop teams appearing in replays:")
    for t, cnt in sorted(teams.items(), key=lambda x: x[1], reverse=True)[:30]:
        print(f"  {t}: {cnt} matches")
else:
    print("scratch/all_parsed_replays_summary.json does not exist yet.")
