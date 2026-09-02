import json
import os

print("Searching state.json...")
if os.path.exists("replays/raw/georgymamarin/state.json"):
    with open("replays/raw/georgymamarin/state.json", "r", encoding="utf-8") as f:
        state = json.load(f)
    print("State keys:", state.keys())
    print("Submissions in state:", len(state.get("submissions", [])))
    print("Episodes in state:", len(state.get("episodes", {})))
    
    # Search for sub_id 55893176
    sub_id = 55893176
    found_eps = []
    for eid, ep in state.get("episodes", {}).items():
        for ag in ep.get("agents", []):
            if ag.get("submissionId") == sub_id:
                found_eps.append((eid, ep))
    print(f"Total episodes matching submission {sub_id} in state.json: {len(found_eps)}")
    if found_eps:
        for eid, ep in found_eps[:5]:
            print(f"Episode {eid}: createTime={ep.get('createTime')}, state={ep.get('state')}")
