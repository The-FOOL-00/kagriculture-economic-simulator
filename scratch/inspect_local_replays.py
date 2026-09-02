import json
import os
import sys

def inspect_local_replays():
    files = [f for f in os.listdir("replays") if f.endswith(".json")]
    print(f"Total local replay json files in replays/: {len(files)}")
    
    summary = []
    for fname in sorted(files)[:5]:
        fpath = os.path.join("replays", fname)
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            # Replay structure inspection
            keys = list(data.keys())
            agents = data.get("agents", [])
            rewards = data.get("rewards", [])
            steps_count = len(data.get("steps", []))
            info = data.get("info", {})
            env_spec = data.get("specification", {})
            
            summary.append({
                "file": fname,
                "keys": keys,
                "agents": agents,
                "rewards": rewards,
                "steps": steps_count,
                "info": info
            })
            print(f"\nReplay: {fname}")
            print(f"  Keys: {keys}")
            print(f"  Agents: {agents}")
            print(f"  Rewards: {rewards}")
            print(f"  Steps: {steps_count}")
            if "environment" in data:
                print(f"  Environment: {data['environment']}")
            if steps_count > 0:
                first_step = data["steps"][0]
                print(f"  Step 0 keys: {list(first_step[0].keys()) if isinstance(first_step, list) else list(first_step.keys())}")
        except Exception as e:
            print(f"Error inspecting {fname}: {e}")

if __name__ == "__main__":
    inspect_local_replays()
