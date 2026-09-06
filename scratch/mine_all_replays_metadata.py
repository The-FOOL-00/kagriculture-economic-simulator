import os
import glob
import json
import traceback

def scan_replays():
    replay_files = glob.glob("replays/**/*.json", recursive=True) + glob.glob("*.json")
    print(f"Total candidate json files found: {len(replay_files)}")
    
    episodes = []
    seen_episodes = set()
    
    for fpath in replay_files:
        # Avoid non-replay result json files
        fname = os.path.basename(fpath)
        if any(x in fname for x in ["manifest", "results", "scoreboard", "trace", "snapshot", "summary", "forensic", "telemetry"]):
            continue
            
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                data = json.load(f)
                
            # Check if this is a Kaggle replay schema
            if not isinstance(data, dict):
                continue
                
            steps = data.get("steps") or data.get("specification", {}).get("steps")
            if not steps or not isinstance(steps, list) or len(steps) < 10:
                continue
                
            ep_id = data.get("id") or data.get("episode_id") or fname.replace(".json", "")
            
            # Extract player names / agent info if present
            agents = data.get("agents") or data.get("info", {}).get("Agents") or []
            team_names = []
            if agents:
                for ag in agents:
                    if isinstance(ag, dict):
                        team_names.append(ag.get("name") or ag.get("submissionId") or str(ag))
                    else:
                        team_names.append(str(ag))
                        
            # Rewards
            last_step = steps[-1]
            rewards = [p.get("reward") for p in last_step] if isinstance(last_step, list) else []
            
            # Step length
            num_steps = len(steps)
            
            # Check actions in step 0, 1, 2...
            # To see if actions vary or are fixed/empty
            has_actions_p0 = any(len(s[0].get("action") or {}) > 0 for s in steps if isinstance(s, list) and len(s) > 0)
            has_actions_p1 = any(len(s[1].get("action") or {}) > 0 for s in steps if isinstance(s, list) and len(s) > 1)
            
            episodes.append({
                "file": fpath.replace("\\", "/"),
                "size_mb": round(os.path.getsize(fpath) / (1024 * 1024), 2),
                "id": str(ep_id),
                "num_steps": num_steps,
                "team_names": team_names,
                "rewards": rewards,
                "has_actions_p0": has_actions_p0,
                "has_actions_p1": has_actions_p1
            })
        except Exception as e:
            # print(f"Skipping {fpath}: {e}")
            pass
            
    print(f"Parsed {len(episodes)} valid replay files.")
    
    with open("scratch/all_parsed_replays_summary.json", "w", encoding="utf-8") as f:
        json.dump(episodes, f, indent=2)
        
    return episodes

if __name__ == "__main__":
    scan_replays()
