import json

with open("scratch/replays/V2_Loss_vs_Yuyajk_104810879.json") as f:
    d = json.load(f)

steps = d["steps"]
p = 1 # Yuyajk is player 1

print("=== YUTAJK FIRST 24 STEPS TELEMETRY ===")
for s in range(25):
    step_data = steps[s][p]
    obs = step_data["observation"]
    act = step_data.get("action", {})
    farm = obs["farms"][p]
    priv = obs.get("private", {})
    
    # Farmer & hands actions
    farmer_act = act.get("farmer") if isinstance(act, dict) else None
    hands_act = act.get("hands") if isinstance(act, dict) else None
    mkt = act.get("market") if isinstance(act, dict) else None
    
    # Farmer & hands pos
    farmer_pos = farm.get("farmer")
    hands_pos = farm.get("hands", [])
    
    # Count plants
    melon_tiles = []
    wheat_tiles = []
    pasture_tiles = []
    for y, row in enumerate(farm.get("tiles", [])):
        for x, t in enumerate(row):
            if isinstance(t, dict):
                if t.get("crop") == "MELON":
                    melon_tiles.append((x, y, t.get("water_level", 0), t.get("growth_stage", 0)))
                elif t.get("crop") == "WHEAT":
                    wheat_tiles.append((x, y, t.get("water_level", 0), t.get("growth_stage", 0)))
                elif t.get("kind") == "PASTURE":
                    pasture_tiles.append((x, y, t.get("animal")))
                    
    money = farm.get("money")
    print(f"Step {s:02d} | Cash:${money:6.1f} | Hands:{len(hands_pos)} | Farmer:{farmer_act} | HandsAct:{hands_act} | Mkt:{mkt} | Pastures:{len(pasture_tiles)} | MelonsPlanted:{len(melon_tiles)} | WheatPlanted:{len(wheat_tiles)}")
