import os
import glob
import json
import pandas as pd

def find_top_agent_replays():
    # Let's search all json files for top agent names or keywords
    target_names = [
        "Crop Dusta", "Whyme", "Yuan800", "MtN", "Kawatta", "Mengfei", "keiz",
        "Tadros", "c0nrad", "peikopon", "Syed", "Milan", "Agent 0", "Aastik",
        "Dresden", "destbreso", "vijaikm", "Aethel", "Apex"
    ]
    
    # Check replays in replays/ and scratch/ and raw/
    files = glob.glob("replays/**/*.json", recursive=True) + glob.glob("scratch/**/*.json", recursive=True) + glob.glob("*.json")
    print(f"Total json files to check: {len(files)}")
    
    matched_episodes = []
    
    for fpath in files:
        fname = os.path.basename(fpath)
        if any(x in fname for x in ["manifest", "results", "scoreboard", "trace", "snapshot", "summary", "audit", "leaderboard", "holdout"]):
            continue
        try:
            sz = os.path.getsize(fpath)
            if sz < 10000 or sz > 50000000:
                continue
            with open(fpath, "r", encoding="utf-8") as fp:
                data = json.load(fp)
            if not isinstance(data, dict):
                continue
            steps = data.get("steps")
            if not steps or len(steps) < 10:
                continue
                
            agents = data.get("agents") or data.get("info", {}).get("Agents") or []
            agent_str = str(agents)
            
            # Check if any target name appears in agent_str or filename
            found_targets = [t for t in target_names if t.lower() in agent_str.lower() or t.lower() in fpath.lower()]
            if found_targets:
                last_step = steps[-1]
                rewards = [p.get("reward") for p in last_step] if isinstance(last_step, list) else []
                matched_episodes.append({
                    "file": fpath.replace("\\", "/"),
                    "size_mb": round(sz / (1024 * 1024), 2),
                    "steps": len(steps),
                    "targets": found_targets,
                    "agents": agents,
                    "rewards": rewards
                })
        except Exception as e:
            pass
            
    print(f"Found {len(matched_episodes)} matching top-agent replay files.")
    with open("scratch/top_agent_matched_replays.json", "w", encoding="utf-8") as f:
        json.dump(matched_episodes, f, indent=2)
        
    for m in matched_episodes[:15]:
        print(f"File: {m['file']} | Targets: {m['targets']} | Rewards: {m['rewards']}")

if __name__ == "__main__":
    find_top_agent_replays()
