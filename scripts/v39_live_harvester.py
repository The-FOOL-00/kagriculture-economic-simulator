"""
V39 Live Episode Harvester
Downloads and catalogs all live episodes for V35 (submission 56540535).
Strictly read-only Kaggle API calls.
Enforces holdout quarantine.
"""

import json
import os
import subprocess
import sys
import time

SUBMISSION_ID = 56540535
OUR_TEAM_NAME = "Sanjay"
PROTECTED_HOLDOUTS = [
    (214200, 214249),
    (340090, 340199),
    (249695, 249734),
]

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
LIVE_DIR = os.path.join(BASE_DIR, "scratch", "v39", "live")
REPLAY_DIR = os.path.join(LIVE_DIR, "replays")
LOGS_DIR = os.path.join(LIVE_DIR, "logs")
OUT_JSONL = os.path.join(LIVE_DIR, "episodes.jsonl")
PROGRESS_FILE = os.path.join(LIVE_DIR, "harvester_progress.json")
DONE_MARKER = os.path.join(LIVE_DIR, ".harvester_done")

def is_protected(seed):
    if seed is None:
        return False
    for start, end in PROTECTED_HOLDOUTS:
        if start <= seed <= end:
            return True
    return False

def get_submission_episodes(sub_id):
    cmd = ["kaggle", "competitions", "episodes", str(sub_id), "--format", "json"]
    res = subprocess.run(cmd, capture_output=True, text=True, check=True)
    s = res.stdout.strip()
    start = s.find("[")
    end = s.rfind("]")
    if start != -1 and end != -1:
        return json.loads(s[start:end+1])
    return json.loads(s)

def harvest():
    os.makedirs(REPLAY_DIR, exist_ok=True)
    os.makedirs(LOGS_DIR, exist_ok=True)
    
    print(f"Fetching episode list for submission {SUBMISSION_ID}...")
    episodes = get_submission_episodes(SUBMISSION_ID)
    print(f"Found {len(episodes)} total episodes.")
    
    existing_records = {}
    if os.path.exists(OUT_JSONL):
        with open(OUT_JSONL, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    rec = json.loads(line)
                    existing_records[rec["episode_id"]] = rec
                    
    results = []
    
    for idx, ep in enumerate(episodes):
        ep_id = ep["id"]
        create_time = ep.get("createTime")
        end_time = ep.get("endTime")
        ep_state = ep.get("state")
        ep_type = ep.get("type")
        
        replay_path = os.path.join(REPLAY_DIR, f"episode-{ep_id}-replay.json")
        if not os.path.exists(replay_path):
            print(f"[{idx+1}/{len(episodes)}] Downloading replay for episode {ep_id}...")
            dl_cmd = ["kaggle", "competitions", "replay", str(ep_id), "-p", REPLAY_DIR, "-q"]
            r = subprocess.run(dl_cmd, capture_output=True, text=True)
            if r.returncode != 0:
                print(f"Warning: failed to download replay for {ep_id}: {r.stderr}")
                continue
                
        # Parse replay
        try:
            with open(replay_path, "r", encoding="utf-8") as f:
                replay = json.load(f)
        except Exception as e:
            print(f"Error parsing replay {replay_path}: {e}")
            continue
            
        info = replay.get("info", {})
        seed = info.get("seed")
        
        # Enforce Quarantine
        if is_protected(seed):
            print(f"CRITICAL: Episode {ep_id} seed {seed} is in PROTECTED HOLDOUT! Quarantining.")
            continue
            
        team_names = info.get("TeamNames", [])
        rewards = replay.get("rewards", [0, 0])
        statuses = replay.get("statuses", ["", ""])
        
        our_seat = None
        opp_seat = None
        opp_name = None
        
        if len(team_names) >= 2:
            if team_names[0] == OUR_TEAM_NAME and team_names[1] != OUR_TEAM_NAME:
                our_seat = 0
                opp_seat = 1
                opp_name = team_names[1]
            elif team_names[1] == OUR_TEAM_NAME and team_names[0] != OUR_TEAM_NAME:
                our_seat = 1
                opp_seat = 0
                opp_name = team_names[0]
            elif team_names[0] == OUR_TEAM_NAME and team_names[1] == OUR_TEAM_NAME:
                our_seat = 0  # Self-play / validation
                opp_seat = 1
                opp_name = "Self/Validation (Sanjay)"
            else:
                our_seat = 0
                opp_seat = 1
                opp_name = team_names[1]
        else:
            our_seat = 0
            opp_seat = 1
            opp_name = "Unknown"
            
        our_reward = rewards[our_seat] if rewards and len(rewards) > our_seat else None
        opp_reward = rewards[opp_seat] if rewards and len(rewards) > opp_seat else None
        
        # Determine terminal cash from final observation
        steps = replay.get("steps", [])
        our_terminal_cash = None
        opp_terminal_cash = None
        if steps:
            final_step = steps[-1]
            try:
                obs_0 = final_step[our_seat].get("observation", {})
                players = obs_0.get("players", [])
                if players and len(players) > our_seat:
                    our_terminal_cash = players[our_seat].get("cash")
                if players and len(players) > opp_seat:
                    opp_terminal_cash = players[opp_seat].get("cash")
            except Exception:
                pass
                
        if our_reward is not None and opp_reward is not None:
            if our_reward > opp_reward:
                result = "WIN"
            elif our_reward < opp_reward:
                result = "LOSS"
            else:
                result = "TIE"
            margin = our_reward - opp_reward
        else:
            result = "UNKNOWN"
            margin = 0
            
        record = {
            "episode_id": ep_id,
            "timestamp": create_time,
            "end_time": end_time,
            "submission_id": SUBMISSION_ID,
            "opponent_id": None,  # Not exposed by platform API
            "opponent_name": opp_name,
            "seat": our_seat,
            "seed": seed,
            "terminal_reward": our_reward,
            "opponent_reward": opp_reward,
            "terminal_cash": our_terminal_cash,
            "opponent_cash": opp_terminal_cash,
            "margin": margin,
            "result": result,
            "episode_status": statuses[our_seat] if statuses and len(statuses) > our_seat else ep_state,
            "episode_type": ep_type,
            "episode_url": f"https://www.kaggle.com/competitions/kaggriculture/leaderboard?dialog=episodes-episode-{ep_id}",
            "steps_count": len(steps)
        }
        
        # Download log if available
        log_file = os.path.join(LOGS_DIR, f"episode-{ep_id}-agent-{our_seat}-logs.json")
        if not os.path.exists(log_file):
            subprocess.run(["kaggle", "competitions", "logs", str(ep_id), str(our_seat), "-p", LOGS_DIR, "-q"], capture_output=True)
            
        results.append(record)
        existing_records[ep_id] = record
        
        # Write progress
        with open(PROGRESS_FILE, "w", encoding="utf-8") as pf:
            json.dump({"processed": idx + 1, "total": len(episodes), "last_id": ep_id}, pf, indent=2)
            
    # Write full jsonl
    with open(OUT_JSONL, "w", encoding="utf-8") as f:
        for ep_id in sorted(existing_records.keys()):
            f.write(json.dumps(existing_records[ep_id]) + "\n")
            
    with open(DONE_MARKER, "w", encoding="utf-8") as df:
        df.write(f"DONE at {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}\n")
        df.write(f"Total episodes cataloged: {len(existing_records)}\n")
        
    print(f"Harvester completed successfully! Cataloged {len(existing_records)} episodes in {OUT_JSONL}")

if __name__ == "__main__":
    harvest()
