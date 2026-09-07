import json

with open("scratch/replays/V2_Loss_vs_Yuyajk_104810879.json") as f:
    d = json.load(f)

steps = d["steps"]
p = 1

print("=== YUYAJK DAYS 5-15 (Steps 120-360) ===")
for s in range(120, 361, 24):
    f = steps[s][p]["observation"]["farms"][p]
    priv = steps[s][p]["observation"]["private"]
    act = steps[s][p].get("action", {})
    day = s // 24
    money = f.get("money", 0)
    hands = len(f.get("hands", []))
    mkt = act.get("market", [])
    shed = priv.get("shed", {})
    quads = len(f.get("unlocked_quadrants", []))
    print(f"Step {s:3d} (D{day:2d}): Cash=${money:8.1f} | Hands={hands:2d} | Quads={quads} | Shed={shed} | Mkt={mkt}")
