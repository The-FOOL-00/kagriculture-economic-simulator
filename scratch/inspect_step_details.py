import json
import os

with open("replays/episode-92890298-replay.json", "r", encoding="utf-8") as f:
    data = json.load(f)

print("ID:", data.get("id"))
print("Version:", data.get("version"))
print("Module Version:", data.get("module_version"))
print("Info:", data.get("info"))
print("Configuration:", data.get("configuration"))
print("Statuses:", data.get("statuses"))
print("Rewards:", data.get("rewards"))

# Check step 0
print("\nStep 0 player 0 observation keys:", list(data["steps"][0][0]["observation"].keys()) if "observation" in data["steps"][0][0] else "No obs")
if "observation" in data["steps"][0][0]:
    obs0 = data["steps"][0][0]["observation"]
    print("Step 0 obs sample keys:", list(obs0.keys()))
    if "controlled_player_index" in obs0:
        print("Controlled player index:", obs0["controlled_player_index"])

# Check step 1 action
print("\nStep 1 actions:")
for p in range(len(data["steps"][1])):
    print(f"  Player {p} action: {data['steps'][1][p].get('action')}")
