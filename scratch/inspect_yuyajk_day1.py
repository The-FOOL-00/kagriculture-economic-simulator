import json

with open("scratch/replays/V2_Loss_vs_Yuyajk_104810879.json") as f:
    d = json.load(f)

steps = d["steps"]
p = 1 # Yuyajk is player 1

print("=== YUYAJK DAYS 1-5 (Steps 24-120) ===")
for s in range(24, 121):
    if s % 24 == 0 or s in (25, 48, 72, 96, 120):
        step_data = steps[s][p]
        obs = step_data["observation"]
        act = step_data.get("action", {})
        farm = obs["farms"][p]
        priv = obs.get("private", {})
        
        day = s // 24
        hour = s % 24
        money = farm.get("money")
        hands = len(farm.get("hands", []))
        shed = priv.get("shed", {})
        
        mkt = act.get("market", [])
        farmer_act = act.get("farmer")
        
        print(f"Step {s:3d} (D{day} H{hour:2d}): Cash=${money:6.1f} | Hands={hands} | Mkt={mkt} | Shed={shed} | Farmer={farmer_act}")
