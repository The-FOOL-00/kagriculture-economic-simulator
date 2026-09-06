import os
import json
import subprocess
from kaggle.api.kaggle_api_extended import KaggleApi

def main():
    api = KaggleApi()
    api.authenticate()
    
    # Check submissions
    print("Fetching submissions...")
    subs = api.competition_submissions('kaggriculture')
    subs_data = []
    for s in subs:
        sub_entry = {
            "id": getattr(s, 'id', None),
            "ref": getattr(s, 'ref', None),
            "fileName": getattr(s, 'fileName', None),
            "description": getattr(s, 'description', None),
            "date": str(getattr(s, 'date', None)),
            "status": str(getattr(s, 'status', None)),
            "publicScore": str(getattr(s, 'publicScore', None)),
            "privateScore": str(getattr(s, 'privateScore', None)),
            "raw": str(s)
        }
        subs_data.append(sub_entry)
        
    with open("scratch/our_submissions_snapshot.json", "w", encoding="utf-8") as f:
        json.dump(subs_data, f, indent=2)
        
    print(f"Saved {len(subs_data)} submissions.")
    for s in subs_data[:5]:
        print(s)

    # Let's download the full leaderboard CSV via kaggle competitions leaderboard --download
    print("Downloading full leaderboard...")
    res = subprocess.run(["kaggle", "competitions", "leaderboard", "-c", "kaggriculture", "-d", "-p", "scratch"], capture_output=True, text=True)
    print("Download stdout:", res.stdout)
    print("Download stderr:", res.stderr)
    
    # Check what zip or csv appeared in scratch
    for f in os.listdir("scratch"):
        print("scratch file:", f)

if __name__ == "__main__":
    main()
