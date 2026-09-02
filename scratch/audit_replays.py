import glob
import json
import os
import pandas as pd

files = sorted(glob.glob("replays/episode-*.json"))
print(f"Total files found matching 'replays/episode-*.json': {len(files)}")

episodes_summary = []
for f in files:
    with open(f, "r", encoding="utf-8") as fp:
        data = json.load(fp)
    
    eid = data.get("id")
    title = data.get("title")
    desc = data.get("description")
    rewards = data.get("rewards")
    statuses = data.get("statuses")
    steps_count = len(data.get("steps", []))
    
    # Extract agent info from steps[0] or steps[-1]
    steps = data.get("steps", [])
    player_obs = steps[0][0].get("observation", {}) if steps else {}
    farms = player_obs.get("farms", [])
    
    # Find which seat is our user and which is opponent
    final_step = steps[-1] if steps else []
    r0 = final_step[0].get("reward") if len(final_step) > 0 else None
    r1 = final_step[1].get("reward") if len(final_step) > 1 else None
    
    episodes_summary.append({
        "file": os.path.basename(f),
        "id": eid,
        "steps": steps_count,
        "reward_0": r0,
        "reward_1": r1,
        "status_0": statuses[0] if statuses else None,
        "status_1": statuses[1] if len(statuses) > 1 else None,
    })

df = pd.DataFrame(episodes_summary)
print(df.to_string())
df.to_csv("scratch/current_27_replays_audit.csv", index=False)
