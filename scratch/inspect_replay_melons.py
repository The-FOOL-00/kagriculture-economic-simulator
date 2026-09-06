import json

with open("scratch/replays/V2_Loss_vs_Yuyajk_104810879.json") as f:
    steps = json.load(f)["steps"]

print("Day | Melons on Farm | Shed Melons | Cash")
for d in range(13):
    s = d * 24
    f1 = steps[s][1]["observation"]["farms"][1]
    priv1 = steps[s][1]["observation"]["private"]
    melons_farm = sum(1 for row in f1["tiles"] for t in row if isinstance(t, dict) and t.get("crop") == "MELON")
    shed_m = priv1["shed"].get("MELON", 0)
    cash = f1["money"]
    print(f"Day {d:2d} (Step {s:3d}): FarmMelons={melons_farm:2d}, ShedMelons={shed_m:2d}, Cash={cash:8.1f}")
