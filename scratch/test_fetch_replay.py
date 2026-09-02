import os
import sys
import json
import kaggle

kaggle.api.authenticate()

print("Testing competition_episode_replay...")
ep_id = 104820229
try:
    rep = kaggle.api.competition_episode_replay(ep_id)
    print(f"Replay type: {type(rep)}")
    os.makedirs("scratch/replays", exist_ok=True)
    with open(f"scratch/replays/{ep_id}.json", "w", encoding="utf-8") as f:
        if isinstance(rep, (dict, list)):
            json.dump(rep, f, indent=2)
        elif hasattr(rep, 'to_dict'):
            json.dump(rep.to_dict(), f, indent=2)
        elif hasattr(rep, '__dict__'):
            json.dump(rep.__dict__, f, indent=2)
        else:
            f.write(str(rep))
    print(f"Saved replay {ep_id} to scratch/replays/{ep_id}.json")
    # Check size of file
    size = os.path.getsize(f"scratch/replays/{ep_id}.json")
    print(f"File size: {size} bytes")
except Exception as e:
    print(f"Error fetching replay: {e}")
