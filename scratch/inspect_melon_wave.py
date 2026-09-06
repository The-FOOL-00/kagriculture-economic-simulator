import json

with open("scratch/replays/V2_Loss_vs_Yuyajk_104810879.json") as f:
    d = json.load(f)

steps = d["steps"]

print("=== DAY 10-11 TELEMETRY (STEPS 240-270) ===")
print("Step | P0(V2) Cash  ShedMelon MktAct                                  | P1(Yuyajk) Cash ShedMelon MktAct")
print("-" * 110)

for s in range(240, 271):
    d_num = s // 24
    h_num = s % 24
    
    # P0 (V2)
    obs0 = steps[s][0]["observation"]
    f0 = obs0["farms"][0]
    p0_priv = obs0.get("private", {})
    p0_cash = f0.get("money", 0)
    p0_melon = p0_priv.get("shed", {}).get("MELON", 0)
    act0 = steps[s][0].get("action", {})
    mkt0 = act0.get("market", []) if isinstance(act0, dict) else []
    
    # P1 (Yuyajk)
    obs1 = steps[s][1]["observation"]
    f1 = obs1["farms"][1]
    p1_priv = obs1.get("private", {})
    p1_cash = f1.get("money", 0)
    p1_melon = p1_priv.get("shed", {}).get("MELON", 0)
    act1 = steps[s][1].get("action", {})
    mkt1 = act1.get("market", []) if isinstance(act1, dict) else []
    
    mkt0_str = str(mkt0) if mkt0 else ""
    mkt1_str = str(mkt1) if mkt1 else ""
    
    if s in [240, 255, 259, 260, 261, 262, 263, 264, 265, 266, 270] or mkt0 or mkt1:
        print(f"{s:3d} (D{d_num:02d}:H{h_num:02d}) | P0: ${p0_cash:7.1f} M:{p0_melon:2d} {mkt0_str:35s} | P1: ${p1_cash:7.1f} M:{p1_melon:2d} {mkt1_str}")
