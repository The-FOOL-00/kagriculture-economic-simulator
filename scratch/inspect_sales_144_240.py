import json

with open("scratch/replays/V2_Loss_vs_Yuyajk_104810879.json") as f:
    steps = json.load(f)["steps"]

print("=== REPLAY SALES (STEPS 144-240) ===")
for s in range(144, 241):
    act = steps[s][1].get("action", {})
    mkt = act.get("market", []) if isinstance(act, dict) else []
    for o in mkt:
        if isinstance(o, list) and len(o) >= 1 and o[0] == "SELL":
            f = steps[s][1]["observation"]["farms"][1]
            print(f"Step {s:3d} (D{s//24:02d}:H{s%24:02d}) | Cash:${f['money']:7.1f} | Order:{o}")
