import os
import json
from kaggle.api.kaggle_api_extended import KaggleApi

def main():
    api = KaggleApi()
    api.authenticate()
    
    print("Fetching leaderboard for kaggriculture...")
    # Get leaderboard
    lb = api.competition_leaderboard_view('kaggriculture')
    print(f"Total entries returned: {len(lb)}")
    
    lb_data = []
    for i, row in enumerate(lb):
        # row has attributes: teamId, teamName, submissionDate, score
        entry = {
            "rank": i + 1,
            "teamId": getattr(row, 'teamId', None) or getattr(row, 'team_id', None),
            "teamName": str(getattr(row, 'teamName', None) or getattr(row, 'team_name', None)),
            "score": float(getattr(row, 'score', 0)),
            "submissionDate": str(getattr(row, 'submissionDate', None) or getattr(row, 'submission_date', None))
        }
        lb_data.append(entry)
        
    os.makedirs("scratch", exist_ok=True)
    with open("scratch/live_leaderboard_snapshot.json", "w", encoding="utf-8") as f:
        json.dump(lb_data, f, indent=2)
        
    print(f"Saved snapshot with {len(lb_data)} teams.")
    
    # Submissions
    print("Fetching our submissions...")
    subs = api.competition_submissions('kaggriculture')
    subs_data = []
    for s in subs:
        sub_entry = {
            "id": getattr(s, 'id', None),
            "ref": getattr(s, 'ref', None),
            "fileName": getattr(s, 'fileName', None),
            "description": getattr(s, 'description', None),
            "date": str(getattr(s, 'date', None)),
            "status": getattr(s, 'status', None),
            "publicScore": getattr(s, 'publicScore', None),
            "privateScore": getattr(s, 'privateScore', None),
        }
        subs_data.append(sub_entry)
        print(f"Sub: {sub_entry}")
        
    with open("scratch/our_submissions_snapshot.json", "w", encoding="utf-8") as f:
        json.dump(subs_data, f, indent=2)

if __name__ == "__main__":
    main()
