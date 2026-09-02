import json

with open("scratch/replays/V2_Loss_vs_KawattaTaido_104817623.json", "r") as f:
    data = json.load(f)

print("Keys:", data.keys())
print("Configuration:", data.get("configuration", {}))
print("Description:", data.get("description", ""))
print("Step 0 info:", data.get("steps", [[]])[0][0].keys())
print("Step 0 observation keys:", data.get("steps", [[]])[0][0].get("observation", {}).keys())
