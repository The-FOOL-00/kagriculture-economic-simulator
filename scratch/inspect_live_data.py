import os
import sys
import json
import kaggle
from datetime import datetime, timezone

# Ensure utf-8 stdout
sys.stdout.reconfigure(encoding='utf-8')

kaggle.api.authenticate()
now_utc = datetime.now(timezone.utc).isoformat()
print(f"Retrieval timestamp: {now_utc}")

# Let's inspect the fields in leaderboard.json
if os.path.exists("scratch/leaderboard.json"):
    with open("scratch/leaderboard.json", "r", encoding="utf-8") as f:
        lb = json.load(f)
    print(f"\nLoaded {len(lb)} entries from current leaderboard.json")
    for i, r in enumerate(lb[:10]):
        print(f"#{i+1}: {r}")

# Let's inspect episodes_55958978.json (V2)
if os.path.exists("scratch/episodes_55958978.json"):
    with open("scratch/episodes_55958978.json", "r", encoding="utf-8") as f:
        v2_eps = json.load(f)
    print(f"\nLoaded {len(v2_eps)} episodes for Slot 2 (V2 - 55958978)")
    if v2_eps:
        print("Sample episode structure:")
        print(json.dumps(v2_eps[0], indent=2, default=str))

# Let's inspect episodes_55944418.json (V1)
if os.path.exists("scratch/episodes_55944418.json"):
    with open("scratch/episodes_55944418.json", "r", encoding="utf-8") as f:
        v1_eps = json.load(f)
    print(f"\nLoaded {len(v1_eps)} episodes for Slot 1 (V1 - 55944418)")
