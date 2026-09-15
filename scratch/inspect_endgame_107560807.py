import json

def inspect_endgame_107560807():
    path = "replays/live_tournament/episode_107560807.json"
    d = json.load(open(path))
    steps = d["steps"]
    
    print("=== ENDGAME ANALYSIS EPISODE 107560807 (Steps 648 to 719) ===")
    
    # Track sales from step 648 onwards
    for s in range(648, 720):
        obs = steps[s][0]["observation"]
        f0 = obs["farms"][0]
        f1 = obs["farms"][1]
        c0 = f0["money"]
        c1 = f1["money"]
        
        act0 = steps[s][0].get("action", {}) or {}
        act1 = steps[s][1].get("action", {}) or {}
        m0 = act0.get("market", [])
        m1 = act1.get("market", [])
        
        # print non-empty market actions
        if m0 or m1:
            print(f"Step {s:3d} (D{s//24} h{s%24:02d}): Us Cash=${c0:6,.0f} | Opp Cash=${c1:6,.0f} | Us Mkt: {m0} | Opp Mkt: {m1}")

if __name__ == "__main__":
    inspect_endgame_107560807()
